import os
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import Qt, QSortFilterProxyModel

class SmartSortFilterProxyModel(QSortFilterProxyModel):
    """
    高度なソートとフィルタリングを提供するProxyモデル
    QFileSystemModelの非同期性やフィルタの癖を吸収し、即時反映を実現する。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        # 階層構造におけるフィルタリングを正しく行うため
        self.setRecursiveFilteringEnabled(True)
        # 0: All, 1: Dirs Only, 2: Files Only
        self._display_mode = 0
        self._show_hidden = False
        self._search_text = ""
        self._target_root_path = ""
        self._marked_paths_ref = None # set() の外部参照

    def setTargetRootPath(self, path):
        self._target_root_path = os.path.abspath(path).lower()
        self.invalidateFilter()

    def setDisplayMode(self, mode):
        self._display_mode = mode
        self.invalidateFilter()

    def setShowHidden(self, show):
        self._show_hidden = show
        self.invalidateFilter()
        
    def setSearchText(self, text):
        self._search_text = text.lower()
        # 標準のフィルタ機能を使って再帰検索を有効にする
        self.setFilterFixedString(text)
        self.invalidateFilter()
        
    def setMarkedPathsRef(self, marked_set):
        """マークされたパスのセット（外部参照）を設定"""
        self._marked_paths_ref = marked_set
        self.updateMarkedCache()

    def updateMarkedCache(self):
        """v19.3 Optimization: マーク済みパスの高速照合用キャッシュを構築"""
        self._marked_cache = set()
        if self._marked_paths_ref:
            for p in self._marked_paths_ref:
                # 念のため標準化して登録
                self._marked_cache.add(os.path.normcase(os.path.normpath(p)))
                # 生のパスも登録（ヒット率向上）
                self._marked_cache.add(p)

    def data(self, index, role=Qt.DisplayRole):
        """見た目のカスタマイズ（マークされた行に色をつける）"""
        if role == Qt.BackgroundRole and self._marked_paths_ref:
            # v19.3 Optimization: 高速キャッシュを使用
            if not getattr(self, '_marked_cache', None):
                return super().data(index, role)

            col0_idx = index.siblingAtColumn(0)
            source_idx = self.mapToSource(col0_idx)
            model = self.sourceModel()
            
            if hasattr(model, 'filePath'):
                # QFileSystemModelの返すパスをそのまま使う（高速）
                raw_path = model.filePath(source_idx)
                if raw_path:
                    # まずはそのまま照合
                    if raw_path in self._marked_cache:
                         from PySide6.QtGui import QColor
                         return QColor(80, 20, 20)
                    
                    # ダメなら正規化して照合（これ自体もキャッシュ内にあるはずなので、変換コストだけで済む）
                    # normcase だけは必須（Windows対応）
                    norm_path = os.path.normcase(os.path.normpath(raw_path))
                    if norm_path in self._marked_cache:
                        from PySide6.QtGui import QColor
                        return QColor(80, 20, 20)
        
        return super().data(index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        """行を表示するかどうかの判定"""
        # 親クラスの判定（標準の検索フィルタ + Recursive）をまず確認
        if self._search_text:
            if not super().filterAcceptsRow(source_row, source_parent):
                return False
        
        # ここから先は「検索にはヒットしている（またはヒットする子を持つ）」要素に対する
        # 追加のフィルタリング（Dotファイル隠し、モード別表示）
        
        model = self.sourceModel()
        idx = model.index(source_row, 0, source_parent)
        
        if isinstance(model, QFileSystemModel):
            # Optimization v21.1: Use QFileInfo directly to avoid absoluteFilePath() if not needed.
            # name processing for dot files
            name = model.fileName(idx)
            if name.startswith('.') and name not in ['.', '..']:
                if not self._show_hidden:
                    return False
            
            # Mode check
            is_dir = model.isDir(idx)
            should_hide_by_mode = False
            if self._display_mode == 1: # Dirs Only
                if not is_dir: should_hide_by_mode = True
            elif self._display_mode == 2: # Files Only
                if is_dir: should_hide_by_mode = True

            if not should_hide_by_mode:
                return True

            # If we need to hide but it might be an ancestor of target root
            if self._target_root_path:
                file_path = model.filePath(idx).lower()
                if file_path == self._target_root_path:
                    return True
                if self._target_root_path.startswith(file_path + os.sep) or \
                   (file_path.endswith(os.sep) and self._target_root_path.startswith(file_path)):
                     return True

            return False
                
        return True # super()を通過し、ここまでの条件もクリアしたら表示

    def lessThan(self, left, right):
        """ソートロジックの強化"""
        model = self.sourceModel()
        if isinstance(model, QFileSystemModel):
            left_info = model.fileInfo(left)
            right_info = model.fileInfo(right)
            
            # フォルダは常に上位に来るようにする (Explorerライク)
            if left_info.isDir() and not right_info.isDir():
                return self.sortOrder() == Qt.AscendingOrder
            if not left_info.isDir() and right_info.isDir():
                return self.sortOrder() != Qt.AscendingOrder
                
            col = left.column()
            # 3: Date
            if col == 3:
                return left_info.lastModified() < right_info.lastModified()
            # 1: Size
            if col == 1:
                return left_info.size() < right_info.size()
                
        return super().lessThan(left, right)

    # --- Async Icon Loading Integration (v21.1) ---

    def data(self, index, role=Qt.DisplayRole):
        """見た目のカスタマイズ（マークされた行に色をつける・アイコン非同期読込）"""
        
        # v21.1 Optimization: Cache IconLoader instance
        if not hasattr(self, '_cached_icon_loader'):
            from core.icon_loader import get_icon_loader
            self._cached_icon_loader = get_icon_loader()
            self._cached_icon_loader.signals.icon_loaded.connect(self._on_icon_loaded)

        # 1. Background Color for Marked Items
        if role == Qt.BackgroundRole and self._marked_paths_ref:
            if not getattr(self, '_marked_cache', None):
                return super().data(index, role)

            col0_idx = index.siblingAtColumn(0)
            source_idx = self.mapToSource(col0_idx)
            model = self.sourceModel()
            
            if hasattr(model, 'filePath'):
                raw_path = model.filePath(source_idx)
                if raw_path:
                    if raw_path in self._marked_cache:
                         from PySide6.QtGui import QColor
                         return QColor(80, 20, 20)
                    
                    norm_path = os.path.normcase(os.path.normpath(raw_path))
                    if norm_path in self._marked_cache:
                        from PySide6.QtGui import QColor
                        return QColor(80, 20, 20)

        # 2. Async Icon Loading (Qt.DecorationRole)
        # Only for column 0 (Name)
        if role == Qt.DecorationRole and index.column() == 0:
            model = self.sourceModel()
            if isinstance(model, QFileSystemModel):
                source_idx = self.mapToSource(index)
                file_path = model.filePath(source_idx)
                
                if file_path:
                    # Try to get icon from cached loader
                    icon, is_ready = self._cached_icon_loader.get_icon(file_path)
                    return icon
        
        return super().data(index, role)

    def _on_icon_loaded(self, path, icon):
        """Slot: When icon is ready, notify the view to repaint."""
        # We need to find the index for this path.
        # This is the tricky part: mapping path -> proxy index.
        # We can scan visible items? No, that's slow.
        # But signals are frequent.
        
        # Optimization: Only trigger update if the path is actually in the current model filter.
        # And finding the index from path in Proxy is hard without source model help.
        
        source_model = self.sourceModel()
        if isinstance(source_model, QFileSystemModel):
            source_idx = source_model.index(path)
            if source_idx.isValid():
                proxy_idx = self.mapFromSource(source_idx)
                if proxy_idx.isValid():
                    # Notify that DecorationRole changed for column 0
                    self.dataChanged.emit(proxy_idx, proxy_idx, [Qt.DecorationRole])
