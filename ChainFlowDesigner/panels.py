from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QSpinBox, 
    QFontComboBox, QDoubleSpinBox, QPushButton, QColorDialog,
    QCheckBox, QSlider, QGroupBox, QHBoxLayout, QButtonGroup
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

class BasePanel(QWidget):
    propertyChanged = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.undo_stack = None
        self.current_item = None
        self._updating = False

    def set_undo_stack(self, stack):
        self.undo_stack = stack

    def set_item(self, item):
        self._updating = True
        self.blockSignals(True)
        self._update_ui_from_item(item)
        self.blockSignals(False)
        self.current_item = item
        self._updating = False

    def _update_ui_from_item(self, item):
        pass

    def on_property_change(self, name, value):
        if self._updating:
            return
        
        if self.current_item:
            if self.undo_stack:
                from commands import PropertyChangeCommand
                command = PropertyChangeCommand(self.current_item, name, value)
                self.undo_stack.push(command)
            else:
                if hasattr(self.current_item, 'set_property'):
                    self.current_item.set_property(name, value)
                    self.current_item.update()
                else:
                    self._apply_property_to_item(self.current_item, name, value)
                    self.current_item.update()

    def _apply_property_to_item(self, item, name, value):
        pass

class TextPanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        form_layout = QFormLayout()
        
        # Font Family
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(
            lambda f: self.on_property_change("font_family", f.family())
        )
        form_layout.addRow("Font:", self.font_combo)
        
        # Size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 200)
        self.size_spin.valueChanged.connect(
            lambda v: self.on_property_change("font_size", v)
        )
        form_layout.addRow("Size:", self.size_spin)
        
        # Color
        self.color_btn = QPushButton("Select Color")
        self.color_btn.clicked.connect(self.choose_color)
        form_layout.addRow("Color:", self.color_btn)
        
        # Style
        self.bold_check = QCheckBox("Bold")
        self.bold_check.toggled.connect(
            lambda v: self.on_property_change("font_bold", v)
        )
        form_layout.addRow("", self.bold_check)
        
        self.italic_check = QCheckBox("Italic")
        self.italic_check.toggled.connect(
            lambda v: self.on_property_change("font_italic", v)
        )
        form_layout.addRow("", self.italic_check)
        
        # Tracking (Letter Spacing)
        self.tracking_spin = QDoubleSpinBox()
        self.tracking_spin.setRange(-50.0, 200.0)
        self.tracking_spin.setSingleStep(1.0)
        self.tracking_spin.valueChanged.connect(
            lambda v: self.on_property_change("letter_spacing", v)
        )
        form_layout.addRow("Tracking:", self.tracking_spin)
        
        # Line Height
        self.line_height_spin = QDoubleSpinBox()
        self.line_height_spin.setRange(0.1, 5.0)
        self.line_height_spin.setSingleStep(0.1)
        self.line_height_spin.setValue(1.0)
        self.line_height_spin.valueChanged.connect(
            lambda v: self.on_property_change("line_height", v)
        )
        form_layout.addRow("Line Height:", self.line_height_spin)
        
        self.layout.addLayout(form_layout)
        
        # Alignment & Width
        align_layout = QFormLayout()
        
        # Width Setup (For fixed width text box)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(-1, 2000) # -1 means auto
        self.width_spin.setSpecialValueText("Auto")
        self.width_spin.valueChanged.connect(
            lambda v: self.on_property_change("width", v)
        )
        align_layout.addRow("Box Width:", self.width_spin)
        
        # Alignment Buttons
        h_layout = QHBoxLayout()
        
        self.align_left_btn = QPushButton("L")
        self.align_left_btn.setCheckable(True)
        self.align_left_btn.clicked.connect(lambda: self._on_align_change("left"))
        
        self.align_center_btn = QPushButton("C")
        self.align_center_btn.setCheckable(True)
        self.align_center_btn.clicked.connect(lambda: self._on_align_change("center"))
        
        self.align_right_btn = QPushButton("R")
        self.align_right_btn.setCheckable(True)
        self.align_right_btn.clicked.connect(lambda: self._on_align_change("right"))
        
        self.align_justify_btn = QPushButton("J")
        self.align_justify_btn.setCheckable(True)
        self.align_justify_btn.clicked.connect(lambda: self._on_align_change("justify"))
        
        self.align_group = QButtonGroup(self)
        self.align_group.addButton(self.align_left_btn)
        self.align_group.addButton(self.align_center_btn)
        self.align_group.addButton(self.align_right_btn)
        self.align_group.addButton(self.align_justify_btn)
        
        h_layout.addWidget(self.align_left_btn)
        h_layout.addWidget(self.align_center_btn)
        h_layout.addWidget(self.align_right_btn)
        h_layout.addWidget(self.align_justify_btn)
        align_layout.addRow("Align:", h_layout)

        # Vertical Alignment Buttons
        v_layout = QHBoxLayout()
        
        self.valign_top_btn = QPushButton("T")
        self.valign_top_btn.setCheckable(True)
        self.valign_top_btn.clicked.connect(lambda: self._on_valign_change("top"))
        
        self.valign_center_btn = QPushButton("M")
        self.valign_center_btn.setCheckable(True)
        self.valign_center_btn.clicked.connect(lambda: self._on_valign_change("center"))
        
        self.valign_bottom_btn = QPushButton("B")
        self.valign_bottom_btn.setCheckable(True)
        self.valign_bottom_btn.clicked.connect(lambda: self._on_valign_change("bottom"))
        
        self.valign_group = QButtonGroup(self)
        self.valign_group.addButton(self.valign_top_btn)
        self.valign_group.addButton(self.valign_center_btn)
        self.valign_group.addButton(self.valign_bottom_btn)
        
        v_layout.addWidget(self.valign_top_btn)
        v_layout.addWidget(self.valign_center_btn)
        v_layout.addWidget(self.valign_bottom_btn)
        align_layout.addRow("V-Align:", v_layout)
        
        self.layout.addLayout(align_layout)
        
        # Box Width Control
        width_layout = QHBoxLayout()
        width_label = QLabel("Box Width:")
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0, 9999) # 0 means auto? No, -1 is auto.
        self.width_spin.setSpecialValueText("Auto") # If value is -1
        self.width_spin.setMinimum(-1)
        self.width_spin.setValue(-1)
        self.width_spin.valueChanged.connect(lambda v: self.on_property_change("width", v))
        
        self.auto_width_check = QCheckBox("Auto")
        self.auto_width_check.setChecked(True)
        self.auto_width_check.toggled.connect(self._on_auto_width_toggled)
        

        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_spin)
        width_layout.addWidget(self.auto_width_check)
        self.layout.addLayout(width_layout)

        # Box Height Control
        height_layout = QHBoxLayout()
        height_label = QLabel("Box Height:")
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0, 9999)
        self.height_spin.setSpecialValueText("Auto")
        self.height_spin.setMinimum(-1)
        self.height_spin.setValue(-1)
        self.height_spin.valueChanged.connect(lambda v: self.on_property_change("fixed_height", v))
        
        self.auto_height_check = QCheckBox("Auto")
        self.auto_height_check.setChecked(True)
        self.auto_height_check.toggled.connect(self._on_auto_height_toggled)
        
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_spin)
        height_layout.addWidget(self.auto_height_check)
        self.layout.addLayout(height_layout)

        # Quick Styles
        style_layout = QHBoxLayout()
        
        btn_title = QPushButton("Title")
        btn_title.clicked.connect(lambda: self.apply_style("Title"))
        
        btn_header = QPushButton("Header")
        btn_header.clicked.connect(lambda: self.apply_style("Header"))
        
        btn_body = QPushButton("Body")
        btn_body.clicked.connect(lambda: self.apply_style("Body"))
        
        btn_caption = QPushButton("Caption")
        btn_caption.clicked.connect(lambda: self.apply_style("Caption"))
        
        style_layout.addWidget(btn_title)
        style_layout.addWidget(btn_header)
        style_layout.addWidget(btn_body)
        style_layout.addWidget(btn_caption)
        
        self.layout.addLayout(style_layout)
        
        self.layout.addStretch()

    def apply_style(self, style_name):
        if not self.current_item:
            return
            
        styles = {
            "Title": (24, True, "#000000"),
            "Header": (18, True, "#333333"),
            "Body": (12, False, "#000000"),
            "Caption": (10, False, "#666666")
        }
        
        if style_name in styles:
            size, is_bold, color_name = styles[style_name]
            
            if self.undo_stack:
                self.undo_stack.beginMacro(f"Apply Style: {style_name}")
            
            if hasattr(self, 'size_spin'):
                 self.size_spin.setValue(size)
            else:
                 self.on_property_change("font_size", size)

            if hasattr(self, 'bold_check'):
                self.bold_check.setChecked(is_bold)
            else:
                self.on_property_change("font_bold", is_bold)

            if color_name:
                c = QColor(color_name)
                self.on_property_change("text_color", c)
                if hasattr(self, 'color_btn'):
                    self.color_btn.setStyleSheet(f"background-color: {c.name()}")

            if self.undo_stack:
                self.undo_stack.endMacro()

    def _on_align_change(self, align_value):
        """配置変更: プロパティを変更した後にBox Widthスピンボックスも同期"""
        self.on_property_change("alignment", align_value)
        if self.current_item:
            current_width = self.current_item.textWidth()
            self._updating = True
            self.width_spin.setValue(current_width)
            self._updating = False

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.on_property_change("text_color", color)
            self.color_btn.setStyleSheet(f"background-color: {color.name()}")

    def _on_auto_width_toggled(self, checked):
        if self._updating: return
        
        if checked:
            self.width_spin.setValue(-1)
            self.width_spin.setEnabled(False)
        else:
            if self.current_item:
                 # Set to current bounding rect width instead of -1
                 current_w = self.current_item.boundingRect().width()
                 self.width_spin.setValue(current_w)
            self.width_spin.setEnabled(True)

    def _on_auto_height_toggled(self, checked):
        if self._updating: return
        
        if checked:
            self.height_spin.setValue(-1)
            self.height_spin.setEnabled(False)
        else:
            if self.current_item:
                 # Set to current bounding rect height instead of -1
                 current_h = self.current_item.boundingRect().height()
                 self.height_spin.setValue(current_h)
            self.height_spin.setEnabled(True)

        self.layout.addLayout(align_layout)

    def _on_valign_change(self, align_value):
        self.on_property_change("vertical_alignment", align_value)

    def _update_ui_from_item(self, item):
        self._updating = True
        font = item.font()
        self.font_combo.setCurrentFont(font)
        self.size_spin.setValue(int(font.pointSize()))
        self.bold_check.setChecked(font.bold())
        self.italic_check.setChecked(font.italic())
        
        # Color
        color = item.defaultTextColor()
        if hasattr(self, 'color_btn'):
             self.color_btn.setStyleSheet(f"background-color: {color.name()}")
        
        # Width
        w = item.textWidth()
        self.width_spin.setValue(w) # If -1, shows "Auto" due to special text
        
        if w == -1:
            self.auto_width_check.setChecked(True)
            self.width_spin.setEnabled(False)
        else:
            self.auto_width_check.setChecked(False)
            self.width_spin.setEnabled(True)

        # Height
        h = -1
        if hasattr(item, '_fixed_height'):
            h = item._fixed_height
        
        self.height_spin.setValue(h)
        
        if h == -1:
            self.auto_height_check.setChecked(True)
            self.height_spin.setEnabled(False)
        else:
            self.auto_height_check.setChecked(False)
            self.height_spin.setEnabled(True)
        
        # Alignment check
        opt = item.document().defaultTextOption()
        align = opt.alignment()
        
        if self.align_group:
            self.align_group.setExclusive(False)
            self.align_left_btn.setChecked(False)
            self.align_center_btn.setChecked(False)
            self.align_right_btn.setChecked(False)
            self.align_justify_btn.setChecked(False)
            self.align_group.setExclusive(True)
            
            # Since _text_alignment handles alignment now
            if hasattr(item, '_text_alignment'):
                align = item._text_alignment
                if align == Qt.AlignRight:
                    self.align_right_btn.setChecked(True)
                elif align == Qt.AlignHCenter:
                    self.align_center_btn.setChecked(True)
                elif align == Qt.AlignJustify:
                    self.align_justify_btn.setChecked(True)
                else:
                    self.align_left_btn.setChecked(True)
            else:
                self.align_left_btn.setChecked(True)
        
        if hasattr(item, '_letter_spacing'):
            self.tracking_spin.setValue(item._letter_spacing)
        if hasattr(item, '_line_height'):
            self.line_height_spin.setValue(item._line_height)

        # Vertical Alignment check
        if hasattr(item, '_vertical_alignment') and self.valign_group:
            valign = item._vertical_alignment
            self.valign_group.setExclusive(False)
            self.valign_top_btn.setChecked(False)
            self.valign_center_btn.setChecked(False)
            self.valign_bottom_btn.setChecked(False)
            self.valign_group.setExclusive(True)
            
            if valign == "center":
                self.valign_center_btn.setChecked(True)
            elif valign == "bottom":
                self.valign_bottom_btn.setChecked(True)
            else:
                self.valign_top_btn.setChecked(True)
            
        self._updating = False

    def _apply_property_to_item(self, item, name, value):
        font = item.font()
        if name == "font_family":
            font.setFamily(value)
        elif name == "font_size":
            font.setPointSize(max(1, int(value))) # Ensure size > 0
            font.setItalic(value)
        elif name == "text_color":
            item.setDefaultTextColor(value)
            return
            
        item.setFont(font)

class ImagePanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        form_layout = QFormLayout()
        
        # Scale
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 10.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.valueChanged.connect(
            lambda v: self.on_property_change("scale", v)
        )
        form_layout.addRow("Scale:", self.scale_spin)
        
        # Opacity
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.on_property_change("opacity", v / 100.0)
        )
        form_layout.addRow("Opacity:", self.opacity_slider)
        
        self.layout.addLayout(form_layout)

    def _update_ui_from_item(self, item):
        self.scale_spin.setValue(item.scale())
        self.opacity_slider.setValue(int(item.opacity() * 100))

    def _apply_property_to_item(self, item, name, value):
        if name == "scale":
            item.setScale(value)
        elif name == "opacity":
            item.setOpacity(value)

class ShapePanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        form_layout = QFormLayout()
        
        # Width
        self.width_spin = QSpinBox()
        self.width_spin.setRange(-2000, 2000)
        self.width_spin.valueChanged.connect(
            lambda v: self.on_property_change("width", v)
        )
        form_layout.addRow("Width:", self.width_spin)
        
        # Height
        self.height_spin = QSpinBox()
        self.height_spin.setRange(-2000, 2000)
        self.height_spin.valueChanged.connect(
            lambda v: self.on_property_change("height", v)
        )
        form_layout.addRow("Height:", self.height_spin)
        
        # Border Width
        self.border_spin = QDoubleSpinBox()
        self.border_spin.setRange(0, 20)
        self.border_spin.setSingleStep(0.5)
        self.border_spin.valueChanged.connect(
            lambda v: self.on_property_change("border_width", v)
        )
        form_layout.addRow("Border:", self.border_spin)
        
        # Fill Color
        self.fill_btn = QPushButton("Fill Color")
        self.fill_btn.clicked.connect(self.choose_fill_color)
        form_layout.addRow("", self.fill_btn)
        
        # Border Color
        self.border_color_btn = QPushButton("Border Color")
        self.border_color_btn.clicked.connect(self.choose_border_color)
        form_layout.addRow("", self.border_color_btn)
        
        self.layout.addLayout(form_layout)

    def choose_fill_color(self):
        color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.on_property_change("fill_color", color)
            self.fill_btn.setStyleSheet(f"background-color: {color.name()}")

    def choose_border_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.on_property_change("border_color", color)
            self.border_color_btn.setStyleSheet(f"background-color: {color.name()}")

    def _update_ui_from_item(self, item):
        self.width_spin.setValue(int(item._width))
        self.height_spin.setValue(int(item._height))
        self.border_spin.setValue(item._border_width)
        self.fill_btn.setStyleSheet(f"background-color: {item._fill_color.name()}")
        self.border_color_btn.setStyleSheet(f"background-color: {item._border_color.name()}")

class TablePanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        form_layout = QFormLayout()
        
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 50)
        self.rows_spin.valueChanged.connect(
            lambda v: self.on_property_change("rows", v)
        )
        form_layout.addRow("Rows:", self.rows_spin)
        
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 20)
        self.cols_spin.valueChanged.connect(
            lambda v: self.on_property_change("cols", v)
        )
        form_layout.addRow("Cols:", self.cols_spin)
        
        self.cell_w_spin = QSpinBox()
        self.cell_w_spin.setRange(30, 400)
        self.cell_w_spin.valueChanged.connect(
            lambda v: self.on_property_change("cell_width", v)
        )
        form_layout.addRow("Cell W:", self.cell_w_spin)
        
        self.cell_h_spin = QSpinBox()
        self.cell_h_spin.setRange(15, 200)
        self.cell_h_spin.valueChanged.connect(
            lambda v: self.on_property_change("cell_height", v)
        )
        form_layout.addRow("Cell H:", self.cell_h_spin)
        
        # Alignment
        align_layout = QFormLayout()
        h_layout = QHBoxLayout()
        
        self.align_left_btn = QPushButton("L")
        self.align_left_btn.setCheckable(True)
        self.align_left_btn.clicked.connect(lambda: self._on_align_change("left"))
        
        self.align_center_btn = QPushButton("C")
        self.align_center_btn.setCheckable(True)
        self.align_center_btn.clicked.connect(lambda: self._on_align_change("center"))
        
        self.align_right_btn = QPushButton("R")
        self.align_right_btn.setCheckable(True)
        self.align_right_btn.clicked.connect(lambda: self._on_align_change("right"))
        
        self.align_group = QButtonGroup(self)
        self.align_group.addButton(self.align_left_btn)
        self.align_group.addButton(self.align_center_btn)
        self.align_group.addButton(self.align_right_btn)
        
        h_layout.addWidget(self.align_left_btn)
        h_layout.addWidget(self.align_center_btn)
        h_layout.addWidget(self.align_right_btn)
        align_layout.addRow("Align:", h_layout)
        
        self.layout.addLayout(align_layout)

        # Border Width
        self.border_spin = QDoubleSpinBox()
        self.border_spin.setRange(0, 10)
        self.border_spin.setSingleStep(0.5)
        self.border_spin.valueChanged.connect(
            lambda v: self.on_property_change("border_width", v)
        )
        form_layout.addRow("Border:", self.border_spin)
        
        # Fill Color
        self.fill_btn = QPushButton("Fill Color")
        self.fill_btn.clicked.connect(self.choose_fill_color)
        form_layout.addRow("", self.fill_btn)
        
        # Border Color
        self.border_color_btn = QPushButton("Border Color")
        self.border_color_btn.clicked.connect(self.choose_border_color)
        form_layout.addRow("", self.border_color_btn)
        
        # Header Color
        self.header_color_btn = QPushButton("Header Color")
        self.header_color_btn.clicked.connect(self.choose_header_color)
        form_layout.addRow("", self.header_color_btn)
        
        self.layout.addLayout(form_layout)

    def choose_fill_color(self):
        color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.on_property_change("fill_color", color)
            self.fill_btn.setStyleSheet(f"background-color: {color.name()}")

    def choose_border_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.on_property_change("border_color", color)
            self.border_color_btn.setStyleSheet(f"background-color: {color.name()}")
    
    def choose_header_color(self):
        color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.on_property_change("header_color", color)
            self.header_color_btn.setStyleSheet(f"background-color: {color.name()}")
            
    def _on_align_change(self, align_value):
        self.on_property_change("alignment", align_value)
    
    def _update_ui_from_item(self, item):
        self.rows_spin.setValue(item._rows)
        self.cols_spin.setValue(item._cols)
        self.cell_w_spin.setValue(int(item._cell_width))
        self.cell_h_spin.setValue(int(item._cell_height))
        self.border_spin.setValue(item._border_width)
        if hasattr(item, '_fill_color'):
            self.fill_btn.setStyleSheet(f"background-color: {item._fill_color.name()}")
        if hasattr(item, '_border_color'):
            self.border_color_btn.setStyleSheet(f"background-color: {item._border_color.name()}")
        if hasattr(item, '_header_color'):
            self.header_color_btn.setStyleSheet(f"background-color: {item._header_color.name()}")
        
        if hasattr(item, '_alignment'):
            align = item._alignment
            self.align_group.setExclusive(False)
            self.align_left_btn.setChecked(False)
            self.align_center_btn.setChecked(False)
            self.align_right_btn.setChecked(False)
            self.align_group.setExclusive(True)
            
            if align == "center":
                self.align_center_btn.setChecked(True)
            elif align == "right":
                self.align_right_btn.setChecked(True)
            else:
                self.align_left_btn.setChecked(True)

