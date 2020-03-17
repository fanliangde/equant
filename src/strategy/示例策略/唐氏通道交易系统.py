import talib
import numpy as np

# 全局变量定义
M = 5
N = 5
MaxPositionNum = 3   # 最大开仓数
StopPoint = 5        # 止损点
WinPoint = 10        # 止赢点
FloatStopStart = 50  # 浮动止损开始点
FloatStopPoint = 20  # 浮动止损点

HHV = np.array([])
LLV = np.array([])

ContractId = 'ZCE|Z|TA|MAIN'#'ZCE|F|TA|005'#

def initialize(context): 
    global ContractId
    SetBarInterval(ContractId, 'M', 1, 500)

def handle_data(context):
    global ContractId

    # 最少获取10根数据
    bars = HisBarsInfo()
    barLen = len(bars)
    if barLen < 10:
        return

    close  = bars[-1]["LastPrice"]
    pclose = bars[-2]["LastPrice"]
    high   = bars[-1]["HighPrice"]
    phigh  = bars[-2]["HighPrice"]
    low    = bars[-1]["LowPrice"]
    plow   = bars[-2]["LowPrice"]

    # 求M周期最高
    HHV = Highest(High().tolist(), M)
    # 求N周期最低
    LLV = Lowest(Low().tolist(), N)

    PlotNumeric("LAST_HHV", HHV[-2], RGB_Red())
    PlotNumeric("LAST_LLV", LLV[-2], RGB_Green())

    if high > HHV[-2]:
        if (CurrentContracts() < MaxPositionNum) or (MarketPosition() < 0):
            Buy(1, high)
    elif low < LLV[-2]:
        if (abs(CurrentContracts()) < MaxPositionNum) or (MarketPosition() > 0):
            SellShort(1, low)
    
    # 止损
    SetStopPoint(StopPoint)
    # 止赢
    SetWinPoint(WinPoint)
    # 浮动止损, 暂不支持
    #SetFloatStopPoint(FloatStopStart, FloatStopPoint)
