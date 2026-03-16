from PySide6.QtGui import QUndoCommand

class AddItemCommand(QUndoCommand):
    def __init__(self, scene, item, pos):
        super().__init__("Add Item")
        self.scene = scene
        self.item = item
        self.pos = pos

    def redo(self):
        self.scene.addItem(self.item)
        self.item.setPos(self.pos)
        self.scene.clearSelection()
        self.item.setSelected(True)

    def undo(self):
        self.scene.removeItem(self.item)

class RemoveItemCommand(QUndoCommand):
    def __init__(self, scene, item):
        super().__init__("Remove Item")
        self.scene = scene
        self.item = item
        self.pos = item.pos()

    def redo(self):
        self.scene.removeItem(self.item)

    def undo(self):
        self.scene.addItem(self.item)
        self.item.setPos(self.pos)

class MoveItemCommand(QUndoCommand):
    def __init__(self, item, old_pos, new_pos):
        super().__init__("Move Item")
        self.item = item
        self.old_pos = old_pos
        self.new_pos = new_pos

    def redo(self):
        self.item.setPos(self.new_pos)

    def undo(self):
        self.item.setPos(self.old_pos)

# Property change command can be generic
class PropertyChangeCommand(QUndoCommand):
    def __init__(self, item, prop_name, new_value):
        super().__init__(f"Change {prop_name}")
        self.item = item
        self.prop_name = prop_name
        self.new_value = new_value
        # Capture old value for undo
        if hasattr(item, 'get_property'):
            self.old_value = item.get_property(prop_name)
        else:
            self.old_value = None # Should not happen if interface is consistent

    def redo(self):
        import logging
        logging.debug(f"[Command] PropertyChangeCommand redo: item={self.item}, prop='{self.prop_name}', val='{self.new_value}'")
        if hasattr(self.item, 'set_property'):
            self.item.set_property(self.prop_name, self.new_value)
            self.item.update()

    def undo(self):
        import logging
        logging.debug(f"[Command] PropertyChangeCommand undo: item={self.item}, prop='{self.prop_name}', val='{self.old_value}'")
        if hasattr(self.item, 'set_property'):
            self.item.set_property(self.prop_name, self.old_value)
            self.item.update()

    def id(self):
        # Qt requires 32-bit int range
        return hash((self.item, self.prop_name)) % 2147483647

    def mergeWith(self, other):
        # Merge if same command ID (same item, same property)
        if other.id() != self.id():
            return False
        # Update the new value to the latest one
        self.new_value = other.new_value
        return True

class ZValueCommand(QUndoCommand):
    def __init__(self, items, increment):
        action_name = "Bring Forward" if increment > 0 else "Send Backward"
        super().__init__(action_name)
        self.items = items
        self.increment = increment
        # Store old values
        self.old_values = {item: item.zValue() for item in items}

    def redo(self):
        for item in self.items:
            item.setZValue(item.zValue() + self.increment)

    def undo(self):
        for item, val in self.old_values.items():
            item.setZValue(val)

class AlignItemsCommand(QUndoCommand):
    def __init__(self, scene, items, align_type):
        super().__init__(f"Align {align_type}")
        self.scene = scene
        self.items = items
        self.align_type = align_type
        self.old_positions = {item: item.pos() for item in items}
        self.new_positions = {}
        self._calculate_positions()

    def _calculate_positions(self):
        if not self.items: return
        
        from PySide6.QtCore import QPointF
        
        # Calculate bounding box
        if len(self.items) == 1:
            # Align to page (scene rect)
            total_rect = self.scene.sceneRect()
        else:
            # Align to selection bounds
            rects = [item.sceneBoundingRect() for item in self.items]
            if not rects: return
            
            total_rect = rects[0]
            for r in rects[1:]:
                total_rect = total_rect.united(r)
            
        for item in self.items:
            rect = item.sceneBoundingRect()
            pos = item.pos()
            
            new_x = pos.x()
            new_y = pos.y()
            
            if self.align_type == 'left':
                new_x += total_rect.left() - rect.left()
            elif self.align_type == 'center_h':
                new_x += total_rect.center().x() - rect.center().x()
            elif self.align_type == 'right':
                new_x += total_rect.right() - rect.right()
            elif self.align_type == 'top':
                 new_y += total_rect.top() - rect.top()
            elif self.align_type == 'center_v':
                new_y += total_rect.center().y() - rect.center().y()
            elif self.align_type == 'bottom':
                new_y += total_rect.bottom() - rect.bottom()
                
            self.new_positions[item] = QPointF(new_x, new_y)

    def redo(self):
        for item, pos in self.new_positions.items():
            item.setPos(pos)

    def undo(self):
        for item, pos in self.old_positions.items():
            item.setPos(pos)

