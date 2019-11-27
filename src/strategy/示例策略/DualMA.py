import talib

p1=5
p2=20

def initialize(context): 
    SetOrderWay(2)

def handle_data(context):
    if len(Close()) < p2:
        return
    
    # 使用talib计算均价
    ma1 = talib.MA(Close(), p1)
    ma2 = talib.MA(Close(), p2) 

    # 执行下单操作
    if MarketPosition() <= 0 and ma1[-1] > ma2[-1]:
        Buy(1, Close()[-1])
    if MarketPosition() >= 0 and ma1[-1] < ma2[-1]:
        SellShort(1, Close()[-1])
    
    # 绘制指标图形
    PlotNumeric("ma1", ma1[-1], RGB_Red())
    PlotNumeric("ma2", ma2[-1], RGB_Green())    
    PlotNumeric("fit", NetProfit() + FloatProfit() - TradeCost(), RGB_Red(), False)

