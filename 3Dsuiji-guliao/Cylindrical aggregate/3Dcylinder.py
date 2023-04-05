#! /user/bin/python
# -*- coding:UTF-8 -*-
# filename：3DSpheres.py
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
session.journalOptions.setValues(replayGeometry=INDEX,recoverGeometry=INDEX)
session.journalOptions.setValues(replayGeometry=COORDINATE,recoverGeometry= COORDINATE)
Mdb()

# rectangular region
ConcLength=150.0  # mm,长方体混凝土长度
ConcWidth=150.0    # mm,长方体混凝土宽度
ConcHeight=150.0    # mm,长方体混凝土高度
# VolumeConc=ConcLength*ConcWidth*ConcHeight                 # 混凝土体积
# AggRatio=0.3                            # 骨料体积比
# AggVolume =VolumeConc*AggRatio;         # 骨料体积
# CumVolume= 0                            # 累计投放骨料体积

def interact_judgement(points, point):
    x1 = point[0]
    y1 = point[1]
    z1 = point[2]
    r11 = point[3]
    r12 = point[4]
    sign = True
    for ii in points:
        x2 = ii[0]
        y2 = ii[1]
        z2 = ii[2]
        r21 = ii[3]
        r22 = ii[4]
        # distance calculate
        distance = sqrt((x1-x2)**2+(y1-y2)**2+(z1-z2)**2)
        if distance < (r11+r21):
            sign = False
            break
    return sign


# generate 圆柱体
CylinNum=1000         # 圆柱体骨料个数  
CylinDatas=[]        # 圆柱体骨料的数据
points=[]             # 累计生成圆柱体骨料的数据
MaxLongaxis=15        # 圆柱体骨料最大长半轴(高度的一半)
minLongaxis=7        # 圆柱体骨料最小长半轴(高度的一半)
MaxShortaxis=7        # 圆柱体骨料最大短半轴(半径)
minShortaxis=2        # 圆柱体骨料最小短半轴(半径)
# Generate 圆柱体 randomly
for k in range(CylinNum):
    Longaxis=np.random.uniform(minLongaxis,MaxLongaxis)   # 圆柱体骨料的长半轴,mm;  2<Longaxis/Shortaxis<6
    Shortaxis=np.random.uniform(minShortaxis,MaxShortaxis)   # 圆柱体骨料的短半轴,mm    
    x1=np.random.uniform(0,ConcLength)     # 圆柱体的x坐标,mm   
    y1=np.random.uniform(0,ConcWidth)      # 圆柱体的y坐标,mm  
    z1=np.random.uniform(0,ConcHeight)     # 圆柱体的z坐标 ,mm
    AngleXaxi=np.random.uniform(0,360)     # 圆柱体取向，与x轴的夹角
    AngleZaxi=np.random.uniform(0,360)     # 圆柱体取向，与z轴的夹角
    point = (x1,y1,z1,Longaxis,Shortaxis)
    if len(points) == 0:
        points.append(point)
        CylinDatas.append([k+1,x1,y1,z1,Longaxis,Shortaxis,AngleXaxi,AngleZaxi])  # 圆柱体骨料的数据 
    elif interact_judgement(points, point):
        points.append(point)
        CylinDatas.append([k+1,x1,y1,z1,Longaxis,Shortaxis,AngleXaxi,AngleZaxi])  # 圆柱体骨料的数据 
    else:
        pass


myModel=mdb.Model(name='Cylin')
b=CylinDatas
for i in range(len(CylinDatas)):
    mySketch=myModel.ConstrainedSketch(name='CylinSketch',sheetSize=500)
    mySketch.CircleByCenterPerimeter(center=(b[i][1], b[i][2]), point1=(b[i][1], b[i][2]+b[i][5]))
    myCylin=myModel.Part(dimensionality=THREE_D, name='Cylin'+str(i), type=
        DEFORMABLE_BODY)
    myPart=myCylin.BaseSolidExtrude(depth=b[i][4]*2, sketch=mySketch)
    myModel.rootAssembly.Instance(dependent=ON, name='Cylin'+str(i),part=myCylin)
    myModel.rootAssembly.translate(instanceList=('Cylin'+str(i), ), 
        vector=(0.0, 0.0, b[i][3]-b[i][4])) 
    myModel.rootAssembly.rotate(angle=b[i][6], axisDirection=(b[i][1]+10, b[i][2], 
        b[i][3]), axisPoint=(b[i][1],  b[i][2], b[i][3]), instanceList=('Cylin'+str(i), ))  
    myModel.rootAssembly.rotate(angle=b[i][7], axisDirection=(b[i][1], b[i][2], 
        b[i][3]+10), axisPoint=(b[i][1],  b[i][2], b[i][3]), instanceList=('Cylin'+str(i), )) 
    del myCylin
    del myPart
    del mySketch

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


## 生成圆柱体的命令
#CylinRadius=10    # 圆柱体的半径
#Cylindepth=20     # 圆柱体的高度
#mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=100.0)
#mdb.models['Model-1'].sketches['__profile__'].CircleByCenterPerimeter(center=(
#    0.0, 0.0), point1=(0.0, CylinRadius))
#mdb.models['Model-1'].Part(dimensionality=THREE_D, name='Part-2', type=
#    DEFORMABLE_BODY)
#mdb.models['Model-1'].parts['Part-2'].BaseSolidExtrude(depth=Cylindepth, sketch=
#    mdb.models['Model-1'].sketches['__profile__'])
#del mdb.models['Model-1'].sketches['__profile__']
#mdb.models['Model-1'].rootAssembly.Instance(dependent=OFF, name='Part-2-1', 
#    part=mdb.models['Model-1'].parts['Part-2'])
#mdb.models['Model-1'].rootAssembly.translate(instanceList=('Part-2-1', ), 
#    vector=(0.0, 0.0, -Longaxis)) 


# 生成圆柱体的命令
# s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', 
#     sheetSize=200.0)
# g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
# s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(100.0, 0.0))
# p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=THREE_D, 
#     type=DEFORMABLE_BODY)
# p = mdb.models['Model-1'].parts['Part-1']
# p.BaseSolidExtrude(sketch=s1, depth=1000.0)
# p = mdb.models['Model-1'].parts['Part-1']
# del mdb.models['Model-1'].sketches['__profile__']






