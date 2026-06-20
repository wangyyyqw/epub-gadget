# 更新日志

## v1.0.5

### 优化改进
- 脚注样式改用 inline `<style>` 内嵌块注入，弃用外部 CSS（兼容更多阅读器）

## v1.0.4

### 新增功能
- 新增「弹窗→脚注」功能：将阅微书城的 `<span class="reader js_readerFooterNote">` 弹窗注释批量转换为多看风格的 `<sup><a epub:type="noteref">[N]</a></sup>` 上标引用，注释内容统一放在章节末尾的 `<aside epub:type="footnote">` 块中；每个章节独立从 [1] 开始编号。

### 优化改进
- TXT → EPUB 章节扫描支持超大文件（修复 64KB 行长限制）
- 超时处理使用 `time.Timer` 替代 `time.After`，避免 timer leak
- 广告净化正则引擎改为逐字符解析，正确处理 `.*?`、转义符和字符类

### 修复
- 修复 TXT 扫描模式传入源文件路径导致权限错误的问题
- 修复 EPUB 拆分点无效时静默跳过、导致分割结果错误的问题
- 修复 EPUB 拆分/合并 nav 文档中书名无 XML 转义的问题（特殊字符可能破坏文档）
- 修复广告净化正则自动优化语义错误的问题
- 修复 EpubTools 广告净化规则移除时 `adPatternIdCounter` 计数器不同步导致删除错误规则的问题
- 修复超时 Kill 后未调用 `Wait()` 产生僵尸进程的问题

### 移除
- 移除豆瓣封面搜索功能（依赖不稳定且存在版权风险）
- 删除 `douban_cover.py` 文件

## v1.0.3

### 新增功能
- 新增「掌阅→多看」脚注转换功能（独立模块，支持掌阅 inline aside 格式）

### 优化改进
- 重构「阅微→多看」模块为模块化函数，提升可维护性
- TXT → EPUB 输出标准 EPUB 2.0 格式（移除 nav.xhtml、OPF 降级为 version 2.0）
- TXT → EPUB 首行缩进改用 CSS `text-indent: 2em`，不再插入全角空格字符
- 源文本原有的首行全角空格在转换时自动去除

### 修复
- 修复 note.png 注入后 OPF manifest 路径不正确的问题（改用 `posixpath.relpath` 计算相对路径）
- 修复掌阅脚注 `<img>` src 未替换为 note.png 的问题
- 修复图片目录检测逻辑，支持不同 EPUB 结构的 images 目录

## v1.0.2

### 修复
- 修复章节分割正则表达式被 `:` 截断的问题（如 `(?:...)` 非捕获组）
- 修复 Windows 下中文正则参数因 GBK 编码导致乱码的问题（改用临时文件传递 UTF-8 参数）
