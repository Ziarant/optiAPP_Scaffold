import sys, os
from odbAccess import *
from abaqus import *
from abaqusConstants import *
from jobMessage import *
from caeModules import *

odbPath = sys.argv[8]
nodeSetBaseName = sys.argv[9]

odbName = os.path.basename(odbPath).split('.')[0]
sys.stdout = open('SurfNode.txt'.format(odbName), 'w')

odb = openOdb(odbPath)
nodeSet = odb.rootAssembly.instances.values()[0].nodeSets[nodeSetBaseName]
nodes = nodeSet.nodes

for node in nodes:
    print(node.label)

sys.stdout.close()
odb.close()