"""
widgets/file_pane/context_menu.py
v14.1 Refactoring: コンテキストメニュー処理の分離

240行超の巨大メソッドをアクション登録方式に改善し、保守性を向上。
"""
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QApplication
from PySide6.QtGui import QAction

from core.file_operations import open_with_system, reveal_in_explorer


class ContextMenuBuilder:
    """コンテキストメニューの構築と実行を担当するクラス"""
    
    # メニュースタイル定数
    MENU_STYLE = """
        QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; }
        QMenu::item:selected { background-color: #094771; }
    """
    BATCH_MENU_STYLE = "QMenu { background-color: #3a1a1a; }"
    
    def __init__(self, file_pane):
        self.pane = file_pane
        
    def build_and_show(self, pos, view, proxy):
        """コンテキストメニューを構築して表示"""
        index = view.indexAt(pos)
        context = self._gather_context(view, proxy, index)
        
        menu = QMenu(self.pane)
        menu.setStyleSheet(self.MENU_STYLE)
        
        # メニュー構築
        self._add_batch_actions(menu, context)
        self._add_mark_actions(menu, context)
        self._add_file_actions(menu, context)
        self._add_path_actions(menu, context)
        self._add_archive_actions(menu, context)
        self._add_edit_actions(menu, context)
        self._add_clipboard_actions(menu, context)
        
        # メニュー表示・実行
        menu.exec(view.mapToGlobal(pos))
    
    def _gather_context(self, view, proxy, index):
        """メニュー構築に必要なコンテキスト情報を収集"""
        # 選択パスの収集
        all_selected_paths = []
        for v, p, _, _ in self.pane.views:
            indices = v.selectionModel().selectedIndexes()
            processed_rows = set()
            for idx in indices:
                row = idx.row()
                if row not in processed_rows:
                    processed_rows.add(row)
                    all_selected_paths.append(idx.data(Qt.UserRole))
        
        paths = list(set([p for p in all_selected_paths if p and os.path.exists(p)]))
        
        # マーク済みアイテム
        marked_list = []
        if self.pane._marked_paths_ref:
            marked_list = [p for p in self.pane._marked_paths_ref if os.path.exists(p)]
        
        # 選択情報
        selection = self.pane.get_selection_info(view, proxy)
        if not paths:
            paths = selection["paths"]
        
        # Office/アーカイブファイルの判定
        office_exts = ('.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt')
        archive_exts = ('.zip', '.7z', '.rar', '.tar', '.gz')
        
        office_files = [p for p in paths if not os.path.isdir(p) and p.lower().endswith(office_exts)]
        has_archive = any(p.lower().endswith(archive_exts) for p in paths if not os.path.isdir(p))
        
        # マーク状態
        has_unmarked = False
        has_marked = False
        if self.pane._marked_paths_ref is not None:
            for p in paths:
                p_abs = os.path.abspath(p)
                if p_abs in self.pane._marked_paths_ref:
                    has_marked = True
                else:
                    has_unmarked = True
        
        return {
            'view': view,
            'proxy': proxy,
            'index': index,
            'paths': paths,
            'marked_list': marked_list,
            'selection': selection,
            'office_files': office_files,
            'has_archive': has_archive or selection.get('has_zip', False),
            'has_unmarked': has_unmarked,
            'has_marked': has_marked,
            'num_files': len([p for p in paths if not os.path.isdir(p)]),
            'num_dirs': len([p for p in paths if os.path.isdir(p)]),
        }
    
    def _add_batch_actions(self, menu, ctx):
        """バッチ処理アクション（マーク済みアイテム用）"""
        marked_list = ctx['marked_list']
        if not marked_list:
            return
            
        batch_menu = menu.addMenu(f"★ Batch Actions ({len(marked_list)} marked)")
        batch_menu.setStyleSheet(self.BATCH_MENU_STYLE)
        
        # PDF変換
        office_exts = ('.docx', '.doc', '.xlsx', '.xls')
        marked_office = [p for p in marked_list if not os.path.isdir(p) and p.lower().endswith(office_exts)]
        if marked_office:
            act = QAction(f"Convert {len(marked_office)} marked office files to PDF", self.pane)
            act.triggered.connect(lambda: self.pane.action_convert_to_pdf(marked_office))
            batch_menu.addAction(act)
        
        # コピー・移動
        copy_act = QAction(f"Copy {len(marked_list)} marked items", self.pane)
        copy_act.triggered.connect(lambda: self.pane.action_aggregate_clipboard(marked_list, "copy"))
        batch_menu.addAction(copy_act)
        
        move_act = QAction(f"Cut/Move {len(marked_list)} marked items", self.pane)
        move_act.triggered.connect(lambda: self.pane.action_aggregate_clipboard(marked_list, "move"))
        batch_menu.addAction(move_act)
        
        batch_menu.addSeparator()
        clear_act = QAction("Clear All Marks", self.pane)
        clear_act.triggered.connect(self.pane.clear_all_marks)
        batch_menu.addAction(clear_act)
        
        menu.addSeparator()
    
    def _add_mark_actions(self, menu, ctx):
        """マーク/アンマーク アクション"""
        paths = ctx['paths']
        if not paths:
            return
            
        if ctx['has_unmarked']:
            mark_act = QAction("Mark Selected (Add to Bucket)", self.pane)
            mark_act.triggered.connect(lambda: self.pane.action_mark_selected(paths, True))
            menu.addAction(mark_act)
        
        if ctx['has_marked']:
            unmark_act = QAction("Unmark Selected (Remove from Bucket)", self.pane)
            unmark_act.triggered.connect(lambda: self.pane.action_mark_selected(paths, False))
            menu.addAction(unmark_act)
        
        menu.addSeparator()
    
    def _add_file_actions(self, menu, ctx):
        """ファイル操作アクション"""
        paths = ctx['paths']
        if not paths:
            return
        
        # ショートカット作成
        shortcut_act = QAction("Create Shortcut", self.pane)
        shortcut_act.triggered.connect(lambda: self.pane.action_create_shortcut(paths))
        menu.addAction(shortcut_act)
        
        # 開く
        open_act = QAction("Open", self.pane)
        open_act.triggered.connect(lambda: self._open_files(paths))
        menu.addAction(open_act)
        
        # PDF変換
        if ctx['office_files']:
            label = f"Convert {len(ctx['office_files'])} files to PDF" if len(ctx['office_files']) > 1 else "Convert to PDF"
            pdf_act = QAction(label, self.pane)
            pdf_act.triggered.connect(lambda: self.pane.action_convert_to_pdf(ctx['office_files']))
            menu.addAction(pdf_act)
        
        # 別のプログラムで開く
        if len(paths) == 1 and not os.path.isdir(paths[0]):
            open_with_act = QAction("Open with...", self.pane)
            open_with_act.triggered.connect(lambda: self.pane.open_with_dialog(paths[0]))
            menu.addAction(open_with_act)
        
        # エクスプローラーで表示
        reveal_act = QAction("Reveal in Explorer", self.pane)
        reveal_act.triggered.connect(lambda: reveal_in_explorer(paths[0]))
        menu.addAction(reveal_act)
        
        # プロパティ
        if len(paths) == 1:
            prop_act = QAction("Properties", self.pane)
            prop_act.triggered.connect(lambda: self.pane.action_show_properties(paths[0]))
            menu.addAction(prop_act)
        
        menu.addSeparator()
    
    def _add_path_actions(self, menu, ctx):
        """パスコピーアクション"""
        paths = ctx['paths']
        if not paths:
            return
            
        copy_menu = menu.addMenu("Copy Path Special")
        
        actions = [
            ("Copy Full Path", lambda: self._copy_text("\n".join(paths))),
            ("Copy Name", lambda: self._copy_text("\n".join([os.path.basename(p) for p in paths]))),
            ('Copy as "Path"', lambda: self._copy_text("\n".join([f'"{p}"' for p in paths]))),
            ("Copy Unix Path (/)", lambda: self._copy_text("\n".join([p.replace("\\", "/") for p in paths]))),
        ]
        
        for label, handler in actions:
            act = QAction(label, self.pane)
            act.triggered.connect(handler)
            copy_menu.addAction(act)
        
        # ターミナル
        term_act = QAction("Terminal Here", self.pane)
        term_act.triggered.connect(lambda: self.pane.action_terminal(paths))
        menu.addAction(term_act)
        
        menu.addSeparator()
    
    def _add_archive_actions(self, menu, ctx):
        """アーカイブ関連アクション"""
        paths = ctx['paths']
        if not paths:
            return
            
        zip_act = QAction("Compress to ZIP...", self.pane)
        zip_act.triggered.connect(lambda: self.pane.action_zip(ctx['selection']))
        menu.addAction(zip_act)
        
        if ctx['has_archive']:
            unzip_act = QAction("Extract Here (Smart)", self.pane)
            unzip_act.triggered.connect(lambda: self.pane.action_unzip(ctx['selection']))
            menu.addAction(unzip_act)
        
        menu.addSeparator()
    
    def _add_edit_actions(self, menu, ctx):
        """編集系アクション"""
        paths = ctx['paths']
        
        # 新規ファイル
        new_file_act = QAction("New File...", self.pane)
        new_file_act.triggered.connect(lambda: self.pane.action_new_file(ctx['view'], ctx['proxy']))
        menu.addAction(new_file_act)

        # 新規フォルダ（常に表示）
        new_folder_act = QAction("New Folder", self.pane)
        new_folder_act.triggered.connect(lambda: self.pane.action_new_folder(ctx['view'], ctx['proxy']))
        menu.addAction(new_folder_act)
        
        if paths:
            # お気に入り追加（ディレクトリのみ）
            if all(os.path.isdir(p) for p in paths):
                fav_act = QAction("Add to Favorites", self.pane)
                fav_act.triggered.connect(lambda: [self.pane.parent_filer.add_to_favorites(p) for p in paths])
                menu.addAction(fav_act)
            
            # リネーム
            rename_act = QAction("Rename", self.pane)
            rename_act.triggered.connect(self.pane.action_rename)
            menu.addAction(rename_act)
            
            # 削除
            delete_act = QAction("Delete", self.pane)
            delete_act.triggered.connect(self.pane.action_delete)
            menu.addAction(delete_act)
    
    def _add_clipboard_actions(self, menu, ctx):
        """クリップボード操作アクション"""
        paths = ctx['paths']
        
        menu.addSeparator()
        
        if paths:
            # ラベル生成
            label_suffix = ""
            if len(paths) > 1:
                parts = []
                if ctx['num_files'] > 0:
                    parts.append(f"{ctx['num_files']} files")
                if ctx['num_dirs'] > 0:
                    parts.append(f"{ctx['num_dirs']} dirs")
                label_suffix = f" ({', '.join(parts)})"
            
            cut_act = QAction(f"Cut{label_suffix}", self.pane)
            cut_act.triggered.connect(lambda: self.pane.action_aggregate_clipboard(paths, "move"))
            menu.addAction(cut_act)
            
            copy_act = QAction(f"Copy{label_suffix}", self.pane)
            copy_act.triggered.connect(lambda: self.pane.action_aggregate_clipboard(paths, "copy"))
            menu.addAction(copy_act)
        
        # 貼り付け
        if self.pane.parent_filer.internal_clipboard["paths"]:
            paste_act = QAction("Paste", self.pane)
            paste_act.triggered.connect(lambda: self._paste(ctx))
            menu.addAction(paste_act)
    
    # --- Helper Methods ---
    
    def _open_files(self, paths):
        """ファイルを開く"""
        for p in paths:
            open_with_system(p)
    
    def _copy_text(self, text):
        """テキストをクリップボードにコピー"""
        QApplication.clipboard().setText(text)
    
    def _paste(self, ctx):
        """貼り付け処理"""
        dest_dir = None
        if ctx['index'].isValid():
            p_under_mouse = ctx['index'].data(Qt.UserRole)
            if p_under_mouse and os.path.isdir(p_under_mouse):
                dest_dir = p_under_mouse
        self.pane.action_paste(dest_dir)
