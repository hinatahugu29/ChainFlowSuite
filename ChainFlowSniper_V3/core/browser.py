from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage

class SniperBrowser(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tab_manager = None

    def set_tab_manager(self, manager):
        self._tab_manager = manager

    def createWindow(self, window_type):
        """新しいウィンドウ要求（ターゲット='_blank' リンクなど）を新しいタブとして開く"""
        if self._tab_manager:
            # 新しいタブを作成し、その中のブラウザインスタンスを返す
            # これにより、QtWebEngineが自動的にリンク先URLをその新しいインスタンスでロードする
            new_browser = self._tab_manager.add_tab(label="Loading...")
            return new_browser
        return super().createWindow(window_type)
