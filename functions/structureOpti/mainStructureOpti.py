import sys, os, json, subprocess, time
from PyQt5.QtCore import pyqtSignal, QThread
import numpy as np
import open3d as o3d
import random

sys.path.append("..")

try:
    from .generate_condition_script import generate_condition_script
    from .generate_structure_script import generate_structure_script
    from .abqsueMonitor import AbaqusMonitor
except:
    pass

# 常量：python脚本
PYTHON_GETSTRESS = 'getNodeStress.py'
PYTHON_GETNODECOUNT = 'getNodeCount.py'
PYTHON_GETSURFNODE= 'getSurfNode.py'

class MainStructureOpti(QThread):

    # 信号传递:循环次数，工况，状态
    monitorStateSignal = pyqtSignal(int, str, str)
    # 信号传递:循环次数，数据字典
    monitorDataSignal = pyqtSignal(int, dict)
    # 信号传递:循环次数，数据字典
    completeSignal = pyqtSignal(bool)

    # 进行结构优化设计
    def __init__(self, configJson:str):
        '''
        输入:   config.json文件路径
        '''
        super(MainStructureOpti, self).__init__()

        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.pythonPath = os.path.dirname(self.parentPath) + '/script/python'
        self.savePath = os.path.dirname(self.parentPath) + '/script/tcl'
        
        self.configJson = configJson
        self.cycleCount:int = 0             # 循环次数计数
        self.getNodeCount : bool = False
        self.getSurfNode : bool =False
        self.subprocessResult : dict = {}

        self.allData : np.ndarray = None 
        
        # 解析config.json文件
        # 对于生成的索引结果，需要重新写入config.json文件
        with open(self.configJson, 'r') as f:
            self.config = json.load(f)
        
        self.hmtemplatefilePath = self.config['hmtemplatefilePath']
        self.hmbatchPath = self.config['hmbatchPath']
        self.hmfilePath = self.config['hmfilePath']
        self.curvesIDFile = self.config['curvesIDFile']
        self.workPath = self.config['workPath']
        self.conditions = self.config['conditions']

        self.odbDict : dict = self.config['odbFile']['structureOpti']

    def generateTcl(self):
        tclDict, inpDict = generate_condition_script(self.hmtemplatefilePath, 
                                                    self.hmfilePath, 
                                                    self.curvesIDFile, 
                                                    self.conditions, 
                                                    self.workPath, 
                                                    self.savePath,
                                                    self.cycleCount)
        self.config["script"]["condition"] = tclDict
        self.config["inpFile"]["condition"] = inpDict
        with open(self.configJson, 'w') as f:
            json.dump(self.config, f, indent=4)

    def generateInp(self):
        print('*********Structure_Cycle:[{}]*********'.format(self.cycleCount))
        print('Create Inp File:')
        with open(self.configJson, 'r') as f:
            self.config = json.load(f)

        tclDict = self.config["script"]["condition"]
        for condition in tclDict.keys():
            tclPath : str = tclDict[condition]
            command = '"{}"  -nogui -tcl {}'.format(self.hmbatchPath, tclPath)
            inpFile = self.config['inpFile']["condition"][condition]
            if not os.path.exists(inpFile):
                # 创建子进程,输出inp文件(若无inp文件)
                process= subprocess.Popen(command, stdout=subprocess.PIPE)
                output, error = process.communicate()
            print('\tCondition:{}\t, Completed'.format(condition))
            state = 'Create'
            self.monitorStateSignal.emit(self.cycleCount, condition, state)

        """
        典型输出结果：
        --------------------------------------------------------------------------------
        Altair HyperMesh v2021.0.0.33
        Copyright (C)1990-2021 - Altair Engineering, Inc.  All Rights Reserved.
        Contains trade secrets of Altair Engineering, Inc.  Copyright notice does not
        imply publication.  Decompilation or disassembly of this software is strictly
        prohibited.
        End of command file - terminating.
        HM exiting with code 1
        --------------------------------------------------------------------------------
        退出代码：
        0 -- 成功执行
        1 -- 一般性错误
        2 -- 脚本语法错误
        ……
        """

    def runAbaqus(self):
        print('Run Abaqus:')
        cpuCount : int  = self.config["cpu"]        # CPU数目
        workPath : str  = self.config["workPath"]   # 工作路径
        parallel : bool = self.config["parallel"]   # 是否并行计算
        self.monitorDict : dict = {}                # Job监视器
        inpDict = self.config["inpFile"]["condition"]
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
            state = self.monitorDict[condition]["monitor"].getState()
            if state in ['Completed', 'Aborted']:
                # 若已完成计算/失败：跳过提交步骤
                continue
            # 运行Abaqus，提交计算;使用Popen创建可交互进程  
            process = subprocess.Popen(command,
                                       shell = True,
                                       stdout = subprocess.PIPE,
                                       stdin = subprocess.PIPE)
            self.monitorDict[condition]["monitor"].setProcess(process)
            # process.stdout.
            
        # 通过解析.sta文件，监控Abaqus计算进程：
        # 直到所有.inp文件计算完成
        while not self.isAllStateEnd():
            time.sleep(5)

    def getStrssFile(self):
        # 获取节点数目(仅第一次需要)
        if not self.getNodeCount:
            self.config["nodeCount"] = self.countOdbNode()
            self.getNodeCount = True

        workPath = self.config["workPath"]
        nodeSetName = self.config["nodeSetName"]
        command_cd = 'cd /d "{}"'.format(workPath)
        
        pythonFile_getStress = self.pythonPath + '/' + PYTHON_GETSTRESS
        pythonFile_getSurfNode = self.pythonPath + '/' + PYTHON_GETSURFNODE
        pythonFile_getStress = pythonFile_getStress.replace('\\', '/')

        # 判断是否已经处理完成
        self.odbDict = self.config['odbFile']['structureOpti']
        flags : dict = self.getFlags_getStressValue()
        self.subprocessResult = {}
        for condition in self.odbDict.keys():
            odbPath = self.odbDict[condition]
            if not flags[condition]:
                # 调用.py获取Node集合的单元应力
                command_py =  'abaqus cae noGUI={} -- {} {}'.format(pythonFile_getStress, odbPath, nodeSetName)
                command = '{} && {}'.format(command_cd, command_py)
                state = '提取结果中'
                self.monitorStateSignal.emit(self.cycleCount, condition, state)
                self.subprocessResult[odbPath] = subprocess.Popen(command, shell = True) 
                
        # 获取表面节点列表(仅第一次需要)
        if not self.getSurfNode:
            surfNodeSetName = self.config["surfNodeSetName"]
            command_py = 'abaqus cae noGUI={} -- {} {}'.format(pythonFile_getSurfNode, odbPath, surfNodeSetName)
            command = '{} && {}'.format(command_cd, command_py)
            result = subprocess.Popen(command, shell = True) 
            self.getSurfNode = True

        # 监控进程是否运行完成:直到完成，返回True
        completed : bool = self.monitorProcess(flags)
        return completed

    def getStressInfo(self) -> list:
        '''
            分析各工况下节点的应力
            ---
            输出：
            List[meanValue, maxValue, nodeCount]
        '''
        lines = {}
        count = 1
        minTargetStress = self.config["minTargetStress"]
        maxTargetStress = self.config["maxTargetStress"]
        # Warning: stressFile not found.
        for condition in self.odbDict.keys():
            count += 1
            odbPath = self.odbDict[condition]
            stressFile = odbPath[:-4] + '_F_stress.txt'
            lines[condition] = np.loadtxt(stressFile, delimiter=',')

        if self.allData is None:
            self.allData = np.zeros(shape = (self.config["nodeCount"], count + 6))
            self.allData[:, 0:3] = lines[condition][:, 0:3]
            self.allData[:, -1] = 1.0 * np.ones(self.config["nodeCount"])
        count = 1
        for condition in self.odbDict.keys():
            # lines[condition]: Id, x, y, z, s1, s2, ……， maxS, weight
            self.allData[:, count+3] = lines[condition][:, 4]
            count += 1
        # 各工况的最大值
        self.allData[:, -2] = np.max(self.allData[:, 4:count+3], axis = 1)
        meanValue, maxValue = np.mean(self.allData[:, -2]), np.max(self.allData[:, -2])
        nodeCount = {}
        C1 = self.allData[:, -2] < minTargetStress
        C2 = self.allData[:, -2] > maxTargetStress
        nodeCount['低于目标区'] = np.sum(C1)
        nodeCount['高于目标区'] = np.sum(C2)
        nodeCount['目标区'] = self.config["nodeCount"] - nodeCount['低于目标区'] - nodeCount['高于目标区']
        # 调整权重：C1降低，C2增加
        self.allData[C1, -1] -= 0.1
        self.allData[C2, -1] += 0.1
        # 限制权重系数范围：0-3
        C4, C5 = self.allData[:, -2] < 0, self.allData[:, -2] > 3
        self.allData[C4, -1] = 0
        self.allData[C5, -1] = 3
        return [meanValue, maxValue, nodeCount]

    def monitorProcess(self, flags:dict) -> bool:
         # 监控进程
        while not all(flags.values()):
            for condition in self.odbDict.keys():
                odbPath = self.odbDict[condition]
                # 使用poll()方法检查进程是否结束：运行->None,结束->返回码
                if odbPath not in self.subprocessResult.keys():
                    continue
                returnCode = self.subprocessResult[odbPath].poll()
                if returnCode is not None:
                    state = '提取完成'
                    self.monitorStateSignal.emit(self.cycleCount, condition, state)
                    flags[condition] = True
                else:
                    time.sleep(4)
                    # 每4s进度可视化
                    stressFile = odbPath[:-4] + '_F_stress.txt'
                    # 异常处理：不存在应力结果文件，则继续
                    if not os.path.exists(stressFile):
                        continue
                    with open(stressFile, 'r') as f:
                        lines = f.readlines()
                        elemCount0 = len(lines)
                        rate = elemCount0 / self.config["nodeCount"] * 100.0
                        state = '提取结果:{:.2f}%'.format(rate)
                        self.monitorStateSignal.emit(self.cycleCount, condition, state)
        return True

    def countOdbNode(self) -> int:
        self.odbDict : dict = self.config['odbFile']['structureOpti']
        for condition in self.odbDict.keys():
            pass
        odbPath = self.odbDict[condition]
        pythonFile_getElemCount = self.pythonPath + '/' + PYTHON_GETNODECOUNT
        pythonFile_getElemCount = pythonFile_getElemCount.replace('\\', '/')
        workPath = self.config["workPath"]
        nodeSetName = self.config["nodeSetName"]
        command_cd = 'cd /d "{}"'.format(workPath)
        command_py =  'abaqus cae noGUI={} -- {} {}'.format(pythonFile_getElemCount, odbPath, nodeSetName)
        command = '{} && {}'.format(command_cd, command_py)
        stdoutFile = workPath + '/nodeCount.txt'

        result = subprocess.Popen(command, shell = True, stdout = open(stdoutFile, 'w'))
        result.communicate()
    
        with open(stdoutFile, 'r') as f:
            nodeCount = f.readline().split('\n')[0]
            return int(nodeCount)

    def getFlags_getStressValue(self) -> dict:
        '''
            判断读取应力是否已经执行完成，返回flags；
            降减少重复执行，提高测试速率；
        '''
        flags = {}
        for condition in self.odbDict.keys():
            flags[condition] = False
            odbPath = self.odbDict[condition]
            stressFile = odbPath[:-4] + '_F_stress.txt'
            if not os.path.exists(stressFile):
                continue
            with open(stressFile, 'r') as f:
                lines = f.readlines()
                nodeCount0 = len(lines)
                rate = nodeCount0 / self.config["nodeCount"] * 100.0
                if rate >= 1.0:
                    flags[condition] = True
                    state = '提取完成'
                    self.monitorStateSignal.emit(self.cycleCount, condition, state)
        return flags
    
    def remesh(self):
        '''
        重新划分网格
        '''
        # STEP-0:检查是否需要跳过该步骤，若存在下一步的所有inp文件，则跳过
        cycle = self.cycleCount + 1
        isExists = []
        for inpFile in self.config['inpFile']["condition"].values():
            suffix = inpFile.split('_')[-1]
            fileName = inpFile.replace(suffix, '{}.inp'.format(cycle))
            isExist = os.path.exists(fileName)
            isExists.append(isExist)
        if np.all(isExists):
            print('\n\tCycle:{}\t,Remesh Completed'.format(self.cycleCount))
            return

        # STEP-1: Remesh所需的锚节点
        anchorNodes, anchorSurfNodes = [],[]                # anchorNode, ID列表
        surfNodeFile = self.workPath + '/SurfNode.txt'
        with open(surfNodeFile, 'r') as f:
            surfNodes = np.loadtxt(f, delimiter=',')
        surfNodes = surfNodes.astype(int)

        if self.allData is None:
            return
        nodesCount = len(self.allData)
        surfNodesCount = len(surfNodes)
        size = self.config['elemSize']

        # 根据权重计算是否作为anchorNode
        anchorNodesData = []
        for node in self.allData:
            x = random.random()
            if x < node[-1] / 3.0:
                anchorNodesData.append(node)

        # anchorNodesData = np.array(anchorNodesData)
        # points = anchorNodesData[:, 1:4]
        # pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
        # min_bound = pcd.get_min_bound() - size * 0.5
        # max_bound = pcd.get_max_bound() + size * 0.5
        # downsampled, ijk, _ = pcd.voxel_down_sample_and_trace(voxel_size = size,
        #                                                       min_bound = min_bound,
        #                                                       max_bound = max_bound)
        # shape = anchorNodesData.shape
        # nodes = anchorNodesData[ijk].reshape(-1, shape[1])
        # for node in nodes:
        for node in anchorNodesData:
            anchorNodes.append(int(node[0]))
            if node[0] in surfNodes:
                anchorSurfNodes.append(int(node[0]))

        # 去重
        anchorNodes = list(set(anchorNodes))
        
        anchorNodesCount = len(anchorNodes)
        anchorSurfNodesCount = len(anchorSurfNodes)
        print('\t锚节点：\n\t表面:{}/{},\t内部:{}/{}'.format(anchorSurfNodesCount, surfNodesCount, anchorNodesCount, nodesCount))

        # STEP-2: 生成.tcl文件
        elemSet : dict = self.config['elemSet']
        elemSetNameList = list(elemSet.keys())
        tclPath = generate_structure_script(self.hmtemplatefilePath, 
                                            self.hmfilePath, 
                                            self.savePath,
                                            elemSetNameList = elemSetNameList,
                                            bonefillSetNameList = self.config["BoneFillRegion"],
                                            nodeSetName = self.config['nodeSetName'],
                                            surfNodeSetName = self.config['surfNodeSetName'],
                                            anchorSurfNodes = anchorSurfNodes,
                                            anchorNodes = anchorNodes,
                                            surfNodes = surfNodes,
                                            elemSize = self.config['elemSize'])
        self.config["script"]["structure"] = tclPath
        with open(self.configJson, 'w') as f:
            json.dump(self.config, f, indent=4)

        # STEP-3：运行.tcl文件，更改HM模型
        command = '"{}"  -nogui -tcl {}'.format(self.hmbatchPath, tclPath)

        # 创建子进程,获取输出结果
        process= subprocess.Popen(command, stdout=subprocess.PIPE)
        output, error = process.communicate()
        print('\n\tCycle:{}\t,Remesh Completed'.format(self.cycleCount))


    def run(self):
        # 循环开始：
        maxIter = self.config["maxIter"]["structureOpti"]
        while self.cycleCount <= maxIter:
            # Step-1: 生成工况自动化设置脚本 -> .tcl
            self.generateTcl()
            
            # Step-2: 运行工况自动化设置脚本 -> .inp
            self.generateInp()
            
            # Step-3: 运行有限元计算
            self.runAbaqus()

            # Step-4: 结果输出，提取有限元结果
            self.getStrssFile()
            meanValue, maxValue, nodeCounts = self.getStressInfo()
            dataDict = {"meanValue" : meanValue,
                        "maxValue" : maxValue,
                        "elemCounts" : nodeCounts}
            # 传递信号
            self.monitorDataSignal.emit(self.cycleCount, dataDict)

            # Step-5: 结果判断，进行有限元网格重新划分
            if self.cycleCount < maxIter:
                self.remesh()

            # Step-6: 循环Step1-5，直到达到优化目标
            self.cycleCount += 1
        
        self.completeSignal.emit(True)

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
                self.config['odbFile']['structureOpti'][condition] = odbName
                with open(self.configJson, 'w') as f:
                    json.dump(self.config, f, indent=4)
        return result
    
if __name__ == "__main__":
    # 测试：
    config = 'F:\optiAPP\preference\config.json'
    app = MainStructureOpti(config)
    app.getStressInfo()
    app.remesh()