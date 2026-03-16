from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                                 QPushButton, QSplitter, QFileDialog, QScrollArea, QLabel,
                                 QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem,
                                 QMenu, QMessageBox, QApplication, QComboBox)
from PySide6.QtCore import Qt, QSize, QRect, Signal, QPoint, QRectF, QMarginsF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap, QCursor, QBrush, QMouseEvent, QPageSize, QPageLayout
from PySide6.QtPrintSupport import QPrinter
import os
import random
import ctypes
from app.core.pdf_handler import PDFScrapHandler

def set_dark_title_bar(window):
    """
    Apply dark mode to the window title bar (Windows 10/11).
    """
    if os.name != 'nt': return
    
    try:
        from ctypes import windll, c_int, byref, sizeof
        hwnd = window.winId()
        
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        
        # Try both constants to support various Windows 10/11 versions
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 
            DWMWA_USE_IMMERSIVE_DARK_MODE, 
            byref(c_int(1)), 
            sizeof(c_int)
        )
        
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, 
            byref(c_int(1)), 
            sizeof(c_int)
        )
    except Exception as e:
        print(f"Failed to set dark title bar: {e}")

# Theme Colors integrated from ChainFlowFiler
class AppColors:
    BG_DARK = "#1e1e1e"
    BG_MEDIUM = "#252526"
    BG_LIGHT = "#2d2d2d"
    BG_HOVER = "#37373d"
    ACCENT_PRIMARY = "#007acc"
    ACCENT_HOVER = "#0098ff"
    TEXT_PRIMARY = "#cccccc"
    BORDER_MEDIUM = "#333333"

# Paper Sizes in Points (72 dpi)
PAPER_SIZES = {
    "A4": (595, 842),
    "A3": (842, 1191),
    "A2": (1191, 1684),
    "Letter": (612, 792),
}

class HandleItem(QGraphicsRectItem):
    """A generic handle for resizing items."""
    def __init__(self, parent, position_flag):
        super().__init__(-4, -4, 8, 8, parent)
        self.position_flag = position_flag
        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.transparent))
        # ItemIsMovable removed to handle manually
        self.setFlags(QGraphicsRectItem.ItemIgnoresTransformations)
        self.setCursor(Qt.SizeFDiagCursor if position_flag in ['tl', 'br'] else Qt.SizeBDiagCursor)
        self._start_pos = None
        self._start_handle_pos = None

    def mousePressEvent(self, event):
        self._start_pos = event.scenePos()
        self._start_handle_pos = self.pos()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._start_pos is None: return
        
        # Calculate delta in scene coordinates
        delta = event.scenePos() - self._start_pos
        
        # Current handle position in parent coordinate space (which is effectively scene space relative to parent origin due to ItemIgnoresTransformations)
        # We simply add delta to start handle pos
        new_pos = self._start_handle_pos + delta
        
        # Constrain or update via parent
        if self.parentItem():
            constrained_pos = self.parentItem().handle_moved(self, new_pos)
            if constrained_pos:
                self.setPos(constrained_pos)
            else:
                # Fallback if parent doesn't return constrained pos (e.g. ResizableRectItem)
                # ResizableRectItem updates its own handles in handle_moved via update_handle_positions
                # So we might not need to setPos here for RectItem... 
                # Wait, ResizableRectItem calls update_handle_positions which sets pos.
                # So we just pass the new_pos to logic.
                pass
        
        event.accept()

    def mouseReleaseEvent(self, event):
        self._start_pos = None
        self._start_handle_pos = None
        super().mouseReleaseEvent(event)

class ResizableRectItem(QGraphicsRectItem):
    """Rect item with 4 corner handles."""
    def __init__(self, rect):
        super().__init__(rect)
        self.setPen(QPen(Qt.red, 2, Qt.DashLine))
        self.setBrush(QColor(255, 0, 0, 40))
        self.setFlags(QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemSendsGeometryChanges)
        self.setZValue(1000)
        self._updating = False
        self.handles = {
            'tl': HandleItem(self, 'tl'),
            'tr': HandleItem(self, 'tr'),
            'bl': HandleItem(self, 'bl'),
            'br': HandleItem(self, 'br')
        }
        self.update_handle_positions()

    def update_handle_positions(self):
        if self._updating: return
        self._updating = True
        r = self.rect()
        self.handles['tl'].setPos(r.topLeft())
        self.handles['tr'].setPos(r.topRight())
        self.handles['bl'].setPos(r.bottomLeft())
        self.handles['br'].setPos(r.bottomRight())
        self._updating = False

    def handle_moved(self, handle, pos):
        if self._updating: return None
        self._updating = True
        r = self.rect()
        if handle.position_flag == 'tl': r.setTopLeft(pos)
        elif handle.position_flag == 'tr': r.setTopRight(pos)
        elif handle.position_flag == 'bl': r.setBottomLeft(pos)
        elif handle.position_flag == 'br': r.setBottomRight(pos)
        self.setRect(r.normalized())
        self._updating = False
        self.update_handle_positions()
        return None

