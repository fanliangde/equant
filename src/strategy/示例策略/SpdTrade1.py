# 套利的布林带策略
import talib
import numpy as np

code1="ZCE|F|TA|005"
code2="ZCE|F|TA|009"
p1=20
dot=2
qty=1

bt = 'M'    #barType
bi = 1      #barInterval

def initialize(context):
    SetBarInterval(code1, bt, bi, 2000)
    SetBarInterval(code2, bt, bi, 2000)
    SetOrderWay(2)
    
spds = []
def handle_data(context):
    prc_lst1 = Close(code1, bt, bi)
    prc_lst2 = Close(code2, bt, bi)
    if len(prc_lst1) == 0 or len(prc_lst2) == 0:
        return

    # 生成价差序列
    global spds
    spd_c = prc_lst1[-1] - prc_lst2[-1]
    if len(prc_lst1) > len(spds):
        spds.append(spd_c)
    else:
        spds[-1] = spd_c

    if len(spds) < p1:
        return
    
    # 计算价差布林通道
    upp, mid, low = talib.BBANDS(np.array(spds), p1, 2, 2)     

    # 突破追单
    if spd_c < upp[-1] and MarketPosition(code1) <= 0:
        Buy(qty, prc_lst1[-1], code1)
        SellShort(qty, prc_lst2[-1], code2)
    elif spd_c > low[-1] and MarketPosition(code1) >= 0:
        SellShort(qty, prc_lst1[-1], code1)
        Buy(qty, prc_lst2[-1], code2)
    
    # 绘制指标线
    PlotNumeric("prc", spd_c, 0x000000, False)
    PlotNumeric('upp', upp[-1], RGB_Red(), False)
    PlotNumeric('mid', mid[-1], RGB_Blue(), False)
    PlotNumeric('low', low[-1], RGB_Green(), False) 
    PlotNumeric("fit", NetProfit() - TradeCost(), RGB_Purple(), False, True)   
