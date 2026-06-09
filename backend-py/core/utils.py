import chardet
import os
import shutil
import sys
import zipfile


def detect_encoding(file_path: str, verbose: bool = True) -> str:
    """
    Detect file encoding using chardet + fallback chain.
    
    Strategy (inspired by SplitChapter):
    1. Use chardet for high-confidence detection
    2. If chardet confidence < 0.7, try fallback chain: utf-8 → utf-16 → gbk
    3. Final fallback: utf-8 with errors='replace'
    """
    if not os.path.exists(file_path):
        return 'utf-8'
        
    with open(file_path, 'rb') as f:
        rawdata = f.read(50000)
    
    if not rawdata:
        return 'utf-8'
    
    result = chardet.detect(rawdata)
    encoding = result.get('encoding')
    confidence = result.get('confidence', 0)
    
    if verbose:
        print(f"PROGRESS: 10% (Detected encoding: {encoding}, confidence: {confidence})", file=sys.stderr)
    
    # High confidence: trust chardet
    if encoding and confidence >= 0.7:
        return encoding
    
    # Low confidence or None: try fallback chain (gbk → utf-8 → utf-16)
    # 中文 TXT 文件 GBK 编码更常见，优先尝试
    for fallback in ('gbk', 'utf-8', 'utf-16'):
        try:
            rawdata.decode(fallback)
            if verbose:
                print(f"PROGRESS: 10% (Fallback encoding: {fallback})", file=sys.stderr)
            return fallback
        except (UnicodeDecodeError, Exception):
            continue
    
    # chardet gave something, use it even with low confidence
    if encoding:
        return encoding
        
    return 'utf-8'


def safe_extract_zip(zf: zipfile.ZipFile, dest_dir: str) -> None:
    """
    Extract a zip archive without allowing entries to escape dest_dir.
    EPUB files are zip archives and may be user-supplied, so never call
    extractall() on them directly.
    """
    dest_real = os.path.realpath(dest_dir)

    for member in zf.infolist():
        member_name = member.filename.replace("\\", "/")
        if (
            os.path.isabs(member_name)
            or member_name == ".."
            or member_name.startswith("../")
            or "/../" in member_name
        ):
            raise ValueError(f"Unsafe zip entry path: {member.filename}")

        target_path = os.path.realpath(os.path.join(dest_dir, member_name))
        if target_path != dest_real and not target_path.startswith(dest_real + os.sep):
            raise ValueError(f"Unsafe zip entry path: {member.filename}")

        if member.is_dir():
            os.makedirs(target_path, exist_ok=True)
            continue

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with zf.open(member, "r") as source, open(target_path, "wb") as target:
            shutil.copyfileobj(source, target)


def safe_join_path(base_dir: str, relative_path: str) -> str:
    """Join a user/archive supplied relative path and require it to stay inside base_dir."""
    normalized_path = relative_path.replace("\\", "/")
    if (
        os.path.isabs(normalized_path)
        or normalized_path == ".."
        or normalized_path.startswith("../")
        or "/../" in normalized_path
    ):
        raise ValueError(f"Unsafe path: {relative_path}")

    base_real = os.path.realpath(base_dir)
    target_path = os.path.realpath(os.path.join(base_dir, normalized_path))
    if target_path != base_real and not target_path.startswith(base_real + os.sep):
        raise ValueError(f"Unsafe path: {relative_path}")
    return target_path
