import os, json

def generate_distElems_script(templatefile : str, 
                              readfile : str,
                              curvesIDFile : str, 
                              conditions : dict,
                              moveElems : dict, 
                              workPath : str, 
                              savePath : str,
                              cycleCount : int = 0):
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
        list[dict], [tcl脚本路径字典, inp文件路径字典]
    """
    tclDict = {}
    inpDict = {}

    # 读取工况序号设置
    with open(curvesIDFile, 'r') as f1:
        curvesID = json.load(f1)

    for condition in conditions:
        # 脚本文件名：moveElems
        filePath = os.path.join(savePath, '{}_moveElems.tcl'.format(condition))
        inpPath = os.path.join(workPath, '{}_Mat_{}.inp'.format(condition, cycleCount))
        inpPath = inpPath.replace('\\', '/')
        # 检查是否存在该文件
        if os.path.exists(filePath):
            os.remove(filePath)
        
        line0 = '*templatefileset "{}"\n'.format(templatefile)
        line1 = '*readfile "{}"\n'.format(readfile)
        # 新建、编写.tcl文件
        conditionJson = conditions[condition]
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
            # 移动单元：
            for elemSetName in moveElems.keys():
                elemIdList : list = moveElems[elemSetName]
                if len(elemIdList) == 0:
                    continue
                ids_str : str = ' '.join(map(str, elemIdList))
                # *createmark elements 1 1-3
                # *movemark elements 1 "Scaffold_03"
                f.write('*createmark elements 1 {}\n'.format(ids_str))
                f.write('*movemark elements 1 "{}"\n'.format(elemSetName))
                f.write('*clearmark elements 1\n')
            # 设置.inp输出脚本
            # 存在文件时预设答案：依然输出，覆盖原文件
            if os.path.exists(inpPath):
                f.write('hm_answernext yes\n')      
            lineStr = '*createstringarray 2 "EXPORTIDS_SKIP" "IDRULES_SKIP"\n'
            lineEnd = '*feoutputwithdata "{}" "{}" 0 0 0 1 2'.format(templatefile, inpPath)
            f.write(lineStr)
            f.write(lineEnd)

        filePath = filePath.replace('\\', '/')
        tclDict[condition] = filePath
        inpDict[condition] = inpPath
                
    return [tclDict, inpDict]