import os, sys, json
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.uic import loadUi
import pyqtgraph as pg
import numpy as np

PEN_COLOR = ['red', 'blue', 'green', 'black', 'cyan', 'yellow', 'gray', 'magenta', 'lightGray']

class CMonitor(QWidget):
    '''
    优化过程监视器
    '''
    def __init__(self, process:str = None):

        self.path = os.path.dirname(__file__)
        self.parentPath = os.path.dirname(self.path)
        # self.configPath = self.parentPath + '\\preference\\config.json'
        
        # 加载UI
        super(CMonitor, self).__init__()
        self.ui = loadUi(self.path + '\\uis\\monitor.ui', self)
        self.process : str = process
        
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self.widget_1)
        # 平均应力曲线
        self.meanStressWidget = pg.PlotWidget()
        self.meanStressWidget.setBackground('w')
        self.meanStressCurve = pg.PlotCurveItem(pen = 'b', name = '平均应力')
        self.meanStressWidget.addItem(self.meanStressCurve)
        self.meanStressGrid = pg.GridItem()
        self.meanStressWidget.addItem(self.meanStressGrid)
        # 最大应力曲线
        self.maxStressWidget = pg.PlotWidget()
        self.maxStressWidget.setBackground('w')
        self.maxStressCurve = pg.PlotCurveItem(pen = 'r', name = '最大应力')
        self.maxStressWidget.addItem(self.maxStressCurve)
        self.maxStressGrid = pg.GridItem()
        self.maxStressWidget.addItem(self.maxStressGrid)

        if self.process == 'structure':
            self.textItem = "骨填充"
        elif self.process == 'beam':
            self.textItem = "支架"

        self.stressLegendWidget = pg.PlotWidget()
        self.stressLegendWidget.setBackground('w')
        self.stressLegendItem = pg.LegendItem(offset=(70,20))
        self.stressLegendItem.addItem(self.meanStressCurve, name = '{}平均应力'.format(self.textItem))
        self.stressLegendItem.addItem(self.maxStressCurve, name = '{}最大应力'.format(self.textItem))
        self.stressLegendWidget.setCentralItem(self.stressLegendItem)
        layout.addWidget(self.stressLegendWidget, stretch = 2)
        layout.addWidget(self.meanStressWidget, stretch = 7)
        layout.addWidget(self.maxStressWidget, stretch = 7)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        layout = QHBoxLayout(self.widget_2)
        self.elemSetWidget = pg.PlotWidget()
        self.elemSetWidget.setBackground('w')
        self.elemSetLegendItem = pg.LegendItem()
        self.elemSetWidget.addItem(self.elemSetLegendItem)
        self.elemSetGrid = pg.GridItem()
        self.elemSetWidget.addItem(self.elemSetGrid)

        self.elemSetLegendWidget = pg.PlotWidget()
        self.elemSetLegendWidget.setBackground('w')
        self.elemSetLegendItem = pg.LegendItem(offset = (70, 20))
        self.elemSetLegendWidget.setCentralItem(self.elemSetLegendItem)
        layout.addWidget(self.elemSetLegendWidget, stretch = 2)
        layout.addWidget(self.elemSetWidget, stretch = 14)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

    def updateData(self, process, optiData):
        if not process == self.process:
            return
        
        meanValueList = []
        maxValueList = []

        if len(optiData.keys()) == 0:
            return

        for cycle in optiData.keys():
            data = optiData[cycle]
            meanValue : float = data["meanValue"]
            maxValue : float = data["maxValue"]
            elemCounts : dict = data["elemCounts"]
            meanValueList.append(meanValue)
            maxValueList.append(maxValue)

        for elemSetName in elemCounts.keys():
            setattr(self, '{}_valueList'.format(elemSetName), [])

        count = 0
        for cycle in optiData.keys():
            elemCounts : dict = optiData[cycle]["elemCounts"]
            for elemSetName in elemCounts.keys():
                if not hasattr(self, '{}_Curve'.format(elemSetName)):
                    setattr(self, '{}_Curve'.format(elemSetName), pg.PlotCurveItem(pen = PEN_COLOR[count]))
                    curveItem = getattr(self, '{}_Curve'.format(elemSetName))
                    self.elemSetWidget.addItem(curveItem)
                    self.elemSetLegendItem.addItem(curveItem, name = elemSetName)
                elemList : list = getattr(self, '{}_valueList'.format(elemSetName))
                elemList.append(elemCounts[elemSetName])
                count += 1

        x = np.linspace(0, len(meanValueList)-1, len(meanValueList))
        y1 = np.array(meanValueList)
        y2 = np.array(maxValueList)

        self.meanStressCurve.setData(x, y1)
        self.maxStressCurve.setData(x, y2)

        for elemSetName in elemCounts.keys():
            curveItem : pg.PlotCurveItem = getattr(self, '{}_Curve'.format(elemSetName))
            elemList : list = getattr(self, '{}_valueList'.format(elemSetName))
            y = np.array(elemList)
            curveItem.setData(x, y)
