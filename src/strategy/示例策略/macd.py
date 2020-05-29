##################################################################
# MACD策略
# MACD指标是所有技术指标里最经典的一个技术指标，
# 正确运用这个指标，通过结合K线、行情走势等，基本上就可以达到较好地买卖效果。
##################################################################
import talib

fast = 12 # 快周期
slow = 26 # 慢周期
back = 9  # dea周期
qty = 1   # 下单量
macd_dx = 0.01 #macd阀值

def initialize(context): 
    SetOrderWay(2)

def handle_data(context):
    # 等待数据就绪，否则计算果结为异常值
    if len(Close()) < slow + back - 1:
        return

    # 计算MACD   
    diff, dea, macd = talib.MACD(Close(), fast, slow, back)

    # 突破下单
    if MarketPosition() != 1 and macd[-1] > macd_dx:
        Buy(qty, Open()[-1]) 
    elif MarketPosition() != -1 and macd[-1] < -macd_dx:
        SellShort(qty, Open()[-1]) 

    # 绘制MACD曲线    
    PlotStickLine('macd', 0, macd[-1], RGB_Red() if macd[-1] > 0 else RGB_Blue(), False, False) 
    PlotNumeric('diff', diff[-1], RGB_Red(), False, False)
    PlotNumeric('dea', dea[-1], RGB_Blue(), False, False) 
    # 绘制盈亏曲线
    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xcccccc, False, True) 

