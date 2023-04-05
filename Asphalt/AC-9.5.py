# -*- coding: utf-8 -*-
'''三维随机多面体骨料建模-圆柱体基体-cylinder basic'''
'''无ITZ，只有骨料和沥青砂浆'''

from abaqus import *
from abaqusConstants import *
from caeModules import *
import os
import math
import numpy as np
from numpy import random
import matplotlib.pyplot as plt
from visualization import *
from odbAccess import *

Mdb()                                        # 模型初始化
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
# 去掉掩码，比如说几何体的编号信息存在掩码,index和coordinate二选一就行，一般选coordinate。

Modelname = 'Model-1'
Partname = 'Part-1'
Instancename = 'Part-1-1'
Jobname = 'RanModel-1'
os.chdir(r"E:\Abaqus-test\Asphalt\AC-9.5")        # 设置工作目录

# 基体basic参数
Cyradius = 50                                       # 圆柱体半径，mm
CyHeight = 100.0                                    # 圆柱体高度，mm
VolumeCy = np.pi * pow(Cyradius, 2) * CyHeight      # 圆柱体体积，mm³
AggRatio = 0.117                                    # 骨料体积比
TargetVol = VolumeCy * AggRatio                     # 给定生成的目标骨料体积，mm³
CumcellVolume = 0.0                                 # 生成骨料的累计体积，mm³

Numlayers = 5                                     # 总共层数
NumNodeslayer1st = 1                              # 第1层的节点数
NumNodeslayer2nd = 8                              # 第2层的节点数
NumNodeslayer3rd = 8                              # 第3层的节点数
NumNodeslayer4th = 8                              # 第4层的节点数
NumNodeslayer5th = 1                              # 第5层的节点数
TotalNumNodes = NumNodeslayer1st + NumNodeslayer2nd + NumNodeslayer3rd + NumNodeslayer4th + NumNodeslayer5th  # 总结点数：26
FaceAndNodes = np.zeros((48, 13))                 # 记录生成随机多面体的各面编号及组成节点
Numaggs = 100000                                  # 骨料个数
RamNode = np.zeros((Numaggs, TotalNumNodes, 4))   # spherical coordinates, 记录球坐标到 RamNode 数组里，numpy的矩阵里第一个是页，第二个是行，第三个是列
RamNodeDK = np.zeros((Numaggs, TotalNumNodes, 4)) # 记录笛卡尔坐标到 RamNodeDK 数组里
cellVolume = np.zeros((Numaggs, 1))               # 记录每个骨料的体积
volumeCentroid = np.zeros((Numaggs, 4))           # 记录每个骨料的质心
AggRadius = np.zeros((1, Numaggs))                # 所有骨料的直径，mm
AMaxlen = np.zeros((Numaggs, 1))                  # 记录每个骨料的空间最长距离
TMaxlenCoord = np.zeros((Numaggs, 2, 3))          # 记录每个骨料组成空间最长距离的两个点坐标
TMinlenCoord = np.zeros((Numaggs, 2, 3))          # 记录每个骨料组成空间最短距离的两个点坐标
TRect = np.zeros((Numaggs, 50, 3))                # 记录骨料的节点坐标
RamAggDatas = []                                  # 随机多面体骨料的数据
points = []                                       # 质心坐标集

Dmax = 13.2                                       # 最大骨料直径，mm
Dmin = 9.5                                        # 最小骨料直径，mm

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
        # distancce calculate 相交判断
        distance = math.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)      # math.sqrt()是用于计算数字X的平方根的函数
        if distance < 1.01*(r1 + r2):
            sign = False
            break
    return sign

######################### 生成圆柱体基体轮廓的命令 ######################
s = mdb.models[Modelname].ConstrainedSketch(name='__profile__', sheetSize=200.0)
s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(Cyradius, 0.0))
p = mdb.models[Modelname].Part(name='basic', dimensionality=THREE_D, type=DEFORMABLE_BODY)
p.BaseSolidExtrude(sketch=s, depth=CyHeight)
del mdb.models[Modelname].sketches['__profile__']
mdb.models[Modelname].rootAssembly.Instance(name='basic',part=p,dependent=OFF)

