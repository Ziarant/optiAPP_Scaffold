import sys, os, json, subprocess
sys.path.append("..")

from .generate_condition_script import generate_condition_script

class MainStructureOpti(object):
    # 进行结构优化设计
    def __init__(self, configJson:str):
        '''
        输入:   config.json文件路径
        '''
        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        self.savePath = os.path.dirname(self.parentPath) + '/script/tcl'
        
        self.configJson = configJson
        self.cycleCount:int = 0             # 循环次数计数
        
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
        
    def run(self):
        # Step-1: 生成工况自动化设置脚本 -> .tcl
        tclDict = generate_condition_script(self.hmtemplatefilePath, 
                                            self.hmfilePath, 
                                            self.curvesIDFile, 
                                            self.conditions, 
                                            self.workPath, 
                                            self.savePath,
                                            self.cycleCount)
        self.config["script"]["condition"] = tclDict
        with open(self.configJson, 'w') as f:
            json.dump(self.config, f, indent=4)
        
        # Step-2: 运行工况自动化设置脚本 -> .inp
        for condition in tclDict.keys():
            tclPath = tclDict[condition]
            command = '"{}" -nogui -tcl {}'.format(self.hmbatchPath, tclPath)
            
            # 创建子进程，获取输出结果
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if error:
                print("Error:", error.decode())
                continue

        # Step-3: 运行有限元计算
        # Step-4: 结果输出，提取有限元结果
        # Step-5: 结果判断，进行有限元网格重新划分
        # Step-6: 循环Step2-5，直到达到优化目标
        pass
