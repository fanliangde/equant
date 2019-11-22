# 双均线策略
# 历史阶段用了buy、sell进行测试
# 实盘阶段用了A函数进行更精细的下单控制
import talib
import time

p1 = 5
p2 = 20
qty = 1
def initialize(context):
    SetOrderWay(2)
    SetActual()
    
# 历史测回执行逻辑
def his_trigger(ma1, ma2):
    if ma1[-1] > ma2[-1] and MarketPosition() <= 0:
        Buy(qty, Close()[-1])
    elif ma1[-1] < ma2[-1] and MarketPosition() >= 0:
        SellShort(qty, Close()[-1])
    
# 实盘阶段执行逻辑
def tim_trigger(ma1, ma2):
    if ma1[-1] > ma2[-1] and A_TotalPosition() <= 0:
        prc = min(Q_BidPrice() + PriceTick(), Q_UpperLimit())
        if A_TotalPosition() < 0:
            A_SendOrder(Enum_Buy(), Enum_ExitToday(), A_SellPosition(), prc)
        A_SendOrder(Enum_Buy(), Enum_Entry(), qty, prc)
    elif ma1[-1] < ma2[-1] and A_TotalPosition() >= 0:
        prc = max(Q_AskPrice() - PriceTick(), Q_LowLimit())
        if A_TotalPosition() > 0:
            A_SendOrder(Enum_Sell(), Enum_ExitToday(), A_BuyPosition(), prc) 
        A_SendOrder(Enum_Sell(), Enum_Entry(), qty, prc)  

def handle_data(context):
    if len(Close()) < p2:
        return;
        
    ma1 = talib.MA(Close(), p1)
    ma2 = talib.MA(Close(), p2)  
    
    his = True  # BarStatus() != 2
    if his:
        his_trigger(ma1, ma2) 
    else: 
        tim_trigger(ma1, ma2) 
    
    PlotNumeric("ma1", ma1[-1], 0xFF0000)
    PlotNumeric("ma2", ma2[-1], 0x00aa00) 
    fit = NetProfit() + FloatProfit() - TradeCost() if his else A_CoverProfit() + A_ProfitLoss() - A_Cost()
    PlotNumeric("fit", fit, 0x0000FF, False)

