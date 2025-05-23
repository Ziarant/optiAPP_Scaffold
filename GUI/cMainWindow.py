import os, json
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidgetItem, QToolButton
from PyQt5.QtCore import *
from PyQt5.uic import loadUi
from GUI.widgets.cTableWidgetItem import CTableWidgetItem

class CMainWindow(QMainWindow):
    def __init__(self):
        # TODO:数据初始化
        
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.configPath = self.parentPath + '\\preference\\config.json'
        
        # 加载GUI
        super(CMainWindow, self).__init__()
        self.ui = loadUi(self.path + '\\uis\\mainWindow.ui', self)
        
        # 优化过程数据
        self.structureOptiData : dict = {}
        self.beamOptiData : dict = {}
        self.monitor = None

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
        self.structureButton.clicked.connect(self.structureButton_clicked)
        self.runStructureButton.clicked.connect(self.runStructureButton_clicked)
        self.structureMonitorButton.clicked.connect(self.structureMonitorButton_clicked)
        
        # 梁径优化
        self.checkStructureOdb()        # 检查结构优化结果：如存在结果，则可直接运行梁径优化
        self.extendButton.clicked.connect(self.extendButton_clicked)
        self.beamButton.clicked.connect(self.beamButton_clicked)
        self.runBeamButton.clicked.connect(self.runBeamButton_clicked)
        self.beamMonitorButton.clicked.connect(self.beamMonitorButton_clicked)
        
        # 关联nameWidget与editButton:
        self.conditionTableWidget.itemChanged.connect(self.nameWidget_textChanged)
        
        for loadName in self.config['conditions'].keys():
            # conditionTableWidget 添加数据
            self.conditionTableWidget.insertRow(self.conditionTableWidget.rowCount())
            row = self.conditionTableWidget.rowCount() - 1
            nameWidget = QTableWidgetItem(loadName)
            self.conditionTableWidget.setRowHeight(row, 40)
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
        nameWidget = QTableWidgetItem('请输入工况名称')
        self.conditionTableWidget.setItem(row, 0, nameWidget)
        self.conditionTableWidget.setRowHeight(row, 40)
        
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
        newFilePath = newFilePath.replace('\\', '/')
            
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
        newFilePath : str = newFilePath.replace('\\', '/')
        self.config['conditions'][name] = newFilePath
        
        # 保存config文件
        with open(self.configPath, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def structureButton_clicked(self):
        # 打开结构优化设置
        from GUI.cStructure import CStructure
        self.structure = CStructure()
        self.structure.show()
            
    def runStructureButton_clicked(self):
        # 进行结构优化计算
        from functions.structureOpti import MainStructureOpti
        self.runStructureButton.setEnabled(False)
        for condition in self.config['conditions'].keys():
            self.structureTable.insertRow(self.structureTable.rowCount())
            row = self.structureTable.rowCount() - 1
            nameWidget = QTableWidgetItem(condition)
            self.structureTable.setRowHeight(row, 40)
            self.structureTable.setItem(row, 0, nameWidget)
        
        self.mainStructureOpti = MainStructureOpti(self.configPath)
        self.mainStructureOpti.monitorStateSignal.connect(self.structureTableUpdate)
        self.mainStructureOpti.completeSignal.connect(self.structureOptiCompleted)
        self.mainStructureOpti.monitorDataSignal.connect(self.structureOptiDataUpdate)
        # 使用start方法启动线程，防止主线程阻塞
        self.mainStructureOpti.setTerminationEnabled(True)
        self.mainStructureOpti.start()
        
    def checkStructureOdb(self):
        # 检查结构优化结果：如存在结果，则extendButton激活，可直接运行梁径优化
        with open(self.configPath, 'r') as f:
            self.config = json.load(f)
        if self.config['odbFile']['structureOpti'].keys() is not None:
            self.extendButton.setEnabled(True)

    def extendButton_clicked(self):
        # extendButton激活，可直接运行梁径优化
        with open(self.configPath, 'r') as f:
            self.config = json.load(f)
        if self.config['odbFile']['structureOpti'].keys() is not None:
            self.runBeamButton.setEnabled(True)
            for conditionName in self.config['odbFile']['structureOpti'].keys():
                self.beamTable.insertRow(self.beamTable.rowCount())
                row = self.beamTable.rowCount() - 1
                nameWidget = QTableWidgetItem(conditionName)
                self.beamTable.setRowHeight(row, 40)
                self.beamTable.setItem(row, 0, nameWidget)
                odbPath = self.config['odbFile']['structureOpti'][conditionName]
                odbName = os.path.basename(odbPath)
                odbWidget = QTableWidgetItem(odbName)
                self.beamTable.setItem(row, 1, odbWidget)
            # 导入后禁用extendButton
            self.extendButton.setEnabled(False)
        
    def runBeamButton_clicked(self):
        # 进行梁径优化计算
        from functions.MainBeamOpti import BeamOpti
        self.runBeamButton.setEnabled(False)
        if self.beamTable.rowCount() <= 1:
            for condition in self.config['conditions'].keys():
                self.beamTable.insertRow(self.beamTable.rowCount())
                row = self.beamTable.rowCount() - 1
                nameWidget = QTableWidgetItem(condition)
                self.beamTable.setRowHeight(row, 40)
                self.beamTable.setItem(row, 0, nameWidget)

        self.mainBeamOpti = BeamOpti(self.configPath)
        self.mainBeamOpti.monitorStateSignal.connect(self.beamTableUpdate)
        self.mainBeamOpti.monitorDataSignal.connect(self.beamOptiDataUpdate)
        # 使用start方法启动线程，防止主线程阻塞
        self.mainBeamOpti.setTerminationEnabled(True)
        self.mainBeamOpti.start()
        
    def beamButton_clicked(self):
        # 打开梁径设置
        from GUI.cBeamSet import CBeamSet
        self.beamSet = CBeamSet()
        self.beamSet.show()

    def structureTableUpdate(self, cycle:int, condition:str, state:str):
        # 添加Cycle列
        if cycle == self.structureTable.columnCount() - 1:
            self.structureTable.insertColumn(self.structureTable.columnCount())
            col = self.structureTable.columnCount() - 1
            nameWidget = QTableWidgetItem("Cycle_{}".format(cycle))
            self.structureTable.setHorizontalHeaderItem(col, nameWidget)
            
        # 寻找condition所在行：
        Items = self.structureTable.findItems(condition, Qt.MatchExactly)
        if Items == []:
            return
        row = Items[0].row()
        col = cycle + 1
        # from PyQt5.QtWidgets import QTableWidget
        # self.structureTable : QTableWidget
        tableItem = self.structureTable.item(row, col)
        if tableItem is None:
            tableItem = CTableWidgetItem(state)
            self.structureTable.setItem(row, col, tableItem)
        else:
            tableItem.setText(state)
        # inpFile:
        inpFile = self.config['workPath'] + '/{}_{}.inp'.format(condition, cycle)
        tableItem.setInpFile(inpFile)

    def beamTableUpdate(self, cycle:int, condition:str, state:str):
        # 添加Cycle列
        if cycle == self.beamTable.columnCount() - 2:
            self.beamTable.insertColumn(self.beamTable.columnCount())
            nameWidget = QTableWidgetItem("Cycle_{}".format(cycle))
            col = cycle + 2
            self.beamTable.setHorizontalHeaderItem(col, nameWidget)
        
        # 寻找condition所在行：
        Items = self.beamTable.findItems(condition, Qt.MatchExactly)
        if Items == []:
            return
        row = Items[0].row()
        col = cycle + 2
        tableItem = self.beamTable.item(row, col)
        if tableItem is None:
            tableItem = CTableWidgetItem(state)
            self.beamTable.setItem(row, col, tableItem)
        else:
            tableItem.setText(state)
        # inpFile:
        inpFile = self.config['workPath'] + '/{}_Mat_{}.inp'.format(condition, cycle)
        tableItem.setInpFile(inpFile)
        
    def structureOptiCompleted(self, state:bool):
        print('结构优化：完成！')
        if state:
            self.setRunBeamButtonState(state)
            if self.config["autoSubmit"]:
                # 自动提交梁径优化
                self.runBeamButton_clicked()
        
    def setRunBeamButtonState(self, state:bool):
        self.runStructureButton.setEnabled(True)
        self.runStructureButton.setChecked(False)
        self.runBeamButton.setEnabled(state)

    def structureMonitorButton_clicked(self):
        # 打开结构优化监控器
        self.showMonitor('structure')

    def beamMonitorButton_clicked(self):
        # 打开梁径优化监控器
        self.showMonitor('beam')

    def showMonitor(self, process:str):
        from GUI.cMonitor import CMonitor
        optiData = getattr(self, '{}OptiData'.format(process))
        if self.monitor is None:
            self.monitor = CMonitor(process)
            self.monitor.show()
            self.monitor.updateData(process, optiData)
        else:
            currentProcess = self.monitor.process
            if not currentProcess == process:
                self.monitor.close()
                self.monitor = CMonitor(process)
                self.monitor.show()
                self.monitor.updateData(process, optiData)
            else:
                self.monitor.show()
                self.monitor.updateData(currentProcess, optiData)

    def structureOptiDataUpdate(self, cycle:int, data:dict):
        # 更新优化数据
        self.structureOptiData[str(cycle)] = data
        self.monitorDataUpdate(process='structure', optiData=self.structureOptiData)

    def beamOptiDataUpdate(self, cycle:int, data:dict):
        # 更新优化数据
        self.beamOptiData[str(cycle)] = data
        self.monitorDataUpdate(process='beam', optiData=self.beamOptiData)

    def monitorDataUpdate(self, process:str, optiData:dict):
        if self.monitor is None:
            from GUI.cMonitor import CMonitor
            self.monitor = CMonitor(process)
        self.monitor.updateData(process, optiData)
