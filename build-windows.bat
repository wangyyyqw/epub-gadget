@echo off
chcp 65001 >nul
echo ========================================
echo   EPUB 工具箱 Windows 一键打包脚本
echo ========================================
echo.

:: 检查依赖
where python >nul 2>&1 || (echo [错误] 未找到 python，请先安装 Python 3 && exit /b 1)
where go >nul 2>&1 || (echo [错误] 未找到 go，请先安装 Go && exit /b 1)
where wails >nul 2>&1 || (echo [错误] 未找到 wails CLI，请运行: go install github.com/wailsapp/wails/v2/cmd/wails@latest && exit /b 1)

:: Step 1: 用 PyInstaller 编译 Python 后端
echo [1/4] 编译 Python 后端...
cd backend-py
pip install -r requirements.txt -q
pip install pyinstaller -q
pyinstaller --onefile --name converter-backend main.py -y --clean
if errorlevel 1 (echo [错误] PyInstaller 编译失败 && exit /b 1)
cd ..

:: Step 2: 复制后端到 embed 目录（供 go:embed 嵌入）
echo [2/4] 嵌入后端到 Go 程序...
if not exist backend-embed mkdir backend-embed
copy /Y backend-py\dist\converter-backend.exe backend-embed\converter-backend.exe

:: Step 3: 复制到 backend-bin（备用路径）
echo [3/4] 复制后端到 backend-bin...
if not exist backend-bin mkdir backend-bin
copy /Y backend-py\dist\converter-backend.exe backend-bin\converter-backend.exe

:: Step 4: Wails 编译
echo [4/4] 编译 Wails 应用...
wails build -platform windows/amd64
if errorlevel 1 (echo [错误] Wails 编译失败 && exit /b 1)

:: 清理 embed 目录中的 exe（不再需要，避免提交到 git）
del /q backend-embed\converter-backend.exe

echo.
echo ========================================
echo   打包完成！发布目录: build\bin\EPUB工具箱.exe
echo   后端已嵌入 exe，首次运行自动解压。
echo ========================================
