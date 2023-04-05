# -*- coding: utf-8 -*-
"""三维随机球型骨料 + ITZ建模-立方体基体-cube basic"""

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


session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
Mdb()

Modelname = 'Model-1'
Partname = 'Part-1'
Instancename = 'Part-1-1'
Jobname = 'sphereModel-1'
os.chdir(r"E:\abaqus-bilibili\1.0 example-cube")        # 设置工作目录

######################### 批量化生成、投放骨料和混凝土外轮廓 #########################
# rectangular region
ConcLength = 150.0                                # 长方体混凝土长度，mm
ConcWidth = 150.0                                 # 长方体混凝土宽度，mm
ConcHeight = 150.0                                # 长方体混凝土高度，mm

VolumeConc = ConcLength * ConcWidth * ConcHeight  # 混凝土体积
AggRatio = 0.3                                    # 骨料体积比
AggVolume = VolumeConc * AggRatio                 # 骨料体积
CumVolume = 0                                     # 累计投放骨料体积

# 定义相交判断
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
        distance = math.sqrt(pow((x1 - x2), 2) + pow((y1 - y2), 2) + pow((z1 - z2), 2))
        if distance < 1.2*(r1 + r2):   # 由于ITZ而对两球心距离进行扩宽处理
            sign = False
            break
    return sign


# 定义骨料数据
SphereNum = 500                              # 球形骨料个数
points = []                                  # 累计生成球形骨料的数据
SphereDatas = []                             # 球形骨料的数据

# 随机生成骨料
for k in range(SphereNum):  # 在进行球形骨料投放的相交判断时会消耗总的SphereNum
    SphereRadius = np.random.uniform(5, 32)  # 球形骨料的半径随机生成,mm
    x1 = np.random.uniform(0, ConcLength)    # 球心的x坐标,mm
    y1 = np.random.uniform(0, ConcWidth)     # 球心的y坐标,mm
    z1 = np.random.uniform(0, ConcHeight)    # 球心的z坐标,mm
    point = (x1, y1, z1, SphereRadius)
    if len(points) == 0:
        points.append(point)
        SphereDatas.append([k + 1, x1, y1, z1, SphereRadius])  # 球形骨料的数据
    elif interact_judgement(points, point):   # 相交判断
        points.append(point)
        SphereDatas.append([k + 1, x1, y1, z1, SphereRadius])  # 球形骨料的数据
    else:
        pass

# 批量化投放骨料
s = mdb.models['Model-1']
b = SphereDatas
for i in range(len(SphereDatas)):
    mySketch = s.ConstrainedSketch(name='Profile', sheetSize=0.2)
    mySketch.ArcByCenterEnds(center=(b[i][1], b[i][2]), direction=CLOCKWISE, point1=(b[i][1], b[i][2] + b[i][4]),
                             point2=(b[i][1], b[i][2] - b[i][4]))
    mySketch.Line(point1=(b[i][1], b[i][2] + b[i][4]), point2=(b[i][1], b[i][2] - b[i][4]))
    myConstructionLine = mySketch.ConstructionLine(point1=(b[i][1], b[i][2] + b[i][4]), point2=(b[i][1], b[i][2] - b[i][4]))
    mysphere = s.Part(name='Part-' + str(i), dimensionality=THREE_D, type=DEFORMABLE_BODY)
    myPart = mysphere.BaseSolidRevolve(angle=360.0, flipRevolveDirection=OFF, sketch=mySketch)
    s.rootAssembly.DatumCsysByDefault(CARTESIAN)
    s.rootAssembly.Instance(name='Part-' + str(i), part=mysphere, dependent=OFF)
    s.rootAssembly.translate(instanceList=('Part-' + str(i),), vector=(0.0, 0.0, b[i][3]))
    session.viewports['Viewport: 1'].assemblyDisplay.geometryOptions.setValues(datumAxes=OFF)   # 隐藏构造线（基准轴）
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

