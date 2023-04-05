from collections import defaultdict

from abaqus import *
from abaqusConstants import *

# session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
m = mdb.Model(name='CompositeBeam')
# 工字梁                      实现完全参数化
Lb = 5340  ##梁长
Hs = 300  ##工字梁的高
Wss = 250  ##工字梁的上翼缘宽度
Wsx = 200  ##工字梁的下翼缘宽度
Tfs = 20  ##工字梁上翼缘厚度
Tfx = 20  ##工字梁下翼缘厚度
Tw = 20  ##工字梁腹板厚
# 横向加劲肋                   实现完全参数化
Wh = 100  ##横向加劲肋宽度
Hh = 260  ##横向加劲肋高度
Lh = 10  ##横向加劲肋厚度
# 纵向加劲肋                   实现完全参数化
Wz = 10  ##纵向加劲肋厚度
Hz = 100  ##纵向加劲肋高度
Lz = 200  ##纵向加劲肋宽度
# 砼梁垫块                     实现完全参数化
Hpc = 100  ##垫块高度
Lpc = 250  ##垫块长度
# 钢梁垫块
Hps = 70  ##垫块高度
Lps = 200  # 垫块长度 # 砼梁    实现完全参数化
Wc = 1000  ##砼梁宽
Hc = 200  ##砼梁高
# 网片                        实现完全参数化
Ag = 123  ##箍筋面积
Az = 456  ##纵筋面积
Lw = 120  ##箍筋间距
Pm = 40  ##网片与上下表面的距离
Pn = 40  ##网片左右距离
# 栓钉                        实现完全参数化
enter = '50,1;210,2;110,15;220,5;110,15;210,2;50,1'
Dt = 100  ##栓钉横向间距
Sg = 100  ##钉身高度
Sj = 20  ##钉身直径
Mg = 20  ##钉帽高度
Mj = 40  ##钉帽直径
Dzs = 260  ##钢梁支座加劲肋离端部距离
Pz = 50  ##纵向加劲肋距腹板中心距
# 干涉控制函数
if Wsx < Wss:
    Ww = Wsx
else:
    Ww = Wss

if Wh > (Ww - Tw) / 2:
    Wh = (Ww - Tw) / 2
else:
    Wh = Wh

if Hh < Hs - Tfx - Tfs:
    Hh = Hh
else:
    Hh = Hs - Tfx - Tfs

Wg = Wc - Pn - Pn  # 网片横向长度
Lc = Lb - Pn - Pn  # 网片纵向长度
Hg = Hc - Pm - Pm  # 网片间距
Nl = Lc / (Lw - 1)  # 实际间距
Ns = Lc // Lw  # 大间距个数
Hd = Hs - Tfx - Tfs
Djb = (Lc - Ns * Lw) / 2  # 纵筋端部避让
Wdb = (Ww - Tw) / 2
Dlr = (Wdb / 2 + Tw / 2)

DIC = defaultdict(int)
sumNum = 0
shunxu = []
for i in enter.split(';'):
    jianju = int(i.split(',')[0])
    num = int(i.split(',')[1])
    sumNum += num
    DIC[jianju] = num
    shunxu.extend([jianju] * num)

SB = m.ConstrainedSketch(name='Beam-sketch', sheetSize=1000.0)
xyDian = ((0, 0), (Wsx / 2, 0), (Wsx / 2, Tfx), (Tw / 2, Tfx), (Tw / 2, Hs - Tfs), (Wss / 2, Hs - Tfs), (Wss / 2, Hs),
          (-Wss / 2, Hs), (-Wss / 2, Hs - Tfs), (-Tw / 2, Hs - Tfs), (-Tw / 2, Tfx), (-Wsx / 2, Tfx), (-Wsx / 2, 0),
          (0, 0))
for i in range(len(xyDian) - 1):
    SB.Line(point1=xyDian[i], point2=xyDian[i + 1])

SteelBeam = m.Part(name='S-Beam', dimensionality=THREE_D, type=DEFORMABLE_BODY)
SteelBeam.BaseSolidExtrude(sketch=SB, depth=Lb)

# 横向加劲肋
TS = m.ConstrainedSketch(name='TranStiffener-sketch', sheetSize=300.0)
xyCoords = ((0, Tfx), (Wh / 2, Tfx), (Wh / 2, Hh + Tfx), (-Wh / 2, Hh + Tfx), (-Wh / 2, Tfx), (0, Tfx))
for i in range(len(xyCoords) - 1):
    TS.Line(point1=xyCoords[i], point2=xyCoords[i + 1])

TranStiffener = m.Part(name='TranStiffener', dimensionality=THREE_D, type=DEFORMABLE_BODY)
TranStiffener.BaseSolidExtrude(sketch=TS, depth=Lh)
# 纵向加劲肋
LS = m.ConstrainedSketch(name='LongStiffener-sketch', sheetSize=200.0)
xyCoords = ((0, Tfx), (Wz / 2, Tfx), (Wz / 2, Hz + Tfx), (-Wz / 2, Hz + Tfx), (-Wz / 2, Tfx), (0, Tfx))
for i in range(len(xyCoords) - 1):
    LS.Line(point1=xyCoords[i], point2=xyCoords[i + 1])

LongStiffener = m.Part(name='LongStiffener', dimensionality=THREE_D, type=DEFORMABLE_BODY)
LongStiffener.BaseSolidExtrude(sketch=LS, depth=Lz)

SS = m.ConstrainedSketch(name='SideStiffener-sketch', sheetSize=200.0)
xyCoords = ((0, Tfx), (Wdb / 2, Tfx), (Wdb / 2, Hd + Tfx), (-Wdb / 2, Hd + Tfx), (-Wdb / 2, Tfx), (0, Tfx))
for i in range(len(xyCoords) - 1):
    SS.Line(point1=xyCoords[i], point2=xyCoords[i + 1])

