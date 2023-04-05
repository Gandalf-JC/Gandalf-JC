# -*- coding:UTF-8 -*-

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
# AggRatio=0.15                            # 骨料体积比
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

# generate 椭圆球
EllipseNum=1000         # 椭圆球骨料个数  
EllipseDatas=[]        # 椭圆球骨料的数据
points=[]             # 累计生成椭圆球骨料的数据
MaxLongaxis=15        # 椭圆球骨料最大长半轴
minLongaxis=7        # 椭圆球骨料最小长半轴
MaxShortaxis=7        # 椭圆球骨料最大短半轴
minShortaxis=2        # 椭圆球骨料最小短半轴

# Generate 椭圆球 randomly
for k in range(EllipseNum):
    Longaxis=np.random.uniform(minLongaxis,MaxLongaxis)   # 椭圆球骨料的长半轴,mm;  2<Longaxis/Shortaxis<6
    Shortaxis=np.random.uniform(minShortaxis,MaxShortaxis)   # 椭圆球骨料的短半轴,mm    
    x1=np.random.uniform(0,ConcLength)     # 椭圆球的x坐标,mm   
    y1=np.random.uniform(0,ConcWidth)      # 椭圆球的y坐标,mm  
    z1=np.random.uniform(0,ConcHeight)     # 椭圆球的z坐标 ,mm
    AngleXaxi=np.random.uniform(0,360)     # 椭圆球取向，与x的夹角
    AngleZaxi=np.random.uniform(0,360)     # 椭圆球取向，与z的夹角
    point = (x1,y1,z1,Longaxis,Shortaxis)
    if len(points) == 0:
        points.append(point)
        EllipseDatas.append([k+1,x1,y1,z1,Longaxis,Shortaxis,AngleXaxi,AngleZaxi])  # 椭圆球骨料的数据 
    elif interact_judgement(points, point):
        points.append(point)
        EllipseDatas.append([k+1,x1,y1,z1,Longaxis,Shortaxis,AngleXaxi,AngleZaxi])  # 椭圆球骨料的数据 
    else:
        pass


myModel=mdb.Model(name='Ellipse')
b=EllipseDatas
for i in range(len(EllipseDatas)):
    mySketch=myModel.ConstrainedSketch(name='EllipseSketch',sheetSize=500)
    mySketch.ConstructionLine(point1=(b[i][1], 
        b[i][2]-b[i][4]), point2=(b[i][1], b[i][2]+b[i][4]))
    mySketch.EllipseByCenterPerimeter(axisPoint1=(b[i][1]+b[i][5],
        b[i][2]), axisPoint2=(b[i][1],b[i][2]+b[i][4]), center=(b[i][1], b[i][2]))
    mySketch.Line(point1=(b[i][1], b[i][2]+b[i][4]), point2=(
        b[i][1], b[i][2]-b[i][4]))    
    mySketch.autoTrimCurve(curve1=mySketch.geometry.findAt((b[i][1]-b[i][5], b[i][2])), point1=(b[i][1]-b[i][5], b[i][2])) 
    myEllipse=myModel.Part(dimensionality=THREE_D, name='Ellipse'+str(i), type=DEFORMABLE_BODY) 
    myPart=myEllipse.BaseSolidRevolve(angle=360.0,flipRevolveDirection=OFF,sketch=mySketch)
    myModel.rootAssembly.Instance(dependent=ON, name='Ellipse'+str(i),part=myEllipse)
    myModel.rootAssembly.translate(instanceList=('Ellipse'+str(i),),vector=(0.0, 0.0, b[i][3]))
    myModel.rootAssembly.rotate(angle=b[i][6], axisDirection=(b[i][1]+10, b[i][2], 
        b[i][3]), axisPoint=(b[i][1],  b[i][2], b[i][3]), instanceList=('Ellipse'+str(i), ))  
    myModel.rootAssembly.rotate(angle=b[i][7], axisDirection=(b[i][1], b[i][2], 
        b[i][3]+10), axisPoint=(b[i][1],  b[i][2], b[i][3]), instanceList=('Ellipse'+str(i), )) 
    del myEllipse
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



# create in Abaqus
myAssembly = mdb.models['Model-1'].rootAssembly
for num in range(SphereNum):
    x = SphereDatas[num][0]
    y = SphereDatas[num][1]
    z = SphereDatas[num][2]
    SphereRadius2 = SphereNum[num][3]
    myAssembly.Instance(name='Part-sphere-solid-{}'.format(num), part=myPart3, dependent=ON)
    myAssembly.translate(instanceList=('Part-sphere-solid-{}'.format(num), ), vector=(x, y, z))
    myAssembly.rotate(instanceList=('Part-sphere-solid-{}'.format(num),), axisPoint=(x, y, z), axisDirection=(x, y+1, z),
             angle=angle_y)
    myAssembly.rotate(instanceList=('Part-sphere-solid-{}'.format(num),), axisPoint=(x, y, z), axisDirection=(x, y, z+1),
             angle=angle_z)


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

# 生成椭圆球的命令
Shortaxis=1
Longaxis=10
mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=20.0)
mdb.models['Model-1'].sketches['__profile__'].ConstructionLine(point1=(0, 
    -Longaxis), point2=(0, Longaxis))
mdb.models['Model-1'].sketches['__profile__'].EllipseByCenterPerimeter(
    axisPoint1=(Shortaxis, 0.0), axisPoint2=(0.0,Longaxis), center=(0.0, 0.0))
mdb.models['Model-1'].sketches['__profile__'].Line(point1=(0.0, Longaxis), point2=(
    0.0, -Longaxis))
mdb.models['Model-1'].sketches['__profile__'].autoTrimCurve(curve1=
    mdb.models['Model-1'].sketches['__profile__'].geometry[3], point1=(
    -Shortaxis, 0))     
mdb.models['Model-1'].Part(dimensionality=THREE_D, name='Part-2', type=
    DEFORMABLE_BODY)
mdb.models['Model-1'].parts['Part-2'].BaseSolidRevolve(angle=360.0, 
    flipRevolveDirection=OFF, sketch=
    mdb.models['Model-1'].sketches['__profile__'])
del mdb.models['Model-1'].sketches['__profile__']
