s.ConstrainedSketch(name='__profile__', sheetSize=200)
s.sketches['__profile__'].rectangle(point1=(xmin, ymin), point2=(xmax, ymax))
PartExCube = s.Part(dimensionality=THREE_D, name='CubeProfile', type=DEFORMABLE_BODY)
s.parts['CubeProfile'].BaseSolidExtrude(depth=zlength, sketch=s.sketches['__profile__'])
del s.sketches['__profile__']
s.rootAssembly.Instance(name='CubeProfile', part=PartExCube, dependent=OFF)
# s.rootAssembly.translate(instanceList=('CubeProfile', ), vector=(0.0, 0.0, zmin))


######################### 批量化材料属性赋予 #########################
s.Material(name='Material-1')
s.materials['Material-1'].Elastic(table=((60000.0, 0.25),))
s.HomogeneousSolidSection(material='Material-1', name='Section-1',thickness=None)
s.Material(name='Material-2')
s.materials['Material-2'].Elastic(table=((300.0, 0.5),))
s.HomogeneousSolidSection(material='Material-2', name='Section-2',thickness=None)

# 对骨料批量指派截面
for i in range(len(SphereDatas)):
    s.parts['Part-'+str(i)].Set(cells=s.parts['Part-'+str(i)].cells, name='Part-'+str(i))
    s.parts['Part-' + str(i)].SectionAssignment(region=
        s.parts['Part-' + str(i)].sets['Part-' + str(i)], sectionName='Section-1', offset=0.0, offsetType=
        MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

# 对砂浆基体指派截面
s.parts['CubeProfile'].Set(cells=s.parts['CubeProfile'].cells, name='CubeProfile')
s.parts['CubeProfile'].SectionAssignment(region=
    s.parts['CubeProfile'].sets['CubeProfile'], sectionName='Section-2', offset=0.0, offsetType=
    MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)


######################### 把所有的骨料限制在混凝土边界内（基于高效算法）#########################

partOutVertice=[]
for i in range(len(SphereDatas)):
    ipartOutVertice = []
    for ipart in range(2):
        vertice1=s.rootAssembly.instances['Part-' + str(i)].vertices[ipart].pointOn[0]
        ipartOutVertice.append(vertice1)
    verticecenter=((ipartOutVertice[0][0] + ipartOutVertice[1][0])/2, (ipartOutVertice[0][1] + ipartOutVertice[1][1])/2,
                   (ipartOutVertice[0][2] + ipartOutVertice[1][2])/2)
    vertice3=(verticecenter[0] - abs(ipartOutVertice[0][1] - ipartOutVertice[1][1]), verticecenter[1], verticecenter[2])
    ipartOutVertice.append(vertice3)
    vertice4=(verticecenter[0] + abs(ipartOutVertice[0][1] - ipartOutVertice[1][1]), verticecenter[1], verticecenter[2])
    ipartOutVertice.append(vertice4)
    vertice5=(verticecenter[0], verticecenter[1], verticecenter[2] + abs(ipartOutVertice[0][1] - ipartOutVertice[1][1]))
    ipartOutVertice.append(vertice5)
    vertice6=(verticecenter[0], verticecenter[1], verticecenter[2] - abs(ipartOutVertice[0][1] - ipartOutVertice[1][1]))
    ipartOutVertice.append(vertice6)
    partOutVertice.append(ipartOutVertice)


OutVerticeXMax = -9999.0
OutVerticeXMin = 9999.0
OutVerticeYMax = -9999.0
OutVerticeYMin = 9999.0
OutVerticeZMax = -9999.0
OutVerticeZMin = 9999.0
for i in range(len(SphereDatas)):
    for j in range(6):
        if OutVerticeXMax <= partOutVertice[i][j][0]:
            OutVerticeXMax = partOutVertice[i][j][0]
        if OutVerticeYMax <= partOutVertice[i][j][1]:
            OutVerticeYMax = partOutVertice[i][j][1]
        if OutVerticeZMax <= partOutVertice[i][j][2]:
            OutVerticeZMax = partOutVertice[i][j][2]
        if OutVerticeXMin >= partOutVertice[i][j][0]:
            OutVerticeXMin = partOutVertice[i][j][0]
        if OutVerticeYMin >= partOutVertice[i][j][1]:
            OutVerticeYMin = partOutVertice[i][j][1]
        if OutVerticeZMin >= partOutVertice[i][j][2]:
            OutVerticeZMin = partOutVertice[i][j][2]

OutVertice = [OutVerticeXMin, OutVerticeXMax, OutVerticeYMin, OutVerticeYMax, OutVerticeZMin, OutVerticeZMax]

eps1 = 0.4         # 由于ITZ而对立方块外轮廓边界进行扩宽处理
OutVertice=[OutVerticeXMin-eps1*OutVerticeXMin, OutVerticeXMax+eps1*OutVerticeXMax, OutVerticeYMin-eps1*OutVerticeYMin,
            OutVerticeYMax+eps1*OutVerticeYMax, OutVerticeZMin-eps1*OutVerticeZMin, OutVerticeZMax+eps1*OutVerticeZMax]

# 生成外轮廓立方体块
s.ConstrainedSketch(name='__profile__', sheetSize=200)
s.sketches['__profile__'].rectangle(point1=(OutVertice[0], OutVertice[2]), point2=(OutVertice[1], OutVertice[3]))
PartExCube = s.Part(dimensionality=THREE_D, name='CubeProfile2', type=DEFORMABLE_BODY)
zdepth = OutVertice[5] - OutVertice[4]
s.parts['CubeProfile2'].BaseSolidExtrude(depth=zdepth, sketch=s.sketches['__profile__'])
del s.sketches['__profile__']
s.rootAssembly.Instance(name='CubeProfile2', part=PartExCube,dependent=OFF)
s.rootAssembly.translate(instanceList=('CubeProfile2',), vector=(0.0, 0.0 ,-abs(OutVertice[4])))

s.rootAssembly.features['CubeProfile'].suppress()            # 对'CubeProfile'实例使用：禁止

s.parts['CubeProfile2'].Set(cells=s.parts['CubeProfile2'].cells, name='CubeProfile2')
s.parts['CubeProfile2'].SectionAssignment(region=
    s.parts['CubeProfile2'].sets['CubeProfile2'], sectionName='Section-2',offset=0.0, offsetType=
    MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)


######################### 批量化从立方块砂浆中抠除所有骨料 #########################

Cumupart = []
for i in range(len(SphereDatas)):
    if i == 0:
        updatepart = 'CubeProfile2'
    else:
        updatepart = 'updatepart-' + str(i)
    updatepart2 = 'updatepart'
    s.rootAssembly.InstanceFromBooleanCut(name=updatepart2,                # 命名
        instanceToBeCut=s.rootAssembly.instances[updatepart],              # 要被切割的实例（被抠的立方块）
        cuttingInstances=(s.rootAssembly.instances['Part-' + str(i)], ),   # 切割去掉的实例（抠除的骨料）
        originalInstances=SUPPRESS)                                        # 原始比例，默认：抑制
    s.rootAssembly.features['Part-' + str(i)].resume()                     # 使'Part-' + str(i)从禁用改成继续
    Cumupart.append(s.rootAssembly.instances['Part-'+str(i)])

Cumupart.append(s.rootAssembly.instances[ 'updatepart-' + str(i+1)])
Cumupart=tuple(Cumupart)
s.rootAssembly.InstanceFromBooleanMerge(name='Part-totall', instances=Cumupart, keepIntersections=ON,
                                        originalInstances=SUPPRESS, domain=GEOMETRY)

# InstanceFromBooleanCut(实例基本库中查询)---这个方法在实例存储库中减去或后创建一个PartInstance，从基本零件实例中切割一组零件实例的几何形状。

######################### 批量化生成 ITZ（界面过渡区） #########################
for i in range(len(SphereDatas)):
    SphereDatas[i][-1] = SphereDatas[i][-1] * 1.2   # 在原有骨料半径的基础上扩大1.2倍

# 批量化生成外径part（骨料+ITZ）
b = SphereDatas
for i in range(len(SphereDatas)):
    mySketch = s.ConstrainedSketch(name='Profile', sheetSize=0.2)
    mySketch.ArcByCenterEnds(center=(b[i][1], b[i][2]), direction=CLOCKWISE, point1=(b[i][1], b[i][2] + b[i][4]),
                             point2=(b[i][1], b[i][2] - b[i][4]))
    mySketch.Line(point1=(b[i][1], b[i][2] + b[i][4]), point2=(b[i][1], b[i][2] - b[i][4]))
    myConstructionLine = mySketch.ConstructionLine(point1=(b[i][1], b[i][2] + b[i][4]), point2=(b[i][1], b[i][2] - b[i][4]))
    mysphere = s.Part(name='ExPart-' + str(i), dimensionality=THREE_D, type=DEFORMABLE_BODY)
    myPart = mysphere.BaseSolidRevolve(angle=360.0, flipRevolveDirection=OFF, sketch=mySketch)
    s.rootAssembly.DatumCsysByDefault(CARTESIAN)
    s.rootAssembly.Instance(dependent=OFF, name='ExPart-' + str(i), part=mysphere)
    s.rootAssembly.translate(instanceList=('ExPart-' + str(i),), vector=(0.0, 0.0, b[i][3]))
    del mysphere
    del myConstructionLine
    del myPart
    del mySketch

# 布尔差集批量化生成ITZ；从外径instance（骨料+ITZ）布尔差集减去内径instance（骨料）
for i in range(len(SphereDatas)):
    s.rootAssembly.InstanceFromBooleanCut(name='ITZ-' + str(i),           # 命名
        instanceToBeCut=s.rootAssembly.instances['ExPart-' + str(i)],     # 要被切割的实例（骨料+ITZ）
        cuttingInstances=(s.rootAssembly.instances['Part-' + str(i)], ),  # 切割去掉的实例（骨料）
        originalInstances=SUPPRESS)                                       # 原始比例，默认：抑制
    s.rootAssembly.features['Part-' + str(i)].resume()                    # 使'Part-' + str(i)从禁用改成继续

# 将所有ITZ的instance建立成Set
ITZinstances = s.rootAssembly.instances['ITZ-' + str(0) + '-1'].cells[0:0]
for i in range(len(SphereDatas)):
    ITZinstances = ITZinstances + s.rootAssembly.instances['ITZ-' + str(i) + '-1'].cells

s.rootAssembly.Set(cells=ITZinstances, name='ITZinstances')


# 批量化对ITZ赋予材料属性
s.Material(name='Material-3')
s.materials['Material-3'].Elastic(table=((50000.0, 0.3),))
s.HomogeneousSolidSection(material='Material-3', name='Section-3',thickness=None)

for i in range(len(SphereDatas)):
    s.parts['ITZ-' + str(i)].Set(cells=s.parts['ITZ-' + str(i)].cells, name='ITZinstances')  # 对ITZ指派截面
    s.parts['ITZ-' + str(i)].SectionAssignment(region=
        s.parts['ITZ-' + str(i)].sets['ITZinstances'], sectionName='Section-3', offset=0.0, offsetType=
        MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

for i in range(len(SphereDatas)):
    s.rootAssembly.features['Part-' + str(i)].resume()                    # 使'Part-' + str(i)从禁用改成继续

for i in range(len(SphereDatas)):
    s.rootAssembly.features['Part-' + str(i)].suppress()                    # 使'Part-' + str(i)从继续改成禁用
# 注：---2022.8.12
# 有部分骨料没有包裹ITZ，这可能是由于对ITZ的厚度设置较大导致距离较近的骨料ITZ或者立方块边界相交而生成失败。
# solve：1、在进行骨料投放相交判断的距离（两骨料球心距离）里增加各自ITZ厚度；
#        2、并且在建立立方块外轮廓时也需对其边界进行扩宽处理，避免ITZ与边界相交。

# 注：---2022.8.13
# 应该改变骨料、ITZ、立方块的生成顺序，先骨料，后ITZ，再立方块砂浆。







