"""
tests/test_file_operations.py
v23.9: ファイル操作ユーティリティと、削除(ゴミ箱送り)の単体テスト。

削除はこのアプリで最も取り返しのつかない操作なので、
「ゴミ箱を経由すること」「失敗を黙らないこと」を実際に動かして守る。

    py -m unittest discover -s tests -v
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_operations import (move_to_trash, same_path, normalize_path,
                                  is_network_path, is_office_file,
                                  is_archive_file)


class SamePathTestCase(unittest.TestCase):

    def test_separator_and_case_differences_are_equal(self):
        """区切り文字と大文字小文字の揺らぎを吸収する(Windows)"""
        if os.name != "nt":
            self.skipTest("Windows 固有の比較")
        self.assertTrue(same_path(r"C:\Temp\A", "C:/temp/a"))

    def test_trailing_relative_segments_are_resolved(self):
        base = tempfile.gettempdir()
        self.assertTrue(same_path(base, os.path.join(base, "x", "..")))

    def test_empty_path_is_never_equal(self):
        self.assertFalse(same_path("", ""))
        self.assertFalse(same_path("C:/", ""))

    def test_normalize_returns_absolute(self):
        self.assertTrue(os.path.isabs(normalize_path(".")))


class ClassifierTestCase(unittest.TestCase):

    def test_office_and_archive_detection_is_case_insensitive(self):
        self.assertTrue(is_office_file("A.XLSX"))
        self.assertTrue(is_archive_file("B.ZIP"))
        self.assertFalse(is_office_file("note.txt"))
        self.assertFalse(is_archive_file("note.txt"))

    def test_unc_path_is_network(self):
        self.assertTrue(is_network_path(r"\\server\share\file.txt"))

    def test_local_temp_is_not_network(self):
        self.assertFalse(is_network_path(tempfile.gettempdir()))

    def test_empty_path_is_not_network(self):
        self.assertFalse(is_network_path(""))


@unittest.skipUnless(os.name == "nt", "ゴミ箱送りは Windows のみ")
class MoveToTrashTestCase(unittest.TestCase):

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="cf_trash_test_")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def make_file(self, name):
        path = os.path.join(self.base, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("x")
        return path

    def test_single_file_is_removed_from_disk(self):
        path = self.make_file("a.txt")
        ok, err = move_to_trash([path])
        self.assertTrue(ok, err)
        self.assertFalse(os.path.exists(path))

    def test_multiple_files_at_once(self):
        paths = [self.make_file("a.txt"), self.make_file("b.txt")]
        ok, err = move_to_trash(paths)
        self.assertTrue(ok, err)
        self.assertFalse(any(os.path.exists(p) for p in paths))

    def test_names_with_shell_metacharacters(self):
        """& や %VAR% を含む名前でも壊れない

        シェル経由ではなく SHFileOperationW に直接渡しているので、
        cmd.exe の変数展開や引用の影響を受けない。
        """
        tricky = self.make_file("a b&c %USERPROFILE% (1).txt")
        ok, err = move_to_trash([tricky])
        self.assertTrue(ok, err)
        self.assertFalse(os.path.exists(tricky))

    def test_japanese_name(self):
        path = self.make_file("日本語 ファイル.txt")
        ok, err = move_to_trash([path])
        self.assertTrue(ok, err)
        self.assertFalse(os.path.exists(path))

    def test_directory_with_contents(self):
        folder = os.path.join(self.base, "d", "sub")
        os.makedirs(folder)
        with open(os.path.join(folder, "f.txt"), "w") as f:
            f.write("x")

        ok, err = move_to_trash([os.path.join(self.base, "d")])
        self.assertTrue(ok, err)
        self.assertFalse(os.path.exists(os.path.join(self.base, "d")))

    def test_missing_path_reports_error(self):
        """存在しないパスは黙って成功にしない"""
        ok, err = move_to_trash([os.path.join(self.base, "nope.txt")])
        self.assertFalse(ok)
        self.assertTrue(err)

    def test_empty_list_reports_error(self):
        ok, err = move_to_trash([])
        self.assertFalse(ok)
        self.assertIn("削除対象", err)


class ConflictResolutionTestCase(unittest.TestCase):
    """衝突ダイアログの判定ロジック(UI を作らない部分)"""

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="cf_conflict_")

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def test_newer_resolves_by_mtime(self):
        from widgets.conflict_dialog import _resolve_newer, NEWER, OVERWRITE, SKIP

        old = os.path.join(self.base, "old.txt")
        new = os.path.join(self.base, "new.txt")
        for p in (old, new):
            with open(p, "w") as f:
                f.write("x")
        os.utime(old, (0, 0))

        self.assertEqual(_resolve_newer(NEWER, new, old), OVERWRITE)
        self.assertEqual(_resolve_newer(NEWER, old, new), SKIP)

    def test_non_newer_choice_passes_through(self):
        from widgets.conflict_dialog import _resolve_newer, OVERWRITE, RENAME

        self.assertEqual(_resolve_newer(OVERWRITE, "a", "b"), OVERWRITE)
        self.assertEqual(_resolve_newer(RENAME, "a", "b"), RENAME)

    def test_no_conflict_returns_empty_without_dialog(self):
        """衝突が無ければダイアログを作らず空 dict を返す

        parent=None を渡しても落ちないことで、ダイアログ生成が
        走っていないことを確認している。
        """
        from widgets.conflict_dialog import resolve_conflicts

        src_dir = os.path.join(self.base, "s")
        dst_dir = os.path.join(self.base, "d")
        os.makedirs(src_dir)
        os.makedirs(dst_dir)
        unique = os.path.join(src_dir, "unique.txt")
        with open(unique, "w") as f:
            f.write("x")

        self.assertEqual(resolve_conflicts(None, [unique], dst_dir), {})


if __name__ == "__main__":
    unittest.main()
