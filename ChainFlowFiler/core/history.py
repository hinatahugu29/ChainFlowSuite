"""
core/history.py
v23.9: ファイル操作の履歴と Undo。

Miller Columns は横に多くのペインが並ぶため、ドラッグ&ドロップの誤爆が
起きやすい。移動・リネームのどれも取り消せないのは、日常的に使う
ファイラーとしては危うい。

対応しているのは「このアプリが行った操作」だけで、以下の方針を取る:

  - 移動 / リネーム: 元の場所へ正確に戻す
  - コピー: 作られた複製をゴミ箱へ送る(元は触らない)
  - 削除: 扱わない。ゴミ箱送りなので OS 側の「元に戻す」で復元できる
  - 上書きで潰した既存ファイル: 復元できないため、そもそも記録しない

「戻せるはずのものが戻らない」のが一番たちが悪いので、記録した時点から
状況が変わっていたら(戻し先に別のものができている等)、黙って上書き
せずに中止して理由を返す。
"""
import os

from .file_operations import move_to_trash


# 操作種別
MOVE = "move"
COPY = "copy"
RENAME = "rename"


class OperationEntry:
    """1回分の操作。複数ファイルをまとめて1エントリとして扱う。"""

    def __init__(self, kind, pairs, label=""):
        """
        Args:
            kind: MOVE / COPY / RENAME
            pairs: [(元のパス, 実際の作成先), ...]
            label: 履歴表示用の短い説明
        """
        self.kind = kind
        self.pairs = list(pairs)
        self.label = label or self._default_label()

    def _default_label(self):
        verb = {MOVE: "移動", COPY: "コピー", RENAME: "リネーム"}.get(self.kind, self.kind)
        if len(self.pairs) == 1:
            return f"{verb}: {os.path.basename(self.pairs[0][1])}"
        return f"{verb}: {len(self.pairs)} 件"

    def describe_undo(self):
        verb = {MOVE: "移動を取り消す", COPY: "コピーを取り消す",
                RENAME: "リネームを取り消す"}.get(self.kind, "取り消す")
        return f"{verb} ({len(self.pairs)} 件)"


class OperationHistory:
    """取り消せる操作のスタック"""

    def __init__(self, limit=50):
        self._entries = []
        self._limit = limit
        # v23.10: 直前の undo で「現れたパス」と「消えたパス」。
        # 一覧側は、変更通知が届かない共有のために消えたパスを自前で
        # 伏せている。取り消しで戻ってきたものは伏せるのをやめる必要が
        # あるため、何がどうなったかをここから取れるようにする。
        self.last_appeared = []
        self.last_vanished = []

    def push(self, kind, pairs, label=""):
        """操作を記録する。pairs が空なら何もしない。"""
        pairs = [(src, dest) for src, dest in pairs if src and dest]
        if not pairs:
            return None
        entry = OperationEntry(kind, pairs, label)
        self._entries.append(entry)
        if len(self._entries) > self._limit:
            self._entries.pop(0)
        return entry

    def can_undo(self):
        return bool(self._entries)

    def peek(self):
        return self._entries[-1] if self._entries else None

    def entries(self):
        """新しい順に返す(履歴表示用)"""
        return list(reversed(self._entries))

    def clear(self):
        self._entries.clear()

    def undo(self):
        """直前の操作を取り消す。

        Returns:
            (ok, message): ok=False なら message に理由が入る。
                           取り消せるものが無い場合は (False, "") を返す。
        """
        if not self._entries:
            return False, ""

        entry = self._entries.pop()
        self.last_appeared = []
        self.last_vanished = []

        if entry.kind == COPY:
            return self._undo_copy(entry)
        return self._undo_move(entry)

    # --- 個別の取り消し ---------------------------------------------------

    def _undo_move(self, entry):
        """移動 / リネームを元の場所へ戻す"""
        restored = 0
        problems = []

        for src, dest in entry.pairs:
            if not os.path.exists(dest):
                problems.append(f"{os.path.basename(dest)}: 移動先に見つかりません")
                continue
            if os.path.exists(src):
                # 戻し先に別のものができている。上書きするとそれを失うので中止。
                problems.append(f"{os.path.basename(src)}: 戻し先に別の項目があります")
                continue

            parent = os.path.dirname(src)
            try:
                if parent and not os.path.isdir(parent):
                    os.makedirs(parent, exist_ok=True)
                if os.path.isfile(dest):
                    os.replace(dest, src)
                else:
                    _move_any(dest, src)
                restored += 1
                self.last_appeared.append(src)
                self.last_vanished.append(dest)
            except Exception as e:
                problems.append(f"{os.path.basename(dest)}: {e}")

        return self._report(restored, len(entry.pairs), problems, "戻しました")

    def _undo_copy(self, entry):
        """コピーで作られた複製をゴミ箱へ送る(元は触らない)"""
        targets = [dest for _src, dest in entry.pairs if os.path.exists(dest)]
        if not targets:
            return False, "取り消す対象が見つかりません"

        ok, err = move_to_trash(targets)
        if ok:
            self.last_vanished = list(targets)
            return True, f"コピーした {len(targets)} 件をゴミ箱へ移動しました"
        if err == "cancelled":
            return False, ""
        return False, f"取り消せませんでした: {err}"

    def _report(self, restored, total, problems, verb):
        if restored == total:
            return True, f"{restored} 件を{verb}"
        detail = chr(10).join(problems[:5])
        if len(problems) > 5:
            detail += chr(10) + f"... 他 {len(problems) - 5} 件"
        if restored:
            return False, f"{restored}/{total} 件のみ{verb}{chr(10)}{detail}"
        return False, f"取り消せませんでした{chr(10)}{detail}"


def _move_any(src, dest):
    """ファイルでもフォルダでも動く移動(同一ボリュームなら即時)"""
    import shutil
    shutil.move(src, dest)
