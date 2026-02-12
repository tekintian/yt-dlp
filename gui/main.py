#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for yt-dlp GUI application
"""

import sys

# 确保使用 UTF-8
if sys.platform.startswith('win'):
    import codecs
    if sys.stdout and hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    if sys.stderr and hasattr(sys.stderr, 'detach'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
