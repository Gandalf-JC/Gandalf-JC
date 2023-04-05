# -*- coding: utf-8 -*-
"""三维随机球型骨料建模-圆柱体基体-cylinder basic"""

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

myModel = mdb.models['Model-1']
os.chdir(r"E:\abaqus-bilibili\1.1 example-cylinder")        # 设置工作目录
session.viewports['Viewport: 1'].assemblyDisplay.geometryOptions.setValues(datumAxes=OFF)   # 隐藏构造线（基准轴）

# 根据级配来设置粒径
sadc = np.random.uniform(9.5,13.2)  # a号粒径（2.36-4.75）mm
savol = 0.0179                        # a号粒径体积分数
sbdc = np.random.uniform(9.5,13.2)   # b号粒径（4.75-9.5）mm
sbvol = 0.0189                        # b号粒径体积分数
scdc = np.random.uniform(13.2,16.0)   # c号粒径粒径（9.5-13.2）mm
scvol = 0.053                        # c号粒径体积分数
vBa = np.pi * 50**2 * 150.0          # 基体体积


def basic():  # 定义part:basic
    s1 = myModel.ConstrainedSketch(name='__profile__', sheetSize=200.0)
    s1.setPrimaryObject(option=STANDALONE)
    s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(50.0, 0.0))
    p = mdb.models['Model-1'].Part(name='basic', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=s1, depth=150.0)
    del myModel.sketches['__profile__']


