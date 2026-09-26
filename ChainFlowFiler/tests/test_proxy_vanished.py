"""
tests/test_proxy_vanished.py
v23.10: 移動・削除した項目が一覧に残り続けないことを守るテスト。

QFileSystemModel はフォルダの変更通知を受けて行を消すが、SMB 共有では
通知が届かないことがあり、移動元に「存在しないファイル」の行が残っていた。
リフレッシュ (キャッシュ破棄 + invalidate) でも setRootPath のやり直しでも
消えないため、操作した側が「これは消えた」と宣言して伏せる作りにしている。

通知が来ない状況は QFileSystemModel.DontWatchForChanges で再現する。

    py -m unittest discover -s tests -v
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QDir, QEventLoop, QTimer
from PySide6.QtWidgets import QFileSystemModel, QTreeView

# Qt アプリケーションの生成は tests/__init__.py に一本化している
from tests import qt_app as _app

from models.proxy_model import SmartSortFilterProxyModel


def _spin(msec):
    loop = QEventLoop()
    QTimer.singleShot(msec, loop.quit)
    loop.exec()


class VanishedPathsTestCase(unittest.TestCase):

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="cf_vanish_")
        self.src_dir = os.path.join(self.base, "A")
        self.dst_dir = os.path.join(self.base, "B")
        os.makedirs(self.src_dir)
        os.makedirs(self.dst_dir)
        for name in ("x.txt", "y.txt"):
            with open(os.path.join(self.src_dir, name), "wb") as fp:
                fp.write(b"d")

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot
                             | QDir.Hidden | QDir.Drives)
        self.model.setResolveSymlinks(False)
        self.model.setReadOnly(False)
        # ネットワーク共有で変更通知が届かない状況を再現する
        self.model.setOption(QFileSystemModel.DontWatchForChanges, True)
        self.model.setRootPath(QDir.rootPath())

        self.proxy = SmartSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.view = QTreeView()
        self.view.setModel(self.proxy)
        self.proxy.setTargetRootPath(self.src_dir)
        self.view.setRootIndex(
            self.proxy.mapFromSource(self.model.index(self.src_dir)))
        self.view.show()
        _spin(1200)

    def tearDown(self):
        self.view.setModel(None)
        self.view.deleteLater()
        self.proxy.setSourceModel(None)
        _spin(100)
        del self.view, self.proxy, self.model
        _spin(100)
        shutil.rmtree(self.base, ignore_errors=True)

    def _displayed(self):
        root = self.view.rootIndex()
        return sorted(self.proxy.data(self.proxy.index(row, 0, root))
                      for row in range(self.proxy.rowCount(root)))

    def test_refresh_alone_does_not_remove_the_ghost(self):
        """前提の確認: 通知が来ない場合、従来のリフレッシュでは消えない"""
        moved = os.path.join(self.src_dir, "x.txt")
        shutil.move(moved, os.path.join(self.dst_dir, "x.txt"))
        _spin(1500)

        self.proxy.clear_native_cache()
        self.proxy.invalidate()
        _spin(500)

        self.assertIn("x.txt", self._displayed(),
                      "この前提が崩れたなら、伏せる仕組みは不要になっている")

    def test_moved_item_disappears_once_declared(self):
        moved = os.path.join(self.src_dir, "x.txt")
        shutil.move(moved, os.path.join(self.dst_dir, "x.txt"))
        _spin(1000)

        self.proxy.mark_paths_vanished([moved])
        _spin(500)

        self.assertEqual(self._displayed(), ["y.txt"])
        self.assertEqual(self._displayed(), sorted(os.listdir(self.src_dir)))

    def test_restored_item_comes_back(self):
        """Undo で元の場所へ戻したら、伏せるのをやめて再び表示する"""
        moved = os.path.join(self.src_dir, "x.txt")
        shutil.move(moved, os.path.join(self.dst_dir, "x.txt"))
        self.proxy.mark_paths_vanished([moved])
        _spin(800)
        self.assertEqual(self._displayed(), ["y.txt"])

        shutil.move(os.path.join(self.dst_dir, "x.txt"), moved)
        self.proxy.unmark_paths_vanished([moved])
        _spin(800)

        self.assertEqual(self._displayed(), ["x.txt", "y.txt"])

    def test_case_and_separator_differences_still_match(self):
        """Windows のパスの揺れ (大小文字・区切り) で取りこぼさない"""
        moved = os.path.join(self.src_dir, "x.txt")
        shutil.move(moved, os.path.join(self.dst_dir, "x.txt"))
        wobbly = moved.upper().replace(os.sep, "/")
        self.proxy.mark_paths_vanished([wobbly])
        _spin(500)

        self.assertEqual(self._displayed(), ["y.txt"])


if __name__ == "__main__":
    unittest.main()
