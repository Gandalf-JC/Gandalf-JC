# -*- coding: utf-8 -*-

from abaqus import *
from abaqusConstants import *
from caeModules import *
import os
import math
import numpy as np
from numpy import random

Modelname = 'Model-1'
for i in range(len(RamAggDatas)):     #  所有骨料设置为自由网格
    p = mdb.models['Model-1'].parts['Part-' + str(i)]
    c = p.cells
    pickedRegions = c[0:1]
    p.setMeshControls(regions=pickedRegions, elemShape=TET, technique=FREE)
    elemType1 = mesh.ElemType(elemCode=C3D20R)
    elemType2 = mesh.ElemType(elemCode=C3D15)
    elemType3 = mesh.ElemType(elemCode=C3D10)
    p = mdb.models['Model-1'].parts['Part-' + str(i)]
    c = p.cells
    cells = c[0:1]
    pickedRegions =(cells, )
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2,
        elemType3))
    p.seedPart(size=3.0, deviationFactor=0.1, minSizeFactor=0.1)
    p = mdb.models['Model-1'].parts['Part-' + str(i)]
    p.generateMesh()



from abaqus import *
from abaqusConstants import *
from caeModules import *
import os
import math

Modelname = 'psb-80p'   # 'psb-1-lin-' + str(i) + '-' + str(j)
for i in range(1,36):
    for j in range(1,41):
        a = mdb.models['psb-80p'].rootAssembly
        region1 = a.instances['psb-2-lin-' + str(i) + '-' + str(j)].sets['psb']
        region2 = a.instances['lu-1'].sets['aruji']
        mdb.models['psb-80p'].EmbeddedRegion(name='psb-2-lin-' + str(i) + '-' + str(j),
                                             embeddedRegion=region1, hostRegion=region2, weightFactorTolerance=1e-06,
                                             absoluteTolerance=0.0, fractionalTolerance=0.05, toleranceMethod=BOTH)