######################### 装配刚体压头和垫板轮廓的命令 ###################### 用于传递荷载和约束
s = mdb.models[Modelname].ConstrainedSketch(name='__profile__', sheetSize=200.0)
s.ConstructionLine(point1=(0.0, -100.0), point2=(0.0, 100.0))
s.Line(point1=(0.0, 0.0), point2=(60.0, 0.0))
s.Line(point1=(60.0, 0.0), point2=(60.0, 10.0))
s.Line(point1=(60.0, 10.0), point2=(0.0, 10.0))
p = mdb.models[Modelname].Part(name='yt', dimensionality=THREE_D, type=ANALYTIC_RIGID_SURFACE)
p.AnalyticRigidSurfRevolve(sketch=s)
del mdb.models[Modelname].sketches['__profile__']
mdb.models[Modelname].rootAssembly.Instance(name='yt',part=p,dependent=OFF)
mdb.models[Modelname].rootAssembly.translate(instanceList=('yt', ), vector=(0, 0, 100.0))
mdb.models[Modelname].rootAssembly.rotate(instanceList=('yt', ), axisPoint=(-50.0, 0.0, 100.0), axisDirection=(
    100.0, 0.0, 0.0), angle=90.0)
mdb.models[Modelname].rootAssembly.Instance(name='db',part=p,dependent=OFF)
mdb.models[Modelname].rootAssembly.rotate(instanceList=('db', ), axisPoint=(-50.0, 0.0, 0.0), axisDirection=(
    100.0, 0.0, 0.0), angle=90.0)
mdb.models[Modelname].rootAssembly.translate(instanceList=('db', ), vector=(0, 0, -10.0))
session.viewports['Viewport: 1'].assemblyDisplay.geometryOptions.setValues(datumAxes=OFF)   # 关闭基准轴显示

########################## 多面体骨料生成 ###############################

