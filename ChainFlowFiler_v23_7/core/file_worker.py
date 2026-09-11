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
        """コピーまたは移動を実行"""
        total = len(self.src_paths)
        completed = 0
        
        for src in self.src_paths:
            if self._cancelled:
                self.finished.emit(False, "キャンセルされました")
                return
            
            if not os.path.exists(src):
                completed += 1
                continue
            
            name = os.path.basename(src)
            dest = os.path.join(self.dest_path, name)
            
            # 同名衝突回避
            dest = self._resolve_conflict(dest)
            
            self.progress.emit(completed, total, name)
            
            try:
                if self.operation_type == "copy":
                    if os.path.isdir(src):
                        self._copy_tree_with_progress(src, dest, completed, total)
                    else:
                        shutil.copy2(src, dest)
                else:  # move
                    shutil.move(src, dest)
            except Exception as e:
                print(f"Operation Error ({src}): {e}", file=sys.stderr)
            
            completed += 1
            self.progress.emit(completed, total, name)
        
        self.finished.emit(True, f"{completed}/{total} 件完了")
    
    def _copy_tree_with_progress(self, src, dest, base_completed, total):
        """フォルダを再帰的にコピー（進捗更新付き）"""
        # shutil.copytree はブロッキングなのでそのまま使用
        # より細かい進捗が必要な場合は手動実装に変更可能
        shutil.copytree(src, dest)
    
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
