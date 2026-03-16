import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, 
                               QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QScrollArea,
                               QPushButton, QHBoxLayout, QFileDialog, QCheckBox, QLineEdit)
from PySide6.QtCore import Qt, Signal

class PropertyPane(QWidget):
    margins_changed = Signal(int, int, int, int)
    typography_changed = Signal(str, float, int, bool, str)
    page_size_changed = Signal(str, str)
    export_pdf_requested = Signal(str) # Emits file path to save PDF
    page_decor_changed = Signal(dict) # Emits dict of header/footer/page_num settings
    guides_toggled = Signal(bool) # Emits True/False for page break guides
    refresh_requested = Signal() # Emits when the user wants to force reload the preview
    
    def __init__(self):
        super().__init__()
        self.last_dir = "" # Store the directory to use as default for export
        self.setup_ui()
        self._connect_signals()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QLabel("PROPERTIES & EXPORT")
        header.setStyleSheet("background-color: #2D2D30; color: #8F8F8F; padding: 8px; font-weight: bold; font-size: 11px;")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #252526; }")
        
        content = QWidget()
        content.setStyleSheet("""
            QWidget { background-color: #252526; color: #CCCCCC; font-size: 12px; }
            QGroupBox { font-weight: bold; border: 1px solid #3E3E42; margin-top: 15px; padding-top: 15px; border-radius: 4px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #4BBAFF; }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #3C3C3C; 
                border: 1px solid #555555; 
                padding: 4px; 
                border-radius: 2px; 
                color: #FFFFFF;
                min-width: 60px;
                min-height: 24px;
            }
            QComboBox { padding-left: 8px; }
            QComboBox::drop-down { border: none; }
            QPushButton {
                background-color: #0E639C; color: white; border: none; padding: 8px; border-radius: 3px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1177BB; }
        """)
        
        form_layout = QVBoxLayout(content)
        form_layout.setContentsMargins(15, 10, 15, 15)
        form_layout.setSpacing(20)
        
        # 1. Document Settings
        doc_group = QGroupBox("Document")
        doc_form = QFormLayout(doc_group)
        self.size_combo = QComboBox()
        self.size_combo.addItems(["A4 (210x297mm)", "B5 (182x257mm)", "Letter"])
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["Portrait", "Landscape"])
        doc_form.addRow("Paper Size:", self.size_combo)
        doc_form.addRow("Orientation:", self.orientation_combo)
        
        # 2. Margins
        margin_group = QGroupBox("Margins (mm)")
        margin_form = QFormLayout(margin_group)
        self.top_margin = QSpinBox()
        self.top_margin.setValue(25)
        self.bottom_margin = QSpinBox()
        self.bottom_margin.setValue(25)
        self.left_margin = QSpinBox()
        self.left_margin.setValue(25)
        self.right_margin = QSpinBox()
        self.right_margin.setValue(25)
        margin_form.addRow("Top:", self.top_margin)
        margin_form.addRow("Bottom:", self.bottom_margin)
        margin_form.addRow("Left:", self.left_margin)
        margin_form.addRow("Right:", self.right_margin)
        
        # 3. Typography
        typo_group = QGroupBox("Typography")
        typo_form = QFormLayout(typo_group)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Serif (Mincho)", "Sans-serif (Gothic)"])
        self.line_height = QDoubleSpinBox()
        self.line_height.setSingleStep(0.1)
        self.line_height.setValue(1.6)
        self.base_size = QSpinBox()
        self.base_size.setValue(10)
        self.base_size.setSuffix(" pt")
        self.heading_underline = QCheckBox("Show Heading Underlines")
        self.heading_underline.setChecked(True)
        self.table_style = QComboBox()
        self.table_style.addItems(["Bordered (Default)", "Clean (No borders/bg)"])
        typo_form.addRow("Font Family:", self.font_combo)
        typo_form.addRow("Base Size:", self.base_size)
        typo_form.addRow("Line Height:", self.line_height)
        typo_form.addRow("Table Style:", self.table_style)
        typo_form.addRow("", self.heading_underline)
        
        # 4. Page Decoration (Headers/Footers)
        decor_group = QGroupBox("Page Decoration")
        decor_form = QFormLayout(decor_group)
        
        self.show_page_num = QCheckBox("Show Page Numbers")
        self.show_page_num.setChecked(False)
        
        self.show_guides = QCheckBox("Show Page Guides (Preview Only)")
        self.show_guides.setChecked(True)
        
        self.header_text = QLineEdit()
        self.header_text.setPlaceholderText("Left Header Text...")
        self.footer_text = QLineEdit()
        self.footer_text.setPlaceholderText("Center Footer Text...")
        
        decor_form.addRow("", self.show_page_num)
        decor_form.addRow("", self.show_guides)
        decor_form.addRow("Header (L):", self.header_text)
        decor_form.addRow("Footer (C):", self.footer_text)
        
        # 5. Export Actions
        export_group = QGroupBox("Actions")
        export_layout = QVBoxLayout(export_group)
        
        self.btn_refresh = QPushButton("Refresh Preview (Final Check)")
        self.btn_refresh.setStyleSheet("background-color: #3E3E42; color: #CCCCCC; margin-bottom: 5px;")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        export_layout.addWidget(self.btn_refresh)
        
        self.btn_export_pdf = QPushButton("Export as PDF...")
        self.btn_export_pdf.clicked.connect(self._on_export_pdf)
        export_layout.addWidget(self.btn_export_pdf)
        
        # Assemble
        form_layout.addWidget(doc_group)
        form_layout.addWidget(margin_group)
        form_layout.addWidget(typo_group)
        form_layout.addWidget(decor_group)
        form_layout.addWidget(export_group)
        form_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(header)
        main_layout.addWidget(scroll)

    def _connect_signals(self):
        self.top_margin.valueChanged.connect(self._emit_margins)
        self.bottom_margin.valueChanged.connect(self._emit_margins)
        self.left_margin.valueChanged.connect(self._emit_margins)
        self.right_margin.valueChanged.connect(self._emit_margins)
        
        self.font_combo.currentTextChanged.connect(self._emit_typography)
        self.line_height.valueChanged.connect(self._emit_typography)
        self.base_size.valueChanged.connect(self._emit_typography)
        self.heading_underline.stateChanged.connect(self._emit_typography)
        self.table_style.currentTextChanged.connect(self._emit_typography)
        
        self.size_combo.currentTextChanged.connect(self._emit_page_size)
        self.orientation_combo.currentTextChanged.connect(self._emit_page_size)
        
        self.show_page_num.stateChanged.connect(self._emit_page_decor)
        self.show_guides.stateChanged.connect(self._on_guides_toggled)
        self.header_text.textChanged.connect(self._emit_page_decor)
        self.footer_text.textChanged.connect(self._emit_page_decor)
        
    def _emit_margins(self):
        self.margins_changed.emit(self.top_margin.value(), self.right_margin.value(), self.bottom_margin.value(), self.left_margin.value())
        
    def _emit_typography(self):
        font = '"Yu Mincho", "MS Mincho", serif' if "Serif" in self.font_combo.currentText() else '"Yu Gothic", "MS Gothic", sans-serif'
        self.typography_changed.emit(font, self.line_height.value(), self.base_size.value(), self.heading_underline.isChecked(), self.table_style.currentText())
        
    def _emit_page_size(self):
        self.page_size_changed.emit(self.size_combo.currentText(), self.orientation_combo.currentText())

    def _emit_page_decor(self):
        decor = {
            "show_page_num": self.show_page_num.isChecked(),
            "header": self.header_text.text(),
            "footer": self.footer_text.text()
        }
        self.page_decor_changed.emit(decor)
        
    def _on_guides_toggled(self):
        self.guides_toggled.emit(self.show_guides.isChecked())

    def _on_export_pdf(self):
        # Use last_dir if set, otherwise fallback to project root or current
        initial_path = os.path.join(self.last_dir, "report.pdf") if self.last_dir else "report.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", initial_path, "PDF Files (*.pdf)")
        if path:
            # Update last_dir to the directory chosen by the user for next time
            self.last_dir = os.path.dirname(path)
            self.export_pdf_requested.emit(path)

    def get_settings(self):
        return {
            "page_size": self.size_combo.currentText(),
            "orientation": self.orientation_combo.currentText(),
            "margin_top": self.top_margin.value(),
            "margin_bottom": self.bottom_margin.value(),
            "margin_left": self.left_margin.value(),
            "margin_right": self.right_margin.value(),
            "font_family": self.font_combo.currentText(),
            "base_size": self.base_size.value(),
            "line_height": self.line_height.value(),
            "heading_underline": self.heading_underline.isChecked(),
            "table_style": self.table_style.currentText(),
            "show_page_num": self.show_page_num.isChecked(),
            "header_text": self.header_text.text(),
            "footer_text": self.footer_text.text(),
            "show_guides": self.show_guides.isChecked()
        }

    def apply_settings(self, settings):
        if not settings: return
        
        # Block signals temporarily to avoid redundant preview updates
        self.blockSignals(True)
        
        if "page_size" in settings: self.size_combo.setCurrentText(settings["page_size"])
        if "orientation" in settings: self.orientation_combo.setCurrentText(settings["orientation"])
        
        if "margin_top" in settings: self.top_margin.setValue(settings["margin_top"])
        if "margin_bottom" in settings: self.bottom_margin.setValue(settings["margin_bottom"])
        if "margin_left" in settings: self.left_margin.setValue(settings["margin_left"])
        if "margin_right" in settings: self.right_margin.setValue(settings["margin_right"])
        
        if "font_family" in settings: self.font_combo.setCurrentText(settings["font_family"])
        if "base_size" in settings: self.base_size.setValue(settings["base_size"])
        if "line_height" in settings: self.line_height.setValue(settings["line_height"])
        if "heading_underline" in settings: 
            # In case someone manually writes true/false strings in YAML, handle boolean parsing
            val = settings["heading_underline"]
            is_checked = (val is True or val == "True" or val == "true")
            self.heading_underline.setChecked(is_checked)
        if "table_style" in settings: self.table_style.setCurrentText(settings["table_style"])
        
        if "show_page_num" in settings:
            val = settings["show_page_num"]
            self.show_page_num.setChecked(val is True or val == "True" or val == "true")
        if "header_text" in settings: self.header_text.setText(str(settings["header_text"]))
        if "footer_text" in settings: self.footer_text.setText(str(settings["footer_text"]))
        if "show_guides" in settings: self.show_guides.setChecked(settings["show_guides"] is True)
        
        self.blockSignals(False)
        
        # Re-emit signals to update preview
        self._emit_margins()
        self._emit_typography()
        self._emit_page_size()
        self._emit_page_decor()
        self._on_guides_toggled()

