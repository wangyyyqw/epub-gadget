# EPUB 工具箱

一站式 EPUB 电子书处理工具，从创建到优化全覆盖。

![Wails](https://img.shields.io/badge/Wails-v2.11-blue)
![Vue](https://img.shields.io/badge/Vue-3-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能特性

### 核心功能

| 功能 | 说明 |
|------|------|
| **TXT → EPUB** | 纯文本转标准 EPUB，支持自动编码检测、智能章节识别、多级目录、豆瓣封面搜索 |
| **加密 / 解密** | EPUB DRM 加密解密，支持字体混淆加密 |
| **EPUB 重构** | 解包重打包，修复结构错误，清理冗余文件 |
| **图片处理** | 压缩图片、转换 WebP 格式、下载远程图片到本地 |
| **简繁转换** | 简体↔繁体双向转换，基于词组级别精确转换 |
| **注音 / 注释** | 生僻字拼音注音、正则匹配弹窗、脚注转弹窗 |

### 格式转换

- 版本转换（EPUB 2.0 ↔ 3.0）
- 字体子集化
- OPF 查看编辑
- 合并 / 拆分 EPUB

### 平台适配

- 阅微 → 多看 脚注格式转换
- 掌阅 → 多看 脚注格式转换

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

# 启动开发服务器
wails dev
```

### 构建发布

```bash
wails build
```

构建产物位于 `build/bin/` 目录。

## 项目结构

```
epub-gadget/
├── main.go                    # Go 应用入口
├── app.go                     # Go App 类（文件对话框、系统交互）
├── wails.json                 # Wails 配置
├── frontend/                  # Vue 前端
│   └── src/
│       ├── App.vue            # 根组件
│       └── components/        # UI 组件
│           ├── Dashboard.vue  # 首页仪表盘
│           ├── Sidebar.vue    # 侧边导航
│           ├── Txt2Epub.vue   # TXT→EPUB 转换
│           └── EpubTools.vue  # EPUB 工具集
└── backend-py/                # Python 后端
    ├── main.py               # 插件调度器
    ├── core/                 # 核心模块
    │   ├── plugin_base.py   # 插件基类
    │   └── utils.py          # 工具函数
    └── plugins/              # 功能插件
        ├── txt_to_epub/      # TXT→EPUB 插件
        └── epub_tool/        # EPUB 工具插件
```

## 架构说明

前端通过 Wails 绑定调用 Go 方法，Go 再通过子进程调用 Python 后端。Python 后端采用插件化架构，每个功能（加密、重构、转换等）独立为插件。

```
Vue 前端
    ↓ window.go.main.App.RunBackend()
Go App (app.go)
    ↓ exec.Command
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
