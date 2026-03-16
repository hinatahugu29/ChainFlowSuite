import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QLabel, QFrame
from PySide6.QtCore import Qt

class ScrollBarDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("スクロールバー・デザイン・デモ")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("スクロールバー デザイン比較 (QSS)")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px; color: #61afef;")
        main_layout.addWidget(title_label)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # サンプルデータ
        items = [f"Item {i}: ファイルやフォルダのリストを想定" for i in range(50)]

        # --- Pattern 1: Modern Minimal (非常に細い) ---
        p1 = self.create_demo_widget("Modern Minimal", items, """
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4b5263;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #abb2bf;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        content_layout.addWidget(p1)

        # --- Pattern 2: Accent Rounded (青いアクセント・角丸) ---
        p2 = self.create_demo_widget("Accent Rounded", items, """
            QScrollBar:vertical {
                border: 1px solid #333;
                background: #252525;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #61afef;
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #82b9ed;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        content_layout.addWidget(p2)

        # --- Pattern 3: Flat Dark (背景に馴染ませる) ---
        p3 = self.create_demo_widget("Flat Dark", items, """
            QScrollBar:vertical {
                background-color: #2c313a;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e4451;
                border: 1px solid #181a1f;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4b5263;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        content_layout.addWidget(p3)

        # --- Pattern 4: Glass-Style (境界なし・浮かせる) ---
        p4 = self.create_demo_widget("Glass-Style", items, """
            QScrollBar:vertical {
                background: transparent;
                width: 14px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.1);
                min-height: 40px;
                border-radius: 7px;
                margin: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        content_layout.addWidget(p4)

    def create_demo_widget(self, name, items, qss):
        container = QFrame()
        layout = QVBoxLayout(container)
        
        label = QLabel(name)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-weight: bold; color: #ccc;")
        layout.addWidget(label)

        list_widget = QListWidget()
        list_widget.addItems(items)
        list_widget.setStyleSheet(f"QListWidget {{ background-color: #21252b; border: 1px solid #333; }} {qss}")
        
        # 水平スクロールバーも同様のパターンを適用（幅を高さに読み替え）
        h_qss = qss.replace(":vertical", ":horizontal").replace("width", "height").replace("min-height", "min-width")
        list_widget.horizontalScrollBar().setStyleSheet(h_qss)
        
        layout.addWidget(list_widget)
        return container

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScrollBarDemo()
    window.show()
    sys.exit(app.exec())
