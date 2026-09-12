"""
widgets/bucket_panel.py
v23.9: BUCKET(マーク済みパス)のサイドバーUI。

Alt+Click で集めた項目は、従来は行の背景色が変わるだけだった。
別フォルダへ移動すると何を集めたか画面から消え、件数も分からず、
タブを閉じれば消滅していた。「フォルダを横断して集めてから、まとめて
処理する」というこのツール固有の使い方が、集めている最中に見えない
のが最大の弱点だったため、常設の一覧を用意する。

NavigationPane に mixin として合流させる。マークの実体は
FlowArea.marked_paths(タブ単位の set)のままで、ここは表示と操作だけを担う。
"""
import os

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                               QListWidget, QListWidgetItem, QPushButton,
                               QAbstractItemView, QMenu, QMessageBox, QStyle)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from core import looks_like_dir

_BTN_STYLE = (
    "QPushButton { background-color: #2d2d2d; color: #bbb; border: 1px solid #3a3a3a;"
    " border-radius: 3px; padding: 3px 6px; font-size: 10px; }"
    "QPushButton:hover { background-color: #094771; border: 1px solid #007acc; color: #fff; }"
    "QPushButton:disabled { color: #555; border: 1px solid #2a2a2a; }"
)

_LIST_STYLE = """
    QListWidget { background: transparent; color: #bbb; outline: none; padding: 5px; }
    QListWidget::item { height: 34px; padding-left: 8px; border-radius: 4px; }
    QListWidget::item:selected { background-color: #094771; color: white; }
    QListWidget::item:hover { background-color: #2a2d2e; }
"""

_MENU_STYLE = (
    "QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; }"
    "QMenu::item:selected { background-color: #094771; }"
)