for ik in range(Numaggs):
    r0 = pow(((random.rand() * (pow(Dmax, 0.5) - pow(Dmin, 0.5))) + pow(Dmin, 0.5)), 2) / 2  # fuller级配下的骨料半径
    AggRadius[0][ik] = r0 * 2.0                      # 骨料直径，mm
    ifflag = 0                                       # 3D面每个面的编号
    SizeLength = 200
    s = mdb.models[Modelname].ConstrainedSketch(name='_profile_', sheetSize=1.0)
    s.rectangle(point1=(-SizeLength / 2, SizeLength / 2),point2=(SizeLength / 2, -SizeLength / 2))
    p = mdb.models[Modelname].Part(name='Part-' + str(ik), dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(depth=SizeLength / 2,sketch=s)
    session.viewports['Viewport: 1'].setValues(displayedObject=p)
    del mdb.models[Modelname].sketches['_profile_']    # 删除草图、拉伸特征
    del mdb.models[Modelname].parts['Part-' + str(ik)].features['Solid extrude-1']
    rvar = 0.2                                       # 节点沿径向的波动倍数（相对于半径），其值应在（0.2-0.4）之间较契合实际骨料（根据论文）
    avar = 12.0/180.0 * np.pi                        # 波动最大范围角转化为弧度；其值应在（18°-36°）之间较契合实际骨料（根据论文），但是度数过大易导致覆盖边失败
    bvar = 18.0 / 180.0 * np.pi                      # 第一层和第五层允许波动偏大，第二三四层波动应偏小
    setrzero = 1                                     # 沿径向是否波动的调节系数，不波动为0,波动为1
    setzero = 1                                      # 沿天顶角方向或方位角方向是否波动的调节系数，不波动为0,波动为1
    for j in range(Numlayers):
        theta = j * 45.0 / 180.0 * np.pi             # 天顶角---转化为弧度
        if abs(j - 0.0) <= 10e-10:                   # 确定层数，j=0，第一层
            for i in range(NumNodeslayer1st):
                fai = i * 45.0 / 180.0 * np.pi       # 方位角---转化为弧度
                RamNode[ik][j][0] = j + 1            # 从此行以下依次确定：节点编号、半径、天顶角、方位角
                RamNode[ik][j][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * np.random.rand())   # random.choice((-1, 1))随机生成(-1 或 1)
                RamNode[ik][j][2] = theta + setzero * bvar * (-1 + 2 * np.random.rand())      # (-1 + 2 * random.rand())随机生成(-1,1)的浮点数
                RamNode[ik][j][3] = fai + setzero * (2 * np.pi) * (-1 + 2 * np.random.rand())
        elif abs(j - (Numlayers - 1.0)) <= 10e-10:  # j=4，第五层
            for i in range(NumNodeslayer5th):  # NumNodeslayer5th = 1，这层的节点数为1个
                fai = i * 45.0 / 180.0 * np.pi  # 第一层和第五层的方位角波动范围角为(2 * np.pi)
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][0] = (Numlayers - 2) * NumNodeslayer2nd + 2
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * np.random.rand())
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][2] = theta + setzero * bvar * (-1 + 2 * np.random.rand())
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][3] = fai + setzero * (2 * np.pi) * (-1 + 2 * np.random.rand())
        else:                                  # j=[1, 2, 3]， 第二、三、四层
            for i in range(NumNodeslayer2nd):  # 在范围 NumNodeslayer2nd = 8 之内按序波动是因为二三四层的节点数都是8
                fai = i * 45.0 / 180.0 * np.pi
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][0] = i + (j - 1) * 8 + 2
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * np.random.rand())
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][2] = theta + setzero * avar * (-1 + 2 * np.random.rand())
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][3] = fai + setzero * avar * (-1 + 2 * np.random.rand())
    for i in range(TotalNumNodes):            # 把球坐标系转化成笛卡尔坐标系，TotalNumNodes = 26
        RamNodeDK[ik][i][0] = RamNode[ik][i][0]                                                           # 球坐标转笛卡尔坐标
        RamNodeDK[ik][i][1] = RamNode[ik][i][1] * np.sin(RamNode[ik][i][2]) * np.cos(RamNode[ik][i][3])   # x = r * sinθ * cosφ
        RamNodeDK[ik][i][2] = RamNode[ik][i][1] * np.sin(RamNode[ik][i][2]) * np.sin(RamNode[ik][i][3])   # y = r * sinθ * sinφ
        RamNodeDK[ik][i][3] = RamNode[ik][i][1] * np.cos(RamNode[ik][i][2])                               # z = r * cosθ
    a1 = [0, 0, 0]
    a2 = [0, 0, 0]
    a3 = [0, 0, 0]
    a4 = [0, 0, 0]
    a5 = [0, 0, 0]
    a6 = [0, 0, 0]
    b1 = (0, 0, 0)
    b2 = (0, 0, 0)
    b3 = (0, 0, 0)
    c1 = (0, 0, 0)
    c2 = (0, 0, 0)
    c3 = (0, 0, 0)
    for j in range(Numlayers):                # 从第一层到第五层的循环，Numlayers = 5
        if abs(j - 0.0) <= 10e-10:            # 第一层，j = 0
            a1[0] = RamNodeDK[ik][j][1]
            a1[1] = RamNodeDK[ik][j][2]
            a1[2] = RamNodeDK[ik][j][3]
            b1 = tuple(a1)                    # 当j=0，b1为 DK[ik][0][] ，编号为1号节点
            for i in range(NumNodeslayer2nd):  # i=[0,8)
                a2[0] = RamNodeDK[ik][i + 1][1]
                a2[1] = RamNodeDK[ik][i + 1][2]
                a2[2] = RamNodeDK[ik][i + 1][3]
                b2 = tuple(a2)                # 当j=0，i=0，b2为 DK[ik][1][] ，编号为2号节点；当j=0，i=6，b2为 DK[ik][7][] ，编号为8号节点
                a3[0] = RamNodeDK[ik][i + 2][1]
                a3[1] = RamNodeDK[ik][i + 2][2]
                a3[2] = RamNodeDK[ik][i + 2][3]
                b3 = tuple(a3)                # 当j=0，i=0，b3为 DK[ik][2][] ，编号为3号节点；当j=0，i=6，b3为 DK[ik][8][] ，编号为9号节点
                if abs(i - (NumNodeslayer2nd - 1)) <= 10e-10:  # i=7
                    a2[0] = RamNodeDK[ik][i + 1][1]
                    a2[1] = RamNodeDK[ik][i + 1][2]
                    a2[2] = RamNodeDK[ik][i + 1][3]
                    b2 = tuple(a2)             # 当j=0，i=7，b2为 DK[ik][8][] ，编号为9号节点
                    a3[0] = RamNodeDK[ik][1][1]
                    a3[1] = RamNodeDK[ik][1][2]
                    a3[2] = RamNodeDK[ik][1][3]
                    b3 = tuple(a3)             # 当j=0，i=7，b3为 DK[ik][1][] ，编号为2号节点
                p.WirePolyLine(mergeType=IMPRINT, meshable=ON,points=((b1, b2), (b2, b3), (b3, b1)))
        elif abs(j - (Numlayers - 1.0)) <= 10e-10:     # 第5层,j = 4
            a1[0] = RamNodeDK[ik][TotalNumNodes - 1][1]
            a1[1] = RamNodeDK[ik][TotalNumNodes - 1][2]
            a1[2] = RamNodeDK[ik][TotalNumNodes - 1][3]
            b1 = tuple(a1)                             # 当j=4，i=0，b1为 DK[ik][25][] ，编号为26号节点
            for i in range(NumNodeslayer2nd):
                a2[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][1]
                a2[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][2]
                a2[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][3]
                b2 = tuple(a2)                         # 当j=4，i=0，b2为 DK[ik][17][] ，编号为18号节点；当j=4，i=6，b2为 DK[ik][23][] ，编号为24号节点
                a3[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 2 + i][1]
                a3[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 2 + i][2]
                a3[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 2 + i][3]
                b3 = tuple(a3)                         # 当j=4，i=0，b3为 DK[ik][18][] ，编号为19号节点；当j=4，i=6，b3为 DK[ik][24][] ，编号为25号节点
                if abs(i - (NumNodeslayer2nd - 1)) <= 10e-10:  # i=7
                    a2[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][1]
                    a2[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][2]
                    a2[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][3]
                    b2 = tuple(a2)                     # 当j=4，i=7，b2为 DK[ik][24][] ，编号为25号节点
                    a3[0] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd +NumNodeslayer3rd][1]
                    a3[1] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd +NumNodeslayer3rd][2]
                    a3[2] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd +NumNodeslayer3rd][3]
                    b3 = tuple(a3)                     # 当j=4，i=7，b3为 DK[ik][17][] ，编号为18号节点
                p.WirePolyLine(mergeType=IMPRINT, meshable=ON, points=((b1, b2), (b2, b3), (b3, b1)))
        elif abs(j - 3) >= 10e-10:                    # 第2,3层,j = [1，2]
            for i in range(NumNodeslayer2nd):         # i = [0,8)
                a1[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][1]
                a1[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][2]
                a1[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][3]
                b1 = tuple(a1)                        # 当j=1，i=0，b1为 DK[ik][1][] ，编号为2号节点；当j=1，i=6，b1为 DK[ik][7][] ，编号为8号节点
                # 当j=2，i=0，b1为 DK[ik][9][] ，编号为10号节点；当j=2，i=6，b1为 DK[ik][15][] ，编号为16号节点
                a2[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][1]
                a2[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][2]
                a2[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][3]
                b2 = tuple(a2)                        # 当j=1，i=0，b2为 DK[ik][9][] ，编号为10号节点；当j=1，i=6，b2为 DK[ik][15][] ，编号为16号节点
                # 当j=2，i=0，b2为 DK[ik][17][] ，编号为18号节点；当j=2，i=6，b2为 DK[ik][23][] ，编号为24号节点
                a3[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][1]
                a3[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][2]
                a3[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][3]
                b3 = tuple(a3)                        # 当j=1，i=0，b3为 DK[ik][10][] ，编号为11号节点；当j=1，i=6，b3为 DK[ik][16][] ，编号为17号节点
                # 当j=2，i=0，b3为 DK[ik][18][] ，编号为19号节点；当j=2，i=6，b3为 DK[ik][24][] ，编号为25号节点
                a4[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][1]
                a4[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][2]
                a4[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][3]
                c1 = tuple(a4)                        # 当j=1，i=0，c1为 DK[ik][1][] ，编号为2号节点；当j=1，i=6，c1为 DK[ik][7][] ，编号为8号节点
                # 当j=2，i=0，c1为 DK[ik][9][] ，编号为10号节点；当j=2，i=6，c1为 DK[ik][15][] ，编号为16号节点
                a5[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 2 + i][1]
                a5[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 2 + i][2]
                a5[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 2 + i][3]
                c2 = tuple(a5)                        # 当j=1，i=0，c2为 DK[ik][2][] ，编号为3号节点；当j=1，i=6，c2为 DK[ik][8][] ，编号为9号节点
                # 当j=2，i=0，c2为 DK[ik][10][] ，编号为11号节点；当j=2，i=6，c2为 DK[ik][16][] ，编号为17号节点
                a6[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][1]
                a6[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][2]
                a6[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][3]
                c3 = tuple(a6)                        # 当j=1，i=0，c3为 DK[ik][10][] ，编号为11号节点；当j=1，i=6，c3为 DK[ik][16][] ，编号为17号节点
                # 当j=2，i=0，c3为 DK[ik][18][] ，编号为19号节点；当j=2，i=6，c3为 DK[ik][24][] ，编号为25号节点
                if abs(i - (NumNodeslayer2nd - 1)) <= 10e-10:   # i = 7
                    a2[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][1]
                    a2[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][2]
                    a2[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][3]
                    b2 = tuple(a2)                        # 当j=1，i=7，b2为 DK[ik][16][] ，编号为17号节点
                    # 当j=2，i=7，b2为 DK[ik][24][] ，编号为25号节点
                    a3[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][1]
                    a3[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][2]
                    a3[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][3]
                    b3 = tuple(a3)                        # 当j=1，i=7，b3为 DK[ik][9][] ，编号为10号节点
                    # 当j=2，i=7，b3为 DK[ik][17][] ，编号为18号节点
                    a5[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1][1]
                    a5[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1][2]
                    a5[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1][3]
                    c2 = tuple(a5)                        # 当j=1，i=7，c2为 DK[ik][1][] ，编号为2号节点
                    # 当j=2，i=7，c2为 DK[ik][9][] ，编号为10号节点
                    a6[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][1]
                    a6[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][2]
                    a6[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][3]
                    c3 = tuple(a6)                        # 当j=1，i=7，c3为 DK[ik][9][] ，编号为10号节点
                    # 当j=2，i=7，c3为 DK[ik][17][] ，编号为18号节点
                p.WirePolyLine(mergeType=IMPRINT,meshable=ON,points=((b1, b2), (b2, b3), (b3, b1)))  # 相邻三顶点构成封闭线框
    for j in range(Numlayers):
        if abs(j - 0.0) <= 10e-10:                   # 第一层,j = 0
            a1[0] = RamNodeDK[ik][j][1]
            a1[1] = RamNodeDK[ik][j][2]
            a1[2] = RamNodeDK[ik][j][3]
            b1 = tuple(a1)
            for i in range(NumNodeslayer2nd):
                a2[0] = RamNodeDK[ik][i + 1][1]
                a2[1] = RamNodeDK[ik][i + 1][2]
                a2[2] = RamNodeDK[ik][i + 1][3]
                b2 = tuple(a2)
                a3[0] = RamNodeDK[ik][i + 2][1]
                a3[1] = RamNodeDK[ik][i + 2][2]
                a3[2] = RamNodeDK[ik][i + 2][3]
                b3 = tuple(a3)
                if abs(i - (NumNodeslayer2nd - 1)) <= 10e-10:
                    a2[0] = RamNodeDK[ik][i + 1][1]
                    a2[1] = RamNodeDK[ik][i + 1][2]
                    a2[2] = RamNodeDK[ik][i + 1][3]
                    b2 = tuple(a2)
                    a3[0] = RamNodeDK[ik][1][1]
                    a3[1] = RamNodeDK[ik][1][2]
                    a3[2] = RamNodeDK[ik][1][3]
                    b3 = tuple(a3)
                p.CoverEdges(edgeList=(                             # 根据边的中点确定边然后构成线框
                    p.edges.findAt(((b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2, (b1[2] + b2[2]) / 2), ),
                    p.edges.findAt(((b2[0] + b3[0]) / 2, (b2[1] + b3[1]) / 2, (b2[2] + b3[2]) / 2), ),
                    p.edges.findAt(((b3[0] + b1[0]) / 2, (b3[1] + b1[1]) / 2, (b3[2] + b1[2]) / 2), )),
                    tryAnalytical=True)
                FaceAndNodes[ifflag][0] = ifflag + 1
                FaceAndNodes[ifflag][1] = a1[0]
                FaceAndNodes[ifflag][2] = a1[1]
                FaceAndNodes[ifflag][3] = a1[2]
                FaceAndNodes[ifflag][4] = a2[0]
                FaceAndNodes[ifflag][5] = a2[1]
                FaceAndNodes[ifflag][6] = a2[2]
                FaceAndNodes[ifflag][7] = a3[0]
                FaceAndNodes[ifflag][8] = a3[1]
                FaceAndNodes[ifflag][9] = a3[2]
                FaceAndNodes[ifflag][10] = (a1[0] + a2[0] + a3[0]) / 3
                FaceAndNodes[ifflag][11] = (a1[1] + a2[1] + a3[1]) / 3
                FaceAndNodes[ifflag][12] = (a1[2] + a2[2] + a3[2]) / 3
                ifflag += 1
        elif abs(j - (Numlayers - 1.0)) <= 10e-10:       # 第五层,j = 4
            a1[0] = RamNodeDK[ik][TotalNumNodes - 1][1]
            a1[1] = RamNodeDK[ik][TotalNumNodes - 1][2]
            a1[2] = RamNodeDK[ik][TotalNumNodes - 1][3]
            b1 = tuple(a1)
            for i in range(NumNodeslayer2nd):
                a2[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][1]
                a2[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][2]
                a2[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][3]
                b2 = tuple(a2)
                a3[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 2 + i][1]
                a3[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 2 + i][2]
                a3[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 2 + i][3]
                b3 = tuple(a3)
                if abs(i - (NumNodeslayer2nd - 1)) <= 10e-10:
                    a2[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][1]
                    a2[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][2]
                    a2[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][3]
                    b2 = tuple(a2)
                    a3[0] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd + NumNodeslayer3rd][1]
                    a3[1] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd + NumNodeslayer3rd][2]
                    a3[2] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd + NumNodeslayer3rd][3]
                    b3 = tuple(a3)
                p.CoverEdges(edgeList=(
                    p.edges.findAt(((b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2, (b1[2] + b2[2]) / 2), ),
                    p.edges.findAt(((b2[0] + b3[0]) / 2, (b2[1] + b3[1]) / 2, (b2[2] + b3[2]) / 2), ),
                    p.edges.findAt(((b3[0] + b1[0]) / 2, (b3[1] + b1[1]) / 2, (b3[2] + b1[2]) / 2), )),
                    tryAnalytical=True)
                FaceAndNodes[ifflag][0] = ifflag + 1
                FaceAndNodes[ifflag][1] = a1[0]
                FaceAndNodes[ifflag][2] = a1[1]
                FaceAndNodes[ifflag][3] = a1[2]
                FaceAndNodes[ifflag][4] = a2[0]
                FaceAndNodes[ifflag][5] = a2[1]
                FaceAndNodes[ifflag][6] = a2[2]
                FaceAndNodes[ifflag][7] = a3[0]
                FaceAndNodes[ifflag][8] = a3[1]
                FaceAndNodes[ifflag][9] = a3[2]
                FaceAndNodes[ifflag][10] = (a1[0] + a2[0] + a3[0]) / 3
                FaceAndNodes[ifflag][11] = (a1[1] + a2[1] + a3[1]) / 3
                FaceAndNodes[ifflag][12] = (a1[2] + a2[2] + a3[2]) / 3
                ifflag += 1
        elif abs(j - 3) >= 10e-10:                                     # 第二、三、四层,j = [1, 2, 3]
            for i in range(NumNodeslayer2nd):
                a1[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][1]
                a1[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][2]
                a1[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][3]
                b1 = tuple(a1)
                a2[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][1]
                a2[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][2]
                a2[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][3]
                b2 = tuple(a2)
                a3[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][1]
                a3[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][2]
                a3[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][3]
                b3 = tuple(a3)
                a4[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][1]
                a4[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][2]
                a4[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1 + i][3]
                c1 = tuple(a4)
                a5[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 2 + i][1]
                a5[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 2 + i][2]
                a5[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 2 + i][3]
                c2 = tuple(a5)
                a6[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][1]
                a6[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][2]
                a6[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 2 + i][3]
                c3 = tuple(a6)
                if abs(i - (NumNodeslayer2nd - 1)) <= 10e-10:
                    a2[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][1]
                    a2[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][2]
                    a2[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 1 + i][3]
                    b2 = tuple(a2)
                    a3[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][1]
                    a3[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][2]
                    a3[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][3]
                    b3 = tuple(a3)
                    a5[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1][1]
                    a5[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1][2]
                    a5[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 1) + 1][3]
                    c2 = tuple(a5)
                    a6[0] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][1]
                    a6[1] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][2]
                    a6[2] = RamNodeDK[ik][NumNodeslayer2nd * j + 1][3]
                    c3 = tuple(a6)
                p.CoverEdges(edgeList=(                                # 封闭线框形成封闭面
                    p.edges.findAt(((b1[0] + b2[0]) / 2, (b1[1] + b2[1]) / 2, (b1[2] + b2[2]) / 2), ),
                    p.edges.findAt(((b2[0] + b3[0]) / 2, (b2[1] + b3[1]) / 2, (b2[2] + b3[2]) / 2), ),
                    p.edges.findAt(((b3[0] + b1[0]) / 2, (b3[1] + b1[1]) / 2, (b3[2] + b1[2]) / 2), )),
                    tryAnalytical=True)
                p.CoverEdges(edgeList=(
                    p.edges.findAt(((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2, (c1[2] + c2[2]) / 2), ),
                    p.edges.findAt(((c2[0] + c3[0]) / 2, (c2[1] + c3[1]) / 2, (c2[2] + c3[2]) / 2), ),
                    p.edges.findAt(((c3[0] + c1[0]) / 2, (c3[1] + c1[1]) / 2, (c3[2] + c1[2]) / 2), )),
                    tryAnalytical=True)
                FaceAndNodes[ifflag][0] = ifflag + 1
                FaceAndNodes[ifflag][1] = a1[0]
                FaceAndNodes[ifflag][2] = a1[1]
                FaceAndNodes[ifflag][3] = a1[2]
                FaceAndNodes[ifflag][4] = a2[0]
                FaceAndNodes[ifflag][5] = a2[1]
                FaceAndNodes[ifflag][6] = a2[2]
                FaceAndNodes[ifflag][7] = a3[0]
                FaceAndNodes[ifflag][8] = a3[1]
                FaceAndNodes[ifflag][9] = a3[2]
                FaceAndNodes[ifflag][10] = (a1[0] + a2[0] + a3[0]) / 3
                FaceAndNodes[ifflag][11] = (a1[1] + a2[1] + a3[1]) / 3
                FaceAndNodes[ifflag][12] = (a1[2] + a2[2] + a3[2]) / 3
                ifflag += 1
                FaceAndNodes[ifflag][0] = ifflag + 1
                FaceAndNodes[ifflag][1] = c1[0]
                FaceAndNodes[ifflag][2] = c1[1]
                FaceAndNodes[ifflag][3] = c1[2]
                FaceAndNodes[ifflag][4] = c2[0]
                FaceAndNodes[ifflag][5] = c2[1]
                FaceAndNodes[ifflag][6] = c2[2]
                FaceAndNodes[ifflag][7] = c3[0]
                FaceAndNodes[ifflag][8] = c3[1]
                FaceAndNodes[ifflag][9] = c3[2]
                FaceAndNodes[ifflag][10] = (c1[0] + c2[0] + c3[0]) / 3
                FaceAndNodes[ifflag][11] = (c1[1] + c2[1] + c3[1]) / 3
                FaceAndNodes[ifflag][12] = (c1[2] + c2[2] + c3[2]) / 3
                ifflag += 1                   # 1、3D封闭面构成多面实体
    facesslist = []                       # 2、前边根据边的中点确定边然后构成线框，此处根据三边的中点来确定面-通过findaAt函数实现
    for ii in range(int(FaceAndNodes.shape[0])):  # 3、把每个面添加（append）到facesslist里面
        facesslist.append( mdb.models[Modelname].parts['Part-' + str(ik)].faces.findAt((FaceAndNodes[ii][10], FaceAndNodes[ii][11], FaceAndNodes[ii][12]),) )
    p.AddCells(faceList=facesslist,flipped=True)
    mdb.models[Modelname].rootAssembly.Instance(dependent=OFF, name='Part-' + str(ik),
        part=mdb.models[Modelname].parts['Part-' + str(ik)])     # 把 part 转化成 instance
    volumeCentroid[ik][0] = ik + 1
    volumeCentroid[ik][1] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][0]
    volumeCentroid[ik][2] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][1]
    volumeCentroid[ik][3] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][2]
    cellVolume[ik][0] = mdb.models[Modelname].parts['Part-' + str(ik)].cells[0].getSize()     # 提取parts单个多面体部件体积
    # cellVolume[ik][0] = mdb.models[Modelname].rootAssembly.getMassProperties()['Volume']    # 提取rootAssembly单个多面体实例体积
    vertices = mdb.models[Modelname].rootAssembly.instances['Part-' + str(ik)].vertices
    for i in range(len(vertices)):
        x = vertices[i].pointOn[0][0]            # pointOn---顶点坐标
        y = vertices[i].pointOn[0][1]
        z = vertices[i].pointOn[0][2]
        TRect[ik][i][:] = [x, y, z]              # 把提取的坐标保存在数组TRect里

    TMaxlenMax = 0.0                             # 单个骨料空间最长距离计算
    TMinlenMin = 999.0
    for i in range(len(vertices)):
        for j in range(len(vertices)):
            TMaxlen2 = math.sqrt(pow((TRect[ik][i][0]-TRect[ik][j][0]),2)+ pow((TRect[ik][i][1]-TRect[ik][j][1]),2)+ pow((TRect[ik][i][2]-TRect[ik][j][2]),2))
            if TMaxlen2 >= TMaxlenMax:
                TMaxlenMax = TMaxlen2
                AMaxlen[ik][0] = TMaxlenMax
                TMaxlenCoord[0][0][:] = TRect[ik][i][:]
                TMaxlenCoord[0][1][:] = TRect[ik][j][:]
            if TMaxlen2 <= TMinlenMin and TMaxlen2 > 0.0:
                TMinlenMin = TMaxlen2
                TMinlenCoord[0][0][:] = TRect[ik][i][:]
                TMinlenCoord[0][1][:] = TRect[ik][j][:]
    CumcellVolume = CumcellVolume + cellVolume[ik][0]
    if CumcellVolume - TargetVol >= 0.0:
        break

