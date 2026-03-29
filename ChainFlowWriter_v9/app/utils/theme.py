import sys
import ctypes

def apply_dark_title_bar(window):
    """Attempt to set the Windows title bar to dark mode."""
    if sys.platform == "win32":
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            hwnd = int(window.winId())
            value = ctypes.c_int(1)
            
            # Try newer attribute first
            result = set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
            if result != 0:
                # Fallback for older Windows 10 versions
                set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

def get_common_stylesheet():
    """Returns a common dark theme stylesheet for the application."""
    return """
        QDialog { 
            background-color: #1E1E1E; 
            color: #D4D4D4; 
        }
        QLabel { 
            color: #D4D4D4; 
        }
        QLineEdit {
            background-color: #2D2D30;
            color: #D4D4D4;
            border: 1px solid #3E3E42;
            border-radius: 2px;
            padding: 4px;
        }
        QLineEdit:focus {
            border: 1px solid #007ACC;
        }
        QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #3C3C3C; 
            border: 1px solid #555555; 
            padding: 4px; 
            border-radius: 2px; 
            color: #FFFFFF;
            min-height: 24px;
        }
        QComboBox::drop-down { border: none; }
        QSplitter::handle {
            background-color: #3E3E42;
        }
        QScrollArea {
            border: none;
            background-color: #1E1E1E;
        }
        QPlainTextEdit, QTextEdit {
            background-color: #1E1E1E;
            color: #D4D4D4;
            border: 1px solid #3E3E42;
        }
        QPushButton {
            background-color: #3E3E42;
            color: #D4D4D4;
            border: 1px solid #4F4F4F;
            border-radius: 4px;
            padding: 5px 15px;
        }
        QPushButton:hover {
            background-color: #4F4F4F;
        }
        QPushButton:pressed {
            background-color: #5F5F5F;
        }
        QPushButton:disabled {
            color: #555;
            background-color: #2D2D30;
            border: 1px solid #333;
        }
    """
