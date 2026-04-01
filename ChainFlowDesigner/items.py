from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem, QApplication, QMenu, QGraphicsItemGroup
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QFont, QColor, QCursor, QBrush, QPen, QUndoCommand, QFontMetrics, QTextCursor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

class ResizeHandle(QGraphicsRectItem):
    def __init__(self, parent, cursor_shape):
        super().__init__(-4, -4, 8, 8, parent) # Center logic
        self.setCursor(QCursor(cursor_shape))
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black))
        self.setFlags(QGraphicsItem.ItemIsMovable)
        self.parent_item = parent

    def mouseMoveEvent(self, event):
        if self.parent_item and hasattr(self.parent_item, 'handle_resize'):
            self.parent_item.handle_resize(self, event.scenePos())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.parent_item and hasattr(self.parent_item, 'prepare_resize'):
            self.parent_item.prepare_resize(self)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.parent_item and hasattr(self.parent_item, 'end_resize'):
            self.parent_item.end_resize(self)

    def paint(self, painter, option, widget=None):
        # ズームに依存せず一定サイズで見せる工夫
        # 親のスケールも考慮する必要があるが、簡易的にViewのスケール逆数を適用
        scale = 1.0
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            # m11() is horizontal scale
            view_scale = view.transform().m11()
            if view_scale > 0:
                scale = 1.0 / view_scale
        
        # 中心基準でスケーリング
        painter.save()
        painter.scale(scale, scale)
        
        # Draw rect manually to avoid bounding rect issues with auto-paint
        # Use a fixed size rect (8x8 centered means -4, -4, 8, 8)
        # But since we scaled the painter, we draw the original coords
        icon_rect = QRectF(-4, -4, 8, 8)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRect(icon_rect)
        
        painter.restore()

class ConstrainedMoveMixin:
    def __init__(self):
        self.drag_start_pos = None

    def mousePressEvent(self, event):
        self.drag_start_pos = self.pos()
        self._raw_un_snapped_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.drag_start_pos is not None and self.pos() != self.drag_start_pos:
            # Movement finished
            if self.scene() and hasattr(self.scene(), 'undo_stack'):
                from commands import MoveItemCommand
                command = MoveItemCommand(self, self.drag_start_pos, self.pos())
                self.scene().undo_stack.push(command)
        self.drag_start_pos = None
        # ガイド線をクリア
        if self.scene() and hasattr(self.scene(), 'clear_guides'):
            self.scene().clear_guides()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            if getattr(self, '_is_resizing', False):
                return super().itemChange(change, value)
            
            # Qt内部の移動ロジックによるオフセット破壊（ガタつき）を防ぐため、
            # 純粋な移動デルタを計算し、仮想の生座標（_raw_un_snapped_pos）に加算する。
            delta = value - self.pos()
            if hasattr(self, '_raw_un_snapped_pos'):
                self._raw_un_snapped_pos += delta
                raw_target = QPointF(self._raw_un_snapped_pos) # コピーして利用
            else:
                raw_target = QPointF(value)
                
            new_pos = raw_target
            
            # Check for Shift key (軸固定)
            modifiers = QApplication.keyboardModifiers()
            if modifiers & Qt.ShiftModifier and self.drag_start_pos:
                dx = abs(new_pos.x() - self.drag_start_pos.x())
                dy = abs(new_pos.y() - self.drag_start_pos.y())
                
                if dx > dy:
                    new_pos = QPointF(new_pos.x(), self.drag_start_pos.y())
                    if hasattr(self, '_raw_un_snapped_pos'): self._raw_un_snapped_pos.setY(self.drag_start_pos.y())
                else:
                    new_pos = QPointF(self.drag_start_pos.x(), new_pos.y())
                    if hasattr(self, '_raw_un_snapped_pos'): self._raw_un_snapped_pos.setX(self.drag_start_pos.x())
            
            # Apply snap logic
            scene = self.scene()
            if scene:
                # 1. Grid Snap (Top priority)
                if hasattr(scene, 'snap_enabled') and scene.snap_enabled:
                    new_pos = scene.snap_to_grid(new_pos)
                    # Clear smart guides if grid snap is active
                    if hasattr(scene, 'clear_guides'):
                        scene.clear_guides()
                        
                # 2. Smart Guides (Only if grid snap is OFF)
                elif hasattr(scene, 'smart_guides_enabled') and scene.smart_guides_enabled:
                    new_pos, guides = scene.calculate_snap(self, new_pos)
                    scene.active_guides = guides
                    scene.update()
            
            return new_pos
                    
        return super().itemChange(change, value)

class ResizeMixin:
    def get_snapped_pos(self, mouse_pos):
        """共通スナップロジック: グリッドスナップ または スマートスナップ"""
        target_pos = mouse_pos
        scene = self.scene()
        if scene:
            if hasattr(scene, 'snap_enabled') and scene.snap_enabled:
                target_pos = scene.snap_to_grid(mouse_pos)
                if hasattr(scene, 'clear_guides'):
                    scene.clear_guides()
            elif hasattr(scene, 'smart_guides_enabled') and scene.smart_guides_enabled:
                target_pos, guides = scene.snap_point_to_objects(mouse_pos, exclude_items=[self])
                scene.active_guides = guides
                scene.update()
            else:
                 if hasattr(scene, 'clear_guides'):
                    scene.clear_guides()
        return target_pos

class ShadowMixin:
    def init_shadow(self):
        self._has_shadow = False
        self._shadow_color = QColor(0, 0, 0, 150)
        self._shadow_blur = 10.0
        self._shadow_offset_x = 5.0
        self._shadow_offset_y = 5.0
        self.update_shadow()
        
    def update_shadow(self):
        if self._has_shadow:
            effect = QGraphicsDropShadowEffect()
            effect.setColor(self._shadow_color)
            effect.setBlurRadius(self._shadow_blur)
            effect.setOffset(self._shadow_offset_x, self._shadow_offset_y)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)

