# -*- coding: utf-8 -*-
# EPUB 转 TXT 模块：将 EPUB 内容提取为纯文本，保留章节结构

import os
import sys
import re
import zipfile
import posixpath
from xml.etree import ElementTree
from urllib.parse import unquote
from html.parser import HTMLParser

try:
    from ..log import logwriter
except ImportError:
    from .log import logwriter

from .merge_epub import (
    _strip_ns,
    _find_opf_path,
    _parse_opf,
    NS_EPUB,
    NS_OPF,
    NS_DC,
    NS_XHTML,
    NS_NCX,
)

logger = logwriter()


def _parse_toc_nav(epub_zip, nav_path):
    """Parse EPUB3 nav document, return list of {"title": str, "href": str}."""
    try:
        nav_content = epub_zip.read(nav_path).decode("utf-8")
    except KeyError:
        return []
    root = ElementTree.fromstring(nav_content)
    nav_dir = posixpath.dirname(nav_path)
    entries = []

    def _find_toc_nav(elem):
        for child in elem:
            tag = _strip_ns(child.tag)
            if tag == "nav":
                epub_type = child.get(f"{{{NS_EPUB}}}type", "") or child.get("epub:type", "")
                if "toc" in epub_type:
                    return child
            result = _find_toc_nav(child)
            if result is not None:
                return result
        return None

    def _walk_nav_list(ol_elem):
        for li in ol_elem:
            if _strip_ns(li.tag) != "li":
                continue
            for child in li:
                child_tag = _strip_ns(child.tag)
                if child_tag == "a":
                    title = "".join(child.itertext()).strip()
                    href_attr = child.get("href", "")
                    href_no_frag = href_attr.split("#")[0] if href_attr else ""
                    href = posixpath.normpath(posixpath.join(nav_dir, unquote(href_no_frag))) if href_no_frag else ""
                    entries.append({"title": title, "href": href})
                elif child_tag == "span":
                    title = "".join(child.itertext()).strip()
                    entries.append({"title": title, "href": ""})
                elif child_tag == "ol":
                    _walk_nav_list(child)

    nav_elem = _find_toc_nav(root)
    if nav_elem is not None:
        for child in nav_elem:
            if _strip_ns(child.tag) == "ol":
                _walk_nav_list(child)
    return entries


def _parse_toc_ncx(epub_zip, ncx_path):
    """Parse EPUB2 NCX TOC, return list of {"title": str, "href": str}."""
    try:
        ncx_content = epub_zip.read(ncx_path).decode("utf-8")
    except KeyError:
        return []
    root = ElementTree.fromstring(ncx_content)
    ncx_dir = posixpath.dirname(ncx_path)
    entries = []

    def _walk_navpoints(parent):
        for child in parent:
            tag = _strip_ns(child.tag)
            if tag == "navPoint":
                title = ""
                href = ""
                for sub in child:
                    sub_tag = _strip_ns(sub.tag)
                    if sub_tag == "navLabel":
                        for t in sub:
                            if _strip_ns(t.tag) == "text":
                                title = (t.text or "").strip()
                    elif sub_tag == "content":
                        src = sub.get("src", "")
                        src_no_frag = src.split("#")[0] if src else ""
                        href = posixpath.normpath(posixpath.join(ncx_dir, src_no_frag)) if src_no_frag else ""
                if title or href:
                    entries.append({"title": title, "href": href})
                _walk_navpoints(child)

    for child in root:
        if _strip_ns(child.tag) == "navMap":
            _walk_navpoints(child)
            break
    return entries


