"""
core/styles.py
v14.1 Refactoring: スタイルシート定数の集約

アプリケーション全体で使用するスタイルシートを一元管理し、
一貫したUI/UXを実現する。
"""

# ============================================================
# カラーパレット
# ============================================================

class Colors:
    """アプリケーションカラーパレット"""
    # 背景色
    BG_DARK = "#1e1e1e"
    BG_MEDIUM = "#252526"
    BG_LIGHT = "#2d2d2d"
    BG_HOVER = "#37373d"
    
    # アクセント
    ACCENT_PRIMARY = "#007acc"
    ACCENT_ACTIVE = "#094771"
    ACCENT_HIGHLIGHT = "#d4a017"  # ゴールド（祖先ハイライト用）
    
    # テキスト
    TEXT_PRIMARY = "#cccccc"
    TEXT_SECONDARY = "#888888"
    TEXT_MUTED = "#555555"
    
    # 境界線
    BORDER_DARK = "#222222"
    BORDER_MEDIUM = "#333333"
    BORDER_ACCENT = "#007acc"
    
    # マーク機能
    MARK_COLOR = "#8b1a1a"  # ワインレッド
    BATCH_MENU_BG = "#3a1a1a"
    
    # ハイライト
    HIGHLIGHT_BG = "rgba(255, 200, 50, 100)"
    HIGHLIGHT_BORDER = "#ffc800"


# ============================================================
# ウィジェット別スタイルシート
# ============================================================

class Styles:
    """事前定義されたスタイルシート"""
    
    # メインウィンドウ
    MAIN_WINDOW = f"""
        QMainWindow {{ background: {Colors.BG_MEDIUM}; }}
    """
    
    # メニュー
    CONTEXT_MENU = f"""
        QMenu {{ 
            background-color: {Colors.BG_MEDIUM}; 
            color: {Colors.TEXT_PRIMARY}; 
            border: 1px solid {Colors.BORDER_MEDIUM}; 
        }}
        QMenu::item:selected {{ 
            background-color: {Colors.ACCENT_ACTIVE}; 
        }}
    """
    
    BATCH_MENU = f"""
        QMenu {{ background-color: {Colors.BATCH_MENU_BG}; }}
    """
    
    # ペインヘッダー
    PANE_HEADER_ACTIVE = f"""
        background: {Colors.BG_HOVER}; 
        border-bottom: 2px solid {Colors.ACCENT_PRIMARY};
    """
    
    PANE_HEADER_INACTIVE = f"""
        background: {Colors.BG_MEDIUM}; 
        border-bottom: 1px solid {Colors.BORDER_MEDIUM};
    """
    
    # セパレーター
    SEPARATOR_NORMAL = f"""
        background: {Colors.BG_LIGHT}; 
        color: {Colors.TEXT_SECONDARY}; 
        font-size: 9px; 
        padding-left: 10px; 
        border-bottom: 1px solid {Colors.BORDER_DARK};
    """
    
    SEPARATOR_FOCUSED = f"""
        background: {Colors.ACCENT_ACTIVE}; 
        color: #fff; 
        font-size: 9px; 
        padding-left: 10px; 
        border-bottom: 1px solid {Colors.ACCENT_PRIMARY}; 
        font-weight: bold;
    """
    
    SEPARATOR_HIGHLIGHTED = f"""
        background: {Colors.ACCENT_HIGHLIGHT}; 
        color: {Colors.BG_DARK}; 
        font-size: 9px; 
        padding-left: 10px; 
        font-weight: bold; 
        border-bottom: 1px solid #b58900;
    """
    
    # 検索ボックス
    SEARCH_BOX = f"""
        QLineEdit {{ 
            background: {Colors.BG_DARK}; 
            color: {Colors.TEXT_PRIMARY}; 
            border: 1px solid {Colors.BORDER_MEDIUM}; 
            border-radius: 4px; 
            padding: 2px 5px; 
            font-size: 11px;
        }}
        QLineEdit:focus {{ 
            border: 1px solid {Colors.ACCENT_PRIMARY}; 
            background: {Colors.BG_MEDIUM}; 
        }}
    """
    
    # ボタン
    BUTTON_TRANSPARENT = f"""
        border: none; 
        color: {Colors.TEXT_MUTED}; 
        font-weight: bold; 
        background: transparent;
    """
    
    BUTTON_ACTIVE = f"""
        border: none; 
        color: {Colors.ACCENT_PRIMARY}; 
        font-weight: bold; 
        background: transparent;
    """
    
    # スクロールバー
    SCROLLBAR = f"""
        QScrollBar:vertical {{
            background: {Colors.BG_DARK};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.BG_LIGHT};
            min-height: 30px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {Colors.TEXT_MUTED};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
    """
    
    # アドレスバー
    ADDRESS_BAR = f"""
        QLineEdit {{
            background-color: {Colors.BG_DARK};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER_MEDIUM};
            border-radius: 3px;
            padding: 4px 8px;
            font-size: 12px;
            selection-background-color: {Colors.ACCENT_PRIMARY};
        }}
        QLineEdit:focus {{
            border: 1px solid {Colors.ACCENT_PRIMARY};
        }}
    """
    
    # タブ
    TAB_BAR = f"""
        QTabBar::tab {{
            background: {Colors.BG_LIGHT};
            color: {Colors.TEXT_SECONDARY};
            border: 1px solid {Colors.BORDER_MEDIUM};
            padding: 5px 15px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {Colors.BG_HOVER};
            color: {Colors.TEXT_PRIMARY};
            border-bottom: 2px solid {Colors.ACCENT_PRIMARY};
        }}
        QTabBar::tab:hover:!selected {{
            background: {Colors.BG_MEDIUM};
        }}
    """
    
    # ツールチップ
    TOOLTIP = f"""
        QToolTip {{
            background-color: {Colors.BG_DARK};
            color: {Colors.TEXT_PRIMARY};
            border: 1px solid {Colors.BORDER_MEDIUM};
            padding: 4px;
        }}
    """
    
    # 空領域
    EMPTY_SPACE = f"""
        background: {Colors.BG_DARK};
    """


# ============================================================
# 定数
# ============================================================

class Constants:
    """マジックナンバーを定数化"""
    
    # ペイン
    PANE_MIN_WIDTH = 100
    PANE_HEADER_HEIGHT = 30
    SEPARATOR_HEIGHT = 20
    SEARCH_BOX_WIDTH = 120
    
    # 列幅
    COLUMN_SIZE_WIDTH = 80
    COLUMN_DATE_WIDTH = 140
    COLUMN_MIN_NAME_WIDTH = 100
    
    # タイマー
    RESIZE_DEBOUNCE_MS = 50
    REFRESH_RESTORE_DELAY_MS = 100
    COLUMN_ADJUST_DELAY_MS = 50
    
    # サイズ変更
    WHEEL_SIZE_CHANGE = 40
    MIN_SPLITTER_SIZE = 50
    
    # ボタンサイズ
    SMALL_BUTTON_SIZE = (20, 20)
    MEDIUM_BUTTON_SIZE = (26, 26)


# ============================================================
# ヘルパー関数
# ============================================================

def get_title_style(color: str = Colors.ACCENT_PRIMARY) -> str:
    """タイトルラベル用スタイルを生成"""
    return f"font-weight: bold; color: {color}; font-size: 11px;"


def get_highlight_container_style() -> str:
    """ハイライトされたコンテナ用スタイル"""
    return f"#ItemContainer {{ border: 2px solid {Colors.ACCENT_HIGHLIGHT}; }}"
