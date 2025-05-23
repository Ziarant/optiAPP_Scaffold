import os

def generate_structure_script(templatefile : str, 
                              readfile : str, 
                              savePath : str,
                              elemSetNameList : list,
                              bonefillSetNameList : list,
                              nodeSetName : str,
                              surfNodeSetName : str,
                              anchorSurfNodes : list,
                              anchorNodes : list,
                              surfNodes : list,
                              elemSize : float = 1.5) -> list:
    '''
    输入：
        templatefile, str, 模板文件路径
        readfile, str, 读取文件路径
        elemSetNameList: list, 支架Comps名称
        anchorSurfNodes: list, 表面锚节点
        anchorNodes: list, 所有锚节点
    '''
    filePath = os.path.join(savePath, 'structure.tcl')
    with open(filePath, 'w') as f:
        line0 = '*templatefileset "{}"\n'.format(templatefile)
        line1 = '*readfile "{}"\n'.format(readfile)
        f.write(line0)
        f.write(line1)
        # 新建、编写.tcl文件
        # STEP-1: 删除旧网格节点
        for elemSetName in elemSetNameList:
            line_0 = '*createmark elems 1 by comps name "{}"\n'.format(elemSetName)
            line_1 = 'set elemList [hm_getmark elems 1]\n'
            line_2 = 'if {[llength $elemList] > 0} {\n'
            line_3 = '    *deletemark elements 1\n'
            line_4 = '}\n'
            f.write(line_0)
            f.write(line_1)
            f.write(line_2)
            f.write(line_3)
            f.write(line_4)

        # STEP-2: 骨填充区域表面
        setNames = ''
        for bonefillSetName in bonefillSetNameList:
            setNames += ' "{}"'.format(bonefillSetName)
        line_0 = '*createmark components 1 {}\n'.format(setNames)
        line_1 = '*findfaces components 1\n'
        f.write(line_0)
        f.write(line_1)
        # STEP-3: Detach
        line_0 = '*createmark elements 1 by comps name "^faces"\n'
        line_1 = '*detachelements 1 0\n'
        f.write(line_0)
        f.write(line_1)
        # STEP-4: REMESH SURF
        line_0 = '*createmark elements 1 by comps name "^faces"\n'
        ids_str : str = ' '.join(map(str, anchorSurfNodes))
        line_1 = '*createmark nodes 2 {}\n'.format(ids_str)
        line_2 = '*elementsaddnodesfixed 1 2\n'
        line_a = '*setedgedensitylinkwithaspectratio -1\n'
        # line_3 = '*interactiveremeshelems 1 {} 0 0 1 1 2 30\n'.format(elemSize)
        line_3 = '*defaultremeshelems 1 {} 0 0 1 1 1 1 0 0 0 0 2 30\n'.format(elemSize)
        '''
        *interactiveremeshelems markmask elemSize elemType elemType_2 sizeCtrl skewCtrl breakConnect angle
        '''
        f.write(line_0)
        f.write(line_1)
        f.write(line_2)
        f.write('*featureangleset 30\n*setusefeatures 3\n')
        f.write(line_a)
        f.write(line_3)
        f.write('*setedgedensitylinkwithaspectratio 2.11\n*featureangleset 30\n*setusefeatures 0\n')
        # STEP-5: Remesh Scaffold
        line_0 = '*currentcollector components "Scaffold_06N"\n'
        line_1 = '''*createstringarray 2 "pars: upd_shell fix_comp_bdr tet_clps='0.100000,1.000000,0' max_size='0,0,1.79769e+308'" \
  "tet: 34 1.3 -1 0 0.8 0 0"\n'''
        line_2 = '*createmark components 2 "^faces"\n'
        ids_str : str = ' '.join(map(str, anchorNodes))
        line_3 = '*createmark nodes 2 {}\n'.format(ids_str)
        line_4 = '*tetmesh components 2 1 nodes 2 5 1 2\n'
        f.write(line_0)
        f.write(line_1)
        f.write(line_2)
        f.write(line_3)
        f.write(line_4)
        # STEP-6: Detach -> edges
        line_0 = '*createmark elements 1 by comps name "Scaffold_06N"\n'
        line_1 = '*detachallelements 1 0\n'
        line_2 = '*findedges1 elems 1 0 0 0 30\n'
        line_3 = '*deletemark elements 1\n'
        f.write(line_0)
        f.write(line_1)
        f.write(line_0)
        f.write(line_2)
        f.write(line_0)
        f.write(line_3)
        # STEP-7: 
        line_0 = '*createmark elements 1 by comps name "^edges"\n'
        line_1 = '*configedit 1 "rod"\n'
        compName = elemSetNameList[-1]
        line_2 = '*movemark elements 1 "{}"\n'.format(compName)
        f.write(line_0)
        f.write(line_1)
        f.write(line_0)
        f.write(line_2)
        line_0 = '*deletemark components 1\n'
        line_1 = '*createmark components 1 "^edges"\n'
        line_2 = '*createmark components 1 "^faces"\n'
        f.write(line_1)
        f.write(line_0)
        f.write(line_2)
        f.write(line_0)
        # STEP-RESET NODE
        line_0 = '*setvalue sets name={} ids={{nodes 0}}\n'.format(nodeSetName)
        line_1 = '*createmark nodes 1 "by comps name" {}\n'.format(setNames)
        line_2 = 'set nodeList [hm_getmark nodes 1]\n'
        line_3 = '*setvalue sets name={} ids={{nodes $nodeList}}\n'.format(nodeSetName)
        ids_str = ' '.join(map(str, surfNodes))
        line_4 = '*setvalue sets name={} ids={{nodes 0}}\n'.format(surfNodeSetName)
        line_5 = '*setvalue sets name={} ids={{nodes {}}}\n'.format(surfNodeSetName, ids_str)
        f.write(line_0)
        f.write(line_1)
        f.write(line_2)
        f.write(line_3)
        f.write(line_4)
        f.write(line_5)
        # STEP-equivalence and duplicates
        setNames += ' "Scaffold_06"'
        line = '*createmark elements 1 by comps name {}\n'.format(setNames)
        f.write(line)
        f.write('*equivalence elements 1 0.001 1 0 0\n')
        f.write('*createmark elements 1 by comps name "Scaffold_06"\n')
        f.write('*elementtestduplicates elements 1 2 1\n')
        line_1 = 'set elemList [hm_getmark elems 2]\n'
        line_2 = 'if {[llength $elemList] > 0} {\n'
        line_3 = '    *deletemark elements 2\n'
        line_4 = '}\n'
        f.write(line_1)
        f.write(line_2)
        f.write(line_3)
        f.write(line_4)
        # STEP-END: SAVE
        line_ans = 'hm_answernext yes\n'
        line_save = '*writefile "{}"\n'.format(readfile)
        f.write(line_ans)
        f.write(line_save)

    return filePath