class ShadowPanel(BasePanel):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.shadow_group = QGroupBox("Drop Shadow")
        self.shadow_group.setCheckable(True)
        self.shadow_group.setChecked(False)
        self.shadow_group.toggled.connect(
            lambda v: self.on_property_change("has_shadow", v)
        )
        
        form_layout = QFormLayout()
        
        # Color
        self.color_btn = QPushButton("Shadow Color")
        self.color_btn.clicked.connect(self.choose_color)
        form_layout.addRow("", self.color_btn)
        
        # Blur
        self.blur_spin = QDoubleSpinBox()
        self.blur_spin.setRange(0, 100)
        self.blur_spin.setValue(10)
        self.blur_spin.valueChanged.connect(
            lambda v: self.on_property_change("shadow_blur", v)
        )
        form_layout.addRow("Blur:", self.blur_spin)
        
        # Offset X
        self.offset_x_spin = QDoubleSpinBox()
        self.offset_x_spin.setRange(-100, 100)
        self.offset_x_spin.setValue(5)
        self.offset_x_spin.valueChanged.connect(
            lambda v: self.on_property_change("shadow_offset_x", v)
        )
        form_layout.addRow("Offset X:", self.offset_x_spin)
        
        # Offset Y
        self.offset_y_spin = QDoubleSpinBox()
        self.offset_y_spin.setRange(-100, 100)
        self.offset_y_spin.setValue(5)
        self.offset_y_spin.valueChanged.connect(
            lambda v: self.on_property_change("shadow_offset_y", v)
        )
        form_layout.addRow("Offset Y:", self.offset_y_spin)
        
        self.shadow_group.setLayout(form_layout)
        self.layout.addWidget(self.shadow_group)
        
    def choose_color(self):
        color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.on_property_change("shadow_color", color)
            self.color_btn.setStyleSheet(f"background-color: {color.name()}")
            
    def _update_ui_from_item(self, item):
        if hasattr(item, '_has_shadow'):
            self.shadow_group.setChecked(item._has_shadow)
        if hasattr(item, '_shadow_color'):
            self.color_btn.setStyleSheet(f"background-color: {item._shadow_color.name()}")
        if hasattr(item, '_shadow_blur'):
            self.blur_spin.setValue(item._shadow_blur)
        if hasattr(item, '_shadow_offset_x'):
            self.offset_x_spin.setValue(item._shadow_offset_x)
        if hasattr(item, '_shadow_offset_y'):
            self.offset_y_spin.setValue(item._shadow_offset_y)
