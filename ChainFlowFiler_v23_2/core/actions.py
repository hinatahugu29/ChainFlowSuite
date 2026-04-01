"""
v23.2: Refactoring: FilePane から抽出されたアクションサービス
ファイル操作（PDF変換、ZIP、新規作成など）のロジックを集約。
"""
import os
import shutil
import subprocess
import json
from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit, QApplication, QProgressDialog
from PySide6.QtCore import Qt, QTimer, QUrl, QMimeData
from PySide6.QtGui import QDesktopServices

from core import FileOperationWorker, logger, same_path

class FileActions:
    """FilePane から呼び出される静的アクション群"""

    @staticmethod
    def execute_path(pane, path):
        """ファイルをOS標準アプリで開く。Windows 'start' と QDesktopServices の併用"""
        if not path or not os.path.exists(path):
            return
        
        if os.name == 'nt':
            try:
                # v23.2: Popen used for non-blocking start in Windows
                cwd = os.path.dirname(path) if os.path.isdir(os.path.dirname(path)) else None
                import subprocess
                subprocess.Popen(f'start "" "{path}"', shell=True, cwd=cwd)
            except Exception as e:
                # Fallback to QDesktopServices
                from PySide6.QtGui import QDesktopServices
                import PySide6.QtCore as QtCore
                QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        else:
            from PySide6.QtGui import QDesktopServices
            import PySide6.QtCore as QtCore
            QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))

    @staticmethod
    def action_terminal(pane, paths):
        """ターミナルを開く"""
        target_dir = paths[0] if paths and os.path.isdir(paths[0]) else os.path.dirname(paths[0]) if paths else pane.current_paths[0]
        if os.path.exists(target_dir):
            subprocess.Popen(f'start cmd /k "cd /d {target_dir}"', shell=True)

    @staticmethod
    def action_convert_to_pdf(pane, paths):
        """PDF変換 (MS Office 連携)"""
        if not paths: return
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            office_success_paths = []
            import win32com.client
            import pythoncom
            pythoncom.CoInitialize()
            
            word_app = None
            excel_app = None
            
            for path in paths:
                abs_path = os.path.abspath(path)
                ext = os.path.splitext(abs_path)[1].lower()
                pdf_path = os.path.splitext(abs_path)[0] + ".pdf"
                
                # 同名回避
                if os.path.exists(pdf_path):
                    base, _ = os.path.splitext(pdf_path)
                    c = 1
                    while os.path.exists(f"{base}_{c}.pdf"):
                        c += 1
                    pdf_path = f"{base}_{c}.pdf"

                try:
                    if ext in ('.docx', '.doc'):
                        if not word_app:
                            word_app = win32com.client.Dispatch("Word.Application")
                            word_app.Visible = False
                        doc = word_app.Documents.Open(abs_path)
                        doc.ExportAsFixedFormat(pdf_path, 17) # wdExportFormatPDF = 17
                        doc.Close(False)
                        office_success_paths.append(path)
                    elif ext in ('.xlsx', '.xls'):
                        if not excel_app:
                            excel_app = win32com.client.Dispatch("Excel.Application")
                            excel_app.Visible = False
                            excel_app.DisplayAlerts = False
                        wb = excel_app.Workbooks.Open(abs_path)
                        wb.ExportAsFixedFormat(0, pdf_path) # xlTypePDF = 0
                        wb.Close(False)
                        office_success_paths.append(path)
                except Exception as e:
                    logger.log_error(f"MS Office Error for {path}: {e}")
            
            # マーク解除の依頼
            if hasattr(pane, 'action_mark_selected'):
                pane.action_mark_selected(office_success_paths, mark=False)

            QMessageBox.information(pane, "PDF Conversion", f"Converted {len(office_success_paths)} files to PDF.\nSaved in the same directory.")
                
        except Exception as e:
            logger.log_error(f"MS Office Dispatch failed or not installed: {e}")
        finally:
            if 'word_app' in locals() and word_app: word_app.Quit()
            if 'excel_app' in locals() and excel_app: excel_app.Quit()
            QApplication.restoreOverrideCursor()

    @staticmethod
    def action_zip(pane, selection):
        """ZIP圧縮を実行 (非同期)"""
        paths = selection["paths"]
        if not paths: return
        
        base_name = os.path.basename(paths[0])
        if len(paths) > 1: base_name = os.path.basename(os.path.dirname(paths[0])) or "Archive"
        if not os.path.isdir(paths[0]) or len(paths) > 1:
             base_name = os.path.splitext(base_name)[0]
        
        default_zip = f"{base_name}.zip"
        zip_name, ok = QInputDialog.getText(pane, "圧縮", "ZIPファイル名:", text=default_zip)
        if ok and zip_name:
            parent_dir = os.path.dirname(paths[0])
            target_zip = os.path.join(parent_dir, zip_name)
            
            worker = FileOperationWorker("zip", pane)
            worker.src_paths = paths
            worker.dest_path = target_zip
            worker.zip_base_dir = parent_dir
            
            progress = QProgressDialog("圧縮中...", "キャンセル", 0, 100, pane)
            progress.setWindowTitle("ZIP圧縮")
            progress.setWindowModality(Qt.WindowModal)
            
            worker.progress.connect(lambda current, total, name: progress.setValue(current))
            worker.progress.connect(lambda current, total, name: progress.setMaximum(total))
            worker.progress.connect(lambda current, total, name: progress.setLabelText(f"圧縮中: {name}"))
            
            def on_finished(success, message):
                progress.close()
                if success: pane.refresh_contents()
            
            worker.finished.connect(on_finished)
            worker.error.connect(lambda msg: QMessageBox.critical(pane, "エラー", msg))
            progress.canceled.connect(worker.cancel)
            worker.start()
            # 参照を維持するためにpaneに持たせる（または別の場所で管理）
            pane._current_worker = worker 

    @staticmethod
    def action_unzip(pane, selection):
        """ZIP解凍を実行 (非同期)"""
        for item in selection["full_infos"]:
            p, is_d = item["path"], item["is_dir"]
            if not is_d and p.lower().endswith('.zip'):
                out_dir = os.path.splitext(p)[0]
                base_out = out_dir
                c = 1
                while os.path.exists(out_dir):
                    out_dir = f"{base_out}_{c}"
                    c += 1
                os.makedirs(out_dir, exist_ok=True)
                
                worker = FileOperationWorker("unzip", pane)
                worker.src_paths = [p]
                worker.dest_path = out_dir
                
                progress = QProgressDialog("解凍中...", "キャンセル", 0, 100, pane)
                progress.setWindowTitle("ZIP解凍")
                progress.setWindowModality(Qt.WindowModal)
                
                worker.progress.connect(lambda current, total, name: progress.setValue(current))
                worker.progress.connect(lambda current, total, name: progress.setMaximum(total))
                worker.progress.connect(lambda current, total, name: progress.setLabelText(f"解凍中: {name}"))
                
                def on_finished(success, message):
                    progress.close()
                    if success: pane.refresh_contents()
                
                worker.finished.connect(on_finished)
                worker.error.connect(lambda msg: QMessageBox.critical(pane, "エラー", msg))
                progress.canceled.connect(worker.cancel)
                worker.start()
                pane._current_worker = worker
                break

    @staticmethod
    def action_new_file(pane, view=None, proxy=None):
        """新規ファイル作成"""
        if view is None or proxy is None:
            info = pane.get_selection_info()
            view, proxy = info["view"], info["proxy"]
        if not view or not proxy: return

        current_dir = proxy.root_path
        if not current_dir or not os.path.exists(current_dir): return

        default_name = "NewFile.txt"
        text, ok = QInputDialog.getText(pane, "New File", "Filename:", QLineEdit.Normal, default_name)
        if ok and text:
            file_path = os.path.join(current_dir, text)
            if os.path.exists(file_path):
                QMessageBox.warning(pane, "Error", "File already exists!")
                return
            try:
                with open(file_path, 'w', encoding='utf-8') as f: pass
                pane.refresh_contents()
                QTimer.singleShot(100, lambda: pane._select_and_edit_created_file(file_path))
            except Exception as e:
                QMessageBox.critical(pane, "Error", f"Failed to create file:\n{e}")

    @staticmethod
    def action_new_folder(pane, view=None, proxy=None):
        """新規フォルダ作成"""
        if view is None or proxy is None:
            info = pane.get_selection_info()
            view, proxy = info["view"], info["proxy"]
        if not view or not proxy: return

        current_dir = proxy.root_path
        if not current_dir or not os.path.exists(current_dir): return

        default_name = "NewFolder"
        text, ok = QInputDialog.getText(pane, "New Folder", "Folder Name:", QLineEdit.Normal, default_name)
        if ok and text:
            folder_path = os.path.join(current_dir, text)
            if os.path.exists(folder_path):
                QMessageBox.warning(pane, "Error", "Folder already exists!")
                return
            try:
                os.makedirs(folder_path, exist_ok=True)
                pane.refresh_contents()
                QTimer.singleShot(150, lambda: pane._select_and_edit_created_file(folder_path))
            except Exception as e:
                QMessageBox.critical(pane, "Error", f"Failed to create folder:\n{e}")

    @staticmethod
    def action_delete(pane):
        """削除を実行"""
        info = pane.get_selection_info()
        paths = info["paths"]
        if paths:
            ret = QMessageBox.question(pane, "Delete", f"Are you sure you want to delete {len(paths)} items?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                for item in info["full_infos"]:
                    try:
                        p = item["path"]
                        if os.path.isdir(p): shutil.rmtree(p)
                        else: os.remove(p)
                    except Exception as e:
                        logger.log_error(f"Delete Error for {p}: {e}")
                pane.refresh_contents()
