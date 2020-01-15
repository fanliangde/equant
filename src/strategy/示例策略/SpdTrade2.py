# 套利的双均线策略
import talib
import numpy as np

code1="ZCE|F|TA|005"
code2="ZCE|F|TA|009"

p1=5
p2=20
dot=1
qty=1

bt = 'M'    #barType
bi = 1      #barLength

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

    if len(spds) < p2:
        return

    # 计算价差ma
    sma1 = talib.MA(np.array(spds), p1)  
    sma2 = talib.MA(np.array(spds), p2)         

    # 根据两根ma的交叉关系下单
    if sma1[-1] > sma2[-1] + dot * PriceTick() and MarketPosition(code1) <= 0:
        Buy(qty, prc_lst1[-1], code1)
        SellShort(qty, prc_lst2[-1], code2)
    elif sma1[-1] < sma2[-1] - dot * PriceTick() and MarketPosition(code1) >= 0:
        SellShort(qty, prc_lst1[-1], code1)
        Buy(qty, prc_lst2[-1], code2)

    # 绘制指标线   
    PlotNumeric("sma1", sma1[-1], 0x0000FF, False)
    PlotNumeric("sma2", sma2[-1], 0xFF0000, False)
    PlotNumeric("fit", NetProfit() - TradeCost(), RGB_Purple(), False, True)   
