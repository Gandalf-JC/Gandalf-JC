#! /user/bin/python
# - * - coding: UTF-8 - * -

# 文件名: simple_sphere_Example.py

from abaqus import *
from abaqusConstants import *
import numpy as np

# 建立模型
myModel=mdb.Model(name='sphere')
b=np.loadtxt('coordinates.txt',delimiter = ',',dtype=np.float32)
print(b)

for i in range(1):
    mySketch=myModel.ConstrainedSketch(name='sphereProfile',sheetSize=0.2)
    mySketch.ArcByCenterEnds(center=(b[i][1],b[i][2]), direction=CLOCKWISE, point1=(b[i][1],b[i][2]+b[i][4]), point2=(b[i][1],b[i][2]-b[i][4]))
    mySketch.Line(point1=(b[i][1],b[i][2]+b[i][4]), point2=(b[i][1],b[i][2]-b[i][4]))
    myConstructionLine=mySketch.ConstructionLine(point1=(b[i][1],b[i][2]+b[i][4]), point2=(b[i][1],b[i][2]-b[i][4]))    
    myBeam=myModel.Part(name='sphere'+str(i),dimensionality=THREE_D,type=DEFORMABLE_BODY)
    myPart=myBeam.BaseSolidRevolve(angle=360.0,flipRevolveDirection=OFF,sketch=mySketch)
    myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
    myModel.rootAssembly.Instance(dependent=ON, name='sphere'+str(i),part=myBeam)
    myModel.rootAssembly.translate(instanceList=('sphere'+str(i),),vector=(0.0, 0.0, b[i][3]))
    del myBeam
    del myConstructionLine
    del myPart
    del mySketch




# 生成球的第一种命令流
s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=0.2)
s1.ConstructionLine(point1=(0.0, -0.1), point2=(0.0, 0.1))
s1.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.015), point2=(0.0, 
    -0.015), direction=CLOCKWISE)
s1.Line(point1=(0.0, 0.015), point2=(0.0, -0.015))
p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=THREE_D, 
    type=DEFORMABLE_BODY)
p = mdb.models['Model-1'].parts['Part-1']
p.BaseSolidRevolve(sketch=s1, angle=360.0, flipRevolveDirection=OFF)



# 生成球的第二种命令流

s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', 
    sheetSize=200.0)
g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
s1.setPrimaryObject(option=STANDALONE)
s1.ConstructionLine(point1=(0.0, -100.0), point2=(0.0, 100.0))
s1.FixedConstraint(entity=g[2])
s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(15.0, 0.0))
s1.CoincidentConstraint(entity1=v[0], entity2=g[2], addUndoState=False)
s1.autoTrimCurve(curve1=g[3], point1=(-8.18963241577148, 13.578052520752))
s1.Line(point1=(0.0, 15.0), point2=(0.0, -15.0))
s1.VerticalConstraint(entity=g[6], addUndoState=False)
s1.PerpendicularConstraint(entity1=g[4], entity2=g[6], addUndoState=False)
p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=THREE_D, 
    type=DEFORMABLE_BODY)
p = mdb.models['Model-1'].parts['Part-1']
p.BaseSolidRevolve(sketch=s1, angle=360.0, flipRevolveDirection=OFF)

















