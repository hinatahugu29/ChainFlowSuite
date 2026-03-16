import json
from PySide6.QtWidgets import QFileDialog, QMessageBox
from items import DTPTextItem, DTPImageItem, DTPShapeItem, DTPTableItem, DTPGroupItem

def save_project_to(scene, file_path, window=None):
    """指定パスに上書き保存（ダイアログなし）"""
    data = {'items': []}
    for item in scene.items():
        if item.parentItem() is not None:
            continue
        if isinstance(item, DTPTextItem):
            data['items'].append(item.to_dict())
        elif isinstance(item, DTPImageItem):
            data['items'].append(item.to_dict())
        elif isinstance(item, DTPShapeItem):
            data['items'].append(item.to_dict())
        elif isinstance(item, DTPTableItem):
            data['items'].append(item.to_dict())
        elif isinstance(item, DTPGroupItem):
            data['items'].append(item.to_dict())
    
    # Save swatches if window is provided
    if window and hasattr(window, 'swatch_panel'):
        data['swatches'] = window.swatch_panel.get_swatches()
        
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return file_path
    except Exception as e:
        print(f"Save error: {e}")
        return None

def save_project(scene, window, initial_dir=None):
    dir_path = initial_dir if initial_dir else ""
    file_path, _ = QFileDialog.getSaveFileName(window, "Save Project", dir_path, "Designer Files (*.cfd);;All Files (*)")
    if not file_path:
        return None

    result = save_project_to(scene, file_path, window)
    if result:
        QMessageBox.information(window, "保存完了", "プロジェクトを保存しました。")
    else:
        QMessageBox.critical(window, "エラー", "プロジェクトの保存に失敗しました。")
    return result

def load_project(scene, window, initial_dir=None):
    dir_path = initial_dir if initial_dir else ""
    file_path, _ = QFileDialog.getOpenFileName(window, "Open Project", dir_path, "Designer Files (*.cfd);;PyDTP Files (*.pydtp);;All Files (*)")
    if not file_path:
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        scene.clear()
        
        for item_data in data.get('items', []):
            item_type = item_data.get('type')
            if item_type == 'text':
                item = DTPTextItem.from_dict(item_data)
                scene.addItem(item)
            elif item_type == 'image':
                item = DTPImageItem.from_dict(item_data)
                scene.addItem(item)
            elif item_type == 'shape':
                item = DTPShapeItem.from_dict(item_data)
                scene.addItem(item)
            elif item_type == 'table':
                item = DTPTableItem.from_dict(item_data)
                scene.addItem(item)
            elif item_type == 'group':
                item = DTPGroupItem.from_dict(item_data)
                scene.addItem(item)
        
        if hasattr(window, 'undo_stack'):
            window.undo_stack.clear()
            
        # Restore swatches
        if hasattr(window, 'swatch_panel') and 'swatches' in data:
            window.swatch_panel.set_swatches(data['swatches'])
            
        QMessageBox.information(window, "読み込み完了", "プロジェクトを読み込みました。")
        return file_path
        
    except Exception as e:
        QMessageBox.critical(window, "エラー", f"プロジェクトの読み込みに失敗しました:\n{e}")
        return None
