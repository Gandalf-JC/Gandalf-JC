# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *
from caeModules import *
import os
import math
import numpy as np
from numpy import random
from visualization import *
from odbAccess import *

Mdb()
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)

Modelname = 'Model-1'
Partname = 'Part-1'
Instancename = 'Part-1-1'
Jobname = 'RanModel-1'
os.chdir(r"E:\Abaqus-test\Asphalt\AC-13C")

Cyradius = 50
CyHeight = 100.0
VolumeCy = np.pi * pow(Cyradius, 2) * CyHeight
AggRatio = 0.04
TargetVol = VolumeCy * AggRatio
CumcellVolume = 0.0

Numlayers = 5
NumNodeslayer1st = 1
NumNodeslayer2nd = 8
NumNodeslayer3rd = 8
NumNodeslayer4th = 8
NumNodeslayer5th = 1
TotalNumNodes = NumNodeslayer1st + NumNodeslayer2nd + NumNodeslayer3rd + NumNodeslayer4th + NumNodeslayer5th
FaceAndNodes = np.zeros((48, 13))
Numaggs = 1000
RamNode = np.zeros((Numaggs, TotalNumNodes, 4))
RamNodeDK = np.zeros((Numaggs, TotalNumNodes, 4))
cellVolume = np.zeros((Numaggs, 1))
volumeCentroid = np.zeros((Numaggs, 4))
AggRadius = np.zeros((1, Numaggs))
AMaxlen = np.zeros((Numaggs, 1))
TMaxlenCoord = np.zeros((Numaggs, 2, 3))
TMinlenCoord = np.zeros((Numaggs, 2, 3))
TRect = np.zeros((Numaggs, 50, 3))
RamAggDatas = []
points = []

Dmax = 16.0
Dmin = 13.2

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
        distance = math.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
        if distance < 1.2*(r1 + r2):
            sign = False
            break
    return sign

s = mdb.models[Modelname].ConstrainedSketch(name='__profile__', sheetSize=200.0)
s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(Cyradius, 0.0))
p = mdb.models[Modelname].Part(name='basic', dimensionality=THREE_D, type=DEFORMABLE_BODY)
p.BaseSolidExtrude(sketch=s, depth=CyHeight)
del mdb.models[Modelname].sketches['__profile__']
mdb.models[Modelname].rootAssembly.Instance(name='basic',part=p,dependent=OFF)

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
session.viewports['Viewport: 1'].assemblyDisplay.geometryOptions.setValues(datumAxes=OFF)