Numaggs = ik+1                                 # 累计生成的骨料个数，由于ik在循环里计数是从0开始，故骨料个数应为ik+1
IndexAR = AggRadius[0].argsort()[::-1]         # ’AggRadius‘是单个骨料最大空间距离，对它进行降序排列，方便从大到小投放骨料

ik = 0
MaxIter = 100000000                            # 最大的骨料投放迭代次数
for ii in range(MaxIter):
    if abs(len(RamAggDatas)-Numaggs) <= 10e-10:
        break
    x1 = random.uniform(-(Cyradius- 1.1*AMaxlen[IndexAR[ik]][0]), (Cyradius- 1.1*AMaxlen[IndexAR[ik]][0]))      # 质心的x坐标，mm
    y1 = random.uniform(-(Cyradius- 1.1*AMaxlen[IndexAR[ik]][0]), (Cyradius- 1.1*AMaxlen[IndexAR[ik]][0]))      # 质心的y坐标，mm
    z1 = random.uniform(AMaxlen[IndexAR[ik]][0]/2, CyHeight- AMaxlen[IndexAR[ik]][0]/2)                         # 质心的z坐标，mm
    xy = pow((x1 ** 2 + y1 ** 2) , 0.5)
    if xy < Cyradius-AMaxlen[IndexAR[ik]][0]:
        point = (x1, y1, z1, AMaxlen[IndexAR[ik]][0]/2.0)
        if len(points) == 0:
            points.append(point)
            RamAggDatas.append([ik+1, x1, y1, z1, AMaxlen[IndexAR[ik]][0] / 2.0])
            ik += 1
        elif interact_judgement(points,point):
            points.append(point)
            RamAggDatas.append([ik+1, x1, y1, z1, AMaxlen[IndexAR[ik]][0] / 2.0])
            ik += 1
        else:
            continue
    else:
        continue

