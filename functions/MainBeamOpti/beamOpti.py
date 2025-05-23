import sys, os, json, subprocess, time
from PyQt5.QtCore import pyqtSignal, QThread
import numpy as np
sys.path.append("..")

# 常量：python脚本
PYTHON_GETELEMCOUNT = 'getElemCount.py'
PYTHON_GETSTRESS = 'getStress.py'

class BeamOpti(QThread):
    
    # 信号传递:循环次数，工况，状态
    monitorStateSignal = pyqtSignal(int, str, str)
    # 信号传递:循环次数，数据字典
    monitorDataSignal = pyqtSignal(int, dict)
    # 信号传递:循环次数，数据字典
    completeSignal = pyqtSignal(bool)
    
    # 进行梁径优化设计
    def __init__(self, configJson:str):
        '''
        输入:   config.json文件路径
        '''
        super(BeamOpti, self).__init__()

        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.pythonPath = os.path.dirname(self.parentPath) + '/script/python'    # .py文件目录
        
        self.configJson = configJson
        self.cycleCount:int = 0             # 循环次数计数
        self.subprocessResult = {}          # 进程池

        self.allData = None                 # 单元数据：[Id, value1, ……, valueN, maxValue, matCode]
        
        # 解析config.json文件
        # 对于生成的索引结果，需要重新写入config.json文件
        with open(self.configJson, 'r') as f:
            self.config = json.load(f)
        
        # 获取初始odb文件列表 -> 更新beam优化 Odb
        self.config['odbFile']['beamOpti'] = self.config['odbFile']['structureOpti']
        with open(self.configJson, 'w') as f:
            json.dump(self.config, f, indent=4)
        with open(self.configJson, 'r') as f:
            self.config = json.load(f)
        self.odbDict : dict = self.config['odbFile']['beamOpti']

        # 单元集合列表
        self.elemSetList : list = self.config["elemSet"].keys()

    def countOdbElem(self) -> int:
        for condition in self.odbDict.keys():
            pass
        odbPath = self.odbDict[condition]
        pythonFile_getElemCount = self.pythonPath + '/' + PYTHON_GETELEMCOUNT
        pythonFile_getElemCount = pythonFile_getElemCount.replace('\\', '/')
        elemSetListStr = ','.join(str(elemSet) for elemSet in self.elemSetList)
        workPath = self.config["workPath"]
        command_cd = 'cd /d "{}"'.format(workPath)
        command_py =  'abaqus cae noGUI={} -- {} {}'.format(pythonFile_getElemCount, odbPath, elemSetListStr)
        command = '{} && {}'.format(command_cd, command_py)
        stdoutFile = workPath + '\elemCount.txt'
        result = subprocess.Popen(command, shell = True, stdout = open(stdoutFile, 'w'))
        result.communicate()
    
        with open(stdoutFile, 'r') as f:
            elemCount = f.readline().split('\n')[0]
            return int(elemCount)
        
    def getFlags_getStressValue(self) -> dict:
        '''
            判断读取应力是否已经执行完成，返回flags；
            降减少重复执行，提高测试速率；
        '''
        flags = {}
        for condition in self.odbDict.keys():
            flags[condition] = False
            odbPath = self.odbDict[condition]
            stressFile = odbPath[:-4] + '_stress.txt'
            if not os.path.exists(stressFile):
                continue
            with open(stressFile, 'r') as f:
                lines = f.readlines()
                elemCount0 = len(lines)
                rate = elemCount0 / self.config["elemCount"] * 100.0
                if rate >= 1.0:
                    flags[condition] = True
                    state = '提取完成'
                    self.monitorStateSignal.emit(self.cycleCount, condition, state)
        return flags

        
    def getStressFile(self):
        # Step-1: 读取odb文件列表，计算单元平均应力

        workPath = self.config["workPath"]
        command_cd = 'cd /d "{}"'.format(workPath)
        
        pythonFile_getStress = self.pythonPath + '/' + PYTHON_GETSTRESS
        pythonFile_getStress = pythonFile_getStress.replace('\\', '/')
        elemSetListStr = ','.join(str(elemSet) for elemSet in self.elemSetList)

        # 判断是否已经处理完成
        flags : dict = self.getFlags_getStressValue()

        for condition in self.odbDict.keys():
            if not flags[condition]:
                odbPath = self.odbDict[condition]
                # 调用.py获取特点单元集合的单元应力
                command_py =  'abaqus cae noGUI={} -- {} {}'.format(pythonFile_getStress, odbPath, elemSetListStr)
                command = '{} && {}'.format(command_cd, command_py)
                state = '提取结果中'
                self.monitorStateSignal.emit(self.cycleCount, condition, state)
                self.subprocessResult[odbPath] = subprocess.Popen(command, shell = True) 
                
        # 监控进程是否运行完成
        self.monitorProcess(flags)
        
    def monitorProcess(self, flags:dict):
        # 监控进程
        while not all(flags.values()):
            for condition in self.odbDict.keys():
                odbPath = self.odbDict[condition]
                # 使用poll()方法检查进程是否结束：运行->None,结束->返回码
                if odbPath not in self.subprocessResult.keys():
                    # 若无此进程，略过
                    continue
                returnCode = self.subprocessResult[odbPath].poll()
                if returnCode is not None:
                    state = '提取完成'
                    self.monitorStateSignal.emit(self.cycleCount, condition, state)
                    flags[condition] = True
                else:
                    time.sleep(4)
                    # 每4s进度可视化
                    stressFile = odbPath[:-4] + '_stress.txt'
                    # 异常处理：不存在应力结果文件，则继续
                    if not os.path.exists(stressFile):
                        continue
                    with open(stressFile, 'r') as f:
                        lines = f.readlines()
                        elemCount0 = len(lines)
                        rate = elemCount0 / self.config["elemCount"] * 100.0
                        state = '提取结果:{:.2f}%'.format(rate)
                        self.monitorStateSignal.emit(self.cycleCount, condition, state)

    def distributeSection(self) -> list:
        '''
            根据各工况的最差情况(最大值)分配材料属性

            ---

            输出：
                List[单元平均应力, 单元最大应力]
        '''
        lines = {}
        count = 1
        for condition in self.odbDict.keys():
            count += 1
            odbPath = self.odbDict[condition]
            stressFile = odbPath[:-4] + '_stress.txt'
            lines[condition] = np.loadtxt(stressFile, delimiter=',')
        if self.allData is None:
            # 无输入，则默认全部为3
            self.allData = np.zeros(shape = (self.config["elemCount"], count + 2))
            self.allData[:, -1] = 3 * np.ones(self.config["elemCount"])
        # allData : [Id, value1, ……, valueN, maxValue, matCode]
        self.allData[:, 0] = lines[condition][:, 0]
        count = 1
        for condition in self.odbDict.keys():
            self.allData[:, count] = lines[condition][:, 1]
            count += 1
        self.allData[:, -2] = np.max(self.allData[:, 1:count], axis = 1)
        meanValue, maxValue = np.mean(self.allData[:, -2]), np.max(self.allData[:, -2])
        # 根据最大应力值进行调整：
        # C1:   若应力值小于0.8,则填充材料应力更小，需要减少梁径，设置matCode = -1
        # C2:   若应力值小于平均值，需要尝试减少梁径以增大应力，设置matCode = -1
        # C3:   若应力值大于1.2倍平均值，需要尝试增加梁径以减少应力，设置matCode = 1
        # C1 & C2 同时满足，则梁径下调两个档位
        C1, C2, C3 = self.allData[:, -2] < 0.8, self.allData[:, -2] < meanValue, self.allData[:, -2] > 1.2*meanValue
        self.allData[C1, -1] -= 1
        self.allData[C2, -1] -= 1
        self.allData[C3, -1] += 1
        # 限制matCode:0-3
        C4, C5 = self.allData[:, -2] < 0, self.allData[:, -2] > 3
        self.allData[C4, -1] = 0
        self.allData[C5, -1] = 3
        return [meanValue, maxValue]
    
    def generateTclScript(self) -> dict:
        '''
        Step-3:生成elemSet对应elemIds,创建tcl脚本;

        输出：统计各单元集合内的单元数目
        {elemSetName : elemCount}
        '''
    
        from functions.MainBeamOpti.generate_distElems_script import generate_distElems_script
        moveElems = {}
        for elemSetName in self.config["elemSet"].keys():
            matCode : int = self.config["elemSet"][elemSetName]['matCode']
            findC = self.allData[:, -1] == matCode
            moveElems[elemSetName] = self.allData[findC, 0].astype(int)
        tclDict, inpDict = generate_distElems_script(templatefile = self.config['hmtemplatefilePath'],
                                                     readfile = self.config['hmfilePath'],
                                                     curvesIDFile = self.config['curvesIDFile'], 
                                                     conditions = self.config['conditions'],
                                                     moveElems = moveElems,
                                                     workPath = self.config['workPath'],
                                                     savePath = os.path.dirname(self.parentPath) + '/script/tcl',
                                                     cycleCount = self.cycleCount
        )
        self.config["script"]["distElems"] = tclDict
        self.config["inpFile"]["matOpti"] = inpDict
        with open(self.configJson, 'w') as f:
            json.dump(self.config, f, indent=4)
        # 统计各单元集合内的单元数目：
        elemCounts = {}
        for elemSetName in self.config["elemSet"].keys():
            elemCount = len(moveElems[elemSetName])
            elemCounts[elemSetName] = elemCount
        return elemCounts
    
    def generateInp(self):
        # 运行tcl文件，生成inp文件
        print('*********Beam_Cycle:[{}]*********'.format(self.cycleCount))
        tclDict = self.config["script"]["distElems"]
        for condition in tclDict.keys():
            tclPath : str = tclDict[condition]
            command = '"{}"  -nogui -tcl {}'.format(self.config['hmbatchPath'], tclPath)
            # 创建子进程,获取输出结果
            process= subprocess.Popen(command, stdout=subprocess.PIPE)
            output, error = process.communicate()
            print('\tCondition:{}\t, Completed'.format(condition))
            state = '创建.inp文件'
            self.monitorStateSignal.emit(self.cycleCount, condition, state)
            # TODO:存在无法创建.inp的情况
    
    def runAbaqus(self):
        # 运行ABAQUS
        from functions.structureOpti.abqsueMonitor import AbaqusMonitor
        print('Run Abaqus:')
        cpuCount : int  = self.config["cpu"]        # CPU数目
        workPath : str  = self.config["workPath"]   # 工作路径
        parallel : bool = self.config["parallel"]   # 是否并行计算
        self.monitorDict : dict = {}                # Job监视器
        inpDict = self.config["inpFile"]["matOpti"]
        for condition in inpDict.keys():
            inpPath : str = inpDict[condition]
            jobName = os.path.basename(inpPath).split('.')[0]
            command_1 = 'cd /d "{}"'.format(workPath)
            command_2 = 'call abaqus job={} cpu={} &'.format(jobName, cpuCount)
            command = '{} && {}'.format(command_1, command_2)
            self.monitorDict[condition] = {
                                        "monitor" : AbaqusMonitor(jobName = jobName, workPath = workPath),
                                        "state" : "Submit"
            }
            result = subprocess.run(command,shell = True)           # 运行Abaqus，提交计算

        # 通过解析.sta文件，监控Abaqus计算进程：
        # 直到所有.inp文件计算完成
        while not self.isAllStateEnd():
            time.sleep(5)

    def isAllStateEnd(self) -> bool:
        # 检查Monitors是否全部为Completed或Aborted状态
        # 输出结果
        result =  True
        for condition in self.monitorDict.keys():
            state = self.monitorDict[condition]["monitor"].getState()
            self.monitorDict[condition]["state"] = state
            # 发送信号：print('{} : {}'.format(condition, state))
            self.monitorStateSignal.emit(self.cycleCount, condition, state)
            if state == 'Submitted':
                result = False
            if 'Running' in state:
                result = False
            if state in ['Completed', 'Aborted']:
                odbName : str = self.monitorDict[condition]["monitor"].getOdbName()
                odbName = odbName.replace('\\', '/')
                self.config['odbFile']["beamOpti"][condition] = odbName
                with open(self.configJson, 'w') as f:
                    json.dump(self.config, f, indent=4)
        return result

        
    def run(self):
        # Step-0: 读取其中一个odb文件，统计单元数目：
        self.config["elemCount"] = self.countOdbElem()

        # 循环开始：
        maxIter = self.config["maxIter"]["beamOpti"]
        while self.cycleCount <= maxIter:
            # Step-1: 读取odb文件列表，计算单元平均应力
            self.getStressFile()
            
            # Step-2: 分析单元应力结果，分配材料属性
            meanValue, maxValue = self.distributeSection()

            # Step-3: 生成自动化单元分配设置脚本 -> .tcl
            elemCounts : dict = self.generateTclScript()

            dataDict = {"meanValue" : meanValue,
                        "maxValue" : maxValue,
                        "elemCounts" : elemCounts}
            # 传递信号
            self.monitorDataSignal.emit(self.cycleCount, dataDict)

            # Step-4: 运行化单元分配设置脚本 -> .inp
            self.generateInp()

            # Step-5: 运行有限元计算
            self.runAbaqus()
            self.cycleCount += 1

        # Step-6: 检查是否达到终止条件
        # Step-7: 循环Step1-6，直到达到优化目标
        
        self.completeSignal.emit(True)
