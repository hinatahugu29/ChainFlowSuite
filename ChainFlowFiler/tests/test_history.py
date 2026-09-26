"""
tests/test_history.py
v23.9: 操作履歴と Undo の単体テスト。

Undo で一番たちが悪いのは「戻ったつもりで戻っていない」ことと、
「戻す際に別のファイルを潰す」こと。その2つを重点的に見る。

    py -m unittest discover -s tests -v
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.history import OperationHistory, MOVE, COPY, RENAME


class HistoryStackTestCase(unittest.TestCase):

    def setUp(self):
        self.history = OperationHistory(limit=3)

    def test_empty_history_reports_nothing_to_undo(self):
        self.assertFalse(self.history.can_undo())
        ok, msg = self.history.undo()
        self.assertFalse(ok)
        self.assertEqual(msg, "")

    def test_empty_pairs_are_not_recorded(self):
        self.assertIsNone(self.history.push(MOVE, []))
        self.assertFalse(self.history.can_undo())

    def test_limit_drops_oldest(self):
        for i in range(5):
            self.history.push(MOVE, [("a{}".format(i), "b{}".format(i))])
        entries = self.history.entries()
        self.assertEqual(len(entries), 3, "上限を超えたら古いものから捨てる")
        self.assertIn("b4", entries[0].label)

    def test_label_describes_single_and_multiple(self):
        single = self.history.push(MOVE, [("a", "b.txt")])
        multi = self.history.push(COPY, [("a", "b"), ("c", "d")])
        self.assertIn("b.txt", single.label)
        self.assertIn("2 件", multi.label)


class UndoMoveTestCase(unittest.TestCase):

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="cf_undo_")
        self.src = os.path.join(self.base, "src")
        self.dst = os.path.join(self.base, "dst")
        os.makedirs(self.src)
        os.makedirs(self.dst)
        self.history = OperationHistory()

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def make(self, path, content="x"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def read(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_move_is_restored_to_original_path(self):
        origin = os.path.join(self.src, "a.txt")
        moved = self.make(os.path.join(self.dst, "a.txt"))
        self.history.push(MOVE, [(origin, moved)])

        ok, msg = self.history.undo()
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.exists(origin))
        self.assertFalse(os.path.exists(moved))

    def test_rename_is_restored(self):
        old = os.path.join(self.src, "before.txt")
        new = self.make(os.path.join(self.src, "after.txt"))
        self.history.push(RENAME, [(old, new)])

        ok, msg = self.history.undo()
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.exists(old))
        self.assertFalse(os.path.exists(new))

    def test_folder_move_is_restored(self):
        origin = os.path.join(self.src, "d")
        moved = os.path.join(self.dst, "d")
        self.make(os.path.join(moved, "sub", "f.txt"))
        self.history.push(MOVE, [(origin, moved)])

        ok, msg = self.history.undo()
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.isfile(os.path.join(origin, "sub", "f.txt")))

    def test_refuses_when_something_else_occupies_original_path(self):
        """戻し先に別のものができていたら、潰さずに中止する"""
        origin = self.make(os.path.join(self.src, "a.txt"), content="SOMETHING ELSE")
        moved = self.make(os.path.join(self.dst, "a.txt"), content="MOVED")
        self.history.push(MOVE, [(origin, moved)])

        ok, msg = self.history.undo()
        self.assertFalse(ok)
        self.assertIn("別の項目", msg)
        self.assertEqual(self.read(origin), "SOMETHING ELSE", "既存を潰していない")
        self.assertTrue(os.path.exists(moved), "移動先も消していない")

    def test_reports_when_target_disappeared(self):
        """移動先が既に無い(外で消された)場合は失敗として報告する"""
        origin = os.path.join(self.src, "a.txt")
        moved = os.path.join(self.dst, "a.txt")
        self.history.push(MOVE, [(origin, moved)])

        ok, msg = self.history.undo()
        self.assertFalse(ok)
        self.assertIn("見つかりません", msg)

    def test_partial_restore_is_reported_as_failure(self):
        """一部しか戻せなければ成功扱いにしない"""
        good_origin = os.path.join(self.src, "good.txt")
        good_moved = self.make(os.path.join(self.dst, "good.txt"))
        bad_origin = os.path.join(self.src, "bad.txt")
        bad_moved = os.path.join(self.dst, "bad.txt")  # 存在しない
        self.history.push(MOVE, [(good_origin, good_moved), (bad_origin, bad_moved)])

        ok, msg = self.history.undo()
        self.assertFalse(ok)
        self.assertIn("1/2", msg)
        self.assertTrue(os.path.exists(good_origin), "戻せる分は戻している")

    def test_undo_pops_the_entry(self):
        origin = os.path.join(self.src, "a.txt")
        moved = self.make(os.path.join(self.dst, "a.txt"))
        self.history.push(MOVE, [(origin, moved)])

        self.history.undo()
        self.assertFalse(self.history.can_undo(), "同じ操作を二重に取り消さない")


@unittest.skipUnless(os.name == "nt", "コピーの取り消しはゴミ箱を使う")
class UndoCopyTestCase(unittest.TestCase):

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="cf_undo_copy_")
        self.history = OperationHistory()

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_copy_undo_removes_duplicate_and_keeps_original(self):
        origin = os.path.join(self.base, "orig.txt")
        copied = os.path.join(self.base, "orig_1.txt")
        for p in (origin, copied):
            with open(p, "w", encoding="utf-8") as f:
                f.write("x")

        self.history.push(COPY, [(origin, copied)])
        ok, msg = self.history.undo()

        self.assertTrue(ok, msg)
        self.assertFalse(os.path.exists(copied), "複製はゴミ箱へ送られた")
        self.assertTrue(os.path.exists(origin), "元は touch していない")

    def test_copy_undo_reports_when_nothing_left(self):
        missing = os.path.join(self.base, "gone.txt")
        self.history.push(COPY, [("orig", missing)])

        ok, msg = self.history.undo()
        self.assertFalse(ok)
        self.assertIn("見つかりません", msg)


if __name__ == "__main__":
    unittest.main()
