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
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
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
                raise Exception('下载已取消')
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
                self.error.emit('下载已取消')
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
        # self.tabWidget.removeTab(2)  # Remove helpTab (currently at index 2)
        # self.tabWidget.insertTab(1, self.helpTab, "使用帮助")  # Insert at index 1

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

        # FFmpeg signals
        self.browseFfmpegBtn.clicked.connect(self.browse_ffmpeg_path)
        self.downloadFfmpegBtn.clicked.connect(self.download_ffmpeg_auto)

        # Settings buttons signals
        self.saveSettingsBtn.clicked.connect(self.save_settings)
        self.resetSettingsBtn.clicked.connect(self.reset_settings)

        # Initialize FFmpeg path in settings
        self._init_ffmpeg_path()

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

        # Enable mouse tracking for QR code labels to enable click events
        self.qqQrLabel.mousePressEvent = lambda event: self._on_qr_code_clicked('qq')
        self.wechatQrLabel.mousePressEvent = lambda event: self._on_qr_code_clicked('wechat')

        # Set cursor to hand pointer to indicate clickable
        self.qqQrLabel.setCursor(Qt.PointingHandCursor)
        self.wechatQrLabel.setCursor(Qt.PointingHandCursor)

        # Store QR code URLs and cache info
        self.qqQrUrl = 'https://dev.tekin.cn/storage/qr/qq.jpg'
        self.wechatQrUrl = 'https://dev.tekin.cn/storage/qr/mpqr.jpg'
        self.qr_cache_days = 7  # 缓存7天

        # Load QR codes from cache or URL
        QTimer.singleShot(100, self.load_qr_codes_with_cache)

        # Enable mouse tracking for QR code labels to enable click events
        self.qqQrLabel.mousePressEvent = lambda event: self._on_qr_code_clicked('qq')
        self.wechatQrLabel.mousePressEvent = lambda event: self._on_qr_code_clicked('wechat')

        # Set cursor to hand pointer to indicate clickable
        self.qqQrLabel.setCursor(Qt.PointingHandCursor)
        self.wechatQrLabel.setCursor(Qt.PointingHandCursor)

        # Load QR codes after window is shown to avoid blocking startup
        QTimer.singleShot(100, self.load_qr_codes_with_cache)

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

    def _get_cache_dir(self):
        """Get cache directory for QR codes"""
        from pathlib import Path
        cache_dir = Path.home() / '.ytdlp-gui' / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _get_cache_file(self, qr_type):
        """Get cache file path for specific QR code"""
        cache_dir = self._get_cache_dir()
        if qr_type == 'qq':
            return cache_dir / 'qq_qr.jpg'
        elif qr_type == 'wechat':
            return cache_dir / 'wechat_qr.jpg'
        return None

    def _is_cache_valid(self, cache_file):
        """Check if cache file is still valid (within 7 days)"""
        if not cache_file or not cache_file.exists():
            return False

        import time
        file_mtime = cache_file.stat().st_mtime
        age_days = (time.time() - file_mtime) / (24 * 60 * 60)
        return age_days < self.qr_cache_days

    def _load_qr_from_cache(self, qr_type):
        """Load QR code from local cache"""
        cache_file = self._get_cache_file(qr_type)
        if not cache_file or not self._is_cache_valid(cache_file):
            return None

        try:
            with open(cache_file, 'rb') as f:
                return f.read()
        except Exception as e:
            self.log(f'读取 {qr_type} 缓存失败: {str(e)}')
            return None

    def _save_qr_to_cache(self, qr_type, image_data):
        """Save QR code image to local cache"""
        cache_file = self._get_cache_file(qr_type)
        if not cache_file:
            return

        try:
            with open(cache_file, 'wb') as f:
                f.write(image_data)
            self.log(f'{qr_type} 二维码已缓存')
        except Exception as e:
            self.log(f'保存 {qr_type} 缓存失败: {str(e)}')

    def load_qr_codes_with_cache(self):
        """Load QR codes with local cache support"""

        class QRCodeLoaderWithCache(QThread):
            finished = pyqtSignal(str, object, str)  # (qr_type, image_data, status)
            wechat_finished = pyqtSignal(object, str)

            def __init__(self, parent):
                super().__init__(parent)
                self.parent = parent

            def run(self):
                # Load QQ QR code
                qq_cache = self.parent._load_qr_from_cache('qq')
                if qq_cache:
                    self.finished.emit('qq', qq_cache, 'cache')
                else:
                    import urllib.request
                    from urllib.error import URLError, HTTPError
                    try:
                        with urllib.request.urlopen(self.parent.qqQrUrl, timeout=5) as response:
                            image_data = response.read()
                        self.parent._save_qr_to_cache('qq', image_data)
                        self.finished.emit('qq', image_data, 'success')
                    except Exception as e:
                        self.finished.emit('qq', None, str(e))

                # Load WeChat QR code
                wechat_cache = self.parent._load_qr_from_cache('wechat')
                if wechat_cache:
                    self.wechat_finished.emit(wechat_cache, 'cache')
                else:
                    import urllib.request
                    from urllib.error import URLError, HTTPError
                    try:
                        with urllib.request.urlopen(self.parent.wechatQrUrl, timeout=5) as response:
                            image_data = response.read()
                        self.parent._save_qr_to_cache('wechat', image_data)
                        self.wechat_finished.emit(image_data, 'success')
                    except Exception as e:
                        self.wechat_finished.emit(None, str(e))

        # Start loading in background
        self.qr_loader = QRCodeLoaderWithCache(self)
        self.qr_loader.finished.connect(self._on_qq_qr_loaded)
        self.qr_loader.wechat_finished.connect(self._on_wechat_qr_loaded)
        self.qr_loader.start()

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

    def _on_qq_qr_loaded(self, qr_type, image_data, status):
        """Handle QQ QR code loaded"""
        if image_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                self.qqQrLabel.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                if status == 'cache':
                    self.log('QQ 二维码已从缓存加载')
                elif status == 'success':
                    self.log('QQ 二维码加载成功')
            else:
                self.qqQrLabel.setText('加载失败')
        else:
            self.qqQrLabel.setText('加载失败')
            self.log(f'QQ 二维码加载失败: {status}')

    def _on_wechat_qr_loaded(self, image_data, status):
        """Handle WeChat QR code loaded"""
        if image_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                self.wechatQrLabel.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                if status == 'cache':
                    self.log('微信公众号二维码已从缓存加载')
                elif status == 'success':
                    self.log('微信公众号二维码加载成功')
            else:
                self.wechatQrLabel.setText('加载失败')
        else:
            self.wechatQrLabel.setText('加载失败')
            self.log(f'微信公众号二维码加载失败: {status}')

    def _on_qr_code_clicked(self, qr_type):
        """Handle QR code label click event"""
        if qr_type == 'qq':
            url = self.qqQrUrl
            name = 'QQ'
        elif qr_type == 'wechat':
            url = self.wechatQrUrl
            name = '微信公众号'
        else:
            return

        try:
            webbrowser.open(url)
            self.log(f'已打开 {name} 二维码: {url}')
        except Exception as e:
            self.log(f'打开二维码失败: {str(e)}')
            QMessageBox.warning(
                self,
                '打开失败',
                f'无法打开 {name} 二维码:\n{str(e)}'
            )

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

    def get_ffmpeg_path(self):
        """Get FFmpeg path from settings or system"""
        import shutil
        import json
        from pathlib import Path

        # 尝试从设置文件读取
        settings_file = os.path.join(Path.home(), '.ytdlp-gui-settings.json')
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    ffmpeg_path = settings.get('ffmpeg_path')
                    if ffmpeg_path and os.path.exists(ffmpeg_path):
                        return ffmpeg_path
        except Exception:
            pass

        # 回退到系统检测
        return shutil.which('ffmpeg')

    def save_ffmpeg_path(self, path):
        """Save FFmpeg path to settings"""
        import json
        from pathlib import Path

        settings_file = os.path.join(Path.home(), '.ytdlp-gui-settings.json')
        try:
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            settings['ffmpeg_path'] = path
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            self.log(f'FFmpeg 路径已保存: {path}')
        except Exception as e:
            self.log(f'保存 FFmpeg 路径失败: {str(e)}')

    def show_ffmpeg_dialog(self):
        """Show FFmpeg configuration dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QProgressBar
        from PyQt5.QtCore import QThread, pyqtSignal, QUrl
        from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

        # FFmpeg 下载链接
        FFmpeg_DOWNLOADS = {
            'Darwin': 'https://evermeet.cx/pub/ffmpeg/ffmpeg-7.1.1.7z',
            'Windows': 'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-7.1.1-essentials_build.7z',
            'Linux': 'https://ffmpeg.org/download.html'  # Linux 需要手动安装
        }

        class DownloadFFmpegWorker(QThread):
            progress = pyqtSignal(int)
            finished = pyqtSignal(str)
            error = pyqtSignal(str)

            def __init__(self, url, save_path):
                super().__init__()
                self.url = url
                self.save_path = save_path

            def run(self):
                import urllib.request
                from urllib.error import URLError, HTTPError

                try:
                    with urllib.request.urlopen(self.url, timeout=30) as response:
                        total_size = int(response.headers.get('Content-Length', 0))
                        downloaded = 0
                        chunk_size = 8192

                        with open(self.save_path, 'wb') as f:
                            while True:
                                chunk = response.read(chunk_size)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    progress = int((downloaded / total_size) * 100)
                                    self.progress.emit(progress)

                    self.finished.emit(self.save_path)
                except HTTPError as e:
                    self.error.emit(f'HTTP 错误: {e.code}')
                except URLError as e:
                    self.error.emit(f'网络错误: {e.reason}')
                except Exception as e:
                    self.error.emit(str(e))

        dialog = QDialog(self)
        dialog.setWindowTitle('FFmpeg 配置')
        dialog.setMinimumWidth(650)

        layout = QVBoxLayout()

        # 当前状态
        current_ffmpeg = self.get_ffmpeg_path()
        if current_ffmpeg:
            status_text = f'<span style="color: green;">✓ 已检测到 FFmpeg: {current_ffmpeg}</span>'
        else:
            status_text = '<span style="color: red;">✗ 未检测到 FFmpeg</span>'

        status_label = QLabel(f'<h3>FFmpeg 状态</h3>{status_text}')
        layout.addWidget(status_label)

        # 说明文本
        info_text = """<p>FFmpeg 用于合并视频和音频流，下载高清视频时必需。</p>
        <p><b>选项：</b></p>
        <ul>
            <li><b>自动下载</b>：一键下载并安装 FFmpeg（推荐）</li>
            <li><b>刷新检测</b>：自动查找系统中已安装的 FFmpeg</li>
            <li><b>手动选择</b>：手动指定 FFmpeg 可执行文件路径</li>
        </ul>"""
        layout.addWidget(QLabel(info_text))

        # 手动设置路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel('FFmpeg 路径:'))
        path_edit = QLineEdit(current_ffmpeg or '')
        browse_btn = QPushButton('浏览...')
        path_layout.addWidget(path_edit)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # 下载进度区域
        progress_label = QLabel('')
        progress_label.setVisible(False)
        layout.addWidget(progress_label)

        progress_bar = QProgressBar()
        progress_bar.setVisible(False)
        layout.addWidget(progress_bar)

        # 按钮布局
        btn_layout = QHBoxLayout()

        system = platform.system()
        download_btn = QPushButton('自动下载 FFmpeg')
        if system == 'Linux':
            download_btn.setEnabled(False)
            download_btn.setToolTip('Linux 请使用包管理器安装：sudo apt install ffmpeg')

        refresh_btn = QPushButton('刷新检测')
        save_btn = QPushButton('保存')
        cancel_btn = QPushButton('取消')

        btn_layout.addWidget(download_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # 下载说明
        system = platform.system()
        if system in FFmpeg_DOWNLOADS:
            if system == 'Darwin':
                install_note = '<p><small>自动下载后，将 FFmpeg 解压到任意目录，然后点击"浏览"选择解压后的 ffmpeg 文件。</small></p>'
            elif system == 'Windows':
                install_note = '<p><small>自动下载后，将 FFmpeg 解压到任意目录，然后点击"浏览"选择 bin 文件夹内的 ffmpeg.exe。</small></p>'
            else:
                install_note = ''
            layout.addWidget(QLabel(install_note))

        dialog.setLayout(layout)

        # 下载器实例
        downloader = None

        # 事件处理
        def browse_path():
            path = QFileDialog.getOpenFileName(dialog, '选择 FFmpeg 可执行文件')[0]
            if path:
                path_edit.setText(path)

        def refresh_detection():
            import shutil
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                path_edit.setText(ffmpeg_path)
                status_label.setText(f'<h3>FFmpeg 状态</h3><span style="color: green;">✓ 已检测到 FFmpeg: {ffmpeg_path}</span>')
            else:
                status_label.setText(f'<h3>FFmpeg 状态</h3><span style="color: red;">✗ 未检测到 FFmpeg</span>')

        def start_download():
            nonlocal downloader

            system = platform.system()
            if system not in FFmpeg_DOWNLOADS:
                QMessageBox.warning(dialog, '不支持的系统', '当前系统不支持自动下载，请手动安装 FFmpeg。')
                return

            url = FFmpeg_DOWNLOADS[system]
            if system == 'Linux':
                # Linux 需要手动安装
                QMessageBox.information(
                    dialog,
                    'Linux 安装说明',
                    'Linux 系统请使用包管理器安装 FFmpeg：\n\n'
                    'Ubuntu/Debian:\n  sudo apt update\n  sudo apt install ffmpeg\n\n'
                    'Fedora:\n  sudo dnf install ffmpeg\n\n'
                    'Arch Linux:\n  sudo pacman -S ffmpeg'
                )
                return

            # 选择保存位置
            save_dir = QFileDialog.getExistingDirectory(dialog, '选择保存 FFmpeg 的目录')
            if not save_dir:
                return

            import os
            filename = os.path.basename(url)
            save_path = os.path.join(save_dir, filename)

            # 开始下载
            download_btn.setEnabled(False)
            refresh_btn.setEnabled(False)
            save_btn.setEnabled(False)
            progress_label.setText(f'正在下载 FFmpeg...')
            progress_label.setVisible(True)
            progress_bar.setVisible(True)
            progress_bar.setValue(0)

            downloader = DownloadFFmpegWorker(url, save_path)
            downloader.progress.connect(progress_bar.setValue)
            downloader.finished.connect(lambda p: on_download_finished(p))
            downloader.error.connect(on_download_error)
            downloader.start()

        def on_download_finished(save_path):
            nonlocal downloader

            progress_label.setText(f'下载完成: {save_path}')
            progress_bar.setValue(100)
            download_btn.setEnabled(True)
            refresh_btn.setEnabled(True)
            save_btn.setEnabled(True)

            QMessageBox.information(
                dialog,
                '下载完成',
                f'FFmpeg 已下载到：\n{save_path}\n\n'
                '请解压文件，然后点击"浏览"选择 FFmpeg 可执行文件。'
            )

            # 自动打开下载目录
            try:
                import subprocess
                if platform.system() == 'Windows':
                    os.startfile(os.path.dirname(save_path))
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', os.path.dirname(save_path)])
                else:
                    subprocess.run(['xdg-open', os.path.dirname(save_path)])
            except:
                pass

            downloader = None

        def on_download_error(error_msg):
            nonlocal downloader

            progress_label.setText(f'下载失败: {error_msg}')
            download_btn.setEnabled(True)
            refresh_btn.setEnabled(True)
            save_btn.setEnabled(True)
            QMessageBox.critical(dialog, '下载失败', f'下载 FFmpeg 失败:\n{error_msg}')
            downloader = None

        browse_btn.clicked.connect(browse_path)
        refresh_btn.clicked.connect(refresh_detection)
        download_btn.clicked.connect(start_download)

        cancel_btn.clicked.connect(dialog.reject)
        save_btn.clicked.connect(lambda: [
            self.save_ffmpeg_path(path_edit.text()),
            self.ffmpegPathEdit.setText(path_edit.text()),
            dialog.accept()
        ])

        if dialog.exec_() == QDialog.Accepted:
            return True
        return False

    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        return self.get_ffmpeg_path() is not None

    def _init_ffmpeg_path(self):
        """Initialize FFmpeg path in settings UI"""
        ffmpeg_path = self.get_ffmpeg_path()
        if ffmpeg_path:
            self.ffmpegPathEdit.setText(ffmpeg_path)
            self.log(f'检测到 FFmpeg: {ffmpeg_path}')
        else:
            self.ffmpegPathEdit.clear()
            self.log('未检测到 FFmpeg')

    def browse_ffmpeg_path(self):
        """Browse for FFmpeg executable"""
        system = platform.system()

        if system == 'Windows':
            filter_text = '可执行文件 (*.exe);;所有文件 (*.*)'
        else:
            filter_text = '可执行文件 (*);;所有文件 (*)'

        path, _ = QFileDialog.getOpenFileName(
            self,
            '选择 FFmpeg 可执行文件',
            '',
            filter_text
        )

        if path:
            self.ffmpegPathEdit.setText(path)
            self.save_ffmpeg_path(path)
            self.log(f'FFmpeg 路径已设置: {path}')

    def download_ffmpeg_auto(self):
        """Show FFmpeg auto-download dialog"""
        self.show_ffmpeg_dialog()
        # Update UI after dialog
        ffmpeg_path = self.get_ffmpeg_path()
        if ffmpeg_path:
            self.ffmpegPathEdit.setText(ffmpeg_path)

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
            reply = QMessageBox.question(
                self,
                '缺少 FFmpeg',
                '检测到系统未安装 FFmpeg。\n\n'
                '下载高清视频需要 FFmpeg 来合并视频和音频流。\n\n'
                '是否立即配置 FFmpeg？',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if not self.show_ffmpeg_dialog():
                    return
            else:
                return

        # Check if save path is writable
        if not os.path.exists(self.save_path):
            try:
                os.makedirs(self.save_path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    '错误',
                    f'无法创建保存目录:\n{self.save_path}\n\n错误: {str(e)}'
                )
                return

        if not self._check_write_permission(self.save_path):
            QMessageBox.critical(
                self,
                '错误',
                f'保存目录没有写入权限:\n{self.save_path}\n\n请选择其他目录或修改权限。'
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

        # Add FFmpeg path if configured
        ffmpeg_path = self.get_ffmpeg_path()
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path
            self.log(f'使用 FFmpeg: {ffmpeg_path}')

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

    def save_settings(self):
        """Save all settings to file"""
        try:
            import json
            from pathlib import Path

            settings_file = Path.home() / '.ytdlp-gui-settings.json'
            settings = {}

            # Load existing settings
            if settings_file.exists():
                try:
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                except:
                    pass

            # Save FFmpeg path
            ffmpeg_path = self.ffmpegPathEdit.text().strip()
            if ffmpeg_path:
                settings['ffmpeg_path'] = ffmpeg_path
            elif 'ffmpeg_path' in settings:
                del settings['ffmpeg_path']

            # Save settings to file
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            QMessageBox.information(
                self,
                '设置已保存',
                '所有设置已成功保存！'
            )
            self.log('设置已保存')

        except Exception as e:
            QMessageBox.critical(
                self,
                '保存失败',
                f'保存设置时出错:\n{str(e)}'
            )
            self.log(f'保存设置失败: {str(e)}')

    def reset_settings(self):
        """Reset all settings to default values"""
        reply = QMessageBox.question(
            self,
            '确认恢复',
            '确定要恢复所有设置为默认值吗？\n\n这将清除所有自定义设置。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                import json
                from pathlib import Path

                settings_file = Path.home() / '.ytdlp-gui-settings.json'

                # Remove settings file
                if settings_file.exists():
                    settings_file.unlink()

                # Reset FFmpeg path
                self.ffmpegPathEdit.clear()

                # Re-detect FFmpeg
                import shutil
                ffmpeg_path = shutil.which('ffmpeg')
                if ffmpeg_path:
                    self.ffmpegPathEdit.setText(ffmpeg_path)

                QMessageBox.information(
                    self,
                    '设置已恢复',
                    '所有设置已恢复为默认值！'
                )
                self.log('设置已恢复为默认值')

            except Exception as e:
                QMessageBox.critical(
                    self,
                    '恢复失败',
                    f'恢复设置时出错:\n{str(e)}'
                )
                self.log(f'恢复设置失败: {str(e)}')

