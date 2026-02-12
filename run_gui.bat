@echo off
REM Windows GUI 启动脚本

REM 尝试查找 Python 解释器
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

REM 运行 GUI
"%PYTHON%" gui\main.py %*
