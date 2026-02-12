# 📋 万能视频下载器 - 跨平台打包指南

本文档详细说明如何从源码构建和打包万能视频下载器 GUI 应用程序。

---

## 📦 项目结构

```
/Volumes/work/projects/python/yt-dlp/
├── ytdlp.ui                  # Qt Designer 界面文件
├── yt-dlp-gui.spec           # PyInstaller 打包配置
├── gui/
│   ├── __init__.py
│   ├── main.py               # GUI 应用入口
│   └── main_window.py        # 主窗口逻辑
├── yt_dlp/                   # yt-dlp 核心库
├── run_gui.bat               # Windows 启动脚本
├── run_gui.sh                # macOS/Linux 启动脚本
└── requirements_gui.txt      # GUI 依赖
```

---

## 🔧 环境要求

| 组件 | 要求 |
|------|------|
| Python | 3.10+ |
| PyQt5 | >= 5.15.0, < 6 |
| PyInstaller | >= 6.17.0 |
| 操作系统 | Windows / macOS / Linux |

---

## 📝 安装步骤

### 1. 克隆项目并安装依赖

```bash
# 进入项目目录
cd /Volumes/work/projects/python/yt-dlp

# 使用 pip 安装依赖（推荐使用虚拟环境）
python -m venv venv

# Windows
venv\Scripts\activate
pip install -e .[default,gui,pyinstaller]

# macOS/Linux
source venv/bin/activate
pip install -e .[default,gui,pyinstaller]
```

### 2. 构建核心库（可选）

核心库在首次运行时会自动构建，如果需要手动构建：

```bash
# 生成 lazy extractors（加速启动）
make lazy-extractors

# 生成文档（可选）
make supportedsites
```

---

## 🚀 运行 GUI 应用

### Windows

```bash
# 方式 1: 使用 Python 直接运行
python gui/main.py

# 方式 2: 使用批处理脚本
run_gui.bat
```

### macOS/Linux

```bash
# 方式 1: 使用 Python 直接运行
python gui/main.py

# 方式 2: 使用 Shell 脚本
./run_gui.sh

# 如果没有执行权限
chmod +x run_gui.sh
./run_gui.sh
```

---

## 📦 打包流程

### 1. 确保依赖已安装

```bash
# 安装 PyInstaller
pip install -e .[pyinstaller]

# 或单独安装
pip install pyinstaller>=6.17.0
```

### 2. 执行打包

#### macOS

```bash
# 使用一键构建脚本（推荐）
./build.sh

# 或手动执行
pyinstaller yt-dlp-gui.spec
cd dist
mkdir -p 万能视频下载器.app/Contents/MacOS
mkdir -p 万能视频下载器.app/Contents/Resources
cat > 万能视频下载器.app/Contents/Info.plist << 'EOF'
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
cp dist/yt-dlp-gui 万能视频下载器.app/Contents/MacOS/
cp assets/app.icns 万能视频下载器.app/Contents/Resources/
cp ytdlp.ui 万能视频下载器.app/Contents/Resources/
chmod +x 万能视频下载器.app/Contents/MacOS/yt-dlp-gui
hdiutil create -volname "万能视频下载器" -srcfolder "万能视频下载器.app" -ov -format UDZO 万能视频下载器.dmg
```

#### Windows

```powershell
# 使用一键构建脚本（推荐）
.\build.ps1

# 或手动执行
pyinstaller yt-dlp-gui.spec
# Windows 会自动生成 .exe 文件，无需额外处理
```

#### Linux

```bash
# 手动执行
pyinstaller yt-dlp-gui.spec
# Linux 会生成独立的可执行文件
```

### 3. 查看打包结果

```bash
# 打包完成后的文件位置
ls -lh dist/
```

**打包输出：**
- macOS:
  - `dist/yt-dlp-gui` - 原始可执行文件
  - `dist/万能视频下载器.app` - macOS 应用包
  - `dist/万能视频下载器.dmg` - 分发用磁盘镜像
- Windows:
  - `dist/yt-dlp-gui.exe` - 可执行文件
- Linux:
  - `dist/yt-dlp-gui` - 可执行文件

---

## 🎨 使用 Qt Designer 修改界面

详细步骤请参考：[gui/README_QT_DESIGNER.md](gui/README_QT_DESIGNER.md)

