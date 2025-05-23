import os, sys, json
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QTableWidgetItem

class CStructure(QWidget):
    
    def __init__(self):
        
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.configPath = self.parentPath + '\\preference\\config.json'
        
        # 加载UI
        super(CStructure, self).__init__()
        self.ui = loadUi(self.path + '\\uis\\structureSet.ui', self)
        
        self.initUI()
        
    def initUI(self):
        # 默认配置文件
        with open(self.configPath, 'r') as f:
            self.config = json.load(f)

        nodeSetName : str = self.config["nodeSetName"]
        minStress : float = self.config["minTargetStress"]
        maxStress : float = self.config["maxTargetStress"]
        maxIter : int = self.config["maxIter"]["structureOpti"]
        elemSize : float = self.config["elemSize"]
        autoSubmit : bool = self.config["autoSubmit"]

        self.lineEdit.setText(nodeSetName)
        self.dsp_minStress.setValue(minStress)
        self.dsp_maxStress.setValue(maxStress)
        self.spinBox.setValue(maxIter)
        self.dsp_elemSize.setValue(elemSize)
        self.saveButton.clicked.connect(self.saveConfig)
        self.cb_autoSubmit.setChecked(autoSubmit)

        self.lineEdit.textChanged.connect(self.lineEditChanged)
        self.dsp_minStress.valueChanged.connect(self.minStress_valueChanged)
        self.dsp_maxStress.valueChanged.connect(self.maxStress_valueChanged)
        self.spinBox.valueChanged.connect(self.maxIterChanged)
        self.dsp_elemSize.valueChanged.connect(self.elemSize_valueChanged)

    def lineEditChanged(self):
        text = self.lineEdit.text()
        self.config["nodeSetName"] = text

    def minStress_valueChanged(self, value : float):
        self.config["minTargetStress"] = value

    def maxStress_valueChanged(self, value : float):
        self.config["maxTargetStress"] = value
    
    def maxIterChanged(self, value : int):
        self.config["maxIter"]["structureOpti"] = value

    def elemSize_valueChanged(self, value : float):
        self.config["elemSize"] = value

    def saveConfig(self):
        # 设置minValue ＜ maxValue
        minValue = min(self.config["minTargetStress"], self.config["maxTargetStress"])
        maxValue = max(self.config["minTargetStress"], self.config["maxTargetStress"])
        self.config["minTargetStress"] = minValue
        self.config["maxTargetStress"] = maxValue

        with open(self.configPath, 'w') as f:
            json.dump(self.config, f, indent=4)