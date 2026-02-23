#!/bin/bash

# ============================================
# 万能视频下载器 - macOS 构建脚本
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  yt-dlp - macOS 构建脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}[1/6] 清理旧的构建文件...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ 清理完成${NC}"
echo ""

echo -e "${YELLOW}[2/6] 安装依赖...${NC}"
pip install -e ".[default,pyinstaller]" -q
echo -e "${GREEN}✓ 依赖安装完成${NC}"
echo ""

# 更新版本号
echo -e "${YELLOW}[4/5] 更新版本号...${NC}"
python3 devscripts/update-version.py
echo -e "${GREEN}✓ 版本号更新完成${NC}"
echo ""

echo -e "${YELLOW}[5/5] 使用 PyInstaller 打包...${NC}"
pyinstaller yt-dlp-cli.spec
echo -e "${GREEN}✓ PyInstaller 打包完成${NC}"
echo ""

# 显示构建结果
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 构建成功！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "构建产物："
echo -e "  ${YELLOW}dist/yt-dlp ${NC}         - 应用程序（可运行）"echo ""
echo -e "${BLUE}文件大小：${NC}"
ls -lh dist/yt-dlp | awk '{print $5}'
echo -e "${GREEN}请将 dist/yt-dlp 复制到 /usr/local/bin 目录下即可使用！${NC}"