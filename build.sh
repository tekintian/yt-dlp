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
echo -e "${BLUE}  万能视频下载器 - macOS 构建脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查图标文件
if [ ! -f "assets/app.icns" ]; then
    echo -e "${RED}错误: 找不到图标文件 assets/app.icns${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] 清理旧的构建文件...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ 清理完成${NC}"
echo ""

echo -e "${YELLOW}[2/6] 安装依赖...${NC}"
pip install -e ".[default,gui,pyinstaller]" -q
echo -e "${GREEN}✓ 依赖安装完成${NC}"
echo ""

echo -e "${YELLOW}[3/6] 使用 PyInstaller 打包...${NC}"
pyinstaller yt-dlp-gui.spec
echo -e "${GREEN}✓ PyInstaller 打包完成${NC}"
echo ""

echo -e "${YELLOW}[4/6] 创建 .app 包...${NC}"
cd dist
mkdir -p 万能视频下载器.app/Contents/MacOS
mkdir -p 万能视频下载器.app/Contents/Resources
cd ..
echo -e "${GREEN}✓ .app 包结构创建完成${NC}"
echo ""

echo -e "${YELLOW}[5/6] 生成 Info.plist...${NC}"
cat > dist/万能视频下载器.app/Contents/Info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>yt-dlp-gui</string>
    <key>CFBundleIconFile</key>
    <string>app.icns</string>
    <key>CFBundleIdentifier</key>
    <string>cn.tekin.ytdlp-gui</string>
    <key>CFBundleName</key>
    <string>万能视频下载器</string>
    <key>CFBundleDisplayName</key>
    <string>万能视频下载器</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
echo -e "${GREEN}✓ Info.plist 生成完成${NC}"
echo ""

echo -e "${YELLOW}[6/6] 复制文件、移除隔离属性并创建 DMG...${NC}"
cd dist
cp yt-dlp-gui 万能视频下载器.app/Contents/MacOS/
cp ../assets/app.icns 万能视频下载器.app/Contents/Resources/
cp ../ytdlp.ui 万能视频下载器.app/Contents/Resources/
chmod +x 万能视频下载器.app/Contents/MacOS/yt-dlp-gui

# 移除隔离属性
xattr -cr 万能视频下载器.app

# 创建 DMG（带 Applications 拖拽快捷方式）
TEMP_DMG_DIR="dmg_temp"
rm -rf "$TEMP_DMG_DIR"
mkdir -p "$TEMP_DMG_DIR"

# 复制 app 到临时文件夹
cp -R "万能视频下载器.app" "$TEMP_DMG_DIR/"

# 创建 Applications 符号链接（拖拽安装）
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# 创建 DMG
hdiutil create -volname "万能视频下载器" -srcfolder "$TEMP_DMG_DIR" -ov -format UDZO "万能视频下载器.dmg"

# 清理临时文件夹
rm -rf "$TEMP_DMG_DIR"

echo -e "${GREEN}✓ DMG 创建完成${NC}"

cd ..

# 移除隔离属性，避免首次打开闪退
echo -e "${YELLOW}移除隔离属性...${NC}"
xattr -cr dist/万能视频下载器.app
echo -e "${GREEN}✓ 隔离属性已移除${NC}"
echo ""

# 显示构建结果
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 构建成功！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "构建产物："
echo -e "  ${YELLOW}dist/yt-dlp-gui${NC}           - 原始可执行文件"
echo -e "  ${YELLOW}dist/万能视频下载器.app${NC}   - macOS 应用包"
echo -e "  ${YELLOW}dist/万能视频下载器.dmg${NC}   - 分发用 DMG 镜像"
echo ""
echo -e "${BLUE}文件大小：${NC}"
ls -lh dist/ | grep -E "(app|dmg|yt-dlp-gui$)" | awk '{print "  " $9 " - " $5}'
echo ""
echo -e "${GREEN}可以双击 DMG 文件进行分发！${NC}"
