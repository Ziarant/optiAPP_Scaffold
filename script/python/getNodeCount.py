import sys, os
from odbAccess import *
from abaqus import *
from abaqusConstants import *
from jobMessage import *

odbPath = sys.argv[8]
nodeSetName = sys.argv[9]

elemCount = 0

odbName = os.path.basename(odbPath).split('.')[0]

odb = openOdb("{}.odb".format(odbName))
odbNodeSetDict = odb.rootAssembly.instances.values()[0].nodeSets
nodes = odbNodeSetDict[nodeSetName].nodes
nodeCount = len(nodes)

dirname = os.path.dirname(odbPath)
nodeCountFile = dirname + '/nodeCount.txt'
sys.stdout = open(nodeCountFile, 'w')
print(nodeCount)