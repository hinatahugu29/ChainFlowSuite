import sys
import os
import subprocess
import json
import sqlite3
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                               QFileDialog, QTextEdit, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon

class SyncWorker(QThread):
    progress = Signal(str)
    total_found = Signal(int)
    current_count = Signal(int)
    diff_ready = Signal(list)
    finished = Signal()
    
    def __init__(self, mode, src, dst, engine_path, plan=None):
        super().__init__()
        self.mode = mode
        self.src = src
        self.dst = dst
        self.engine_path = engine_path
        self.plan = plan
        
    def stream_process(self, cmd_args):
        # Explicitly set stderr=subprocess.STDOUT to capture Rust errors into the progress log
        process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8')
        last_json = None
        for line in iter(process.stdout.readline, ''):
            clean_line = line.strip()
            if not clean_line: continue
            
            if clean_line.startswith("PROGRESS:TOTAL:"):
                try:
                    total = int(clean_line.split(":")[-1])
                    self.total_found.emit(total)
                except: pass
            elif clean_line.startswith("PROGRESS:SCANNED:"):
                try:
                    count = int(clean_line.split(":")[-1])
                    self.current_count.emit(count)
                except: pass
            elif (clean_line.startswith("{") and clean_line.endswith("}")) or \
                 (clean_line.startswith("[") and clean_line.endswith("]")):
                last_json = clean_line
            else:
                # Capture all other output (including Rust Panics or Syncing: path)
                self.progress.emit(clean_line)
        
        process.wait()
        return last_json, process.returncode

    def run(self):
        try:
            DB_NAME = ".cfs_index.db"
            if self.mode == 'analyze':
                self.progress.emit(f"Scanning Source: {self.src}")
                src_db = os.path.join(self.src, DB_NAME)
                self.stream_process([self.engine_path, "scan", self.src, src_db])
                
                self.progress.emit(f"Scanning Destination: {self.dst}")
                dst_db = os.path.join(self.dst, DB_NAME)
                self.stream_process([self.engine_path, "scan", self.dst, dst_db])
                
                self.progress.emit("Analyzing differences...")
                res_json, code = self.stream_process([self.engine_path, "diff", src_db, dst_db])
                if code == 0 and res_json:
                    actions = json.loads(res_json)
                    self.diff_ready.emit(actions)
                else:
                    self.progress.emit(f"Analysis Failed with code {code}")
            
            elif self.mode == 'scan_source':
                self.progress.emit(f"Indexing Source: {self.src}")
                db_path = os.path.join(self.src, DB_NAME)
                self.stream_process([self.engine_path, "scan", self.src, db_path])
                self.progress.emit("Source index updated.")

            elif self.mode == 'scan_target':
                self.progress.emit(f"Indexing Target: {self.dst}")
                db_path = os.path.join(self.dst, DB_NAME)
                self.stream_process([self.engine_path, "scan", self.dst, db_path])
                self.progress.emit("Target index updated.")

            elif self.mode == 'apply':
                self.progress.emit("Starting Synchronization...")
                cwd = os.getcwd()
                if getattr(sys, 'frozen', False): cwd = os.path.dirname(sys.executable)
                plan_file = os.path.join(cwd, "sync_plan.json")
                with open(plan_file, "w") as f:
                    json.dump(self.plan, f)
                
                res_json, code = self.stream_process([self.engine_path, "apply", plan_file, self.src, self.dst])
                if code != 0:
                    self.progress.emit(f"Sync process FAILED with code {code}.")
                else:
                    self.progress.emit("Sync process completed successfully.")

        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
        self.finished.emit()

