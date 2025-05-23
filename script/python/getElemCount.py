import sys, os
from odbAccess import *
from abaqus import *
from abaqusConstants import *
from jobMessage import *

odbPath = sys.argv[8]
elemSetList = sys.argv[9].split(',')

elemCount = 0

odbName = os.path.basename(odbPath).split('.')[0]

odb = openOdb("{}.odb".format(odbName))
odbElemSetDict = odb.rootAssembly.instances.values()[0].elementSets
odbElemSetList = odbElemSetDict.keys()

for elemSetName in elemSetList:
    elemSetName = elemSetName.upper()
    if elemSetName in odbElemSetList:
        elemSet = odbElemSetDict[elemSetName]
        elemCount += len(elemSet.elements)

dirname = os.path.dirname(odbPath)
elemCountFile = dirname + '\elemCount.txt'
sys.stdout = open(elemCountFile, 'w')
print(elemCount)