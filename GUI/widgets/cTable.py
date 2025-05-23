import sys
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt

sys.path.append("..")
from .tableExpand import TableExpand

class CTable(QTableWidget, TableExpand):
    def __init__(self, parent=None):
        super(CTable, self).__init__(parent)

    def mousePressEvent(self, event:QMouseEvent):
        if event.button() != Qt.RightButton:
            super().mousePressEvent(event)
        
        # 右键呼出菜单：
        pos = event.pos()
        item = self.itemAt(pos)
        if hasattr(item, 'createRightMenu'):
            pos =self.mapToGlobal(pos)
            item.createRightMenu(pos)