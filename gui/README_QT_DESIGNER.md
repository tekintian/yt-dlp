# Qt Designer 工作流程指南

本指南说明如何使用 Qt Designer 维护 ytdlp.ui 文件。

---

## 📋 系统要求

| 组件 | 要求 |
|------|------|
| Python | 3.10+ |
| PyQt5 | >= 5.15.0, < 6 |
| Qt Designer | 5.15+ （可选，用于可视化编辑） |

---

## 📦 安装 PyQt5

### 使用 uv（项目默认包管理器）

```bash
uv pip install PyQt5
```

### 使用 pip

```bash
pip install PyQt5
```

### 从 pyproject.toml 安装

```bash
# 安装包含 GUI 依赖的完整环境
pip install -e .[default,gui]
```

---

## 🎨 Qt Designer 使用流程

### 1. 安装 Qt Designer

#### macOS

```bash
# 使用 Homebrew 安装
brew install --cask qt-creator

# 或安装独立的 Qt Designer
brew install --cask qt-designer
```

#### Windows

```bash
# 下载 Qt Creator（包含 Qt Designer）
# https://www.qt.io/download-qt-installer

# 或使用 winget
winget install TheQtCompany.QtCreator
```

#### Linux

```bash
# Ubuntu/Debian
sudo apt-get install qttools5-dev-tools qttools5-dev

# CentOS/RHEL
sudo yum install qt5-qttools-devel
```

---

### 2. 编辑界面文件

使用 Qt Designer 打开并编辑 `ytdlp.ui` 文件：

```bash
# 方式 1: 使用 Qt Designer（独立应用程序）
# 双击 ytdlp.ui 或通过 Qt Designer 打开

# 方式 2: 使用集成在 IDE 中的 Qt Designer
# 大多数 IDE（如 VSCode, PyCharm）支持 .ui 文件预览
```

---

### 3. 调整界面元素

在 Qt Designer 中可以进行的操作：

- **拖放组件：** 调整布局、添加新控件
- **修改属性：** 文本、尺寸、字体、颜色等
- **信号槽连接：** 建立控件与逻辑的关联（推荐在 Python 代码中连接）
- **布局调整：** 调整边距、间距、对齐方式

#### ⚠️ 重要：保持控件名称不变

以下控件的 `objectName` **不能**更改，因为它们在 `gui/main_window.py` 中被引用：

| 控件名称 | 用途 |
|---------|------|
| `videoUrl` | 视频链接输入框 |
| `downloadBtn` | 下载按钮 |
| `downloadStatus` | 下载状态显示 |
| `savePath` | 保存路径选择 |
| `tabWidget` | 标签页容器 |
| `urlLabel` | （已废弃，不再使用） |

---

### 4. 重新生成 Python 代码（可选）

如果需要生成独立的 UI Python 文件：

```bash
# 使用 PyQt5
python -m PyQt5.uic.pyuic ytdlp.ui -o gui/ytdlp_ui.py

# 或使用 pyuic5 命令（如果已安装）
pyuic5 ytdlp.ui -o gui/ytdlp_ui.py
```

> **注意：** 当前实现使用 `uic.loadUi()` 动态加载 `.ui` 文件，**不需要**每次修改都生成 Python 代码。这种方式更加方便，修改界面后直接运行即可。

---

## 🚀 运行应用

### 开发模式

```bash
# 方式 1: 直接运行 GUI
python gui/main.py

# 方式 2: 作为模块运行
python -m gui.main

# 方式 3: 使用启动脚本
# Windows
run_gui.bat

# macOS/Linux
./run_gui.sh
```

### 打包后测试

```bash
# 使用 PyInstaller 打包
pyinstaller yt-dlp-gui.spec

# 运行打包后的应用
# Windows
dist\yt-dlp-gui.exe

# macOS/Linux
./dist/yt-dlp-gui
```

---

## 📂 项目结构

```
/Volumes/work/projects/python/yt-dlp/
├── ytdlp.ui                  # Qt Designer 文件（在此编辑界面）
├── yt-dlp-gui.spec           # PyInstaller 打包配置
├── gui/
│   ├── __init__.py
│   ├── main.py               # GUI 应用入口
│   └── main_window.py        # 主窗口逻辑（在此实现功能）
└── yt_dlp/                   # yt-dlp 核心库
```

---

