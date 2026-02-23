#!/usr/bin/env python3

# Execute with
# $ python3 -m yt_dlp

import sys
import os.path

if __package__ is None and not getattr(sys, 'frozen', False):
    # direct call of __main__.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

def get_version():
    # 直接读取版本文件，不导入任何模块
    try:
        if getattr(sys, 'frozen', False):
            # 打包后的应用 - version.py 在 _MEIPASS 内
            meipass = getattr(sys, '_MEIPASS', '')
            version_file = os.path.join(meipass, 'yt_dlp', 'version.py')
        else:
            # 正常 Python 运行
            path = os.path.realpath(os.path.abspath(__file__))
            package_dir = os.path.dirname(os.path.dirname(path))
            version_file = os.path.join(package_dir, 'yt_dlp', 'version.py')

        with open(version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    # 提取版本号
                    version = line.split('=')[1].strip().strip("'\"")
                    print(version)
                    sys.exit(0)
    except Exception as e:
        # 降级到导入方式
        if __package__ is None and not getattr(sys, 'frozen', False):
            path = os.path.realpath(os.path.abspath(__file__))
            sys.path.insert(0, os.path.dirname(os.path.dirname(path)))
        from yt_dlp.version import __version__
        print(__version__)
        sys.exit(0)


if __name__ == '__main__':
    # 快速处理 --version 选项，避免加载整个 yt_dlp 模块
    if len(sys.argv) > 1 and sys.argv[1] in ('--version', '-v'):
        get_version()
    else:
        import yt_dlp
        yt_dlp.main()