b = RamAggDatas
for ik in range(len(RamAggDatas)):             # 对多面体的质心坐标进行平移
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(b[ik][1], 0.0, 0.0))
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(0.0, b[ik][2], 0.0))
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(0.0, 0.0, b[ik][3]))

# 将所有骨料的instance建立成Set
Partinstances = mdb.models[Modelname].rootAssembly.instances['Part-' + str(0)].cells[0:0]  #建立一个空数组
for i in range(len(RamAggDatas)):
    Partinstances = Partinstances + mdb.models[Modelname].rootAssembly.instances['Part-' + str(i)].cells

mdb.models[Modelname].rootAssembly.Set(cells=Partinstances, name='Partinstances')

######################### 批量化材料属性赋予 #########################
mdb.models[Modelname].Material(name='aggregate')
mdb.models[Modelname].materials['aggregate'].Density(table=((2.7e-9,),))
mdb.models[Modelname].materials['aggregate'].Elastic(table=((5.0e4, 0.20),))
mdb.models[Modelname].HomogeneousSolidSection(material='aggregate', name='Section-1',thickness=None)
mdb.models[Modelname].Material(name='asphalt-mortar')
mdb.models[Modelname].materials['asphalt-mortar'].Density(table=((2.35e-9,),))
mdb.models[Modelname].materials['asphalt-mortar'].Elastic(table=((50.0, 0.30),))
mdb.models[Modelname].HomogeneousSolidSection(material='asphalt-mortar', name='Section-2',thickness=None)


