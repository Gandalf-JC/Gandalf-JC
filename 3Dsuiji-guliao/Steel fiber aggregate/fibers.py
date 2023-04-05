#! /user/bin/python
# -*- coding:UTF-8 -*-
# filename：fibers.py
from abaqus import *
from abaqusConstants import *
from caeModules import *
import os
import numpy as np
import math
import matplotlib.pyplot as plt
import numpy as np
from visualization import *
from odbAccess import *
import xlwt
import math
Mdb()
session.journalOptions.setValues(replayGeometry=INDEX,recoverGeometry=INDEX)
session.journalOptions.setValues(replayGeometry=COORDINATE,recoverGeometry= COORDINATE)

# rectangular region
ConcLength=150  # mm,长方体混凝土长度
ConcWidth=80    # mm,长方体混凝土宽度
ConcHeight=50    # mm,长方体混凝土高度

# fibers information
FiberLength=10.0           # mm,钢纤维的长度
FiberRadius=0.1        # mm,钢纤维的半径
FiberNum=200             # 钢纤维的数量

# modeling
part=mdb.models['Model-1'].Part(name="fibers", dimensionality=THREE_D, type=DEFORMABLE_BODY)
sketch=mdb.models['Model-1'].ConstrainedSketch(name="sketch", sheetSize=200)
sketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(FiberRadius, 0.0))
part.BaseSolidExtrude(sketch=sketch, depth=FiberLength)

# 形参points表示已存在的线段坐标，
# point线段点坐标((cx,cy,cz),(dx,dy,dz))
def interact_judgement(points, point, FiberRadius):
    c = point[0]
    d = point[1]
    num = 50
    sign = True
    for point in points:
        a = point[0]
        b = point[1]
        for i in range(num+1):
            mx = c[0] + (d[0] - c[0]) * (1. / num) *  i  
            my = c[1] + (d[1] - c[1]) * (1. / num) *  i  
            mz = c[2] + (d[2] - c[2]) * (1. / num) *  i  
            for j in range(num+1):
                nx = a[0] + (b[0] - a[0]) * (1. / num) * j 
                ny = a[1] + (b[1] - a[1]) * (1. / num) * j 
                nz = a[2] + (b[2] - a[2]) * (1. / num) * j 
                # distance calculate
                distance = sqrt((mx-nx)**2+(my-ny)**2+(mz-nz)**2)
                if distance < FiberRadius*2:
                    sign = False
                    break
            if not sign:
                break
        if not sign:
            break
    return sign


points=[]
fibers=[]
# Generate fibers randomly
for k in range(FiberNum):
    Angle=np.random.uniform(0,360)  #随机生成一个角度
    x1=np.random.uniform(0,ConcLength)
    y1=np.random.uniform(0,ConcWidth)
    z1=np.random.uniform(0,ConcHeight)#xyz坐标范围限制
    AngleXaxi=np.random.uniform(0,360)
    AngleZaxi=np.random.uniform(0,360)#X轴和Z轴
    x2=x1+FiberLength*np.sin(AngleZaxi*np.pi/180)*np.cos(AngleXaxi*np.pi/180)
    y2=y1+FiberLength*np.sin(AngleZaxi*np.pi/180)*np.sin(AngleXaxi*np.pi/180)
    z2=z1+FiberLength*np.cos(AngleZaxi*np.pi/180)
    point = ((x1,y1,z1), (x2,y2,z2))#确定出两个点的空间坐标
    if len(points) == 0:
        points.append(point)
        fibers.append([x1, y1, z1, AngleXaxi, AngleZaxi])
    elif interact_judgement(points, point, FiberRadius):
        points.append(point)
        fibers.append([x1, y1, z1, AngleXaxi, AngleZaxi])
    else:
        pass


### create fiber wire
#for point in points:
#    part.WirePolyLine(points=(point, ), mergeType=IMPRINT, meshable=ON)

# create in Abaqus
myAssembly = mdb.models['Model-1'].rootAssembly
for num in range(FiberNum):
    x = fibers[num][0]
    y = fibers[num][1]
    z = fibers[num][2]
    angle_y = fibers[num][3]
    angle_z = fibers[num][4]
    myAssembly.Instance(name='Part-fiber-solid-{}'.format(num), part=part, dependent=ON)
    myAssembly.translate(instanceList=('Part-fiber-solid-{}'.format(num), ), vector=(x, y, z))
    myAssembly.rotate(instanceList=('Part-fiber-solid-{}'.format(num),), axisPoint=(x, y, z), axisDirection=(x, y+1, z),
             angle=angle_y)
    myAssembly.rotate(instanceList=('Part-fiber-solid-{}'.format(num),), axisPoint=(x, y, z), axisDirection=(x, y, z+1),
             angle=angle_z)

myModel=mdb.models['Model-1']
# 生成混凝土轮廓的命令
xmin=0
xmax=ConcLength
ymin=0
ymax=ConcWidth
zmin=0
zmax=ConcHeight
zlength=abs(zmax-zmin)

myModel.ConstrainedSketch(name='__profile__',sheetSize=200)
myModel.sketches['__profile__'].rectangle(point1=(xmin, ymin), 
    point2=(xmax, ymax))
PartExCube=myModel.Part(dimensionality=THREE_D, name='CubeProfile', type=
    DEFORMABLE_BODY)
myModel.parts['CubeProfile'].BaseSolidExtrude(depth=zlength, sketch=
    myModel.sketches['__profile__'])
del myModel.sketches['__profile__']
myModel.rootAssembly.Instance(name='CubeProfile', part=PartExCube, dependent=ON)
#mdb.models[myModel].rootAssembly.translate(instanceList=('CubeProfile', ), 
#    vector=(0.0, 0.0, zmin)) 
