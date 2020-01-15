#-*-coding:utf-8
import talib as ta
import numpy as np
#import math

RiskRatio = 1   # % Risk Per N ( 0 - 100)
ATRLength = 20  # 平均波动周期 ATR Length
boLength = 20   # 短周期 BreakOut Length
fsLength = 55   # 长周期 FailSafe Length
teLength = 10   # 离市周期 Trailing Exit Length
LPTF = True     # 使用入市过滤条件
PreEP = 0       # 前一次开仓的价格
AvgTR = 1       # 真实价格波动范围指数平均

SendOrderThisBar = False    # 当前Bar有过交易
PreBreakoutFailure = False  # 前一次突破是否失败

myEntryPrice = 0
myExitPrice = 0
DonchianHi = 0
DonchianLo = 0
fsDonchianHi = 0
fsDonchianLo = 0
ExitHighestPrice = 0
ExitLowestPrice = 0

ContractId = 'SHFE|F|CU|MAIN'

# 求真实最高价，真实最低价，真实范围序列值
def TrueRange(barsinfo:list):
    if len(barsinfo) <= 0:
        return None, None, None

    ths = []
    tls = []
    trs = []
    hs = []
    ls = []

    for i, p in enumerate(barsinfo):
        high = barsinfo[i]["HighPrice"]
        low = barsinfo[i]["LowPrice"]
        hs.append(high)
        ls.append(low)

        if i == 0:
            th = high
            tl = low
        else:
            pclose = barsinfo[i-1]["LastPrice"]
            th = high if high >= pclose else pclose
            tl = low  if low  <= pclose else pclose

        tr = th - tl
        ths.append(th)
        tls.append(tl)
        trs.append(tr)

    return np.array(hs), np.array(ls), np.array(trs)

# 求指数平均
def XAverage(prices:np.array, length):
    fac = 2.0/(length+1)
    xa = 1

    if len(prices) < length:
        return xa    

    for i, p in enumerate(prices):
        if i == 0:
            xa = p
        else:
            xa = xa + fac * (p - xa)
    
    return xa

def initialize(context):
    global ContractId
    SetBarInterval(ContractId, 'M', 1, 2000)
    SetActual()

