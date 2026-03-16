import os
import shutil
import zipfile
import subprocess
import sys
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QWidget, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QScrollArea, QSplitter, 
                               QTreeView, QHeaderView, QMenu, QInputDialog, QMessageBox,
                               QSizePolicy, QApplication, QFileSystemModel, QStyledItemDelegate, 
                               QAbstractItemView, QProgressDialog)
from PySide6.QtCore import Qt, QDir, QSize, QTimer, QEvent, QUrl, QMimeData, QModelIndex, QRect
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QShortcut, QDrag, QIcon, QPixmap, QColor, QPainter, QImage

from models.proxy_model import SmartSortFilterProxyModel
from core import same_path, FileOperationWorker, logger
from core.global_model import get_global_file_system_model

# v14.2 Refactoring: Classes extracted to subpackage for maintainability
from .highlight_delegate import HighlightDelegate
from .batch_tree_view import BatchTreeView
from .context_menu import ContextMenuBuilder


# (HighlightDelegate, BatchTreeView, and ContextMenuBuilder moved to file_pane/ subpackage)


class FilePane(QFrame):
    """個別のファイルペイン（縦割り）"""
    def __init__(self, title="Flow", parent_filer=None):
        super().__init__()
        self.parent_filer = parent_filer # これはMainWindowを指す想定
        self.setFrameStyle(QFrame.NoFrame)
        self.setObjectName("Pane")
        self.setMouseTracking(True)
        self.setMinimumWidth(100) # 最小幅を設定して「0か1か」を防ぐ
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 固定ヘッダー
        self.header = QWidget()
        self.header.setFixedHeight(30)
        self.header.setObjectName("PaneHeader")
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(10, 0, 5, 0)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; color: #007acc; font-size: 11px;")
        h_layout.addWidget(self.title_label)
        
        # 検索ボックス (インクリメンタルサーチ)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.setFixedWidth(120)
        self.search_box.setStyleSheet("""
            QLineEdit { 
                background: #1e1e1e; color: #ccc; border: 1px solid #333; 
                border-radius: 4px; padding: 2px 5px; font-size: 11px;
            }
            QLineEdit:focus { border: 1px solid #007acc; background: #252526; }
        """)
        self.search_box.textChanged.connect(self.on_search_text_changed)
        h_layout.addWidget(self.search_box)
        
        h_layout.addStretch()
        
        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(20, 20)
        self.up_btn.setStyleSheet("border: none; color: #555; font-weight: bold; background: transparent;")
        self.up_btn.clicked.connect(self.go_up)
        h_layout.addWidget(self.up_btn)
        
        self.main_layout.addWidget(self.header)

        # 全体をスクロール可能にする領域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setObjectName("PaneScrollArea")
        
        # コンテンツを保持する垂直スプリッター
        self.content_splitter = QSplitter(Qt.Vertical)
        self.content_splitter.setObjectName("PaneSplitter")
        self.scroll.setWidget(self.content_splitter)
        
        # ショートカット: Ctrl+F, Esc
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.focus_search)
        QShortcut(QKeySequence("Esc"), self, activated=self.clear_search)
        
        self.main_layout.addWidget(self.scroll)

        # v16.2 Fix: Explicit dark theme styling for dynamically created panes
        self.setStyleSheet("QFrame#Pane { background-color: #1e1e1e; border: none; }")
        self.header.setStyleSheet("QWidget#PaneHeader { background-color: #1e1e1e; }")
        self.scroll.setStyleSheet("QScrollArea#PaneScrollArea { background-color: #1e1e1e; border: none; }")
        self.scroll.viewport().setStyleSheet("background-color: #1e1e1e;")
        self.content_splitter.setStyleSheet("QSplitter#PaneSplitter { background-color: #1e1e1e; }")
        
        # --- Model Architecture Change ---
        # v19 Performance Fix: Use Global Shared Model
        self.base_model = get_global_file_system_model()
        
        # 状態変数
        self.display_mode = 0  
        self.show_hidden = False
        self.current_sort_col = 0
        self.sort_order = Qt.AscendingOrder
        
        self.views = [] # (view, proxy, path, sep_widget) のタプルを保持
        self.current_paths = []
        self.last_selected_paths = [] # 前回選択されていたパス（順序維持用）
        self.is_compact = False # コンパクトモード状態
        # v7.2 Alt+Clickでマークされたパス（永続選択）。
        # FlowArea（タブ単位）で管理される実体への参照を取得する。
        self._marked_paths_ref = None 
        
        self.installEventFilter(self)
        
        # v9.0 スクロール抑止のために子要素も監視
        self.scroll.installEventFilter(self)
        self.scroll.viewport().installEventFilter(self)
        self.content_splitter.installEventFilter(self)
        
        # v14.1 Performance Optimization
        # self._resize_timer は BatchTreeView 側で初期化されるため、ここでは不要

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Wheel:
            # v9.0 Ctrl+Wheelで幅変更、Shift+Wheelで高さ変更
            # どの子要素でホイールしてもここでキャッチして親へ伝播させない
            msg_modifiers = event.modifiers()
            delta = event.angleDelta().y()
            
            if msg_modifiers & Qt.ControlModifier:
                # Ctrl + Wheel -> 横幅変更 (Paneの幅)
                # Laneのスプリッターを取得してサイズ変更
                if hasattr(self, 'parent_lane') and self.parent_lane:
                    splitter = self.parent_lane.splitter
                    idx = splitter.indexOf(self)
                    if idx != -1:
                        sizes = splitter.sizes()
                        # v21.0 Smooth Resize: Use proportional delta instead of fixed step
                        # Standard notch is 120. Factor 0.15 gives ~18px per notch (smoother than old 40px).
                        factor = 0.15
                        change = int(delta * factor)
                        if change == 0 and delta != 0:
                            change = 1 if delta > 0 else -1

                        # 自身(idx)の幅を変えるため、右隣または左隣との境界を動かす必要がある
                        # 基本的に「自身の幅を増やす」=「隣を減らす」
                        # ここでは簡易的に「自分を増減させ、隣接する残りを調整」するが、
                        # QSplitterの挙動上、sizesリスト全体をセットし直すのが確実。
                        
                        if len(sizes) > 1:
                            new_w = sizes[idx] + change
                            if new_w < 50: new_w = 50 # 最小幅ガード
                            
                            # 差分を他のペインから吸い取る（あるいは押し付ける）
                            # 簡単のため「次のペイン」があるならそこと調整、なければ「前のペイン」と調整
                            target_neighbor = idx + 1 if idx + 1 < len(sizes) else idx - 1
                            
                            diff = new_w - sizes[idx]
                            neighbor_w = sizes[target_neighbor] - diff
                            
                            if neighbor_w >= 50: # 隣も最小幅ガード
                                sizes[idx] = new_w
                                sizes[target_neighbor] = neighbor_w
                                splitter.setSizes(sizes)
                                
                                # v12.0: 名前列の幅を再計算 (レイアウト更新後に実行するため少し遅延)
                                QTimer.singleShot(50, self._trigger_column_adjust)
                            
                event.accept()
                return True # イベント消費（スクロールさせない）
                
            elif msg_modifiers & Qt.ShiftModifier:
                # Shift + Wheel -> 高さ変更 (Laneの高さ)
                # Areaのスプリッターを取得してサイズ変更
                if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
                    lane = self.parent_lane
                    area = lane.parent_area
                    splitter = area.vertical_splitter
                    idx = splitter.indexOf(lane)
                    
                    if idx != -1:
                        sizes = splitter.sizes()
                        # v21.0 Smooth Resize
                        factor = 0.15
                        change = int(delta * factor)
                        if change == 0 and delta != 0:
                            change = 1 if delta > 0 else -1
                        
                        if len(sizes) > 1:
                            new_h = sizes[idx] + change
                            if new_h < 50: new_h = 50
                            
                            target_neighbor = idx + 1 if idx + 1 < len(sizes) else idx - 1
                            diff = new_h - sizes[idx]
                            neighbor_h = sizes[target_neighbor] - diff
                            
                            if neighbor_h >= 50:
                                sizes[idx] = new_h
                                sizes[target_neighbor] = neighbor_h
                                splitter.setSizes(sizes)
                                
                event.accept()
                return True # イベント消費（スクロールさせない）

        elif event.type() == QEvent.Enter:
            # v11.1: FilePane自体へのホバー処理
            # Viewへのホバーは BatchTreeView.enterEvent で処理されるため、
            # ここでは「ペインの余白」などにマウスが来た場合の処理、
            # あるいは「ペイン全体のアクティブ化」を担保する。
            
            # Ctrlキーロック
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                return False

            # 親(MainWindow)のアクティブペイン管理を通じて状態更新
            # v14.3 Fix: 構成要素（スクロールエリア等）へのホバーでもペインをアクティブにする
            # 空のフォルダなどでTreeViewがない場合、ここでの判定が重要になる
            if watched == self or watched == self.scroll or watched == self.scroll.viewport() or watched == self.content_splitter:
                self.parent_filer.set_active_pane(self)
                if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
                    self.parent_lane.parent_area.active_lane = self.parent_lane
                
                # Update address bar
                if self.current_paths:
                    self.parent_filer.update_address_bar(self.current_paths[0])
                    
        elif event.type() == QEvent.Leave:
            # v6.4 離れてもアクティブ状態は維持する（他のペインがアクティブになるまで）
            pass
            
        elif event.type() == QEvent.KeyPress:
            # v14.1 Fix: Ctrl+C でクリップボードにコピー (AHK連携用)
            if (event.modifiers() & Qt.ControlModifier) and event.key() == Qt.Key_C:
                # Alt+Ctrl+C は別の機能（Clear Marks）になるのでAltがない場合のみ
                if not (event.modifiers() & Qt.AltModifier):
                    self.copy_selected_to_clipboard()
                    return True
            
            # v7.2 Alt + C で全マーク解除 (eventFilterで確実にキャッチ)
            if (event.modifiers() & Qt.AltModifier) and event.key() == Qt.Key_C:
                self.clear_all_marks()
                return True
            
            # v7.3 Backspace で上の階層へ
            if event.key() == Qt.Key_Backspace:
                self.go_up()
                return True

            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # 監視対象がView（QTreeView）かつEnterが押された場合
                for view, proxy, _, _ in self.views:
                    if watched == view:
                        # v19.1 Fix: 編集中（リネーム中）ならショートカット処理をスキップ
                        # リネーム確定のみを行い、ダブルクリック動作は発火させない
                        if view.state() == QAbstractItemView.EditingState:
                            return False  # Qt標準のリネーム確定処理に任せる
                        
                        idx = view.currentIndex()
                        if idx.isValid():
                            self.on_double_clicked(idx, view)
                        return True # イベントを消費
        
        # v11.0: フォーカスフィードバック（アクティブなViewのセパレータを強調）
        elif event.type() == QEvent.FocusIn:
            # Watched object is a View (BatchTreeView)
            for i, (view, _, _, sep) in enumerate(self.views):
                if watched == view:
                    # Highlight this separator
                    if sep:
                        sep.setStyleSheet("background: #094771; color: #fff; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #007acc; font-weight: bold;")
                    else:
                        # 0番目のアイテムでsepが無い場合（Compactモードでない場合など）
                        # ヘッダー自体の色を変える等はHighlightメソッドでペイン全体やってるが、
                        # ここでは個別のViewのアクティブ感を出したい。
                        # しかしsepがない場合は構造上難しいのでスキップして良いか、
                        # あるいはItemContainerの枠を変えるか。
                        # 現状はsepがある場合（2つ目以降、またはパス1つの場合のタイトルバー）のみ対応。
                        pass
        elif event.type() == QEvent.FocusOut:
             for i, (view, _, _, sep) in enumerate(self.views):
                if watched == view:
                    # Restore style
                    if sep:
                        sep.setStyleSheet("background: #2d2d2d; color: #888; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #222;")
        
        return super().eventFilter(watched, event)

    def highlight(self, active):
        if active:
            self.header.setStyleSheet("background: #37373d; border-bottom: 2px solid #007acc;")
            self.up_btn.setStyleSheet("border: none; color: #007acc; font-weight: bold; background: transparent;")
        else:
            self.header.setStyleSheet("background: #252526; border-bottom: 1px solid #333;")
            self.up_btn.setStyleSheet("border: none; color: #555; background: transparent;")

    def _trigger_column_adjust(self):
        """v12.0: Ctrl+Wheelでスプリッタサイズ変更後、全Viewの名前列幅を再計算"""
        # レイアウトの更新を強制してから幅を調整
        QApplication.processEvents()
        for view, _, _, _ in self.views:
            if hasattr(view, '_adjust_name_column_width'):
                view._adjust_name_column_width()

    def display_folders(self, paths):
        self.current_paths = [os.path.abspath(p) for p in paths]
        # v7.2 マーク機能の参照を確実にリンクする（タブ間移動などで親が変わる可能性に備え）
        if self._marked_paths_ref is None and hasattr(self, 'parent_lane'):
            if hasattr(self.parent_lane, 'parent_area'):
                self._marked_paths_ref = self.parent_lane.parent_area.marked_paths
        
        if not paths:
            self.title_label.setText("...waiting for flow")
            # 全クリア
            while self.content_splitter.count():
                w = self.content_splitter.widget(0)
                w.setParent(None)
                w.deleteLater()
            self.views.clear()
            
            dummy = QWidget()
            dummy.setObjectName("EmptySpace")
            dummy.setStyleSheet("background: #1e1e1e;") # v9.2 Fix: 空領域を黒くする
            self.content_splitter.addWidget(dummy)
            return

        # 1. 削除処理: 新しいパスに含まれない既存Viewを削除
        # 逆順で消さないとインデックスがずれる可能性があるが、リストから消すので注意
        new_path_set = set(self.current_paths)
        i = len(self.views) - 1
        while i >= 0:
            view, proxy, path, sep = self.views[i]
            if path not in new_path_set:
                # コンテナ（Viewの親）を削除する必要がある
                # sepがある場合、それはitem_containerの中にあるので一緒に消えるはず
                # view.parent() は item_container
                container = view.parentWidget() # QFrame
                if container:
                    container.setParent(None)
                    container.deleteLater()
                self.views.pop(i)
            i -= 1

        # Waiting状態のダミーがあれば消す
        for i in range(self.content_splitter.count()):
            w = self.content_splitter.widget(i)
            if w.objectName() == "EmptySpace":
                w.deleteLater()

        # 既存Viewのマップを作成 (path -> (view, proxy, sep, container))
        existing_map = {}
        for v, p, path, s in self.views:
            existing_map[path] = (v, p, s, v.parentWidget())
            
        new_views_list = []

        # 2. 追加・並び替え処理
        for i, path in enumerate(self.current_paths):
            if not os.path.exists(path): continue
            
            # 既存にあるか？
            if path in existing_map:
                view, proxy, sep, container = existing_map[path]
                # splitter内の現在の位置を確認
                current_idx = self.content_splitter.indexOf(container)
                
                # 期待する位置(i)と違うなら移動
                if current_idx != i:
                    self.content_splitter.insertWidget(i, container)
                
                # sepの状態更新（パス数による表示切り替え）
                if len(self.current_paths) > 1:
                    if sep is None:
                        # sepがなかった（＝以前は単独表示だった）場合、作る必要がある
                        # レイアウトに追加
                        sep = QLabel(f" ■ {os.path.basename(path)}")
                        sep.setFixedHeight(20)
                        sep.setStyleSheet("background: #2d2d2d; color: #888; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #222;")
                        container.layout().insertWidget(0, sep)
                        if self.is_compact: sep.hide()
                    else:
                        sep.setVisible(not self.is_compact)
                else:
                    if sep:
                        sep.hide()
                
                # ヘッダー制御
                if self.is_compact:
                    if i > 0: view.setHeaderHidden(True)
                    else: view.setHeaderHidden(False)

                new_views_list.append((view, proxy, path, sep))

            else:
                # 新規作成
                item_container = QFrame()
                item_container.setObjectName("ItemContainer")
                item_layout = QVBoxLayout(item_container)
                item_layout.setContentsMargins(0, 0, 0, 0)
                item_layout.setSpacing(0)
                
                sep = None
                if len(self.current_paths) > 1:
                    sep = QLabel(f" ■ {os.path.basename(path)}")
                    sep.setFixedHeight(20)
                    sep.setStyleSheet("background: #2d2d2d; color: #888; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #222;")
                    item_layout.addWidget(sep)

                # Proxy作成
                proxy = SmartSortFilterProxyModel()
                proxy.setSourceModel(self.base_model)
                proxy.setTargetRootPath(path)
                proxy.setDisplayMode(self.display_mode)
                proxy.setShowHidden(self.show_hidden)
                # v7.2 マーク共有（実体への参照を渡す）
                if self._marked_paths_ref is None and hasattr(self, 'parent_lane'):
                    self._marked_paths_ref = self.parent_lane.parent_area.marked_paths
                proxy.setMarkedPathsRef(self._marked_paths_ref)
                proxy.sort(self.current_sort_col, self.sort_order)

                view = BatchTreeView(self)
                view.setModel(proxy)
                
                source_idx = self.base_model.index(path)
                proxy_idx = proxy.mapFromSource(source_idx)
                view.setRootIndex(proxy_idx)
                
                view.setSortingEnabled(True)
                view.setItemsExpandable(False) 
                view.setExpandsOnDoubleClick(False)
                view.setRootIsDecorated(False)
                view.setSelectionBehavior(QTreeView.SelectRows)
                view.setSelectionMode(QTreeView.ExtendedSelection)
                view.setEditTriggers(QTreeView.NoEditTriggers) # ダブルクリックでのリネームを無効化
                view.setHeaderHidden(False)
                view.setIndentation(0)
                
                view.hideColumn(1) 
                
                # Header Resizing Strategy (v12.0 Revised)
                # Stretchだとユーザー操作がロックされるため、Interactive + resizeEventで制御
                header = view.header()
                header.setStretchLastSection(False) # 最終列の自動拡張を無効化
                header.setSectionResizeMode(0, QHeaderView.Interactive)
                header.setSectionResizeMode(2, QHeaderView.Interactive)
                header.setSectionResizeMode(3, QHeaderView.Interactive)
                
                # 初期幅の設定
                view.setColumnWidth(2, 80)
                view.setColumnWidth(3, 140)
                
                view.setFrameStyle(QFrame.NoFrame)
                view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                view.setDragEnabled(True)
                view.setAcceptDrops(True)
                view.setDropIndicatorShown(True)
                view.setDragDropMode(QTreeView.DragDrop)
                view.setDefaultDropAction(Qt.MoveAction)
                
                view.header().setSortIndicator(self.current_sort_col, self.sort_order)
                
                view.setContextMenuPolicy(Qt.CustomContextMenu)
                view.customContextMenuRequested.connect(lambda pos, v=view, p=proxy: self.open_context_menu(pos, v, p))
                
                # キーイベント監視
                view.installEventFilter(self)
                view.viewport().installEventFilter(self)

                view.selectionModel().selectionChanged.connect(self.on_selection_changed)
                view.clicked.connect(self.on_item_clicked)
                view.doubleClicked.connect(lambda idx, v=view: self.on_double_clicked(idx, v))
                
                if self.is_compact:
                    if len(self.current_paths) > 1:
                        if sep: sep.hide()
                    if i > 0:
                        view.setHeaderHidden(True)

                item_layout.addWidget(view)
                
                # 挿入
                self.content_splitter.insertWidget(i, item_container)
                new_views_list.append((view, proxy, path, sep))

        self.views = new_views_list

        # 初回のサイズ調整だけ行い、あとはユーザー調整を尊重したいが、
        # 追加されたときは等分しないとつぶれて見えないことがある
        # ここでは簡易的に、新しく追加された場合のみサイズ調整するロジックにするのは複雑なので
        # パス数が変わった場合のみリセットくらいにするか？
        # いや、維持したいという要望ならサイズも維持すべきだが、増えた分を表示領域確保する必要がある。
        # 既存の比率を保ったまま...は難しいので、パス数が変わったら再計算（等分）が無難か。
        # リセットされるのが嫌という要望なので、なるべく維持したいが。
        
        # ひとまず「パス数が変わった時だけ」等分リセットを行う。
        # (厳密にはこれでもスクロール領域が変わるかもしれないが、中身の状態は維持される)
        
        # しかし splitter.sizes() を取得して、よしなに計算するのは高度すぎる。
        # 追加時は単純に等分で再設定する。（これが一番安全）
        if len(paths) > 0 and self.content_splitter.count() == len(paths):
            # 現在のサイズ合計
            total_h = sum(self.content_splitter.sizes()) 
            if total_h < 100: total_h = self.height()
            each_h = total_h // len(paths)
            
            # もし大幅に数が増減したならリサイズ、そうでなければ維持...
            # 「既存維持」が最優先なので、setSizesを呼ばないほうがいいかもしれない。
            # QSplitterはウィジェット追加時に自動でスペースを割り当てるはず。
            # いったん setSizes を呼ばないで様子を見る。
            pass
            
        self.update_header_title()
        
        # v19.1: パス変更時にタブ名更新をトリガー
        if self.parent_filer and hasattr(self.parent_filer, 'update_current_tab_title'):
             # 全てのペイン変更で呼ぶと頻度が高いが、軽い処理なので許容
             # 厳密には「自分が左上のペインである」場合のみで良いが、判定が複雑になるためMainWindow側で判定させる（get_representative_nameで現在の左上を見るため）
             self.parent_filer.update_current_tab_title()

    def distribute_views(self):
        """v13.0 Splitter内のビュー高さを均等にする"""
        if not self.content_splitter or self.content_splitter.count() == 0:
            return
            
        count = self.content_splitter.count()
        total_size = sum(self.content_splitter.sizes())
        
        # サイズ合計が極端に小さい場合（初期化前など）、現在のペイン高さから推測
        if total_size < 50:
             # ヘッダー分を引く
             total_size = self.height() - 40
        
        if total_size <= 0: return

        avg_size = total_size // count
        new_sizes = [avg_size] * count
        
        # 余り調整
        diff = total_size - sum(new_sizes)
        if diff > 0:
            new_sizes[-1] += diff
            
        self.content_splitter.setSizes(new_sizes)

    def get_state(self):
        """現在のペインの状態を辞書で返す（セッション保存用）"""
        # pathsは現在のcurrent_pathsを使う
        # ただし、有効なパスのみ
        valid_paths = [p for p in self.current_paths if os.path.exists(p)]
        return {
            "paths": valid_paths,
            "display_mode": self.display_mode,
            "show_hidden": self.show_hidden,
            "sort_col": self.current_sort_col,
            "sort_order": self.sort_order.value, # Enum to int
            "is_compact": self.is_compact
        }

    def set_temp_highlight(self, path):
        """v14.0 指定パスを含むViewを探してハイライト
        
        v14.2 改善: ビューのルートが祖先パスの「親」である場合だけでなく、
        祖先パスがビューのルート配下にある場合もハイライト対象とする。
        """
        target_path = os.path.normpath(path)
        target_parent = os.path.dirname(target_path)
        
        # v14.2 Fix: ルートパス（D:\など）の場合は処理をスキップ
        if same_path(target_path, target_parent):
            return False
            
        # Debug Log (Requested by User)
        logger.log_debug(f"[Highlight] Request: {target_path}")
        
        for view, proxy, root_path, _ in self.views:
            root_norm = os.path.normpath(root_path)
            
            # ケース1: このビューのルートが target_path の親ディレクトリと一致
            # （元の動作: ビューが target_path を直接含んでいる）
            if same_path(root_norm, target_parent):
                logger.log_debug(f"  -> Direct match in {root_norm}")
                view.set_temp_highlight(target_path)
                return True
            
            # ケース2: target_path がこのビューのルートよりも深い階層（子孫）である場合
            # ビューの直下にある、ターゲットへ繋がるフォルダを特定してハイライトする
            if self._is_ancestor_of(root_norm, target_path) and not same_path(root_norm, target_path):
                try:
                    # Rootからの相対パスを取得して最初のセグメントを特定
                    rel_path = os.path.relpath(target_path, root_norm)
                    parts = rel_path.split(os.sep)
                    if parts:
                        first_segment = parts[0]
                        highlight_target = os.path.join(root_norm, first_segment)
                        
                        # 安全策: ルート自体をハイライトしようとしたらスキップ
                        if same_path(root_norm, highlight_item := highlight_target):
                            continue

                        logger.log_debug(f"  -> Deep match in {root_norm}, Highlighting: {highlight_target}")
                        view.set_temp_highlight(highlight_target)
                        return True
                except ValueError:
                    continue
        
        return False
    
    def _is_ancestor_of(self, ancestor_path, descendant_path):
        """ancestor_path が descendant_path の祖先かどうかを判定"""
        ancestor_norm = os.path.normcase(os.path.normpath(os.path.abspath(ancestor_path)))
        descendant_norm = os.path.normcase(os.path.normpath(os.path.abspath(descendant_path)))
        
        # ancestor が descendant のパスプレフィックスかチェック
        return descendant_norm.startswith(ancestor_norm + os.sep) or descendant_norm == ancestor_norm

    def clear_temp_highlight(self):
        """v14.0 全Viewのハイライト解除"""
        for view, _, _, _ in self.views:
            view.clear_temp_highlight()
            
        self.clear_view_highlight()

    def set_view_highlight(self, path):
        """v14.0 指定パスをルートとして表示しているView（下流）をハイライト"""
        for view, proxy, root_path, sep in self.views:
            # v14.1 Fix: same_pathを使用
            if same_path(root_path, path):
                # ハイライト色: ゴールド系
                highlight_style = "background: #d4a017; color: #1e1e1e; font-size: 9px; padding-left: 10px; font-weight: bold; border-bottom: 1px solid #b58900;"
                
                if sep and sep.isVisible():
                    sep.setStyleSheet(highlight_style)
                else:
                    # ヘッダーがない場合（単一表示など）、ペイン自体のヘッダーをハイライト
                    # ただしペインヘッダーはタイトルなどあるので、コンテナの枠を変える
                    container = view.parentWidget()
                    if container:
                        container.setStyleSheet("#ItemContainer { border: 2px solid #d4a017; }")
                return True
        return False

    def clear_view_highlight(self):
        """v14.0 Viewハイライト解除"""
        normal_sep_style = "background: #2d2d2d; color: #888; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #222;"
        
        for view, proxy, root_path, sep in self.views:
            if sep:
                sep.setStyleSheet(normal_sep_style)
            
            container = view.parentWidget()
            if container:
                container.setStyleSheet("") # スタイル解除

    def refresh_contents(self):
        """v14.0 F5リフレッシュ: 現在表示中のフォルダ内容を再読み込み"""
        if not self.current_paths:
            return
        
        # 各Viewの選択状態とスクロール位置を保存
        saved_states = []
        for view, proxy, root_path, _ in self.views:
            # 選択パス保存
            selected_paths = []
            for idx in view.selectionModel().selectedIndexes():
                if idx.column() == 0:
                    src_idx = proxy.mapToSource(idx)
                    selected_paths.append(self.base_model.filePath(src_idx))
            
            # 現在のカーソル位置
            current_idx = view.currentIndex()
            current_path = None
            if current_idx.isValid():
                src_idx = proxy.mapToSource(current_idx)
                current_path = self.base_model.filePath(src_idx)
            
            # スクロール位置
            scroll_pos = view.verticalScrollBar().value()
            
            saved_states.append({
                'root_path': root_path,
                'selected_paths': selected_paths,
                'current_path': current_path,
                'scroll_pos': scroll_pos
            })
        
        # モデルを強制リフレッシュ
        # v19 Performance Fix: Shared Modelを使用しているため、setRootPathのリセットは全ペインに影響するので禁止としていたが、
        # v21.4 Fix: ネットワークドライブ等でゴースト（削除済みフォルダ）が残る問題を解決するため、
        # ネットワークパスの場合に限り、あえてsetRootPathを呼び直して監視（＝再スキャン）を強制する。
        # QFileSystemModelの特性上、監視パスを切り替えると再読込が走るため、これを利用してキャッシュを更新させる。
        
        for view, proxy, root_path, _ in self.views:
            # ネットワークパス（UNCパス）の簡易判定
            if root_path.startswith(r"\\") or root_path.startswith("//"):
                # 強制再スキャン (Aggressive Refresh)
                # 単にsetRootPathを呼ぶだけでは、既に監視中と判断されてスキップされることがあるため、
                # 一度無効なパス（ルートなど）に切り替えてから戻すことで、確実に内部キャッシュを破棄させる。
                # ただし画面が一瞬ルートに戻る副作用があるため、これを抑制するためにシグナルを一時ブロックする手もあるが、
                # モデル共有の観点から他への影響が懸念される。
                # ここでは「QDir.rootPath()」を一時的にセットし、直後に戻すことでリロードを誘発する。
                
                # 注意: これは重い処理になる可能性があるが、整合性優先。
                self.base_model.setRootPath(QDir.rootPath())
                QApplication.processEvents() # イベントループを回して変更を処理させる
                self.base_model.setRootPath(root_path)
            
            # Proxyを無効化して再フィルタ
            proxy.invalidate()
        
        # 選択状態とスクロール位置を復元
        QTimer.singleShot(100, lambda: self._restore_after_refresh(saved_states))

    def _restore_after_refresh(self, saved_states):
        """リフレッシュ後の状態復元"""
        from PySide6.QtCore import QItemSelectionModel
        
        for i, state in enumerate(saved_states):
            if i >= len(self.views):
                break
            
            view, proxy, _, _ = self.views[i]
            
            # スクロール位置復元
            view.verticalScrollBar().setValue(state['scroll_pos'])
            
            # 選択復元
            selection_model = view.selectionModel()
            for path in state['selected_paths']:
                src_idx = self.base_model.index(path)
                if src_idx.isValid():
                    proxy_idx = proxy.mapFromSource(src_idx)
                    if proxy_idx.isValid():
                        selection_model.select(proxy_idx, 
                            QItemSelectionModel.Select | QItemSelectionModel.Rows)
            
            # 現在位置復元
            if state['current_path']:
                src_idx = self.base_model.index(state['current_path'])
                if src_idx.isValid():
                    proxy_idx = proxy.mapFromSource(src_idx)
                    if proxy_idx.isValid():
                        view.setCurrentIndex(proxy_idx)

    def restore_state(self, state):
        """辞書からペインの状態を復元する"""
        self.display_mode = state.get("display_mode", 0)
        self.show_hidden = state.get("show_hidden", False)
        self.current_sort_col = state.get("sort_col", 0)
        self.sort_order = Qt.SortOrder(state.get("sort_order", 0))
        self.is_compact = state.get("is_compact", False)
        
        paths = state.get("paths", [])
        if paths:
            self.display_folders(paths)
        else:
            # デフォルト
            self.display_folders([os.path.abspath(".")])

    def open_context_menu(self, pos, view, proxy):
        """v14.1 Refactoring: コンテキストメニュー処理をContextMenuBuilderに委譲"""
        builder = ContextMenuBuilder(self)
        builder.build_and_show(pos, view, proxy)

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)

    def action_create_shortcut(self, paths):
        """v7.5 選択したファイルのショートカットを作成"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            
            for target in paths:
                target_abs = os.path.abspath(target)
                parent_dir = os.path.dirname(target_abs)
                name = os.path.basename(target_abs)
                base, _ = os.path.splitext(name)
                
                # Desktop以外の場合は同階層に作成
                link_path = os.path.join(parent_dir, f"{base} - Shortcut.lnk")
                
                # 同名回避
                c = 1
                while os.path.exists(link_path):
                    link_path = os.path.join(parent_dir, f"{base} - Shortcut ({c}).lnk")
                    c += 1
                
                shortcut = shell.CreateShortcut(link_path)
                shortcut.TargetPath = target_abs
                shortcut.WorkingDirectory = parent_dir
                shortcut.Save()
        except Exception as e:
            QMessageBox.critical(self, "Shortcut Error", f"Failed to create shortcut:\n{e}")

    def action_show_properties(self, path):
        """v7.5 Windows標準のプロパティ画面を表示"""
        try:
            import ctypes
            from ctypes import wintypes
            
            SEE_MASK_INVOKEIDLIST = 0x0000000C
            SW_SHOWNORMAL = 1
            
            class SHELLEXECUTEINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_uint32),
                    ("fMask", ctypes.c_uint32),
                    ("hwnd", wintypes.HWND),
                    ("lpVerb", wintypes.LPCWSTR),
                    ("lpFile", wintypes.LPCWSTR),
                    ("lpParameters", wintypes.LPCWSTR),
                    ("lpDirectory", wintypes.LPCWSTR),
                    ("nShow", ctypes.c_int),
                    ("hInstApp", wintypes.HINSTANCE),
                    ("lpIDList", ctypes.c_void_p),
                    ("lpClass", wintypes.LPCWSTR),
                    ("hkeyClass", ctypes.c_void_p),
                    ("dwHotKey", ctypes.c_uint32),
                    ("hIcon", ctypes.c_void_p),
                    ("hProcess", ctypes.c_void_p),
                ]
            
            sei = SHELLEXECUTEINFO()
            sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
            sei.fMask = SEE_MASK_INVOKEIDLIST
            sei.hwnd = int(self.window().winId()) # 親ウィンドウハンドル
            sei.lpVerb = "properties"
            sei.lpFile = os.path.abspath(path)
            sei.nShow = SW_SHOWNORMAL
            
            ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
            
        except Exception as e:
             QMessageBox.critical(self, "Properties Error", f"Failed to show properties:\n{e}")


    def get_selection_info(self, view=None, proxy=None):
        if view is None or proxy is None:
            # 1. アクティブ（フォーカスあり）なViewを探す
            view, proxy = None, None
            for v, p, _, _ in self.views:
                if v.hasFocus():
                    view, proxy = v, p
                    break
            
            # 2. フォーカスがない場合、選択項目があるViewを探す (v12.0 fix: ホバー操作時のUX改善)
            # クリックせずにマウスオーバーだけでCtrl+C等をする場合、フォーカスが当たっていない可能性があるため
            if not view:
                for v, p, _, _ in self.views:
                    if v.selectionModel().hasSelection():
                        view, proxy = v, p
                        break
            
            # 3. それでもなければ先頭をデフォルトとする
            if not view and self.views:
                view, proxy = self.views[0][0], self.views[0][1]

        paths = []
        full_infos = []
        has_zip = False
        if view:
            selected_indexes = view.selectionModel().selectedRows()
            for idx in selected_indexes:
                src_idx = proxy.mapToSource(idx)
                path = self.base_model.filePath(src_idx)
                if os.path.exists(path):
                    paths.append(path)
                    is_dir = os.path.isdir(path)
                    full_infos.append({"index": src_idx, "path": path, "is_dir": is_dir})
                    if not is_dir and path.lower().endswith('.zip'):
                        has_zip = True
        return {"paths": paths, "full_infos": full_infos, "has_zip": has_zip, "view": view, "proxy": proxy}

    def action_aggregate_clipboard(self, paths, mode):
        """v7.2 全Viewから集めた項目をクリップボードにセット（重複排除・入れ子対応）"""
        if not paths: return
        
        # 入れ子関係の排除ロジック:
        # 親フォルダが選択されている場合、その中にある選択済みファイルはリストから除外する
        sorted_paths = sorted(paths, key=len) # 短いパス（親ディレクトリ）から順に処理
        final_list = []
        
        for p in sorted_paths:
            p_abs = os.path.abspath(p)
            # すでにfinal_listにあるフォルダの配下かどうかチェック
            is_redundant = False
            for existing in final_list:
                if os.path.isdir(existing):
                    # existing が p_abs の親ディレクトリであるか確認
                    common = os.path.commonpath([existing, p_abs])
                    if common == os.path.abspath(existing) and existing != p_abs:
                        is_redundant = True
                        break
            if not is_redundant:
                final_list.append(p)
                
        self.parent_filer.internal_clipboard = {"paths": final_list, "mode": mode}
        
        # v7.2 収集コピー起動時はマークをクリア
        if self._marked_paths_ref:
            for p in final_list:
                if p in self._marked_paths_ref:
                    self._marked_paths_ref.remove(p)
            self.refresh_all_views_in_tab()

    def action_cut(self):
        info = self.get_selection_info()
        if info["paths"]:
            self.parent_filer.internal_clipboard = {"paths": info["paths"], "mode": "move"}

    def action_copy(self):
        # v14.1 Fix: 内部クリップボードだけでなくOSクリップボードにもコピーする
        # これにより、右クリックコピー -> エクスプローラーで貼り付け や AHK連携が可能になる
        info = self.get_selection_info()
        if info["paths"]:
            self.parent_filer.internal_clipboard = {"paths": info["paths"], "mode": "copy"}
            # OSクリップボード連携
            self.copy_selected_to_clipboard()

    def action_paste(self, dest_dir=None):
        # 1. Determine Destination Directory
        if dest_dir is None:
            # v20.1 Fix: Focus priority
            info = self.get_selection_info()
            if info["view"]:
                for v, p, path, _ in self.views:
                    if v == info["view"]:
                        dest_dir = path
                        break
            
            # Fallback
            if not dest_dir:
                dest_dir = self.current_paths[0] if self.current_paths else None
        
        if not dest_dir or not os.path.exists(dest_dir): return
        
        # 2. Check Clipboard Content
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Priority 1: ChainFlow Internal Clipboard (File Operation)
        cb = self.parent_filer.internal_clipboard
        if cb.get("paths"):
            self.execute_batch_paste(cb["paths"], dest_dir, cb["mode"])
            if cb["mode"] == "cut":
                 # Clear internal clipboard after move
                 self.parent_filer.internal_clipboard = {"paths": [], "mode": "copy"}
            return

        # Priority 2: OS File Clipboard (Explorer Copy)
        if mime_data.hasUrls():
            urls = mime_data.urls()
            paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if paths:
                # Treat as copy from external
                self.execute_batch_paste(paths, dest_dir, "copy")
                return

        # Priority 3: Image Data (Screenshot Paste) -> v21.0 New Feature
        if mime_data.hasImage():
            self.save_clipboard_image(dest_dir)
            return

    def save_clipboard_image(self, dest_dir):
        """v21.0: Save clipboard image as PNG with timestamp"""
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if image.isNull(): return

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # Generate unique filename
        filename = f"clipboard_{timestamp}.png"
        file_path = os.path.join(dest_dir, filename)
        
        # Avoid collision (rare case with same second)
        c = 1
        while os.path.exists(file_path):
             filename = f"clipboard_{timestamp}_{c}.png"
             file_path = os.path.join(dest_dir, filename)
             c += 1
             
        # Save
        try:
            image.save(file_path, "PNG")
            
            # Highlight the new file
            QTimer.singleShot(100, lambda: self.set_temp_highlight(file_path))
            # Selecting it for immediate F2 rename is also good UX
            # But highlight is enough for now.
            
            # Log
            logger.log_info(f"Saved clipboard image to: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Image Paste Error", f"Failed to save image:\n{e}")

    def action_delete(self):
        info = self.get_selection_info()
        paths = info["paths"]
        if paths:
            ret = QMessageBox.question(self, "Delete", f"Are you sure you want to delete {len(paths)} items?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                for item in info["full_infos"]:
                    self.base_model.remove(item["index"])

    def action_rename(self):
        info = self.get_selection_info()
        if info["view"]:
            idx = info["view"].currentIndex()
            if idx.isValid():
                info["view"].edit(idx)

    def action_new_folder(self, view=None, proxy=None):
        if view is None or proxy is None:
            info = self.get_selection_info()
            view, proxy = info["view"], info["proxy"]
        
        if view and proxy:
            src_root_idx = proxy.mapToSource(view.rootIndex())
            name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")
            if ok and name:
                self.base_model.mkdir(src_root_idx, name)

    def action_terminal(self, paths):
        target_dir = paths[0] if paths and os.path.isdir(paths[0]) else os.path.dirname(paths[0]) if paths else self.current_paths[0]
        if os.path.exists(target_dir):
            subprocess.Popen(f'start cmd /k "cd /d {target_dir}"', shell=True)

    def action_zip(self, selection):
        paths = selection["paths"]
        full_infos = selection["full_infos"]
        if not paths: return
        base_name = os.path.basename(paths[0])
        if len(paths) > 1: base_name = os.path.basename(os.path.dirname(paths[0])) or "Archive"
        if os.path.isdir(paths[0]) and len(paths) == 1: pass 
        else: base_name = os.path.splitext(base_name)[0]
        
        default_zip = f"{base_name}.zip"
        zip_name, ok = QInputDialog.getText(self, "圧縮", "ZIPファイル名:", text=default_zip)
        if ok and zip_name:
            parent_dir = os.path.dirname(paths[0])
            target_zip = os.path.join(parent_dir, zip_name)
            
            # v14.2 スレッド化
            self._zip_worker = FileOperationWorker("zip", self)
            self._zip_worker.src_paths = paths
            self._zip_worker.dest_path = target_zip
            self._zip_worker.zip_base_dir = parent_dir
            
            # プログレスダイアログ作成
            self._zip_progress = QProgressDialog("圧縮中...", "キャンセル", 0, 100, self)
            self._zip_progress.setWindowTitle("ZIP圧縮")
            self._zip_progress.setWindowModality(Qt.WindowModal)
            self._zip_progress.setMinimumDuration(500)
            self._zip_progress.setAutoClose(True)
            
            # シグナル接続
            self._zip_worker.progress.connect(self._on_zip_progress)
            self._zip_worker.finished.connect(self._on_zip_finished)
            self._zip_worker.error.connect(self._on_zip_error)
            self._zip_progress.canceled.connect(self._zip_worker.cancel)
            
            # 開始
            self._zip_worker.start()
    
    def _on_zip_progress(self, current, total, current_file):
        """v14.2 ZIP進捗更新"""
        if hasattr(self, '_zip_progress') and self._zip_progress:
            self._zip_progress.setMaximum(total)
            self._zip_progress.setValue(current)
            self._zip_progress.setLabelText(f"圧縮中: {current_file}")
    
    def _on_zip_finished(self, success, message):
        """v14.2 ZIP圧縮完了"""
        if hasattr(self, '_zip_progress') and self._zip_progress:
            self._zip_progress.close()
        if hasattr(self, '_zip_worker') and self._zip_worker:
            self._zip_worker.deleteLater()
            self._zip_worker = None
    
    def _on_zip_error(self, error_message):
        """v14.2 ZIP圧縮エラー"""
        if hasattr(self, '_zip_progress') and self._zip_progress:
            self._zip_progress.close()
        QMessageBox.critical(self, "エラー", error_message)
        if hasattr(self, '_zip_worker') and self._zip_worker:
            self._zip_worker.deleteLater()
            self._zip_worker = None

    def action_unzip(self, selection):
        """v14.2 スレッド化: ZIP解凍をバックグラウンドで実行"""
        for item in selection["full_infos"]:
            p, is_d = item["path"], item["is_dir"]
            if not is_d and p.lower().endswith('.zip'):
                out_dir = os.path.splitext(p)[0]
                base_out = out_dir
                c = 1
                while os.path.exists(out_dir):
                    out_dir = f"{base_out}_{c}"
                    c += 1
                os.makedirs(out_dir, exist_ok=True)
                
                # v14.2 スレッド化
                self._unzip_worker = FileOperationWorker("unzip", self)
                self._unzip_worker.src_paths = [p]
                self._unzip_worker.dest_path = out_dir
                
                # プログレスダイアログ作成
                self._unzip_progress = QProgressDialog("解凍中...", "キャンセル", 0, 100, self)
                self._unzip_progress.setWindowTitle("ZIP解凍")
                self._unzip_progress.setWindowModality(Qt.WindowModal)
                self._unzip_progress.setMinimumDuration(500)
                self._unzip_progress.setAutoClose(True)
                
                # シグナル接続
                self._unzip_worker.progress.connect(self._on_unzip_progress)
                self._unzip_worker.finished.connect(self._on_unzip_finished)
                self._unzip_worker.error.connect(self._on_unzip_error)
                self._unzip_progress.canceled.connect(self._unzip_worker.cancel)
                
                # 開始
                self._unzip_worker.start()
                break  # 最初のZIPファイルのみ処理
    
    def _on_unzip_progress(self, current, total, current_file):
        """v14.2 解凍進捗更新"""
        if hasattr(self, '_unzip_progress') and self._unzip_progress:
            self._unzip_progress.setMaximum(total)
            self._unzip_progress.setValue(current)
            self._unzip_progress.setLabelText(f"解凍中: {current_file}")
    
    def _on_unzip_finished(self, success, message):
        """v14.2 解凍完了"""
        if hasattr(self, '_unzip_progress') and self._unzip_progress:
            self._unzip_progress.close()
        if hasattr(self, '_unzip_worker') and self._unzip_worker:
            self._unzip_worker.deleteLater()
            self._unzip_worker = None
    
    def _on_unzip_error(self, error_message):
        """v14.2 解凍エラー"""
        if hasattr(self, '_unzip_progress') and self._unzip_progress:
            self._unzip_progress.close()
        QMessageBox.critical(self, "エラー", error_message)
        if hasattr(self, '_unzip_worker') and self._unzip_worker:
            self._unzip_worker.deleteLater()
            self._unzip_worker = None

    def execute_batch_paste(self, src_paths, dest_dir, mode):
        """v14.2 スレッド化: コピー/移動をバックグラウンドで実行"""
        if not os.path.exists(dest_dir): 
            return
        
        # ワーカー作成
        self._paste_worker = FileOperationWorker("copy" if mode == "copy" else "move", self)
        self._paste_worker.src_paths = src_paths
        self._paste_worker.dest_path = dest_dir
        
        # プログレスダイアログ作成
        operation_name = "コピー中..." if mode == "copy" else "移動中..."
        self._paste_progress = QProgressDialog(operation_name, "キャンセル", 0, len(src_paths), self)
        self._paste_progress.setWindowTitle("ファイル操作")
        self._paste_progress.setWindowModality(Qt.WindowModal)
        self._paste_progress.setMinimumDuration(500)  # 500ms以上かかる場合のみ表示
        self._paste_progress.setAutoClose(True)
        self._paste_progress.setAutoReset(True)
        
        # シグナル接続
        self._paste_worker.progress.connect(self._on_paste_progress)
        self._paste_worker.finished.connect(self._on_paste_finished)
        self._paste_worker.error.connect(self._on_paste_error)
        self._paste_progress.canceled.connect(self._paste_worker.cancel)
        
        # 開始
        self._paste_worker.start()
    
    def _on_paste_progress(self, current, total, current_file):
        """v14.2 ペースト進捗更新"""
        if hasattr(self, '_paste_progress') and self._paste_progress:
            self._paste_progress.setMaximum(total)
            self._paste_progress.setValue(current)
            self._paste_progress.setLabelText(f"処理中: {current_file}")
    
    def _on_paste_finished(self, success, message):
        """v14.2 ペースト完了"""
        if hasattr(self, '_paste_progress') and self._paste_progress:
            self._paste_progress.close()
        
        if hasattr(self, '_paste_worker') and self._paste_worker:
            self._paste_worker.deleteLater()
            self._paste_worker = None
    
    def _on_paste_error(self, error_message):
        """v14.2 ペーストエラー"""
        if hasattr(self, '_paste_progress') and self._paste_progress:
            self._paste_progress.close()
        
        QMessageBox.critical(self, "エラー", error_message)
        
        if hasattr(self, '_paste_worker') and self._paste_worker:
            self._paste_worker.deleteLater()
            self._paste_worker = None

    def open_with_dialog(self, path):
        try:
            path = os.path.normpath(path)
            
            # 試行1: OpenWith.exe (Windows 10/11)
            cmd = f'C:\\Windows\\System32\\OpenWith.exe "{path}"'
            subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
            
        except Exception as e:
            # フォールバック: rundll32
            try:
                cmd = f'rundll32.exe shell32.dll,OpenAs_RunDLL "{path}"'
                subprocess.Popen(cmd, shell=True)
            except Exception:
                 pass

    def update_header_title(self):
        titles = []
        for p in self.current_paths:
            name = os.path.basename(p) if os.path.basename(p) else p
            titles.append(name)
        
        mode_text = ["All", "Dirs", "Files"][self.display_mode]
        hidden_text = "+H" if self.show_hidden else ""
        col_names = {0: "Name", 2: "Type", 3: "Date"}
        sort_name = col_names.get(self.current_sort_col, "?")
        order_text = "ASC" if self.sort_order == Qt.AscendingOrder else "DESC"
        
        tag = f"[{mode_text}{' ' + hidden_text if hidden_text else ''} | {sort_name} {order_text}]"
        compact_tag = " (COMPACT)" if self.is_compact else ""
        self.title_label.setText(f"{tag}{compact_tag}  " + " + ".join(titles) if titles else "Empty")

    def toggle_sort(self, col):
        current_col = self.current_sort_col
        if current_col == col:
            new_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            new_order = Qt.AscendingOrder

        self.current_sort_col = col
        self.sort_order = new_order
            
        for view, proxy, _, _ in self.views:
            proxy.sort(col, self.sort_order)
            view.header().setSortIndicator(col, self.sort_order)
            
        self.update_header_title()

    def cycle_display_mode(self):
        self.display_mode = (self.display_mode + 1) % 3
        # モード切替時にViewがルート(My Computer)に飛ぶのを防ぐため、
        # 各Viewのルートインデックスを現在のパスで再拘束する
        for i, (view, proxy, path, _) in enumerate(self.views):
            proxy.setDisplayMode(self.display_mode)
            
            # 再設定
            source_idx = self.base_model.index(path)
            proxy_idx = proxy.mapFromSource(source_idx)
            view.setRootIndex(proxy_idx)
            
        self.update_header_title()

    def toggle_hidden(self):
        self.show_hidden = not self.show_hidden
        for i, (view, proxy, path, _) in enumerate(self.views):
            proxy.setShowHidden(self.show_hidden)
            # 再設定
            source_idx = self.base_model.index(path)
            proxy_idx = proxy.mapFromSource(source_idx)
            view.setRootIndex(proxy_idx)
            
        self.update_header_title()

    def on_selection_changed(self):
        current_selected = []
        for view, proxy, _, _ in self.views:
            for idx in view.selectionModel().selectedRows():
                # ProxyインデックスなのでSourceに戻してパス取得
                source_idx = proxy.mapToSource(idx)
                p = self.base_model.filePath(source_idx)
                if os.path.isdir(p): current_selected.append(p)
        
        if not current_selected:
            # 選択解除された場合、空にするかどうかは要検討だが、
            # ChainFlowFilerとしては「何も表示しない」のが正しい
            self.last_selected_paths = []
            return

        # 順序維持ロジック:
        # 新しい選択リストを作成する際、「前回選択されていたもの」が今回も含まれていれば、
        # それらをリストの先頭に（前回の順序のまま）配置する。
        # 新しく追加されたものは、その後ろに追加する。
        
        prioritized_paths = []
        new_paths_set = set(current_selected)
        
        # 1. 前回の選択に含まれていて、かつ今回も選択されているものを先頭へ
        for p in self.last_selected_paths:
            if p in new_paths_set:
                prioritized_paths.append(p)
                new_paths_set.remove(p) # 追加済み
        
        # 2. 残り（新規追加分）を後ろへ。元のcurrent_selectedの順序（基本は名前順）を守る
        for p in current_selected:
            if p in new_paths_set:
                prioritized_paths.append(p)
        
        # 更新
        self.last_selected_paths = prioritized_paths
        
        # アドレスバー更新
        if prioritized_paths:
            self.parent_filer.update_address_bar(prioritized_paths[-1])
        
        # 反映
        if prioritized_paths:
            QTimer.singleShot(10, lambda: self.parent_filer.update_downstream(self, prioritized_paths))

    def on_item_clicked(self, index):
        # indexはProxyIndex
        view = self.sender()
        if not view: return
        # viewに対応するproxyを探す（ちょっと非効率だが確実）
        target_proxy = None
        for v, p, _, _ in self.views:
            if v == view:
                target_proxy = p
                break
        if target_proxy:
            source_idx = target_proxy.mapToSource(index)
            path = os.path.abspath(self.base_model.filePath(source_idx))
            
            # v7.2 Alt + Click でマーク処理
            if QApplication.keyboardModifiers() & Qt.AltModifier and self._marked_paths_ref is not None:
                if path in self._marked_paths_ref:
                    self._marked_paths_ref.remove(path)
                else:
                    self._marked_paths_ref.add(path)
                # 全Viewの表示を更新するためにinvalidateをかける
                self.refresh_all_views_in_tab()
                return # Altクリック時は通常のプレビュー更新などはしない（邪魔しない）

            self.parent_filer.update_preview(path)
            self.parent_filer.update_address_bar(path)

    def refresh_all_views_in_tab(self):
        """タブ内の全ペインの全Viewの見た目をリフレッシュ（マーク色反映用）"""
        if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
            area = self.parent_lane.parent_area
            for lane in area.lanes:
                for pane in lane.panes:
                    for _, p, _, _ in pane.views:
                        p.invalidate()

    def clear_all_marks(self):
        if self._marked_paths_ref is not None:
            self._marked_paths_ref.clear()
            self.refresh_all_views_in_tab()

    def get_current_selected_path(self):
        """現在選択されているアイテムのパスを返す（QuickLook用）"""
        # v20.1 Fix: get_selection_infoを使用してフォーカスのあるViewを優先する
        # これにより、Split View時に意図しない（上のブロックの）ファイルがプレビューされるのを防ぐ
        info = self.get_selection_info()
        if info["paths"]:
            # 複数の選択がある場合は最後のものを返す（従来の挙動に準拠）
            return info["paths"][-1]
        return None

    def on_double_clicked(self, index, view):
        # ここもProxyIndexが来る
        target_proxy = None
        for v, p, _, _ in self.views:
            if v == view: target_proxy = p; break
            
        if target_proxy:
            source_idx = target_proxy.mapToSource(index)
            path = self.base_model.filePath(source_idx)
            
            if os.path.isdir(path):
                # フォルダなら下流ペインへ遷移
                self.navigate_to(view, path)
            else:
                # ファイルならOS標準のアプリで開く
                if os.name == 'nt':
                    try:
                        # v6.12 作業ディレクトリを適切に設定
                        cwd = os.path.dirname(path) if os.path.isdir(os.path.dirname(path)) else None
                        subprocess.Popen(f'start "" "{path}"', shell=True, cwd=cwd)
                    except Exception as e:
                        print(f"Exec Error: {e}")
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def on_search_text_changed(self, text):
        """インクリメンタルサーチ実行"""
        for i, (view, proxy, path, _) in enumerate(self.views):
            proxy.setSearchText(text)
            # フィルタ変更によるルートロスト防止：位置を再固定
            source_idx = self.base_model.index(path)
            proxy_idx = proxy.mapFromSource(source_idx)
            view.setRootIndex(proxy_idx)
            
    def focus_search(self):
        self.search_box.setFocus()
        self.search_box.selectAll()
        
    def clear_search(self):
        self.search_box.clear()

    def action_mark_selected(self, paths, mark=True):
        """v7.3 選択したアイテムを一括でマーク/マーク解除する"""
        if not paths: return
        
        # 参照がない場合のフェイルセーフ
        if self._marked_paths_ref is None:
            if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
                self._marked_paths_ref = self.parent_lane.parent_area.marked_paths
        
        if self._marked_paths_ref is None: return

        changed = False
        for p in paths:
            # パスを正規化（絶対パス）して使用する
            p_abs = os.path.abspath(p)
            if mark:
                if p_abs not in self._marked_paths_ref:
                    self._marked_paths_ref.add(p_abs)
                    changed = True
            else:
                if p_abs in self._marked_paths_ref:
                    self._marked_paths_ref.remove(p_abs)
                    changed = True
        
        if changed:
            self.refresh_all_views_in_tab()

    def refresh_all_views_in_tab(self):
        """タブ内の全ペインの全Viewの見た目をリフレッシュ（マーク色反映用）"""
        if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
            area = self.parent_lane.parent_area
            for lane in area.lanes:
                for pane in lane.panes:
                    for _, p, _, _ in pane.views:
                        # キャッシュ更新
                        if hasattr(p, 'updateMarkedCache'):
                            p.updateMarkedCache()
                        # 色の変更（data関数の結果変更）を反映させるには layoutChanged が確実
                        p.layoutChanged.emit()

    def action_convert_to_pdf(self, paths):
        """v7.1 Hybrid PDF Conversion (MS Office -> LibreOffice)"""
        if not paths: return
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            office_success_paths = []
            
            # --- Try Microsoft Office first ---
            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                
                word_app = None
                excel_app = None
                
                for path in paths:
                    abs_path = os.path.abspath(path)
                    ext = os.path.splitext(abs_path)[1].lower()
                    pdf_path = os.path.splitext(abs_path)[0] + ".pdf"
                    
                    # 同名回避
                    if os.path.exists(pdf_path):
                        base, _ = os.path.splitext(pdf_path)
                        c = 1
                        while os.path.exists(f"{base}_{c}.pdf"):
                            c += 1
                        pdf_path = f"{base}_{c}.pdf"

                    try:
                        if ext in ('.docx', '.doc'):
                            if not word_app:
                                word_app = win32com.client.Dispatch("Word.Application")
                                word_app.Visible = False
                            doc = word_app.Documents.Open(abs_path)
                            doc.ExportAsFixedFormat(pdf_path, 17) # wdExportFormatPDF = 17
                            doc.Close(False)
                            office_success_paths.append(path)
                        elif ext in ('.xlsx', '.xls'):
                            if not excel_app:
                                excel_app = win32com.client.Dispatch("Excel.Application")
                                excel_app.Visible = False
                                excel_app.DisplayAlerts = False
                            wb = excel_app.Workbooks.Open(abs_path)
                            wb.ExportAsFixedFormat(0, pdf_path) # xlTypePDF = 0
                            wb.Close(False)
                            office_success_paths.append(path)
                    except Exception as e:
                        print(f"MS Office Error for {path}: {e}")
                
            except Exception as e:
                 # 呼び出し元がExceptionをキャッチしているので、ここはログ出すくらい
                pass
            finally:
                if word_app: word_app.Quit()
                if excel_app: excel_app.Quit()
                QApplication.restoreOverrideCursor()
            
            # v7.2 バッチ処理成功後にマークを解除（もしカゴから実行された場合）
            if hasattr(self, '_marked_paths_ref') and self._marked_paths_ref:
                # 変換に成功したパス（または渡されたパス全体）をマークから消す
                for p in paths:
                    if p in self._marked_paths_ref:
                        self._marked_paths_ref.remove(p)
                self.refresh_all_views_in_tab()

            QMessageBox.information(self, "PDF Conversion", f"Converted {len(office_success_paths)} files to PDF.\nSaved in the same directory.")
                
        except Exception as e:
            print(f"MS Office Dispatch failed or not installed: {e}")

    def action_new_file(self, view=None, proxy=None):
        """v15.0: 新規ファイル作成"""
        if view is None or proxy is None:
            info = self.get_selection_info()
            view, proxy = info["view"], info["proxy"]
            
        if not view or not proxy:
             return

        root_idx = view.rootIndex()
        src_root_idx = proxy.mapToSource(root_idx)
        current_dir = self.base_model.filePath(src_root_idx)
        
        if not current_dir or not os.path.exists(current_dir):
            return

        # デフォルト名
        default_name = "NewFile.txt"
        
        text, ok = QInputDialog.getText(self, "New File", "Filename:", QLineEdit.Normal, default_name)
        if ok and text:
            file_path = os.path.join(current_dir, text)
            if os.path.exists(file_path):
                QMessageBox.warning(self, "Error", "File already exists!")
                return
                
            try:
                # 空ファイル作成
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass
                
                # 作成したファイルを選択状態にする（少し待ってから）
                QTimer.singleShot(100, lambda: self._select_and_edit_created_file(file_path))
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file:\n{e}")

    def _select_and_edit_created_file(self, path):
        """作成したファイルをハイライト選択し、QuickLookの編集モードで開く"""
        # ハイライト (選択状態にする)
        from PySide6.QtCore import QItemSelectionModel
        
        target_dir = os.path.dirname(path)
        for view, proxy, root_path, _ in self.views:
             if same_path(root_path, target_dir):
                 src_idx = self.base_model.index(path)
                 if src_idx.isValid():
                      proxy_idx = proxy.mapFromSource(src_idx)
                      if proxy_idx.isValid():
                           view.setCurrentIndex(proxy_idx)
                           view.scrollTo(proxy_idx)
                           view.selectionModel().select(proxy_idx, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
                 break
        
        # 簡易編集モードで開く
        if self.parent_filer:
            # v16.0: Satellite Editor起動
            if hasattr(self.parent_filer, 'launch_editor'):
                self.parent_filer.launch_editor(path)
            elif hasattr(self.parent_filer, 'quick_look'):
                 # Fallback
                ql = self.parent_filer.quick_look
                ql.show_file(path, edit_mode=True)
                if not ql.isVisible():
                    ql.popup()

    def copy_selected_to_clipboard(self):
        """v14.1 AHK連携: 選択されたパスをクリップボードにコピー（テキスト＆URI）"""
        # 1. 現在の選択を取得
        paths = []
        
        # A. マークされたパス (Global)
        if self._marked_paths_ref:
            paths.extend(list(self._marked_paths_ref))
            
        # B. アクティブな選択 (Local)
        current = self.get_current_selected_paths_all() # 既存メソッドか新規作成が必要
        for p in current:
            if p not in paths:
                paths.append(p)
        
        if not paths: return

        # 2. クリップボードへのセット
        mime = QMimeData()
        
        # URI List (File Copy)
        urls = [QUrl.fromLocalFile(p) for p in paths]
        mime.setUrls(urls)
        
        # Text (AHK Support)
        # 改行区切りでパスをセット
        text_data = "\n".join(paths)
        mime.setText(text_data)
        
        QApplication.clipboard().setMimeData(mime)

    def get_current_selected_paths_all(self):
        """全Viewの選択アイテムパスを収集"""
        res = []
        for view, proxy, _, _ in self.views:
            for idx in view.selectionModel().selectedRows():
                source_idx = proxy.mapToSource(idx)
                p = self.base_model.filePath(source_idx)
                res.append(os.path.abspath(p))
        return res

    def go_up(self):
        """一つ上の階層へ"""# 1. アクティブなViewを探す
        target_view = None
        target_path = None
        
        # フォーカスがあるViewを優先
        for view, _, path, _ in self.views:
            if view.hasFocus():
                target_view = view
                target_path = path
                break
        
        # フォーカスがない場合は、既存の挙動(views[0])または安全策として何もしない
        # ここでは「何も選択されていないなら一番上」という従来の挙動をフォールバックとして残す
        if target_view is None and self.views:
            target_view, _, target_path, _ = self.views[0]

        if not target_view:
            return

        parent_path = os.path.dirname(target_path)
        if parent_path and parent_path != target_path:
            self.navigate_to(target_view, parent_path)

    def navigate_to(self, view, path):
        # ターゲットViewを探して更新
        for i, info in enumerate(self.views):
            v, proxy, p = info[0], info[1], info[2]
            if v == view:
                # ターゲットルート更新（これを先にやらないとフィルタで弾かれてsetRootIndexが失敗する）
                proxy.setTargetRootPath(path)
                
                # RootIndex更新
                source_idx = self.base_model.index(path)
                proxy_idx = proxy.mapFromSource(source_idx)
                view.setRootIndex(proxy_idx)
                
                # タプルを更新 (view, proxy, path, sep)
                new_info = list(info)
                new_info[2] = path
                self.views[i] = tuple(new_info)
                self.current_paths[i] = path
                self.parent_filer.update_address_bar(path)
                break
        self.update_header_title()

    def toggle_compact(self):
        self.is_compact = not self.is_compact
        for i, (view, proxy, path, sep) in enumerate(self.views):
            if sep:
                sep.setVisible(not self.is_compact)
            
            # 1つ目のviewのヘッダーは常に表示、2つ目以降を制御
            if i > 0:
                view.setHeaderHidden(self.is_compact)
            else:
                view.setHeaderHidden(False)
        
        # タイトル更新で状態を表示
        self.update_header_title()

    def pop_active_view(self):
        """v10.1 Shift+W: フォーカスのあるビュー(または末尾)を削除する"""
        if len(self.current_paths) <= 1:
            return

        # フォーカスのあるViewを探す
        target_index = -1
        for i, (view, _, _, _) in enumerate(self.views):
            if view.hasFocus():
                target_index = i
                break
        
        # フォーカスがなければ末尾を対象にする
        if target_index == -1:
            target_index = len(self.current_paths) - 1
            
        # 削除実行
        # 先頭(index 0)を消すとペインが空になるわけではないが、仕様として「ペインそのものは消さない」ので、
        # もし全部消そうとしているなら(len<=1)すでにreturn済み。
        # ここでは target_index を消す。
        if 0 <= target_index < len(self.current_paths):
            self.current_paths.pop(target_index)
            self.display_folders(self.current_paths)
            
            # アドレスバー更新
            if self.current_paths:
                # 消した場所の手前、あるいは末尾などに合わせるのが親切
                new_focus_idx = min(target_index, len(self.current_paths) - 1)
                self.parent_filer.update_address_bar(self.current_paths[new_focus_idx])
                
                # フォーカス復元（できれば）
                # display_foldersでViewが再生成されるため、indexで追うしかない
                if 0 <= new_focus_idx < len(self.views):
                     self.views[new_focus_idx][0].setFocus()