for ik in range(Numaggs):
    r0 = pow(((random.rand() * (pow(Dmax, 0.5) - pow(Dmin, 0.5))) + pow(Dmin, 0.5)), 2) / 2
    AggRadius[0][ik] = r0 * 2.0
    ifflag = 0
    SizeLength = 200
    s = mdb.models[Modelname].ConstrainedSketch(name='_profile_', sheetSize=1.0)
    s.rectangle(point1=(-SizeLength / 2, SizeLength / 2),point2=(SizeLength / 2, -SizeLength / 2))
    p = mdb.models[Modelname].Part(name='Part-' + str(ik), dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(depth=SizeLength / 2,sketch=s)
    session.viewports['Viewport: 1'].setValues(displayedObject=p)
    del mdb.models[Modelname].sketches['_profile_']
    del mdb.models[Modelname].parts['Part-' + str(ik)].features['Solid extrude-1']
    rvar = 0.2
    avar = 12.0/180.0 * np.pi
    bvar = 18.0 / 180.0 * np.pi
    setrzero = 1
    setzero = 1
    for j in range(Numlayers):
        theta = j * 45.0 / 180.0 * np.pi
        if abs(j - 0.0) <= 10e-10:
            for i in range(NumNodeslayer1st):
                fai = i * 45.0 / 180.0 * np.pi
                RamNode[ik][j][0] = j + 1
                RamNode[ik][j][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * np.random.rand())
                RamNode[ik][j][2] = theta + setzero * bvar * (-1 + 2 * np.random.rand())
                RamNode[ik][j][3] = fai + setzero * (2 * np.pi) * (-1 + 2 * np.random.rand())
        elif abs(j - (Numlayers - 1.0)) <= 10e-10:
            for i in range(NumNodeslayer5th):
                fai = i * 45.0 / 180.0 * np.pi
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][0] = (Numlayers - 2) * NumNodeslayer2nd + 2
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * np.random.rand())
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][2] = theta + setzero * bvar * (-1 + 2 * np.random.rand())
                RamNode[ik][(Numlayers - 2) * NumNodeslayer2nd + 1][3] = fai + setzero * (2 * np.pi) * (-1 + 2 * np.random.rand())
        else:
            for i in range(NumNodeslayer2nd):
                fai = i * 45.0 / 180.0 * np.pi
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][0] = i + (j - 1) * 8 + 2
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][1] = r0 + setrzero * r0 * rvar * (-1 + 2 * np.random.rand())
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][2] = theta + setzero * avar * (-1 + 2 * np.random.rand())
                RamNode[ik][i + (j - 1) * NumNodeslayer2nd + 1][3] = fai + setzero * avar * (-1 + 2 * np.random.rand())
    for i in range(TotalNumNodes):
        RamNodeDK[ik][i][0] = RamNode[ik][i][0]
        RamNodeDK[ik][i][1] = RamNode[ik][i][1] * np.sin(RamNode[ik][i][2]) * np.cos(RamNode[ik][i][3])
        RamNodeDK[ik][i][2] = RamNode[ik][i][1] * np.sin(RamNode[ik][i][2]) * np.sin(RamNode[ik][i][3])
        RamNodeDK[ik][i][3] = RamNode[ik][i][1] * np.cos(RamNode[ik][i][2])
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
    for j in range(Numlayers):
        if abs(j - 0.0) <= 10e-10:
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
                p.WirePolyLine(mergeType=IMPRINT, meshable=ON,points=((b1, b2), (b2, b3), (b3, b1)))
        elif abs(j - (Numlayers - 1.0)) <= 10e-10:
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
                if abs(i - (NumNodeslayer2nd - 1)) <= 10e-10:  # i=7
                    a2[0] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][1]
                    a2[1] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][2]
                    a2[2] = RamNodeDK[ik][NumNodeslayer2nd * (j - 2) + 1 + i][3]
                    b2 = tuple(a2)
                    a3[0] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd +NumNodeslayer3rd][1]
                    a3[1] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd +NumNodeslayer3rd][2]
                    a3[2] = RamNodeDK[ik][NumNodeslayer1st + NumNodeslayer2nd +NumNodeslayer3rd][3]
                    b3 = tuple(a3)
                p.WirePolyLine(mergeType=IMPRINT, meshable=ON, points=((b1, b2), (b2, b3), (b3, b1)))
        elif abs(j - 3) >= 10e-10:
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
                p.WirePolyLine(mergeType=IMPRINT,meshable=ON,points=((b1, b2), (b2, b3), (b3, b1)))
    for j in range(Numlayers):
        if abs(j - 0.0) <= 10e-10:
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
        elif abs(j - (Numlayers - 1.0)) <= 10e-10:
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
        elif abs(j - 3) >= 10e-10:
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
                p.CoverEdges(edgeList=(
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
                ifflag += 1
    facesslist = []
    for ii in range(int(FaceAndNodes.shape[0])):
        facesslist.append( mdb.models[Modelname].parts['Part-' + str(ik)].faces.findAt((FaceAndNodes[ii][10], FaceAndNodes[ii][11], FaceAndNodes[ii][12]),) )
    p.AddCells(faceList=facesslist,flipped=True)
    mdb.models[Modelname].rootAssembly.Instance(dependent=OFF, name='Part-' + str(ik),
        part=mdb.models[Modelname].parts['Part-' + str(ik)])
    volumeCentroid[ik][0] = ik + 1
    volumeCentroid[ik][1] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][0]
    volumeCentroid[ik][2] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][1]
    volumeCentroid[ik][3] = mdb.models[Modelname].rootAssembly.getMassProperties()['volumeCentroid'][2]
    cellVolume[ik][0] = mdb.models[Modelname].parts['Part-' + str(ik)].cells[0].getSize()
    vertices = mdb.models[Modelname].rootAssembly.instances['Part-' + str(ik)].vertices
    for i in range(len(vertices)):
        x = vertices[i].pointOn[0][0]
        y = vertices[i].pointOn[0][1]
        z = vertices[i].pointOn[0][2]
        TRect[ik][i][:] = [x, y, z]

    TMaxlenMax = 0.0
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

