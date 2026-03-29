"""
v7.4 複数ペイン・マーク済みアイテムを一括でドラッグするためのカスタムTreeView
v14.1 Refactoring: file_pane.py から分離
"""
import os
from PySide6.QtWidgets import QTreeView, QApplication, QAbstractItemView
from PySide6.QtCore import Qt, QTimer, QUrl, QMimeData
from PySide6.QtGui import QKeySequence, QDrag
from core import same_path, logger

from .highlight_delegate import HighlightDelegate


class BatchTreeView(QTreeView):
    """複数ペイン・マーク済みアイテムを一括でドラッグするためのカスタムTreeView"""
    
    def __init__(self, owner_pane):
        super().__init__()
        self.owner_pane = owner_pane
        self.setMouseTracking(True)  # v11.1 Hover Auto-Focus
        
        # v14.0 Ancestral Highlight Delegate
        self.highlight_delegate = HighlightDelegate(self)
        self.setItemDelegate(self.highlight_delegate)

        # v14.1 Performance Optimization
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(50)  # 50ms delay
        self._resize_timer.timeout.connect(self._adjust_name_column_width)

    def set_temp_highlight(self, path):
        """v14.0 指定パスを一時的にハイライト＆スクロール表示
        
        v14.2 改善: プロキシマッピングが失敗しても、デリゲートにはパスを設定し、
        描画時に個別にチェックするようにした。
        """
        if not path:
            return
        
        proxy = self.model()
        source_model = proxy.sourceModel()  # QFileSystemModel
        
        # デリゲートにパスを設定（描画時に個別チェック）
        self.highlight_delegate.set_highlight_path(path)
        
        # インデックス取得を試みる（スクロール用）
        source_index = source_model.index(path)
        if source_index.isValid():
            proxy_index = proxy.mapFromSource(source_index)
            if proxy_index.isValid():
                # スクロールして表示 (Centerにすることで前後が見えるように)
                self.scrollTo(proxy_index, QAbstractItemView.PositionAtCenter)
            else:
                logger.log_debug(f"  [TreeView] Proxy mapping failed (Filtered?): {path}")
        else:
            logger.log_debug(f"  [TreeView] Source index invalid (Not loaded?): {path}")
    
        # 再描画（デリゲートがハイライト判定を行う）
        self.viewport().update()
        
    def clear_temp_highlight(self):
        """v14.0 ハイライト解除"""
        self.highlight_delegate.set_highlight_path(None)
        self.viewport().update()

    def enterEvent(self, event):
        # v11.1 Hover Auto-Focus Logic
        # Ctrlが押されていない場合、マウスが入っただけでフォーカスを奪う
        if not (QApplication.keyboardModifiers() & Qt.ControlModifier):
            self.setFocus()
            # 親ペインもアクティブにする
            self.owner_pane.parent_filer.set_active_pane(self.owner_pane)

            # v14.x Dynamic Address Bar Update: Update address bar based on the specific view hovered
            # v21.5 Performance Fix: デバウンスで連続発火を抑制
            path_to_show = None
            if hasattr(self.owner_pane, 'views'):
                for v, proxy, path, sep in self.owner_pane.views:
                    if v == self:
                        path_to_show = path
                        break
            
            if path_to_show:
                self._path_to_show = path_to_show
                # デバウンス: 既存タイマーがあればキャンセルして再設定
                if not hasattr(self, '_address_bar_timer'):
                    self._address_bar_timer = QTimer()
                    self._address_bar_timer.setSingleShot(True)
                    self._address_bar_timer.setInterval(50)
                    self._address_bar_timer.timeout.connect(
                        lambda: self.owner_pane.parent_filer.update_address_bar(getattr(self, '_path_to_show', ''))
                    )
                self._address_bar_timer.start()
            
            # v11.0 セパレータハイライトのために再描画要求などは eventFilter (FocusIn) で行われる
        
        super().enterEvent(event)

    def keyPressEvent(self, event):
        # v14.1 Fix: Ctrl+C を自前で完全にハンドルする (標準機能を無効化)
        if event.matches(QKeySequence.Copy):
            self.owner_pane.copy_selected_to_clipboard()
            event.accept()
            return
            
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # v14.1 Performance Optimization: Debounce
        # 連続的に呼ばれるresizeEventでは計算せず、入力が止まってから一度だけ実行する
        self._resize_timer.start()

    def _adjust_name_column_width(self):
        # 名前列以外の固定・可変幅を取得
        col2 = self.columnWidth(2)  # Size
        col3 = self.columnWidth(3)  # Date
        
        # スクロールバーの幅を考慮
        sb_w = 0
        if self.verticalScrollBar().isVisible():
            sb_w = self.verticalScrollBar().width()
        
        # 利用可能な幅 (self.width() は現在の最新幅)
        total_w = self.width()
        
        # bufferを少し大きめに取る
        new_name_w = total_w - col2 - col3 - sb_w - 10 
        
        # 最低幅の確保 (100px以下にはしない)
        if new_name_w < 100:
            new_name_w = 100
            
        self.setColumnWidth(0, int(new_name_w))

    def startDrag(self, supportedActions):
        # 1. ドラッグ対象のパスを全収集
        drag_paths = set()
        
        # A. マーク（収集カゴ）内のアイテム [Global]
        # 上位構造（タブエリア）にアクセスしてマークを取得
        if hasattr(self.owner_pane, 'parent_lane') and hasattr(self.owner_pane.parent_lane, 'parent_area'):
            area = self.owner_pane.parent_lane.parent_area
            if area and area.marked_paths:
                for p in area.marked_paths:
                    if os.path.exists(p):
                        drag_paths.add(os.path.abspath(p))
            
        # B. このビューの選択アイテム [Local]
        # v10.0 Updated: ペインをまたぐ（他ペインの）選択はドラッグ対象に含めない
        # あくまでも「マークされたもの」＋「現在掴んでいるもの」だけを動かす
        info = self.owner_pane.get_selection_info(view=self, proxy=self.model())
        for p in info['paths']:
            drag_paths.add(os.path.abspath(p))

        if not drag_paths:
            return

        # 2. MimeData作成
        mime = QMimeData()
        urls = [QUrl.fromLocalFile(p) for p in drag_paths]
        mime.setUrls(urls)
        
        # 3. Dragオブジェクト作成と実行
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        drag.exec(supportedActions, Qt.CopyAction)
