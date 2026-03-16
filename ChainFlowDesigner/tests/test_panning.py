
import sys
import unittest
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtCore import Qt, QPointF, QEvent, QPoint
from PySide6.QtGui import QMouseEvent

# Add project path
sys.path.append(r"d:\CODE\Antigravity\Py_FILE\ChainFlowDesigner")

try:
    from canvas import DTPView, DTPScene
except ImportError as e:
    print(f"Import Error: {e}", file=sys.stderr)
    sys.exit(1)

app = QApplication.instance() or QApplication(sys.argv)

class TestPanning(unittest.TestCase):
    def setUp(self):
        self.scene = DTPScene()
        # Set a large scene to ensure scrollbars appear
        self.scene.setSceneRect(0, 0, 2000, 2000)
        self.view = DTPView(self.scene)
        self.view.resize(400, 400)
        self.view.show()
        
        # Ensure scrollbars are visible and at 0
        self.view.horizontalScrollBar().setValue(0)
        self.view.verticalScrollBar().setValue(0)
        
    def tearDown(self):
        self.view.close()

    def test_middle_click_panning(self):
        # Initial scroll values
        h_val_start = self.view.horizontalScrollBar().value()
        v_val_start = self.view.verticalScrollBar().value()
        
        center_pt = self.view.viewport().rect().center()
        
        # 1. Press Middle Button
        press_event = QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(center_pt),
            QPointF(center_pt),
            Qt.MiddleButton,
            Qt.MiddleButton,
            Qt.NoModifier
        )
        self.view.mousePressEvent(press_event)
        
        self.assertTrue(self.view._panning)
        self.assertEqual(self.view.cursor().shape(), Qt.ClosedHandCursor)
        
        # 2. Move Mouse (Drag left and up -> Scroll right and down)
        # If we drag the 'paper' to the left (-delta), the viewport should move right (+scroll)
        # Implementation: scroll_value -= delta
        # If mouse moves LEFT (x decreases), delta is negative. 
        # So scroll_value -= (-val) => scroll_value += val.
        
        move_to = center_pt + QPoint(100, 100) # Dragging right and down
        move_event = QMouseEvent(
            QEvent.MouseMove,
            QPointF(move_to),
            QPointF(move_to),
            Qt.MiddleButton,
            Qt.MiddleButton,
            Qt.NoModifier
        )
        self.view.mouseMoveEvent(move_event)
        
        # Dragging RIGHT (+x) means we are pulling the paper to the right.
        # This means we should see MORE of the LEFT side.
        # So scrollbar should DECREASE.
        # delta = +100. scroll -= 100.
        
        h_val_end = self.view.horizontalScrollBar().value()
        v_val_end = self.view.verticalScrollBar().value()
        
        # Since we started at 0, decreasing might stay at 0 if min is 0.
        # So let's try dragging LEFT (-x) and UP (-y) first?
        # Or better, set initial scroll to middle.
        
    def test_panning_from_center(self):
        # Center the scrollbars first
        h_bar = self.view.horizontalScrollBar()
        v_bar = self.view.verticalScrollBar()
        
        h_bar.setValue(self.scene.width() // 2)
        v_bar.setValue(self.scene.height() // 2)
        
        start_h = h_bar.value()
        start_v = v_bar.value()
        
        center_pt = QPointF(200, 200)
        
        # Press
        press_event = QMouseEvent(
            QEvent.MouseButtonPress,
            center_pt,
            center_pt,
            Qt.MiddleButton,
            Qt.MiddleButton,
            Qt.NoModifier
        )
        self.view.mousePressEvent(press_event)
        
        # Move RIGHT (+50) and DOWN (+50)
        # This is strictly "Mouse Move", dragging the paper.
        # If I grab paper and move hand RIGHT, the paper moves RIGHT.
        # The viewport stays still relative to monitor.
        # So I see content that was to the LEFT.
        # So Scrollbar value should DECREASE.
        
        move_pt = center_pt + QPointF(50, 50)
        move_event = QMouseEvent(
            QEvent.MouseMove,
            move_pt,
            move_pt,
            Qt.MiddleButton,
            Qt.MiddleButton,
            Qt.NoModifier
        )
        self.view.mouseMoveEvent(move_event)
        
        new_h = h_bar.value()
        new_v = v_bar.value()
        
        # Expect values to decrease
        self.assertLess(new_h, start_h)
        self.assertLess(new_v, start_v)
        self.assertEqual(new_h, start_h - 50)
        self.assertEqual(new_v, start_v - 50)
        
        # Release
        release_event = QMouseEvent(
            QEvent.MouseButtonRelease,
            move_pt,
            move_pt,
            Qt.MiddleButton,
            Qt.MiddleButton,
            Qt.NoModifier
        )
        self.view.mouseReleaseEvent(release_event)
        
        self.assertFalse(self.view._panning)
        self.assertEqual(self.view.cursor().shape(), Qt.ArrowCursor)

if __name__ == '__main__':
    unittest.main()
