"""将阅微书城格式的弹窗注释 (reader / js_readerFooterNote span) 批量转换为
标准 EPUB3 aside 脚注格式。

转换规则：
  输入（句中）:
    <span class="reader js_readerFooterNote" data-wr-footernote="注释内容"></span>
  输出（句中）:
    <sup><a epub:type="noteref" href="#fn1">[1]</a></sup>
  输出（章节末尾，插在 </body> 之前）:
    <aside id="fn1" class="aside-fn" epub:type="footnote">
        <p>注释内容</p>
    </aside>
  输出（每个章节 <head> 末尾注入）:
    <style>
      .aside-fn { font-size: 0.85em; margin-top: 1.5em; padding: 0.5em 0;
                  text-indent: 0; line-height: 1.4; color: [用户颜色]; }
      a.fn-ref  { text-decoration: none; font-size: 0.75em; vertical-align: super;
                   color: [用户颜色]; }
    </style>

特性：
  - 每个 HTML 文件（章节）独立从 [1] 开始编号；
  - 匹配 class 中包含 reader 或 js_readerFooterNote 的 span；
  - 跳过空注释；
  - 保留文件其余结构不变；
  - 自动为 <html> 标签添加 epub 命名空间；
  - 通过 <style> 内嵌块注入样式（幂等：检测已有标记则跳过）；
  - 引用标记和脚注文字颜色均可通过参数配置。
"""

import re
import zipfile
import shutil
import os
from typing import Dict, List, Tuple, Optional

# 匹配目标 span（连同闭合标签）
_SPAN_PATTERN = re.compile(
    r'<span\b[^>]*\bclass="[^"]*\b(reader|js_readerFooterNote)\b[^"]*"[^>]*\bdata-wr-footernote="([^"]*)"[^>]*>(?:</span>)?',
)

# 匹配 <html ...> 标签
_HTML_TAG_PATTERN = re.compile(r'<html\b([^>]*)>', re.IGNORECASE)

# 匹配 <head> 标签的闭合位置
_HEAD_CLOSE_PATTERN = re.compile(r'(</head>)', re.IGNORECASE)


def _build_style_block(
    footnote_color: Optional[str],
    noteref_color: Optional[str],
    skip_guard: bool = False,
) -> str:
    """生成注入到 <head> 中的 <style> 块内容。"""
    guard = "/* _epub_footnote_style_ */\n" if skip_guard else ""
    fn_color = footnote_color or "#004e1c"
    nr_color = noteref_color or "#b00020"
    return (
        "%s<style>\n"
        ".aside-fn {"
        " font-size: 0.85em;"
        " margin-top: 1.5em;"
        " padding: 0.5em 0;"
        " text-indent: 0;"
        " line-height: 1.4;"
        " color: %s;"
        "}\n"
        "a.fn-ref {"
        " text-decoration: none;"
        " font-size: 0.75em;"
        " vertical-align: super;"
        " color: %s;"
        "}\n"
        "</style>\n" % (guard, fn_color, nr_color)
    )


class SpanToFootnote:
    def convert(
        self,
        epub_path: str,
        output_path: Optional[str] = None,
        footnote_color: Optional[str] = None,
        noteref_color: Optional[str] = None,
    ) -> Tuple[int, int]:
        if output_path is None:
            output_path = epub_path

        if output_path != epub_path:
            shutil.copy2(epub_path, output_path)

        style_block = _build_style_block(footnote_color, noteref_color, skip_guard=True)

        total, skipped = 0, 0
        with zipfile.ZipFile(output_path, "r") as zin:
            names = zin.namelist()
            entries = {n: zin.read(n) for n in names}

        html_files = [n for n in names if re.search(r"\.x?html?$", n.lower())]

        modified: Dict[str, bytes] = {}
        for fname in html_files:
            html = entries[fname].decode("utf-8")
            # 跳过已有 guard 注释的（幂等）
            if "_epub_footnote_style_" in html:
                modified[fname] = html.encode("utf-8")
                continue
            result, n_replaced = self._convert_html(html, footnote_color, noteref_color)
            if result is not None:
                modified[fname] = result.encode("utf-8")
            if n_replaced > 0:
                total += 1
            else:
                skipped += 1

        # 更新所有 HTML 命名空间
        for fname in html_files:
            raw = modified.get(fname, entries[fname])
            html = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            html = self._ensure_epub_ns(html)
            modified[fname] = html.encode("utf-8")

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for fname in names:
                zout.writestr(fname, modified.get(fname, entries[fname]))

        return total, skipped

    def _convert_html(
        self,
        html: str,
        footnote_color: Optional[str],
        noteref_color: Optional[str],
    ) -> Tuple[Optional[str], int]:
        """将 span 替换为 sup+aside，并注入 <style> 块。"""
        footnotes: List[str] = []
        counter = [0]

        def make_replacement(match: re.Match) -> str:
            note_text = match.group(2)
            if not note_text or not note_text.strip():
                return match.group(0)
            note_text = self._escape_xml(note_text.strip())
            counter[0] += 1
            idx = counter[0]
            footnotes.append(
                '<aside id="fn%d" class="aside-fn" epub:type="footnote">\n'
                '        <p>%s</p>\n'
                '    </aside>' % (idx, note_text)
            )
            return '<sup><a class="fn-ref" epub:type="noteref" href="#fn%d">[%d]</a></sup>' % (idx, idx)

        new_html, n_replaced = _SPAN_PATTERN.subn(make_replacement, html)
        if n_replaced == 0:
            return None, 0

        # 注入 <style> 到 <head> 末尾
        style_block = _build_style_block(footnote_color, noteref_color)
        new_html = _HEAD_CLOSE_PATTERN.sub(style_block + r"\1", new_html, count=1)

        # 插入 aside 块到 </body> 之前
        if footnotes:
            aside_block = "\n" + "\n".join(footnotes) + "\n"
            new_html = new_html.replace("</body>", aside_block + "</body>", 1)

        return new_html, n_replaced

    @staticmethod
    def _escape_xml(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    @staticmethod
    def _ensure_epub_ns(html: str) -> str:
        def add_ns(m: re.Match) -> str:
            attrs = m.group(1)
            if "xmlns:epub" in attrs:
                return m.group(0)
            return '<html%s xmlns:epub="http://www.idpf.org/2007/ops">' % attrs

        return _HTML_TAG_PATTERN.sub(add_ns, html, count=1)


def run(
    input_path: str,
    output_dir: str,
    footnote_color: Optional[str] = None,
    noteref_color: Optional[str] = None,
) -> int:
    """供 plugin.py 调用的入口。"""
    if not input_path or not os.path.exists(input_path):
        return 1
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join(output_dir, base + "_converted.epub")
    total, skipped = SpanToFootnote().convert(
        input_path, out_path,
        footnote_color=footnote_color,
        noteref_color=noteref_color,
    )
    print("完成: %d 章含注释, %d 章无注释" % (total, skipped))
    return 0


if __name__ == "__main__":
    import sys

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    total, skipped = SpanToFootnote().convert(inp, out)
    print("完成: %d 章含注释, %d 章无注释" % (total, skipped))
