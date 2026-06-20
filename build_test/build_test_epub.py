# -*- coding: utf-8 -*-
"""构造一个最小的 EPUB 用于测试 span_to_footnote。"""

import os
import shutil
import zipfile

# 清理旧文件
for p in ("build_test/test_in.epub", "build_test/test_out.epub"):
    if os.path.exists(p):
        os.remove(p)
os.makedirs("build_test", exist_ok=True)

container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

content_opf = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:00000000-0000-0000-0000-000000000001</dc:identifier>
    <dc:title>测试图书</dc:title>
    <dc:language>zh-CN</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="css"  href="style.css" media-type="text/css"/>
  </manifest>
  <spine>
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
  </spine>
</package>
"""

# 注意：故意不带 xmlns:epub，验证工具自动补上
ch1 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>第一章</title><link rel="stylesheet" href="style.css"/></head>
<body>
<h2>1</h2>
<p>整个白天都只是呆呆地看着电视。</p>
<p>三郎不时会看几眼电影和电视<span class="reader js_readerFooterNote" data-wr-footernote="三郎对电影和电视的态度是“不时看几眼”，暗示他并非主动选择内容，而是被动消磨时间。"></span>，不过大部分都是以前看过的<span class="reader js_readerFooterNote" data-wr-footernote="“以前看过的”说明设施内播放内容重复率高，侧面反映娱乐资源更新缓慢。"></span>，所以并没有用心去看。至于体育比赛<span class="reader js_readerFooterNote" data-wr-footernote="日本养老院常播放体育比赛，尤其是棒球或相扑，以迎合老年男性的兴趣。"></span>，他原本就没兴趣<span class="reader js_readerFooterNote" data-wr-footernote="三郎对体育“没兴趣”，与其他老人形成对比，突显他的疏离感。"></span>，而且从一开始就不相信那是实况转播<span class="reader js_readerFooterNote" data-wr-footernote="“不相信实况转播”反映三郎对设施内娱乐真实性的根本怀疑。"></span>。就算<span class="reader js_readerFooterNote" data-wr-footernote="“不至于花费那么多心思”暗示三郎认为养老院不会为体育比赛投入太多制作成本。"></span>。</p>
<p>这是只有 reader 的 span<span class="reader" data-wr-footernote="只包含 reader class 应该被识别"></span>，以及无意义的空注释<span class="reader js_readerFooterNote" data-wr-footernote="   "></span>。</p>
</body>
</html>
"""

ch2 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>第二章</title><link rel="stylesheet" href="style.css"/></head>
<body>
<h2>2</h2>
<p>这是第二章，开头的注释<span class="reader js_readerFooterNote" data-wr-footernote="第二章第 1 条注释"></span>，以及第二章的<span class="js_readerFooterNote" data-wr-footernote="第二章第 2 条注释"></span>。</p>
</body>
</html>
"""

style_css = """body { font-family: serif; }
"""

src = "build_test/test_in.epub"
dst = "build_test/test_out.epub"

with zipfile.ZipFile(src, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
    z.writestr("META-INF/container.xml", container_xml)
    z.writestr("OEBPS/content.opf", content_opf)
    z.writestr("OEBPS/ch1.xhtml", ch1)
    z.writestr("OEBPS/ch2.xhtml", ch2)
    z.writestr("OEBPS/style.css", style_css)

print(f"created: {src}")
