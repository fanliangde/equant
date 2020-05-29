##################################################################
# 布林带策略
# 根据布林带计算出高中低三个通道，较好的体现了行情的盘整和突破
# 根据行情时段与特点灵活运用会有不错的效果
##################################################################
import talib

p = 8    # 计算周期
qty = 1  # 下单量

def initialize(context): 
    SetOrderWay(2)

def handle_data(context):  
    # 等待数据就绪，否则计算果结为异常值
    if len(Close()) < p:
        return
  
    # 计算布林带高中低点
    upp, mid, low = talib.BBANDS(Close(), p, 2, 2)
    
    # 低买高卖
    if MarketPosition() != 1 and Open()[-1] < low[-1]: 
        Buy(qty, Open()[-1])
    elif MarketPosition() != -1 and Open()[-1] > upp[-1]:
        SellShort(qty, Open()[-1])

    # 绘制布林带曲线
    PlotNumeric('upp', upp[-1], RGB_Red())
    PlotNumeric('mid', mid[-1], RGB_Blue())
    PlotNumeric('low', low[-1], RGB_Green())
    # 绘制盈亏曲线
    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xFF00FF, False) 