class DTPTextItem(ConstrainedMoveMixin, ResizeMixin, ShadowMixin, QGraphicsTextItem):
    def __init__(self, text="New Text"):
        QGraphicsTextItem.__init__(self, text)
        ConstrainedMoveMixin.__init__(self)
        self.init_shadow()
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsFocusable |
            QGraphicsItem.ItemSendsScenePositionChanges
        )
        self.locked = False
        # Default to NoTextInteraction to allow easy moving.
        # Edit mode is entered via double click.
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setDefaultTextColor(Qt.black)
        self.setFont(QFont("Arial", 12))
        self._fixed_height = -1 # -1 means auto height
        self._vertical_alignment = "top" # top, center, bottom
        self._letter_spacing = 0.0 # Standard tracking (0.0 = normal)
        self._line_height = 1.0 # Multiplier (1.0 = normal)
        self._text_alignment = Qt.AlignLeft
        self._is_resizing = False

    def boundingRect(self):
        rect = super().boundingRect()
        if self._fixed_height > 0:
            rect.setHeight(self._fixed_height)
        return rect
        
    def _apply_text_formatting(self):
        import logging
        logging.debug(f"[DTPTextItem] _apply_text_formatting: text='{self.toPlainText()}', alignment={self._text_alignment}, tracking={self._letter_spacing}")
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        
        # Character formatting (Tracking)
        char_format = cursor.charFormat()
        char_format.setFontLetterSpacingType(QFont.AbsoluteSpacing)
        char_format.setFontLetterSpacing(self._letter_spacing)
        cursor.setCharFormat(char_format)
        
        # Block formatting (Line Height & Alignment)
        block_format = cursor.blockFormat()
        # Ensure we're using proportional line height based on font metrics or simple multiplier
        # QTextBlockFormat.setLineHeight takes points or simple multiplier, we use ProportionalHeight
        # block_format.setLineHeight(self._line_height * 100, QTextBlockFormat.ProportionalHeight)
        block_format.setAlignment(self._text_alignment)
        cursor.setBlockFormat(block_format)
        
        # Also apply document level text option 
        from PySide6.QtGui import QTextOption
        option = self.document().defaultTextOption()
        option.setAlignment(self._text_alignment)
        self.document().setDefaultTextOption(option)
        
        self.setTextCursor(cursor)
        
    def paint(self, painter, option, widget=None):
        # Clip if fixed height is set
        if self._fixed_height > 0:
             painter.save()
             painter.setClipRect(self.boundingRect())
             
             # Calculate Vertical Offset
             y_offset = 0
             if self._vertical_alignment != "top":
                 doc_h = self.document().size().height()
                 avail_h = self._fixed_height
                 
                 if self._vertical_alignment == "center":
                     y_offset = (avail_h - doc_h) / 2
                 elif self._vertical_alignment == "bottom":
                     y_offset = avail_h - doc_h
                 
                 # Don't offset if text is larger than box (top align behavior usually preferred then)
                 if y_offset < 0: y_offset = 0
             
             painter.translate(0, y_offset)
             super().paint(painter, option, widget)
             painter.restore()
        else:
             super().paint(painter, option, widget)
             
        # Draw border if selected or fixed size (visual feedback)
        if self.isSelected() or self._fixed_height > 0 or self.textWidth() != -1:
            painter.save()
            pen = QPen(Qt.DashLine)
            pen.setColor(QColor(0, 0, 0, 100))
            if self.isSelected():
                pen.setColor(QColor(0, 120, 215)) # Blue when selected
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())
            painter.restore()

    def mouseDoubleClickEvent(self, event):
        # Enter edit mode
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus()
        super().mouseDoubleClickEvent(event)
        
    def focusInEvent(self, event):
        self._original_text = self.toPlainText()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        # Exit edit mode
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        
        # Check for text change
        new_text = self.toPlainText()
        if hasattr(self, '_original_text') and self._original_text != new_text:
            if self.scene() and hasattr(self.scene(), 'undo_stack'):
                from commands import PropertyChangeCommand
                command = PropertyChangeCommand(self, "text", new_text)
                command.old_value = self._original_text
                self.scene().undo_stack.push(command)

        self._apply_text_formatting()
        super().focusOutEvent(event)

    def itemChange(self, change, value):
        # Handle selection change to show/hide handles
        if change == QGraphicsItem.ItemSelectedChange:
            if value and not self.locked:
                self.create_handles()
            else:
                self.remove_handles()
        return super().itemChange(change, value)

    def set_locked(self, locked):
        self.locked = locked
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not locked)
        self.setFlag(QGraphicsItem.ItemIsFocusable, not locked)
        if locked:
            self.remove_handles()
            self.setSelected(False)

    def create_handles(self):
        self.remove_handles()
        bg = self.boundingRect()
        
        # Only create Right/Bottom-Right/Bottom handles for resizing width/height?
        # For text box, standard DTP is changing width via corners or side handles.
        # Let's add all 8 handles but currently only implement width resizing for simplicity,
        # or standard scaling?
        # User requested: "Box size != text size".
        # So dragging handle should change setTextWidth.
        
        # Currently only implementing Width resizing (Right interactions)
        # 4 corners + 4 sides
        
        # For text area, usually right-bottom, right-middle, etc. change width.
        # Height is auto unless we strictly clip (which QGraphicsTextItem doesn't do easily without custom paint)
        # So we mainly control WIDTH.
        
        # Let's add 2 handles: Right-Middle and Bottom-Right to control width.
        # Or standard 8 handles.
        self.handles = []
        
        # Right handle (Width)
        h = ResizeHandle(self, Qt.SizeHorCursor)
        h.setPos(bg.right(), bg.center().y())
        h.name = 'right'
        self.handles.append(h)
        
        # Bottom-Right (Width + Height? Text height is auto)
        # For now, let it control width too.
        h = ResizeHandle(self, Qt.SizeFDiagCursor)
        h.setPos(bg.bottomRight())
        h.name = 'bottom_right'
        self.handles.append(h)

    def remove_handles(self):
        if hasattr(self, 'handles'):
            for h in self.handles:
                if self.scene():
                    self.scene().removeItem(h)
                h.setParentItem(None)
            self.handles = []

    def prepare_resize(self, handle):
        self._is_resizing = True
        self._resize_start_width = self.textWidth()
        if self._resize_start_width == -1:
            self._resize_start_width = self.boundingRect().width()
            
        self._resize_start_height = self._fixed_height
        if self._resize_start_height == -1:
            self._resize_start_height = self.boundingRect().height()
            
        self._resize_start_pos = handle.scenePos()

    def handle_resize(self, handle, new_scene_pos):
        # Apply strict snap to the target position
        target_pos = self.get_snapped_pos(new_scene_pos)
             
        # Transform mouse pos to item coords
        local_pos = self.mapFromScene(target_pos)
        
        # 1. Calculate Candidates
        new_width = local_pos.x()
        new_height = local_pos.y()
        
        # 2. Apply Constraints
        modifiers = QApplication.keyboardModifiers()
        if handle.name == 'bottom_right' and (modifiers & Qt.ShiftModifier):
            start_w = getattr(self, '_resize_start_width', -1)
            start_h = getattr(self, '_resize_start_height', -1)
            
            if start_w > 0 and start_h > 0:
                ratio = start_w / start_h
                # Adjust based on dominant axis
                if abs(new_width) > abs(new_height * ratio):
                     new_height = new_width / ratio
                else:
                     new_width = new_height * ratio

        # 3. Apply Limits (Min size)
        if new_width < 10: new_width = 10
        if handle.name == 'bottom_right':
            if new_height < 10: new_height = 10
        
        # 4. Set Properties
        self.setTextWidth(new_width)
        
        if handle.name == 'bottom_right':
            self.prepareGeometryChange()
            self._fixed_height = new_height
        
        self.update_handles()
        
    def end_resize(self, handle):
        self._is_resizing = False
        # Push undo command for width change
        if hasattr(self, '_resize_start_width'):
            new_width = self.textWidth()
            if abs(new_width - self._resize_start_width) > 1:
                if self.scene() and hasattr(self.scene(), 'undo_stack'):
                    from commands import PropertyChangeCommand
                    cmd = PropertyChangeCommand(self, "width", new_width)
                    cmd.old_value = self._resize_start_width
                    self.scene().undo_stack.push(cmd)

        # Push undo command for height change
        if hasattr(self, '_resize_start_height'):
            new_height = self._fixed_height
            if abs(new_height - self._resize_start_height) > 1:
                if self.scene() and hasattr(self.scene(), 'undo_stack'):
                    from commands import PropertyChangeCommand
                    cmd = PropertyChangeCommand(self, "fixed_height", new_height)
                    cmd.old_value = self._resize_start_height
                    self.scene().undo_stack.push(cmd)

    def update_handles(self):
        if hasattr(self, 'handles'):
             bg = self.boundingRect() # logic coords
             for h in self.handles:
                 # Handles are items in the scene (or child items? code says parent=self)
                 # ResizeHandle(self) means child item. So setPos uses local coords.
                 if h.name == 'right':
                     h.setPos(bg.right(), bg.center().y())
                 elif h.name == 'bottom_right':
                     h.setPos(bg.bottomRight())


    def to_dict(self):
        return {
            'type': 'text',
            'pos': (self.pos().x(), self.pos().y()),
            'text': self.toPlainText(),
            'font': {
                'family': self.font().family(),
                'size': self.font().pointSize(),
                'bold': self.font().bold(),
                'italic': self.font().italic()
            },
            'color': self.defaultTextColor().name(), # Keep name() for simple colors
            'alignment': int(self.document().defaultTextOption().alignment()), # Store int value
            'vertical_alignment': self._vertical_alignment,
            'text_width': self.textWidth(),
            'fixed_height': self._fixed_height if hasattr(self, '_fixed_height') else -1,
            'z': self.zValue(),
            'locked': getattr(self, 'locked', False),
            'visible': self.isVisible(),
            'letter_spacing': getattr(self, '_letter_spacing', 0.0),
            'line_height': getattr(self, '_line_height', 1.0),
            'text_alignment': int(getattr(self, '_text_alignment', Qt.AlignLeft)),
            'has_shadow': self._has_shadow,
            'shadow_color': self._shadow_color.name() if hasattr(self._shadow_color, 'name') else "#000000",
            'shadow_color_alpha': self._shadow_color.alpha(),
            'shadow_blur': self._shadow_blur,
            'shadow_offset_x': self._shadow_offset_x,
            'shadow_offset_y': self._shadow_offset_y
        }

    @classmethod
    def from_dict(cls, data):
        item = cls(data['text'])
        item.setPos(data['pos'][0], data['pos'][1])
        item.setZValue(data.get('z', 0))
        
        font = QFont(data['font']['family'], data['font']['size'])
        font.setBold(data['font']['bold'])
        font.setItalic(data['font']['italic'])
        item.setFont(font)
        
        item.setDefaultTextColor(QColor(data['color']))
        
        # Restore width & alignment
        text_width = data.get('text_width', -1)
        item.setTextWidth(text_width)
        
        # Restore fixed height
        fixed_height = data.get('fixed_height', -1)
        item._fixed_height = fixed_height
        
        # Restore vertical alignment
        item._vertical_alignment = data.get('vertical_alignment', 'top')
        
        align_int = data.get('alignment', int(Qt.AlignLeft))
        option = item.document().defaultTextOption()
        option.setAlignment(Qt.AlignmentFlag(align_int))
        item.document().setDefaultTextOption(option)
        
        if data.get('locked', False):
            item.set_locked(True)
        if not data.get('visible', True):
            item.setVisible(False)
            
        if 'letter_spacing' in data:
            item._letter_spacing = float(data['letter_spacing'])
        if 'line_height' in data:
            item._line_height = float(data['line_height'])
        if 'text_alignment' in data:
            item._text_alignment = Qt.AlignmentFlag(data['text_alignment'])
            
        if 'has_shadow' in data:
            item._has_shadow = data['has_shadow']
            color = QColor(data.get('shadow_color', '#000000'))
            color.setAlpha(data.get('shadow_color_alpha', 150))
            item._shadow_color = color
            item._shadow_blur = data.get('shadow_blur', 10.0)
            item._shadow_offset_x = data.get('shadow_offset_x', 5.0)
            item._shadow_offset_y = data.get('shadow_offset_y', 5.0)
            item.update_shadow()
            
        item._apply_text_formatting()
        
        return item

    def get_property(self, name):
        if name == "text": return self.toPlainText()
        if name == "font_family": return self.font().family()
        if name == "font_size": return self.font().pointSize()
        if name == "font_bold": return self.font().bold()
        if name == "font_italic": return self.font().italic()

        if name == "text_color": return self.defaultTextColor()
        if name == "width": return self.textWidth()
        if name == "fixed_height": return self._fixed_height if hasattr(self, '_fixed_height') else -1
        if name == "vertical_alignment": return self._vertical_alignment
        if name == "alignment":
            align = getattr(self, '_text_alignment', Qt.AlignLeft)
            if align == Qt.AlignRight: return "right"
            elif align == Qt.AlignHCenter: return "center"
            elif align == Qt.AlignJustify: return "justify"
            else: return "left"
        if name == "letter_spacing": return getattr(self, '_letter_spacing', 0.0)
        if name == "line_height": return getattr(self, '_line_height', 1.0)
        if name == "has_shadow": return self._has_shadow
        if name == "shadow_color": return self._shadow_color
        if name == "shadow_blur": return self._shadow_blur
        if name == "shadow_offset_x": return self._shadow_offset_x
        if name == "shadow_offset_y": return self._shadow_offset_y
        return None

    def set_property(self, name, value):
        import logging
        logging.debug(f"[DTPTextItem] set_property: name='{name}', value='{value}'")
        if name == "text":
            self.setPlainText(value)
            return
        font = self.font()
        if name == "font_family":
            font.setFamily(value)
            self.setFont(font)
        elif name == "font_size":
            font.setPointSize(value)
            self.setFont(font)
        elif name == "font_bold":
            font.setBold(value)
            self.setFont(font)
        elif name == "font_italic":
            font.setItalic(value)
            self.setFont(font)

        elif name == "alignment":
            if value == "left":
                self._text_alignment = Qt.AlignLeft
            elif value == "center":
                self._text_alignment = Qt.AlignHCenter
            elif value == "right":
                self._text_alignment = Qt.AlignRight
            elif value == "justify":
                self._text_alignment = Qt.AlignJustify
            self._apply_text_formatting()
            
            # If width is auto (-1), alignment is not visible. Snap to current width.
            if self.textWidth() == -1:
                self.setTextWidth(self.boundingRect().width())
        elif name == "vertical_alignment":
            self._vertical_alignment = value
            self.update()
        elif name == "width":
            self.setTextWidth(value)
        elif name == "fixed_height":
            self.prepareGeometryChange()
            self._fixed_height = value
            self.update_handles()
        elif name == "text_color":
            self.setDefaultTextColor(value)
        elif name == "has_shadow":
            self._has_shadow = value
            self.update_shadow()
        elif name == "shadow_color":
            self._shadow_color = QColor(value) if isinstance(value, str) else value
            self.update_shadow()
        elif name == "shadow_blur":
            self._shadow_blur = float(value)
            self.update_shadow()
        elif name == "shadow_offset_x":
            self._shadow_offset_x = float(value)
            self.update_shadow()
        elif name == "shadow_offset_y":
            self._shadow_offset_y = float(value)
            self.update_shadow()

