import os, json

def generate_condition_script(templatefile : str, 
                              readfile : str, 
                              curvesIDFile : str, 
                              conditions : dict, 
                              workPath : str, 
                              savePath : str,
                              cycleCount : int = 0) -> dict:
    """
    输入：
        templatefile, str, 模板文件路径
        readfile, str, 读取文件路径
        curvesIDFile, str, 工况序号设置
        conditions, dict, 工况字典
        workPath, str, 工作路径
        savePath, str, 保存路径
        cycleCount, int, 循环次数计数
    输出：
        list[str], tcl脚本路径列表
    """
    tclDict = {}
    
    # 读取工况序号设置
    with open(curvesIDFile, 'r') as f1:
        curvesID = json.load(f1)
    
    for condition in conditions:
        filePath = os.path.join(savePath, condition+'.tcl')
        conditionJson = conditions[condition]
        inpPath = os.path.join(workPath, condition+'_{}.inp'.format(cycleCount))
        inpPath = inpPath.replace('\\', '/')
        
        # 检查是否存在该文件
        if os.path.exists(filePath):
            os.remove(filePath)
        
        line0 = '*templatefile "{}"\n'.format(templatefile)
        line1 = '*readfile "{}"\n'.format(readfile)
        # 新建、编写.tcl文件
        with open(conditionJson, 'r') as fc:
            conditionDict = json.load(fc)
        with open(filePath, 'w') as f:
            f.write(line0)
            f.write(line1)
            # 设置工况曲线编辑脚本
            for loadName in curvesID.keys():
                rightID = curvesID[loadName]["right"]
                leftID = curvesID[loadName]["left"]
                rightValue = conditionDict[loadName]["right"]
                leftValue = conditionDict[loadName]["left"]
        
                line_right_1 = '*curvemodifypointcords {} 1 "-y" {}\n'.format(rightID, rightValue)
                line_right_2 = '*curvemodifypointcords {} 2 "-y" {}\n'.format(rightID, rightValue)
                line_left_1 = '*curvemodifypointcords {} 1 "-y" {}\n'.format(leftID, leftValue)
                line_left_2 = '*curvemodifypointcords {} 2 "-y" {}\n'.format(leftID, leftValue)
                f.write(line_right_1)
                f.write(line_right_2)
                f.write(line_left_1)
                f.write(line_left_2)
            # 设置.inp输出脚本
            f.write('hm_answernext yes\n')      # 预设答案：存在文件时依然输出，覆盖原文件
            lineEnd = '*feoutputwithdata "{}" "{}" 0 0 0 1 4'.format(templatefile, inpPath)
            f.write(lineEnd)
            
        filePath = filePath.replace('\\', '/')
        tclDict[condition] = filePath
                
    return tclDict     