class ChainFlowSync(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChainFlow Sync v0.1")
        self.resize(800, 600)
        
        icon_path = ""
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
            icon_path = os.path.join(base_dir, "app_icon.ico")
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_dir, "app_icon.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.current_plan = None
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header / Status
        status_row = QHBoxLayout()
        status_label = QLabel("🛡️ Safe Sync Mode: Add/Update Only (No Deletions)")
        status_label.setStyleSheet("color: #238636; font-weight: bold; padding: 5px;")
        status_row.addWidget(status_label)
        layout.addLayout(status_row)

        for label, edit_name, mode in [("Source:", "src_edit", "scan_source"), 
                                        ("Target:", "dst_edit", "scan_target")]:
            row_v = QVBoxLayout()
            row_h = QHBoxLayout()
            row_h.addWidget(QLabel(label))
            edit = QLineEdit()
            edit.setPlaceholderText("Select folder...")
            edit.textChanged.connect(self.update_indexed_counts)
            setattr(self, edit_name, edit)
            row_h.addWidget(edit)
            
            browse = QPushButton("Browse")
            browse.clicked.connect(lambda checked, e=edit: self.browse_folder(e))
            row_h.addWidget(browse)
            
            idx_btn = QPushButton("Index")
            idx_btn.clicked.connect(lambda checked, m=mode: self.start_indexing(m))
            row_h.addWidget(idx_btn)
            row_v.addLayout(row_h)
            
            count_label = QLabel("Indexed: No data")
            count_label.setStyleSheet("color: #58a6ff; font-size: 10px; margin-left: 65px;")
            setattr(self, f"{edit_name}_count", count_label)
            row_v.addWidget(count_label)
            
            layout.addLayout(row_v)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Start Analysis")
        self.analyze_btn.setFixedHeight(40)
        self.analyze_btn.clicked.connect(self.start_analysis)
        
        self.sync_btn = QPushButton("Execute Sync")
        self.sync_btn.setFixedHeight(40)
        self.sync_btn.setEnabled(False)
        self.sync_btn.setStyleSheet("background-color: #238636; color: white; font-weight: bold;")
        self.sync_btn.clicked.connect(self.start_sync_execution)
        
        btn_layout.addWidget(self.analyze_btn)
        btn_layout.addWidget(self.sync_btn)
        layout.addLayout(btn_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        
        self.setup_styles()
        self.update_indexed_counts()

    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; color: #c9d1d9; }
            QLabel { color: #8b949e; width: 60px; }
            QLineEdit { background-color: #0d1117; color: #fff; border: 1px solid #30363d; padding: 5px; border-radius: 4px; }
            QPushButton { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 5px 15px; border-radius: 6px; }
            QPushButton:hover { background-color: #30363d; border-color: #8b949e; }
            QTextEdit { background-color: #0d1117; color: #79c0ff; font-family: 'Consolas', monospace; border: 1px solid #30363d; }
            QProgressBar { border: 1px solid #30363d; border-radius: 4px; text-align: center; height: 16px; font-weight: bold; }
            QProgressBar::chunk { background-color: #238636; }
        """)

    def update_indexed_counts(self):
        for edit_name in ["src_edit", "dst_edit"]:
            edit_widget = getattr(self, edit_name)
            path = edit_widget.text()
            label = getattr(self, f"{edit_name}_count")
            if not path or not os.path.isdir(path):
                label.setText("Indexed: No data")
                continue
            
            db_path = os.path.join(path, ".cfs_index.db")
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM files")
                    count = cursor.fetchone()[0]
                    label.setText(f"Indexed: {count:,} items")
                    conn.close()
                except:
                    label.setText("Indexed: DB Error")
            else:
                label.setText("Indexed: Not indexed")

    def browse_folder(self, edit_widget):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path: edit_widget.setText(path)

    def get_engine_path(self):
        exe_name = "sync-engine.exe"
        if getattr(sys, 'frozen', False):
            p = os.path.join(sys._MEIPASS, exe_name)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            p = os.path.join(base_dir, "engine", "target", "release", exe_name)
            if not os.path.exists(p):
                p = os.path.join(base_dir, "engine", "target", "debug", exe_name)
        return p

    def start_indexing(self, mode):
        path = self.src_edit.text() if 'source' in mode else self.dst_edit.text()
        if not path or not os.path.isdir(path): return
        engine = self.get_engine_path()
        self.analyze_btn.setEnabled(False)
        self.sync_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.worker = SyncWorker(mode, self.src_edit.text(), self.dst_edit.text(), engine)
        self.worker.progress.connect(self.log_view.append)
        self.worker.total_found.connect(lambda t: self.progress_bar.setRange(0, t))
        self.worker.current_count.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def start_analysis(self):
        src, dst = self.src_edit.text(), self.dst_edit.text()
        if not src or not dst: return
        engine = self.get_engine_path()
        self.analyze_btn.setEnabled(False)
        self.sync_btn.setEnabled(False)
        self.log_view.clear()
        self.progress_bar.setRange(0, 0) 
        self.worker = SyncWorker('analyze', src, dst, engine)
        self.worker.progress.connect(self.log_view.append)
        self.worker.total_found.connect(lambda t: self.progress_bar.setRange(0, t))
        self.worker.current_count.connect(self.progress_bar.setValue)
        self.worker.diff_ready.connect(self.handle_diff)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def handle_diff(self, actions):
        self.current_plan = actions
        stats = {"Create": 0, "Update": 0, "NoChange": 0}
        for act in actions:
            t = act.get("type", "NoChange")
            if t in stats: stats[t] += 1
        
        res = f"--- Analysis Result (Safe Mode) ---\nNew: {stats.get('Create',0)} | Changed: {stats.get('Update',0)} | Skip: {stats.get('NoChange',0)}\n"
        self.log_view.append(res)
        if any(stats.get(k,0) > 0 for k in ["Create", "Update"]):
            self.sync_btn.setEnabled(True)

    def start_sync_execution(self):
        if not self.current_plan: return
        if QMessageBox.question(self, "Confirm", "Execute Safe Sync (Add/Update Only)?") == QMessageBox.No: return
        self.analyze_btn.setEnabled(False)
        self.sync_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.worker = SyncWorker('apply', self.src_edit.text(), self.dst_edit.text(), self.get_engine_path(), self.current_plan)
        self.worker.progress.connect(self.log_view.append)
        self.worker.total_found.connect(lambda t: self.progress_bar.setRange(0, t))
        self.worker.current_count.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self):
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.update_indexed_counts()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChainFlowSync()
    window.show()
    sys.exit(app.exec())
