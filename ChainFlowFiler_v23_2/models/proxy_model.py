import os
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QColor, QPixmap, QIcon, QPainter, QFont

# v23.0 Native Performance: Load Rust-based native core
try:
    import chainflow_core
    _HAVE_NATIVE_CORE = True
except ImportError:
    # 開発環境やビルド直後等でインポートできない場合のフォールバック
    import sys
    import os
    # models/../native/target/release 等を探索
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(base_dir, "native", "target", "release")
    if target_path not in sys.path:
        sys.path.append(target_path)
    
    try:
        import chainflow_core
        _HAVE_NATIVE_CORE = True
    except ImportError:
        _HAVE_NATIVE_CORE = False

class SmartSortFilterProxyModel(QSortFilterProxyModel):
    """
    高度なソートとフィルタリングを提供するProxyモデル
    QFileSystemModelの非同期性やフィルタの癖を吸収し、即時反映を実現する。
    v22.1 Performance: アイコンを拡張子ベースの固定マップに変更（I/Oゼロ化）
    """

    # === クラス変数: 拡張子→アイコンの静的マップ（全インスタンスで共有） ===
    _ICON_MAP = None
    _FOLDER_ICON = None
    _DEFAULT_ICON = None

    @classmethod
    def _init_icon_map(cls):
        """拡張子→QIconマップを初期化（起動時に1回だけ）"""
        if cls._ICON_MAP is not None:
            return  # 既に初期化済み

        icon_size = 16

        def _make_icon(text, bg_color=None):
            """絵文字テキストからQIconを生成"""
            pm = QPixmap(icon_size, icon_size)
            pm.fill(Qt.transparent)
            painter = QPainter(pm)
            if bg_color:
                painter.fillRect(0, 0, icon_size, icon_size, QColor(bg_color))
            painter.setFont(QFont("Segoe UI Emoji", 10))
            painter.drawText(pm.rect(), Qt.AlignCenter, text)
            painter.end()
            return QIcon(pm)

        def _make_color_icon(color_hex, label=""):
            """色付きの小さなアイコンを生成"""
            pm = QPixmap(icon_size, icon_size)
            pm.fill(Qt.transparent)
            painter = QPainter(pm)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(color_hex))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(1, 1, icon_size - 2, icon_size - 2, 3, 3)
            if label:
                painter.setPen(QColor("#ffffff"))
                painter.setFont(QFont("Segoe UI", 6, QFont.Bold))
                painter.drawText(pm.rect(), Qt.AlignCenter, label)
            painter.end()
            return QIcon(pm)

        cls._FOLDER_ICON = _make_color_icon("#e8a838", "D")

        # 拡張子マッピング
        ext_groups = {
            # テキスト・ドキュメント系
            "#5c9fd4": {  # 青
                "label": "T",
                "exts": [".txt", ".md", ".log", ".ini", ".cfg", ".conf", ".yaml", ".yml", ".toml"]
            },
            # コード系
            "#4ec9b0": {  # 緑
                "label": "<>",
                "exts": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".bat", ".sh",
                         ".ps1", ".c", ".cpp", ".h", ".java", ".cs", ".rb", ".go", ".rs", ".php",
                         ".vue", ".jsx", ".tsx", ".sql", ".r", ".swift", ".kt"]
            },
            # 画像系
            "#c27fd6": {  # 紫
                "label": "Im",
                "exts": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico", ".webp", ".tiff", ".tif"]
            },
            # 表計算・データ系
            "#6ab04c": {  # 緑(明)
                "label": "XL",
                "exts": [".xlsx", ".xls", ".csv", ".tsv", ".ods"]
            },
            # PDF
            "#e74c3c": {  # 赤
                "label": "PDF",
                "exts": [".pdf"]
            },
            # Word系
            "#2b5797": {  # 濃い青
                "label": "W",
                "exts": [".docx", ".doc", ".odt", ".rtf"]
            },
            # PPT系
            "#d04423": {  # オレンジ
                "label": "P",
                "exts": [".pptx", ".ppt", ".odp"]
            },
            # 音声系
            "#f39c12": {  # 黄
                "label": "♪",
                "exts": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"]
            },
            # 動画系
            "#e056a0": {  # ピンク
                "label": "▶",
                "exts": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"]
            },
            # アーカイブ系
            "#7f8c8d": {  # グレー
                "label": "Z",
                "exts": [".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz", ".lzh"]
            },
            # 実行ファイル系
            "#2c3e50": {  # 濃紺
                "label": "EX",
                "exts": [".exe", ".msi", ".dll", ".sys", ".com"]
            },
        }

        cls._ICON_MAP = {}
        for color, group in ext_groups.items():
            icon = _make_color_icon(color, group["label"])
            for ext in group["exts"]:
                cls._ICON_MAP[ext] = icon

        cls._DEFAULT_ICON = _make_color_icon("#555555", "?")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        # v22.1 Performance: 再帰フィルタリングを無効化（ルート直下のみ表示のため不要）
        self.setRecursiveFilteringEnabled(False)
        # 0: All, 1: Dirs Only, 2: Files Only
        self._display_mode = 0
        self._show_hidden = False
        self._search_text = ""
        self._target_root_path = ""
        self._marked_paths_ref = None # set() の外部参照

        # アイコンマップの初期化（クラス共有、1回だけ）
        SmartSortFilterProxyModel._init_icon_map()

        # v23.0 Native Cache
        self._native_cache = {} # path -> FileMetadata

    def setTargetRootPath(self, path):
        # v23.1: Windowsのパス揺らぎを防ぐため、完全に正規化して保持
        self._target_root_path = os.path.normpath(os.path.abspath(path)).lower()
        self._native_cache.clear()
        self.invalidateFilter()

    def setDisplayMode(self, mode):
        self._display_mode = mode
        self.invalidateFilter()

    def setShowHidden(self, show):
        self._show_hidden = show
        self.invalidateFilter()
        
    def setSearchText(self, text):
        self._search_text = text.lower()
        # 標準のフィルタ機能を使って検索を有効にする
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
        """見た目のカスタマイズ（マークされた行に色をつける・拡張子ベースアイコン）"""

        # 1. Background Color for Marked Items
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
                         return QColor(80, 20, 20)
                    
                    # ダメなら正規化して照合
                    norm_path = os.path.normcase(os.path.normpath(raw_path))
                    if norm_path in self._marked_cache:
                        return QColor(80, 20, 20)
        
        # 2. v22.1 Performance: 拡張子ベースの固定アイコン（I/Oゼロ）
        if role == Qt.DecorationRole and index.column() == 0:
            model = self.sourceModel()
            if isinstance(model, QFileSystemModel):
                source_idx = self.mapToSource(index)
                if model.isDir(source_idx):
                    return self._FOLDER_ICON
                file_path = model.filePath(source_idx)
                if file_path:
                    ext = os.path.splitext(file_path)[1].lower()
                    return self._ICON_MAP.get(ext, self._DEFAULT_ICON)

        return super().data(index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        """行を表示するかどうかの判定"""

        # v22.1 Performance: 検索なし + All表示 + 隠しファイル表示 の場合は即通過
        if not self._search_text and self._display_mode == 0 and self._show_hidden:
            return True

        # 親クラスの判定（標準の検索フィルタ）をまず確認
        if self._search_text:
            if not super().filterAcceptsRow(source_row, source_parent):
                return False
        
        # 検索なし + All表示（隠しファイル非表示）の場合、ドットファイルチェックのみ
        model = self.sourceModel()
        idx = model.index(source_row, 0, source_parent)
        
        if isinstance(model, QFileSystemModel):
            # name processing for dot files
            name = model.fileName(idx)
            if name.startswith('.') and name not in ['.', '..']:
                if not self._show_hidden:
                    return False
            
            # v22.1 Performance: All表示なら隠しファイルチェック通過後は即通過
            if self._display_mode == 0:
                return True

            # Mode check
            is_dir = model.isDir(idx)
            should_hide_by_mode = False
            if self._display_mode == 1: # Dirs Only
                if not is_dir: should_hide_by_mode = True
            elif self._display_mode == 2: # Files Only
                if is_dir: should_hide_by_mode = True

            if not should_hide_by_mode:
                return True

            # フォルダを非表示にする設定の時でも、
            # 「現在地（ルート）」とその「先祖」だけは表示を許可しないと、中身が見えなくなる。
            if self._target_root_path:
                raw_path = model.filePath(idx)
                if raw_path:
                    # Windowsのパスの揺らぎを完全に排除するための徹底した正規化
                    # 例: C:/A, C:\A, c:\a, C:\A\ などを全て同じものとして扱う
                    file_path = os.path.normpath(raw_path).lower().rstrip(os.sep)
                    target_path = self._target_root_path.rstrip(os.sep)
                    
                    # 1. 自分がターゲットルートそのものなら表示
                    if file_path == target_path:
                        return True
                    
                    # 2. 自分がターゲットルートの「先祖」なら表示
                    # ※os.sepを付与して比較することで、部分一致（F-STAT と F-STAT-BACKUP など）を確実に防ぐ
                    target_with_sep = target_path + os.sep
                    file_with_sep = file_path + os.sep
                    if target_with_sep.startswith(file_with_sep):
                        return True

            return False
                
        return True # super()を通過し、ここまでの条件もクリアしたら表示

    def lessThan(self, left, right):
        """ソートロジックの強化（v23.0 Native対応）"""
        model = self.sourceModel()
        if isinstance(model, QFileSystemModel):
            if _HAVE_NATIVE_CORE:
                m_left = self._get_native_metadata(left)
                m_right = self._get_native_metadata(right)
                if m_left and m_right:
                    # Rustエンジンで高速比較（v23.1: 昇順固定で渡し、反転はQtに任せる）
                    return chainflow_core.compare_items(
                        m_left, m_right, left.column()
                    )

            # Fallback to pure Python/Qt
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

    def _get_native_metadata(self, index):
        """インデックスに対応するFileMetadataを取得（キャッシュ利用）"""
        model = self.sourceModel()
        path = model.filePath(index)
        if not path: return None
        
        if path in self._native_cache:
            return self._native_cache[path]
        
        # なければ作成して登録
        try:
            is_dir = model.isDir(index)
            # QFileSystemModelがまだ情報を取得していない場合はデフォルト値
            size = model.size(index)
            modified = model.lastModified(index).toMSecsSinceEpoch()
            
            meta = chainflow_core.FileMetadata(
                os.path.basename(path),
                is_dir,
                size,
                modified
            )
            self._native_cache[path] = meta
            return meta
        except Exception:
            return None
