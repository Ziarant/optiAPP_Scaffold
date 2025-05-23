import sys, os
from PyQt5.QtWidgets import QTableWidgetItem, QMenu, QAction
from PyQt5.QtGui import QIcon, QColor
from .INPVisualizer import INPVisualizer

sys.path.append('..')

class CTableWidgetItem(QTableWidgetItem):
    def __init__(self, text:str):
        super().__init__()
        self.setText(text)
        self.inpFile : str = None

    def setText(self, text:str):
        if text == 'Aborted':
            self.setBackground(QColor(255, 86, 86, 100))
        elif text == 'Completed':
            self.setBackground(QColor(86, 255, 86, 100))
        super().setText(text)

    def setInpFile(self, inp:str):
        self.inpFile : str = inp

    def createRightMenu(self, pos):
        menu = QMenu()
        showStructure = QAction(QIcon(u'GUI\icons\SpaceMesh.png'), '显示支架')
        if self.inpFile is None:
            showStructure.setEnabled(False)
        if not os.path.exists(self.inpFile):
            showStructure.setEnabled(False)
        showStructure.triggered.connect(self.showInp)
        menu.addAction(showStructure)
        menu.exec_(pos)
        menu.show()

    def showInp(self):
        # 可视化T3D2单元
        input_file = self.inpFile
        if os.path.exists(input_file):
            visualizer = INPVisualizer()
            visualizer.setInpFile(input_file)
            visualizer.run()
        else:
            print('不存在文件：{}'.format(input_file))