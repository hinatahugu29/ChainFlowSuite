"""
widgets/conflict_dialog.py
v23.9: ペースト時の同名衝突をユーザーに確認する。

従来は core/file_worker.py の _resolve_conflict() が無条件に連番を付けており、
「更新した資料を元の場所に貼り直して差し替える」という操作ができなかった。
気づかないまま name_1 / name_2 が増え続けるため、最新版が分からなくなる。

ダイアログはワーカースレッドからは出せないので、UI スレッド側で先に全ての
衝突を解決し、決定済みの方針だけをワーカーへ渡す設計にしている。
"""
import os
from datetime import datetime

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QCheckBox, QFrame, QWidget)
from PySide6.QtCore import Qt

# 方針の識別子。file_worker.resolutions の値と対応する。
OVERWRITE = "overwrite"
SKIP = "skip"
RENAME = "rename"
# NEWER はダイアログ上の選択肢。resolutions に入れる前に、更新日時を比べて
# OVERWRITE / SKIP のどちらかへ解決する(ワーカーは NEWER を知らない)。
NEWER = "newer"


def _format_size(num_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def _describe(path):
    """サイズと更新日時を「12.3 MB / 2026-09-12 14:03」形式で返す"""
    try:
        st = os.stat(path)
        stamp = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
        if os.path.isdir(path):
            return f"フォルダ / {stamp}"
        return f"{_format_size(st.st_size)} / {stamp}"
    except Exception:
        return "(情報を取得できません)"


def _mtime(path):
    try:
        return os.stat(path).st_mtime
    except Exception:
        return 0.0


class ConflictDialog(QDialog):
    """1件の衝突について方針を尋ねるダイアログ"""

    def __init__(self, src, dest, remaining, parent=None):
        super().__init__(parent)
        self.setWindowTitle("同じ名前の項目があります")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.choice = None
        self.apply_to_all = False

        self.setStyleSheet(
            "QDialog { background-color: #252526; }"
            "QLabel { color: #ccc; }"
            "QCheckBox { color: #ccc; }"
            "QPushButton { background-color: #333; color: #ddd; border: 1px solid #444;"
            " border-radius: 4px; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #094771; border: 1px solid #007acc; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)

        name = os.path.basename(src)
        head = QLabel(f"<b>{name}</b> は移動先に既に存在します。")
        head.setWordWrap(True)
        layout.addWidget(head)

        layout.addWidget(self._make_row("既存のもの", _describe(dest)))
        layout.addWidget(self._make_row("貼り付けるもの", _describe(src)))

        if os.path.isdir(src) and os.path.isdir(dest):
            note = QLabel("※ フォルダを上書きすると、中身が既存のフォルダに統合されます。")
            note.setStyleSheet("color: #e8a838; font-size: 11px;")
            note.setWordWrap(True)
            layout.addWidget(note)

        if remaining > 1:
            self.all_check = QCheckBox(f"残り {remaining - 1} 件にも同じ操作を適用する")
            layout.addWidget(self.all_check)
        else:
            self.all_check = None

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #3a3a3a;")
        layout.addWidget(line)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        cancel_btn = QPushButton("操作を中止")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        buttons.addStretch()

        for label, value, tip in (
            ("別名で保存", RENAME, "連番を付けて、既存のものを残したまま保存します"),
            ("スキップ", SKIP, "この項目は貼り付けません"),
            ("新しければ上書き", NEWER, "貼り付けるものの方が新しいときだけ置き換えます"),
            ("上書き", OVERWRITE, "既存のものを置き換えます"),
        ):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _checked=False, v=value: self._choose(v))
            buttons.addWidget(btn)

        layout.addLayout(buttons)

    def _make_row(self, caption, detail):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        cap = QLabel(caption)
        cap.setFixedWidth(120)
        cap.setStyleSheet("color: #888; font-size: 11px;")
        val = QLabel(detail)
        val.setStyleSheet("font-size: 11px;")
        row_layout.addWidget(cap)
        row_layout.addWidget(val)
        row_layout.addStretch()
        return row

    def _choose(self, value):
        self.choice = value
        self.apply_to_all = bool(self.all_check and self.all_check.isChecked())
        self.accept()


def resolve_conflicts(parent, src_paths, dest_dir):
    """衝突する項目について方針を決める。

    Returns:
        dict: {src_path: OVERWRITE/SKIP/RENAME}。衝突が無ければ空 dict。
        None: ユーザーが操作全体を中止した場合。
    """
    conflicts = []
    for src in src_paths:
        dest = os.path.join(dest_dir, os.path.basename(src))
        if os.path.exists(dest) and os.path.exists(src):
            conflicts.append((src, dest))

    if not conflicts:
        return {}

    resolutions = {}
    blanket = None

    for i, (src, dest) in enumerate(conflicts):
        if blanket is not None:
            resolutions[src] = _resolve_newer(blanket, src, dest)
            continue

        dialog = ConflictDialog(src, dest, len(conflicts) - i, parent)
        if dialog.exec() != QDialog.Accepted or dialog.choice is None:
            return None

        resolutions[src] = _resolve_newer(dialog.choice, src, dest)
        if dialog.apply_to_all:
            blanket = dialog.choice

    return resolutions


def _resolve_newer(choice, src, dest):
    """NEWER を、更新日時の比較で OVERWRITE / SKIP に落とし込む"""
    if choice != NEWER:
        return choice
    return OVERWRITE if _mtime(src) > _mtime(dest) else SKIP
