# ============================================
# 万能视频下载器 - Windows 构建脚本
# ============================================

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "  万能视频下载器 - Windows 构建脚本" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

# 检查图标文件
if (-not (Test-Path "assets\app.ico")) {
    Write-ColorOutput "错误: 找不到图标文件 assets\app.ico" "Red"
    exit 1
}

Write-ColorOutput "[1/4] 清理旧的构建文件..." "Yellow"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Write-ColorOutput "✓ 清理完成" "Green"
Write-Host ""

Write-ColorOutput "[2/4] 安装依赖..." "Yellow"
pip install -e ".[default,gui,pyinstaller]" -q
Write-ColorOutput "✓ 依赖安装完成" "Green"
Write-Host ""

Write-ColorOutput "[3/4] 编译 UI 文件..." "Yellow"
if (Test-Path "ytdlp.ui") {
    pyuic5 ytdlp.ui -o gui/ytdlp_ui.py
    Write-ColorOutput "✓ UI 文件编译完成" "Green"
} else {
    Write-ColorOutput "✓ UI 文件不存在，跳过编译（使用已编译的版本）" "Green"
}
Write-Host ""

Write-ColorOutput "[4/4] 使用 PyInstaller 打包..." "Yellow"
pyinstaller yt-dlp-gui.spec
Write-ColorOutput "✓ PyInstaller 打包完成" "Green"
Write-Host ""

Write-ColorOutput "[5/5] 验证打包结果..." "Yellow"
if (Test-Path "dist\yt-dlp-gui\yt-dlp-gui.exe") {
    Write-ColorOutput "✓ 应用目录已生成" "Green"
} else {
    Write-ColorOutput "错误: 应用目录未生成" "Red"
    exit 1
}
Write-Host ""

# 显示构建结果
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "✓ 构建成功！" "Green"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

Write-ColorOutput "构建产物：" "Cyan"
Write-Host "  dist\yt-dlp-gui\           - 应用目录"
Write-Host "  dist\yt-dlp-gui\yt-dlp-gui.exe"
Write-Host ""

$dirSize = (Get-ChildItem -Path "dist\yt-dlp-gui" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-ColorOutput "文件大小：" "Cyan"
Write-Host ("  " + "{0:N2}" -f $dirSize + " MB")
Write-Host ""

Write-ColorOutput "✓ 可以直接运行 exe 文件！" "Green"
