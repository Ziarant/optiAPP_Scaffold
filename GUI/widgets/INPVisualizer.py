import os
import numpy as np
import pyvista as pv
from PyQt5.QtCore import QThread

COLOR = ['#0000FF', '#00A9FF', '#00FFFF', '#00FFA9', '#00FF00', '#A9A900', '#FFA900','#FF0000']

class INPVisualizer(QThread):
    """ABAQUS INP文件可视化工具，使用PyVista库"""
    
    def __init__(self):
        # 存储节点和单元数据
        self.nodes = {}      # 节点ID -> [x, y, z]坐标
        self.elements = []   # 每个元素是一个字典，包含id, type, nodes
        self.inpFile = None
        self.mesh : dict = {}

    def setInpFile(self, input_file):
        self.inpFile = input_file
    
    def parse_inp_file(self):
        """解析ABAQUS INP文件"""
        file_path = self.inpFile
        print(f"正在解析文件: {file_path}")
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # 初始化解析状态
        node_section = False
        element_section = False
        current_element_type = None
        current_element_set = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否为新的部分
            if line.startswith('*'):
                # 移除注释
                if ',' in line:
                    line_ = line.split(',')[0]
                # 转换为小写以便比较
                keyword = line[1:].strip().lower()
                if keyword.startswith('node'):
                    node_section = True
                    element_section = False
                elif keyword.startswith('element'):
                    node_section = False
                    element_section = True
                    
                    # 提取单元类型
                    if 'type=' in line.lower():
                        type_str = line.lower().split('type=')[1].split(',')[0].strip()
                        current_element_type = type_str.upper()

                    # 提取单元集合名称
                    if 'elset=' in line.lower():
                        set_str = line.lower().split('elset=')[1].split(',')[0].strip()
                        current_element_set = set_str.upper()

                else:
                    # 其他部分，停止解析节点和单元
                    node_section = False
                    element_section = False
                    current_element_type = None
                    current_element_set = None
                    
                continue
                
            # 解析节点数据
            if node_section:
                parts = line.replace(',', ' ').split()
                if len(parts) >= 4:  # 至少需要节点ID和3个坐标
                    node_id = int(parts[0])
                    coords = [float(p) for p in parts[1:4]]
                    self.nodes[node_id] = coords
                    
            # 解析单元数据
            if element_section and current_element_type == 'T3D2':
                parts = line.replace(',', ' ').split()
                if len(parts) >= 3:  # T3D2需要单元ID和2个节点
                    element_id = int(parts[0])
                    node_ids = [int(p) for p in parts[1:3]]
                    
                    # 检查所有节点是否存在
                    valid = True
                    for nid in node_ids:
                        if nid not in self.nodes:
                            valid = False
                            break
                    
                    if valid:
                        self.elements.append({
                            'id': element_id,
                            'type': 'T3D2',
                            'nodes': node_ids,
                            'eleSet' : current_element_set,
                        })
        
        print(f"解析完成: 共找到 {len(self.nodes)} 个节点 和 {len(self.elements)} 个T3D2单元")
    
    def visualize_t3d2_elements(self, title=None, line_width=None):
        """使用PyVista可视化T3D2单元"""
        if not self.elements:
            print("没有T3D2单元可可视化")
            return
            
        # 准备点数据
        print('# 准备点数据')
        points = []
        # 构建节点ID到索引的映射表
        node_id_to_index = {}
        for i, (node_id, coords) in enumerate(self.nodes.items()):
            points.append(coords)
            node_id_to_index[node_id] = i
        points = np.array(points)
        
        # 准备单元连接数据
        print('# 准备单元连接数据')
        lineDict : dict = {}
        # lines = []
        for elem in self.elements:
            node1_id, node2_id = elem['nodes']
            eleSet = elem['eleSet']
            if eleSet not in lineDict.keys():
                lineDict[eleSet] = []
            
            # 使用映射表直接查找索引，时间复杂度O(1)
            node1_idx = node_id_to_index[node1_id]
            node2_idx = node_id_to_index[node2_id]
            lineDict[eleSet].append([2, node1_idx, node2_idx])  # 每条线由2个点连接而成
        
        # 如果有单元数据，设置到mesh
        for eleSet in lineDict.keys():

            if points.size > 0 and lineDict[eleSet]:
                lines_array = np.array(lineDict[eleSet]).flatten()
                self.mesh[eleSet] = pv.PolyData(var_inp = points,
                                                lines = lines_array)

        # 创建绘图器
        print('# 创建绘图器')
        plotter = pv.Plotter(window_size=[1024, 768])
        for eleSet in self.mesh.keys():
            line_width = int(eleSet[-1])
            color = COLOR[line_width]
            plotter.add_mesh(self.mesh[eleSet], color=color, line_width=line_width, render_lines_as_tubes=True)
        
        # 设置标题
        title = os.path.basename(self.inpFile)
        numElem = len(self.elements)
        plotter.add_title('{}(elemCount:{})'.format(title, numElem), font_size=10)
        
        # 添加坐标轴
        plotter.add_axes()
        
        # 设置背景色
        plotter.set_background('white')
        
        # 自动定位相机
        plotter.camera_position = 'iso'
        
        # 显示结果
        print('# 显示结果')
        plotter.show()

    def run(self):
        self.parse_inp_file()
        self.visualize_t3d2_elements()

def main():
    # 创建可视化器并解析文件
    # app = QApplication([])
    input_file = 'F:\JawOpti\CAE_TEST2\ICP_TEST.inp'
    visualizer = INPVisualizer()
    visualizer.setInpFile(input_file)
    
    # 可视化T3D2单元
    visualizer.run()
    # app.exec_()

if __name__ == "__main__":
    main()    