class _XhtmlTextExtractor(HTMLParser):
    """Extract readable text from XHTML, stripping tags and normalising whitespace."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._in_script = False
        self._in_style = False
        self._skip_depth = 0  # depth counter for nested skip elements

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style"):
            self._skip_depth += 1
        elif tag_lower in ("br", "hr"):
            self.text_parts.append("\n")
        elif tag_lower in ("p", "div"):
            self.text_parts.append("\n\n")

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style"):
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag_lower in ("p", "div"):
            self.text_parts.append("\n\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self.text_parts.append(data)

    def get_text(self):
        text = "".join(self.text_parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        lines = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
        return "\n".join(lines)


def _extract_text_from_xhtml(xhtml_content: str) -> str:
    """Strip XHTML tags and return plain text with normalised whitespace."""
    parser = _XhtmlTextExtractor()
    try:
        parser.feed(xhtml_content)
    except Exception:
        return xhtml_content
    return parser.get_text()


def _build_chapter_title_map(toc_entries, spine_bookpaths):
    """Build a dict {bookpath: title} from TOC entries, fallback to spine."""
    title_map = {}

    for entry in toc_entries:
        href = entry.get("href", "")
        title = entry.get("title", "")
        if href and title:
            if href in title_map:
                if title_map[href] != title:
                    title_map[href] = title_map[href] + " | " + title
            else:
                title_map[href] = title

    for idx, bp in enumerate(spine_bookpaths):
        if bp not in title_map:
            title_map[bp] = f"第 {idx + 1} 节"

    return title_map


def run(epub_path: str, output_dir: str = None, keep_images: bool = False) -> int:
    """Convert EPUB to TXT.

    Args:
        epub_path: Path to the input EPUB file.
        output_dir: Output directory. Defaults to the directory of the EPUB.
        keep_images: If True, copy images to an 'images/' subdirectory.

    Returns:
        0 on success, non-zero on failure.
    """
    if not os.path.exists(epub_path):
        logger.write(f"ERROR: 文件不存在: {epub_path}")
        return 1
    if not zipfile.is_zipfile(epub_path):
        logger.write(f"ERROR: 不是有效的 EPUB/ZIP 文件: {epub_path}")
        return 1

    if output_dir is None:
        output_dir = os.path.dirname(epub_path)

    try:
        return _do_convert(epub_path, output_dir, keep_images)
    except Exception as e:
        logger.write(f"ERROR: 转换失败: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


def _do_convert(epub_path, output_dir, keep_images):
    with zipfile.ZipFile(epub_path, "r") as zf:
        opf_path = _find_opf_path(zf)
        if not opf_path:
            logger.write("ERROR: 无法找到 OPF 文件")
            return 1

        version, metadata_elem, manifest, spine, opf_dir, toc_id = _parse_opf(zf, opf_path)

        # --- Extract metadata ---
        title = ""
        author = ""
        if metadata_elem is not None:
            for child in metadata_elem:
                tag = _strip_ns(child.tag)
                if tag == "title":
                    title = (child.text or "").strip()
                elif tag == "creator":
                    author = (child.text or "").strip()

        if not title:
            title = os.path.splitext(os.path.basename(epub_path))[0]

        # --- Find nav / NCX TOC ---
        toc_entries = []
        nav_path = None

        for item_id, (href, media_type, props) in manifest.items():
            if "nav" in props:
                nav_path = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
                toc_entries = _parse_toc_nav(zf, nav_path)
                break

        if not toc_entries and toc_id and toc_id in manifest:
            ncx_href = manifest[toc_id][0]
            ncx_path = posixpath.normpath(posixpath.join(opf_dir, ncx_href)) if opf_dir else ncx_href
            toc_entries = _parse_toc_ncx(zf, ncx_path)

        # --- Build spine bookpath list (XHTML content docs in reading order) ---
        spine_bookpaths = []
        spine_id_map = {}
        for idref, linear, props in spine:
            if idref in manifest:
                href, media_type, _ = manifest[idref]
                if media_type == "application/xhtml+xml" or href.lower().endswith((".xhtml", ".html")):
                    bp = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
                    if bp not in spine_id_map:
                        spine_bookpaths.append(bp)
                    spine_id_map[bp] = (idref, linear, props)

        if not spine_bookpaths:
            logger.write("ERROR: EPUB 中没有可读取的章节内容")
            return 1

        # --- Build href -> title map from TOC ---
        title_map = _build_chapter_title_map(toc_entries, spine_bookpaths)

        # --- Extract text from each chapter ---
        chapter_texts = []
        image_map = {}

        for idx, bp in enumerate(spine_bookpaths):
            try:
                raw = zf.read(bp).decode("utf-8")
            except (KeyError, UnicodeDecodeError):
                logger.write(f"WARNING: 无法读取章节文件: {bp}")
                continue

            text = _extract_text_from_xhtml(raw)
            if text.strip():
                chapter_texts.append((bp, text))

        # --- Extract images if requested ---
        images_dir = None
        if keep_images:
            images_dir = os.path.join(output_dir, "images")
            os.makedirs(images_dir, exist_ok=True)

            for item_id, (href, media_type, _) in manifest.items():
                if media_type.startswith("image/"):
                    bp = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
                    try:
                        img_data = zf.read(bp)
                        img_filename = os.path.basename(href)
                        img_out_path = os.path.join(images_dir, img_filename)
                        with open(img_out_path, "wb") as imgf:
                            imgf.write(img_data)
                        image_map[bp] = os.path.join("images", img_filename)
                    except (KeyError, UnicodeDecodeError):
                        pass

        # --- Build TOC lines ---
        toc_lines = []
        toc_lines.append(f"{'=' * 60}")
        toc_lines.append(f"  《{title}》")
        if author:
            toc_lines.append(f"  作者：{author}")
        toc_lines.append(f"{'=' * 60}")
        toc_lines.append("")

        for bp, text in chapter_texts:
            first_line = text.split("\n")[0] if text else ""
            toc_lines.append(f"  {first_line}")

        toc_lines.append("")
        toc_lines.append(f"{'=' * 60}")
        toc_lines.append("")

        # --- Build full text ---
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"  《{title}》")
        if author:
            lines.append(f"  作者：{author}")
        lines.append(f"{'=' * 60}")
        lines.append("")

        for bp, text in chapter_texts:
            chapter_title = title_map.get(bp, "")
            if chapter_title:
                lines.append("")
                lines.append(f"{chapter_title}")
                lines.append(f"{'─' * 40}")
                lines.append("")

            lines.append(text)
            lines.append("")
            lines.append("")

        # --- Write output ---
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        txt_filename = f"{safe_title}.txt"
        txt_path = os.path.join(output_dir, txt_filename)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        file_size = os.path.getsize(txt_path)
        logger.write(f"SUCCESS: {txt_path} ({file_size} bytes)")

        if images_dir:
            logger.write(f"图片已保存至: {images_dir}")

        return 0
