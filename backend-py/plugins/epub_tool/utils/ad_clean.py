import zipfile
import os
import re
import traceback

try:
    from ..log import logwriter
except ImportError:
    from .log import logwriter

logger = logwriter()

class AdClean:
    def __init__(self, epub_path, output_path, ad_patterns):
        if not os.path.exists(epub_path):
            raise Exception("EPUB文件不存在")

        self.epub_path = os.path.normpath(epub_path)
        self.output_path = output_path
        self.ad_patterns = ad_patterns
        self.epub = zipfile.ZipFile(epub_path)
        
        if output_path and os.path.exists(output_path):
            if os.path.isfile(output_path):
                raise Exception("输出路径不能是文件")
        else:
            output_path = os.path.dirname(epub_path)
            
        self.output_path = os.path.normpath(output_path)
        self.file_write_path = os.path.join(
            self.output_path,
            os.path.basename(self.epub_path).replace(".epub", "_cleaned.epub"),
        )
        
        if os.path.exists(self.file_write_path):
            os.remove(self.file_write_path)
            
        self.target_epub = zipfile.ZipFile(
            self.file_write_path,
            "w",
            zipfile.ZIP_DEFLATED,
        )

    def process_file(self):
        # 解析广告模式
        patterns = []
        for pattern_str, replacement in self.ad_patterns:
            try:
                # 优化正则
                optimized_pattern = pattern_str.replace("(.*)", "(.*?)")
                if optimized_pattern != pattern_str:
                    logger.write(f"自动优化正则: {pattern_str} -> {optimized_pattern}")
                
                pattern = re.compile(optimized_pattern, re.DOTALL)
                patterns.append((pattern, replacement))
            except re.error as e:
                logger.write(f"无效的正则表达式 '{pattern_str}': {e}")
                continue

        if not patterns:
            logger.write("没有有效的广告净化规则")
            return

        for item in self.epub.infolist():
            content = self.epub.read(item.filename)
            
            # 处理 HTML 文件
            if item.filename.lower().endswith(('.html', '.xhtml', '.htm')):
                try:
                    try:
                        text_content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        text_content = content.decode('gbk', errors='ignore')
                    
                    # 应用所有广告净化规则
                    modified = False
                    for pattern, replacement in patterns:
                        if pattern.search(text_content):
                            text_content = pattern.sub(replacement, text_content)
                            modified = True
                    
                    if modified:
                        self.target_epub.writestr(item.filename, text_content.encode('utf-8'))
                    else:
                        self.target_epub.writestr(item.filename, content)
                        
                except Exception as e:
                    logger.write(f"文件 {item.filename} 处理失败: {e}")
                    traceback.print_exc()
                    self.target_epub.writestr(item.filename, content)
            
            else:
                self.target_epub.writestr(item.filename, content)

        self.close_file()
        logger.write(f"广告净化完成，输出路径: {self.file_write_path}")

    def close_file(self):
        if self.epub:
            self.epub.close()
        if self.target_epub:
            self.target_epub.close()

    def fail_del_target(self):
        if self.file_write_path and os.path.exists(self.file_write_path):
            os.remove(self.file_write_path)
            logger.write(f"删除临时文件: {self.file_write_path}")

def run(epub_path, output_path, ad_patterns_str):
    if not ad_patterns_str:
        logger.write("错误：广告净化规则为空")
        return "patterns_empty"
        
    # 解析广告模式字符串
    # 格式: pattern1|||replacement1|||PATTERNS|||pattern2|||replacement2
    patterns_data = ad_patterns_str.split("|||PATTERNS|||")
    ad_patterns = []
    
    for pattern_data in patterns_data:
        parts = pattern_data.split("|||")
        if len(parts) >= 2:
            pattern = parts[0].strip()
            replacement = parts[1].strip()
            ad_patterns.append((pattern, replacement))
        else:
            logger.write(f"无效的广告净化规则格式: {pattern_data}")
    
    if not ad_patterns:
        logger.write("错误：没有有效的广告净化规则")
        return "patterns_empty"
        
    logger.write(f"\n正在进行广告净化: {epub_path}")
    for pattern, replacement in ad_patterns:
        logger.write(f"规则: {pattern} -> {replacement}")
    
    tool = None
    try:
        tool = AdClean(epub_path, output_path, ad_patterns)
        tool.process_file()
        return 0
    except Exception as e:
        logger.write(f"广告净化失败: {e}")
        traceback.print_exc()
        if tool:
            tool.close_file()
            tool.fail_del_target()
        return e