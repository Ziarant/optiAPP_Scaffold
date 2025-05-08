import os, sys, json
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QTableWidgetItem

class CCondition(QWidget):
    
    def __init__(self):
        
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.configPath = self.parentPath + '\\preference\\config.json'
        self.curvesIDFile = self.parentPath + '\\preference\\curvesID.json'
        
        # 加载UI
        super(CCondition, self).__init__()
        self.ui = loadUi(self.path + '\\uis\\condition.ui', self)
        
        self.initUI()
        
    def initUI(self):
        # 默认配置文件
        self.lineEdit.setText(self.curvesIDFile)
        self.loadButton.clicked.connect(self.loadButton_clicked)
        self.saveButton.clicked.connect(self.saveButton_clicked)
        
        # 读取工况配置文件
        with open(self.configPath, 'r') as f:
            self.config = json.load(f)
        with open(self.curvesIDFile, 'r') as f:
            self.curvesID = json.load(f)
            
        for condition in self.curvesID.keys():
            leftId = str(self.curvesID[condition]['left'])
            rightId = str(self.curvesID[condition]['right'])
            
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            row = self.tableWidget.rowCount() - 1
            self.tableWidget.setItem(row, 0, QTableWidgetItem(condition))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(rightId))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(leftId))
            
    def loadButton_clicked(self):
        fileName = QFileDialog.getOpenFileName(parent = self,
                                            caption = '选择文件',
                                            directory = self.parentPath,
                                            filter = 'json文件(*.json)')
        if fileName[0] == '':
            return
        self.curvesIDFile = fileName[0]
        self.lineEdit.setText(self.curvesIDFile)

        # 读取工况配置文件
        with open(self.curvesIDFile, 'r') as f:
            self.curvesID = json.load(f)

        # 清空表格
        self.tableWidget.clearContents()

        self.tableWidget.setRowCount(0)
        for condition in self.curvesID.keys():
            leftId = str(self.curvesID[condition]['left'])
            rightId = str(self.curvesID[condition]['right'])

            self.tableWidget.insertRow(self.tableWidget.rowCount())
            row = self.tableWidget.rowCount() - 1
            self.tableWidget.setItem(row, 0, QTableWidgetItem(condition))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(rightId))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(leftId))
            
    def saveButton_clicked(self):
        # 保存工况配置文件
        with open(self.curvesIDFile, 'w') as f:
            json.dump(self.curvesID, f)

        # 修改config.json文件
        self.config['curvesIDFile'] = self.curvesIDFile
        with open(self.configPath, 'w') as f:
            json.dump(self.config, f)
            
        # 关闭窗口
        self.close()