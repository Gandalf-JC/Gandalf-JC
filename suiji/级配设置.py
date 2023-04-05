from numpy import random
import numpy as np

# 根据级配来设置粒径

Numaggs = 10000                                      # 骨料个数
cellVolume = np.zeros((Numaggs, 1))                 # 单个骨料体积
TargetVol = np.zeros((5, 1))                        # 给定生成的目标骨料体积，mm³
CumcellVolume = 0.0                                 # 生成骨料的累计体积，mm³

m = 0
n = 0
for ik in range(Numaggs):
    VolumeCy = 785398                           # 圆柱体体积，mm³
    Diameter1 = np.random.uniform(13.2, 16.0)  # 0号粒径（13.2-16.0）mm
    Volume1 = 0.035                              # 0号粒径体积分数
    Diameter2 = np.random.uniform(9.5, 13.2)  # 1号粒径（9.5-13.2）mm
    Volume2 = 0.172                              # 1号粒径体积分数
    Diameter3 = np.random.uniform(5.5, 9.5)  # 2号粒径粒径（4.75-9.5）mm
    Volume3 = 0.030                              # 2号粒径体积分数
    Diameter4 = np.random.uniform(3.50, 5.0)  # 3号粒径粒径（2.36-4.75）mm
    Volume4 = 0.002                             # 3号粒径体积分数
    Diameter5 = np.random.uniform(2.0, 3.0)  # 4号粒径粒径（1.18-2.36）mm
    Volume5 = 0.0002                            # 4号粒径体积分数
    Diameter = [Diameter1, Diameter2, Diameter3, Diameter4,Diameter5]
    AggRatio = [Volume1, Volume1 + Volume2, Volume1 + Volume2 + Volume3,
                Volume1 + Volume2 + Volume3 + Volume4, Volume1 + Volume2 + Volume3 + Volume4 + Volume5]

    r0 = Diameter[n]/2
    cellVolume[ik][0] = pow(r0, 3) * np.pi * 4 / 3 * 0.7 # 第k个骨料体积
    CumcellVolume = CumcellVolume + cellVolume[ik][0]  # 累计体积
    TargetVol[m][0] = VolumeCy * AggRatio[m]
    if m < 10e-10 and CumcellVolume - TargetVol[0][0] > 0:
        print('第', n, '号粒径：', Diameter[n], '  第', ik, '个骨料体积：', cellVolume[ik][0],
              '第', m, '目标体积：', TargetVol[m][0], '  累计体积：', CumcellVolume)
        m += 1
        n += 1
    elif m > 10e-10 and m < 1+10e-10 and CumcellVolume - TargetVol[1][0] > 0:
        print('第', n, '号粒径：', Diameter[n], '  第', ik, '个骨料体积：', cellVolume[ik][0],
              '第', m, '目标体积：', TargetVol[m][0], '  累计体积：', CumcellVolume)
        m += 1
        n += 1
    elif m > 1+10e-10 and m < 2+10e-10 and CumcellVolume - TargetVol[2][0] > 0:
        print('第', n, '号粒径：', Diameter[n], '  第', ik, '个骨料体积：', cellVolume[ik][0],
              '第', m, '目标体积：', TargetVol[m][0], '  累计体积：', CumcellVolume)
        m += 1
        n += 1
    elif m > 2+10e-10 and m < 3+10e-10 and CumcellVolume - TargetVol[3][0] > 0:
        print('第', n, '号粒径：', Diameter[n], '  第', ik, '个骨料体积：', cellVolume[ik][0],
              '第', m, '目标体积：', TargetVol[m][0], '  累计体积：', CumcellVolume)
        m += 1
        n += 1
    elif m > 3 + 10e-10 and m < 4 + 10e-10 and CumcellVolume - TargetVol[4][0] > 0:
        print('第', n, '号粒径：', Diameter[n], '  第', ik, '个骨料体积：', cellVolume[ik][0],
              '第', m, '目标体积：', TargetVol[m][0], '  累计体积：', CumcellVolume)
        break





