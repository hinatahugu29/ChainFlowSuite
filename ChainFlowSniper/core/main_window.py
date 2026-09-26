import os
import sys
import re
import json
import ctypes
from PySide6.QtWidgets import (QApplication, QMainWindow, QSplitter, 
                               QListWidget, QVBoxLayout, QHBoxLayout, QWidget, 
                               QLineEdit, QListWidgetItem, QLabel, QPushButton)
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineScript, QWebEnginePage
from PySide6.QtCore import Qt, QUrl, Slot, QFile, QIODevice, QTimer, QMimeData
from PySide6.QtWebChannel import QWebChannel

from core.bridge import SniperBridge
from core.browser import SniperBrowser
from core.tab_manager import SniperTabManager
from core.widgets import ExtractionItemWidget, ClipboardPopup
from core.storage import StorageManager
from PySide6.QtGui import QAction, QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sniper Research Shell V3")
        self.setWindowFlags(Qt.Window) # Ensure it's a normal window
        self.resize(1200, 800)

        # --- Icon Settings ---
        # 1. Try PyInstaller Bundle Path (_MEIPASS)
        # 2. Try Current Directory
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_path, "app_icon.ico")
            
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Final fallback: search parent (dev mode)
            icon_path_dev = os.path.join(os.path.dirname(base_path), "app_icon.ico")
            if os.path.exists(icon_path_dev):
                self.setWindowIcon(QIcon(icon_path_dev))
        
        # Session Persistence
        if getattr(sys, 'frozen', False):
            # EXE化されている場合、.exe ファイルの真横
            app_root = os.path.dirname(sys.executable)
        else:
            # 開発環境の場合、main.py の親(project_root)
            # core/main_window.py の親(core)の親(project_root)
            app_root = os.path.dirname(os.path.dirname(__file__))
            
        storage_path = os.path.join(app_root, ".web_data")
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
            
        self.profile = QWebEngineProfile("SniperProfile", self)
        self.profile.setPersistentStoragePath(storage_path)
        # 社内システムに多い「セッションCookie（無期限ではない一時Cookie）」も強制的にディスクに保存する
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        self.profile.setCachePath(os.path.join(storage_path, "cache"))
        
        # User-Agent を Firefox に擬装（Googleログインのセキュリティチェック回避対策）
        firefox_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        self.profile.setHttpUserAgent(firefox_ua)
        
        # 万能クリップボード連携
        self._block_clipboard_signal = False
        QApplication.clipboard().dataChanged.connect(self.on_clipboard_changed)
        
        self.popup = None
        self._detached_backup = None

        self.splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.splitter)

        # Left Pane: Favorites & History (Vertical Split)
        self.left_container = QSplitter(Qt.Vertical)
        
        # Favorites Section
        self.favorites_widget = QWidget()
        fav_layout = QVBoxLayout(self.favorites_widget)
        fav_layout.setContentsMargins(5, 5, 5, 5)
        
        fav_header = QHBoxLayout()
        self.fav_label = QLabel("FAVORITES")
        self.fav_label.setObjectName("sectionHeader")
        
        self.add_fav_btn = QPushButton("+")
        self.add_fav_btn.setObjectName("favControlBtn")
        self.add_fav_btn.setFixedSize(20, 20)
        self.add_fav_btn.clicked.connect(self.add_favorite)
        
        self.remove_fav_btn = QPushButton("-")
        self.remove_fav_btn.setObjectName("favControlBtn")
        self.remove_fav_btn.setFixedSize(20, 20)
        self.remove_fav_btn.clicked.connect(self.remove_favorite)
        
        fav_header.addWidget(self.fav_label)
        fav_header.addStretch()
        fav_header.addWidget(self.add_fav_btn)
        fav_header.addWidget(self.remove_fav_btn)
        
        self.favorites_list = QListWidget()
        fav_layout.addLayout(fav_header)
        fav_layout.addWidget(self.favorites_list)
        
        # History Section
        self.history_widget = QWidget()
        hist_layout = QVBoxLayout(self.history_widget)
        hist_layout.setContentsMargins(5, 5, 5, 5)
        self.hist_label = QLabel("HISTORY")
        self.hist_label.setObjectName("sectionHeader")
        self.history_list = QListWidget()
        hist_layout.addWidget(self.hist_label)
        hist_layout.addWidget(self.history_list)
        
        self.left_container.addWidget(self.favorites_widget)
        self.left_container.addWidget(self.history_widget)
        self.left_container.setSizes([300, 500])
        
        # Right Pane: Extraction List with Header
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        header_layout = QHBoxLayout()
        self.extract_label = QLabel("EXTRACTIONS")
        self.extract_label.setObjectName("sectionHeader")
        
        self.clear_btn = QPushButton("×")
        self.clear_btn.setObjectName("favControlBtn")
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setToolTip("抽出リストを全消去")
        self.clear_btn.clicked.connect(self.clear_extraction_list)
        
        self.detach_btn = QPushButton("Detach")
        self.detach_btn.setObjectName("detachButton")
        self.detach_btn.setFixedWidth(60)
        self.detach_btn.clicked.connect(self.detach_list)
        
        header_layout.addWidget(self.extract_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_btn)
        header_layout.addWidget(self.detach_btn)
        
        self.extraction_list = QListWidget()
        self.extraction_list.setObjectName("extractionList")
        right_layout.addLayout(header_layout)
        right_layout.addWidget(self.extraction_list)
        
        self.browser_container = QWidget()
        browser_layout = QVBoxLayout(self.browser_container)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_layout.setSpacing(0)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("URLを入してEnterを押す... (Ctrl+L)")
        self.url_bar.returnPressed.connect(self.navigate)

        # Setup QWebChannel & Bridge first (required for tabs)
        self.channel = QWebChannel()
        self.bridge = SniperBridge(self)
        self.channel.registerObject("sniperBridge", self.bridge)

        self.tab_manager = SniperTabManager(self)
        self.setup_sniper_script()
        
        # Connect tab manager signals
        self.tab_manager.tab_changed.connect(self.on_tab_changed)
        self.tab_manager.url_changed.connect(self.update_url_bar)
        self.tab_manager.title_changed.connect(self.update_history_title)
        
        # Connect events
        self.history_list.itemClicked.connect(self.on_history_clicked)
        self.favorites_list.itemClicked.connect(self.on_history_clicked)
        self.extraction_list.itemClicked.connect(self.on_extraction_clicked)
        self.extraction_list.itemDoubleClicked.connect(self.on_item_double_clicked)

        browser_layout.addWidget(self.url_bar)
        browser_layout.addWidget(self.tab_manager)

        self.splitter.addWidget(self.left_container)
        self.splitter.addWidget(self.browser_container)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([200, 800, 200])

        self.setup_shortcuts()
        self.load_favorites()
        
        # Open first tab
        self.tab_manager.add_tab("https://ja.wikipedia.org/wiki/Python")

    def load_favorites(self):
        favorites = StorageManager.load_favorites()
        for fav in favorites:
            title = fav.get("title", "")
            url = fav.get("url", "")
            if not url:
                continue
            if not title:
                title = url
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, url)
            item.setToolTip(url)
            self.favorites_list.addItem(item)

    def setup_shortcuts(self):
        """ショートカットキーの設定"""
        # 新規タブ (Ctrl+T)
        self.new_tab_action = QAction(self)
        self.new_tab_action.setShortcut("Ctrl+T")
        self.new_tab_action.triggered.connect(lambda: self.tab_manager.add_tab())
        self.addAction(self.new_tab_action)

        # タブを閉じる (Ctrl+W)
        self.close_tab_action = QAction(self)
        self.close_tab_action.setShortcut("Ctrl+W")
        self.close_tab_action.triggered.connect(lambda: self.tab_manager.close_tab(self.tab_manager.tabs.currentIndex()))
        self.addAction(self.close_tab_action)

        # URLバーにフォーカス (Ctrl+L)
        self.focus_url_action = QAction(self)
        self.focus_url_action.setShortcut("Ctrl+L")
        self.focus_url_action.triggered.connect(self.url_bar.setFocus)
        self.addAction(self.focus_url_action)

    def navigate(self):
        import urllib.parse
        url = self.url_bar.text().strip()
        if not url:
            return
        # URLでない場合はBing検索にリダイレクト（Googleのbot判定回避のため）
        if not url.startswith("http") and "." not in url.split()[0]:
            # 日本語検索時などにbot判定を誘発しないよう、正しくURLエンコードする
            encoded_query = urllib.parse.quote(url)
            url = f"https://www.bing.com/search?q={encoded_query}"
        elif not url.startswith("http"):
            url = "https://" + url
        browser = self.tab_manager.current_browser()
        if browser:
            browser.setUrl(QUrl(url))

    def update_url_bar(self, qurl):
        url_str = qurl.toString()
        self.url_bar.setText(url_str)

    @Slot(str)
    def update_history_title(self, title):
        browser = self.tab_manager.current_browser()
        if not browser:
            return
        url_str = browser.url().toString()
        item_text = f"[{title}]\n{url_str}"
        
        # Check if identical to last item to prevent duplicates
        if self.history_list.count() > 0:
            last_item = self.history_list.item(self.history_list.count() - 1)
            if last_item.data(Qt.UserRole) == url_str:
                return

        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, url_str)
        item.setToolTip(url_str)
        self.history_list.addItem(item)
        self.history_list.scrollToBottom()
        
        # 履歴の上限を200件に制限（メモリ肥大防止）
        MAX_HISTORY = 200
        while self.history_list.count() > MAX_HISTORY:
            self.history_list.takeItem(0)

    @Slot(QListWidgetItem)
    def on_history_clicked(self, item):
        url_str = item.data(Qt.UserRole)
        if url_str:
            browser = self.tab_manager.current_browser()
            if browser:
                browser.setUrl(QUrl(url_str))

    def add_favorite(self):
        browser = self.tab_manager.current_browser()
        if not browser:
            return
        url = browser.url().toString()
        title = browser.page().title()
        if not title:
            title = url
        
        # 重複チェック（同じURLがすでに登録されている場合はスキップ）
        for i in range(self.favorites_list.count()):
            if self.favorites_list.item(i).data(Qt.UserRole) == url:
                self.statusBar().showMessage(f"すでにお気に入りに登録済み: {title}", 3000)
                return
            
        item = QListWidgetItem(title)
        item.setData(Qt.UserRole, url)
        item.setToolTip(url)
        self.favorites_list.addItem(item)
        self.save_favorites()
        self.statusBar().showMessage(f"Added to favorites: {title}", 3000)

    def remove_favorite(self):
        current_item = self.favorites_list.currentItem()
        if current_item:
            title = current_item.text()
            self.favorites_list.takeItem(self.favorites_list.row(current_item))
            self.save_favorites()
            self.statusBar().showMessage(f"Removed from favorites: {title}", 3000)

    def clear_extraction_list(self):
        """抽出リストを全消去する"""
        if self.extraction_list.count() == 0:
            return
        self.extraction_list.clear()
        self.statusBar().showMessage("抽出リストを消去しました", 2000)

    def save_favorites(self):
        favorites = []
        for i in range(self.favorites_list.count()):
            item = self.favorites_list.item(i)
            favorites.append({
                "title": item.text(),
                "url": item.data(Qt.UserRole)
            })
        StorageManager.save_favorites(favorites)

    def on_item_double_clicked(self, item):
        # メインウィンドウのリストまたはポップアップのリスト共有のトグル処理
        widget = self.extraction_list.itemWidget(item)
        if widget and hasattr(widget, "toggle_expand"):
            widget.toggle_expand()
            item.setSizeHint(widget.sizeHint())

    def on_extraction_clicked(self, item):
        widget = self.extraction_list.itemWidget(item)
        if not widget:
            return
        text = widget.get_full_text()
        if text:
            # クリップボード変更シグナルを一時的にブロック（遅延解除でイベントループの非同期到着に対応）
            self._block_clipboard_signal = True
            clipboard = QApplication.clipboard()
            if widget.is_html:
                # HTML項目はリッチテキストとしてコピー
                mime = QMimeData()
                mime.setHtml(text)
                mime.setText(text)
                clipboard.setMimeData(mime)
                self.statusBar().showMessage(f"Copied HTML: {len(text)} chars", 3000)
            else:
                clipboard.setText(text)
                self.statusBar().showMessage(f"Copied: {text[:30]}...", 3000)
            QTimer.singleShot(100, lambda: setattr(self, '_block_clipboard_signal', False))

    def on_clipboard_changed(self):
        """外部でのコピー（Ctrl+C等）を検知してリストに追加する"""
        if self._block_clipboard_signal:
            return
            
        text = QApplication.clipboard().text()
        if text:
            # 重複チェック等は add_extracted_text 側で処理
            self.add_extracted_text(text, is_manual=True)

    def setup_sniper_script(self):
        """スナイパースクリプトを全フレームへ自動注入する設定"""
        project_root = os.path.dirname(os.path.dirname(__file__))
        script_path = os.path.join(project_root, "resources", "sniper.js")
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                script_content = f.read()

            # PySide6 内蔵の qwebchannel.js を読み込んで先頭に結合（JS通信用）
            qrc_file = QFile(":/qtwebchannel/qwebchannel.js")
            if qrc_file.open(QIODevice.ReadOnly):
                qwebchannel_js = bytes(qrc_file.readAll()).decode("utf-8")
                script_content = qwebchannel_js + "\n" + script_content
                qrc_file.close()
            
            script = QWebEngineScript()
            script.setName("SniperJS")
            script.setSourceCode(script_content)
            script.setInjectionPoint(QWebEngineScript.DocumentReady)
            script.setWorldId(QWebEngineScript.MainWorld)
            script.setRunsOnSubFrames(True) # 全フレームに対応
            
            # Profile レベルで登録することで、全てのページ/フレームに確実に適用
            self.profile.scripts().insert(script)
        except Exception as e:
            print(f"Error loading sniper script: {e}")

    def add_extracted_text(self, text, is_manual=False):
        """抽出データをリスト（およびポップアップ）に追加"""
        text = text.strip()
        if not text:
            return
            
        # 重複チェック（直前と同じならスキップ）
        if self.extraction_list.count() > 0:
            last_item = self.extraction_list.item(self.extraction_list.count() - 1)
            last_widget = self.extraction_list.itemWidget(last_item)
            if last_widget and last_widget.get_full_text() == text:
                return

        item = QListWidgetItem(self.extraction_list)
        item.setText(text) # クリップボード取得や検索用にテキストをセット
        item.setForeground(Qt.transparent) # 表示の二重化を防ぐためデフォルト描画を消す
        widget = ExtractionItemWidget(text)
        item.setSizeHint(widget.sizeHint())
        
        if is_manual:
            # 外部コピーの時はステータスバーで通知
            self.statusBar().showMessage(f"External Copy Captured: {text[:20]}...", 2000)

        self.extraction_list.addItem(item)
        self.extraction_list.setItemWidget(item, widget)
        self.extraction_list.scrollToBottom()
        
        if self.popup and self.popup.isVisible():
            self.popup.add_item(text)

    def add_extracted_html(self, html):
        """Style Snipeで抽出されたHTMLデータをリストに追加"""
        html = html.strip()
        if not html:
            return
            
        # 重複チェック（直前と同じならスキップ）
        if self.extraction_list.count() > 0:
            last_item = self.extraction_list.item(self.extraction_list.count() - 1)
            last_widget = self.extraction_list.itemWidget(last_item)
            if last_widget and last_widget.get_full_text() == html:
                return

        # HTMLタグを除去してプレーンテキストのプレビューを生成
        preview = re.sub(r'<[^>]+>', '', html).strip()
        preview = re.sub(r'\s+', ' ', preview)  # 連続空白を圧縮
        if len(preview) > 200:
            preview = preview[:200] + "..."

        item = QListWidgetItem(self.extraction_list)
        item.setText(html)  # 内部データとしてHTML原文を保持
        item.setForeground(Qt.transparent)
        widget = ExtractionItemWidget(html, is_html=True, preview_text=preview)
        item.setSizeHint(widget.sizeHint())

        self.extraction_list.addItem(item)
        self.extraction_list.setItemWidget(item, widget)
        self.extraction_list.scrollToBottom()
        self.statusBar().showMessage(f"Style Snipe: HTML captured ({len(html)} chars)", 3000)
        
        if self.popup and self.popup.isVisible():
            self.popup.add_item(html)

    def on_tab_changed(self, browser):
        """タブが切り替わった時の処理"""
        # 必要に応じて追加の処理をここに記述
        pass

    def detach_list(self):
        if self.popup:
            return
            
        items = []
        for i in range(self.extraction_list.count()):
            # ExtractionItemWidgetからテキストを取得
            widget = self.extraction_list.itemWidget(self.extraction_list.item(i))
            if widget:
                items.append(widget.get_full_text()) 
        
        # データ消失防止: ポップアップが異常終了してもデータを復元できるようバックアップを保持
        self._detached_backup = list(items)
            
        self.popup = ClipboardPopup(items, self)
        self.popup.closed.connect(self.attach_list)
        self.popup.show()
        
        self.extraction_list.clear()
        self.right_widget.hide()

    def attach_list(self, items_text):
        self.extraction_list.setObjectName("extractionList")
        self.extraction_list.clear()
        for text in items_text:
            # add_extracted_text を使ってアイテムを再追加
            self.add_extracted_text(text)
        
        self.popup = None
        self._detached_backup = None
        self.right_widget.show()
    
    def showEvent(self, event):
        """Windows 10/11のタイトルバーをダークモードにする"""
        try:
            hwnd = self.winId()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            value = ctypes.c_int(1)
            
            # Try Attribute 20
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                int(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE, 
                ctypes.byref(value), ctypes.sizeof(value)
            )
            if result != 0:
                # Fallback for older Win10
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    int(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, 
                    ctypes.byref(value), ctypes.sizeof(value)
                )
        except Exception as e:
            print(f"Failed to apply dark title bar: {e}")
        super().showEvent(event)

    def closeEvent(self, event):
        """ウィンドウ終了時: Detach中のデータがあれば復元して安全にシャットダウン"""
        if self._detached_backup and self.popup:
            try:
                self.popup.close()
            except Exception:
                pass
        super().closeEvent(event)
