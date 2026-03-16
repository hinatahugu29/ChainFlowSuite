from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QApplication
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPdfWriter, QPageLayout, QPageSize, QPixmap
from items import DTPTextItem, DTPImageItem, DTPShapeItem, DTPTableItem
import os

class DTPScene(QGraphicsScene):
    PAGE_SIZES = {
        'A3':      (297, 420),
        'A4':      (210, 297),
        'A5':      (148, 210),
        'B5':      (176, 250),
        'Letter':  (216, 279),
        'Legal':   (216, 356),
    }
    
    def __init__(self, parent=None, undo_stack=None):
        super().__init__(parent)
        self.undo_stack = undo_stack
        self._page_name = 'A4'
        self._landscape = False
        self._printing = False # 印刷中フラグ（グリッド非表示用）
        self.snap_enabled = False
        self.grid_size = 20
        self.smart_guides_enabled = True
        self.snap_threshold = 8
        self.active_guides = []
        
        w_mm, h_mm = self.PAGE_SIZES['A4']
        self._set_page_dimensions(w_mm, h_mm)
    
    def _set_page_dimensions(self, w_mm, h_mm):
        """mmからピクセルに変換してページサイズを設定"""
        dpi = 96
        self._w_px = w_mm / 25.4 * dpi
        self._h_px = h_mm / 25.4 * dpi
        
        # 用紙サイズをシーンサイズとする（シンプル構成）
        # 余白やペーストボードの実装は、まず用紙が見えるようにしてから検討
        self.setSceneRect(0, 0, self._w_px, self._h_px)
    
    def set_page_size(self, name, landscape=False):
        """ページサイズを変更"""
        if name in self.PAGE_SIZES:
            self._page_name = name
            self._landscape = landscape
            w_mm, h_mm = self.PAGE_SIZES[name]
            if landscape:
                w_mm, h_mm = h_mm, w_mm
            self._set_page_dimensions(w_mm, h_mm)
            self.update()
    
    def snap_to_grid(self, pos):
        """位置をグリッドにスナップ"""
        if not self.snap_enabled:
            return pos
        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size
        return QPointF(x, y)
    
    def calculate_snap(self, moving_item, new_pos):
        """移動中アイテムのスナップ位置とガイド線を計算"""
        guides = []
        snapped_x = new_pos.x()
        snapped_y = new_pos.y()
        
        # 移動中アイテムの矩形（new_posを適用した場合）
        moving_rect = moving_item.boundingRect()
        
        # オフセット（(0,0)からの相対座標）
        off_left = moving_rect.left()
        off_right = moving_rect.right()
        off_cx = moving_rect.center().x()
        off_top = moving_rect.top()
        off_bottom = moving_rect.bottom()
        off_cy = moving_rect.center().y()
        
        m_left = new_pos.x() + off_left
        m_right = new_pos.x() + off_right
        m_cx = new_pos.x() + off_cx
        m_top = new_pos.y() + off_top
        m_bottom = new_pos.y() + off_bottom
        m_cy = new_pos.y() + off_cy

        found_x = False
        found_y = False
        threshold = self.snap_threshold
        
        # ページ境界もスナップ対象に
        page_rect = self.sceneRect()
        target_edges_x = [
            (page_rect.left(), "page_left"),
            (page_rect.right(), "page_right"),
            (page_rect.center().x(), "page_cx"),
        ]
        target_edges_y = [
            (page_rect.top(), "page_top"),
            (page_rect.bottom(), "page_bottom"),
            (page_rect.center().y(), "page_cy"),
        ]
        
        from items import ResizeHandle
        for item in self.items():
            if item is moving_item or item.parentItem() is not None:
                continue
            if isinstance(item, ResizeHandle):
                continue
                
            rect = item.sceneBoundingRect()
            target_edges_x.append((rect.left(), "left"))
            target_edges_x.append((rect.right(), "right"))
            target_edges_x.append((rect.center().x(), "cx"))
            target_edges_y.append((rect.top(), "top"))
            target_edges_y.append((rect.bottom(), "bottom"))
            target_edges_y.append((rect.center().y(), "cy"))
        
        # X軸スナップ
        my_edges_x = [
            (m_left, "left", off_left),
            (m_right, "right", off_right),
            (m_cx, "cx", off_cx),
        ]
        
        best_dx = threshold + 1
        best_snap_x_info = None
        
        for my_val, my_name, my_offset in my_edges_x:
            for target_val, target_name in target_edges_x:
                diff = abs(my_val - target_val)
                if diff < best_dx:
                    best_dx = diff
                    best_snap_x_info = (target_val, my_offset, target_val)
        
        if best_dx <= threshold and best_snap_x_info:
            target_val, my_offset, guide_x = best_snap_x_info
            snapped_x = target_val - my_offset
            guides.append(QLineF(guide_x, page_rect.top(), guide_x, page_rect.bottom()))
            found_x = True
        
        # Y軸スナップ
        my_edges_y = [
            (m_top, "top", off_top),
            (m_bottom, "bottom", off_bottom),
            (m_cy, "cy", off_cy),
        ]
        
        best_dy = threshold + 1
        best_snap_y_info = None
        
        for my_val, my_name, my_offset in my_edges_y:
            for target_val, target_name in target_edges_y:
                diff = abs(my_val - target_val)
                if diff < best_dy:
                    best_dy = diff
                    best_snap_y_info = (target_val, my_offset, target_val)
        
        if best_dy <= threshold and best_snap_y_info:
            target_val, my_offset, guide_y = best_snap_y_info
            snapped_y = target_val - my_offset
            guides.append(QLineF(page_rect.left(), guide_y, page_rect.right(), guide_y))
            found_y = True
        
        return QPointF(snapped_x, snapped_y), guides
    
    def clear_guides(self):
        """ガイド線をクリア"""
        if self.active_guides:
            self.active_guides = []
            self.update()

    def snap_point_to_objects(self, point, exclude_items=None):
        """指定した1点 (point) を他のオブジェクトの境界線や中心にスナップさせる"""
        if exclude_items is None:
            exclude_items = []
            
        guides = []
        snapped_x = point.x()
        snapped_y = point.y()
        
        threshold = self.snap_threshold
        found_x = False
        found_y = False
        
        # 1. ページ境界
        page_rect = self.sceneRect()
        target_edges_x = [
            (page_rect.left(), "page_left"),
            (page_rect.right(), "page_right"),
            (page_rect.center().x(), "page_cx"),
        ]
        target_edges_y = [
            (page_rect.top(), "page_top"),
            (page_rect.bottom(), "page_bottom"),
            (page_rect.center().y(), "page_cy"),
        ]
        
        # 2. 他のアイテム境界
        from items import ResizeHandle
        for item in self.items():
            if item in exclude_items or item.parentItem() is not None:
                continue
            if isinstance(item, ResizeHandle):
                continue
                
            rect = item.sceneBoundingRect()
            target_edges_x.append((rect.left(), "left"))
            target_edges_x.append((rect.right(), "right"))
            target_edges_x.append((rect.center().x(), "cx"))
            target_edges_y.append((rect.top(), "top"))
            target_edges_y.append((rect.bottom(), "bottom"))
            target_edges_y.append((rect.center().y(), "cy"))
            
        # X軸スナップ判定 (point.x vs targets)
        best_dx = threshold + 1
        best_target_x = None
        
        for tx, tname in target_edges_x:
            diff = abs(point.x() - tx)
            if diff < best_dx:
                best_dx = diff
                best_target_x = tx
        
        if best_dx <= threshold and best_target_x is not None:
            snapped_x = best_target_x
            guides.append(QLineF(snapped_x, page_rect.top(), snapped_x, page_rect.bottom()))
            found_x = True
            
        # Y軸スナップ判定 (point.y vs targets)
        best_dy = threshold + 1
        best_target_y = None
        
        for ty, tname in target_edges_y:
            diff = abs(point.y() - ty)
            if diff < best_dy:
                best_dy = diff
                best_target_y = ty
                
        if best_dy <= threshold and best_target_y is not None:
            snapped_y = best_target_y
            guides.append(QLineF(page_rect.left(), snapped_y, page_rect.right(), snapped_y))
            found_y = True
            
        return QPointF(snapped_x, snapped_y), guides
    
    def drawBackground(self, painter, rect):
        # シンプルに用紙だけを描画する。背景（地の底）はQGraphicsViewの設定に任せる。
        
        page_rect = QRectF(0, 0, self._w_px, self._h_px)
        
        painter.save()
        
        # Shadow (Paper shadow) - PDFエクスポート時は描画したくないかも？
        # export時は背景全体を描画しない方がいい場合も。
        # 今回は Border の制御のみ。
        
        if getattr(self, '_exporting_border', None) is None:
            # Normal View
            shadow_rect = page_rect.translated(8, 8)
            painter.fillRect(shadow_rect, QColor(0, 0, 0, 60))

        # Paper (White)
        painter.fillRect(page_rect, Qt.white)
        
        # Border
        draw_border = True
        if getattr(self, '_exporting_border', None) is not None:
             draw_border = self._exporting_border
        
        if draw_border:
            painter.setPen(QPen(Qt.black, 0)) # Cosmetic border
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(page_rect)
        
        painter.restore()
    
    def drawForeground(self, painter, rect):
        """スマートスナップガイド線とオーバーレイグリッドを描画"""
        super().drawForeground(painter, rect)
        
        painter.save()
        
        # 1. Overlay Grid (Itemsの下ではなく上に描画)
        draw_grid = False
        if getattr(self, '_exporting_grid', None) is not None:
            draw_grid = self._exporting_grid
        else:
            # Normal View logic: Visible if snap enabled and not printing (printing flag is separate)
            if self.snap_enabled and not self._printing:
                draw_grid = True
        
        if draw_grid:
            # 少し透明な青みがかったグレーで見やすくする
            grid_pen = QPen(QColor(100, 100, 150, 100), 0)
            grid_pen.setCosmetic(True)
            painter.setPen(grid_pen)
            
            x = 0
            while x <= self._w_px:
                painter.drawLine(QLineF(x, 0, x, self._h_px))
                x += self.grid_size
                
            y = 0
            while y <= self._h_px:
                painter.drawLine(QLineF(0, y, self._w_px, y))
                y += self.grid_size

        # 2. Smart Snap Guides
        if self.active_guides and not self._printing:
            pen = QPen(QColor(0, 120, 215), 1, Qt.DashLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            for line in self.active_guides:
                painter.drawLine(line)
                
        painter.restore()
    

    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            from commands import RemoveItemCommand
            items = self.selectedItems()
            if items and self.undo_stack:
                self.undo_stack.beginMacro("Delete Items")
                for item in items:
                    if item.parentItem() is None:
                        cmd = RemoveItemCommand(self, item)
                        self.undo_stack.push(cmd)
                self.undo_stack.endMacro()
        elif event.key() == Qt.Key_BracketRight:
            # ] key: Bring to front
            self.bring_to_front()
        elif event.key() == Qt.Key_BracketLeft:
            # [ key: Send to back
            self.send_to_back()
        else:
            super().keyPressEvent(event)
    
    def export_pdf(self, file_path, draw_grid=False, draw_border=True):
        self.clearSelection()
        
        page_rect = self.sceneRect()
        w_mm = page_rect.width() / 96 * 25.4
        h_mm = page_rect.height() / 96 * 25.4
        
        page_size = QPageSize(QPageSize.PageSizeId.A4)
        
        for name, (pw, ph) in self.PAGE_SIZES.items():
            exp_w, exp_h = pw, ph
            if self._landscape:
                exp_w, exp_h = ph, pw
            if abs(w_mm - exp_w) < 1 and abs(h_mm - exp_h) < 1:
                size_map = {
                    'A3': QPageSize.PageSizeId.A3,
                    'A4': QPageSize.PageSizeId.A4,
                    'A5': QPageSize.PageSizeId.A5,
                    'B5': QPageSize.PageSizeId.B5,
                    'Letter': QPageSize.PageSizeId.Letter,
                    'Legal': QPageSize.PageSizeId.Legal,
                }
                # Try to get the mapped size
                mapped = size_map.get(name)
                if mapped:
                    page_size = QPageSize(mapped)
                break
        
        writer = QPdfWriter(file_path)
        writer.setPageSize(page_size)
        
        if self._landscape:
            writer.setPageLayout(QPageLayout(page_size, QPageLayout.Landscape, 
                                             writer.pageLayout().margins()))
        
        writer.setPageMargins(writer.pageLayout().margins())
        
        painter = QPainter(writer)
        
        # Scale to fit
        target_rect = writer.pageLayout().paintRectPixels(writer.resolution())
        sx = target_rect.width() / page_rect.width()
        sy = target_rect.height() / page_rect.height()
        scale = min(sx, sy)
        painter.scale(scale, scale)
        
        # Hide guides temporarily, set export flags
        old_guides = self.active_guides
        self.active_guides = []
        self._exporting_grid = draw_grid
        self._exporting_border = draw_border
        
        self.render(painter, QRectF(page_rect), page_rect)
        
        self.active_guides = old_guides
        self._exporting_grid = None
        self._exporting_border = None
        painter.end()
        
    def export_image(self, file_path, dpi=300, draw_grid=False, draw_border=False):
        self.clearSelection()
        
        page_rect = self.sceneRect()
        
        # Calculate pixel size based on DPI (Qt default DPI is 96)
        scale = dpi / 96.0
        width = int(page_rect.width() * scale)
        height = int(page_rect.height() * scale)
        
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtCore import Qt, QRectF
        
        # Create high resolution image
        image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent) # DTP background handled by drawBackground
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Hide guides temporarily, set export flags
        old_guides = self.active_guides
        self.active_guides = []
        self._exporting_grid = draw_grid
        self._exporting_border = draw_border
        
        # Render the scene
        self.render(painter, QRectF(0, 0, width, height), page_rect)
        
        self.active_guides = old_guides
        self._exporting_grid = None
        self._exporting_border = None
        painter.end()
        
        image.save(file_path)
    
    def bring_to_front(self):
        items = self.selectedItems()
        if not items:
            return
            
        from items import ResizeHandle
        all_items = [i for i in self.items() 
                     if i.parentItem() is None and not isinstance(i, ResizeHandle)]
        if not all_items:
            return
            
        max_z = max(i.zValue() for i in all_items)
        
        if self.undo_stack:
            from commands import ZValueCommand
            increment = max_z - min(i.zValue() for i in items) + 1
            self.undo_stack.push(ZValueCommand(items, increment))
        else:
            for item in items:
                item.setZValue(max_z + 1)
    
    def send_to_back(self):
        items = self.selectedItems()
        if not items:
            return
            
        from items import ResizeHandle
        all_items = [i for i in self.items() 
                     if i.parentItem() is None and not isinstance(i, ResizeHandle)]
        if not all_items:
            return
            
        min_z = min(i.zValue() for i in all_items)
        
        if self.undo_stack:
            from commands import ZValueCommand
            decrement = min_z - max(i.zValue() for i in items) - 1
            self.undo_stack.push(ZValueCommand(items, decrement))
        else:
            for item in items:
                item.setZValue(min_z - 1)
    
    def copy_selection(self):
        items = self.selectedItems()
        if not items:
            return
        
        data = []
        for item in items:
            if item.parentItem() is not None:
                continue
            if hasattr(item, 'to_dict'):
                data.append(item.to_dict())
        
        if data:
            import json
            clipboard = QApplication.clipboard()
            clipboard.setText(json.dumps(data))
    
    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            return
            
        try:
            import json
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return
        
        if not isinstance(data, list):
            return
        
        self.clearSelection()
        
        if self.undo_stack:
            from commands import AddItemCommand
            self.undo_stack.beginMacro("Paste Items")
        
        for item_data in data:
            item_type = item_data.get('type')
            item = None
            
            if item_type == 'text':
                item = DTPTextItem.from_dict(item_data)
            elif item_type == 'image':
                item = DTPImageItem.from_dict(item_data)
            elif item_type == 'shape':
                item = DTPShapeItem.from_dict(item_data)
            elif item_type == 'table':
                item = DTPTableItem.from_dict(item_data)
            
            if item:
                # Offset pasted items slightly
                original_pos = item.pos()
                offset_pos = QPointF(original_pos.x() + 20, original_pos.y() + 20)
                
                if self.undo_stack:
                    cmd = AddItemCommand(self, item, offset_pos)
                    self.undo_stack.push(cmd)
                else:
                    self.addItem(item)
                    item.setPos(offset_pos)
                
                item.setSelected(True)
        
        if self.undo_stack:
            self.undo_stack.endMacro()
    
    def add_image_item(self, file_path, pos):
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            item = DTPImageItem(pixmap)
            from commands import AddItemCommand
            cmd = AddItemCommand(self, item, pos)
            self.undo_stack.push(cmd)