def handle_data(context):
    global RiskRatio, ATRLength, boLength
    global teLength, fsLength, LPTF
    global PreEP, AvgTR, SendOrderThisBar
    global PreBreakoutFailure, ContractId
    global myEntryPrice, myExitPrice
    global ExitHighestPrice, ExitLowestPrice
    global DonchianHi, DonchianLo   
    global fsDonchianHi, fsDonchianLo

    if BarStatus() == 0:
        PreEP = np.nan
        PreBreakoutFailure = False

    MinPoint = PriceTick()    

    barsinfo = HisBarsInfo()

    bslen = len(barsinfo)

    if bslen < fsLength:
        return

    op = barsinfo[-1]["OpeningPrice"]

    #if len(barsinfo) > 600:
    #   barsinfo = barsinfo[-500:]

    highs, lows, trs = TrueRange(barsinfo)
    
    high  = highs[-1]
    low   = lows[-1]
    phigh = high if len(highs) <= 1 else highs[-2]
    plow  = low  if len(lows)  <= 1 else lows[-2]

    N = AvgTR
    AvgTR = XAverage(trs, ATRLength)

    #LogInfo("N:%f,cu:%f\n" %(N, ContractUnit()))
    
    TotalEquity = Available() + Margin()
    TurtleUnits = (TotalEquity*RiskRatio/100)/(N*ContractUnit(ContractId))
    TurtleUnits = int(TurtleUnits)
    maxUnites = int(Available()/(high*ContractUnit(ContractId)))
    TurtleUnits = min(maxUnites , TurtleUnits)
    LogInfo("avl:%f, mar:%f, conu:%f, tu:%f, N:%f, mp:%f, cidx:%d, bslen:%d\n" \
        %(Available(), Margin(), ContractUnit(ContractId), TurtleUnits, N, MinPoint, CurrentBar(), bslen))

    DonchianHi   = ta.MAX(highs[:-1], timeperiod=boLength)[-1]
    DonchianLo   = ta.MIN(lows[:-1],  timeperiod=boLength)[-1]
    fsDonchianHi = ta.MAX(highs[:-1], timeperiod=fsLength)[-1]
    fsDonchianLo = ta.MIN(lows[:-1],  timeperiod=fsLength)[-1]
    ExitHighestPrice = ta.MAX(highs[:-1], timeperiod=teLength)[-1]
    ExitLowestPrice = ta.MIN(lows[:-1],  timeperiod=teLength)[-1]

    # LogInfo("PreEP=%f\n" % PreEP)
    # LogInfo("PreBreakoutFailure=%s\n" % PreBreakoutFailure)

    LogInfo("mpos:%d, bpos:%d, spos:%d\n" %(MarketPosition(), BuyPosition(), SellPosition()))
    LogInfo("low:%f,high:%f,dh:%f,dl:%f,fdh:%f,fdl:%f,ehp:%f,elp:%f,pep:%f,n:%f\n" %(low, high, DonchianHi, \
        DonchianLo, fsDonchianHi, fsDonchianLo, ExitHighestPrice, ExitLowestPrice,PreEP,N))

    # 当不使用过滤条件，或者使用过滤条件并且条件为PreBreakoutFailure为True进行后续操作
    if MarketPosition() == 0 and ((not LPTF) or PreBreakoutFailure):
        # 突破开仓
        if high > DonchianHi and TurtleUnits >= 1:
            # 开仓价格取突破上轨+一个价位和最高价之间的较小值，这样能更接近真实情况，并能尽量保证成交
            myEntryPrice = min(high, DonchianHi + MinPoint)
            # 大跳空的时候用开盘价代替
            myEntryPrice = max(op, myEntryPrice)
            PreEP = myEntryPrice
            Buy(TurtleUnits, myEntryPrice)
            SendOrderThisBar = True
            PreBreakoutFailure = False

        if low < DonchianLo and TurtleUnits >= 1:
            # 开仓价格取突破下轨-一个价位和最低价之间的较大值，这样能更接近真实情况，并能尽量保证成交
            myEntryPrice = max(low, DonchianLo - MinPoint)
            # 大跳空的时候用开盘价代替
            myEntryPrice = min(op, myEntryPrice)
            PreEP = myEntryPrice
            SellShort(TurtleUnits, myEntryPrice)
            SendOrderThisBar = True
            PreBreakoutFailure = False

    # 长周期突破开仓 Failsafe Breakout point
    if MarketPosition() == 0:
        # LogInfo("fsDonchianHi=%f\n" % fsDonchianHi)
        # LogInfo("fsDonchianLo=%f\n" % fsDonchianLo)

        if high > fsDonchianHi and TurtleUnits >= 1:
            # 开仓价格取突破上轨+一个价位和最高价之间的较小值，这样能更接近真实情况，并能尽量保证成交
            myEntryPrice = min(high, fsDonchianHi + MinPoint)
            # 大跳空的时候用开盘价代替
            myEntryPrice = max(op, myEntryPrice)
            PreEP = myEntryPrice
            Buy(TurtleUnits, myEntryPrice)
            SendOrderThisBar = True
            PreBreakoutFailure = False

        if low < fsDonchianLo and TurtleUnits >= 1:
            # 开仓价格取突破下轨-一个价位和最低价之间的较大值，这样能更接近真实情况，并能尽量保证成交
            myEntryPrice = max(low, fsDonchianLo - MinPoint)
            # 大跳空的时候用开盘价代替
            myEntryPrice = min(op, myEntryPrice)
            PreEP = myEntryPrice
            SellShort(TurtleUnits, myEntryPrice)
            SendOrderThisBar = True
            PreBreakoutFailure = False

    # 有多仓的情况
    if MarketPosition() == 1:
        # LogInfo("ExitLowestPrice=%f\n" % ExitLowestPrice)
        if low < ExitLowestPrice:
            myExitPrice = max(low, ExitLowestPrice - MinPoint)
            myExitPrice = min(op, myExitPrice)
            # 全平多仓
            bpos = BuyPosition()
            if bpos > 0:
                Sell(bpos, myExitPrice)
        else:
            if PreEP != np.nan and TurtleUnits >= 1:
                if high >= PreEP + 0.5*N:
                    myEntryPrice = high
                    PreEP = myEntryPrice
                    Buy(TurtleUnits, myEntryPrice)
                    SendOrderThisBar = True

            # 止损指令, 加仓Bar不止损
            if low <= (PreEP - 2*N) and SendOrderThisBar == False:
                myExitPrice = PreEP - 2*N
                # 全平多仓
                bpos = BuyPosition()
                if bpos > 0:
                    Sell(bpos, myExitPrice)
                PreBreakoutFailure = True
    # 有空仓的情况
    elif MarketPosition() == -1:
        # 求出持空仓时离市的条件比较值
        # LogInfo("ExitHighestPrice=%f\n" % ExitHighestPrice)
        if high > ExitHighestPrice:
            myExitPrice = min(high, ExitHighestPrice + MinPoint)
            # 大跳空的时候用开盘价代替
            myExitPrice = max(op, myExitPrice)
            # 全平空仓
            spos = SellPosition()
            if spos > 0:
                BuyToCover(spos, myExitPrice)
        else:
            if PreEP != np.nan and TurtleUnits >= 1:
                if low <= PreEP - 0.5*N:
                    myEntryPrice = low
                    PreEP = myEntryPrice
                    SellShort(TurtleUnits, myEntryPrice)
                    SendOrderThisBar = True
            # 止损指令, 加仓Bar不止损
            if high >= (PreEP + 2*N) and SendOrderThisBar == False:
                myExitPrice = PreEP + 2*N
                # 全平空仓
                spos = SellPosition()
                if spos > 0:
                    BuyToCover(spos, myExitPrice)
                PreBreakoutFailure = True

