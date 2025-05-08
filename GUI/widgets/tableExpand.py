import sys, os, json
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon

class TableExpand():
    def __init__(self):
        self.isExpand = True
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.configPath = os.path.dirname(self.parentPath) + '\\preference\\config.json'
        self.icon = self.parentPath  + '\\icons\\edit.png'
        
        with open(self.configPath, 'r') as f:
            self.config = json.load(f)
        
    def createEditButton(self, name:str):
        # 导入编辑按钮
        widget = QWidget()
        widget.setParent(self)
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(0)
        self.editButton = QToolButton()
        self.editButton.setObjectName('edit-' + name)
        self.editButton.setText('')
        self.editButton.setToolTip('编辑')
        self.editButton.setIcon(QIcon(self.icon))
        self.editButton.setFixedSize(35, 35)
        self.editButton.setIconSize(QSize(35, 35))
        self.editButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.editButton.clicked.connect(self.editButton_clicked)
        box_layout.addWidget(self.editButton)
        widget.setLayout(box_layout)
        return widget
    
    def editButton_clicked(self):
        button = self.sender()
        if button:
            name = button.objectName()[5:]
        else:
            raise('button is None')
        
        curveJsonFile = 'condition_{}.json'.format(name)
        filePath = os.path.dirname(self.parentPath) + "\\preference"
        if curveJsonFile in os.listdir(filePath):
            pass
        else:
            # 创建新的曲线文件
            with open(filePath + '\\' + curveJsonFile, 'w') as f:
                json.dump({}, f)
        
        # 创建表单编辑器
        # tableWidgetItem : QTableWidgetItem = self.findChild(QTableWidgetItem, name)
        from GUI.curveEdit import CurveEdit
        self.curveEditWidget = CurveEdit(filePath + '\\' + curveJsonFile)
        self.curveEditWidget.show()