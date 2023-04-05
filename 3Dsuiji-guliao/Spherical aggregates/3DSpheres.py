# -*- coding:UTF-8 -*-
# filename：3DSpheres.py
from abaqus import *
from abaqusConstants import *
from caeModules import *
import os
import numpy as np
import math
import matplotlib.pyplot as plt
from visualization import *
from odbAccess import *
import xlwt
import math

session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
Mdb()

# rectangular region
ConcLength = 150.0  # mm,长方体混凝土长度
ConcWidth = 150.0  # mm,长方体混凝土宽度
ConcHeight = 150.0  # mm,长方体混凝土高度

VolumeConc = ConcLength * ConcWidth * ConcHeight  # 混凝土体积
AggRatio = 0.3  # 骨料体积比
AggVolume = VolumeConc * AggRatio  # 骨料体积
CumVolume = 0  # 累计投放骨料体积


def interact_judgement(points, point):
    x1 = point[0]
    y1 = point[1]
    z1 = point[2]
    r1 = point[3]
    sign = True
    for ii in points:
        x2 = ii[0]
        y2 = ii[1]
        z2 = ii[2]
        r2 = ii[3]
        # distance calculate
        distance = sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)
        if distance < (r1 + r2):
            sign = False
            break
    return sign


# generate spheres
SphereNum = 1000  # 球形骨料个数
points = []  # 累计生成球形骨料的数据
SphereDatas = []  # 球形骨料的数据
# Generate spheres randomly
for k in range(SphereNum):
    SphereRadius = np.random.uniform(5, 30)  # 球形骨料的半径,mm
    x1 = np.random.uniform(0, ConcLength)  # 球心的x坐标,mm
    y1 = np.random.uniform(0, ConcWidth)  # 球心的y坐标,mm
    z1 = np.random.uniform(0, ConcHeight)  # 球心的z坐标 ,mm
    point = (x1, y1, z1, SphereRadius)
    if len(points) == 0:
        points.append(point)
        SphereDatas.append([k + 1, x1, y1, z1, SphereRadius])  # 球形骨料的数据
    elif interact_judgement(points, point):
        points.append(point)
        SphereDatas.append([k + 1, x1, y1, z1, SphereRadius])  # 球形骨料的数据
    else:
        pass

# create in Abaqus
myModel = mdb.Model(name='sphere')
b = SphereDatas
for i in range(len(SphereDatas)):
    mySketch = myModel.ConstrainedSketch(name='sphereProfile', sheetSize=0.2)
    mySketch.ArcByCenterEnds(center=(b[i][1], b[i][2]), direction=CLOCKWISE, point1=(b[i][1], b[i][2] + b[i][4]),
                             point2=(b[i][1], b[i][2] - b[i][4]))
    mySketch.Line(point1=(b[i][1], b[i][2] + b[i][4]), point2=(b[i][1], b[i][2] - b[i][4]))
    myConstructionLine = mySketch.ConstructionLine(point1=(b[i][1], b[i][2] + b[i][4]),
                                                   point2=(b[i][1], b[i][2] - b[i][4]))
    mysphere = myModel.Part(name='sphere' + str(i), dimensionality=THREE_D, type=DEFORMABLE_BODY)
    myPart = mysphere.BaseSolidRevolve(angle=360.0, flipRevolveDirection=OFF, sketch=mySketch)
    myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
    myModel.rootAssembly.Instance(dependent=ON, name='sphere' + str(i), part=mysphere)
    myModel.rootAssembly.translate(instanceList=('sphere' + str(i),), vector=(0.0, 0.0, b[i][3]))
    del mysphere
    del myConstructionLine
    del myPart
    del mySketch

# 生成混凝土轮廓的命令
xmin = 0
xmax = ConcLength
ymin = 0
ymax = ConcWidth
zmin = 0
zmax = ConcHeight
zlength = abs(zmax - zmin)

myModel.ConstrainedSketch(name='__profile__', sheetSize=200)
myModel.sketches['__profile__'].rectangle(point1=(xmin, ymin),
                                          point2=(xmax, ymax))
PartExCube = myModel.Part(dimensionality=THREE_D, name='CubeProfile', type=DEFORMABLE_BODY)
myModel.parts['CubeProfile'].BaseSolidExtrude(depth=zlength, sketch=myModel.sketches['__profile__'])
del myModel.sketches['__profile__']
myModel.rootAssembly.Instance(name='CubeProfile', part=PartExCube, dependent=ON)
# mdb.models[myModel].rootAssembly.translate(instanceList=('CubeProfile', ),
#    vector=(0.0, 0.0, zmin)) 


# create in Abaqus
myAssembly = mdb.models['Model-1'].rootAssembly
for num in range(SphereNum):
    x = SphereDatas[num][0]
    y = SphereDatas[num][1]
    z = SphereDatas[num][2]
    SphereRadius2 = SphereNum[num][3]
    myAssembly.Instance(name='Part-sphere-solid-{}'.format(num), part=myPart3, dependent=ON)
    myAssembly.translate(instanceList=('Part-sphere-solid-{}'.format(num),), vector=(x, y, z))
    myAssembly.rotate(instanceList=('Part-sphere-solid-{}'.format(num),), axisPoint=(x, y, z),
                      axisDirection=(x, y + 1, z),
                      angle=angle_y)
    myAssembly.rotate(instanceList=('Part-sphere-solid-{}'.format(num),), axisPoint=(x, y, z),
                      axisDirection=(x, y, z + 1),
                      angle=angle_z)

# 建立模型
myModel = mdb.Model(name='sphere')
b = np.loadtxt('coordinates.txt', delimiter=',', dtype=np.float32)
print(b)

for i in range(1):
    mySketch = myModel.ConstrainedSketch(name='sphereProfile', sheetSize=0.2)
    mySketch.ArcByCenterEnds(center=(b[i][1], b[i][2]), direction=CLOCKWISE, point1=(b[i][1], b[i][2] + b[i][4]),
                             point2=(b[i][1], b[i][2] - b[i][4]))
    mySketch.Line(point1=(b[i][1], b[i][2] + b[i][4]), point2=(b[i][1], b[i][2] - b[i][4]))
    myConstructionLine = mySketch.ConstructionLine(point1=(b[i][1], b[i][2] + b[i][4]),
                                                   point2=(b[i][1], b[i][2] - b[i][4]))
    myBeam = myModel.Part(name='sphere' + str(i), dimensionality=THREE_D, type=DEFORMABLE_BODY)
    myPart = myBeam.BaseSolidRevolve(angle=360.0, flipRevolveDirection=OFF, sketch=mySketch)
    myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
    myModel.rootAssembly.Instance(dependent=ON, name='sphere' + str(i), part=myBeam)
    myModel.rootAssembly.translate(instanceList=('sphere' + str(i),), vector=(0.0, 0.0, b[i][3]))
    del myBeam
    del myConstructionLine
    del myPart
    del mySketch

# 生成球的第一种命令流
s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=0.2)
s1.ConstructionLine(point1=(0.0, -0.1), point2=(0.0, 0.1))
s1.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.015), point2=(0.0, -0.015), direction=CLOCKWISE)
s1.Line(point1=(0.0, 0.015), point2=(0.0, -0.015))
p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=THREE_D, type=DEFORMABLE_BODY)
p.BaseSolidRevolve(sketch=s1, angle=360.0, flipRevolveDirection=OFF)

# 生成球的第二种命令流

s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=200.0)
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
p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=THREE_D, type=DEFORMABLE_BODY)
p.BaseSolidRevolve(sketch=s1, angle=360.0, flipRevolveDirection=OFF)
