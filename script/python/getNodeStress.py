import sys, os
from odbAccess import *
from abaqus import *
from abaqusConstants import *
from jobMessage import *
from caeModules import *
import xyPlot

odbPath = sys.argv[8]
nodeSetBaseName = sys.argv[9]
# TEST:
# odbPath = "F:/JawOpti/CAE_TEST2/ICP_0.odb"
odbName = os.path.basename(odbPath).split('.')[0]
sys.stdout = open('{}_F_stress.txt'.format(odbName), 'w')

session.Viewport(name='Viewport: 1', origin=(0.0, 0.0), width=315.376556396484, height=125.800003051758)
session.viewports['Viewport: 1'].partDisplay.geometryOptions.setValues(referenceRepresentation=ON)

odb = session.openOdb(odbPath)
session.viewports['Viewport: 1'].setValues(displayedObject=odb)

instanceName = odb.rootAssembly.instances.keys()[0]
# nodeSetBaseName = 'FILLINGMATERIAL'
nodeSetName = '{}.{}'.format(instanceName, nodeSetBaseName)
xyList = xyPlot.xyDataListFromField(odb=odb, outputPosition=NODAL,
                                    variable=(('S', INTEGRATION_POINT, ((INVARIANT, 'Mises'), )), ),
                                    nodeSets=(nodeSetName, ))
nodeSet = odb.rootAssembly.instances.values()[0].nodeSets[nodeSetBaseName]
nodes = nodeSet.nodes

nodeCount = len(xyList)
for n in range(nodeCount):
    xyValue = xyList[n]
    coords = nodes[n].coordinates
    name = xyValue.name
    nodeLabel = int(name.split(":")[-1])
    stress = xyValue.data[-1][-1]
    print("{:d},\t{:.3f},\t{:.3f},\t{:.3f},\t{:.3f}".format(nodeLabel, coords[0], coords[1], coords[2], stress))

sys.stdout.close()
odb.close()