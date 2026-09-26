"""
tests/__init__.py
v23.10: テスト全体で使う Qt アプリケーションを1つに揃える。

QThread だけなら QCoreApplication で足りるが、ウィジェットを使うテストが
同じプロセスに混ざると、非GUIのインスタンスの上に QTreeView を載せる形に
なり、終了時にプロセスごと落ちる。ここで先に GUI 版を1つ作っておき、
各テストは QApplication.instance() を受け取るだけにする。

画面は出さない (offscreen)。
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

qt_app = QApplication.instance() or QApplication(sys.argv)
