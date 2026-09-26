"""
v7.4 複数ペイン・マーク済みアイテムを一括でドラッグするためのカスタムTreeView
v14.1 Refactoring: file_pane.py から分離
"""
import os
from PySide6.QtWidgets import QTreeView, QApplication, QAbstractItemView
from PySide6.QtCore import Qt, QTimer, QUrl, QMimeData
from PySide6.QtGui import QKeySequence, QDrag
from core import same_path, logger

from .highlight_delegate import HighlightDelegate, EditingDelegate


class BatchTreeView(QTreeView):
    """複数ペイン・マーク済みアイテムを一括でドラッグするためのカスタムTreeView"""
    
    def __init__(self, owner_pane):
        super().__init__()
        self.owner_pane = owner_pane
        self.setMouseTracking(True)  # v11.1 Hover Auto-Focus
        # v23.6 Performance: 全行同一高さのため、行ごとのsizeHint計算を省略させる
        self.setUniformRowHeights(True)
        
        # v14.0 Ancestral Highlight Delegate
        # v23.8 Performance: 通常時は paint() を上書きしない EditingDelegate を使い、
        # ハイライト表示中だけ HighlightDelegate に差し替える。
        # paint() を常時 Python 側で持つと、可視セルごとに Python↔C++ の往復が発生し、
        # ハイライトが無効なときも往復代だけを払い続けるため。
        self.highlight_delegate = HighlightDelegate(self)
        self.plain_delegate = EditingDelegate(self)
        self.setItemDelegate(self.plain_delegate)
        # itemDelegate() は呼ぶたびに別の Python ラッパーを返し得るため、
        # 現在どちらを挿しているかは自前で保持する（is 比較を当てにしない）
        self._highlight_delegate_active = False

        # v14.1 Performance Optimization
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(50)  # 50ms delay
        self._resize_timer.timeout.connect(self._adjust_name_column_width)

        # v23.1: Active Drag Management
        self._drag_start_pos = None
        
        # v23.3: Column Display Mode
        self._show_details = True

    def keyboardSearch(self, search):
        """v23.3: 標準のインクリメンタルサーチを無効化し、Eキーなどが奪われるのを防ぐ"""
        pass

    def toggle_details_mode(self):
        """v23.3: Eキーによる表示モード（詳細表示/Nameのみ）のトグル"""
        self._show_details = not self._show_details
        
        # Size (2), Date (3) 列の表示切替
        self.setColumnHidden(2, not self._show_details)
        self.setColumnHidden(3, not self._show_details)
        
        # 名前列の幅を再調整（タイマーを待たずに即座に実行）
        self._adjust_name_column_width()

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
        self._use_highlight_delegate(True)
        
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
        self._use_highlight_delegate(False)
        self.viewport().update()

    def _use_highlight_delegate(self, enabled):
        """v23.8: 描画用デリゲートの差し替え。

        リネーム編集中の差し替えはエディタを巻き込む恐れがあるため行わない
        （ハイライトは装飾であり、1フレーム遅れても実害がない）。
        """
        if self._highlight_delegate_active == enabled:
            return
        if self.state() == QAbstractItemView.EditingState:
            return
        self.setItemDelegate(self.highlight_delegate if enabled else self.plain_delegate)
        self._highlight_delegate_active = enabled

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
        # 名前列以外の固定・可変幅を取得 (非表示の場合は 0 とする)
        col2 = self.columnWidth(2) if not self.isColumnHidden(2) else 0
        col3 = self.columnWidth(3) if not self.isColumnHidden(3) else 0
        
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
