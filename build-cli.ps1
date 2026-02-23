# ============================================
# 万能视频下载器 - Windows 构建脚本
# ============================================

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "  yt-dlp - Windows 构建脚本" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

Write-ColorOutput "[1/4] 清理旧的构建文件..." "Yellow"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Write-ColorOutput "✓ 清理完成" "Green"
Write-Host ""

Write-ColorOutput "[2/4] 安装依赖..." "Yellow"
pip install -e ".[default,pyinstaller]" -q
Write-ColorOutput "✓ 依赖安装完成" "Green"
Write-Host ""

# 更新版本号
Write-ColorOutput "[4/5] 更新版本号..." "Yellow"
python3 devscripts/update-version.py
Write-ColorOutput "✓ 版本号更新完成" "Green"
Write-Host ""


Write-ColorOutput "[5/5] 使用 PyInstaller 打包..." "Yellow"
pyinstaller yt-dlp-cli.spec
Write-ColorOutput "✓ PyInstaller 打包完成" "Green"
Write-Host ""

Write-ColorOutput "[6/5] 验证打包结果..." "Yellow"
if (Test-Path "dist\yt-dlp\yt-dlp.exe") {
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
Write-Host "  dist\yt-dlp\yt-dlp.exe"
Write-Host ""

$dirSize = (Get-ChildItem -Path "dist\yt-dlp" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-ColorOutput "文件大小：" "Cyan"
Write-Host ("  " + "{0:N2}" -f $dirSize + " MB")
Write-Host ""

Write-ColorOutput "✓ 可以直接运行 exe 文件！" "Green"
