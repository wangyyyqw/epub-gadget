"""豆瓣封面搜索与下载模块"""
import os
import tempfile
import requests
from typing import List, Dict, Optional

SUGGEST_URL = "https://book.douban.com/j/subject_suggest"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://book.douban.com/",
}
TIMEOUT = 10


def search_books(query: str) -> List[Dict]:
    """搜索豆瓣图书，返回结果列表。
    
    每个结果包含: id, title, author, cover_url, year, publisher
    """
    try:
        resp = requests.get(
            SUGGEST_URL,
            params={"q": query},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return []

    results = []
    for item in data:
        if item.get("type") != "b":  # 只要图书类型
            continue
        cover_url = item.get("img", "")
        # 豆瓣返回的是小图，替换为大图
        if cover_url:
            cover_url = cover_url.replace("/s/", "/l/")
        results.append({
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "author": item.get("author_name", ""),
            "cover_url": cover_url,
            "year": item.get("year", ""),
            "publisher": item.get("pub", ""),
        })
    return results


def download_cover(cover_url: str, save_dir: Optional[str] = None) -> str:
    """下载封面图片到临时文件，返回本地路径。"""
    if not cover_url:
        raise ValueError("封面 URL 为空")

    resp = requests.get(cover_url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    ext = ".jpg"
    if "png" in content_type:
        ext = ".png"
    elif "webp" in content_type:
        ext = ".webp"

    if save_dir is None:
        save_dir = tempfile.gettempdir()
    os.makedirs(save_dir, exist_ok=True)

    # 生成唯一的文件名
    import uuid
    unique_name = f"douban_cover_{uuid.uuid4().hex[:8]}{ext}"
    path = os.path.join(save_dir, unique_name)
    with open(path, "wb") as f:
        f.write(resp.content)
    return path
