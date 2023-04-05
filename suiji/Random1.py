# -*- coding: utf-8 -*-
"""三维随机凹凸型骨料建模-立方体基体-cube basic"""

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
import xlwt

Mdb()                                              # 模型初始化
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
# 去掉掩码，比如说几何体的编号信息存在掩码,index和coordinate二选一就行，一般选coordinate。

Modelname = 'Model-1'
Partname = 'Part-1'
Instancename = 'Part-1-1'
Jobname = 'RamModel-1'
os.chdir(r"E:\Abaqus-test\Three-dimensional scale model")        # 设置工作目录

# rectangular region
ConcLength = 100.0                                 # 长方体混凝土长度，mm
ConcWidth = 100.0                                  # 长方体混凝土宽度，mm
ConcHeight = 100.0                                 # 长方体混凝土高度，mm
VolumeConc = ConcLength * ConcWidth * ConcHeight   # 混凝土体积，mm³
AggRatio = 0.3                                     # 骨料体积比
TargetVol = VolumeConc * AggRatio                  # 给定生成的骨料体积，mm³
Cumcellvolume = 0.0                                # 生成骨料的累计体积，mm³

Numlayers = 5                                     # 总共层数
NumNodeslayer1st = 1                              # 第1层的节点数
NumNodeslayer2nd = 8                              # 第2层的节点数
NumNodeslayer3rd = 8                              # 第3层的节点数
NumNodeslayer4th = 8                              # 第4层的节点数
NumNodeslayer5th = 1                              # 第5层的节点数
TotalNumNodes = NumNodeslayer1st + NumNodeslayer2nd + NumNodeslayer3rd + NumNodeslayer4th + NumNodeslayer5th  # 总结点数：26
FaceAndNodes = np.zeros((48, 13))                 # 记录生成随机多面体的各面编号及组成节点
Numaggs = 300                                     # 骨料个数
RamNode = np.zeros((Numaggs, TotalNumNodes, 4))   # spherical coordinates, 记录球坐标到 RamNode 数组里，numpy的矩阵里第一个是页，第二个是行，第三个是列
RamNodeDK = np.zeros((Numaggs, TotalNumNodes, 4)) # 记录笛卡尔坐标到 RamNodeDK 数组里
cellvolume = np.zeros((Numaggs, 1))               # 记录每个骨料的体积
volumeCentroid = np.zeros((Numaggs, 4))           # 记录每个骨料的质心
AMaxlen = np.zeros((Numaggs, 1))                  # 记录每个骨料的空间最长距离
TMaxlenCoord = np.zeros((Numaggs, 2, 3))          # 记录每个骨料组成空间最长距离的两个点坐标
TMinlenCoord = np.zeros((Numaggs, 2, 3))          # 记录每个骨料组成空间最短距离的两个点坐标
TRect = np.zeros((Numaggs, 50, 3))                # 记录骨料的节点坐标
RamAggDatas = []                                  # 随机多面体骨料的数据
points = []                                       # 质心坐标集

AggRadius = np.zeros((1, Numaggs))                # 所有骨料的直径，mm
Dmax = 16                                         # 最大骨料直径，mm
Dmin = 2.36                                       # 最小骨料直径，mm

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
        distance = math.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)      # sqrt()是用于计算数字X的平方根的函数
        if distance < (r1 + r2):
            sign = False
            break
    return sign


