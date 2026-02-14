#!/bin/bash
# 跨平台 GUI 启动脚本（macOS/Linux）

# 尝试查找 Python 解释器
if [ -f ".venv/bin/python3" ]; then
    PYTHON=".venv/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
else
    PYTHON="python3"
fi

# 如果版本文件不存在，更新版本号
if [ ! -f "yt_dlp/version.py" ]; then
    echo "更新版本号..."
    python3 devscripts/update-version.py
fi

# 编译UI文件
if [ -f "ytdlp.ui" ]; then
    echo "编译UI文件..."
    pyuic5 ytdlp.ui -o gui/ytdlp_ui.py
fi

# 运行 GUI
exec "$PYTHON" gui/main.py "$@"
