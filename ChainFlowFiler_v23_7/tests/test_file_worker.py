"""
tests/test_file_worker.py
v23.9: コピー/移動エンジンの単体テスト。

このファイルが守っているのは「ファイルを失わないこと」。
過去に以下の事故があり、いずれも GUI を触らないと気づけなかった:

  - 移動に失敗しても finished(True, "N/N 件完了") を emit していたため、
    移動できたつもりで元を失う経路があった
  - 同名衝突が黙って連番になり、貼り直しでの差し替えができなかった
  - フォルダコピーが shutil.copytree() の一発呼び出しで、進捗も
    キャンセルも効かなかった

pytest は入れていない。標準ライブラリだけで動くようにしてあるので、
リポジトリのルートで次のように実行する:

    py -m unittest discover -s tests -v
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QCoreApplication

from core.file_worker import FileOperationWorker

# QThread を作るのに QCoreApplication が要る(1度だけ作れば使い回せる)
_app = QCoreApplication.instance() or QCoreApplication(sys.argv)


class CopyMoveTestCase(unittest.TestCase):

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="cfw_test_")
        self.src = os.path.join(self.base, "src")
        self.dst = os.path.join(self.base, "dst")
        os.makedirs(self.src)
        os.makedirs(self.dst)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    # --- ヘルパ -------------------------------------------------------

    def make_file(self, *parts, content="x"):
        path = os.path.join(*parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def read(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def run_worker(self, op, srcs, dest, resolutions=None, cancel_after=None):
        """ワーカーを同期実行して (success, message, ticks) を返す"""
        worker = FileOperationWorker(op)
        worker.src_paths = srcs
        worker.dest_path = dest
        worker.resolutions = resolutions or {}

        result = {}
        ticks = []

        def on_progress(current, total, name):
            ticks.append((current, total, name))
            if cancel_after and len(ticks) >= cancel_after:
                worker.cancel()

        worker.progress.connect(on_progress)
        worker.finished.connect(lambda ok, msg: result.update(ok=ok, msg=msg))
        worker.run()  # スレッドを起こさずその場で実行する
        return result.get("ok"), result.get("msg", ""), ticks

    # --- 失敗の報告 ---------------------------------------------------

    def test_move_failure_is_reported_not_swallowed(self):
        """ロックされたファイルの移動失敗が success=False で返る

        v23.8 以前はここが True になっており、移動できていないのに
        「完了」と表示されていた。
        """
        locked = self.make_file(self.src, "locked.txt")
        handle = open(locked, "r+")  # Windows では移動がブロックされる
        try:
            ok, msg, _ = self.run_worker("move", [locked], self.dst)
        finally:
            handle.close()

        self.assertFalse(ok)
        self.assertIn("locked.txt", msg)
        self.assertTrue(os.path.exists(locked), "失敗したのに元が消えていない")

    def test_partial_failure_reports_both_counts(self):
        """一部成功・一部失敗で、成功数と失敗内訳の両方が出る"""
        good = self.make_file(self.src, "good.txt")
        locked = self.make_file(self.src, "locked.txt")
        handle = open(locked, "r+")
        try:
            ok, msg, _ = self.run_worker("move", [good, locked], self.dst)
        finally:
            handle.close()

        self.assertFalse(ok)
        self.assertIn("成功 1/2", msg)
        self.assertIn("失敗 1", msg)

    def test_missing_source_is_skipped_not_failed(self):
        """元が存在しないものは失敗ではなくスキップ扱い"""
        missing = os.path.join(self.src, "nope.txt")
        ok, msg, _ = self.run_worker("move", [missing], self.dst)
        self.assertTrue(ok)
        self.assertIn("スキップ", msg)

    # --- 危険な移動の拒否 ---------------------------------------------

    def test_move_into_same_folder_is_rejected(self):
        """移動元と移動先が同じフォルダなら弾く(連番コピーを作らない)"""
        f = self.make_file(self.src, "a.txt")
        ok, msg, _ = self.run_worker("move", [f], self.src)
        self.assertFalse(ok)
        self.assertIn("同じフォルダ", msg)
        self.assertEqual(sorted(os.listdir(self.src)), ["a.txt"])

    def test_move_folder_into_itself_is_rejected(self):
        """自分の内側へのフォルダ移動を弾く(無限再帰を防ぐ)"""
        self.make_file(self.src, "d", "f.txt")
        folder = os.path.join(self.src, "d")
        inner = os.path.join(folder, "inner")
        os.makedirs(inner)

        ok, msg, _ = self.run_worker("move", [folder], inner)
        self.assertFalse(ok)
        self.assertIn("内側", msg)

    # --- 衝突時の方針 -------------------------------------------------

    def test_default_conflict_keeps_both_with_suffix(self):
        """方針未指定なら従来どおり連番を付けて両方残す"""
        new = self.make_file(self.src, "a.txt", content="NEW")
        self.make_file(self.dst, "a.txt", content="OLD")

        ok, _, _ = self.run_worker("copy", [new], self.dst)
        self.assertTrue(ok)
        self.assertEqual(sorted(os.listdir(self.dst)), ["a.txt", "a_1.txt"])
        self.assertEqual(self.read(os.path.join(self.dst, "a.txt")), "OLD")

    def test_overwrite_replaces_existing(self):
        """overwrite で既存が置き換わり、連番は作られない"""
        new = self.make_file(self.src, "a.txt", content="NEW")
        self.make_file(self.dst, "a.txt", content="OLD")

        ok, _, _ = self.run_worker("copy", [new], self.dst, {new: "overwrite"})
        self.assertTrue(ok)
        self.assertEqual(os.listdir(self.dst), ["a.txt"])
        self.assertEqual(self.read(os.path.join(self.dst, "a.txt")), "NEW")

    def test_skip_leaves_existing_untouched(self):
        """skip なら既存がそのまま残り、何も増えない"""
        new = self.make_file(self.src, "a.txt", content="NEW")
        self.make_file(self.dst, "a.txt", content="OLD")

        ok, _, _ = self.run_worker("copy", [new], self.dst, {new: "skip"})
        self.assertTrue(ok)
        self.assertEqual(os.listdir(self.dst), ["a.txt"])
        self.assertEqual(self.read(os.path.join(self.dst, "a.txt")), "OLD")

    def test_folder_overwrite_merges_and_keeps_other_files(self):
        """フォルダの上書きはマージ。既存にしかないファイルは残る"""
        self.make_file(self.src, "d", "same.txt", content="NEW")
        self.make_file(self.src, "d", "only_new.txt")
        self.make_file(self.dst, "d", "same.txt", content="OLD")
        self.make_file(self.dst, "d", "only_old.txt")
        folder = os.path.join(self.src, "d")

        ok, _, _ = self.run_worker("copy", [folder], self.dst, {folder: "overwrite"})
        self.assertTrue(ok)

        merged = sorted(os.listdir(os.path.join(self.dst, "d")))
        self.assertEqual(merged, ["only_new.txt", "only_old.txt", "same.txt"])
        self.assertEqual(self.read(os.path.join(self.dst, "d", "same.txt")), "NEW")

    # --- 進捗とキャンセル ---------------------------------------------

    def test_folder_copy_reports_per_file_progress(self):
        """フォルダのコピーがファイル単位で進捗を出す

        v23.9 以前は copytree() 一発だったため、巨大フォルダでも
        進捗が 0 のまま動かなかった。
        """
        for i in range(5):
            self.make_file(self.src, "big", "sub", "f{}.txt".format(i))
        folder = os.path.join(self.src, "big")

        ok, _, ticks = self.run_worker("copy", [folder], self.dst)
        self.assertTrue(ok)
        self.assertEqual(len(ticks), 5, "ファイル数だけ進捗が出る")
        self.assertEqual(ticks[0][1], 5, "分母が総ファイル数になっている")

    def test_folder_copy_can_be_cancelled_midway(self):
        """フォルダのコピー中にキャンセルが効く"""
        for i in range(20):
            self.make_file(self.src, "big", "f{}.txt".format(i))
        folder = os.path.join(self.src, "big")

        ok, msg, ticks = self.run_worker("copy", [folder], self.dst, cancel_after=3)
        copied = sum(len(files) for _, _, files in os.walk(self.dst))

        self.assertFalse(ok)
        self.assertIn("キャンセル", msg)
        self.assertLess(copied, 20, "途中で止まっている")

    # --- 移動の後始末 -------------------------------------------------

    def test_folder_move_removes_source(self):
        """フォルダを移動したら元が残らない"""
        for i in range(3):
            self.make_file(self.src, "mv", "sub", "f{}.txt".format(i))
        folder = os.path.join(self.src, "mv")

        ok, _, _ = self.run_worker("move", [folder], self.dst)
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(folder), "移動元が消えている")
        self.assertTrue(os.path.isdir(os.path.join(self.dst, "mv", "sub")))


if __name__ == "__main__":
    unittest.main()
