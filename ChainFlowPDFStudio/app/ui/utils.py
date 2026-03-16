import ctypes
from PySide6.QtCore import Qt

def apply_dark_title_bar(window):
    """
    Windows 10/11のタイトルバーをダークモードにする。
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    """
    try:
        hwnd = window.winId()
        # Windows 11 Build 22000+ works with 20. Windows 10 1809+ might need 19 or 20.
        # Generally 20 is safe for newer Windows.
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        
        # ctypes.windll.dwmapi.DwmSetWindowAttribute takes: hwnd, attribute, byref(value), sizeof(value)
        value = ctypes.c_int(1)
        
        # Try Attribute 20 (Windows 11 / Win 10 20H1+)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            int(hwnd), 
            DWMWA_USE_IMMERSIVE_DARK_MODE, 
            ctypes.byref(value), 
            ctypes.sizeof(value)
        )
        
        if result != 0:
            # Fallback for older Win10
            final_res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                int(hwnd), 
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1, 
                ctypes.byref(value), 
                ctypes.sizeof(value)
            )
            if final_res != 0:
                print(f"Propagated error: DwmSetWindowAttribute failed with code {final_res}")
        
        # Force a non-client area redraw to ensure the title bar updates immediately
        # SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED
        ctypes.windll.user32.SetWindowPos(int(hwnd), 0, 0, 0, 0, 0, 0x0027)
            
    except Exception as e:
        print(f"Failed to apply dark title bar: {e}")