def qiu(na, a, n):  # 定义parts：sa + str(n), sb + str(n), sc + str(n)
    nq = na + str(n)
    s1 = myModel.ConstrainedSketch(name='__profile__', sheetSize=200.0)
    s1.ConstructionLine(point1=(0.0, -100.0), point2=(0.0, 100.0))
    s1.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, a / 2), point2=(0.0, -a / 2), direction=CLOCKWISE)
    s1.Line(point1=(0.0, a / 2), point2=(0.0, -a / 2))
    p = myModel.Part(name=nq, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidRevolve(sketch=s1, angle=360.0, flipRevolveDirection=OFF)
    del myModel.sketches['__profile__']


def baamss():  # 装配里生成instance：basic
    a1 = myModel.rootAssembly
    p = myModel.parts['basic']
    a1.Instance(name='basic-1', part=p, dependent=OFF)


def qiuamss(na, a):  # 装配里生成实例instances：sa-i,sb-i,sc-i
    a1 = myModel.rootAssembly
    i = 1
    while i < a + 1:
        p = myModel.parts[na + str(i)]
        a1.Instance(name=na + '-' + str(i), part=p, dependent=OFF)
        i = i + 1


def translateqiu(a, b, c, na, nb, nc):  # 装配随机生成的instances
    tempsc = [(np.random.uniform(-(50 - scdc), 50 - scdc),
               np.random.uniform(-(50 - scdc), 50 - scdc),
               np.random.uniform(scdc / 2, 150 - scdc))]
    a1 = myModel.rootAssembly
    a1.translate(instanceList=(nc + '-1',), vector=(tempsc[0][0], tempsc[0][1], tempsc[0][2]))

    # 粒径（13.2-16.0）mm填充
    n = 2
    while n < c + 1:
        x = np.random.uniform(-(50 - scdc), 50 - scdc)
        y = np.random.uniform(-(50 - scdc), 50 - scdc)
        z = np.random.uniform(scdc / 2, 150 - scdc)
        xy = (x ** 2 + y ** 2) ** 0.5
        i = 0
        while i < len(tempsc):
            if xy < 50 - scdc:
                if (x - tempsc[i][0]) ** 2 + (y - tempsc[i][1]) ** 2 + (z - tempsc[i][2]) ** 2 >= scdc ** 2:
                    i = i + 1
                    if i == len(tempsc):
                        a1 = myModel.rootAssembly
                        a1.translate(instanceList=(nc + '-' + str(n),), vector=(x, y, z))
                        n = n + 1
                        tempsc.append((x, y, z))
                else:
                    break
            else:
                break

    # 粒径（9.5-13.2）mm填充
    n = 1
    tempsb = []
    while n < b + 1:
        x = np.random.uniform(-(50 - sbdc), 50 - sbdc)
        y = np.random.uniform(-(50 - sbdc), 50 - sbdc)
        z = np.random.uniform(sbdc / 2, 150 - sbdc)
        xy = (x ** 2 + y ** 2) ** 0.5
        i = 0
        while i < len(tempsc):
            if xy < 50 - sbdc:
                if (x - tempsc[i][0]) ** 2 + (y - tempsc[i][1]) ** 2 + (z - tempsc[i][2]) ** 2 >= (
                        scdc / 2 + sbdc / 2) ** 2:
                    i = i + 1
                    if i == len(tempsc):
                        if len(tempsb) == 0:
                            a1 = myModel.rootAssembly
                            a1.translate(instanceList=(nb + '-' + str(n),), vector=(x, y, z))
                            tempsb.append((x, y, z))
                            n = n + 1
                        else:
                            for g in tempsb:
                                if (x - g[0]) ** 2 + (y - g[1]) ** 2 + (z - g[2]) ** 2 >= (sbdc / 2) ** 2:
                                    if g[0] == tempsb[-1][0] and g[1] == tempsb[-1][1] and g[2] == tempsb[-1][2]:
                                        a1 = myModel.rootAssembly
                                        a1.translate(instanceList=(nb + '-' + str(n),), vector=(x, y, z))
                                        tempsb.append((x, y, z))
                                        n = n + 1
                                else:
                                    break
                else:
                    break
            else:
                break

    # 粒径（4.75-9.5）mm填充
    n = 1
    tempsa = []
    while n < a + 1:
        x = np.random.uniform(-(50 - sadc), 50 - sadc)
        y = np.random.uniform(-(50 - sadc), 50 - sadc)
        z = np.random.uniform(sadc / 2, 150 - sadc)
        xy = (x ** 2 + y ** 2) ** 0.5
        bol = 0
        ist = 0
        while ist < len(tempsc):
            if xy < 50 - sadc:
                if (x - tempsc[ist][0]) ** 2 + (y - tempsc[ist][1]) ** 2 + (z - tempsc[ist][2]) ** 2 >= (
                        scdc / 2 + sadc / 2) ** 2:
                    ist = ist + 1
                    if ist == len(tempsc):
                        bol = 1
                else:
                    break
            else:
                break
            if bol == 1:
                isz = 0
                while isz < len(tempsb):
                    if (x - tempsb[isz][0]) ** 2 + (y - tempsb[isz][1]) ** 2 + (z - tempsb[isz][2]) ** 2 >= (
                            sbdc / 2 + sadc / 2) ** 2:
                        isz = isz + 1
                        if isz == len(tempsb):
                            if len(tempsa) == 0:
                                a1 = myModel.rootAssembly
                                a1.translate(instanceList=(na + '-' + str(n),), vector=(x, y, z))
                                tempsa.append((x, y, z))
                                n = n + 1
                            else:
                                for h in tempsa:
                                    if (x - h[0]) ** 2 + (y - h[1]) ** 2 + (z - h[2]) ** 2 >= (sadc / 2) ** 2:
                                        if h[0] == tempsa[-1][0] and h[1] == tempsa[-1][1] and h[2] == tempsa[-1][2]:
                                            a1 = myModel.rootAssembly
                                            a1.translate(instanceList=(na + '-' + str(n),), vector=(x, y, z))
                                            tempsa.append((x, y, z))
                                            n = n + 1
                                    else:
                                        break
                    else:
                        break
            bol = 0


basic()
i1 = 1
nusa = (vBa * savol) / ((4.0 / 3.0) * math.pi * (sadc / 2) ** 3)
while i1 < nusa + 1:
    qiu('sa', sadc, i1)
    i1 = i1 + 1
i2 = 1
nusb = (vBa * sbvol) / ((4.0 / 3.0) * math.pi * (sbdc / 2) ** 3)
while i2 < nusb + 1:
    qiu('sb', sbdc, i2)
    i2 = i2 + 1
i3 = 1
nusc = (vBa * scvol) / ((4.0 / 3.0) * math.pi * (scdc / 2) ** 3)
while i3 < nusc + 1:
    qiu('sc', scdc, i3)
    i3 = i3 + 1
baamss()
qiuamss('sa', nusa)
qiuamss('sb', nusb)
qiuamss('sc', nusc)

translateqiu(nusa, nusb, nusc, 'sa', 'sb', 'sc')

# part布尔，对同一类型和粒径的骨料进行合并


# 定义材料，创建截面，指派截面：basic,st,sz,sn

