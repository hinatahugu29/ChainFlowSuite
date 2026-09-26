"""
tests/test_proxy_freshness.py
v23.10: 既存ファイルが書き換わったときに、並べ替えが追随することを守るテスト。

ZIP の作り直しや同名への上書きコピーは、行が増えも減りもしないまま
更新日時とサイズだけが変わる。プロキシはメタデータをパス単位で
キャッシュしているため、これを捨てないと日付ソートの順位が
古いままになり、作り直したはずのファイルが一番下に沈む。

    py -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import Qt, QEventLoop, QTimer
from PySide6.QtWidgets import QTreeView

from PySide6.QtCore import QDir
from PySide6.QtWidgets import QFileSystemModel

from models.proxy_model import SmartSortFilterProxyModel

# Qt アプリケーションの生成は tests/__init__.py に一本化している
from tests import qt_app as _app

DATE_COLUMN = 3


def _spin(msec):
    """Qt のイベントループを msec だけ回す(監視の通知を届かせるため)。"""
    loop = QEventLoop()
    QTimer.singleShot(msec, loop.quit)
    loop.exec()


class SortFollowsInPlaceModificationTestCase(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="cf_fresh_")
        # 更新日時に確実な差を付けるため、1秒以上空けて作る
        for name in ("a.zip", "b.txt", "c.txt"):
            with open(os.path.join(self.dir, name), "wb") as fp:
                fp.write(b"x")
            time.sleep(1.1)

        # core.global_model の共有インスタンスは使わない。プロセス全体で
        # 生き続け、他のテストが作っては消す一時フォルダを監視し続けるため、
        # 終了時にコレクションスレッドと衝突して落ちることがある。
        # 設定は get_global_file_system_model() と同じにする。
        self.model = QFileSystemModel()
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot
                             | QDir.Hidden | QDir.Drives)
        self.model.setResolveSymlinks(False)
        self.model.setRootPath(self.dir)
        self.model.setReadOnly(False)
        self.proxy = SmartSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.view = QTreeView()
        self.view.setModel(self.proxy)
        self.proxy.setTargetRootPath(self.dir)
        self.view.setRootIndex(
            self.proxy.mapFromSource(self.model.index(self.dir)))
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(DATE_COLUMN, Qt.DescendingOrder)
        self.view.show()
        _spin(1500)

    def tearDown(self):
        self.view.setModel(None)
        self.view.deleteLater()
        self.proxy.setSourceModel(None)
        _spin(100)
        del self.view, self.proxy, self.model
        _spin(100)

    def _displayed_order(self):
        root = self.view.rootIndex()
        return [self.proxy.data(self.proxy.index(row, 0, root))
                for row in range(self.proxy.rowCount(root))]

    def _actual_order(self):
        names = os.listdir(self.dir)
        return sorted(
            names,
            key=lambda n: -os.path.getmtime(os.path.join(self.dir, n)))

    def test_rebuilt_file_moves_to_top_of_date_sort(self):
        self.assertEqual(self._displayed_order(), ["c.txt", "b.txt", "a.zip"],
                         "前提: 最初は a.zip が一番古い")

        time.sleep(1.1)
        # ZIP の作り直しに相当する、同一パスへの上書き
        with open(os.path.join(self.dir, "a.zip"), "wb") as fp:
            fp.write(b"REBUILT")
        _spin(3000)

        self.assertEqual(self._displayed_order(), self._actual_order())
        self.assertEqual(self._displayed_order()[0], "a.zip",
                         "作り直した a.zip が日付降順の先頭に来ていない")


if __name__ == "__main__":
    unittest.main()
