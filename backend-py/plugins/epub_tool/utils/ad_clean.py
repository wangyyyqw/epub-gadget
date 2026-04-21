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
    def __init__(self, file_path, output_path, ad_patterns):
        if not os.path.exists(file_path):
            raise Exception("文件不存在")

        self.file_path = os.path.normpath(file_path)
        self.output_path = output_path
        self.ad_patterns = ad_patterns
        self.is_txt = self.file_path.lower().endswith('.txt')
        
        if output_path and os.path.exists(output_path):
            if os.path.isfile(output_path):
                raise Exception("输出路径不能是文件")
        else:
            output_path = os.path.dirname(file_path)
            
        self.output_path = os.path.normpath(output_path)
        
        if self.is_txt:
            self.file_write_path = os.path.join(
                self.output_path,
                os.path.basename(self.file_path).replace(".txt", "_cleaned.txt"),
            )
        else:
            self.file_write_path = os.path.join(
                self.output_path,
                os.path.basename(self.file_path).replace(".epub", "_cleaned.epub"),
            )
            self.epub = zipfile.ZipFile(file_path)
            self.target_epub = zipfile.ZipFile(
                self.file_write_path,
                "w",
                zipfile.ZIP_DEFLATED,
            )
        
        if os.path.exists(self.file_write_path):
            os.remove(self.file_write_path)

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

        if self.is_txt:
            # 处理 TXT 文件
            try:
                # 检测编码
                encoding = 'utf-8'
                try:
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    encoding = 'gbk'
                    with open(self.file_path, 'r', encoding='gbk', errors='ignore') as f:
                        content = f.read()
                
                # 应用所有广告净化规则
                modified = False
                for pattern, replacement in patterns:
                    if pattern.search(content):
                        content = pattern.sub(replacement, content)
                        modified = True
                
                # 写入结果
                with open(self.file_write_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.write(f"TXT 广告净化完成，输出路径: {self.file_write_path}")
                
            except Exception as e:
                logger.write(f"TXT 文件处理失败: {e}")
                traceback.print_exc()
        else:
            # 处理 EPUB 文件
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
            logger.write(f"EPUB 广告净化完成，输出路径: {self.file_write_path}")

    def close_file(self):
        if not self.is_txt:
            if hasattr(self, 'epub') and self.epub:
                self.epub.close()
            if hasattr(self, 'target_epub') and self.target_epub:
                self.target_epub.close()

    def fail_del_target(self):
        if self.file_write_path and os.path.exists(self.file_write_path):
            os.remove(self.file_write_path)
            logger.write(f"删除临时文件: {self.file_write_path}")

def run(file_path, output_path, ad_patterns_str):
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
        
    logger.write(f"\n正在进行广告净化: {file_path}")
    for pattern, replacement in ad_patterns:
        logger.write(f"规则: {pattern} -> {replacement}")
    
    tool = None
    try:
        tool = AdClean(file_path, output_path, ad_patterns)
        tool.process_file()
        return 0
    except Exception as e:
        logger.write(f"广告净化失败: {e}")
        traceback.print_exc()
        if tool:
            tool.close_file()
            tool.fail_del_target()
        return e