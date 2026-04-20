# EPUB 工具箱

一站式 EPUB 电子书处理工具，从创建到优化全覆盖。

![Wails](https://img.shields.io/badge/Wails-v2.11-blue)
![Vue](https://img.shields.io/badge/Vue-3-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能特性

### TXT → EPUB

| 功能 | 说明 |
|------|------|
| 自动编码检测 | 自动识别 GBK / GB2312 / UTF-8 等编码 |
| 智能章节识别 | 按空行、标题层级、字数等多种规则切分章节 |
| 多级目录 | 支持生成嵌套的章-节目录结构 |
| 豆瓣封面搜索 | 根据书名自动从豆瓣获取封面图片 |
| 元数据编辑 | 标题、作者、出版社、语言、简介、版权信息 |

### EPUB 工具集

#### 文件处理

| 功能 | 说明 |
|------|------|
| **加密** | EPUB DRM 加密解密 |
| **字体加密** | 指定字体文件或书名字体进行混淆加密 |
| **解密** | 移除 DRM 加密 |
| **EPUB 重构** | 解包重打包，修复结构错误，清理冗余文件 |
| **更换封面** | 替换 EPUB 封面图片，输出文件加 `_cover` 后缀，不覆盖原文件 |

#### 格式转换

| 功能 | 说明 |
|------|------|
| 版本转换 | EPUB 2.0 ↔ 3.0 双向转换 |
| 简繁转换 | 简体↔繁体双向转换，基于词组级别精确转换 |
| 字体子集化 | 提取 EPUB 中实际使用的字形，减小字体文件体积 |
| OPF 查看 | 查看编辑 OPF 文档内容 |
| 合并 / 拆分 | 将多个 EPUB 合并为一个，或按章节点拆分 |

#### 图片处理

| 功能 | 说明 |
|------|------|
| 图片压缩 | JPEG/PNG 压缩，支持质量调节、PNG 转 JPG |
| 转 WebP | 图片转换为 WebP 格式 |
| WebP 转图片 | WebP 转换回 JPEG/PNG |
| 下载远程图片 | 将 EPUB 中的外链图片下载到本地 |

#### 文本增强

| 功能 | 说明 |
|------|------|
| 生僻字注音 | 为生僻字添加拼音注音 |
| 脚注转弹窗 | 正则匹配脚注内容转为弹出注释 |
| 注释转换 | 正则匹配文本转为注释形式 |
| 广告清理 | 按自定义正则规则批量清理广告内容 |

#### 平台适配

| 功能 | 说明 |
|------|------|
| 阅微→多看 | 脚注格式从阅微转换为多看格式 |
| 掌阅→多看 | 脚注格式从掌阅转换为多看格式 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 桌面框架 | [Go](https://go.dev/) + [Wails](https://wails.io/) |
| 前端 | Vue 3 + Tailwind CSS + Vite |
| 后端逻辑 | Python 3（插件化架构） |

## 快速开始

### 环境要求

- Go 1.18+
- Node.js 14+
- Python 3.9+
- Wails CLI: `go install github.com/wailsapp/wails/v2/cmd/wails@latest`

### 开发模式

```bash
# 克隆项目
git clone https://github.com/yourname/epub-gadget.git
cd epub-gadget

# 安装前端依赖
cd frontend && npm install && cd ..

# 启动开发服务器（同时运行前端和后端）
wails dev
```

### 构建发布

#### macOS

```bash
# 1. 编译 Python 后端
cd backend-py
pip install -r requirements.txt -q
pip install pyinstaller -q
python3 -m PyInstaller --onefile --name converter-backend main.py -y --clean

# 2. 复制到 backend-bin
cd ..
mkdir -p backend-bin
cp backend-py/dist/converter-backend backend-bin/

# 3. 构建 Wails 应用
wails build

# 4. 将后端二进制打包进 app（macOS 不会自动包含）
cp backend-bin/converter-backend build/bin/EPUB工具箱.app/Contents/Resources/backend-bin/
```

#### Windows

```bash
# 双击 build-windows.bat 或手动执行以下步骤
python -m PyInstaller --onefile --name converter-backend backend-py/main.py -y --clean
mkdir backend-bin 2>nul
copy backend-py\dist\converter-backend.exe backend-bin\converter-backend.exe
wails build -platform windows/amd64
```

构建产物位于 `build/bin/` 目录。

## 项目结构

```
epub-gadget/
├── main.go                    # Go 应用入口
├── app.go                     # Go App 类（文件对话框、系统交互）
├── wails.json                 # Wails 配置
├── build/                     # 构建资源
│   └── bin/                   # 输出目录
├── frontend/                  # Vue 前端
│   └── src/
│       ├── App.vue            # 根组件
│       └── components/
│           ├── Dashboard.vue      # 首页仪表盘
│           ├── Sidebar.vue        # 侧边导航
│           ├── Txt2Epub.vue       # TXT→EPUB
│           ├── MetadataEditor.vue # 元数据编辑器
│           └── EpubTools.vue      # EPUB 工具集
└── backend-py/                # Python 后端
    ├── main.py               # 插件调度器
    ├── core/                 # 核心模块
    │   └── plugin_base.py   # 插件基类
    └── plugins/              # 功能插件
        ├── txt_to_epub/       # TXT→EPUB 插件
        ├── epub_tool/         # EPUB 工具插件
        └── metadata_edit/     # 元数据编辑插件
```

## 架构说明

前端通过 Wails 绑定调用 Go 方法，Go 再通过子进程调用 Python 后端。Python 后端采用插件化架构，每个功能独立为插件。

```
Vue 前端
    ↓ Wails 绑定
Go App (app.go)
    ↓ 子进程 exec
Python 后端 (main.py)
    ↓ 插件调度
各功能插件
```

## 致谢

感谢以下用户和项目的贡献：

- [遥遥心航](https://tieba.baidu.com/home/main?id=tb.1.7f262ae1.5_dXQ2Jp0F0MH9YJtgM2Ew)
- [lgernier](https://github.com/lgernier)
- [fontObfuscator](https://github.com/solarhell/fontObfuscator)
- [epub_tool](https://github.com/cnwxi/epub_tool)

## License

MIT License
