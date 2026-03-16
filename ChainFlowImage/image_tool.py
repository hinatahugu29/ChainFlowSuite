import sys
import os
import argparse
from PIL import Image
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QListWidget, QPushButton, QLabel, QComboBox, QSpinBox, 
                               QProgressBar, QFileDialog, QMessageBox, QGroupBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, QThread, Signal, QEvent

def apply_dark_title_bar(window):
    """v21.1: Forces Windows dark title bar"""
    try:
        import ctypes
        hwnd = window.winId()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(hwnd),
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
    except:
        pass
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent

class Worker(QThread):
    progress = Signal(int, int) # current, total
    finished = Signal()
    log = Signal(str)

    def __init__(self, files, config):
        super().__init__()
        self.files = files
        self.config = config
        self._is_running = True

    def get_unique_path(self, path):
        if not os.path.exists(path):
            return path
        
        base, ext = os.path.splitext(path)
        counter = 1
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def run(self):
        import concurrent.futures
        
        total = len(self.files)
        completed_count = 0
        
        # Use simple CPU count or limit
        max_workers = os.cpu_count() or 4
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map futures to file paths
            future_to_file = {executor.submit(self.process_single_file, path): path for path in self.files}
            
            for future in concurrent.futures.as_completed(future_to_file):
                path = future_to_file[future]
                if not self._is_running:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                try:
                    future.result() # Will raise exception if occurred in thread
                except Exception as e:
                    self.log.emit(f"Error processing {os.path.basename(path)}: {e}")
                
                completed_count += 1
                self.progress.emit(completed_count, total)
        
        self.finished.emit()

    def process_single_file(self, path):
        """Thread-safe file processing"""
        if not self._is_running: return

        try:
            img = Image.open(path)
            
            # Resize
            if self.config['resize_mode'] == 'width':
                w = self.config['resize_value']
                if img.width > w:
                    ratio = w / img.width
                    h = int(img.height * ratio)
                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                    self.log.emit(f"Resized {os.path.basename(path)} to {w}x{h}")
            elif self.config['resize_mode'] == 'percent':
                p = self.config['resize_value'] / 100.0
                if p != 1.0:
                    w = int(img.width * p)
                    h = int(img.height * p)
                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                    self.log.emit(f"Resized {os.path.basename(path)} by {self.config['resize_value']}%")

            # Convert / Save
            fmt = self.config['format'].lower()
            if fmt == 'original':
                fmt = os.path.splitext(path)[1][1:].lower()
                if fmt == 'jpg': fmt = 'jpeg'
            
            # Save path (add suffix or new folder?)
            # Strategy: Create 'processed' folder in same dir
            d = os.path.dirname(path)
            out_dir = os.path.join(d, "processed")
            os.makedirs(out_dir, exist_ok=True)
            
            
            fname = os.path.splitext(os.path.basename(path))[0]
            base_out = os.path.join(out_dir, f"{fname}.{fmt.replace('jpeg','jpg')}")
            # Ensure unique path invocation is thread-safe or atomic enough
            # get_unique_path checks file existence. Race condition possible if same filename processed 
            # in parallel, but inputs are distinct files, so output filenames in 'processed' 
            # shouldn't collide unless source files map to same output name (unlikely).
            out_path = self.get_unique_path(base_out)
            
            # Format specific options
            save_args = {}
            if fmt in ['jpeg', 'jpg']:
                save_args['quality'] = 85
            
            if img.mode in ('RGBA', 'LA') and fmt in ['jpeg', 'jpg']:
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background

            img.save(out_path, format=fmt.upper(), **save_args)
            self.log.emit(f"Saved: {out_path}")
            
        except Exception as e:
            # Re-raise to be caught in main loop
            raise e

    def stop(self):
        self._is_running = False

class ImageTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChainFlow Image Tool")
        self.setWindowTitle("ChainFlow Image Tool")
        
        # --- Icon Settings ---
        icon_path = ""
        if getattr(sys, 'frozen', False):
            # sys._MEIPASS logic for PyInstaller
            bundle_dir = sys._MEIPASS
            icon_path = os.path.join(bundle_dir, "app_icon.ico")
        else:
            # Local dev path
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # ---------------------
        
        self.resize(800, 600)
        self.setAcceptDrops(True)
        self.apply_theme()
        
        self.files = []
        
        # UI
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header
        header = QLabel("ChainFlow Image Tool")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #fff; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Main Area (List | Controls)
        h_layout = QHBoxLayout()
        
        # File List
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        h_layout.addWidget(self.file_list, stretch=2)
        
        # Controls
        controls = QWidget()
        controls.setFixedWidth(250)
        c_layout = QVBoxLayout(controls)
        c_layout.setAlignment(Qt.AlignTop)
        
        # 1. Format
        gb_fmt = QGroupBox("Output Format")
        gb_fmt_l = QVBoxLayout()
        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["Original", "JPG", "PNG", "WEBP"])
        gb_fmt_l.addWidget(self.combo_fmt)
        gb_fmt.setLayout(gb_fmt_l)
        c_layout.addWidget(gb_fmt)
        
        # 2. Resize
        gb_res = QGroupBox("Resize")
        gb_res_l = QVBoxLayout()
        
        self.rb_none = QRadioButton("No Resize")
        self.rb_none.setChecked(True)
        self.rb_width = QRadioButton("Fix Width (px)")
        self.rb_pct = QRadioButton("Scale (%)")
        
        self.bg_res = QButtonGroup()
        self.bg_res.addButton(self.rb_none)
        self.bg_res.addButton(self.rb_width)
        self.bg_res.addButton(self.rb_pct)
        
        gb_res_l.addWidget(self.rb_none)
        
        row_w = QHBoxLayout()
        row_w.addWidget(self.rb_width)
        self.spin_width = QSpinBox()
        self.spin_width.setRange(100, 8000)
        self.spin_width.setValue(1200)
        self.spin_width.setEnabled(False)
        row_w.addWidget(self.spin_width)
        gb_res_l.addLayout(row_w)
        
        row_p = QHBoxLayout()
        row_p.addWidget(self.rb_pct)
        self.spin_pct = QSpinBox()
        self.spin_pct.setRange(10, 200)
        self.spin_pct.setValue(50)
        self.spin_pct.setEnabled(False)
        row_p.addWidget(self.spin_pct)
        gb_res_l.addLayout(row_p)
        
        gb_res.setLayout(gb_res_l)
        c_layout.addWidget(gb_res)
        
        # Signals for enable/disable
        self.bg_res.buttonClicked.connect(self.update_ui_state)
        
        c_layout.addStretch()
        
        # Actions
        self.btn_run = QPushButton("Process Images")
        self.btn_run.setFixedHeight(40)
        self.btn_run.setStyleSheet("background-color: #007acc; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_run.clicked.connect(self.run_process)
        c_layout.addWidget(self.btn_run)
        
        self.btn_clear = QPushButton("Clear List")
        self.btn_clear.clicked.connect(self.clear_list)
        c_layout.addWidget(self.btn_clear)

        h_layout.addWidget(controls)
        layout.addLayout(h_layout)
        
        # Log / Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready. Drag files here.")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
        
        # Initial args
        self.parse_args()

    def update_ui_state(self):
        self.spin_width.setEnabled(self.rb_width.isChecked())
        self.spin_pct.setEnabled(self.rb_pct.isChecked())

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--files", nargs="+", help="Input files")
        # Filer passes files as arguments, possibly multiple if supported by launcher
        # But currently, plugin_manager might pass one by one if not 'AllowMultiple'?
        # Actually our current mechanism supports list of files? 
        # The tools.json arguments usually specify how to pass.
        # If we define arguments: ["{FILES}"] (plural), we need support in PluginManager.
        # For now, let's assume it might receive one file or we handle sys.argv direct.
        
        # Simple hack: treat all non-flag args as files
        for arg in sys.argv[1:]:
            if not arg.startswith("-") and os.path.exists(arg):
                self.add_file(arg)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path): # Directory handling could be added
                self.add_file(path)

    def add_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.gif']:
            if path not in self.files:
                self.files.append(path)
                self.file_list.addItem(path)
                self.status_label.setText(f"{len(self.files)} files ready.")

    def clear_list(self):
        self.files.clear()
        self.file_list.clear()
        self.status_label.setText("List cleared.")

    def run_process(self):
        if not self.files:
            return
        
        config = {
            'format': self.combo_fmt.currentText(),
            'resize_mode': 'none',
            'resize_value': 0
        }
        
        if self.rb_width.isChecked():
            config['resize_mode'] = 'width'
            config['resize_value'] = self.spin_width.value()
        elif self.rb_pct.isChecked():
            config['resize_mode'] = 'percent'
            config['resize_value'] = self.spin_pct.value()
            
        self.worker = Worker(self.files, config)
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.log_message)
        self.worker.finished.connect(self.on_finished)
        
        self.btn_run.setEnabled(False)
        self.progress_bar.setRange(0, len(self.files))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        self.worker.start()

    def update_progress(self, current, total):
        self.progress_bar.setValue(current)

    def log_message(self, msg):
        self.status_label.setText(msg)
        print(msg)

    def on_finished(self):
        self.btn_run.setEnabled(True)
        self.progress_bar.hide()
        QMessageBox.information(self, "Done", f"Processed {len(self.files)} images.")
        self.status_label.setText("Finished.")
        self.files.clear()
        self.file_list.clear()

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #252526; color: #ccc; }
            QListWidget { background-color: #1e1e1e; color: #ccc; border: 1px solid #333; }
            QGroupBox { border: 1px solid #444; margin-top: 10px; padding-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }
            QLabel { color: #ccc; }
            QPushButton { background-color: #333; color: #ccc; border: 1px solid #555; padding: 5px; }
            QPushButton:hover { background-color: #444; }
            QSpinBox, QComboBox { background-color: #333; color: #ccc; border: 1px solid #555; padding: 3px; }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)

    def changeEvent(self, event):
        # v21.1: Re-apply dark title bar on state changes to prevent theme breakage
        if event.type() in [QEvent.WindowStateChange, QEvent.ActivationChange]:
            apply_dark_title_bar(self)
        super().changeEvent(event)

if __name__ == "__main__":
    # Windows Taskbar Icon Fix
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChainFlow.ImageTool.v21")
    except ImportError:
        pass

    app = QApplication(sys.argv)
    
    window = ImageTool()
    window.show()
    sys.exit(app.exec())
