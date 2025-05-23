import os, sys, json
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QTableWidgetItem

class CBeamSet(QWidget):
    
    def __init__(self):
        
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.configPath = self.parentPath + '\\preference\\config.json'
        
        # 加载UI
        super(CBeamSet, self).__init__()
        self.ui = loadUi(self.path + '\\uis\\beamSet.ui', self)
        
        self.initUI()
        
    def initUI(self):
        # 默认配置文件
        with open(self.configPath, 'r') as f:
            self.config = json.load(f)

        # 修改
        maxIter = self.config["maxIter"]["beamOpti"]
        self.spinBox.setValue(maxIter)
        self.spinBox.valueChanged.connect(self.editMaxIter)
            
        self.elemSet = self.config['elemSet']
        for elemSetName in self.elemSet.keys():
            diameter = self.elemSet[elemSetName]['diameter']
            matCode = self.elemSet[elemSetName]['matCode']
            csa =  diameter * diameter * 0.7854         # CSA:横截面积
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            row = self.tableWidget.rowCount() - 1
            self.tableWidget.setItem(row, 0, QTableWidgetItem(elemSetName))
            self.tableWidget.setItem(row, 1, QTableWidgetItem("{:.2f}".format(diameter)))
            self.tableWidget.setItem(row, 2, QTableWidgetItem("{:.4f}".format(csa)))
            self.tableWidget.setItem(row, 3, QTableWidgetItem("{}".format(matCode)))

    def editMaxIter(self, value:int):
        maxIter = self.spinBox.value()
        self.config["maxIter"]["beamOpti"] = maxIter
        with open(self.configPath, 'w') as f:
            json.dump(self.config, f, indent=4)