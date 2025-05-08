import sys
from PyQt5.QtWidgets import QTableWidget

sys.path.append("..")
from .tableExpand import TableExpand

class CTable(QTableWidget, TableExpand):
    def __init__(self, parent=None):
        super(CTable, self).__init__(parent)