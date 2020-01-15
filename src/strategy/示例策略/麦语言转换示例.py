# 文华麦语言转EQuant策略示例：
# 麦语言与EQuant的函数对照见QQ群472789093里的群文件：极星量化与麦语言对照.html

###########################################################################
# 麦语言代码：
###########################################################################
# //该策略为趋势跟踪交易策略，适用较大周期，如日线。
# //该模型仅用作模型开发案例，依此入市，风险自负。
# ////////////////////////////////////////////////////////
# MOVAVGVAL:MA((HIGH+LOW+CLOSE)/3,AVGLENGTH);//三价均线
# TRUEHIGH1:=IF(HIGH>REF(C,1),HIGH,REF(C,1));
# TRUELOW1:=IF(LOW<=REF(C,1),LOW,REF(C,1));
# TRUERANGE1:=IF(ISLASTBAR,H-L,TRUEHIGH1-TRUELOW1);
# UPBAND:MOVAVGVAL+MA(TRUERANGE1,ATRLENGTH);
# DNBAND:MOVAVGVAL-MA(TRUERANGE1,ATRLENGTH);//通道上下轨
# LIQUIDPOINT:=MOVAVGVAL;//出场条件
# MOVAVGVAL>REF(MOVAVGVAL,1)&&C>UPBAND,BK;//三价均线向上，并且价格上破通道上轨，开多单
# C<LIQUIDPOINT,SP;//持有多单时，价格下破三价均线，平多单
# MOVAVGVAL<REF(MOVAVGVAL,1)&&C<DNBAND,SK;//三价均线向下，并且价格下破通道下轨，开空单
# C>LIQUIDPOINT,BP;//持有空单时，价格上破三价均线，平空单
# AUTOFILTER;


###########################################################################
# EQuant代码：
###########################################################################
import talib
import numpy as np

# 策略参数
g_params['QTY'] = 1         #下单量
g_params['AVGLENGTH'] = 20
g_params['ATRLENGTH'] = 3

AVGS = []
TRUERANGE1 = []

class lst():
    def update_lst(self, lst, val):
        if len(Close()) > len(lst):
            lst.append(val)
        else:
            lst[-1] = val

def initialize(context):
    SetOrderWay(2)

def handle_data(context):
    if len(Close()) < 2:
        return
    QTY = g_params['QTY']
    AVGLENGTH = g_params['AVGLENGTH']
    ATRLENGTH = g_params['ATRLENGTH']

    ls = lst()
    global AVGS, TRUERANGE1
    ls.update_lst(AVGS, (High()[-1] + Low()[-1] + Close()[-1]) / 3)
    TRUEHIGH1    = High()[-1] if High()[-1] > Close()[-2] else Close()[-2]
    TRUELOW1     = Low()[-1] if Low()[-1] <= Close()[-2] else Close()[-2]
    ls.update_lst(TRUERANGE1, High()[-1] - Low()[-1] if BarStatus() == 2 else TRUEHIGH1 - TRUELOW1)
    if len(AVGS) < AVGLENGTH + 1:
        return

    # 三价均线
    MOVAVGVAL    = talib.MA(np.array(AVGS), AVGLENGTH)
    # 通道上下轨
    ATR          = talib.MA(np.array(TRUERANGE1), ATRLENGTH)
    UPBAND       = MOVAVGVAL[-1] + ATR[-1]
    DNBAND       = MOVAVGVAL[-1] - ATR[-1]
    # 出场条件
    LIQUIDPOINT  = MOVAVGVAL[-1]

    # 三价均线向上，并且价格上破通道上轨，开多单
    if MOVAVGVAL[-1] > MOVAVGVAL[-2] and Close()[-1] > UPBAND:
        Buy(QTY, Close()[-1], needCover = False)
    # 持有多单时，价格下破三价均线，平多单
    if Close()[-1] < LIQUIDPOINT:
        Sell(QTY, Close()[-1])
    # 三价均线向下，并且价格下破通道下轨，开空单
    if MOVAVGVAL[-1] < MOVAVGVAL[-2] and Close()[-1] < DNBAND:
        SellShort(QTY, Close()[-1], needCover = False)
    # 持有空单时，价格上破三价均线，平空单
    if Close()[-1] > LIQUIDPOINT:
        BuyToCover(QTY, Close()[-1])

    # 绘制指标线
    PlotNumeric('MOVAVGVAL', MOVAVGVAL[-1], 0x0000ff)
    PlotNumeric('UPBAND', UPBAND, 0xff0000)
    PlotNumeric('DNBAND', DNBAND, 0x00ff00)
    # 盈亏曲线
    PlotNumeric('PROFIT', NetProfit() - TradeCost(), RGB_Purple(), False)