## 💻 开发注意事项

### 1. 界面调整

- ✅ **只在 Qt Designer 中修改** `ytdlp.ui`
- ❌ **不要修改** `main_window.py` 中的界面代码
- 🔄 如果需要改变行为，在 `main_window.py` 中添加逻辑

### 2. 功能实现

- 在 `gui/main_window.py` 中添加业务逻辑
- 保持界面（UI 文件）和逻辑（Python 代码）分离
- 使用 `self.ui` 访问 UI 元素

### 3. 保持控件名称

- 如果在 Qt Designer 中重命名控件，需要同步修改 `main_window.py` 中的引用
- 常用控件引用示例：
  ```python
  self.ui.videoUrl.text()           # 获取输入的 URL
  self.ui.downloadBtn.clicked.connect(...)  # 连接按钮点击信号
  self.ui.savePath.setText(...)      # 设置保存路径
  ```

### 4. 测试界面

- 修改 `.ui` 文件后，直接运行 `python gui/main.py` 查看效果
- 确保所有信号和槽连接正常
- 测试不同操作系统下的显示效果

---

## 🔄 推荐工作流程

```
1. 在 Qt Designer 中打开 ytdlp.ui
           ↓
2. 调整界面布局和控件
           ↓
3. 保存文件 (Ctrl+S / Cmd+S)
           ↓
4. 运行 python gui/main.py 测试
           ↓
5. 如需新功能，在 main_window.py 中添加代码
           ↓
6. 循环步骤 1-5
```

---

## ✅ 这种方式的优势

| 优势 | 说明 |
|------|------|
| ✅ 无需每次生成 Python 代码 | 直接修改 `.ui` 文件即可 |
| ✅ 界面和逻辑分离 | UI 文件专注布局，Python 代码专注逻辑 |
| ✅ Qt Designer 修改即时生效 | 保存后运行立即看到效果 |
| ✅ 易于团队协作 | 设计师可以独立修改界面 |
| ✅ 可视化调试 | 直观地看到界面效果 |

---

## 🔧 高级技巧

### 1. 使用样式表美化界面

在 `main_window.py` 中设置样式：

```python
# 设置全局样式表
self.setStyleSheet("""
    QMainWindow {
        background-color: #f5f5f5;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
    }
""")
```

### 2. 动态调整界面

在 `main_window.py` 中动态修改控件属性：

```python
# 动态修改按钮文本
self.ui.downloadBtn.setText('开始下载')

# 动态禁用控件
self.ui.downloadBtn.setEnabled(False)

# 动态显示/隐藏控件
self.ui.adLabel.setVisible(False)
```

### 3. 调试 UI 问题

```python
# 打印控件信息
print(f"videoUrl type: {type(self.ui.videoUrl)}")
print(f"videoUrl objectName: {self.ui.videoUrl.objectName()}")

# 查看所有子控件
for child in self.findChildren(QWidget):
    print(child.objectName())
```

---

## 📚 相关资源

- [Qt 官方文档](https://doc.qt.io/)
- [PyQt5 官方文档](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [GUI 跨平台打包指南](/Volumes/work/projects/python/yt-dlp/gui.md)
- [yt-dlp 项目主页](https://github.com/yt-dlp/yt-dlp)

---

## ❓ 常见问题

### Q1: 修改 .ui 文件后没有效果？

**A:** 确保保存了 `.ui` 文件，并重新运行应用。如果仍然没有效果，检查是否有编译错误。

### Q2: 如何添加新的控件？

**A:**
1. 在 Qt Designer 中拖放新控件到界面
2. 设置合适的 `objectName`
3. 在 `main_window.py` 中通过 `self.ui.objectName` 访问
4. 连接信号和槽（如果需要）

### Q3: 如何调整窗口大小？

**A:**
- 在 Qt Designer 中：选中主窗口 → 属性 → geometry → 设置 width 和 height
- 在代码中：`self.resize(800, 600)`
- 设置最小/最大尺寸：`self.setMinimumSize(400, 300)`

### Q4: 打包后 UI 文件找不到？

**A:** PyInstaller 配置中已包含 UI 文件：
```python
datas=[('ytdlp.ui', '.')],  # 确保 spec 文件中包含此行
```

---

## 📄 许可证

本 GUI 应用遵循与 yt-dlp 相同的许可证：Unlicense
