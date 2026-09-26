import os
import sys
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import (Qt, QSortFilterProxyModel, QModelIndex, QDateTime, 
                            QTimer, Signal, QRect, QDir)
from PySide6.QtGui import QColor, QPixmap, QIcon, QPainter, QFont, QPen

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

        def _make_folder_shortcut_icon(base_color_hex, label="D"):
            """フォルダアイコンにショートカットバッジ（矢印）を付与したアイコンを生成"""
            pm = QPixmap(icon_size, icon_size)
            pm.fill(Qt.transparent)
            painter = QPainter(pm)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Base Folder Icon
            painter.setBrush(QColor(base_color_hex))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(1, 1, icon_size - 2, icon_size - 2, 3, 3)
            
            # Label
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Segoe UI", 6, QFont.Bold))
            painter.drawText(pm.rect(), Qt.AlignCenter, label)
            
            # Shortcut Badge (Bottom Left)
            badge_size = 6
            badge_rect = QRect(0, icon_size - badge_size, badge_size, badge_size)
            painter.setBrush(QColor("#007acc")) # Blue badge
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(badge_rect, 1, 1)
            
            # Draw tiny arrow inside badge
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawLine(1, icon_size - 2, 4, icon_size - 5) # Diagonal line
            painter.drawLine(4, icon_size - 5, 2, icon_size - 5) # Arrow head logic (simplified)
            painter.drawLine(4, icon_size - 5, 4, icon_size - 3)
            
            painter.end()
            return QIcon(pm)

        cls._FOLDER_ICON = _make_color_icon("#e8a838", "D")
        cls._FOLDER_SHORTCUT_ICON = _make_folder_shortcut_icon("#e8a838", "D")

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
        self._shortcut_folder_cache = {} # v23.4 path -> bool (is it a folder shortcut?)

        # v23.5 Rank Cache: フォルダを開いた際に一括計算した順位テーブル
        # v23.8: 鍵を (親フォルダのノードID, sort_col) に変更。共有 QFileSystemModel は
        # ドライブ階層から表示中フォルダまで同一プロキシで比較が走るため、単一の
        # テーブルでは取り違えが起きていた。親ごとに保持して取り違えを無くす。
        self._rank_tables = {}   # (parent_internal_id, sort_col) -> {path: rank}
        self._RANK_TABLE_LIMIT = 16

        # v23.10: 自分たちで消した(移動・削除した)ことが分かっているパス。
        # QFileSystemModel はフォルダの変更通知を受けて行を消すが、SMB 共有では
        # 通知が届かないことがあり、移動元に消えたはずの行が残り続けていた。
        # 通知を待たず、操作した側が「これは消えた」と宣言して伏せるための集合。
        # os.path.normcase 済みのパスを入れる。
        self._vanished_paths = set()

        # v23.10: dataChanged はフォルダ読み込み中に大量に飛ぶ。1回ごとに
        # 再ソートするとロードが目に見えて重くなるため、短い間隔でまとめる。
        self._sort_refresh_timer = QTimer(self)
        self._sort_refresh_timer.setSingleShot(True)
        self._sort_refresh_timer.setInterval(120)
        self._sort_refresh_timer.timeout.connect(self.invalidate)

    def setSourceModel(self, model):
        super().setSourceModel(model)
        # v23.6: QFileSystemModelは非同期に行を追加するため、表示中フォルダの内容が
        # 変化したらランクキャッシュを無効化する。これがないと初回ソート時点の
        # 部分的な内容でキャッシュが固定され、ロード完了分が毎回フォールバック比較になる。
        if isinstance(model, QFileSystemModel):
            model.directoryLoaded.connect(self._on_source_dir_loaded)
            # AboutToBeInserted で無効化しておくと、挿入処理中の再ソート時に
            # 全内容（新規行込み）でキャッシュが再構築される
            model.rowsAboutToBeInserted.connect(self._on_source_rows_inserted)
            model.rowsAboutToBeRemoved.connect(self._on_source_rows_removed)
            # v23.10: 伏せ札の外し判定は「挿入後」でなければならない。
            # rowsAboutToBeInserted の時点では行がまだ無く、filePath() が
            # 目的のパスを返さないため判定できない。
            model.rowsInserted.connect(self._on_source_rows_did_insert)
            # v23.10: 既存ファイルの中身が書き換わった場合 (ZIP の作り直し、
            # 同名への上書きコピーなど) は行の増減が起きないため、上の3つの
            # シグナルはどれも飛ばない。QFileSystemModel 自体は監視で気付いて
            # 表示を更新するが、こちらのメタデータ/ランク表は古い更新日時を
            # 抱えたままになり、日付ソートの順位が動かなかった。
            model.dataChanged.connect(self._on_source_data_changed)

    def mark_paths_vanished(self, paths):
        """v23.10: 移動・削除で消えたパスを一覧から伏せる。

        ネットワーク共有では QFileSystemModel に変更通知が届かないことがあり、
        待っていても行が消えない。実体が無いことは操作した側が知っているので、
        存在確認(ネットワークでは重く、かつ当てにならない)はせずに宣言する。
        """
        if not paths:
            return
        for path in paths:
            if path:
                self._vanished_paths.add(os.path.normcase(os.path.normpath(path)))
        self._native_cache.clear()
        self._invalidate_rank_cache()
        self.invalidateFilter()

    def unmark_paths_vanished(self, paths):
        """v23.10: 同じ場所に作り直された場合に、伏せるのをやめる。"""
        if not paths or not self._vanished_paths:
            return
        for path in paths:
            if path:
                self._vanished_paths.discard(
                    os.path.normcase(os.path.normpath(path)))
        self.invalidateFilter()

    def _revalidate_vanished(self, candidates):
        """v23.10: 伏せている行に動きがあったら、実体が戻っていないか確かめる。

        同じ名前で作り直された場合 (ZIP の作り直しなど)、Qt は行を消して
        足し直すのではなく、元の行を更新するだけで済ませることがある。
        その場合 rowsInserted が飛ばないため、伏せたままになって
        「実体はあるのに一覧に出ない」状態になっていた。

        存在確認をするのは伏せている数件だけで、一覧の全行は見ない。
        ネットワーク上でも件数が知れているため、ここでは確認してよい。
        """
        if not self._vanished_paths or not candidates:
            return False
        restored = [key for key in candidates
                    if key in self._vanished_paths and os.path.exists(key)]
        if not restored:
            return False
        for key in restored:
            self._vanished_paths.discard(key)
        return True

    def revalidate_all_vanished(self):
        """v23.10: 伏せている全パスを確かめ直す。F5 のときに呼ばれる。"""
        if not self._vanished_paths:
            return
        if self._revalidate_vanished(list(self._vanished_paths)):
            self.invalidateFilter()

    def _on_source_data_changed(self, top_left, bottom_right, roles=None):
        """v23.10: 更新された行のメタデータキャッシュを捨て、並べ替えをやり直す。

        フォルダの読み込み中は行ごとに何度も飛んでくるため、ここでは捨てるだけに
        留め、実際の再ソートは _sort_refresh_timer で一度にまとめる。
        """
        if not top_left.isValid():
            return

        model = self.sourceModel()
        if not isinstance(model, QFileSystemModel):
            return

        parent = top_left.parent()
        touched = []
        try:
            for row in range(top_left.row(), bottom_right.row() + 1):
                path = model.filePath(model.index(row, 0, parent))
                if path:
                    self._native_cache.pop(path, None)
                    if self._vanished_paths:
                        touched.append(
                            os.path.normcase(os.path.normpath(path)))
            self._drop_rank_tables_for(parent.internalId())
        except Exception:
            self._native_cache.clear()
            self._invalidate_rank_cache()

        # v23.10: 伏せている行が更新されたなら、同じ名前で作り直された
        # 可能性がある。実体が戻っていれば再び見せる。
        if touched and self._revalidate_vanished(touched):
            self.invalidateFilter()

        # 連続して飛んでくる dataChanged を1回の再ソートにまとめる
        self._sort_refresh_timer.start()

    def _invalidate_rank_cache(self):
        self._rank_tables.clear()

    def _drop_rank_tables_for(self, parent_id):
        """v23.8: 特定の親フォルダのランク表だけを捨てる（列ごとに複数あり得る）"""
        if not self._rank_tables:
            return
        for key in [k for k in self._rank_tables if k[0] == parent_id]:
            del self._rank_tables[key]

    def _on_source_dir_loaded(self, path):
        # 非同期ロードが完了した時点で、そのフォルダのランク表を作り直させる
        if not self._rank_tables:
            return
        model = self.sourceModel()
        try:
            self._drop_rank_tables_for(model.index(path).internalId())
        except Exception:
            self._invalidate_rank_cache()

    def _on_source_rows_did_insert(self, parent, first, last):
        """v23.10: 行が実際に入ったあとで、伏せ札を外せるか確かめる。

        伏せていたパスと同じ場所にファイルが現れたら、実体が戻ったという
        ことなので再び見せる(ZIP の作り直し、移動 -> 貼り直しなど)。
        """
        if not self._vanished_paths:
            return
        model = self.sourceModel()
        try:
            inserted = []
            for row in range(first, last + 1):
                path = model.filePath(model.index(row, 0, parent))
                if path:
                    inserted.append(os.path.normcase(os.path.normpath(path)))
            if self._revalidate_vanished(inserted):
                self.invalidateFilter()
        except Exception:
            pass

    def _on_source_rows_inserted(self, parent, first, last):
        if not self._rank_tables:
            return
        try:
            self._drop_rank_tables_for(parent.internalId())
        except Exception:
            self._invalidate_rank_cache()

    def _on_source_rows_removed(self, parent, first, last):
        # 行の削除はノードの解放を伴い、内部IDが再利用され得る。
        # 取り違えを避けるため、この場合のみ全テーブルを捨てる。
        self._invalidate_rank_cache()

    def clear_native_cache(self):
        """v23.4.1: ネイティブキャッシュを強制クリアする。ファイル操作後のリフレッシュ時に使用。

        v23.10: _vanished_paths はここでは消さない。変更通知が届かない共有では
        リフレッシュしても行は戻ってこないため、捨てるとゴーストが復活する。
        """
        self._native_cache.clear()
        self._shortcut_folder_cache.clear()
        self._rank_tables.clear()
        # v23.10: 伏せている数件だけは確かめ直す。取りこぼしがあっても
        # F5 で必ず正しい状態に戻れるようにするための逃げ道。
        self.revalidate_all_vanished()

    def setTargetRootPath(self, path):
        # v23.1: Windowsのパス揺らぎを防ぐため、完全に正規化して保持
        self._target_root_path = os.path.normpath(os.path.abspath(path)).lower()
        self._native_cache.clear()
        self._shortcut_folder_cache.clear() # v23.4 キャッシュクリア
        self._rank_tables.clear()
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
        # v23.6 Performance: setFilterFixedString が内部で invalidate するため、
        # 追加の invalidateFilter() は不要（1キーストロークで2回全行フィルタが走っていた）
        self.setFilterFixedString(text)
        
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
                # v23.6 Performance: フルパス文字列の生成(filePath)を避け、
                # ファイル名のみで拡張子・ショートカット判定を行う
                name = model.fileName(source_idx)

                if name and name.lower().endswith('.lnk'):
                    return self._FOLDER_SHORTCUT_ICON

                if model.isDir(source_idx):
                    return self._FOLDER_ICON

                if name:
                    ext = os.path.splitext(name)[1].lower()
                    return self._ICON_MAP.get(ext, self._DEFAULT_ICON)

        # 3. v23.4 Display Text Customization (Name & Type column)
        # v23.6 Performance: 対象は列0(Name)と列2(Type)のみ。他の列（サイズ・日付）は
        # mapToSource/filePath を呼ばずに即返す。列0は表示名だけで .lnk 判定できるため
        # フルパス生成を完全に省略する（全セル描画のホットパス）。
        if role == Qt.DisplayRole:
            col = index.column()
            if col == 0:
                actual_name = super().data(index, role)
                if isinstance(actual_name, str) and actual_name.lower().endswith(".lnk"):
                    # 名前列: .lnk を取り除いて表示（完全にフォルダに見せる）
                    return actual_name[:-4]
                return actual_name
            if col == 2:
                model = self.sourceModel()
                if isinstance(model, QFileSystemModel):
                    source_idx = self.mapToSource(index.siblingAtColumn(0))
                    name = model.fileName(source_idx)
                    if name and name.lower().endswith(".lnk"):
                        # Type列: フォルダとして表示
                        return "File Folder"

        return super().data(index, role)

    def _check_if_folder_shortcut(self, path):
        """v23.4: I/O ゼロ版: 拡張子が .lnk かどうかのみを判定する。
        （実体の解析はUIスレッドをブロックするため、ここでは行わない）
        """
        if not path:
            return False
        return path.lower().endswith('.lnk')

    def filterAcceptsRow(self, source_row, source_parent):
        """行を表示するかどうかの判定"""
        model = self.sourceModel()
        idx = model.index(source_row, 0, source_parent)

        if not isinstance(model, QFileSystemModel):
            return True

        # v23.10: 移動・削除で消えたと分かっている行を伏せる。
        # 集合が空のときは何もしないので、通常の表示ではコストがかからない。
        if self._vanished_paths:
            raw = model.filePath(idx)
            if raw and os.path.normcase(os.path.normpath(raw)) in self._vanished_paths:
                return False

        # v23.4.1: [最優先] 現在のターゲット（表示フォルダ）とその祖先は常に許可する。
        # これを最初に行うことで、検索キーワードにフォルダ名が含まれていない場合に
        # 表示中のフォルダがフィルタで消され、ビューがルートに飛ばされるのを防ぐ。
        if self._target_root_path:
            raw_path = model.filePath(idx)
            # v23.5 Performance: 祖先パスは必ずターゲットパス以下の長さになるため、
            # 明らかに子孫/兄弟(＝長い方)である行は正規化コスト(normpath/lower)を
            # かけずに素通りさせる。閾値には多少の余裕(+2)を持たせて誤判定を防ぐ。
            if raw_path and len(raw_path) <= len(self._target_root_path) + 2:
                # Windowsのパスの揺らぎを完全に排除するための徹底した正規化
                file_path = os.path.normpath(raw_path).lower().rstrip(os.sep)
                target_path = self._target_root_path.rstrip(os.sep)

                # 1. 自分がターゲットルートそのもの、またはその「先祖」なら無条件で表示
                # ※os.sepを付与して比較することで、部分一致（例: F-STAT と F-STAT-BAK）を確実に防ぐ
                if file_path == target_path or (target_path + os.sep).startswith(file_path + os.sep):
                    return True

        # v22.1 Performance: 検索なし + All表示 + 隠しファイル表示 の場合は即通過
        if not self._search_text and self._display_mode == 0 and self._show_hidden:
            return True

        # 親クラスの判定（標準の検索フィルタ）を確認
        if self._search_text:
            if not super().filterAcceptsRow(source_row, source_parent):
                return False
        
        # 隠しファイルチェック
        name = model.fileName(idx)
        if name.startswith('.') and name not in ['.', '..']:
            if not self._show_hidden:
                return False
        
        # v22.1 Performance: All表示ならここまでのチェック通過後は即通過
        if self._display_mode == 0:
            return True

        # 表示モード（フォルダのみ、ファイルのみ）のチェック
        is_dir = model.isDir(idx)
        if self._display_mode == 1: # Dirs Only
            if not is_dir: return False
        elif self._display_mode == 2: # Files Only
            if is_dir: return False

        return True # すべての条件をクリア

    def lessThan(self, left, right):
        """ソートロジックの強化（v23.4: フォルダ固定＋Native対応）
        
        注意: Qt の lessThan() に渡される left, right は
        **既にソースモデルのインデックス**である。mapToSource() は不要。
        """
        model = self.sourceModel()
        if isinstance(model, QFileSystemModel):
            # 列によらず正確に判定するため siblingAtColumn(0) を経由
            idx_left_0 = left.siblingAtColumn(0)
            idx_right_0 = right.siblingAtColumn(0)
            
            # ディレクトリ判定（v23.4: I/O ゼロのため、ショートカットはファイルとして扱う）
            is_left_dir = model.isDir(idx_left_0)
            is_right_dir = model.isDir(idx_right_0)

            # フォルダ vs ファイルの比較: ソート順に関わらず常にフォルダを上部に固定
            # v23.8 Performance: この早期判定は全比較の約4割を占め、パス文字列を必要と
            # しない。filePath() の呼び出しはここを抜けた後まで遅延させる。
            if is_left_dir != is_right_dir:
                if self.sortOrder() == Qt.AscendingOrder:
                    return is_left_dir  # フォルダが「小さい」= 上に来る
                else:
                    return is_right_dir  # 降順時は反転させてフォルダを上に保つ

            # ----------------------------------------------------
            # ディレクトリ同士、またはファイル同士の比較
            # ----------------------------------------------------
            # v23.5: 一括計算済みランクテーブルを使ったO(1)比較（高速パス）
            if _HAVE_NATIVE_CORE:
                col = left.column()
                # v23.8 Fix: ランク表は「実際に比較している親フォルダ」ごとに保持する。
                # 旧実装は鍵に self._target_root_path（そのビューが表示中のフォルダ）を
                # 使っていたため、共有 QFileSystemModel の都合で最初の比較がドライブ階層
                # だった場合、ルートのランク表に表示中フォルダの鍵が刻まれて永久に
                # 食い違い、以降すべての比較が低速フォールバックへ落ちていた。
                ranks = self._rank_table_for(left.parent(), col)
                if ranks:
                    # v23.8 Performance: ランク表のキーはノードID（整数）。
                    # 以前はフルパス文字列をキーにしていたため、比較のたびに
                    # filePath() が2回走り、大フォルダでは全体の最大コストになっていた
                    # （33,788件で filePath 約177万回）。IDならパス生成が不要。
                    left_rank = ranks.get(idx_left_0.internalId())
                    right_rank = ranks.get(idx_right_0.internalId())
                    if left_rank is not None and right_rank is not None:
                        return left_rank < right_rank

                # キャッシュ構築後に増えたアイテムなど、未登録の場合のフォールバック
                m_left = self._get_native_metadata(left)
                m_right = self._get_native_metadata(right)
                if m_left and m_right:
                    return chainflow_core.compare_items(
                        m_left, m_right, col
                    )

            # Fallback to pure Python/Qt
            left_path = model.filePath(left)
            right_path = model.filePath(right)
            left_info = model.fileInfo(left)
            right_info = model.fileInfo(right)
            
            col = left.column()
            # 3: Date
            if col == 3:
                return left_info.lastModified() < right_info.lastModified()
            # 2: Type (Extension)
            if col == 2:
                # 拡張子を取得して比較（フォルダは空、ファイルは .ext）
                l_ext = os.path.splitext(left_path)[1].lower() if left_path else ""
                r_ext = os.path.splitext(right_path)[1].lower() if right_path else ""
                return l_ext < r_ext
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
            # 列によらず正確に判定するため siblingAtColumn(0) を使用
            is_dir = model.isDir(index.siblingAtColumn(0))
            # ショートカットはファイルとして扱う (I/O ゼロ)
                
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

    def _rank_table_for(self, parent_index, sort_col):
        """v23.8: 親フォルダ単位のランク表を返す（無ければ構築してキャッシュ）。

        旧 _build_rank_cache は単一のテーブルと、それとは無関係な鍵
        (target_root_path, sort_col) を持っていたため、共有 QFileSystemModel 上で
        ドライブ階層の比較が先に走ると「ルートのランク表」に「表示中フォルダの鍵」が
        刻まれ、以降そのビューの高速パスが永久に無効化されていた。
        鍵を実際の親ノードに一致させることでこの取り違えを無くす。
        """
        key = (parent_index.internalId(), sort_col)
        table = self._rank_tables.get(key)
        if table is None:
            table = self._build_rank_table(parent_index, sort_col)
            # 際限なく増えないように上限を設ける（フォルダを渡り歩いた場合の保険）
            if len(self._rank_tables) >= self._RANK_TABLE_LIMIT:
                self._rank_tables.clear()
            self._rank_tables[key] = table
        return table

    def _build_rank_table(self, parent_index, sort_col):
        """v23.5: 指定フォルダの子要素を一括取得し、Rust側で1回だけソートして
        path -> rank の辞書を作る。lessThan() の逐次ネイティブ呼び出しを避けるための
        事前計算パス。失敗時は空辞書を返し、呼び出し元でフォールバックする。

        非同期ロード途中で空／部分的な表になった場合は、directoryLoaded と
        rowsInserted のシグナルで破棄され、次回呼び出し時に作り直される。
        """
        model = self.sourceModel()
        try:
            row_count = model.rowCount(parent_index)
            node_ids = []
            metadata = []
            for row in range(row_count):
                idx = model.index(row, 0, parent_index)
                # v23.8: 表の構築でも filePath() を使わない。
                # FileMetadata が必要とするのはベース名だけなので fileName() で足りる。
                name = model.fileName(idx)
                if not name:
                    continue
                is_dir = model.isDir(idx)
                size = model.size(idx)
                modified = model.lastModified(idx).toMSecsSinceEpoch()
                node_ids.append(idx.internalId())
                metadata.append(chainflow_core.FileMetadata(
                    name, is_dir, size, modified
                ))

            order = chainflow_core.compute_rank_order(metadata, sort_col)
            return {node_ids[k]: rank for rank, k in enumerate(order)}
        except Exception:
            return {}