# 对骨料批量指派截面
for i in range(Numaggs):
    mdb.models[Modelname].parts['Part-'+str(i)].Set(cells=mdb.models[Modelname].parts['Part-'+str(i)].cells, name='Part-'+str(i))
    mdb.models[Modelname].parts['Part-' + str(i)].SectionAssignment(region=
        mdb.models[Modelname].parts['Part-' + str(i)].sets['Part-' + str(i)], sectionName='Section-1', offset=0.0, offsetType=
        MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

# 对砂浆基体指派截面
mdb.models[Modelname].parts['basic'].Set(cells=mdb.models[Modelname].parts['basic'].cells, name='basic')
mdb.models[Modelname].parts['basic'].SectionAssignment(region=
    mdb.models[Modelname].parts['basic'].sets['basic'], sectionName='Section-2', offset=0.0, offsetType=
    MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)


######################### 批量化从立方块砂浆中抠除所有骨料 #########################
Cumupart = []
a = mdb.models['Model-1'].rootAssembly
for i in range(len(RamAggDatas)):
    Cumupart.append(a.instances['Part-' + str(i)])

Cumupart=tuple(Cumupart)
mdb.models[Modelname].rootAssembly.InstanceFromBooleanCut(name='Part-mortar',                # 命名
    instanceToBeCut=a.instances['basic'],                                                 # 要被切割的实例（被抠的圆柱体）
    cuttingInstances=Cumupart,                                                            # 切割去掉的实例（抠除的骨料）
    originalInstances=SUPPRESS)                                                           # 原始实例，默认：抑制

# 使'Part-' + str(i)从禁用改成继续
for i in range(len(RamAggDatas)):
    mdb.models[Modelname].rootAssembly.features['Part-' + str(i)].resume()



















