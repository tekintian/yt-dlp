"""
Main window logic for yt-dlp GUI
This file contains the main application logic and should NOT be edited by Qt Designer.
UI definitions are in gui/ytdlp_ui.py (generated from ytdlp.ui)
"""

import os
import sys
import datetime
import platform
import webbrowser
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QApplication
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap

# 导入预编译的 UI
from gui import ytdlp_ui

# 延迟导入 yt_dlp 以加快启动速度
_yt_dlp_version = None

def get_ytdlp_version():
    """延迟获取 yt_dlp 版本"""
    global _yt_dlp_version
    if _yt_dlp_version is None:
        from yt_dlp.version import __version__
        _yt_dlp_version = __version__
    return _yt_dlp_version

YTDLP_VERSION = get_ytdlp_version()


class DownloadWorker(QThread):
    """Worker thread for downloading videos to avoid blocking the UI"""
    progress = pyqtSignal(dict)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, options=None):
        super().__init__()
        self.url = url
        self.options = options or {}
        self._cancelled = False

    def run(self):
        import yt_dlp

        def progress_hook(d):
            if self._cancelled:
                raise Exception('Download cancelled')
            self.progress.emit(d)

        ydl_opts = {
            **self.options,
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit()
        except Exception as e:
            if self._cancelled:
                self.error.emit('Download cancelled')
            else:
                self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True


class MainWindow(QMainWindow, ytdlp_ui.Ui_MainWindow):
    def __init__(self):
        super().__init__()

        # Setup UI from pre-compiled code (much faster than uic.loadUi)
        self.setupUi(self)

        # Setup platform-specific settings (must be after UI is loaded)
        self._setup_platform()

        # Reorder tabs: Video Download, Help, Settings
        self.tabWidget.removeTab(2)  # Remove helpTab (currently at index 2)
        self.tabWidget.insertTab(1, self.helpTab, "使用帮助")  # Insert at index 1

        # Initialize download path
        self.save_path = self._get_default_download_path()
        self.pathEdit.setText(self.save_path)

        # Download worker
        self.download_worker = None

        # Connect signals
        self.downloadBtn.clicked.connect(self.start_download)
        self.browsePathBtn.clicked.connect(self.browse_save_path)
        self.cancelBtn.clicked.connect(self.cancel_download)
        self.clearUrlBtn.clicked.connect(lambda: self.videoUrl.clear())
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.show_about)

        # Connect advertisement and contact signals
        self.websiteBtn.clicked.connect(lambda: webbrowser.open('https://dev.tekin.cn'))
        self.contactPageBtn.clicked.connect(lambda: webbrowser.open('https://dev.tekin.cn/contactus.html'))
        self.actionContact.triggered.connect(lambda: webbrowser.open('https://dev.tekin.cn/contactus.html'))

        # Load QR codes asynchronously (don't block startup)
        # Moved to background loading after window is shown
        self._qr_codes_loaded = False

        # Set version info in help tab
        self.versionLabel.setText(f'当前版本：{YTDLP_VERSION}')

        # Set window title
        self.setWindowTitle('万能视频下载器')

        # Load QR codes after window is shown to avoid blocking startup
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.load_qr_codes_async)

        # Apply global styles to ensure consistent button appearance
        self.setStyleSheet("""
            QPushButton#downloadBtn {
                background-color: #4CAF50 !important;
                color: white !important;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#downloadBtn:hover {
                background-color: #45a049 !important;
            }
            QPushButton#downloadBtn:pressed {
                background-color: #3d8b40 !important;
            }
            QPushButton#downloadBtn:disabled {
                background-color: #cccccc !important;
                color: #888888 !important;
            }
        """)

        # Log initialization
        self.log('yt-dlp GUI 已启动')
        self.log(f'yt-dlp 版本: {YTDLP_VERSION}')

    def log(self, message):
        """Add message to log text area"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.logText.append(f'[{timestamp}] {message}')
        # Scroll to bottom
        scrollbar = self.logText.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def load_qr_codes_async(self):
        """Load QQ and WeChat QR codes asynchronously in background"""
        import urllib.request
        from urllib.error import URLError, HTTPError
        from PyQt5.QtCore import QThread, pyqtSignal

        class QRCodeLoader(QThread):
            finished = pyqtSignal(object, str)
            wechat_finished = pyqtSignal(object, str)

            def __init__(self):
                super().__init__()

            def run(self):
                # Load QQ QR code
                try:
                    with urllib.request.urlopen('https://dev.tekin.cn/storage/qr/qq.jpg', timeout=5) as response:
                        image_data = response.read()
                    self.finished.emit(image_data, 'success')
                except Exception as e:
                    self.finished.emit(None, str(e))

                # Load WeChat QR code
                try:
                    with urllib.request.urlopen('https://dev.tekin.cn/storage/qr/mpqr.jpg', timeout=5) as response:
                        image_data = response.read()
                    self.wechat_finished.emit(image_data, 'success')
                except Exception as e:
                    self.wechat_finished.emit(None, str(e))

        # Start loading in background
        self.qr_loader = QRCodeLoader()
        self.qr_loader.finished.connect(self._on_qq_qr_loaded)
        self.qr_loader.wechat_finished.connect(self._on_wechat_qr_loaded)
        self.qr_loader.start()

    def _on_qq_qr_loaded(self, image_data, status):
        """Handle QQ QR code loaded"""
        if image_data and status == 'success':
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                self.qqQrLabel.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.qqQrLabel.setText('加载失败')
        else:
            self.qqQrLabel.setText('加载失败')

    def _on_wechat_qr_loaded(self, image_data, status):
        """Handle WeChat QR code loaded"""
        if image_data and status == 'success':
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                self.wechatQrLabel.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.wechatQrLabel.setText('加载失败')
        else:
            self.wechatQrLabel.setText('加载失败')

    def load_qr_codes(self):
        """Legacy method for backward compatibility, now uses async loading"""
        pass

    def browse_save_path(self):
        """Open dialog to select save directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            '选择保存目录',
            self.save_path
        )
        if path:
            if not self._check_write_permission(path):
                QMessageBox.warning(
                    self,
                    '警告',
                    f'所选路径没有写入权限:\n{path}'
                )
                return
            self.save_path = path
            self.pathEdit.setText(self.save_path)
            self.log(f'保存路径已设置为: {self.save_path}')

    def get_format_options(self):
        """Get format selection based on combo box"""
        format_text = self.formatCombo.currentText()
        format_map = {
            '最佳质量': 'bestvideo+bestaudio/best',
            '最佳视频 + 音频': 'bestvideo+bestaudio/best',
            '仅音频': 'bestaudio',
            '仅音频 (mp3)': 'bestaudio/best',
            '仅音频 (m4a)': 'bestaudio[ext=m4a]/bestaudio',
            '仅视频 (mp4)': 'bestvideo[ext=mp4]/bestvideo',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        }
        return format_map.get(format_text, 'bestvideo+bestaudio/best')

    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        import shutil
        return shutil.which('ffmpeg') is not None

    def start_download(self):
        """Start the download process"""
        url = self.videoUrl.text().strip()

        if not url:
            QMessageBox.warning(self, '警告', '请输入视频网址')
            return

        if self.download_worker and self.download_worker.isRunning():
            QMessageBox.warning(self, '提示', '下载正在进行中')
            return

        # Check if FFmpeg is installed for video+audio merging
        if not self.check_ffmpeg():
            QMessageBox.warning(
                self,
                '缺少 FFmpeg',
                '检测到系统未安装 FFmpeg。\n\n'
                '下载高清视频需要 FFmpeg 来合并视频和音频流。\n\n'
                '安装方法：\n'
                'macOS: brew install ffmpeg\n'
                'Windows: 下载 https://ffmpeg.org/download.html 并添加到 PATH\n'
                'Linux: sudo apt install ffmpeg\n\n'
                '如果不安装 FFmpeg，只能下载预合并的格式（可能画质较低）。'
            )
            return

        # Show progress group
        self.progressGroup.setVisible(True)

        # Clear previous logs
        self.logText.clear()
        self.log('=' * 50)
        self.log(f'开始下载: {url}')
        self.log('=' * 50)

        # Configure download options
        # 使用 outtmpl 参数为每个视频创建单独的目录
        ydl_opts = {
            'outtmpl': os.path.join(self.save_path, '%(title)s', '%(title)s.%(ext)s'),
            'format': self.get_format_options(),
        }

        # Add subtitle option
        if self.subtitleCheck.isChecked():
            ydl_opts['writesubtitles'] = True
            ydl_opts['subtitleslangs'] = ['all']
            ydl_opts['writeautomaticsub'] = True
            self.log('字幕下载: 启用')

        # Add thumbnail option
        if self.thumbnailCheck.isChecked():
            ydl_opts['writethumbnail'] = True
            self.log('缩略图下载: 启用')

        # Add metadata option
        if self.metadataCheck.isChecked():
            ydl_opts['addmetadata'] = True
            self.log('元数据嵌入: 启用')

        # Handle audio-only formats
        format_text = self.formatCombo.currentText()
        if 'mp3' in format_text:
            ydl_opts['extractaudio'] = True
            ydl_opts['audioformat'] = 'mp3'
            ydl_opts['audioquality'] = '192'
            self.log('音频格式: MP3 192kbps')
        elif 'm4a' in format_text:
            ydl_opts['extractaudio'] = True
            ydl_opts['audioformat'] = 'm4a'
            self.log('音频格式: M4A')

        # Create and start worker
        self.download_worker = DownloadWorker(url, ydl_opts)
        self.download_worker.progress.connect(self.update_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)

        # Update UI state
        self.downloadBtn.setEnabled(False)
        self.downloadBtn.setText('下载中...')
        self.cancelBtn.setEnabled(True)
        self.videoUrl.setEnabled(False)
        self.progressLabel.setText('准备中...')

        self.download_worker.start()

    def cancel_download(self):
        """Cancel the current download"""
        if self.download_worker and self.download_worker.isRunning():
            self.log('正在取消下载...')
            self.download_worker.cancel()

    def update_progress(self, data):
        """Update progress bar based on download status"""
        status = data.get('status')

        if status == 'downloading':
            total_bytes = data.get('total_bytes') or data.get('total_bytes_estimate')
            downloaded_bytes = data.get('downloaded_bytes', 0)

            if total_bytes and total_bytes > 0:
                progress = int((downloaded_bytes / total_bytes) * 100)
                self.downloadStatus.setValue(progress)
                self.downloadStatus.setRange(0, 100)

            # Update progress label
            speed = data.get('_speed_str', '')
            eta = data.get('_eta_str', '')
            downloaded_size = data.get('_total_bytes_str', '')

            progress_text = f'{downloaded_size} | 速度: {speed} | 剩余: {eta}'
            self.progressLabel.setText(progress_text)

            # Update status bar
            self.statusbar.showMessage(f'下载中... {progress_text}')

        elif status == 'finished':
            self.downloadStatus.setValue(100)
            self.progressLabel.setText('下载完成')
            self.statusbar.showMessage('下载完成！')
            self.log('✓ 下载完成')

        elif status == 'error':
            self.downloadStatus.setValue(0)
            self.progressLabel.setText('下载失败')
            self.statusbar.showMessage('下载失败')

    def on_download_finished(self):
        """Handle download completion"""
        self.downloadBtn.setEnabled(True)
        self.downloadBtn.setText('开始下载')
        self.cancelBtn.setEnabled(False)
        self.videoUrl.setEnabled(True)
        self.progressLabel.setText('就绪')

        # Custom message box with "Open Download Folder" button
        msg = QMessageBox(self)
        msg.setWindowTitle('完成')
        msg.setText('视频下载完成！')
        msg.setIcon(QMessageBox.Information)

        # Add custom button to open download folder
        open_folder_btn = msg.addButton('打开下载目录', QMessageBox.ActionRole)
        msg.addButton('确定', QMessageBox.AcceptRole)

        msg.exec_()

        # Check if user clicked "Open Download Folder"
        if msg.clickedButton() == open_folder_btn:
            self.open_download_folder()

    def open_download_folder(self):
        """Open the download folder in system file manager"""
        import subprocess
        import platform

        path = self.save_path
        if not os.path.exists(path):
            path = os.path.dirname(path)

        system = platform.system()
        try:
            if system == 'Windows':
                os.startfile(path)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', path])
            elif system == 'Linux':
                subprocess.run(['xdg-open', path])
        except Exception as e:
            self.log(f'无法打开目录: {str(e)}')
            QMessageBox.warning(self, '错误', f'无法打开下载目录:\n{str(e)}')

    def on_download_error(self, error_msg):
        """Handle download error"""
        self.downloadBtn.setEnabled(True)
        self.downloadBtn.setText('开始下载')
        self.cancelBtn.setEnabled(False)
        self.videoUrl.setEnabled(True)
        self.downloadStatus.setValue(0)
        self.progressLabel.setText('就绪')
        self.statusbar.showMessage('')
        self.log(f'✗ 错误: {error_msg}')

        # Keep progress group visible to show error
        QMessageBox.critical(self, '错误', f'下载失败:\n{error_msg}')

    def show_about(self):
        """Show about dialog"""
        about_text = f"""🎬 万能视频下载器

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
版本：{YTDLP_VERSION}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

一款优雅、强大的跨平台视频下载工具
支持全球 1000+ 主流视频网站与流媒体平台

┌─────────────────────────────────────┐
│  ✨ 核心特性                      │
├─────────────────────────────────────┤
│  🎥 多格式高清下载               │
│  📹 4K/1080P 原画支持           │
│  🎬 字幕与缩略图自动提取          │
│  🎵 音频单独提取 (MP3/M4A)       │
│  ℹ️  元数据智能嵌入               │
│  ⚡ 多线程高速下载               │
│  🌐 全球站点支持                 │
└─────────────────────────────────────┘

支持平台
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YouTube · Bilibili · 优酷 · 爱奇艺
抖音 · 快手 · TikTok · Instagram
Twitter/X · Facebook · Twitch
及更多 1000+ 网站...

版权所有 © 2026 Tekin.cn
技术支持：QQ 932256355 | dev.tekin.cn

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
让视频下载变得简单而优雅
"""
        QMessageBox.about(self, '关于', about_text)

    def _setup_platform(self):
        """Setup platform-specific settings"""
        system = platform.system()

        if system == 'Windows':
            # Windows specific settings
            self.log('运行平台: Windows')
            try:
                QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
                QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            except AttributeError:
                pass
        elif system == 'Darwin':
            # macOS specific settings
            self.log('运行平台: macOS')
        elif system == 'Linux':
            # Linux specific settings
            self.log('运行平台: Linux')

        self.log(f'Python 版本: {sys.version.split()[0]}')

    def _find_ui_file(self):
        """Find ytdlp.ui in various locations"""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'ytdlp.ui'),  # Development
            os.path.join(os.path.dirname(sys.executable), 'ytdlp.ui'),   # PyInstaller frozen
            os.path.join(getattr(sys, '_MEIPASS', ''), 'ytdlp.ui'),      # PyInstaller temp
            'ytdlp.ui',                                                   # Current dir
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        return None

    def _get_default_download_path(self):
        """Get platform-specific default download path"""
        if platform.system() == 'Windows':
            try:
                import ctypes
                from ctypes import wintypes

                # Get real Downloads folder path from Windows
                CSIDL_PERSONAL = 5  # My Documents
                SHGFP_TYPE_CURRENT = 0

                buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(
                    0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf
                )
                downloads_path = os.path.join(buf.value, 'Downloads')
                if os.path.exists(downloads_path):
                    return downloads_path
            except Exception:
                pass

        # Fallback to ~/Downloads
        from pathlib import Path
        path = Path.home() / 'Downloads'
        if path.exists():
            return str(path)

        # Last resort: home directory
        return str(Path.home())

    def _check_write_permission(self, path):
        """Check if path is writable"""
        try:
            test_file = os.path.join(path, '.yt_dlp_write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except Exception as e:
            self.log(f'路径不可写: {str(e)}')
            return False