class ResizablePixmapItem(QGraphicsPixmapItem):
    """Pixmap item with resize handles and snapping."""
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setFlags(QGraphicsPixmapItem.ItemIsMovable | QGraphicsPixmapItem.ItemIsSelectable | QGraphicsPixmapItem.ItemSendsGeometryChanges)
        self.setTransformationMode(Qt.SmoothTransformation)
        self._updating = False
        self.handles = {'br': HandleItem(self, 'br')}
        self.update_handle_positions()

    def set_handles_visible(self, visible):
        for h in self.handles.values():
            h.setVisible(visible)

    def update_handle_positions(self):
        if self._updating: return
        self._updating = True
        b = self.boundingRect()
        s = self.scale()
        # ItemIgnoresTransformations on handles means we must manually position them at visual corners
        self.handles['br'].setPos(b.width() * s, b.height() * s)
        self._updating = False

    def handle_moved(self, handle, pos):
        if self._updating: return None
        self._updating = True
        try:
            orig_px = self.pixmap().size()
            
            # pos is in parent coordinates, visual coordinate.
            new_w = max(10, pos.x())
            new_s = new_w / orig_px.width()
            
            print(f"DEBUG: handle_moved pos={pos}, new_w={new_w}, new_s={new_s}")
            self.setScale(new_s)
            
            # Calculate constrained position (Y follows aspect ratio)
            b = self.boundingRect()
            constrained_pos = QPointF(b.width() * new_s, b.height() * new_s)
            return constrained_pos
        finally:
            self._updating = False

    def itemChange(self, change, value):
        if change == QGraphicsPixmapItem.ItemPositionChange and self.scene():
            new_pos = value
            snap_dist = 15
            
            my_rect = self.boundingRect()
            s = self.scale()
            my_w, my_h = my_rect.width()*s, my_rect.height()*s
            my_br = new_pos + QPoint(my_w, my_h)
            my_cx, my_cy = new_pos.x() + my_w/2, new_pos.y() + my_h/2
            
            targets_x = []
            targets_y = []
            
            try:
                # Paper edges
                # Use scene() because this is a QGraphicsItem
                scn = self.scene()
                if not scn: return new_pos
                
                paper = getattr(scn, 'paper_item', None)
                if paper:
                    p_rect = paper.rect() # local rect, centered usually
                    pp = paper.pos()
                    pl = pp.x() + p_rect.left()
                    pr = pp.x() + p_rect.right()
                    pt = pp.y() + p_rect.top()
                    pb = pp.y() + p_rect.bottom()
                    pcx = pp.x() + p_rect.center().x()
                    pcy = pp.y() + p_rect.center().y()
                    
                    targets_x.extend([pl, pr, pcx])
                    targets_y.extend([pt, pb, pcy])

                for item in scn.items():
                    if item == self or not isinstance(item, QGraphicsPixmapItem) or item == paper:
                        continue
                    ir = item.boundingRect()
                    isc = item.scale()
                    iw, ih = ir.width()*isc, ir.height()*isc
                    tl = item.pos()
                    br = tl + QPoint(iw, ih)
                    targets_x.extend([tl.x(), br.x(), tl.x() + iw/2])
                    targets_y.extend([tl.y(), br.y(), tl.y() + ih/2])

                snapped_x = False
                scn.v_guide.setVisible(False)
                for mx in [new_pos.x(), my_br.x(), my_cx]:
                    for ox in targets_x:
                        if abs(mx - ox) < snap_dist:
                            if mx == new_pos.x(): new_pos.setX(ox)
                            elif mx == my_br.x(): new_pos.setX(ox - my_w)
                            else: new_pos.setX(ox - my_w/2)
                            snapped_x = True; 
                            # Show guide
                            scn.v_guide.setLine(ox, -50000, ox, 50000)
                            scn.v_guide.setVisible(True)
                            break
                    if snapped_x: break
                
                snapped_y = False
                scn.h_guide.setVisible(False)
                for my in [new_pos.y(), my_br.y(), my_cy]:
                    for oy in targets_y:
                        if abs(my - oy) < snap_dist:
                            if my == new_pos.y(): new_pos.setY(oy)
                            elif my == my_br.y(): new_pos.setY(oy - my_h)
                            else: new_pos.setY(oy - my_h/2)
                            snapped_y = True; 
                            # Show guide
                            scn.h_guide.setLine(-50000, oy, 50000, oy)
                            scn.h_guide.setVisible(True)
                            break
                    if snapped_y: break
            except Exception as e:
                print(f"Snap error: {e}")
                
            return new_pos
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        s = self.scene()
        if s and hasattr(s, 'v_guide'):
            s.v_guide.setVisible(False)
            s.h_guide.setVisible(False)