class DTPImageItem(ConstrainedMoveMixin, ResizeMixin, ShadowMixin, QGraphicsPixmapItem):
    def __init__(self, pixmap, image_data=None):
        QGraphicsPixmapItem.__init__(self, pixmap)
        ConstrainedMoveMixin.__init__(self)
        self.init_shadow()
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsScenePositionChanges
        )
        self.locked = False
        self.setAcceptHoverEvents(True)
        self.handles = {}
        self._create_handles()
        self._update_handles()
        self._is_resizing = False

    def prepare_resize(self, handle):
        self._is_resizing = True
        self._resize_start_scale = self.scale()
        
    def end_resize(self, handle):
        self._is_resizing = False
        # Push undo command if scale changed
        if hasattr(self, '_resize_start_scale') and abs(self.scale() - self._resize_start_scale) > 0.001:
            if self.scene() and hasattr(self.scene(), 'undo_stack'):
                from commands import PropertyChangeCommand
                command = PropertyChangeCommand(self, "scale", self.scale())
                command.old_value = self._resize_start_scale
                self.scene().undo_stack.push(command)
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self._update_handles()
        if change == QGraphicsItem.ItemSelectedChange:
            for handle in self.handles.values():
                handle.setVisible(value and not self.locked)
        return super().itemChange(change, value)

    def set_locked(self, locked):
        self.locked = locked
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not locked)
        if locked:
            for handle in self.handles.values():
                handle.setVisible(False)
            self.setSelected(False)

    def _create_handles(self):
        # Top-Left, Top-Right, Bottom-Left, Bottom-Right
        self.handles['tl'] = ResizeHandle(self, Qt.SizeFDiagCursor)
        self.handles['tr'] = ResizeHandle(self, Qt.SizeBDiagCursor)
        self.handles['bl'] = ResizeHandle(self, Qt.SizeBDiagCursor)
        self.handles['br'] = ResizeHandle(self, Qt.SizeFDiagCursor)
        for handle in self.handles.values():
            handle.setVisible(False)

    def _update_handles(self):
        rect = self.boundingRect()
        offset = 4 # Half of handle size (8x8)
        
        w = rect.width()
        h = rect.height()
        
        self.handles['tl'].setPos(-offset, -offset)
        self.handles['tr'].setPos(w - offset, -offset)
        self.handles['bl'].setPos(-offset, h - offset)
        self.handles['br'].setPos(w - offset, h - offset)

    def handle_resize(self, handle, mouse_pos):
        # Apply strict snap to the target position
        target_pos = self.get_snapped_pos(mouse_pos)
             
        # mouse_pos is in scene coordinates
        local_pos = self.mapFromScene(target_pos)
        rect = self.pixmap().rect()
        
        if handle == self.handles['br']:
            w = rect.width()
            h = rect.height()
            
            if w == 0 or h == 0: return

            new_width_local = local_pos.x()
            new_height_local = local_pos.y()
            
            scale_x = new_width_local / w
            scale_y = new_height_local / h
            
            new_scale = max(0.1, min(scale_x, scale_y))
            
            new_scale = max(0.1, min(scale_x, scale_y))
            
            # Directly set scale during drag (undo handled in end_resize)
            self.setScale(new_scale)
            
            self._update_handles()
        
    def to_dict(self):
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice
        import base64
        
        # Encode pixmap to base64
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        self.pixmap().save(buffer, "PNG")
        base64_data = base64.b64encode(byte_array.data()).decode('utf-8')
        
        return {
            'type': 'image',
            'pos': (self.pos().x(), self.pos().y()),
            'scale': self.scale(),
            'opacity': self.opacity(),
            'z': self.zValue(),
            'data': base64_data,
            'locked': self.locked,
            'visible': self.isVisible()
        }

    @classmethod
    def from_dict(cls, data):
        import base64
        from PySide6.QtGui import QPixmap
        
        byte_data = base64.b64decode(data['data'])
        pixmap = QPixmap()
        pixmap.loadFromData(byte_data)
        
        item = cls(pixmap)
        item.setPos(data['pos'][0], data['pos'][1])
        item.setScale(data['scale'])
        item.setOpacity(data.get('opacity', 1.0))
        item.setZValue(data.get('z', 0))
        if data.get('locked', False):
            item.set_locked(True)
        if not data.get('visible', True):
            item.setVisible(False)
        return item

    def get_property(self, name):
        if name == "scale": return self.scale()
        if name == "opacity": return self.opacity()
        return None

    def set_property(self, name, value):
        if name == "scale": self.setScale(value)
        if name == "opacity": self.setOpacity(value)