class DTPView(QGraphicsView):
    zoomChanged = Signal(float)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        # 背景色をスタイルシートで強制指定（ダークテーマ対策）
        self.setStyleSheet("background: #505050; border: none;")
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # ウィンドウリサイズ時にシーンを常に中央に表示
        self.setAlignment(Qt.AlignCenter)
        
        self.setAcceptDrops(True)

        # Panning state
        self._panning = False
        self._pan_start_pos = QPointF()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._pan_start_pos
            self._pan_start_pos = event.position()
            
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            # Zoom logic with limits (10% to 800%)
            factor = 1.15
            current_scale = self.transform().m11()
            
            if event.angleDelta().y() > 0:
                if current_scale < 8.0:
                    self.scale(factor, factor)
            else:
                if current_scale > 0.1:
                    self.scale(1 / factor, 1 / factor)
            
            self.zoomChanged.emit(self.transform().m11())
            event.accept()
        else:
            super().wheelEvent(event)

    def reset_zoom(self):
        # Reset to identity matrix (1.0 scale)
        from PySide6.QtGui import QTransform
        self.setTransform(QTransform())
        self.zoomChanged.emit(1.0)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if not file_path:
                    continue
                    
                ext = os.path.splitext(file_path)[1].lower()
                image_exts = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff']
                text_exts = ['.txt', '.md', '.py', '.json', '.csv', '.html', '.css', '.js', '.bat', '.sh']
                
                scene = self.scene()
                pos = self.mapToScene(event.position().toPoint())
                
                if ext in image_exts:
                    pixmap = QPixmap(file_path)
                    if not pixmap.isNull():
                        # Scale down large images
                        max_dim = 600
                        if pixmap.width() > max_dim or pixmap.height() > max_dim:
                            pixmap = pixmap.scaled(max_dim, max_dim, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        
                        item = DTPImageItem(pixmap)
                        if scene and hasattr(scene, 'undo_stack') and scene.undo_stack:
                            from commands import AddItemCommand
                            cmd = AddItemCommand(scene, item, pos)
                            scene.undo_stack.push(cmd)
                        else:
                            scene.addItem(item)
                            item.setPos(pos)
                            
                elif ext in text_exts:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Limit content length to avoid massive lag
                        if len(content) > 10000:
                            content = content[:10000] + "\n... (Truncated)"
                            
                        item = DTPTextItem(content)
                        if scene and hasattr(scene, 'undo_stack') and scene.undo_stack:
                            from commands import AddItemCommand
                            cmd = AddItemCommand(scene, item, pos)
                            scene.undo_stack.push(cmd)
                        else:
                            scene.addItem(item)
                            item.setPos(pos)
                    except Exception as e:
                        print(f"Failed to read text file: {e}")
            
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                self.copy_selection()
                return
            elif event.key() == Qt.Key_V:
                self.paste_from_clipboard()
                return
        super().keyPressEvent(event)

    def copy_selection(self):
        self.scene().copy_selection()

    def paste_from_clipboard(self):
        self.scene().paste_from_clipboard()