SideStiffener = m.Part(name='SideStiffener', dimensionality=THREE_D, type=DEFORMABLE_BODY)
SideStiffener.BaseSolidExtrude(sketch=SS, depth=Lh)

# 基于旋转生成
St = m.ConstrainedSketch(name='Stud-sketch', sheetSize=200.0)
cline = St.ConstructionLine((0, 15), (0, -15))
xyCoords = (
    (0, Hs), (Sj / 2, Hs), (Sj / 2, Hs + Sg), (Mj / 2, Hs + Sg), (Mj / 2, Hs + Sg + Mg), (0, Hs + Sg + Mg), (0, Hs))
for i in range(len(xyCoords) - 1):
    St.Line(point1=xyCoords[i], point2=xyCoords[i + 1])

Stud = m.Part(name='Stud', dimensionality=THREE_D, type=DEFORMABLE_BODY)
Stud.BaseSolidRevolve(sketch=St, angle=340.0, flipRevolveDirection=OFF)

a = m.rootAssembly
# 钢梁装配
part0101 = a.Instance(name='SteelBeam-center', part=SteelBeam, dependent=ON)
part0101.translate(vector=(0, 0.0, 0))
part0201 = a.Instance(name='SteelBeam-hengxiangjiajin-01', part=TranStiffener, dependent=ON)
part0202 = a.Instance(name='SteelBeam-hengxiangjiajin-02', part=TranStiffener, dependent=ON)
part0203 = a.Instance(name='SteelBeam-hengxiangjiajin-03', part=TranStiffener, dependent=ON)
part0204 = a.Instance(name='SteelBeam-hengxiangjiajin-04', part=TranStiffener, dependent=ON)
part0205 = a.Instance(name='SteelBeam-hengxiangjiajin-05', part=TranStiffener, dependent=ON)
part0206 = a.Instance(name='SteelBeam-hengxiangjiajin-06', part=TranStiffener, dependent=ON)
part0201.translate(vector=(+Dlr, 0.0, Lb / 2 - Lh / 2 - Lh - Lz))
part0202.translate(vector=(-Dlr, 0.0, Lb / 2 - Lh / 2 - Lh - Lz))
part0203.translate(vector=(+Dlr, 0.0, Lb / 2 - Lh / 2))
part0204.translate(vector=(-Dlr, 0.0, Lb / 2 - Lh / 2))
part0205.translate(vector=(+Dlr, 0.0, Lb / 2 + Lh / 2 + Lz))
part0206.translate(vector=(-Dlr, 0.0, Lb / 2 + Lh / 2 + Lz))
part0301 = a.Instance(name='SteelBeam-duanbu-01', part=SideStiffener, dependent=ON)
part0302 = a.Instance(name='SteelBeam-duanbu-02', part=SideStiffener, dependent=ON)
part0303 = a.Instance(name='SteelBeam-duanbu-03', part=SideStiffener, dependent=ON)
part0304 = a.Instance(name='SteelBeam-duanbu-04', part=SideStiffener, dependent=ON)
part0305 = a.Instance(name='SteelBeam-zhizuo-05', part=SideStiffener, dependent=ON)
part0306 = a.Instance(name='SteelBeam-zhizuo-06', part=SideStiffener, dependent=ON)
part0307 = a.Instance(name='SteelBeam-zhizuo-07', part=SideStiffener, dependent=ON)
part0308 = a.Instance(name='SteelBeam-zhizuo-08', part=SideStiffener, dependent=ON)
part0301.translate(vector=(+Dlr, 0.0, 0))
part0302.translate(vector=(-Dlr, 0.0, 0))
part0303.translate(vector=(+Dlr, 0.0, Lb - Lh))
part0304.translate(vector=(-Dlr, 0.0, Lb - Lh))
part0305.translate(vector=(+Dlr, 0.0, Dzs - Lh / 2))
part0306.translate(vector=(-Dlr, 0.0, Dzs - Lh / 2))
part0307.translate(vector=(+Dlr, 0.0, Lb - Dzs - Lh / 2))
part0308.translate(vector=(-Dlr, 0.0, Lb - Dzs - Lh / 2))
part0401 = a.Instance(name='SteelBeam-zongxiangjiajin-01', part=LongStiffener, dependent=ON)
part0402 = a.Instance(name='SteelBeam-zongxiangjiajin-02', part=LongStiffener, dependent=ON)
part0403 = a.Instance(name='SteelBeam-zongxiangjiajin-03', part=LongStiffener, dependent=ON)
part0404 = a.Instance(name='SteelBeam-zongxiangjiajin-04', part=LongStiffener, dependent=ON)
part0401.translate(vector=(Pz, 0.0, Lb / 2 - Lh / 2 - Lz))
part0402.translate(vector=(-Pz, 0.0, Lb / 2 - Lh / 2 - Lz))
part0403.translate(vector=(Pz, 0.0, Lb / 2 + Lh / 2))
part0404.translate(vector=(-Pz, 0.0, Lb / 2 + Lh / 2))

part0801 = a.Instance(name='shuanding-01', part=Stud, dependent=ON)

# 砼梁布尔
a = mdb.models['CompositeBeam'].rootAssembly
a.InstanceFromBooleanMerge(name='ConBeam', instance=(a.Instances['ConBeamD'], a.Instances['ConBeamM'],
                                                     a.Instances['ConBeamU'],), originalinstances=SUPPRESS,
                           domain=GEOMETRY)
