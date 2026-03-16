from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QColor, QPainter
import os

class PDFThumbnail(QFrame):
    def __init__(self, page_num, pixmap=None, file_path=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(140, 180) # Slightly larger to fit image
        
        # Calculate subtle border color from filename
        self.current_border_color = "#555"
        if file_path:
            self.current_border_color = self._generate_color_from_string(os.path.basename(file_path))
            # Make it slightly more subtle by blending or using opacity if needed, 
            # but here we rely on the pastel generation.
            
        self.is_used = False # New state for 'used' pages
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Image Label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #444; color: #fff; border: none;")
        self.image_label.setFixedSize(130, 150) # Fixed size container for image
        
        if pixmap:
            self.original_pixmap = pixmap
            self._update_image()
        else:
            self.image_label.setText(f"Page {page_num}")
            
        layout.addWidget(self.image_label, 0, Qt.AlignCenter)

        # Page Number Label creation logic
        label_text = f"P.{page_num}"
        if file_path:
            base_name = os.path.basename(file_path)
            # Calculate available width for filename
            # Total width (140) - Layout Margins (10) - Suffix width
            suffix = f": P.{page_num}"
            fm = self.fontMetrics()
            
            # Using slightly less width to be safe
            available_width = 130 - fm.horizontalAdvance(suffix)
            
            if available_width > 20:
                elided_name = fm.elidedText(base_name, Qt.ElideMiddle, available_width)
                label_text = f"{elided_name}{suffix}"
            else:
                # Fallback if extremely narrow (unlikely with 140px width)
                label_text = f"{base_name[:5]}..{suffix}"

        self.num_label = QLabel(label_text)
        self.num_label.setAlignment(Qt.AlignCenter)
        self.num_label.setStyleSheet("color: #aaa; font-size: 10px;")
        layout.addWidget(self.num_label)
        
        # Initial style update
        self._update_style()

    def set_used(self, used: bool):
        """Update visual state based on whether the page is used in timeline."""
        if self.is_used != used:
            self.is_used = used
            self._update_style()
            
    def set_active(self, active: bool):
        """Update visual state based on selection."""
        # Use a property to store active state if needed, but for now just pass to update_style
        # Or store it? We need both states to persist.
        self.is_active = active 
        self._update_style()

    def _update_style(self):
        # Base style
        base_color = "#333"
        border_color = self.current_border_color if hasattr(self, 'current_border_color') else "#555"
        border_width = "1px"
        
        # Used state (Dimmed)
        opacity = 1.0
        if hasattr(self, 'is_used') and self.is_used:
            opacity = 0.4 # Dim the widget content
            
        # Active state (Selected) - Overrides subtle border
        if hasattr(self, 'is_active') and self.is_active:
            base_color = "#444"
            border_color = "#3498db"
            border_width = "2px"
            opacity = 1.0 # Selected item should be fully visible even if used? Or keep it dimmed?
            # User wants: "Gray out, but prioritize selection highlight (blue) if selected".
            # If we keep opacity low, it might be hard to see. 
            # If we restore opacity, we lose "used" context when selected.
            # Let's keep opacity low but use BRIGHT border.
            if hasattr(self, 'is_used') and self.is_used:
                opacity = 0.6 # slightly more visible if selected
            
        style = f"background-color: {base_color}; border: {border_width} solid {border_color}; border-radius: 4px;"
        self.setStyleSheet(style)
        
        # For image opacity, we can use QGraphicsOpacityEffect on the image_label
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        effect = QGraphicsOpacityEffect(self.image_label)
        effect.setOpacity(opacity)
        self.image_label.setGraphicsEffect(effect)

    def resize_thumbnail(self, width, height):
        self.setFixedSize(width, height)
        
        # Determine image label size (leaving space for number label and margins)
        # Margins: 5px each side -> 10px total width/height deduction
        # Number label: approx 20px (font size 10 + padding)
        
        image_width = width - 10
        image_height = height - 30 # Reserve space for text
        
        self.image_label.setFixedSize(image_width, image_height)
        
        # Re-scale existing pixmap if present
        if self.image_label.pixmap():
            self._update_image()
            
    def set_pixmap(self, pixmap):
        self.original_pixmap = pixmap # Store original
        self._update_image()

    def _update_image(self):
        if hasattr(self, 'original_pixmap') and self.original_pixmap:
             scaled = self.original_pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
             self.image_label.setPixmap(scaled)

    # Old set_active removed, logic moved to _update_style

    def _generate_color_from_string(self, s: str) -> str:
        """
        Generates a deterministic pastel color from a string seed (filename).
        Returns a hex string.
        """
        import hashlib
        
        # Use MD5 to get a consistent hash from the filename
        hash_object = hashlib.md5(s.encode())
        hex_dig = hash_object.hexdigest()
        
        # Take first 6 chars to form a base color
        r = int(hex_dig[0:2], 16)
        g = int(hex_dig[2:4], 16)
        b = int(hex_dig[4:6], 16)
        
        # Mix with specific base color (e.g. #444 or #555) to make it subtle
        # Instead of white, we mix with a dark grey so the border isn't too bright
        # Wait, user said "pastel" usually implies mixing with white, but "not too harsh"
        # and dark theme context.
        # Let's try mixing with a mid-grey to desaturate and darken slightly
        # Mix with a lighter grey to ensure visibility but keep it subtle (low saturation)
        mix_target = 150 # Mid-Light Grey
        mix_factor = 0.6 # Balance between color and grey
        
        r = int(r * (1 - mix_factor) + mix_target * mix_factor)
        g = int(g * (1 - mix_factor) + mix_target * mix_factor)
        b = int(b * (1 - mix_factor) + mix_target * mix_factor)
        
        return f"#{r:02x}{g:02x}{b:02x}"

