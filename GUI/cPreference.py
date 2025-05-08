import os, sys, json
from PyQt5.QtWidgets import QWidget
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QFileDialog

class CPreference(QWidget):
    
    def __init__(self):
        
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.configPath = self.parentPath + '\\preference\\config.json'
        
        # 加载UI
        super(CPreference, self).__init__()
        self.ui = loadUi(self.path + '\\uis\\preference.ui', self)
        
        self.initUI()
        
    def initUI(self):
        # 导入预设config
        with open(self.configPath, 'r') as f:
            self.config = json.load(f)
        
        self.hmtemplateLineEdit.setText(self.config['hmtemplatefilePath'])
        self.hmbatchLineEdit.setText(self.config['hmbatchPath'])
        
        self.hmtemplateButton.clicked.connect(self.hmtemplateButton_clicked)
        self.hmbatchButton.clicked.connect(self.hmbatchButton_clicked)
        
    def hmtemplateButton_clicked(self):
        fileName = QFileDialog.getOpenFileName(parent = self,
                                            caption = '选择hm-abaqus输出模板文件',
                                            directory = self.parentPath,
                                            filter = 'hypermesh模板(*.3d)')
        if fileName[0] == '':
            return
        self.hmtemplateFileName = fileName[0]
        self.hmtemplateLineEdit.setText(self.hmtemplateFileName)
        
        # 修改json文件
        self.config['hmtemplatefilePath'] = self.hmtemplateFileName
        with open(self.configPath, 'w') as f:
            json.dump(self.config, f)
            
    def hmbatchButton_clicked(self):
        fileName = QFileDialog.getOpenFileName(parent = self,
                                            caption = '选择hmbatch程序',
                                            directory = self.parentPath,
                                            filter = 'hmbatch(*.exe)')
        if fileName[0] == '':
            return
        self.hmbatchFileName = fileName[0]
        self.hmbatchLineEdit.setText(self.hmbatchFileName)

        # 修改json文件
        self.config['hmbatchPath'] = self.hmbatchFileName
        with open(self.configPath, 'w') as f:
            json.dump(self.config, f)