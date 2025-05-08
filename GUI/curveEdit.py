import os, sys, json
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
import json
from PyQt5.QtWidgets import QTableWidgetItem

class CurveEdit(QWidget):
    
    def __init__(self, curveJsonFile:str):
        
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.curveJsonFile = curveJsonFile
        
        # 加载UI
        super(CurveEdit, self).__init__()
        self.ui = loadUi(self.path + '\\uis\\curveEdit.ui', self)
        
        self.initUI()
        
    def initUI(self):
        
        curveName = os.path.basename(self.curveJsonFile).split('.')[0]
        self.lineEdit.setText(curveName[10:])
        self.saveButton.clicked.connect(self.saveButton_clicked)
        
        self.tableWidget.itemChanged.connect(self.tableWidget_itemChanged)
        
        with open(self.curveJsonFile, 'r') as f:
            self.curveJson = json.load(f)
            
        for loadName in self.curveJson.keys():
            leftValue = self.curveJson[loadName]['left']
            rightValue = self.curveJson[loadName]['right']
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            row = self.tableWidget.rowCount() - 1
            nameWidget = QTableWidgetItem(loadName)
            self.tableWidget.setItem(row, 0, nameWidget)
            leftWidget = QTableWidgetItem(str(leftValue))
            self.tableWidget.setItem(row, 1, leftWidget)
            rightWidget = QTableWidgetItem(str(rightValue))
            self.tableWidget.setItem(row, 2, rightWidget)
            
    def tableWidget_itemChanged(self, item:QTableWidgetItem):
        row, col = item.row(), item.column()
        if col == 0:
            return
        else:
            loadName = self.tableWidget.item(row, 0).text()
            value = self.tableWidget.item(row, col).text()
            if col == 1:
                self.curveJson[loadName]['right'] = float(value)
            elif col == 2:
                self.curveJson[loadName]['left'] = float(value)
            
    def saveButton_clicked(self):
        # 保存工况配置文件
        with open(self.curveJsonFile, 'w') as f:
            json.dump(self.curveJson, f)

        # 关闭窗口
        self.close()
            
        