from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QFrame, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QUrl, QThread, Signal
from PySide6.QtGui import QDesktopServices
from app.core.pdf_handler import PDFHandler
import os

class ExportWorker(QThread):
    progress = Signal(str)
    finished = Signal(int)

    def __init__(self, job_data_list, output_dir):
        super().__init__()
        self.job_data_list = job_data_list
        self.output_dir = output_dir
        self.pdf_handler = PDFHandler()

    def run(self):
        success_count = 0
        for job_data in self.job_data_list:
            filename = job_data["filename"]
            pages = job_data["pages"]
            is_active = job_data.get("active", True)
            
            if not is_active:
                self.progress.emit(f"Skipped {filename} (Not selected)")
                continue
            
            if not pages:
                self.progress.emit(f"Skipped {filename} (Empty)")
                continue
                
            output_path = os.path.join(self.output_dir, filename)
            
            self.progress.emit(f"Processing {filename} ({len(pages)} pages)...")
            
            if self.pdf_handler.save_pdf(output_path, pages):
                self.progress.emit(f"SUCCESS: Saved to {filename}")
                success_count += 1
            else:
                self.progress.emit(f"ERROR: Failed to save {filename}")
                
        self.finished.emit(success_count)

class RightPane(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window # Reference to main window to access center pane
        self.pdf_handler = PDFHandler()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Export Manager")
        # ... (style omitted for brevity, same as before) ...
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ddd;")
        self.layout.addWidget(title_label)

        # Info Box
        info_box = QFrame()
        info_box.setStyleSheet("background-color: #2b2b2b; border: 1px solid #3c3c3c; border-radius: 4px;")
        info_layout = QVBoxLayout(info_box)
        info_layout.addWidget(QLabel("Current Configuration:"))
        self.total_jobs_label = QLabel("- Total Jobs: 0")
        self.total_jobs_label.setStyleSheet("color: #aaa;")
        info_layout.addWidget(self.total_jobs_label)
        self.layout.addWidget(info_box)

        # Job List (Queue)
        self.layout.addWidget(QLabel("Export Queue:"))
        self.job_list = QListWidget()
        self.job_list.setStyleSheet("background-color: #2b2b2b; border: none; font-size: 12px;")
        self.layout.addWidget(self.job_list)

        if self.main_window:
            self.main_window.center_pane.jobs_updated.connect(self.update_job_list)

        # Handle item editing
        self.job_list.itemChanged.connect(self.on_item_changed)
        self.is_updating = False # Flag to prevent feedback loop

        self.layout.addStretch()

        # Button Layout
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(5)
        
        # Export Button
        self.export_btn = QPushButton("Process Selected Jobs")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #d35400; 
                color: white; 
                padding: 12px; 
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.export_btn.clicked.connect(self.process_all_jobs)
        btn_layout.addWidget(self.export_btn)
        
        # Open Folder Button (Initially Disabled)
        self.open_folder_btn = QPushButton("📂 Open Output Folder")
        self.open_folder_btn.setEnabled(False) # Default disabled
        self.open_folder_btn.setToolTip("Available after successful export")
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white; 
                padding: 8px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        btn_layout.addWidget(self.open_folder_btn)
        
        self.layout.addLayout(btn_layout)
        
        self.last_output_dir = None
        
        # Initial update
        if self.main_window:
            self.update_job_list()

    def update_job_list(self):
        if not self.main_window:
            return
            
        # Prevent recursion if triggered by our own update
        if hasattr(self, 'is_updating') and self.is_updating:
            return

        self.is_updating = True
        self.job_list.clear() # This triggers itemChanged for removed items? No, usually not if cleared.
        # But to be safe, we block signals during clear/rebuild
        self.job_list.blockSignals(True)
        
        rows = self.main_window.center_pane.rows
        active_count = 0
        total_pages = 0
        
        for row in rows:
            data = row.get_job_data()
            if data.get("active", True):
                active_count += 1
                page_count = len(data["pages"])
                total_pages += page_count
                
                # Format: "filename.pdf (N pages)"
                # We want just the filename to be editable? 
                # QListWidget items are editable as a whole string.
                # User will edit "filename.pdf (N pages)". We need to parse it back?
                # Better: Just display filename on the item, and put page count in tooltip or separate column?
                # QListWidget is single column.
                # Let's try to keep the format simple: "filename.pdf"
                # And maybe put page count in status or tooltip.
                
                # Check user request: "Export Queueからもファイルの名前を中央ペインと同様に変更可能に"
                # So we should just show the filename as the editable text.
                
                item_text = data['filename']
                item = QListWidgetItem(item_text)
                
                # Enable editing
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                
                # Store reference to TimelineRow to callback
                item.setData(Qt.UserRole, row)
                
                item.setToolTip(f"Pages: {page_count}\nDouble click to rename")
                
                self.job_list.addItem(item)
        
        self.total_jobs_label.setText(f"- Total Jobs: {active_count}\n- Total Pages: {total_pages}")
        
        if active_count == 0:
             no_item = QListWidgetItem("No active jobs selected.")
             # No editable flag
             self.job_list.addItem(no_item)
             
        self.job_list.blockSignals(False)
        self.is_updating = False

    def on_item_changed(self, item):
        """Handle filename editing in the list."""
        if self.is_updating:
            return
            
        row = item.data(Qt.UserRole)
        if hasattr(row, 'filename_input'):
            new_filename = item.text().strip()
            
            # Basic validation
            if not new_filename:
                # Revert? Hard to revert without old data.
                # Just ignore or set default
                return
                
            if not new_filename.endswith(".pdf"):
                new_filename += ".pdf"
                # Update list item to reflect extension addition immediately?
                # self.job_list.blockSignals(True)
                # item.setText(new_filename)
                # self.job_list.blockSignals(False)
            
            # Update the TimelineRow
            # This triggers 'textChanged' -> 'emit_state_change' -> 'jobs_updated'
            # -> 'update_job_list' 
            # So we set is_updating = True to prevent list rebuild while we are the source?
            # Actually, we WANT to update the list if the row normalizes the name,
            # but we experienced that rebuild kills focus.
            # However, on_item_changed happens AFTER editing is done.
            # So focus loss is acceptable.
            
            self.is_updating = True # Block immediate echo back to prevent loop
            row.filename_input.setText(new_filename)
            self.is_updating = False
            
            # But wait, setting text on row triggers state_change signal, 
            # which calls update_job_list in RightPane.
            # If we don't set is_updating=True, update_job_list will run, 
            # clearing the list and re-adding items. 
            # This is fine since the user finished editing.
            # BUT, we just set is_updating=False above.
            # So the loop WILL happen: 
            # RightPane sets Row -> Row signals Main -> Main signals RightPane -> RightPane rebuilds.
            # Ideally we want this to update page counts or other info if checks changed, 
            # so a rebuild is okay ensuring consistency.

    def process_all_jobs(self):
        if not self.main_window:
            return
 
        # Get rows from center pane
        center_pane = self.main_window.center_pane
        rows = center_pane.rows
        
        if not rows:
            QMessageBox.warning(self, "No Jobs", "Please add at least one job track.")
            return

        # Select Output Directory
        dialog = QFileDialog(self, "Select Output Directory", "")
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        
        # Apply dark title bar
        try:
            from app.ui.utils import apply_dark_title_bar
            apply_dark_title_bar(dialog)
        except Exception as e:
            print(f"Failed to apply dark title bar to dialog: {e}")
            
        if dialog.exec() == QFileDialog.Accepted:
            output_dir = dialog.selectedFiles()[0]
        else:
            return
            
        self.last_output_dir = output_dir

        self.job_list.clear()
        self.log(f"Started processing {len(rows)} jobs...")
        
        self.export_btn.setEnabled(False)
        self.export_btn.setText("Processing...")
        
        job_data_list = [row.get_job_data() for row in rows]
        
        self.worker = ExportWorker(job_data_list, output_dir)
        self.worker.progress.connect(self.log)
        self.worker.finished.connect(self._on_export_finished)
        self.worker.start()

    def _on_export_finished(self, success_count):
        self.export_btn.setEnabled(True)
        self.export_btn.setText("Process Selected Jobs")
        
        # Enable Open Folder button and update tooltip
        self.open_folder_btn.setEnabled(True)
        self.open_folder_btn.setToolTip(f"Open: {self.last_output_dir}")
        
        total_jobs = len(self.worker.job_data_list)
        QMessageBox.information(self, "Export Complete", f"Processed {total_jobs} jobs.\nSuccessful: {success_count}")

    def open_output_folder(self):
        if self.last_output_dir and os.path.exists(self.last_output_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_output_dir))

    def log(self, message):
        self.job_list.addItem(message)
        self.job_list.scrollToBottom()
