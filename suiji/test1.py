from abaqus import *
from abaqusConstants import *
from driverUtils import executeOnCaeStartup

executeOnCaeStartup()
Mdb()

session.viewports['Viewport: 1'].setValues(displayedObject=None)
p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=THREE_D,
                               type=DEFORMABLE_BODY)
session.viewports['Viewport: 1'].setValues(displayedObject=p)

p.WirePolyLine(points=(((0.0, 0.0, 0.0), (5.0, 0.0, 0.0)), ((0.0, 5.0, 0.0), (
    0.0, 0.0, 0.0)), ((5.0, 0.0, 0.0), (0.0, 5.0, 0.0))), mergeWire=OFF,
               meshable=ON)
e = p.edges
edges = e.getSequenceFromMask(mask=('[#7 ]',), )
p.Set(edges=edges, name='Wire-1-Set-1')

p.WirePolyLine(points=(((0.0, 0.0, 0.0), (0.0, 0.0, 5.0)),), mergeWire=OFF,
               meshable=ON)

e = p.edges
edges = e.getSequenceFromMask(mask=('[#1 ]',), )
p.Set(edges=edges, name='Wire-2-Set-1')

v = p.vertices
p.WirePolyLine(points=((v[0], v[2]), (v[3], v[0])), mergeWire=OFF, meshable=ON)
p = mdb.models['Model-1'].parts['Part-1']
e = p.edges
edges = e.getSequenceFromMask(mask=('[#3 ]',), )
p.Set(edges=edges, name='Wire-3-Set-1')

e = p.edges
p.CoverEdges(edgeList=e[0:1] + e[3:5], tryAnalytical=True)

e1 = p.edges
p.CoverEdges(edgeList=e1[0:1] + e1[2:3] + e1[5:6], tryAnalytical=True)

e = p.edges
p.CoverEdges(edgeList=e[0:1] + e[3:4] + e[5:6], tryAnalytical=True)

e1 = p.edges
p.CoverEdges(edgeList=e1[0:1] + e1[3:4] + e1[5:6], tryAnalytical=True)

f = p.faces
p.AddCells(faceList=f[0:4])
session.viewports['Viewport: 1'].setValues(displayedObject=p)

# create in Abaqus
# myAssembly = mdb.models['Model-1'].rootAssembly
# for num in range(SphereNum):
#     x = SphereDatas[num][0]
#     y = SphereDatas[num][1]
#     z = SphereDatas[num][2]
#     SphereRadius2 = SphereNum[num][3]
#     myAssembly.Instance(name='Part-sphere-solid-{}'.format(num), part=myPart3, dependent=ON)
#     myAssembly.translate(instanceList=('Part-sphere-solid-{}'.format(num),), vector=(x, y, z))
#     myAssembly.rotate(instanceList=('Part-sphere-solid-{}'.format(num),), axisPoint=(x, y, z),
#                       axisDirection=(x, y + 1, z),
#                       angle=angle_y)
#     myAssembly.rotate(instanceList=('Part-sphere-solid-{}'.format(num),), axisPoint=(x, y, z),
#                       axisDirection=(x, y, z + 1),
#                       angle=angle_z)
#
# # 建立模型
# myModel = mdb.Model(name='sphere')
# b = np.loadtxt('coordinates.txt', delimiter=',', dtype=np.float32)
# print(b)
#
# for i in range(1):
#     mySketch = myModel.ConstrainedSketch(name='sphereProfile', sheetSize=0.2)
#     mySketch.ArcByCenterEnds(center=(b[i][1], b[i][2]), direction=CLOCKWISE, point1=(b[i][1], b[i][2] + b[i][4]),
#                              point2=(b[i][1], b[i][2] - b[i][4]))
#     mySketch.Line(point1=(b[i][1], b[i][2] + b[i][4]), point2=(b[i][1], b[i][2] - b[i][4]))
#     myConstructionLine = mySketch.ConstructionLine(point1=(b[i][1], b[i][2] + b[i][4]),
#                                                    point2=(b[i][1], b[i][2] - b[i][4]))
#     myBeam = myModel.Part(name='sphere' + str(i), dimensionality=THREE_D, type=DEFORMABLE_BODY)
#     myPart = myBeam.BaseSolidRevolve(angle=360.0, flipRevolveDirection=OFF, sketch=mySketch)
#     myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
#     myModel.rootAssembly.Instance(dependent=ON, name='sphere' + str(i), part=myBeam)
#     myModel.rootAssembly.translate(instanceList=('sphere' + str(i),), vector=(0.0, 0.0, b[i][3]))
#     del myBeam
#     del myConstructionLine
#     del myPart
#     del mySketch
#
# # 生成球的第一种命令流，旋转
# s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=0.2)
# s1.ConstructionLine(point1=(0.0, -0.1), point2=(0.0, 0.1))
# s1.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, 0.015), point2=(0.0, -0.015), direction=CLOCKWISE)
# s1.Line(point1=(0.0, 0.015), point2=(0.0, -0.015))
# p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=THREE_D, type=DEFORMABLE_BODY)
# p.BaseSolidRevolve(sketch=s1, angle=360.0, flipRevolveDirection=OFF)
#
# # 生成球的第二种命令流，扫掠
#
# s1 = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=200.0)
# g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
# s1.setPrimaryObject(option=STANDALONE)
# s1.ConstructionLine(point1=(0.0, -100.0), point2=(0.0, 100.0))
# s1.FixedConstraint(entity=g[2])
# s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(15.0, 0.0))
# s1.CoincidentConstraint(entity1=v[0], entity2=g[2], addUndoState=False)
# s1.autoTrimCurve(curve1=g[3], point1=(-8.18963241577148, 13.578052520752))
# s1.Line(point1=(0.0, 15.0), point2=(0.0, -15.0))
# s1.VerticalConstraint(entity=g[6], addUndoState=False)
# s1.PerpendicularConstraint(entity1=g[4], entity2=g[6], addUndoState=False)
# p = mdb.models['Model-1'].Part(name='Part-1', dimensionality=THREE_D, type=DEFORMABLE_BODY)
# p.BaseSolidRevolve(sketch=s1, angle=360.0, flipRevolveDirection=OFF)

