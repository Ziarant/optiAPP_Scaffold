import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QIcon

class FlowEffectButton(QPushButton):
    """带绿色流动特效的按钮类"""
    
    # 按钮状态常量
    NORMAL = 0
    LOADING = 1
    SUCCESS = 2
    ERROR = 3
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        
        # 按钮状态
        self.state = self.NORMAL
        
        # 流动效果相关变量
        self.flow_pos = 0
        self.flow_width = 50
        self.flow_speed = 3
        self.flow_color = QColor(100, 255, 100, 150)
        
        # 进度条相关变量
        self.progress = 0
        self.max_progress = 100
        
        # 定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateFlow)
        
        # 设置字体
        font = QFont()
        font.setFamily("Segoe UI")
        font.setWeight(QFont.Medium)
        font.setPixelSize(14)
        self.setFont(font)
        
        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                transition-duration: 0.4s;
                cursor: pointer;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        # 动画持续时间（毫秒）
        self.animation_duration = 3000
        
    def startFlowEffect(self):
        """开始流动特效"""
        self.state = self.LOADING
        self.flow_pos = -self.flow_width
        self.timer.start(30)  # 每30毫秒更新一次
        self.update()
        
    def stopFlowEffect(self, success=True):
        """停止流动特效"""
        self.timer.stop()
        self.state = self.SUCCESS if success else self.ERROR
        self.update()
        
        # 2秒后恢复正常状态
        QTimer.singleShot(2000, self.resetState)
        
    def resetState(self):
        """恢复按钮到正常状态"""
        self.state = self.NORMAL
        self.update()
        
    def updateFlow(self):
        """更新流动效果位置"""
        self.flow_pos += self.flow_speed
        if self.flow_pos > self.width():
            self.flow_pos = -self.flow_width
        self.update()
        
    def paintEvent(self, event):
        """重写绘制事件"""
        super().paintEvent(event)
        
        if self.state == self.LOADING:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 创建渐变效果
            gradient = QColor(self.flow_color)
            gradient.setAlpha(50)
            
            # 绘制流动效果
            flow_rect = QRect(self.flow_pos, 0, self.flow_width, self.height())
            painter.fillRect(flow_rect, self.flow_color)
            
            # 绘制渐变边缘
            pen = QPen(gradient, 2)
            painter.setPen(pen)
            painter.drawLine(self.flow_pos, 0, self.flow_pos, self.height())
            painter.drawLine(self.flow_pos + self.flow_width, 0, 
                             self.flow_pos + self.flow_width, self.height())
            
            painter.end()
        
        elif self.state == self.SUCCESS:
            # 绘制成功状态
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制绿色背景
            success_color = QColor(76, 175, 80, 200)
            painter.fillRect(self.rect(), success_color)
            
            # 绘制对勾图标
            pen = QPen(Qt.white, 3)
            painter.setPen(pen)
            
            check_width = self.width() // 3
            check_height = self.height() // 3
            check_x = (self.width() - check_width) // 2
            check_y = (self.height() - check_height) // 2
            
            painter.drawLine(check_x, check_y + check_height // 2, 
                             check_x + check_width // 2, check_y + check_height)
            painter.drawLine(check_x + check_width // 2, check_y + check_height, 
                             check_x + check_width, check_y)
            
            painter.end()
        
        elif self.state == self.ERROR:
            # 绘制错误状态
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制红色背景
            error_color = QColor(244, 67, 54, 200)
            painter.fillRect(self.rect(), error_color)
            
            # 绘制叉号图标
            pen = QPen(Qt.white, 3)
            painter.setPen(pen)
            
            cross_size = min(self.width(), self.height()) // 3
            cross_x = (self.width() - cross_size) // 2
            cross_y = (self.height() - cross_size) // 2
            
            painter.drawLine(cross_x, cross_y, cross_x + cross_size, cross_y + cross_size)
            painter.drawLine(cross_x + cross_size, cross_y, cross_x, cross_y + cross_size)
            
            painter.end()

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("美化按钮示例")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # 创建美化按钮
        self.beautiful_button = FlowEffectButton("开始处理")
        self.beautiful_button.setMinimumSize(150, 40)
        self.beautiful_button.clicked.connect(self.onButtonClick)
        
        # 添加按钮到布局
        layout.addWidget(self.beautiful_button, alignment=Qt.AlignCenter)
        
        # 添加状态标签
        self.status_label = QPushButton("等待点击...")
        self.status_label.setMinimumSize(150, 40)
        self.status_label.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                cursor: default;
            }
        """)
        self.status_label.setEnabled(False)
        layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        
    def onButtonClick(self):
        """按钮点击事件处理"""
        self.status_label.setText("处理中...")
        self.beautiful_button.startFlowEffect()
        
        # 模拟耗时操作
        QTimer.singleShot(5000, self.simulateProcessComplete)
        
    def simulateProcessComplete(self):
        """模拟处理完成"""
        # 随机决定成功或失败
        import random
        success = random.choice([True, False])
        
        self.beautiful_button.stopFlowEffect(success)
        self.status_label.setText("处理成功!" if success else "处理失败!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用全局样式
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())    