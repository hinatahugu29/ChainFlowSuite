"""
tests/test_proxy_vanished.py
v23.10: 移動・削除した項目が一覧に残り続けないこと、そして作り直した
項目が消えたままにならないことを守るテスト。

QFileSystemModel はフォルダの変更通知を受けて行を消すが、SMB 共有では
通知が届かないことがあり、移動元に「存在しないファイル」の行が残っていた。
リフレッシュ (キャッシュ破棄 + invalidate) でも setRootPath のやり直しでも
消えないため、操作した側が「これは消えた」と宣言して伏せる作りにしている。

伏せる仕組みには逆方向の危険がある。伏せ札が外れないと「実体はあるのに
一覧に出ない」状態になり、こちらの方が害が大きい。両方向を固定する。

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
    """Qt のイベントループを msec だけ回す(監視の通知を届かせるため)。"""
    loop = QEventLoop()
    QTimer.singleShot(msec, loop.quit)
    loop.exec()


class _PaneFixture:
    """一覧を1つ用意するだけの土台。TestCase ではないので単体では走らない。"""

    # 変更通知を受け取るか。False は SMB 共有で通知が届かない状況の再現。
    WATCH = False
    # 最初から置いておくファイル
    FILES = ("x.txt", "y.txt")

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="cf_vanish_")
        self.src_dir = os.path.join(self.base, "A")
        self.dst_dir = os.path.join(self.base, "B")
        os.makedirs(self.src_dir)
        os.makedirs(self.dst_dir)
        for name in self.FILES:
            with open(os.path.join(self.src_dir, name), "wb") as fp:
                fp.write(b"d")

        self.model = QFileSystemModel()
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot
                             | QDir.Hidden | QDir.Drives)
        self.model.setResolveSymlinks(False)
        self.model.setReadOnly(False)
        self.model.setOption(QFileSystemModel.DontWatchForChanges,
                             not self.WATCH)
        self.model.setRootPath(
            self.src_dir if self.WATCH else QDir.rootPath())

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

    def displayed(self):
        root = self.view.rootIndex()
        return sorted(self.proxy.data(self.proxy.index(row, 0, root))
                      for row in range(self.proxy.rowCount(root)))

    def on_disk(self):
        return sorted(os.listdir(self.src_dir))


class UnwatchedShareTestCase(_PaneFixture, unittest.TestCase):
    """変更通知が届かない共有での挙動(SMB 相当)"""

    WATCH = False

    def test_refresh_alone_does_not_remove_the_ghost(self):
        """前提の確認: 通知が来ない場合、従来のリフレッシュでは消えない"""
        moved = os.path.join(self.src_dir, "x.txt")
        shutil.move(moved, os.path.join(self.dst_dir, "x.txt"))
        _spin(1500)

        self.proxy.invalidate()
        _spin(500)

        self.assertIn("x.txt", self.displayed(),
                      "この前提が崩れたなら、伏せる仕組みは不要になっている")

    def test_moved_item_disappears_once_declared(self):
        moved = os.path.join(self.src_dir, "x.txt")
        shutil.move(moved, os.path.join(self.dst_dir, "x.txt"))
        _spin(1000)

        self.proxy.mark_paths_vanished([moved])
        _spin(500)

        self.assertEqual(self.displayed(), ["y.txt"])
        self.assertEqual(self.displayed(), self.on_disk())

    def test_restored_item_comes_back(self):
        """Undo で元の場所へ戻したら、伏せるのをやめて再び表示する"""
        moved = os.path.join(self.src_dir, "x.txt")
        shutil.move(moved, os.path.join(self.dst_dir, "x.txt"))
        self.proxy.mark_paths_vanished([moved])
        _spin(800)
        self.assertEqual(self.displayed(), ["y.txt"])

        shutil.move(os.path.join(self.dst_dir, "x.txt"), moved)
        self.proxy.unmark_paths_vanished([moved])
        _spin(800)

        self.assertEqual(self.displayed(), ["x.txt", "y.txt"])

    def test_case_and_separator_differences_still_match(self):
        """Windows のパスの揺れ (大小文字・区切り) で取りこぼさない"""
        moved = os.path.join(self.src_dir, "x.txt")
        shutil.move(moved, os.path.join(self.dst_dir, "x.txt"))
        wobbly = moved.upper().replace(os.sep, "/")
        self.proxy.mark_paths_vanished([wobbly])
        _spin(500)

        self.assertEqual(self.displayed(), ["y.txt"])

    def test_f5_unhides_a_file_that_still_exists(self):
        """取りこぼしても F5 で正しい状態に戻せる(逃げ道の確認)"""
        target = os.path.join(self.src_dir, "x.txt")
        self.proxy.mark_paths_vanished([target])   # 実体はまだある
        _spin(500)
        self.assertNotIn("x.txt", self.displayed())

        self.proxy.clear_native_cache()   # F5 が呼ぶ経路
        self.proxy.invalidate()
        _spin(500)

        self.assertIn("x.txt", self.displayed())


class WatchedLocalDriveTestCase(_PaneFixture, unittest.TestCase):
    """変更通知が届くローカルドライブでの挙動"""

    WATCH = True
    FILES = ("x.txt", "y.txt", "Looper.zip")

    def test_recreated_with_same_name_becomes_visible_again(self):
        """ZIP を作り直したら一覧に出ること

        v23.10 の回帰。伏せる仕組みを入れた当初、削除 -> 同名で作り直しの
        流れで「実体はあるのに一覧に出ない」状態になっていた。伏せ札を
        外す判定を rowsAboutToBeInserted に繋いでいたためで、挿入前の
        時点では行がまだ無く filePath() が目的のパスを返さない。判定は
        挿入後(rowsInserted)でなければならない。
        """
        zip_path = os.path.join(self.src_dir, "Looper.zip")
        self.assertIn("Looper.zip", self.displayed())

        # 古い ZIP を消す -> アプリが「消えた」と宣言する
        os.remove(zip_path)
        self.proxy.mark_paths_vanished([zip_path])
        _spin(1200)
        self.assertNotIn("Looper.zip", self.displayed())

        # 同じ名前で作り直す
        with open(zip_path, "wb") as fp:
            fp.write(b"REBUILT")
        _spin(3000)

        self.assertIn("Looper.zip", self.displayed(),
                      "作り直した ZIP が一覧に出ていない")
        self.assertEqual(self.displayed(), self.on_disk())

    def test_overwritten_in_place_stays_visible(self):
        """消さずに上書きで作り直した場合も見えたままであること"""
        zip_path = os.path.join(self.src_dir, "Looper.zip")
        with open(zip_path, "wb") as fp:
            fp.write(b"REBUILT_IN_PLACE_LONGER")
        _spin(2500)

        self.assertIn("Looper.zip", self.displayed())
        self.assertEqual(self.displayed(), self.on_disk())


if __name__ == "__main__":
    unittest.main()
