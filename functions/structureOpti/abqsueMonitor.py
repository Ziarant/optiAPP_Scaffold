import os

class AbaqusMonitor(object):

    def __init__(self, jobName, workPath):
        self.jobName = jobName
        self.staFileName : str = '{}\{}.sta'.format(workPath, jobName)
        self.odbName : str = '{}\{}.odb'.format(workPath, jobName)
        self.state : str = 'Running'
        self.process = None

    def getState(self):
        if os.path.exists(self.staFileName):
            with open(self.staFileName, 'r') as f:
                lastLine : str = f.readlines()[-1]
                if 'NOT BEEN COMPLETED' in lastLine:
                    self.state = 'Aborted'
                elif 'COMPLETED' in lastLine:
                    self.state = 'Completed'
                else:
                    p = lastLine.split(' ')
                    ps = [x for x in p if x != '']
                    process = ps[-3]
                    self.state = 'Running:{:.2f}%'.format(100 * float(process))
        else:
            self.state = 'Submitted'

        return self.state
    
    def getOdbName(self):
        return self.odbName
    
    def setProcess(self, process):
        # 获取输出信息
        self.process = process
    #     self.checkOutput()

    # def checkOutput(self):
    #     while self.process and self.process.poll() is None:
    #         line = self.process.stdout
            # # line = iter(self.process.stdout.readlines(), '')
            # print(line)
            # if line:
            #     print('ABAQUS输出：{}'.format(line))
            # 继续

if __name__ == "__main__":
    workPath = 'F:\JawOpti\CAE_TEST2'
    jobName = 'ICP_7'
    abaqusMonitor = AbaqusMonitor(jobName=jobName, workPath=workPath)
    state = abaqusMonitor.getState()
    print(state)