class BucketMixin:
    """NavigationPane に BUCKET セクションを提供する mixin"""

    def build_bucket_section(self, section_header_cls):
        """BUCKET セクションを構築して返す。

        Args:
            section_header_cls: NavigationPane 側の SectionHeader クラス。
                循環 import を避けるため、呼び出し側から渡してもらう。
        """
        container = QWidget()
        box = QVBoxLayout(container)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        self.bucket_header = section_header_cls("BUCKET")
        self.bucket_header.setChecked(True)
        self.bucket_header.setArrowType(Qt.DownArrow)

        self.bucket_list = QListWidget()
        self.bucket_list.setFrameStyle(QFrame.NoFrame)
        self.bucket_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.bucket_list.setStyleSheet(_LIST_STYLE)
        self.bucket_list.itemDoubleClicked.connect(self.on_bucket_double_clicked)
        self.bucket_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bucket_list.customContextMenuRequested.connect(self.open_bucket_menu)

        self.bucket_actions = QWidget()
        act_layout = QHBoxLayout(self.bucket_actions)
        act_layout.setContentsMargins(6, 2, 6, 6)
        act_layout.setSpacing(4)

        for label, slot, tip in (
            ("コピー", self.bucket_copy_here, "Bucket の中身を現在のフォルダへコピーします"),
            ("移動", self.bucket_move_here, "Bucket の中身を現在のフォルダへ移動します"),
            ("クリア", self.bucket_clear, "Bucket を空にします(ファイルは消えません)"),
        ):
            btn = QPushButton(label)
            btn.setStyleSheet(_BTN_STYLE)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            act_layout.addWidget(btn)

        box.addWidget(self.bucket_header)
        box.addWidget(self.bucket_list)
        box.addWidget(self.bucket_actions)

        self.bucket_header.clicked.connect(self._toggle_bucket_section)
        return container

    def _toggle_bucket_section(self):
        self.toggle_section(self.bucket_list)
        self.bucket_actions.setVisible(self.bucket_list.isVisible())

    # --- 状態取得 ---------------------------------------------------------

    def _current_area(self):
        """現在のタブ(FlowArea)を返す。取れなければ None。"""
        filer = self.parent_filer
        if not filer or not hasattr(filer, "tab_widget"):
            return None
        area = filer.tab_widget.currentWidget()
        return area if hasattr(area, "marked_paths") else None

    def bucket_paths(self):
        """Bucket の中身を、表示順(フォルダ→名前)で返す"""
        area = self._current_area()
        if area is None:
            return []
        return sorted(
            area.marked_paths,
            key=lambda p: (os.path.dirname(p).lower(), os.path.basename(p).lower())
        )

    def selected_bucket_paths(self):
        return [i.data(Qt.UserRole) for i in self.bucket_list.selectedItems()]

    # --- 表示更新 ---------------------------------------------------------

    def refresh_bucket(self):
        """Bucket 一覧を作り直す。marks_changed とタブ切替から呼ばれる。"""
        if not hasattr(self, "bucket_list"):
            return

        paths = self.bucket_paths()
        self.bucket_list.clear()

        for path in paths:
            name = os.path.basename(path) or path
            parent = os.path.dirname(path)
            item = QListWidgetItem(name + chr(10) + parent)
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            icon = QStyle.SP_DirIcon if looks_like_dir(path) else QStyle.SP_FileIcon
            item.setIcon(self.style().standardIcon(icon))
            self.bucket_list.addItem(item)

        count = len(paths)
        self.bucket_header.setText("  BUCKET (" + str(count) + ")" if count else "  BUCKET")

        layout = self.bucket_actions.layout()
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setEnabled(count > 0)

    # --- 操作 -------------------------------------------------------------

    def on_bucket_double_clicked(self, item):
        """ダブルクリックでその項目のある場所を開く"""
        path = item.data(Qt.UserRole)
        if not path:
            return
        target = path if looks_like_dir(path) else os.path.dirname(path)
        if target:
            self.open_path(target)

    def open_bucket_menu(self, pos):
        item = self.bucket_list.itemAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_STYLE)

        if item:
            selected = self.selected_bucket_paths() or [item.data(Qt.UserRole)]

            reveal_act = QAction("場所を開く", self)
            reveal_act.triggered.connect(lambda: self.on_bucket_double_clicked(item))
            menu.addAction(reveal_act)

            remove_act = QAction("Bucket から外す (" + str(len(selected)) + ")", self)
            remove_act.triggered.connect(lambda: self.bucket_remove(selected))
            menu.addAction(remove_act)

            menu.addSeparator()

        clear_act = QAction("すべて外す", self)
        clear_act.triggered.connect(self.bucket_clear)
        clear_act.setEnabled(self.bucket_list.count() > 0)
        menu.addAction(clear_act)

        menu.exec(self.bucket_list.mapToGlobal(pos))

    def bucket_remove(self, paths):
        """指定項目を Bucket から外す(ファイル自体は消さない)"""
        area = self._current_area()
        if area is None:
            return
        for p in paths:
            area.marked_paths.discard(p)
        self._repaint_marks(area)

    def bucket_clear(self):
        area = self._current_area()
        if area is None:
            return
        area.marked_paths.clear()
        self._repaint_marks(area)

    def _repaint_marks(self, area):
        """マーク色の再描画と Bucket 一覧の更新をまとめて行う"""
        for lane in getattr(area, "lanes", []):
            for pane in getattr(lane, "panes", []):
                try:
                    # 1つのペインから呼べばタブ全体が更新される
                    pane.refresh_all_views_in_tab()
                    return
                except Exception:
                    continue
        # ペインが1つも無い場合でも一覧だけは更新する
        area.notify_marks_changed()

    # --- Bucket からの一括処理 -------------------------------------------

    def bucket_copy_here(self):
        self._bucket_transfer("copy")

    def bucket_move_here(self):
        self._bucket_transfer("move")

    def _bucket_transfer(self, mode):
        """Bucket の中身を、現在アクティブなペインのフォルダへ送る。

        選択があればその分だけ、無ければ Bucket 全体を対象にする。
        """
        paths = self.selected_bucket_paths() or self.bucket_paths()
        if not paths:
            return

        pane = self._bucket_target_pane()
        if pane is None or not pane.current_paths:
            QMessageBox.information(
                self, "Bucket",
                "送り先が分かりません。対象のフォルダを表示しているペインを"
                "クリックしてから実行してください。"
            )
            return

        dest = pane.current_paths[0]
        verb = "コピー" if mode == "copy" else "移動"
        ret = QMessageBox.question(
            self, "Bucket から" + verb,
            str(len(paths)) + " 件を次の場所へ" + verb + "しますか?" + chr(10) + dest,
            QMessageBox.Yes | QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return

        # 衝突確認と進捗表示は execute_batch_paste 側が持っている
        pane.execute_batch_paste(paths, dest, mode)

    def _bucket_target_pane(self):
        """送り先として使うペインを決める"""
        filer = self.parent_filer
        pane = getattr(filer, "active_pane", None) or getattr(filer, "hovered_pane", None)
        if pane is not None and getattr(pane, "current_paths", None):
            return pane

        area = self._current_area()
        if area is None:
            return None
        lane = getattr(area, "active_lane", None) or (area.lanes[0] if area.lanes else None)
        if lane is None or not getattr(lane, "panes", None):
            return None
        # 一番深い(右端の)ペインを既定の送り先とする
        for candidate in reversed(lane.panes):
            if getattr(candidate, "current_paths", None):
                return candidate
        return None