for ik in range(Numaggs):    # random.rand()随机生成(0,1)的浮点数
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
    setrzero = 1                                     # 沿径向是否波动的调节系数，不波动为0,波动为1
    setzero = 1                                      # 沿天顶角方向或方位角方向是否波动的调节系数，不波动为0,波动为1
    for j in range(Numlayers):
        theta = j * 45.0 / 180.0 * np.pi             # 天顶角---转化为弧度
        if abs(j - 0.0) <= 10e-10:                   # 确定层数，j=0，第一层
            for i in range(NumNodeslayer1st):
                fai = i * 45.0 / 180.0 * np.pi       # 方位角---转化为弧度
                RamNode[ik][j][0] = j + 1            # 从此行以下依次确定：节点编号、半径、天顶角、方位角
                RamNode[ik][j][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * random.rand())   # random.choice((-1, 1))随机生成(-1 或 1)
                RamNode[ik][j][2] = theta + setzero * avar * (-1 + 2 * random.rand())    # (-1 + 2 * random.rand())随机生成(-1,1)的浮点数
                RamNode[ik][j][3] = fai + setzero * (2 * np.pi) * (-1 + 2 * random.rand())
        elif abs(j - (Numlayers - 1.0)) <= 10e-10:   # j=4，第五层
            for i in range(NumNodeslayer5th):  # NumNodeslayer5th = 1，这层的节点数为1个
                fai = i * 45.0 / 180.0 * np.pi  # 第一层和第五层的方位角波动范围角为(2 * np.pi)
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][0] = (Numlayers - 2) * NumNodeslayer2nd + 2
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * random.rand())
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][2] = theta + setzero * avar * (-1 + 2 * random.rand())
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][3] = fai + setzero * (2 * np.pi) * (-1 + 2 * random.rand())
        else:                                  # j=[1, 2, 3]， 第二、三、四层
            for i in range(NumNodeslayer2nd):  # 在范围 NumNodeslayer2nd = 8 之内按序波动是因为二三四层的节点数都是8
                fai = i * 45.0 / 180.0 * np.pi
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][0] = i + (j - 1) * 8 + 2
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * random.rand())
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][2] = theta + setzero * avar * (-1 + 2 * random.rand())
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][3] = fai + setzero * avar * (-1 + 2 * random.rand())
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
    volumeCentroid[ik][0] = ik + 1                               # 多面体的体积、质心计算
    volumeCentroid[ik][1] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][0]
    volumeCentroid[ik][2] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][1]
    volumeCentroid[ik][3] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][2]
    cellvolume[ik][0] = mdb.models[Modelname].parts['Part-' + str(ik)].cells[0].getSize()     # 提取parts单个多面体部件体积
    # cellvolume[ik][0] = mdb.models[Modelname].rootAssembly.getMassProperties()['volume']      # 提取rootAssembly单个多面体实例体积
    vertices = mdb.models[Modelname].rootAssembly.instances['Part-' + str(ik)].vertices
    for i in range(len(vertices)):
        x = vertices[i].pointOn[0][0]            # pointOn---顶点坐标
        y = vertices[i].pointOn[0][1]
        z = vertices[i].pointOn[0][2]
        TRect[ik][i][:] = [x, y, z]              # 把提取的坐标保存在数组TRect里
    # except BaseException:
    #     del mdb.models[Modelname].parts['Part-' + str(ik)]
    #     continue

    TMaxlenMax = 0.0                             # 骨料空间最长距离计算
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
    Cumcellvolume = Cumcellvolume + cellvolume[ik][0]              # 提取所有多面体体积
    if (Cumcellvolume - TargetVol) >= 0.0:
        del mdb.models[Modelname].rootAssembly.features['Part-' + str(ik)]
        AggRadius[0][ik] = 0
        break

Numaggs = ik                                   # 累计生成的骨料个数
IndexAR = AggRadius[0].argsort()[::-1]         # ’AggRadius‘是单个骨料最大空间距离
# 下例四行是对排序的演示
# a = [3,7,9]
# a.sort(key=None,reverse=True)
# a = np.array([3,7,9])
# b = a.argsort()[::-1]

ik = 0
MaxIter = 100000                               # 最大的骨料投放迭代次数
for ii in range(MaxIter):
        if abs(len(RamAggDatas)-Numaggs) <= 10e-10:
            break
        x1 = 0+ AMaxlen[IndexAR[ik]][0] + random.rand()*(ConcLength- 2*AMaxlen[IndexAR[ik]][0])      # 质心的x坐标，mm
        y1 = 0+ AMaxlen[IndexAR[ik]][0] + random.rand()*(ConcWidth- 2*AMaxlen[IndexAR[ik]][0])        # 质心的y坐标，mm
        z1 = 0+ AMaxlen[IndexAR[ik]][0] + random.rand()*(ConcHeight- 2*AMaxlen[IndexAR[ik]][0])       # 质心的z坐标，mm
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



b = RamAggDatas
for ik in range(len(RamAggDatas)):             # 对多面体的质心坐标进行平移
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(b[ik][1], 0.0, 0.0))
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(0.0, b[ik][2], 0.0))
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(0.0, 0.0, b[ik][3]))

# 生成混凝土基体轮廓的命令
xmin = 0
xmax = ConcLength
ymin = 0
ymax = ConcWidth
zmin = 0
zmax = ConcHeight
zlength = abs(zmax - zmin)

s = mdb.models[Modelname].ConstrainedSketch(name='__profile__',sheetSize=200.0)
s.rectangle(point1=(xmin, ymin),point2=(xmax, ymax))
p = mdb.models[Modelname].Part(name='basic', dimensionality=THREE_D, type=DEFORMABLE_BODY)
p.BaseSolidExtrude(sketch=s, depth=zlength)
del mdb.models[Modelname].sketches['__profile__']
mdb.models[Modelname].rootAssembly.Instance(name='basic',part=p,dependent=OFF)






