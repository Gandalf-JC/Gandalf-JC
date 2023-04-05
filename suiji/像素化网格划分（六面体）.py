# 筛选砂浆单元并建集
from abaqus import *
from abaqusConstants import *
import numpy as np

model = mdb.models["Model-1"]
partGear = model.parts["Part-mortar"]
partBase = model.parts["basic"]

elements = partBase.elements
nodes = partBase.nodes
labels = []
cells = partGear.cells

for element in elements:
    nodeIndex = element.connectivity
    center = np.array([0.0, 0.0, 0.0])
    for index in nodeIndex:
        center += nodes[index].coordinates
    center /= 8
    findCell = cells.findAt((center,),printWarning=False)
    if len(findCell):
        labels.append(element.label)

partBase.Set(elements=elements.sequenceFromLabels(labels=labels), name="Part-mortar")



# 详细版
#前处理无脑导入一下包就完事了
from abaqus import *
from abaqusConstants import *
#我需要用到numpy,拿过来用一下
import numpy as np

#定义一下model
model = mdb.models["Model-1"]
#partGear就是参考的钻头几何模型
#partBase就是几何
partGear = model.parts["Part-1"]
partBase = model.parts["Part-2"]

#存一下变量
elements = partBase.elements
nodes = partBase.nodes

#labels数组存一下在钻头内部的单元编号
labels = []
cells = partGear.cells

#这个循环，就是核心部分了
#遍历每个element
for element in elements:
    #connectivity存的是组成该单元的节点索引值，
    #注意是索引值，不是单元编号
    nodeIndex = element.connectivity
    center = np.array([0.0, 0.0, 0.0])
    #这里的循环，是把单元的8个节点坐标加起来在除8，
    #就可以计算出单元中心点坐标了
    for index in nodeIndex:
        center += nodes[index].coordinates
    center /= 8
    #这一步是未了判断单元中心点是否在参考几何的内部，
    #利用的是findAt()函数，这个函数的所有使用方法，
    #可以在abaqus帮助文档查到
    #如果findAt()找到了，会返回一个cell序列值，如果没找到，就返回一个空值
    findCell = cells.findAt((center,),printWarning=False)
    #所以，就可以下定义了，如果findCell不是空的，就表明这个单元点
    #在几何内部，把单元编号存起来
    if len(findCell):
        labels.append(element.label)

#这里主要是把内部单元存在一个set里，当然，也可以选择删除其他的单元，
#只需要最后这里改改就好了
#大家可以学学用用sequenceFromLabels()，根据单元编号找单元的序列
#这个函数非常好用，会经常用到，记住它
partBase.Set(elements=elements.sequenceFromLabels(labels=labels), name="Set-Test")
