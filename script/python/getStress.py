import sys, os
from odbAccess import *
from abaqus import *
from abaqusConstants import *
from jobMessage import *

odbPath = sys.argv[8]
elemSetList = sys.argv[9].split(',')

odbName = os.path.basename(odbPath).split('.')[0]
sys.stdout = open('{}_stress.txt'.format(odbName), 'w')

odb = openOdb("{}.odb".format(odbName))
step1 = odb.steps.values()[-1]
frame = step1.frames[-1]
stressField = frame.fieldOutputs['S']

odbElemSetDict = odb.rootAssembly.instances.values()[0].elementSets
odbElemSetList = odbElemSetDict.keys()

for elemSetName in elemSetList:
    elemSetName = elemSetName.upper()
    if elemSetName in odbElemSetList:
        elemSet = odbElemSetDict[elemSetName]
        for elem in elemSet.elements:
            stressValue = stressField.getSubset(region = elem).values
            # Only one Integration Point
            misesValue = stressValue[0].mises
            elemId = elem.label
            # Need Optimize
            print('{}, {}'.format(elemId, misesValue))

sys.stdout.close()
odb.close()