Numaggs = ik+1
IndexAR = AggRadius[0].argsort()[::-1]

ik = 0
MaxIter = 100000000
for ii in range(MaxIter):
    if abs(len(RamAggDatas)-Numaggs) <= 10e-10:
        break
    x1 = random.uniform(-(Cyradius- 1.01*AMaxlen[IndexAR[ik]][0]), (Cyradius- 1.01*AMaxlen[IndexAR[ik]][0]))
    y1 = random.uniform(-(Cyradius- 1.01*AMaxlen[IndexAR[ik]][0]), (Cyradius- 1.01*AMaxlen[IndexAR[ik]][0]))
    z1 = random.uniform(AMaxlen[IndexAR[ik]][0]/2, CyHeight- AMaxlen[IndexAR[ik]][0]/2)
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
for ik in range(len(RamAggDatas)):
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(b[ik][1], 0.0, 0.0))
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(0.0, b[ik][2], 0.0))
    mdb.models[Modelname].rootAssembly.translate(instanceList=('Part-' + str(IndexAR[ik]),), vector=(0.0, 0.0, b[ik][3]))

Partinstances = mdb.models[Modelname].rootAssembly.instances['Part-' + str(0)].cells[0:0]
for i in range(len(RamAggDatas)):
    Partinstances = Partinstances + mdb.models[Modelname].rootAssembly.instances['Part-' + str(i)].cells

mdb.models[Modelname].rootAssembly.Set(cells=Partinstances, name='Partinstances')

mdb.models[Modelname].Material(name='aggregate')
mdb.models[Modelname].materials['aggregate'].Density(table=((2.7e-9,),))
mdb.models[Modelname].materials['aggregate'].Elastic(table=((5.0e4, 0.20),))
mdb.models[Modelname].HomogeneousSolidSection(material='aggregate', name='Section-1',thickness=None)
mdb.models[Modelname].Material(name='asphalt-mortar')
mdb.models[Modelname].materials['asphalt-mortar'].Density(table=((2.35e-9,),))
mdb.models[Modelname].materials['asphalt-mortar'].Elastic(table=((50.0, 0.30),))
mdb.models[Modelname].HomogeneousSolidSection(material='asphalt-mortar', name='Section-2',thickness=None)

for i in range(Numaggs):
    mdb.models[Modelname].parts['Part-'+str(i)].Set(cells=mdb.models[Modelname].parts['Part-'+str(i)].cells, name='Part-'+str(i))
    mdb.models[Modelname].parts['Part-' + str(i)].SectionAssignment(region=
        mdb.models[Modelname].parts['Part-' + str(i)].sets['Part-' + str(i)], sectionName='Section-1', offset=0.0, offsetType=
        MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

mdb.models[Modelname].parts['basic'].Set(cells=mdb.models[Modelname].parts['basic'].cells, name='basic')
mdb.models[Modelname].parts['basic'].SectionAssignment(region=
    mdb.models[Modelname].parts['basic'].sets['basic'], sectionName='Section-2', offset=0.0, offsetType=
    MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

Cumupart = []
a = mdb.models['Model-1'].rootAssembly
for i in range(len(RamAggDatas)):
    Cumupart.append(a.instances['Part-' + str(i)])

Cumupart=tuple(Cumupart)
mdb.models[Modelname].rootAssembly.InstanceFromBooleanCut(name='Part-mortar',
    instanceToBeCut=a.instances['basic'],
    cuttingInstances=Cumupart,
    originalInstances=SUPPRESS)

for i in range(len(RamAggDatas)):
    mdb.models[Modelname].rootAssembly.features['Part-' + str(i)].resume()

a = mdb.models['Model-1'].rootAssembly
a.makeIndependent(instances=(a.instances['Part-mortar-1'], ))