### 快速修改流程

1. 打开 `ytdlp.ui` 文件（使用 Qt Designer）
2. 调整界面布局和控件
3. 保存文件
4. 运行 `python gui/main.py` 测试

---

## 🔍 PyInstaller 配置说明

### yt-dlp-gui.spec 配置要点

```python
# 入口文件
['gui/main.py']

# 包含的数据文件
datas=[
    ('ytdlp.ui', '.'),  # UI 文件打包到根目录
],

# 隐式导入
hiddenimports=[
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.uic',
    'yt_dlp',            # 核心 yt-dlp 库
],

# GUI 模式配置
console=False,          # 不显示控制台窗口
upx=True,              # 启用 UPX 压缩
```

### 自定义图标

准备图标文件并修改 spec 文件：

```python
icon='assets/app.ico',     # Windows: .ico 文件
# icon='assets/app.icns',   # macOS: .icns 文件
```

---

## 🌐 跨平台注意事项

### Windows

- 高 DPI 缩放：默认启用 DPI 感知
- UTF-8 编码：自动设置 UTF-8 模式
- 路径分隔符：自动适配 Windows 路径

### macOS

- 需要 macOS 10.15+（Catalina）
- 推荐使用 Python 3.10+
- 如需签名和公证，需配置 Apple 开发者账号

### Linux

- 兼容主流发行版（Ubuntu, Debian, CentOS 等）
- 需要安装系统依赖：
  ```bash
  sudo apt-get install libxcb-xinerama0  # Ubuntu/Debian
  ```

---

## 🧪 测试打包结果

### Windows

```bash
# 进入 dist 目录
cd dist

# 运行打包后的程序
yt-dlp-gui.exe
```

### macOS/Linux

```bash
# 进入 dist 目录
cd dist

# 运行打包后的程序
./yt-dlp-gui
```

---

## ⚠️ 常见问题

### 1. 打包后启动失败

**问题：** 提示找不到模块或文件

**解决：**
```bash
# 检查 hiddenimports 是否包含所有依赖
pyinstaller --onefile --hidden-import=yt_dlp gui/main.py

# 或者使用 --collect-all 收集整个包
pyinstaller --onefile --collect-all yt_dlp gui/main.py
```

### 2. macOS 无法打开应用

**问题：** 提示"已损坏"或无法打开

**解决：**
```bash
# 移除隔离属性
xattr -cr dist/yt-dlp-gui

# 或者临时允许（仅限测试）
sudo spctl --master-disable
```

### 3. Linux Qt 缺失依赖

**问题：** 提示 libxcb 错误

**解决：**
```bash
# Ubuntu/Debian
sudo apt-get install libxcb-xinerama0 libxcb-cursor0

# CentOS/RHEL
sudo yum install libxcb-xinerama
```

### 4. 打包文件过大

**问题：** 可执行文件体积过大（通常 > 100MB）

**原因：** 这是 PyInstaller 的正常行为，因为打包了：
- Python 解释器
- PyQt5 库（~50MB）
- yt-dlp 核心库（~20MB）
- 所有依赖项

**优化方案：**
- 使用 `--strip` 移除符号表
- 使用 `upx` 压缩（已默认启用）
- 考虑使用虚拟环境减小依赖

---

## 📦 发布分发

### Windows

```bash
# 打包为单文件
pyinstaller --onefile yt-dlp-gui.spec

# 或使用目录模式（更快启动）
pyinstaller yt-dlp-gui.spec
```

### macOS

```bash
# 打包为 .app 应用
pyinstaller yt-dlp-gui.spec

# 如需签名
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/万能视频下载器.app
```

### Linux

```bash
# 创建 AppImage（需要额外工具）
pyinstaller yt-dlp-gui.spec
cd dist
# 使用 appimagetool 创建 AppImage
```

---

## 📚 相关文档

- [Qt Designer 工作流程指南](gui/README_QT_DESIGNER.md)
- [yt-dlp 项目主页](https://github.com/yt-dlp/yt-dlp)
- [PyInstaller 官方文档](https://pyinstaller.org/en/stable/)

---

## 📄 许可证

本 GUI 应用遵循与 yt-dlp 相同的许可证：Unlicense
