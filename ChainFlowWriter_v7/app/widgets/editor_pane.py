import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, 
                               QLabel, QPushButton, QMenu, QInputDialog, QDialog,
                               QFormLayout, QComboBox, QSpinBox, QDialogButtonBox,
                               QFileDialog)
from PySide6.QtCore import Qt, Signal, QDateTime, QTimer, QRegularExpression, QLocale
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextCursor
from app.utils.theme import apply_dark_title_bar, get_common_stylesheet
import os


class ImageSizeDialog(QDialog):
    """画像サイズ指定ダイアログ"""
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.setWindowTitle("画像サイズ設定")
        self.setStyleSheet(get_common_stylesheet())
        # Override with specific needs if any, else use common
        self.setStyleSheet(self.styleSheet() + """
            QComboBox, QSpinBox { min-width: 120px; }
            QPushButton { background-color: #0E639C; color: white; border: none; padding: 6px 16px; border-radius: 3px; font-weight: bold; }
            QPushButton:hover { background-color: #1177BB; }
        """)
        
        layout = QFormLayout(self)
        
        self.label_file = QLabel(filename)
        self.label_file.setStyleSheet("color: #4BBAFF; font-weight: bold;")
        layout.addRow("ファイル:", self.label_file)
        
        self.size_mode = QComboBox()
        self.size_mode.addItems(["パーセント指定 (%)", "ピクセル指定 (px)", "原寸大"])
        layout.addRow("サイズ方式:", self.size_mode)
        
        self.size_value = QSpinBox()
        self.size_value.setRange(1, 2000)
        self.size_value.setValue(80)
        self.size_value.setSuffix(" %")
        layout.addRow("幅:", self.size_value)
        
        self.size_mode.currentIndexChanged.connect(self._on_mode_change)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_title_bar(self)
        
    def _on_mode_change(self, index):
        if index == 0:  # percent
            self.size_value.setRange(1, 200)
            self.size_value.setValue(80)
            self.size_value.setSuffix(" %")
            self.size_value.setEnabled(True)
        elif index == 1:  # px
            self.size_value.setRange(1, 4000)
            self.size_value.setValue(400)
            self.size_value.setSuffix(" px")
            self.size_value.setEnabled(True)
        else:  # original
            self.size_value.setEnabled(False)
    
    def get_width_style(self):
        mode = self.size_mode.currentIndex()
        if mode == 0:
            return f"width: {self.size_value.value()}%;"
        elif mode == 1:
            return f"width: {self.size_value.value()}px;"
        else:
            return ""


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown用の簡易シンタックスハイライター"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # カラーテーマ (VS Code Dark風)
        color_header = QColor("#569CD6") # Blue
        color_bold = QColor("#CE9178")   # Orange
        color_italic = QColor("#CE9178")
        color_link = QColor("#4EC9B0")   # Teal
        color_code = QColor("#D7BA7D")   # Yellowish
        color_quote = QColor("#6A9955")  # Green
        color_container = QColor("#C586C0") # Purple
        color_list = QColor("#B5CEA8")   # Pale Green
        color_tag = QColor("#569CD6")    # Light Blue
        color_comment = QColor("#6A9955") # Green
        color_hr = QColor("#808080")     # Gray

        # 1. ヘッダー (#)
        header_format = QTextCharFormat()
        header_format.setForeground(color_header)
        header_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r"^#+ .*", QRegularExpression.MultilineOption), header_format))

        # 2. 太字 (**)
        bold_format = QTextCharFormat()
        bold_format.setForeground(color_bold)
        bold_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r"\*\*.*?\*\*"), bold_format))

        # 3. 斜体 (*)
        italic_format = QTextCharFormat()
        italic_format.setForeground(color_italic)
        italic_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"\s\*([^*]+)\*"), italic_format))

        # 4. リンク [text](url)
        link_format = QTextCharFormat()
        link_format.setForeground(color_link)
        self.highlighting_rules.append((QRegularExpression(r"\[.*?\]\(.*?\)"), link_format))

        # 5. インラインコード (`)
        code_format = QTextCharFormat()
        code_format.setForeground(color_code)
        code_format.setBackground(QColor("#2d2d2d"))
        self.highlighting_rules.append((QRegularExpression(r"`.*?`"), code_format))

        # 6. リスト (-, *, 1.)
        list_format = QTextCharFormat()
        list_format.setForeground(color_list)
        self.highlighting_rules.append((QRegularExpression(r"^\s*([-*]|\d+\.)\s"), list_format))

        # 7. 引用 (>)
        quote_format = QTextCharFormat()
        quote_format.setForeground(color_quote)
        self.highlighting_rules.append((QRegularExpression(r"^>.*"), quote_format))

        # 8. 特殊コンテナ (::: stamp 等)
        container_format = QTextCharFormat()
        container_format.setForeground(color_container)
        container_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r"^:::\s*\w+"), container_format))
        self.highlighting_rules.append((QRegularExpression(r"^:::"), container_format))

        # 9. HTML タグ (<...>)
        tag_format = QTextCharFormat()
        tag_format.setForeground(color_tag)
        # タグの開始・終了、およびタグ全体をハイライト
        self.highlighting_rules.append((QRegularExpression(r"<[^>]+>"), tag_format))

        # 10. HTML コメント (<!-- ... -->)
        comment_format = QTextCharFormat()
        comment_format.setForeground(color_comment)
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"<!--.*?-->"), comment_format))

        # 11. 水平線 (---)
        hr_format = QTextCharFormat()
        hr_format.setForeground(color_hr)
        self.highlighting_rules.append((QRegularExpression(r"^---+$"), hr_format))


        # マルチライン・コードブロック用の設定
        self.multi_line_code_format = QTextCharFormat()
        self.multi_line_code_format.setForeground(color_code)
        self.multi_line_code_format.setBackground(QColor("#2d2d2d"))
        
        self.code_block_start = QRegularExpression(r"^```")
        self.code_block_end = QRegularExpression(r"^```")

    def highlightBlock(self, text):
        # 1. 通常のルール適用
        for pattern, char_format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)

        # 2. マルチラインのコードブロック (```) 判定
        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            start_index = self.code_block_start.match(text).capturedStart()

        while start_index >= 0:
            match = self.code_block_end.match(text, start_index)
            end_index = match.capturedStart()
            code_length = match.capturedLength()

            if end_index == -1:
                self.setCurrentBlockState(1)
                code_length = len(text) - start_index
            else:
                code_length = end_index - start_index + code_length

            self.setFormat(start_index, code_length, self.multi_line_code_format)
            start_index = self.code_block_start.match(text, start_index + code_length).capturedStart()


class MarkdownEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        # シンタックスハイライターの適用
        self.highlighter = MarkdownHighlighter(self.document())

    def canInsertFromMimeData(self, source):
        if source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        if source.hasUrls():
            urls = source.urls()
            for url in urls:
                if url.isLocalFile():
                    path = url.toLocalFile()
                    ext = os.path.splitext(path)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']:
                        img_uri = url.toString()
                        name = os.path.basename(path)
                        self._insert_image_with_size(name, img_uri)
                        return
        super().insertFromMimeData(source)

    def _insert_image_with_size(self, name, img_uri):
        dialog = ImageSizeDialog(name, self)
        if dialog.exec() == QDialog.Accepted:
            style = dialog.get_width_style()
            if style:
                tag = f'\n<img src="{img_uri}" alt="{name}" style="{style}">\n'
            else:
                tag = f'\n<img src="{img_uri}" alt="{name}">\n'
            
            cursor = self.textCursor()
            cursor.beginEditBlock()
            cursor.insertText(tag)
            cursor.endEditBlock()
            self.setFocus()



class EditorPane(QWidget):
    text_changed = Signal(str)
    save_requested = Signal()
    save_as_requested = Signal()
    open_requested = Signal()
    save_snippet_requested = Signal(str) # Emits the raw text to be saved as a snippet
    open_cheat_sheet_requested = Signal() # Emits when the user wants to browse snippets
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header Area (Dynamic 2-row Toolbar)
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #2D2D30; border-bottom: 1px solid #3E3E42;")
        header_vbox = QVBoxLayout(header_widget)
        header_vbox.setContentsMargins(4, 4, 4, 4)
        header_vbox.setSpacing(4)
        
        # Row 1: File, Info, spacers
        row1_layout = QHBoxLayout()
        row1_layout.setContentsMargins(4, 0, 4, 0)
        
        header_label = QLabel("📝 EDITOR")
        header_label.setStyleSheet("color: #8F8F8F; font-weight: bold; font-size: 10px; margin-right: 10px;")
        row1_layout.addWidget(header_label)
        row1_layout.addStretch()
        
        # Toolbar Buttons
        btn_style = """
            QPushButton {
                background-color: #3E3E42; color: #D4D4D4; border: none; padding: 4px 8px; border-radius: 2px; font-size: 11px;
            }
            QPushButton:hover { background-color: #4B4B4B; }
        """
        
        self.btn_file = QPushButton("File ▾")
        self.btn_file.setStyleSheet(btn_style)
        self._setup_file_menu()
        
        self.btn_insert = QPushButton("Insert Table")
        self.btn_insert.setStyleSheet(btn_style)
        self.btn_insert.clicked.connect(self._show_insert_menu)
        
        self.btn_cheat_sheet = QPushButton("🌟 Cheat Sheet")
        self.btn_cheat_sheet.setStyleSheet("""
            QPushButton {
                background-color: #0E639C; color: white; border: none; padding: 4px 10px; border-radius: 2px; font-weight: bold; font-size: 11px;
            }
            QPushButton:hover { background-color: #1177BB; }
        """)
        self.btn_cheat_sheet.clicked.connect(self.open_cheat_sheet_requested.emit)
        
        self.btn_format = QPushButton("Format ▾")
        self.btn_format.setStyleSheet(btn_style)
        self._setup_format_menu()
        
        self.btn_macro = QPushButton("Macros ▾")
        self.btn_macro.setStyleSheet(btn_style)
        self._setup_macro_menu()
        
        self.btn_html = QPushButton("HTML ▾") # Shortened label
        self.btn_html.setStyleSheet(btn_style)
        self._setup_html_menu()
        
        # Assemble Row 1: App/File actions
        row1_layout.addWidget(self.btn_file)
        row1_layout.addSpacing(4)
        row1_layout.addWidget(self.btn_format)
        row1_layout.addSpacing(4)
        row1_layout.addWidget(self.btn_macro)
        header_vbox.addLayout(row1_layout)
        
        # Row 2: Insert tools & Cheat Sheet
        row2_layout = QHBoxLayout()
        row2_layout.setContentsMargins(4, 0, 4, 0)
        
        row2_layout.addWidget(self.btn_html)
        row2_layout.addWidget(self.btn_insert)
        row2_layout.addStretch()
        row2_layout.addWidget(self.btn_cheat_sheet)
        header_vbox.addLayout(row2_layout)
        
        # Editor
        self.editor = MarkdownEditor()
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                border: none;
                padding: 15px;
            }
        """)
        
        layout.addWidget(header_widget)
        layout.addWidget(self.editor)
        
        self.editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.editor)
        
        # Additional formatting shortcuts (Standalone)
        self._setup_additional_shortcuts()
        
        # Connect text changed signal to emit the whole content
        self.editor.textChanged.connect(lambda: self.text_changed.emit(self.editor.toPlainText()))
        
    def _setup_file_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2D2D30; color: #D4D4D4; border: 1px solid #3E3E42; }
            QMenu::item { padding: 4px 24px; }
            QMenu::item:selected { background-color: #0E639C; }
        """)
        
        act_open = QAction("開く (Open)", self)
        act_open.triggered.connect(self.open_requested.emit)
        
        act_save = QAction("保存 (Save)", self)
        act_save.triggered.connect(self.save_requested.emit)
        
        act_save_as = QAction("名前をつけて保存 (Save As...)", self)
        act_save_as.triggered.connect(self.save_as_requested.emit)
        
        menu.addAction(act_open)
        menu.addSeparator()
        menu.addAction(act_save)
        menu.addAction(act_save_as)
        
        self.btn_file.setMenu(menu)
        
    def _show_insert_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #252526; color: #D4D4D4; border: 1px solid #3E3E42; }
            QMenu::item:selected { background-color: #094771; }
        """)
        
        act_table = QAction("Insert Table...", self)
        act_table.triggered.connect(self._insert_table_dialog)
        
        act_checklist = QAction("Insert Task List", self)
        act_checklist.triggered.connect(self._insert_tasklist)
        
        menu.addAction(act_table)
        menu.addAction(act_checklist)
        
        menu.exec_(self.btn_insert.mapToGlobal(self.btn_insert.rect().bottomLeft()))
        
    def _insert_table_dialog(self):
        cols, ok_col = QInputDialog.getInt(self, "Insert Table", "Number of Columns:", 3, 1, 20)
        if not ok_col: return
        rows, ok_row = QInputDialog.getInt(self, "Insert Table", "Number of Rows:", 4, 1, 50)
        if not ok_row: return
        
        # Build Markdown Table
        header = "|" + "|".join([f" Header {i+1} " for i in range(cols)]) + "|"
        divider = "|" + "|".join(["---" for _ in range(cols)]) + "|"
        
        lines = [header, divider]
        for r in range(rows):
            line = "|" + "|".join([f" Row {r+1} Col {i+1} " for i in range(cols)]) + "|"
            lines.append(line)
            
        table_md = "\n" + "\n".join(lines) + "\n\n"
        self.editor.insertPlainText(table_md)
        self.editor.setFocus()
        
    def _insert_tasklist(self):
        task_md = "\n- [ ] Task 1\n- [ ] Task 2\n- [x] Completed task\n\n"
        self.editor.insertPlainText(task_md)
        self.editor.setFocus()

    def _setup_additional_shortcuts(self):
        """標準的なMarkdown編集ショートカットの追加"""
        
        # Bold: Ctrl+B / Ctrl+Shift+B
        act_bold = QAction("Bold", self)
        act_bold.setShortcuts([QKeySequence("Ctrl+B"), QKeySequence("Ctrl+Shift+B")])
        act_bold.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        act_bold.triggered.connect(lambda: self._apply_inline_format("**"))
        self.editor.addAction(act_bold)
        
        # Italic: Ctrl+I
        act_italic = QAction("Italic", self)
        act_italic.setShortcut(QKeySequence("Ctrl+I"))
        act_italic.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        act_italic.triggered.connect(lambda: self._apply_inline_format("*"))
        self.editor.addAction(act_italic)
        
        # Heading 1-3
        for i in range(1, 4):
            act_h = QAction(f"Heading {i}", self)
            act_h.setShortcut(QKeySequence(f"Ctrl+{i}"))
            act_h.setShortcutContext(Qt.WindowShortcut)
            act_h.triggered.connect(lambda checked=False, level=i: self._apply_heading(level))
            self.addAction(act_h)
        
        # Link: Ctrl+K
        act_link = QAction("Insert Link", self)
        act_link.setShortcut(QKeySequence("Ctrl+K"))
        act_link.setShortcutContext(Qt.WindowShortcut)
        act_link.triggered.connect(self._insert_link_template)
        self.addAction(act_link)

        # Alignment
        act_center = QAction("Center Text", self)
        act_center.setShortcut(QKeySequence("Ctrl+Shift+E"))
        act_center.setShortcutContext(Qt.WindowShortcut)
        act_center.triggered.connect(lambda: self._wrap_selection("center"))
        self.addAction(act_center)

        act_right = QAction("Right Text", self)
        act_right.setShortcut(QKeySequence("Ctrl+Shift+R"))
        act_right.setShortcutContext(Qt.WindowShortcut)
        act_right.triggered.connect(lambda: self._wrap_selection("right"))
        self.addAction(act_right)

        # Text Size
        act_large = QAction("Large Text", self)
        act_large.setShortcut(QKeySequence("Ctrl+Shift+L"))
        act_large.setShortcutContext(Qt.WindowShortcut)
        act_large.triggered.connect(lambda: self._wrap_selection("large"))
        self.addAction(act_large)

        act_small = QAction("Small Text", self)
        act_small.setShortcut(QKeySequence("Ctrl+Shift+M"))
        act_small.setShortcutContext(Qt.WindowShortcut)
        act_small.triggered.connect(lambda: self._wrap_selection("small"))
        self.addAction(act_small)

        # Special
        act_stamp = QAction("Stamp", self)
        act_stamp.setShortcut(QKeySequence("Ctrl+Shift+T"))
        act_stamp.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        act_stamp.triggered.connect(lambda: self._wrap_selection("stamp"))
        self.editor.addAction(act_stamp)

        act_date = QAction("Insert Date", self)
        act_date.setShortcut(QKeySequence("Ctrl+D"))
        act_date.setShortcutContext(Qt.WindowShortcut)
        act_date.triggered.connect(lambda: self._insert_at_cursor(QDateTime.currentDateTime().toString("yyyy/MM/dd")))
        self.addAction(act_date)

        # [STRUCTURE]
        # Unordered List: Ctrl+Shift+8
        act_ul = QAction("Unordered List", self)
        act_ul.setShortcut(QKeySequence("Ctrl+Shift+8"))
        act_ul.setShortcutContext(Qt.WindowShortcut)
        act_ul.triggered.connect(lambda: self._toggle_list("* "))
        self.addAction(act_ul)

        # Ordered List: Ctrl+Shift+9
        act_ol = QAction("Ordered List", self)
        act_ol.setShortcut(QKeySequence("Ctrl+Shift+9"))
        act_ol.setShortcutContext(Qt.WindowShortcut)
        act_ol.triggered.connect(lambda: self._toggle_list("1. "))
        self.addAction(act_ol)

        # Quote: Ctrl+Shift+> (Actually Ctrl+Shift+. on most layouts)
        act_quote = QAction("Quote", self)
        act_quote.setShortcut(QKeySequence("Ctrl+Shift+."))
        act_quote.setShortcutContext(Qt.WindowShortcut)
        act_quote.triggered.connect(self._toggle_quote)
        self.addAction(act_quote)

        # Horizontal Rule: Ctrl+Shift+-
        act_hr = QAction("Horizontal Rule", self)
        act_hr.setShortcut(QKeySequence("Ctrl+Shift+-"))
        act_hr.setShortcutContext(Qt.WindowShortcut)
        act_hr.triggered.connect(self._insert_hr)
        self.addAction(act_hr)

        # Code Block: Ctrl+Shift+C
        act_cb = QAction("Code Block", self)
        act_cb.setShortcut(QKeySequence("Ctrl+Shift+C"))
        act_cb.setShortcutContext(Qt.WindowShortcut)
        act_cb.triggered.connect(self._insert_code_block)
        self.addAction(act_cb)

        # [COMPONENTS]
        # Table: Ctrl+T
        act_table = QAction("Insert Table", self)
        act_table.setShortcut(QKeySequence("Ctrl+T"))
        act_table.setShortcutContext(Qt.WindowShortcut)
        act_table.triggered.connect(self._insert_table_template)
        self.addAction(act_table)

        # Snippets: Ctrl+Q / Ctrl+G
        act_snip = QAction("Snippets", self)
        act_snip.setShortcuts([QKeySequence("Ctrl+Q"), QKeySequence("Ctrl+G")])
        act_snip.setShortcutContext(Qt.WindowShortcut)
        act_snip.triggered.connect(self._show_cheat_sheet)
        self.addAction(act_snip)

        # Macros: Ctrl+M
        act_macro = QAction("Macros", self)
        act_macro.setShortcut(QKeySequence("Ctrl+M"))
        act_macro.setShortcutContext(Qt.WindowShortcut)
        act_macro.triggered.connect(self._show_macros_menu)
        self.addAction(act_macro)

        # [EXTRA]
        # Hard Break: Ctrl+Enter
        act_br = QAction("Hard Break", self)
        act_br.setShortcut(QKeySequence("Ctrl+Return"))
        act_br.setShortcutContext(Qt.WindowShortcut)
        act_br.triggered.connect(self._insert_hard_break)
        self.addAction(act_br)

        # Page Break: Ctrl+Shift+Enter
        act_pb = QAction("Page Break", self)
        act_pb.setShortcut(QKeySequence("Ctrl+Shift+Return"))
        act_pb.setShortcutContext(Qt.WindowShortcut)
        act_pb.triggered.connect(self._insert_page_break)
        self.addAction(act_pb)

        # <m-d> Tag: Ctrl+Shift+D
        act_md = QAction("<m-d> Tag", self)
        act_md.setShortcut(QKeySequence("Ctrl+Shift+D"))
        act_md.setShortcutContext(Qt.WindowShortcut)
        act_md.triggered.connect(self._insert_md_tag)
        self.addAction(act_md)

        # Variable: Ctrl+Shift+V
        act_var = QAction("Variable {{}}", self)
        act_var.setShortcut(QKeySequence("Ctrl+Shift+V"))
        act_var.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        act_var.triggered.connect(lambda: self._apply_inline_format("{{", "}}"))
        self.editor.addAction(act_var)

    def _apply_inline_format(self, marker_start, marker_end=None):
        if marker_end is None:
            marker_end = marker_start
            
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"{marker_start}{text}{marker_end}")
        else:
            cursor.insertText(f"{marker_start}text{marker_end}")
            # Position cursor between markers
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(marker_end))
            self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _apply_heading(self, level):
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.insertText("#" * level + " ")
        self.editor.setFocus()

    def _insert_link_template(self):
        self._insert_at_cursor("[text](url)")

    def _toggle_list(self, marker):
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        start_pos = cursor.position()
        
        cursor.setPosition(end)
        cursor.movePosition(QTextCursor.EndOfLine)
        end_pos = cursor.position()
        
        cursor.setPosition(start_pos)
        
        lines_to_process = []
        while cursor.position() < end_pos:
            cursor.movePosition(QTextCursor.StartOfLine)
            line_text = cursor.block().text()
            
            if line_text.startswith(marker):
                # Remove marker
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(marker))
                cursor.removeSelectedText()
            else:
                # Add marker
                cursor.insertText(marker)
                
            if not cursor.movePosition(QTextCursor.Down):
                break
        
        cursor.endEditBlock()
        self.editor.setFocus()

    def _toggle_quote(self):
        self._toggle_list("> ")
        self.editor.setFocus()

    def _insert_hr(self):
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        if cursor.block().text().strip():
            cursor.movePosition(QTextCursor.EndOfLine)
            cursor.insertText("\n\n---\n\n")
        else:
            cursor.insertText("---\n\n")
        self.editor.setFocus()

    def _insert_code_block(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText().replace('\u2029', '\n')
            cursor.insertText(f"```\n{text}\n```")
        else:
            cursor.insertText("```\n\n```")
            cursor.movePosition(QTextCursor.Up)
        self.editor.setFocus()

    def _insert_table_template(self):
        template = (
            "| Header | Header | Header |\n"
            "| --- | --- | --- |\n"
            "| Cell | Cell | Cell |\n"
            "| Cell | Cell | Cell |"
        )
        self._insert_at_cursor(template)
        self.editor.setFocus()

    def _insert_hard_break(self):
        self._insert_at_cursor("<br>\n")
        self.editor.setFocus()

    def _insert_page_break(self):
        self._insert_at_cursor('\n<div style="page-break-before: always;"></div>\n')
        self.editor.setFocus()

    def _insert_md_tag(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText().replace('\u2029', '\n')
            cursor.insertText(f"<m-d>\n{text}\n</m-d>")
        else:
            cursor.insertText("<m-d>\n\n</m-d>")
            cursor.movePosition(QTextCursor.Up)
        self.editor.setFocus()

    def _show_macros_menu(self):
        self.btn_macro.showMenu() # Corrected from btn_macros to btn_macro based on existing code
        self.editor.setFocus()

    def _show_cheat_sheet(self):
        self.open_cheat_sheet_requested.emit()
        self.editor.setFocus()

    def _insert_at_cursor(self, text):
        cursor = self.editor.textCursor()
        cursor.insertText(text)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _wrap_selection(self, format_type):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            # Handle unicode block characters that QPlainTextEdit might insert
            text = text.replace('\u2029', '\n') 
        else:
            text = "text"
            
        if format_type == "large":
            cursor.insertText(f"::: large\n{text}\n:::")
        elif format_type == "small":
            cursor.insertText(f"::: small\n{text}\n:::")
        elif format_type == "center":
            cursor.insertText(f"::: center\n{text}\n:::")
        elif format_type == "right":
            cursor.insertText(f"::: right\n{text}\n:::")
        elif format_type == "stamp":
            if not cursor.hasSelection():
                # Default template with inline tutorial comments
                template = (
                    "::: stamp\n"
                    "![](seal.png)\n"
                    ":::\n"
                    "<!-- 💡 スタンプ調整ガイド (::: stamp の横に記述可能):\n"
                    "  - 位置調整: right:20mm; margin-top:-15mm; (mm/px指定可)\n"
                    "  - サイズ: width:30mm;\n"
                    "  - 回転: transform: rotate(10deg);\n"
                    "  - 透明度: opacity: 0.8;\n"
                    "  - モード: normal; (文字を透過させない場合に記述)\n"
                    "  例: ::: stamp right:10mm; transform: rotate(5deg);\n"
                    "-->\n"
                )
                cursor.insertText(template)
            else:
                cursor.insertText(f"::: stamp\n{text}\n:::")

    def _show_context_menu(self, position):
        menu = self.editor.createStandardContextMenu()
        
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            menu.addSeparator()
            action_save_snippet = menu.addAction("🌟 Save Selection as Snippet...")
            action_save_snippet.triggered.connect(self._emit_save_snippet)
            
        menu.exec(self.editor.viewport().mapToGlobal(position))

    def _emit_save_snippet(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            text = text.replace('\u2029', '\n')
            self.save_snippet_requested.emit(text)

    def _setup_format_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2D2D30; color: #D4D4D4; border: 1px solid #3E3E42; }
            QMenu::item { padding: 4px 24px; }
            QMenu::item:selected { background-color: #0E639C; }
        """)
        
        # Text alignment
        act_center = menu.addAction("Center Text (中央揃え)")
        act_center.triggered.connect(lambda: self._wrap_selection("center"))
        
        act_right = menu.addAction("Right Text (右揃え)")
        act_right.triggered.connect(lambda: self._wrap_selection("right"))
        
        menu.addSeparator()
        
        # Text size
        act_large = menu.addAction("Large Text (拡大)")
        act_large.triggered.connect(lambda: self._wrap_selection("large"))
        
        act_small = menu.addAction("Small Text (縮小)")
        act_small.triggered.connect(lambda: self._wrap_selection("small"))
        
        menu.addSeparator()
        
        # Stamp / Absolute Positioning
        act_stamp = menu.addAction("電子印影 / スタンプ (Stamp)")
        act_stamp.triggered.connect(lambda: self._wrap_selection("stamp"))
        act_stamp.setToolTip("選択範囲をスタンプ（絶対配置モード）として囲みます")
        
        self.btn_format.setMenu(menu)

    def _setup_html_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2D2D30; color: #D4D4D4; border: 1px solid #3E3E42; }
            QMenu::item { padding: 4px 24px; }
            QMenu::item:selected { background-color: #0E639C; }
        """)
        
        action_pb = menu.addAction("ページ区切り (Page Break)")
        action_pb.triggered.connect(lambda: self._insert_html('\n<div style="page-break-before: always;"></div>\n'))
        
        action_2col = menu.addAction("2段組みレイアウト (Flex Multi-Col)")
        snip_2col = '\n<div style="display: flex; gap: 20px;">\n  <div style="flex: 1;">\n    左側のテキスト\n  </div>\n  <div style="flex: 1;">\n    右側のテキスト\n  </div>\n</div>\n'
        action_2col.triggered.connect(lambda: self._insert_html(snip_2col))
        
        action_red = menu.addAction("赤文字・強調 (Red Span)")
        action_red.triggered.connect(lambda: self._insert_html('<span style="color: #d32f2f; font-weight: bold;">赤文字</span>'))
        
        action_clear = menu.addAction("回り込み解除 (Clearfix)")
        action_clear.triggered.connect(lambda: self._insert_html('\n<div style="clear: both;"></div>\n'))
        
        menu.addSeparator()
        
        action_info = menu.addAction("補足情報ブロック (Info)")
        action_info.triggered.connect(lambda: self._insert_html('\n::: info\n【情報】ここに補足説明を入力します。\n:::\n'))
        
        action_warning = menu.addAction("警告ブロック (Warning)")
        action_warning.triggered.connect(lambda: self._insert_html('\n::: warning\n【注意】ここに注意書きを入力します。\n:::\n'))
        
        action_noprint = menu.addAction("印刷非表示ブロック (No Print)")
        action_noprint.triggered.connect(lambda: self._insert_html('\n::: no-print\n【非表示メモ】この部分は編集中のみ見え、PDF出力時には削除されます。\n:::\n'))
        
        menu.addSeparator()
        
        action_math = menu.addAction("数式 (LaTeX Block)")
        math_snip = '\n$$\nx = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}\n$$\n'
        action_math.triggered.connect(lambda: self._insert_html(math_snip))
        
        action_mermaid = menu.addAction("図解 (Mermaid Chart)")
        mermaid_snip = '\n```mermaid\ngraph TD\n    A[Start] --> B{Process}\n    B -->|Yes| C[End]\n    B -->|No| D[Retry]\n```\n'
        action_mermaid.triggered.connect(lambda: self._insert_html(mermaid_snip))
        
        self.btn_html.setMenu(menu)
        
    def _setup_macro_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2D2D30; color: #D4D4D4; border: 1px solid #3E3E42; }
            QMenu::item { padding: 4px 24px; }
            QMenu::item:selected { background-color: #0E639C; }
        """)
        
        # 1. Date/Time Macros
        act_date = menu.addAction("今日の日付 (YYYY/MM/DD)")
        act_date.triggered.connect(lambda: self._insert_at_cursor(QDateTime.currentDateTime().toString("yyyy/MM/dd")))
        
        act_date_jp = menu.addAction("今日の日付 (YYYY年MM月DD日)")
        act_date_jp.triggered.connect(lambda: self._insert_at_cursor(QDateTime.currentDateTime().toString("yyyy年MM月dd日")))
        
        act_date_en = menu.addAction("今日の日付 (DD MMMM YYYY)")
        act_date_en.triggered.connect(lambda: self._insert_at_cursor(QLocale(QLocale.English).toString(QDateTime.currentDateTime(), "dd MMMM yyyy")))
        
        act_date_iso = menu.addAction("今日の日付 (YYYY-MM-DD)")
        act_date_iso.triggered.connect(lambda: self._insert_at_cursor(QDateTime.currentDateTime().toString("yyyy-MM-dd")))
        
        act_time = menu.addAction("現在の時刻 (HH:mm)")
        act_time.triggered.connect(lambda: self._insert_at_cursor(QDateTime.currentDateTime().toString("HH:mm")))
        
        menu.addSeparator()
        
        # 2. Document Info
        # Note: EditorPane doesn't directly know the filename, but we can pass it or 
        # emit a signal to request it. For now, simple placeholders or generic ones.
        act_filename = menu.addAction("ファイル名 (Placeholder)")
        act_filename.triggered.connect(lambda: self._insert_at_cursor("{{filename}}"))
        
        act_frontmatter = menu.addAction("Front Matter設定 (v4標準)")
        frontmatter_template = (
            "---\n"
            "project_name: \"プロジェクト名\"\n"
            "code_bg: \"#2d2d2d\"\n"
            "---\n"
            "## {{project_name}} 報告書\n"
        )
        act_frontmatter.triggered.connect(lambda: self._insert_at_cursor(frontmatter_template))

        act_layout_md = menu.addAction("HTML内Markdown (<m-d>レイアウト)")
        layout_md_snip = (
            '\n<div style="padding: 20px; border: 1px solid #ddd; border-radius: 8px;">\n'
            '  <m-d>\n'
            '  ### HTML内部のタイトル\n'
            '  - ここで **Markdown** が使えます\n'
            '  - リストや `code` もOK\n'
            '  </m-d>\n'
            '</div>\n'
        )
        act_layout_md.triggered.connect(lambda: self._insert_at_cursor(layout_md_snip))

        menu.addSeparator()
        
        # 3. Custom Quick Snippets (Experimental)
        act_sign = menu.addAction("署名スニペット (Signature)")
        act_sign.triggered.connect(lambda: self._insert_at_cursor("\n---\n**作成者:** [Your Name]\n**日付:** " + QDateTime.currentDateTime().toString("yyyy/MM/dd") + "\n"))
        
        self.btn_macro.setMenu(menu)
        
    def _insert_at_cursor(self, text):
        cursor = self.editor.textCursor()
        cursor.insertText(text)
        self.editor.setFocus()
        
    def _insert_html(self, html_text):
        cursor = self.editor.textCursor()
        cursor.insertText(html_text)
        self.editor.setFocus()
