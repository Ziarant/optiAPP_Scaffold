import os, json
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QToolButton
from PyQt5.QtCore import *
from PyQt5.uic import loadUi # type: ignore


class CMainWindow(QMainWindow):
    def __init__(self):
        # TODO:数据初始化
        
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.configPath = self.parentPath + '\\preference\\config.json'
        
        # 加载GUI
        super(CMainWindow, self).__init__()
        self.ui = loadUi(self.path + '\\uis\\mainWindow.ui', self)
        
        self.initUI()
        
    def initUI(self):
        # 导入预设config
        with open(self.configPath, 'r') as f:
            self.config = json.load(f)
        self.hmLineEdit.setText(self.config['hmfilePath'])
        self.workPathLineEdit.setText(self.config['workPath'])
        
        self.preferenceButton.clicked.connect(self.preferenceButton_clicked)
        self.hmButton.clicked.connect(self.hmButton_clicked)
        self.workPathButton.clicked.connect(self.workPathButton_clicked)
        
        # 工况设置
        self.conditionButton.clicked.connect(self.conditionButton_clicked)
        self.addButton.clicked.connect(self.addButton_clicked)
        
        # 结构优化
        self.runStructureButton.clicked.connect(self.runStructureButton_clicked)
        
        # 梁径优化
        
        # 关联nameWidget与editButton:
        self.conditionTableWidget.itemChanged.connect(self.nameWidget_textChanged)
        
        for loadName in self.config['conditions'].keys():
            # conditionTableWidget 添加数据
            self.conditionTableWidget.insertRow(self.conditionTableWidget.rowCount())
            row = self.conditionTableWidget.rowCount() - 1
            self.conditionTableWidget.setRowHeight(row, 40)
            nameWidget = QTableWidgetItem(loadName)
            self.conditionTableWidget.setItem(row, 0, nameWidget)
            editButton = self.conditionTableWidget.createEditButton(loadName)
            self.conditionTableWidget.setCellWidget(row, 1, editButton)
        
    def preferenceButton_clicked(self):
        from GUI.cPreference import CPreference
        self.preference = CPreference()
        self.preference.show()
        
    def hmButton_clicked(self):
        fileName = QFileDialog.getOpenFileName(parent = self, 
                                            caption = '选择hm模型文件',
                                            directory = self.parentPath,
                                            filter = 'hypermesh模型(*.hm)')
        if fileName[0] == '':
            return
        
        self.hmFileName = fileName[0]
        self.hmLineEdit.setText(self.hmFileName)
        self.config['hmfilePath'] = self.hmFileName
        with open(self.configPath, 'w') as f:
            json.dump(self.config, f, indent=4)
        
    def workPathButton_clicked(self):
        workPathName = QFileDialog.getExistingDirectory(parent = self,
                                            caption = '选择文件夹',
                                            directory = self.parentPath)
        if workPathName == '':
            return
        self.workPathLineEdit.setText(workPathName)
        self.config['workPath'] = workPathName
        with open(self.configPath, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def conditionButton_clicked(self):
        from GUI.cCondition import CCondition
        self.condition = CCondition()
        self.condition.show()
            
    def addButton_clicked(self):
        # conditionTableWidget 添加数据
        self.conditionTableWidget.insertRow(self.conditionTableWidget.rowCount())
        row = self.conditionTableWidget.rowCount() - 1
        self.conditionTableWidget.setRowHeight(row, 40)
        nameWidget = QTableWidgetItem('请输入工况名称')
        self.conditionTableWidget.setItem(row, 0, nameWidget)
        
        # 使用唯一ID标记editButton
        name = nameWidget.text()
        editButton = self.conditionTableWidget.createEditButton(str(name))
        self.conditionTableWidget.setCellWidget(row, 1, editButton)
        
    def nameWidget_textChanged(self, item:QTableWidgetItem):
        row = item.row()
        name = item.text()
        cellWidget = self.conditionTableWidget.cellWidget(row, 1)
        if cellWidget == None:
            return
        
        editButton = cellWidget.findChildren(QToolButton)[0]
        if editButton == None:
            return
        oldName = editButton.objectName()[5:]
        editButton.setObjectName('edit-' + name)
        
        configFilePath = self.parentPath + '\\preference'
        configFileName = 'condition_' + oldName + '.json'
        
        newFilePath = configFilePath + '\\' + 'condition_' + name + '.json'
        newFilePath.replace('\\', '/')
            
        # 文件重命名：
        if configFileName in os.listdir(configFilePath):
            # 文件名冲突：删除原文件
            # TODO：可以增加提示和选择
            if 'condition_{}.json'.format(name) in os.listdir(configFilePath):
                os.remove(newFilePath)
            os.rename(configFilePath + '\\' + configFileName, newFilePath)
        else:
            # 新建文件
            curve = {}
            curvesIDFile = self.config['curvesIDFile']
            with open(curvesIDFile, 'r') as f:
                curvesID = json.load(f)
            for loadName in curvesID.keys():
                curve[loadName] = {'left': "", 'right': ""}
            with open(configFilePath + '\\' + 'condition_' + name + '.json', 'w') as f:
                json.dump(curve, f, indent=4)
                
        # 删除原键值
        if oldName in self.config['conditions'].keys():
            self.config['conditions'].pop(oldName)
        self.config['conditions'][name] = newFilePath
        
        # 保存config文件
        with open(self.configPath, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def runStructureButton_clicked(self):
        # TODO:更新表
        # 进行结构优化计算
        from functions.structureOpti import MainStructureOpti
        mainStructureOpti = MainStructureOpti(self.configPath)
        mainStructureOpti.run()