class DTPShapeItem(ConstrainedMoveMixin, ResizeMixin, ShadowMixin, QGraphicsItem):
    """矩形・楕円・線を描画するアイテム（リサイズハンドル付き）"""
    SHAPE_RECT = 'rect'
    SHAPE_ELLIPSE = 'ellipse'
    SHAPE_LINE = 'line'
    
    def __init__(self, shape_type='rect', width=150, height=100):
        QGraphicsItem.__init__(self)
        ConstrainedMoveMixin.__init__(self)
        self.init_shadow()
        self.shape_type = shape_type
        self._width = width
        self._height = height
        self._fill_color = QColor(200, 220, 255, 100)
        self._border_color = QColor(0, 0, 0)
        self._border_width = 2.0
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsScenePositionChanges
        )
        self.locked = False
        self.setAcceptHoverEvents(True)
        
        # Resize handles
        self.handles = {}
        self._resize_start_width = None
        self._resize_start_height = None
        self._is_resizing = False
        self._resize_start_pos = None
        self._create_handles()
        self._update_handles()
    
    def _create_handles(self):
        self.handles['tl'] = ResizeHandle(self, Qt.SizeFDiagCursor)
        self.handles['tr'] = ResizeHandle(self, Qt.SizeBDiagCursor)
        self.handles['bl'] = ResizeHandle(self, Qt.SizeBDiagCursor)
        self.handles['br'] = ResizeHandle(self, Qt.SizeFDiagCursor)
        # Edge handles
        self.handles['t'] = ResizeHandle(self, Qt.SizeVerCursor)
        self.handles['b'] = ResizeHandle(self, Qt.SizeVerCursor)
        self.handles['l'] = ResizeHandle(self, Qt.SizeHorCursor)
        self.handles['r'] = ResizeHandle(self, Qt.SizeHorCursor)
        for handle in self.handles.values():
            handle.setVisible(False)
    
    def _update_handles(self):
        hs = 4  # half handle size
        w, h = self._width, self._height
        
        # ハンドル位置は (0,0) から (w,h) の矩形の四隅
        self.handles['tl'].setPos(-hs, -hs)
        self.handles['tr'].setPos(w - hs, -hs)
        self.handles['bl'].setPos(-hs, h - hs)
        self.handles['br'].setPos(w - hs, h - hs)
        self.handles['t'].setPos(w / 2 - hs, -hs)
        self.handles['b'].setPos(w / 2 - hs, h - hs)
        self.handles['l'].setPos(-hs, h / 2 - hs)
        self.handles['r'].setPos(w - hs, h / 2 - hs)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            for handle in self.handles.values():
                handle.setVisible(value and not self.locked)
        return super().itemChange(change, value)
        
    def set_locked(self, locked):
        self.locked = locked
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not locked)
        if locked:
            for handle in self.handles.values():
                handle.setVisible(False)
            self.setSelected(False)
    
    def handle_resize(self, handle, mouse_pos):
        # Apply strict snap to the target position
        target_pos = self.get_snapped_pos(mouse_pos)
             
        local = self.mapFromScene(target_pos)
        old_w, old_h = self._width, self._height
        
        # 1. Calculate Candidate Size (Unconstrained)
        cand_w = old_w
        cand_h = old_h
        
        if handle == self.handles['br']:
            cand_w = local.x()
            cand_h = local.y()
        elif handle == self.handles['r']:
            cand_w = local.x()
        elif handle == self.handles['b']:
            cand_h = local.y()
        elif handle == self.handles['tr']:
            cand_w = local.x()
            # tr: y moves top edge. Height change is old_h - y
            cand_h = old_h - local.y() 
        elif handle == self.handles['bl']:
            # bl: x moves left edge. Width change is old_w - x
            cand_w = old_w - local.x()
            cand_h = local.y()
        elif handle == self.handles['tl']:
            cand_w = old_w - local.x()
            cand_h = old_h - local.y()
        elif handle == self.handles['t']:
            cand_h = old_h - local.y()
        elif handle == self.handles['l']:
            cand_w = old_w - local.x()
        
        # 2. Apply Constraints (Shift)
        new_w = cand_w
        new_h = cand_h
        
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ShiftModifier and self._resize_start_width is not None:
             if self.shape_type == self.SHAPE_LINE:
                 # Angle Snap
                 import math
                 # Logic determines vector from Start(0,0) to End(w,h)?
                 # Actually, handle logic above computes 'new width/height' as if 
                 # we are dragging relative to the anchor point.
                 # E.g. for TL, anchor is BR. calculated w/h is vector from BR to TL (inverted).
                 # So we can just snap the vector (new_w, new_h).
                 
                 angle = math.atan2(new_h, new_w)
                 pi4 = math.pi / 4
                 snapped_angle = round(angle / pi4) * pi4
                 
                 dist = math.sqrt(new_w**2 + new_h**2)
                 new_w = dist * math.cos(snapped_angle)
                 new_h = dist * math.sin(snapped_angle)
                 
             else:
                 # Rect/Ellipse: Maintain Aspect Ratio
                 # Only for corner handles
                 if handle in [self.handles['tl'], self.handles['tr'], self.handles['bl'], self.handles['br']]:
                     start_w = self._resize_start_width
                     start_h = self._resize_start_height
                     if start_h != 0:
                         ratio = start_w / start_h
                         
                         # Determine driver dimension
                         # Use the one with larger relative change?
                         # Or just use X as driver?
                         # Let's use larger absolute value to avoid snapping to zero easily
                         if abs(new_w) > abs(new_h * ratio):
                             new_h = new_w / ratio
                         else:
                             new_w = new_h * ratio
        
        # 3. Minimum Size & Normalization
        if self.shape_type != self.SHAPE_LINE:
             if abs(new_w) < 1: new_w = 1 if new_w >=0 else -1
             if abs(new_h) < 1: new_h = 1 if new_h >=0 else -1
             
        # 4. Apply Geometry Change (Position) based on Handle Type
        # Calculate how much we need to move based on the finalized size change
        # Anchor point logic:
        # TL moves: Anchor is BR. Pos change = (old_w - new_w, old_h - new_h)
        # TR moves: Anchor is BL. Pos change = (0, old_h - new_h)
        # BL moves: Anchor is TR. Pos change = (old_w - new_w, 0)
        # BR moves: Anchor is TL. Pos change = (0, 0)
        # T moves: Anchor is Bottom. Pos change = (0, old_h - new_h)
        # L moves: Anchor is Right. Pos change = (old_w - new_w, 0)
        
        dx = 0
        dy = 0
        
        if handle in [self.handles['tl'], self.handles['l'], self.handles['bl']]:
             dx = old_w - new_w
        
        if handle in [self.handles['tl'], self.handles['t'], self.handles['tr']]:
             dy = old_h - new_h
             
        if dx != 0 or dy != 0:
            self.moveBy(dx, dy)

        self.prepareGeometryChange()
        self._width = new_w
        self._height = new_h
        self._update_handles()
        self.update()
    
    def prepare_resize(self, handle):
        self._is_resizing = True
        # リサイズ開始時のサイズを保存
        self._resize_start_width = self._width
        self._resize_start_height = self._height
        self._resize_start_pos = self.pos()

    def end_resize(self, handle):
        self._is_resizing = False
        # サイズが変わっていたら Undo コマンドを発行
        if (self._resize_start_width is not None and
            (self._resize_start_width != self._width or 
             self._resize_start_height != self._height)):
            if self.scene() and hasattr(self.scene(), 'undo_stack'):
                from commands import PropertyChangeCommand, MoveItemCommand
                stack = self.scene().undo_stack
                stack.beginMacro("図形リサイズ")
                
                # 位置が変わっていれば移動コマンドも push
                if self.pos() != self._resize_start_pos:
                    cmd_move = MoveItemCommand(self, self._resize_start_pos, self.pos())
                    stack.push(cmd_move)
                
                if self._resize_start_width != self._width:
                    cmd_w = PropertyChangeCommand(self, 'width', self._width)
                    cmd_w.old_value = self._resize_start_width
                    stack.push(cmd_w)
                    
                if self._resize_start_height != self._height:
                    cmd_h = PropertyChangeCommand(self, 'height', self._height)
                    cmd_h.old_value = self._resize_start_height
                    stack.push(cmd_h)
                    
                stack.endMacro()
        self._resize_start_width = None
        self._resize_start_height = None
        self._resize_start_pos = None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
    
    def boundingRect(self):
        pad = self._border_width / 2
        left = min(0, self._width)
        top = min(0, self._height)
        w = abs(self._width)
        h = abs(self._height)
        return QRectF(left - pad, top - pad, w + pad * 2, h + pad * 2)
    
    def paint(self, painter, option, widget=None):
        pen = QPen(self._border_color, self._border_width)
        painter.setPen(pen)
        
        if self.shape_type == self.SHAPE_LINE:
            painter.drawLine(0, 0, self._width, self._height)
        else:
            brush = QBrush(self._fill_color)
            painter.setBrush(brush)
            rect = QRectF(0, 0, self._width, self._height)
            if self.shape_type == self.SHAPE_RECT:
                painter.drawRect(rect)
            elif self.shape_type == self.SHAPE_ELLIPSE:
                painter.drawEllipse(rect)
        
        # Draw selection highlight
        if self.isSelected():
            pen = QPen(QColor(0, 120, 215), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(0, 0, self._width, self._height))
    
    def to_dict(self):
        return {
            'type': 'shape',
            'shape_type': self.shape_type,
            'pos': (self.pos().x(), self.pos().y()),
            'width': self._width,
            'height': self._height,
            'fill_color': self._fill_color.name(QColor.HexArgb),
            'border_color': self._border_color.name(QColor.HexArgb),
            'border_width': self._border_width,
            'z': self.zValue(),
            'locked': self.locked,
            'visible': self.isVisible(),
            'has_shadow': self._has_shadow,
            'shadow_color': self._shadow_color.name() if hasattr(self._shadow_color, 'name') else "#000000",
            'shadow_color_alpha': self._shadow_color.alpha(),
            'shadow_blur': self._shadow_blur,
            'shadow_offset_x': self._shadow_offset_x,
            'shadow_offset_y': self._shadow_offset_y
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(data['shape_type'], data['width'], data['height'])
        item.setPos(data['pos'][0], data['pos'][1])
        item._fill_color = QColor(data.get('fill_color', '#C8DCFF64'))
        item._border_color = QColor(data.get('border_color', '#000000'))
        item._border_width = data.get('border_width', 2.0)
        item.setZValue(data.get('z', 0))
        if data.get('locked', False):
            item.set_locked(True)
        if not data.get('visible', True):
            item.setVisible(False)
            
        if 'has_shadow' in data:
            item._has_shadow = data['has_shadow']
            color = QColor(data.get('shadow_color', '#000000'))
            color.setAlpha(data.get('shadow_color_alpha', 150))
            item._shadow_color = color
            item._shadow_blur = data.get('shadow_blur', 10.0)
            item._shadow_offset_x = data.get('shadow_offset_x', 5.0)
            item._shadow_offset_y = data.get('shadow_offset_y', 5.0)
            item.update_shadow()
            
        return item
    
    def get_property(self, name):
        if name == "width": return self._width
        if name == "height": return self._height
        if name == "fill_color": return self._fill_color
        if name == "border_color": return self._border_color
        if name == "border_width": return self._border_width
        if name == "has_shadow": return self._has_shadow
        if name == "shadow_color": return self._shadow_color
        if name == "shadow_blur": return self._shadow_blur
        if name == "shadow_offset_x": return self._shadow_offset_x
        if name == "shadow_offset_y": return self._shadow_offset_y
        return None
    
    def set_property(self, name, value):
        if name == "width":
            self._width = value
            self.prepareGeometryChange()
            self._update_handles()
        elif name == "height":
            self._height = value
            self.prepareGeometryChange()
            self._update_handles()
        elif name == "fill_color":
            self._fill_color = value
        elif name == "border_color":
            self._border_color = value
        elif name == "border_width":
            self._border_width = value
        elif name == "has_shadow":
            self._has_shadow = value
            self.update_shadow()
        elif name == "shadow_color":
            self._shadow_color = QColor(value) if isinstance(value, str) else value
            self.update_shadow()
        elif name == "shadow_blur":
            self._shadow_blur = float(value)
            self.update_shadow()
        elif name == "shadow_offset_x":
            self._shadow_offset_x = float(value)
            self.update_shadow()
        elif name == "shadow_offset_y":
            self._shadow_offset_y = float(value)
            self.update_shadow()
        self.update()


class DTPTableCell(QGraphicsTextItem):
    """表専用セル: focusOut時にUndoコマンドを発行"""
    def __init__(self, parent_table, row, col):
        super().__init__("", parent_table)
        self._table = parent_table
        self._row = row
        self._col = col
        self._original_text = ""
        self.setFont(QFont("Arial", 9))
        self.setDefaultTextColor(QColor(0, 0, 0))
        self.setTextInteractionFlags(Qt.NoTextInteraction)
    
    def focusInEvent(self, event):
        self._original_text = self.toPlainText()
        # 編集中のセルを視覚的に強調
        self._table.setFlag(QGraphicsItem.ItemIsMovable, False)
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        # 親テーブルの移動を再有効化
        self._table.setFlag(QGraphicsItem.ItemIsMovable, True)
        new_text = self.toPlainText()
        if new_text != self._original_text:
            self._table.notify_cell_changed(self._row, self._col, self._original_text, new_text)
        super().focusOutEvent(event)


class DTPTableItem(ConstrainedMoveMixin, ShadowMixin, QGraphicsItem):
    """表アイテム: DTPTableCell をセルとしてグリッド状に配置"""
    
    def __init__(self, rows=3, cols=3, cell_width=100, cell_height=30):
        QGraphicsItem.__init__(self)
        ConstrainedMoveMixin.__init__(self)
        self.init_shadow()
        self._rows = rows
        self._cols = cols
        self._cell_width = cell_width
        self._cell_height = cell_height
        
        # 可変サイズ用
        self._col_widths = [cell_width] * cols
        self._row_heights = [cell_height] * rows
        
        # スタイル設定
        self._fill_color = QColor(255, 255, 255, 0) # 透明
        self._border_color = QColor(0, 0, 0)
        self._border_width = 1.0
        self._header_color = QColor(220, 230, 245)
        
        self.cells = []
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsScenePositionChanges
        )
        self.locked = False
        self.setAcceptHoverEvents(True)
        
        # テキスト配置（デフォルトは左揃え）
        self._alignment = "left"
        
        # Resize handles
        self.handles = {}
        self._resize_start_cell_w = None
        self._resize_start_cell_h = None
        self._resize_start_pos = None
        self._resize_start_col_widths = None
        self._resize_start_row_heights = None
        
        # Interactive Resize State
        self._resizing_col = None
        self._resizing_row = None
        self._hover_col_border = None
        self._hover_row_border = None
        
        self._build_cells()
        self._create_handles()
        self._update_handles()
    
    def _build_cells(self):
        """セルを生成してグリッド状に配置"""
        # 既存セルを削除
        for row in self.cells:
            for cell in row:
                if cell.scene():
                    cell.scene().removeItem(cell)
        self.cells = []
        
        current_y = 0
        for r in range(self._rows):
            row_cells = []
            h = self._row_heights[r]
            current_x = 0
            for c in range(self._cols):
                w = self._col_widths[c]
                cell = DTPTableCell(self, r, c)
                # 微調整: 枠線が重ならないように +1, +2 など
                cell.setPos(current_x + 2, current_y + 1)
                cell.setTextWidth(w - 4)
                
                # 配置適用
                option = cell.document().defaultTextOption()
                if self._alignment == "center":
                    option.setAlignment(Qt.AlignHCenter)
                elif self._alignment == "right":
                    option.setAlignment(Qt.AlignRight)
                else:
                    option.setAlignment(Qt.AlignLeft)
                cell.document().setDefaultTextOption(option)
                
                row_cells.append(cell)
                current_x += w
            self.cells.append(row_cells)
            current_y += h
    
    def notify_cell_changed(self, row, col, old_text, new_text):
        """セルの内容変更をUndoスタックに通知"""
        if self.scene() and hasattr(self.scene(), 'undo_stack'):
            from commands import TableTextChangeCommand
            cmd = TableTextChangeCommand(self, row, col, old_text, new_text)
            self.scene().undo_stack.push(cmd)
            # Rebuild layout to recenter text if height changed
            self._rebuild_layout()
            
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            for handle in self.handles.values():
                handle.setVisible(value and not self.locked)
        return super().itemChange(change, value)
        
    def set_locked(self, locked):
        self.locked = locked
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setFlag(QGraphicsItem.ItemIsSelectable, not locked)
        if locked:
            for handle in self.handles.values():
                handle.setVisible(False)
            self.setSelected(False)
    
    def _create_handles(self):
        self.handles['tl'] = ResizeHandle(self, Qt.SizeFDiagCursor)
        self.handles['tr'] = ResizeHandle(self, Qt.SizeBDiagCursor)
        self.handles['bl'] = ResizeHandle(self, Qt.SizeBDiagCursor)
        self.handles['br'] = ResizeHandle(self, Qt.SizeFDiagCursor)
        # Edge handles
        self.handles['t'] = ResizeHandle(self, Qt.SizeVerCursor)
        self.handles['b'] = ResizeHandle(self, Qt.SizeVerCursor)
        self.handles['l'] = ResizeHandle(self, Qt.SizeHorCursor)
        self.handles['r'] = ResizeHandle(self, Qt.SizeHorCursor)
        for handle in self.handles.values():
            handle.setVisible(False)
            handle.setZValue(100) # Ensure on top of cells

    def _update_handles(self):
        w = sum(self._col_widths)
        h = sum(self._row_heights)
        
        self.handles['tl'].setPos(0, 0)
        self.handles['tr'].setPos(w, 0)
        self.handles['bl'].setPos(0, h)
        self.handles['br'].setPos(w, h)
        self.handles['t'].setPos(w / 2, 0)
        self.handles['b'].setPos(w / 2, h)
        self.handles['l'].setPos(0, h / 2)
        self.handles['r'].setPos(w, h / 2)

    def prepare_resize(self, handle):
        self._resize_start_w = sum(self._col_widths)
        self._resize_start_h = sum(self._row_heights)
        self._resize_start_col_widths = list(self._col_widths)
        self._resize_start_row_heights = list(self._row_heights)
        self._resize_start_pos = self.pos()

    def handle_resize(self, handle, mouse_pos):
        # Apply snap if enabled (Reuse ResizeMixin logic if inherited, but here logic is custom)
        # Actually DTPItem logic.
        target_pos = mouse_pos
        scene = self.scene()
        if scene:
             if hasattr(scene, 'snap_enabled') and scene.snap_enabled:
                 target_pos = scene.snap_to_grid(mouse_pos)
                 scene.clear_guides()
             elif hasattr(scene, 'smart_guides_enabled') and scene.smart_guides_enabled:
                 target_pos, guides = scene.snap_point_to_objects(mouse_pos, exclude_items=[self])
                 scene.active_guides = guides
                 scene.update()
             else:
                 scene.clear_guides()
        
        local = self.mapFromScene(target_pos)
        
        current_w = sum(self._col_widths)
        current_h = sum(self._row_heights)
        
        new_w = current_w
        new_h = current_h
        
        if handle == self.handles['br']:
            new_w = local.x()
            new_h = local.y()
        elif handle == self.handles['r']:
            new_w = local.x()
        elif handle == self.handles['b']:
            new_h = local.y()
        elif handle == self.handles['tr']:
            new_w = local.x()
            new_h = current_h - local.y()
            if new_h != current_h: self.moveBy(0, local.y())
        elif handle == self.handles['bl']:
            new_w = current_w - local.x()
            new_h = local.y()
            if new_w != current_w: self.moveBy(local.x(), 0)
        
        # Min Size
        min_w = self._cols * 5
        min_h = self._rows * 5
        if new_w < min_w: new_w = min_w
        if new_h < min_h: new_h = min_h
        
        # Scale
        if current_w > 0:
             scale_w = new_w / current_w
             if scale_w != 1.0:
                 self._col_widths = [w * scale_w for w in self._col_widths]
        
        if current_h > 0:
             scale_h = new_h / current_h
             if scale_h != 1.0:
                 self._row_heights = [h * scale_h for h in self._row_heights]

        # Sync legacy
        if self._cols > 0: self._cell_width = sum(self._col_widths) / self._cols
        if self._rows > 0: self._cell_height = sum(self._row_heights) / self._rows

        self.prepareGeometryChange()
        self._rebuild_layout()
        self._update_handles()
        self.update()

    def _rebuild_layout(self):
        """セルの位置を再計算（可変サイズ・垂直中央・アライメント適用）"""
        current_y = 0
        
        # Alignment flag mapping
        align_flag = Qt.AlignLeft
        if self._alignment == "center": align_flag = Qt.AlignHCenter
        elif self._alignment == "right": align_flag = Qt.AlignRight

        for r in range(self._rows):
            h = self._row_heights[r]
            current_x = 0
            for c in range(self._cols):
                w = self._col_widths[c]
                if r < len(self.cells) and c < len(self.cells[r]):
                    cell = self.cells[r][c]
                    # Alignment update
                    option = cell.document().defaultTextOption()
                    option.setAlignment(align_flag)
                    cell.document().setDefaultTextOption(option)
                    
                    cell.setTextWidth(w - 4)
                    
                    # Vertical center
                    doc_h = cell.document().size().height()
                    offset_y = (h - doc_h) / 2
                    if offset_y < 0: offset_y = 0
                    
                    cell.setPos(current_x + 2, current_y + offset_y)
                current_x += w
            current_y += h

    def end_resize(self, handle):
        # Resize finished (Outer resize)
        changed = False
        
        # Check against start state
        # We stored start state in prepare_resize (start_pos, start_col_widths, start_row_heights)
        # But wait, prepare_resize stores them.
        
        if hasattr(self, '_resize_start_col_widths') and self._resize_start_col_widths != self._col_widths:
            changed = True
        if hasattr(self, '_resize_start_row_heights') and self._resize_start_row_heights != self._row_heights:
             changed = True
             
        if changed and self.scene() and hasattr(self.scene(), 'undo_stack'):
            from commands import PropertyChangeCommand, MoveItemCommand
            stack = self.scene().undo_stack
            stack.beginMacro("テーブルリサイズ")
            
            if self.pos() != self._resize_start_pos:
                cmd_move = MoveItemCommand(self, self._resize_start_pos, self.pos())
                stack.push(cmd_move)
            
            if self._resize_start_col_widths != self._col_widths:
                cmd_w = PropertyChangeCommand(self, 'col_widths', list(self._col_widths))
                cmd_w.old_value = list(self._resize_start_col_widths)
                stack.push(cmd_w)
                
            if self._resize_start_row_heights != self._row_heights:
                cmd_h = PropertyChangeCommand(self, 'row_heights', list(self._row_heights))
                cmd_h.old_value = list(self._resize_start_row_heights)
                stack.push(cmd_h)
                
            stack.endMacro()
        
        self._resize_start_pos = None
        self._resize_start_col_widths = None
        self._resize_start_row_heights = None

    def hoverMoveEvent(self, event):
        pos = event.pos()
        x, y = pos.x(), pos.y()
        
        # Check vertical lines (col resize)
        current_x = 0
        self._hover_col_border = None
        for i in range(self._cols - 1): # Last border is item edge? No, handled by transform handles.
            current_x += self._col_widths[i]
            if abs(x - current_x) <= 3: # Tolerance
                self.setCursor(Qt.SplitHCursor)
                self._hover_col_border = i
                return

        # Check horizontal lines (row resize)
        current_y = 0
        self._hover_row_border = None
        for i in range(self._rows - 1):
            current_y += self._row_heights[i]
            if abs(y - current_y) <= 3:
                self.setCursor(Qt.SplitVCursor)
                self._hover_row_border = i
                return
        
        # Reset if no hover
        self.setCursor(Qt.ArrowCursor)
        self._hover_col_border = None
        self._hover_row_border = None
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._hover_col_border is not None:
                self._resizing_col = self._hover_col_border
                self._resize_start_pos = event.pos() # Generic usage
                event.accept()
                return
            elif self._hover_row_border is not None:
                self._resizing_row = self._hover_row_border
                self._resize_start_pos = event.pos()
                event.accept()
                return
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing_col is not None:
            # Resize Col i
            # New width = mouse x - start of col i
            # Find start x of col i
            current_x = 0
            for k in range(self._resizing_col):
                current_x += self._col_widths[k]
            
            new_w = event.pos().x() - current_x
            if new_w < 10: new_w = 10 # Min width
            
            self._col_widths[self._resizing_col] = new_w
            self.prepareGeometryChange()
            self._rebuild_layout()
            self._update_handles()
            self.update()
            return
            
        elif self._resizing_row is not None:
            # Resize Row i
            current_y = 0
            for k in range(self._resizing_row):
                current_y += self._row_heights[k]
            
            new_h = event.pos().y() - current_y
            if new_h < 10: new_h = 10
            
            self._row_heights[self._resizing_row] = new_h
            self.prepareGeometryChange()
            self._rebuild_layout()
            self._update_handles()
            self.update()
            return
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing_col is not None:
             # Check if width changed
             if self._resize_start_col_widths and self._col_widths != self._resize_start_col_widths:
                 if self.scene() and hasattr(self.scene(), 'undo_stack'):
                     from commands import PropertyChangeCommand
                     cmd = PropertyChangeCommand(self, 'col_widths', list(self._col_widths))
                     # Hack: Manually set old_value because we modified inplace before command creation?
                     # No, PropertyChangeCommand captures old_value via get_property.
                     # But get_property returns CURRENT value which is already modified!
                     # So we must manually set old_value on the command.
                     cmd.old_value = list(self._resize_start_col_widths)
                     self.scene().undo_stack.push(cmd)
             
             self._resizing_col = None
             self.setCursor(Qt.ArrowCursor)
             return

        if self._resizing_row is not None:
             if self._resize_start_row_heights and self._row_heights != self._resize_start_row_heights:
                 if self.scene() and hasattr(self.scene(), 'undo_stack'):
                     from commands import PropertyChangeCommand
                     cmd = PropertyChangeCommand(self, 'row_heights', list(self._row_heights))
                     cmd.old_value = list(self._resize_start_row_heights)
                     self.scene().undo_stack.push(cmd)

             self._resizing_row = None
             self.setCursor(Qt.ArrowCursor)
             return

        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """ダブルクリック: 該当セルのテキスト編集モードに入る"""
        local = event.pos()
        x, y = local.x(), local.y()
        
        # Find Col
        col = -1
        current_x = 0
        for i, w in enumerate(self._col_widths):
             if current_x <= x < current_x + w:
                 col = i
                 break
             current_x += w
             
        # Find Row
        row = -1
        current_y = 0
        for i, h in enumerate(self._row_heights):
             if current_y <= y < current_y + h:
                 row = i
                 break
             current_y += h
        
        if 0 <= row < self._rows and 0 <= col < self._cols:
            cell = self.cells[row][col]
            cell.setTextInteractionFlags(Qt.TextEditorInteraction)
            cell.setFocus()
        else:
            super().mouseDoubleClickEvent(event)
    
    def boundingRect(self):
        w = sum(self._col_widths)
        h = sum(self._row_heights)
        return QRectF(0, 0, w, h)
    
    def paint(self, painter, option, widget=None):
        total_w = sum(self._col_widths)
        total_h = sum(self._row_heights)
        
        # 背景色（塗りつぶし）
        if self._fill_color.alpha() > 0:
            painter.setBrush(QBrush(self._fill_color))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(0, 0, total_w, total_h))
            
        # ヘッダー行の背景（ヘッダーがある場合）
        if self._rows > 0 and self._header_color.alpha() > 0:
            h = self._row_heights[0]
            painter.setBrush(QBrush(self._header_color))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(0, 0, total_w, h))
        
        # 罫線
        pen = QPen(self._border_color, self._border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # 外枠
        painter.drawRect(QRectF(0, 0, total_w, total_h))
        
        # 横線
        current_y = 0
        for r in range(self._rows - 1):
             current_y += self._row_heights[r]
             painter.drawLine(0, int(current_y), int(total_w), int(current_y))
        
        # 縦線
        current_x = 0
        for c in range(self._cols - 1):
             current_x += self._col_widths[c]
             painter.drawLine(int(current_x), 0, int(current_x), int(total_h))
        
        # 選択ハイライト
        if self.isSelected():
            pen = QPen(QColor(0, 120, 215), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(QRectF(0, 0, total_w, total_h))
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        pos = event.pos()
        
        # Find row/col
        col = -1
        current_x = 0
        for i, w in enumerate(self._col_widths):
             if current_x <= pos.x() < current_x + w:
                 col = i
                 break
             current_x += w
             
        row = -1
        current_y = 0
        for i, h in enumerate(self._row_heights):
             if current_y <= pos.y() < current_y + h:
                 row = i
                 break
             current_y += h
             
        if 0 <= row < self._rows:
            menu.addAction("Insert Row Above", lambda: self.insert_row(row))
            menu.addAction("Insert Row Below", lambda: self.insert_row(row + 1))
            menu.addAction("Delete Row", lambda: self.delete_row(row))
            menu.addSeparator()
            
        if 0 <= col < self._cols:
            menu.addAction("Insert Column Left", lambda: self.insert_col(col))
            menu.addAction("Insert Column Right", lambda: self.insert_col(col + 1))
            menu.addAction("Delete Column", lambda: self.delete_col(col))
            menu.addSeparator()

        menu.addAction("Distribute Rows Evenly", self.distribute_rows)
        menu.addAction("Distribute Cols Evenly", self.distribute_cols)
            
        menu.exec(event.screenPos())

    def insert_row(self, index):
        self._rows += 1
        self._row_heights.insert(index, self._cell_height) # Default height
        
        row_cells = []
        for c in range(self._cols):
             cell = DTPTableCell(self, index, c) # Row index will be fixed in rebuild
             row_cells.append(cell)
        self.cells.insert(index, row_cells)
        
        self.prepareGeometryChange()
        self._rebuild_layout()
        self._update_handles()
        self.update()

    def delete_row(self, index):
        if self._rows <= 1: return
        self._rows -= 1
        del self._row_heights[index]
        
        # Remove items from scene
        for cell in self.cells[index]:
            if cell.scene():
                cell.scene().removeItem(cell)
        del self.cells[index]
        
        self.prepareGeometryChange()
        self._rebuild_layout()
        self._update_handles()
        self.update()

    def insert_col(self, index):
        self._cols += 1
        self._col_widths.insert(index, self._cell_width)
        
        for r in range(self._rows):
            cell = DTPTableCell(self, r, index)
            self.cells[r].insert(index, cell)
            
        self.prepareGeometryChange()
        self._rebuild_layout()
        self._update_handles()
        self.update()

    def delete_col(self, index):
        if self._cols <= 1: return
        self._cols -= 1
        del self._col_widths[index]
        
        for r in range(self._rows):
            cell = self.cells[r][index]
            if cell.scene():
                cell.scene().removeItem(cell)
            del self.cells[r][index]
            
        self.prepareGeometryChange()
        self._rebuild_layout()
        self._update_handles()
        self.update()

    def distribute_rows(self):
        avg_h = sum(self._row_heights) / self._rows
        self._row_heights = [avg_h] * self._rows
        self.prepareGeometryChange()
        self._rebuild_layout()
        self._update_handles()
        self.update()

    def distribute_cols(self):
        avg_w = sum(self._col_widths) / self._cols
        self._col_widths = [avg_w] * self._cols
        self.prepareGeometryChange()
        self._rebuild_layout()
        self._update_handles()
        self.update()

    def set_property(self, name, value):
        if name in ("rows", "cols"):
            # 現在のデータを退避
            old_data = [[c.toPlainText() for c in row] for row in self.cells]
            if name == "rows":
                self._rows = value
                # Resize Heights list
                if len(self._row_heights) < self._rows:
                    self._row_heights.extend([self._cell_height] * (self._rows - len(self._row_heights)))
                elif len(self._row_heights) > self._rows:
                    self._row_heights = self._row_heights[:self._rows]
            else:
                self._cols = value
                # Resize Widths list
                if len(self._col_widths) < self._cols:
                    self._col_widths.extend([self._cell_width] * (self._cols - len(self._col_widths)))
                elif len(self._col_widths) > self._cols:
                    self._col_widths = self._col_widths[:self._cols]
            
            self._build_cells()
            # 可能な限りデータを復元
            for r in range(min(len(old_data), self._rows)):
                for c in range(min(len(old_data[r]), self._cols)):
                    self.cells[r][c].setPlainText(old_data[r][c])
            
            self.prepareGeometryChange()
            self._rebuild_layout()
            self._update_handles()
        elif name == 'cell_width':
            self._cell_width = value
            self._col_widths = [value] * self._cols
            self.prepareGeometryChange()
            self._rebuild_layout()
            self._update_handles()
        elif name == 'cell_height':
            self._cell_height = value
            self._row_heights = [value] * self._rows
            self.prepareGeometryChange()
            self._rebuild_layout()
            self._update_handles()
        elif name == 'col_widths':
            self._col_widths = list(value)
            if self._cols > 0: self._cell_width = sum(self._col_widths) / self._cols
            self.prepareGeometryChange()
            self._rebuild_layout()
            self._update_handles()
        elif name == 'row_heights':
            self._row_heights = list(value)
            if self._rows > 0: self._cell_height = sum(self._row_heights) / self._rows
            self.prepareGeometryChange()
            self._rebuild_layout()
            self._update_handles()
        elif name == 'fill_color':
             self._fill_color = value
        elif name == 'border_color':
             self._border_color = value
        elif name == 'border_width':
             self._border_width = value
        elif name == 'header_color':
             self._header_color = value
        elif name == 'alignment':
             self._alignment = value
             # _rebuild_layout now handles alignment application
             self.prepareGeometryChange()
             self._rebuild_layout()
        
        self.update()

    def get_property(self, name):
        if name == "rows": return self._rows
        if name == "cols": return self._cols
        if name == "cell_width": return self._cell_width
        if name == "cell_height": return self._cell_height
        if name == "col_widths": return list(self._col_widths)
        if name == "row_heights": return list(self._row_heights)
        if name == "fill_color": return self._fill_color
        if name == "border_color": return self._border_color
        if name == "border_width": return self._border_width
        if name == "header_color": return self._header_color
        if name == "alignment": return self._alignment
        return None

    def to_dict(self):
        cell_data = []
        for r in range(self._rows):
            row_data = []
            for c in range(self._cols):
                row_data.append(self.cells[r][c].toPlainText())
            cell_data.append(row_data)
        
        return {
            'type': 'table',
            'pos': (self.pos().x(), self.pos().y()),
            'rows': self._rows,
            'cols': self._cols,
            'cell_width': self._cell_width,
            'cell_height': self._cell_height,
            'fill_color': self._fill_color.name(QColor.HexArgb),
            'border_color': self._border_color.name(QColor.HexArgb),
            'border_width': self._border_width,
            'header_color': self._header_color.name(QColor.HexArgb),
            'alignment': self._alignment,
            'col_widths': self._col_widths,
            'row_heights': self._row_heights,
            'cell_data': cell_data,
            'z': self.zValue()
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(data['rows'], data['cols'], data['cell_width'], data['cell_height'])
        item.setPos(data['pos'][0], data['pos'][1])
        
        # カラー復元（HexArgb対応）
        fill = data.get('fill_color', '#00FFFFFF')
        item._fill_color = QColor(fill)
        
        border = data.get('border_color', '#000000')
        item._border_color = QColor(border)
        
        item._border_width = data.get('border_width', 1.0)
        
        header = data.get('header_color', '#DCE6F5')
        item._header_color = QColor(header)
        
        item._alignment = data.get('alignment', 'left')
        
        item.setZValue(data.get('z', 0))
        
        item._col_widths = data.get('col_widths', [data['cell_width']] * data['cols'])
        item._row_heights = data.get('row_heights', [data['cell_height']] * data['rows'])
        
        # Ensure list lengths match rows/cols (in case of data mismatch)
        if len(item._col_widths) != item._cols:
             item._col_widths = [data['cell_width']] * item._cols
        if len(item._row_heights) != item._rows:
             item._row_heights = [data['cell_height']] * item._rows
             
        cell_data = data.get('cell_data', [])
        for r in range(min(len(cell_data), item._rows)):
            for c in range(min(len(cell_data[r]), item._cols)):
                item.cells[r][c].setPlainText(cell_data[r][c])
        
        return item

class DTPGroupItem(ConstrainedMoveMixin, ShadowMixin, QGraphicsItemGroup):
    """複数アイテムをまとめるグループアイテム"""
    def __init__(self, items_to_group=None):
        QGraphicsItemGroup.__init__(self)
        ConstrainedMoveMixin.__init__(self)
        self.init_shadow()
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsScenePositionChanges
        )
        self.handles = {}
        self._create_handles()
        
        if items_to_group:
            for item in items_to_group:
                # `addToGroup` in Qt keeps scene transform
                self.addToGroup(item)
                
        self._update_handles()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            for handle in self.handles.values():
                handle.setVisible(value)
                
            # Update bounds just in case
            if value:
                self._update_handles()
        return super().itemChange(change, value)

    def _create_handles(self):
        # グループ用のリサイズハンドル（見た目のみ、リサイズ機能は将来拡張用）
        self.handles['tl'] = ResizeHandle(self, Qt.SizeFDiagCursor)
        self.handles['tr'] = ResizeHandle(self, Qt.SizeBDiagCursor)
        self.handles['bl'] = ResizeHandle(self, Qt.SizeBDiagCursor)
        self.handles['br'] = ResizeHandle(self, Qt.SizeFDiagCursor)
        for handle in self.handles.values():
            handle.setVisible(False)
            handle.setZValue(100)

    def _update_handles(self):
        rect = self.boundingRect()
        self.handles['tl'].setPos(rect.topLeft())
        self.handles['tr'].setPos(rect.topRight())
        self.handles['bl'].setPos(rect.bottomLeft())
        self.handles['br'].setPos(rect.bottomRight())

    def paint(self, painter, option, widget=None):
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 120, 215), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())
        # QGraphicsItemGroup normally does not paint anything
        super().paint(painter, option, widget)

    def to_dict(self):
        children_data = []
        for child in self.childItems():
            if isinstance(child, ResizeHandle):
                continue
            if hasattr(child, 'to_dict'):
                children_data.append(child.to_dict())
                
        return {
            'type': 'group',
            'pos': (self.pos().x(), self.pos().y()),
            'z': self.zValue(),
            'children': children_data,
            'scale': self.scale(),
            'locked': self.locked,
            'visible': self.isVisible(),
            'has_shadow': self._has_shadow,
            'shadow_color': self._shadow_color.name() if hasattr(self._shadow_color, 'name') else "#000000",
            'shadow_color_alpha': self._shadow_color.alpha(),
            'shadow_blur': self._shadow_blur,
            'shadow_offset_x': self._shadow_offset_x,
            'shadow_offset_y': self._shadow_offset_y
        }
        
    @classmethod
    def from_dict(cls, data):
        group = cls()
        group.setPos(data['pos'][0], data['pos'][1])
        group.setZValue(data.get('z', 0))
        group.setScale(data.get('scale', 1.0))
        
        # Deferred import avoids circular dependency issues
        from items import DTPTextItem, DTPImageItem, DTPShapeItem, DTPTableItem
        
        for child_data in data.get('children', []):
            t = child_data.get('type')
            item = None
            if t == 'text': item = DTPTextItem.from_dict(child_data)
            elif t == 'image': item = DTPImageItem.from_dict(child_data)
            elif t == 'shape': item = DTPShapeItem.from_dict(child_data)
            elif t == 'table': item = DTPTableItem.from_dict(child_data)
            elif t == 'group': item = cls.from_dict(child_data)
            
            if item:
                # setParentItem retains local pos as set by from_dict
                item.setParentItem(group)
                
        group._update_handles()
        if data.get('locked', False):
            group.set_locked(True)
        if not data.get('visible', True):
            group.setVisible(False)
            
        if 'has_shadow' in data:
            group._has_shadow = data['has_shadow']
            color = QColor(data.get('shadow_color', '#000000'))
            color.setAlpha(data.get('shadow_color_alpha', 150))
            group._shadow_color = color
            group._shadow_blur = data.get('shadow_blur', 10.0)
            group._shadow_offset_x = data.get('shadow_offset_x', 5.0)
            group._shadow_offset_y = data.get('shadow_offset_y', 5.0)
            group.update_shadow()
            
        return group
