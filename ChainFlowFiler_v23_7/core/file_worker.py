"""
v14.2 ファイル操作ワーカースレッド
UIフリーズを防止するため、重いファイル操作をバックグラウンドで実行する
"""
import os
import sys
import shutil
import zipfile

from PySide6.QtCore import QThread, Signal


class FileOperationWorker(QThread):
    """
    ファイル操作（コピー/移動/ZIP圧縮・解凍）をバックグラウンドで実行するワーカー
    
    Signals:
        progress(current, total, current_file): 進捗更新
        finished(success, message): 操作完了
        error(message): エラー発生
    """
    
    progress = Signal(int, int, str)  # current, total, current_file
    finished = Signal(bool, str)       # success, message
    error = Signal(str)                # error_message
    
    def __init__(self, operation_type, parent=None):
        """
        Args:
            operation_type: "copy", "move", "zip", "unzip" のいずれか
        """
        super().__init__(parent)
        self.operation_type = operation_type
        self._cancelled = False
        
        # 操作パラメータ（サブクラスまたはセッターで設定）
        self.src_paths = []      # コピー/移動元、またはZIP対象
        self.dest_path = ""      # コピー/移動先、またはZIPファイルパス
        self.zip_base_dir = ""   # ZIP時のベースディレクトリ
        # v23.9: 同名衝突時の方針。{src_path: "overwrite"|"skip"|"rename"}
        # UI スレッド側で事前に決めて渡す(ダイアログをワーカーから出せないため)。
        # 未指定のものは "rename" 扱い＝従来どおり連番を付けて退避する。
        self.resolutions = {}
        self._done_files = 0
        self._total_files = 0
        
    def cancel(self):
        """操作をキャンセルする"""
        self._cancelled = True
        
    def is_cancelled(self):
        """キャンセルされたかどうか"""
        return self._cancelled
    
    def run(self):
        """メイン処理（別スレッドで実行される）"""
        try:
            if self.operation_type in ("copy", "move"):
                self._run_copy_move()
            elif self.operation_type == "zip":
                self._run_zip()
            elif self.operation_type == "unzip":
                self._run_unzip()
            else:
                self.error.emit(f"Unknown operation: {self.operation_type}")
        except Exception as e:
            self.error.emit(str(e))
    
    # ----------------------------------------------------------------
    # コピー/移動
    # ----------------------------------------------------------------
    def _run_copy_move(self):
        """コピーまたは移動を実行

        v23.8: 以前は個々の失敗を stderr に print するだけで、最後に必ず
        finished(True, "N/N 件完了") を emit していた。GUI では stderr が
        誰の目にも触れないため、移動に失敗しても「完了」と表示されていた。
        失敗を集計して報告する。

        v23.9: 衝突時の方針(resolutions)を受け取れるようにし、フォルダも
        ファイル単位で進捗を出しながらコピーする(キャンセルを効かせるため)。
        """
        # --- 1) 実行計画を立てる -------------------------------------------
        plan = []        # (src, dest, action) action は "copy"/"merge"/"skip"
        skipped = []     # 元が無い / ユーザーがスキップを選んだもの
        failures = []    # (名前, 理由)

        for src in self.src_paths:
            name = os.path.basename(src)

            if not os.path.exists(src):
                skipped.append(name)
                continue

            dest = os.path.join(self.dest_path, name)

            reason = self._reject_reason(src, dest)
            if reason:
                failures.append((name, reason))
                continue

            action = self.resolutions.get(src, "rename")

            if action == "skip":
                skipped.append(name)
                continue

            if os.path.exists(dest):
                if action == "overwrite":
                    # フォルダはマージ(中身を重ねる)、ファイルは単純上書き
                    plan.append((src, dest, "merge" if os.path.isdir(src) else "copy"))
                else:
                    plan.append((src, self._resolve_conflict(dest), "copy"))
            else:
                plan.append((src, dest, "copy"))

        # --- 2) 進捗の分母をファイル単位で数える ---------------------------
        # フォルダを1件としてしまうと、巨大フォルダのコピー中に進捗が
        # 一切動かず、キャンセルも効かないように見えてしまう。
        total_files = 0
        for src, _dest, _action in plan:
            if self._cancelled:
                self.finished.emit(False, self._build_report(0, 0, failures, skipped, cancelled=True))
                return
            total_files += self._count_files(src)
        total_files = max(total_files, 1)

        # --- 3) 実行 -------------------------------------------------------
        self._done_files = 0
        self._total_files = total_files
        succeeded = 0

        for src, dest, action in plan:
            if self._cancelled:
                break

            name = os.path.basename(src)
            try:
                if os.path.isdir(src):
                    self._transfer_tree(src, dest, merge=(action == "merge"))
                else:
                    self._transfer_file(src, dest)

                if self._cancelled:
                    break
                succeeded += 1
            except Exception as e:
                failures.append((name, str(e)))
                print(f"Operation Error ({src}): {e}", file=sys.stderr)

        cancelled = self._cancelled
        message = self._build_report(succeeded, len(plan), failures, skipped, cancelled=cancelled)

        # 一部でも失敗したら成功扱いにしない。error ではなく finished(False) で
        # 返すのは、error 側のハンドラがワーカーを片付けてしまい finished 側の
        # リフレッシュが走らなくなるため(成否にかかわらず一覧は更新したい)。
        self.finished.emit(not failures and not cancelled, message)

    def _count_files(self, src):
        """進捗の分母用にファイル数を数える(フォルダは再帰)"""
        try:
            if not os.path.isdir(src):
                return 1
            count = 0
            for _root, _dirs, files in os.walk(src):
                if self._cancelled:
                    return count
                count += len(files)
            return count
        except Exception:
            return 1

    def _tick(self, name):
        """1ファイル分の進捗を進める"""
        self._done_files += 1
        self.progress.emit(self._done_files, self._total_files, name)

    def _transfer_file(self, src, dest):
        """ファイル1件をコピーまたは移動する"""
        parent = os.path.dirname(dest)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)

        if self.operation_type == "copy":
            shutil.copy2(src, dest)
        else:
            # shutil.move は移動先が既存だと失敗するため、上書き時は先に消す
            if os.path.exists(dest):
                os.remove(dest)
            shutil.move(src, dest)

        self._tick(os.path.basename(src))

    def _transfer_tree(self, src, dest, merge=False):
        """フォルダを再帰的にコピー/移動する。

        v23.9: 以前は shutil.copytree() を呼ぶだけで、進捗が動かず
        キャンセルも効かなかった。ファイル単位で回して両方を可能にする。
        merge=True のときは移動先の既存フォルダに中身を重ねる。
        """
        if not merge and os.path.exists(dest):
            dest = self._resolve_conflict(dest)

        os.makedirs(dest, exist_ok=True)

        # キャンセルで途中 return するため、with で確実にイテレータを閉じる
        with os.scandir(src) as entries:
            for entry in entries:
                if self._cancelled:
                    return
                target = os.path.join(dest, entry.name)
                if entry.is_dir(follow_symlinks=False):
                    self._transfer_tree(entry.path, target, merge=True)
                else:
                    self._transfer_file(entry.path, target)

        if self.operation_type == "move" and not self._cancelled:
            # 中身を運び終わったので空になった元フォルダを片付ける
            try:
                os.rmdir(src)
            except OSError:
                # 何か残っている(隠しファイル等)場合は消さずに残す
                pass

    def _reject_reason(self, src, dest):
        """実行前に弾くべきケースかを判定し、理由文字列を返す(問題なければ None)"""
        try:
            src_abs = os.path.normcase(os.path.abspath(src))
            dest_dir_abs = os.path.normcase(os.path.abspath(self.dest_path))
        except Exception:
            return None

        if src_abs == dest_dir_abs:
            return "移動先が自分自身です"
        if os.path.isdir(src) and (dest_dir_abs + os.sep).startswith(src_abs + os.sep):
            return "自分の内側のフォルダへは移動できません"
        if (self.operation_type == "move"
                and os.path.normcase(os.path.abspath(os.path.dirname(src))) == dest_dir_abs):
            return "移動元と移動先が同じフォルダです"
        return None

    def _build_report(self, succeeded, total, failures, skipped, cancelled=False):
        """結果メッセージを組み立てる"""
        parts = []
        if cancelled:
            parts.append("キャンセルされました")
        parts.append(f"成功 {succeeded}/{total} 件")
        if skipped:
            parts.append(f"スキップ: {len(skipped)} 件")
        if failures:
            parts.append(f"失敗 {len(failures)} 件:")
            for name, reason in failures[:10]:
                parts.append(f"  - {name}: {reason}")
            if len(failures) > 10:
                parts.append(f"  ... 他 {len(failures) - 10} 件")
        return chr(10).join(parts)

    def _resolve_conflict(self, dest):
        """同名ファイル/フォルダの衝突を回避"""
        if not os.path.exists(dest):
            return dest
        
        base, ext = os.path.splitext(dest)
        # フォルダの場合は ext が空
        if os.path.isdir(dest) or ext == "":
            base = dest
            ext = ""
        
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        return f"{base}_{counter}{ext}"
    
    # ----------------------------------------------------------------
    # ZIP圧縮
    # ----------------------------------------------------------------
    def _run_zip(self):
        """ZIP圧縮を実行"""
        # ファイルリストを先に収集（進捗計算用）
        all_files = []
        for item_path in self.src_paths:
            if os.path.isdir(item_path):
                for root, dirs, files in os.walk(item_path):
                    if self._cancelled:
                        self.finished.emit(False, "キャンセルされました")
                        return
                    for f in files:
                        all_files.append(os.path.join(root, f))
            else:
                all_files.append(item_path)
        
        total = len(all_files)
        
        try:
            with zipfile.ZipFile(self.dest_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for i, file_path in enumerate(all_files):
                    if self._cancelled:
                        self.finished.emit(False, "キャンセルされました")
                        return
                    
                    arcname = os.path.relpath(file_path, self.zip_base_dir)
                    self.progress.emit(i + 1, total, os.path.basename(file_path))
                    zf.write(file_path, arcname)
            
            self.finished.emit(True, f"圧縮完了: {os.path.basename(self.dest_path)}")
        except Exception as e:
            self.error.emit(f"ZIP圧縮エラー: {e}")
    
    # ----------------------------------------------------------------
    # ZIP解凍
    # ----------------------------------------------------------------
    def _run_unzip(self):
        """ZIP解凍を実行"""
        if not self.src_paths:
            self.error.emit("解凍対象が指定されていません")
            return
        
        zip_path = self.src_paths[0]  # 最初のファイルのみ
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                members = zf.namelist()
                total = len(members)
                
                for i, member in enumerate(members):
                    if self._cancelled:
                        self.finished.emit(False, "キャンセルされました")
                        return
                    
                    self.progress.emit(i + 1, total, member)
                    zf.extract(member, self.dest_path)
            
            self.finished.emit(True, f"解凍完了: {len(members)} ファイル")
        except Exception as e:
            self.error.emit(f"ZIP解凍エラー: {e}")