class ScrapCanvas(QGraphicsView):
    """View to hold and manage scrap items with paper background."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setStyleSheet(f"background-color: {AppColors.BG_DARK}; border: none;")
        # Huge scene rect to never run out of space
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)

        # Paper Item
        self.paper_item = QGraphicsRectItem()
        self.paper_item.setBrush(QBrush(Qt.white))
        self.paper_item.setPen(QPen(Qt.black, 1))
        self.paper_item.setZValue(-1000) # Always at bottom
        self.scene.addItem(self.paper_item)
        self.scene.paper_item = self.paper_item
        
        # Snap Guides
        pen = QPen(QColor(0, 255, 255), 1, Qt.DashLine)
        self.v_guide = self.scene.addLine(0, -50000, 0, 50000, pen)
        self.h_guide = self.scene.addLine(-50000, 0, 50000, 0, pen)
        self.v_guide.setZValue(2000); self.v_guide.setVisible(False)
        self.h_guide.setZValue(2000); self.h_guide.setVisible(False)
        self.scene.v_guide = self.v_guide
        self.scene.h_guide = self.h_guide
        
        self.set_paper_size("A4")

    def set_paper_size(self, size_name):
        w, h = PAPER_SIZES.get(size_name, PAPER_SIZES["A4"])
        # Center the paper at 0,0
        self.paper_item.setRect(-w/2, -h/2, w, h)
        self.centerOn(0, 0)

    def add_scrap(self, pixmap, pos=None):
        item = ResizablePixmapItem(pixmap)
        self.scene.addItem(item)
        if pos:
            item.setPos(pos)
        else:
            offset = random.randint(-50, 50)
            item.setPos(offset, offset)
    
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            factor = 1.25 if event.angleDelta().y() > 0 else 0.8
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake = QMouseEvent(event.type(), event.position(), Qt.LeftButton, event.buttons() | Qt.LeftButton, event.modifiers())
            super().mousePressEvent(fake)
        else:
            super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for i in self.scene.selectedItems():
                if i != self.paper_item: self.scene.removeItem(i)
        elif event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_C: self.copy_selection()
            elif event.key() == Qt.Key_V: self.paste_selection()
            elif event.key() == Qt.Key_D:
                for i in self.scene.selectedItems():
                    if isinstance(i, QGraphicsPixmapItem):
                        self.add_scrap(i.pixmap(), i.pos() + QPoint(20, 20))
        else:
            super().keyPressEvent(event)

    def copy_selection(self):
        items = self.scene.selectedItems()
        if items and isinstance(items[0], QGraphicsPixmapItem):
            QApplication.clipboard().setPixmap(items[0].pixmap())

    def paste_selection(self):
        pix = QApplication.clipboard().pixmap()
        if not pix.isNull():
            pos = self.mapToScene(self.mapFromGlobal(QCursor.pos()))
            self.add_scrap(pix, pos)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item and item != self.paper_item:
            menu = QMenu()
            f = menu.addAction("Bring to Front")
            b = menu.addAction("Send to Back")
            action = menu.exec(event.globalPos())
            if action == f:
                max_z = max([i.zValue() for i in self.scene.items() if i != self.paper_item] + [0])
                item.setZValue(max_z + 1)
            elif action == b:
                min_z = min([i.zValue() for i in self.scene.items() if i != self.paper_item] + [0])
                item.setZValue(min_z - 1)

class SourcePageViewer(QGraphicsView):
    selection_confirmed = Signal(QRectF)
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(); self.setScene(self.scene)
        self.setAlignment(Qt.AlignCenter); self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setStyleSheet(f"background-color: {AppColors.BG_MEDIUM}; border: none;")
        self.pixmap_item = None; self.selection_item = None
        self.is_selecting = False; self.start_pos = None

    def set_page(self, pixmap):
        self.scene.clear(); self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item); self.scene.setSceneRect(self.pixmap_item.boundingRect())
        self.resetTransform(); self.selection_item = None
        self.centerOn(self.pixmap_item)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            f = 1.25 if event.angleDelta().y() > 0 else 0.8; self.scale(f, f); event.accept()
        else: super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake = QMouseEvent(event.type(), event.position(), Qt.LeftButton, 
                               event.buttons() | Qt.LeftButton, event.modifiers())
            super().mousePressEvent(fake); return
            
        if event.button() == Qt.LeftButton:
            # Check if we clicked a handle or the existing selection
            scene_pos = self.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.transform())
            
            if item and (item == self.selection_item or (item.parentItem() and item.parentItem() == self.selection_item)):
                super().mousePressEvent(event)
                return
            
            # Start new selection
            if self.selection_item:
                self.scene.removeItem(self.selection_item)
                self.selection_item = None
                
            self.is_selecting = True
            self.start_pos = scene_pos
            self.selection_item = ResizableRectItem(QRectF(self.start_pos.x(), self.start_pos.y(), 0, 0))
            self.scene.addItem(self.selection_item)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_selecting and self.selection_item:
            curr_pos = self.mapToScene(event.pos())
            rect = QRectF(self.start_pos, curr_pos).normalized()
            self.selection_item.setRect(rect)
            self.selection_item.update_handle_positions()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)
            super().mouseReleaseEvent(event)
            return
            
        if self.is_selecting:
            self.is_selecting = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter] and self.selection_item:
            r = self.selection_item.rect(); r.translate(self.selection_item.pos())
            self.selection_confirmed.emit(r)
            # Remove selection after confirm to clean up
            self.scene.removeItem(self.selection_item); self.selection_item = None
        elif event.key() == Qt.Key_Delete and self.selection_item:
            self.scene.removeItem(self.selection_item); self.selection_item = None
        else: super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChainFlow PDF Scrap"); self.resize(1400, 900)
        
        # Apply Global Stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {AppColors.BG_MEDIUM}; color: {AppColors.TEXT_PRIMARY}; }}
            QWidget {{ color: {AppColors.TEXT_PRIMARY}; }}
            QPushButton {{
                background-color: {AppColors.BG_LIGHT};
                border: 1px solid {AppColors.BORDER_MEDIUM};
                border-radius: 4px;
                padding: 6px 12px;
                color: {AppColors.TEXT_PRIMARY};
                font-size: 11px;
            }}
            QPushButton:hover {{ 
                background-color: {AppColors.BG_HOVER}; 
                border: 1px solid {AppColors.ACCENT_PRIMARY}; 
            }}
            QPushButton:pressed {{ background-color: {AppColors.ACCENT_PRIMARY}; color: white; }}
            QComboBox {{
                background-color: {AppColors.BG_DARK};
                border: 1px solid {AppColors.BORDER_MEDIUM};
                border-radius: 4px;
                padding: 4px;
                color: {AppColors.TEXT_PRIMARY};
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ image: none; border-left: 1px solid {AppColors.BORDER_MEDIUM}; }}
            QLabel {{ color: {AppColors.TEXT_PRIMARY}; }}
            QSplitter::handle {{ background-color: {AppColors.BG_LIGHT}; }}
            QMessageBox {{ background-color: {AppColors.BG_MEDIUM}; color: {AppColors.TEXT_PRIMARY}; }}
        """)

        self.pdf_handler = PDFScrapHandler(); self.current_page = 0
        self.init_ui()
        set_dark_title_bar(self)

    def init_ui(self):
        cw = QWidget(); self.setCentralWidget(cw); ml = QVBoxLayout(cw)
        tl = QHBoxLayout()
        btn_l = QPushButton("Load PDF"); btn_l.clicked.connect(self.load_pdf); tl.addWidget(btn_l)
        btn_l.setToolTip("素材となるPDFファイルを読み込みます。")
        self.inf = QLabel("No PDF loaded"); tl.addWidget(self.inf)
        tl.addStretch()
        
        lbl_sz = QLabel("Paper Size:")
        # lbl_sz.setStyleSheet("color: #ccc; font-size: 11px;") # Managed by global style
        tl.addWidget(lbl_sz)
        
        self.combo_size = QComboBox()
        self.combo_size.addItems(list(PAPER_SIZES.keys()))
        self.combo_size.setToolTip("スクラップ帳（出力先）の用紙サイズを選択します。")
        self.combo_size.currentTextChanged.connect(self.update_paper_size)
        tl.addWidget(self.combo_size)
        
        btn_c = QPushButton("Clear Canvas"); btn_c.clicked.connect(self.clear_canvas); tl.addWidget(btn_c)
        btn_c.setToolTip("キャンバス上のすべてのスクラップを消去します。")
        
        btn_e = QPushButton("Export PDF")
        btn_e.setStyleSheet(f"background-color: {AppColors.ACCENT_PRIMARY}; color: white; font-weight: bold; padding: 6px 12px; border: none;")
        btn_e.setToolTip("現在のレイアウトをPDFとして保存します。")
        btn_e.clicked.connect(self.export_to_pdf); tl.addWidget(btn_e)
        ml.addLayout(tl)
        
        sp = QSplitter(Qt.Horizontal)
        lc = QWidget(); ll = QVBoxLayout(lc)
        self.sv = SourcePageViewer(); self.sv.selection_confirmed.connect(self.handle_selection); ll.addWidget(self.sv)
        nv = QHBoxLayout()
        b_p = QPushButton("<<"); b_n = QPushButton(">>")
        b_p.clicked.connect(lambda: self.chg_pg(-1)); b_n.clicked.connect(lambda: self.chg_pg(1))
        nv.addWidget(b_p); nv.addWidget(b_n); ll.addLayout(nv)
        sp.addWidget(lc)
        self.sc = ScrapCanvas(); sp.addWidget(self.sc)
        sp.setStretchFactor(0, 1); sp.setStretchFactor(1, 2); ml.addWidget(sp)

    def load_pdf(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if p and self.pdf_handler.load_pdf(p):
            self.current_page = 0; self.update_pg()

    def chg_pg(self, d):
        np = self.current_page + d
        if 0 <= np < self.pdf_handler.get_page_count():
            self.current_page = np; self.update_pg()

    def update_pg(self):
        pix = self.pdf_handler.get_page_pixmap(self.current_page, width=1200)
        if pix: self.sv.set_page(pix); self.inf.setText(f"Page {self.current_page+1}/{self.pdf_handler.get_page_count()}")

    def update_paper_size(self, size_name):
        self.sc.set_paper_size(size_name)

    def handle_selection(self, rect):
        if not self.pdf_handler.doc: return
        p = self.pdf_handler.doc.load_page(self.current_page)
        pr = p.rect; pw = self.sv.pixmap_item.pixmap().width()
        ph = self.sv.pixmap_item.pixmap().height()
        sx, sy = pr.width/pw, pr.height/ph
        crop = (rect.x()*sx, rect.y()*sy, rect.right()*sx, rect.bottom()*sy)
        s = self.pdf_handler.get_clipped_pixmap(self.current_page, crop, dpi=300)
        if s: self.sc.add_scrap(s)

    def clear_canvas(self):
        for i in self.sc.scene.items():
            if i != self.sc.paper_item: self.sc.scene.removeItem(i)

    def export_to_pdf(self):
        p, _ = QFileDialog.getSaveFileName(self, "Export", "", "PDF (*.pdf)")
        if not p: return
        if not p.endswith(".pdf"): p += ".pdf"
        
        prnt = QPrinter(QPrinter.HighResolution)
        prnt.setOutputFormat(QPrinter.PdfFormat); prnt.setOutputFileName(p)
        
        target_size = self.combo_size.currentText()
        # Map combo text to QPageSize.PageSizeId
        size_map = {
            "A4": QPageSize.A4,
            "A3": QPageSize.A3,
            "A2": QPageSize.A2,
            "Letter": QPageSize.Letter
        }
        
        prnt.setPageSize(QPageSize(size_map.get(target_size, QPageSize.A4)))
        prnt.setPageOrientation(QPageLayout.Portrait)
        prnt.setFullPage(True) # Use full page without margins
        
        # Ensure margins are zero
        layout = prnt.pageLayout()
        layout.setMode(QPageLayout.FullPageMode)
        layout.setMargins(QMarginsF(0, 0, 0, 0))
        prnt.setPageLayout(layout)
        
        pnt = QPainter(prnt)
        pnt.setRenderHint(QPainter.SmoothPixmapTransform)
        pnt.setRenderHint(QPainter.Antialiasing)
        
        # Store selection and hide handles/selection
        selected_items = self.sc.scene.selectedItems()
        for item in self.sc.scene.items():
            item.setSelected(False)
            if isinstance(item, ResizablePixmapItem):
                item.set_handles_visible(False)
                
        # We render the paper rect area
        source_rect = self.sc.paper_item.sceneBoundingRect()
        target_rect = prnt.pageRect(QPrinter.DevicePixel)
        
        self.sc.scene.render(pnt, target_rect, source_rect)
        
        # Restore handles and selection
        for item in self.sc.scene.items():
            if isinstance(item, ResizablePixmapItem):
                item.set_handles_visible(True)
        
        for item in selected_items:
            item.setSelected(True)
                
        pnt.end()
        QMessageBox.information(self, "Export", f"Saved to {p}")