class TableTextChangeCommand(QUndoCommand):
    """表セルのテキスト変更Undoコマンド"""
    def __init__(self, table, row, col, old_text, new_text):
        super().__init__("セルテキスト変更")
        self.table = table
        self.row = row
        self.col = col
        self.old_text = old_text
        self.new_text = new_text
    
    def redo(self):
        if self.row < len(self.table.cells) and self.col < len(self.table.cells[self.row]):
            self.table.cells[self.row][self.col].setPlainText(self.new_text)
    
    def undo(self):
        if self.row < len(self.table.cells) and self.col < len(self.table.cells[self.row]):
            self.table.cells[self.row][self.col].setPlainText(self.old_text)

class GroupCommand(QUndoCommand):
    def __init__(self, scene, items):
        super().__init__("グループ化")
        self.scene = scene
        self.items = list(items)
        self.group_z = max((item.zValue() for item in self.items), default=0)
        self.group = None

    def redo(self):
        from items import DTPGroupItem
        self.group = DTPGroupItem()
        self.scene.addItem(self.group)
        self.group.setZValue(self.group_z)
        for item in self.items:
            self.group.addToGroup(item)
        self.scene.clearSelection()
        self.group.setSelected(True)

    def undo(self):
        if self.group:
            self.scene.destroyItemGroup(self.group)
            self.group = None
        self.scene.clearSelection()
        for item in self.items:
            item.setSelected(True)


class UngroupCommand(QUndoCommand):
    def __init__(self, scene, group_item):
        super().__init__("グループ解除")
        self.scene = scene
        self.group = group_item
        from items import ResizeHandle
        self.items = [item for item in group_item.childItems() if not isinstance(item, ResizeHandle)]
        self.group_z = group_item.zValue()

    def redo(self):
        if self.group:
            self.scene.destroyItemGroup(self.group)
            self.group = None
        self.scene.clearSelection()
        for item in self.items:
            item.setSelected(True)

    def undo(self):
        from items import DTPGroupItem
        self.group = DTPGroupItem()
        self.scene.addItem(self.group)
        self.group.setZValue(self.group_z)
        for item in self.items:
            self.group.addToGroup(item)
        self.scene.clearSelection()
        self.group.setSelected(True)

class VisibilityChangeCommand(QUndoCommand):
    def __init__(self, item, new_visible):
        super().__init__("表示切替")
        self.item = item
        self.new_visible = new_visible
        self.old_visible = item.isVisible()

    def redo(self):
        self.item.setVisible(self.new_visible)

    def undo(self):
        self.item.setVisible(self.old_visible)

class LockChangeCommand(QUndoCommand):
    def __init__(self, item, new_locked):
        super().__init__("ロック切替")
        self.item = item
        self.new_locked = new_locked
        self.old_locked = getattr(item, 'locked', False)

    def redo(self):
        if hasattr(self.item, 'set_locked'):
            self.item.set_locked(self.new_locked)

    def undo(self):
        if hasattr(self.item, 'set_locked'):
            self.item.set_locked(self.old_locked)
