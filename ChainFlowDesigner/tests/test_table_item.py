
import sys
import unittest
print("STARTING TEST SCRIPT", file=sys.stderr)
print(f"Python: {sys.executable}", file=sys.stderr)

from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import Qt, QPointF

# Add project path
sys.path.append(r"G:\CODE\Antigravity\Py_FILE\ChainFlowDesigner")

try:
    import items
    from items import DTPTableItem
except ImportError as e:
    print(f"Import Error: {e}", file=sys.stderr)
    sys.exit(1)

app = QApplication.instance() or QApplication(sys.argv)

class TestDTPTableItem(unittest.TestCase):
    def setUp(self):
        self.scene = QGraphicsScene()
        self.item = DTPTableItem(rows=3, cols=3, cell_width=100, cell_height=30)
        self.scene.addItem(self.item)

    def test_initial_state(self):
        self.assertEqual(self.item._rows, 3)
        self.assertEqual(self.item._cols, 3)
        self.assertEqual(len(self.item._col_widths), 3)
        self.assertEqual(len(self.item._row_heights), 3)
        self.assertEqual(self.item._col_widths[0], 100)
        self.assertEqual(self.item._row_heights[0], 30)
        
        rect = self.item.boundingRect()
        self.assertEqual(rect.width(), 300)
        self.assertEqual(rect.height(), 90)

    def test_resize_logic(self):
        # Simulate dragging column 0 border
        # This requires calling mouse methods, which is hard.
        # But we can test set_property ("col_widths")
        new_widths = [150, 100, 100]
        self.item.set_property('col_widths', new_widths)
        self.assertEqual(self.item._col_widths, new_widths)
        
        rect = self.item.boundingRect()
        self.assertEqual(rect.width(), 350)
        
        # Check cell positions
        # Cell(0, 1) should start at 150 + 2
        cell = self.item.cells[0][1]
        self.assertEqual(cell.pos().x(), 150 + 2)

    def test_insert_row(self):
        initial_h = self.item.boundingRect().height()
        self.item.insert_row(1)
        
        self.assertEqual(self.item._rows, 4)
        self.assertEqual(len(self.item._row_heights), 4)
        self.assertEqual(len(self.item.cells), 4)
        
        rect = self.item.boundingRect()
        self.assertEqual(rect.height(), initial_h + 30)

    def test_delete_col(self):
        initial_w = self.item.boundingRect().width()
        self.item.delete_col(1)
        
        self.assertEqual(self.item._cols, 2)
        self.assertEqual(len(self.item._col_widths), 2)
        
        rect = self.item.boundingRect()
        self.assertEqual(rect.width(), initial_w - 100)

    def test_serialization(self):
        self.item.cells[0][0].setPlainText("Test")
        self.item.set_property('col_widths', [120, 100, 100])
        
        data = self.item.to_dict()
        self.assertEqual(data['rows'], 3)
        self.assertEqual(data['col_widths'], [120, 100, 100])
        self.assertEqual(data['cell_data'][0][0], "Test")
        
        # Deserialize
        new_item = DTPTableItem.from_dict(data)
        self.assertEqual(new_item._rows, 3)
        self.assertEqual(new_item._col_widths, [120, 100, 100])
        self.assertEqual(new_item.cells[0][0].toPlainText(), "Test")

if __name__ == '__main__':
    unittest.main()
