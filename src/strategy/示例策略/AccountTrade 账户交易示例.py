#-*-coding:utf-8
import talib

# 定义全局变量
ShortPeriod = 5
LongPeriod = 20
buyPos = 0
sellPos = 0

OrderNum = 1
TakeProfitSet = 45
StopLossSet = 20

MyEnterPrice = 0
EnterOrderId = -1
ExitOrderId = -1
retEnter = -1
retExit = -1
ContractId = "SHFE|F|CU|MAIN"
UserId = "ET001"


# 初始化函数
def initialize(context): 
    # 使用全局变量
    global ContractId, UserId
    
    SetBarInterval(ContractId, 'M', 1, 100)
    SetActual()
    
# 策略触发执行函数
def handle_data(context):
    # 使用全局变量
    global EnterOrderId, ExitOrderId
    global ShortPeriod, LongPeriod
    global buyPos, sellPos
    global OrderNum, TakeProfitSet, StopLossSet
    global MyEnterPrice, ContractId, UserId
    global retEnter, retExit
    
    # 定义局部变量
    MovePoint = 10

    MinPoint = PriceTick()
    MyEnterPrice = A_TotalAvgPrice()
    
    ma1 = talib.MA(Close(), timeperiod=ShortPeriod)
    ma2 = talib.MA(Close(), timeperiod=LongPeriod)
    
    #记录指标
    PlotNumeric('MA1', ma1[-1], color=RGB_Red())
    PlotNumeric('MA2', ma2[-1], color=RGB_Green())
    
    #撤消未成交开仓单
    if retEnter == 0 and A_OrderStatus(EnterOrderId) != 6:
        #A_DeleteOrder(EnterOrderId)
        LogInfo("撤销未成交的开仓单：%s, 订单状态值：%d, 可用资金：%f\n" %(EnterOrderId, A_DeleteOrder(EnterOrderId), A_FreeMargin()))
        retEnter = -1

    #撤消未成交平仓单
    if retExit == 0 and A_OrderStatus(ExitOrderId) != 6:
        #A_DeleteOrder(ExitOrderId)
        LogInfo("撤销未成交的平仓单：%s, 订单状态值：%d, 可用资金：%f\n" %(ExitOrderId, A_DeleteOrder(ExitOrderId), A_FreeMargin()))
        retExit = -1
        
        
    #打印账户当前合约持仓信息
    LogInfo("Buy:%d, Sell:%d, Total:%d\n" %(A_BuyPosition(), A_SellPosition(), A_TotalPosition()))
 
 
    #策略执行区
    #有多仓的情况
    if A_BuyPosition() > 0: 
        StopProfit = MyEnterPrice + TakeProfitSet * MinPoint
        StopLoss = MyEnterPrice - StopLossSet * MinPoint
        #止盈
        if Q_Close() >= StopProfit:
            retExit, ExitOrderId = A_SendOrder(Enum_Sell(), Enum_Exit(), OrderNum, Q_BidPrice() - MovePoint * MinPoint, ContractId, UserId, Enum_Order_Limit(), Enum_FOK(), Enum_Speculate())
            if retExit == 0:
                LogInfo("定单号：%s, 合约：%s, 卖出平仓数量：%d, 价格: %f\n" %(ExitOrderId, ContractId, OrderNum, Q_BidPrice() - MovePoint * MinPoint))
            else:
                LogInfo("卖出平仓 error: %s\n" % ExitOrderId)
        #止损
        elif Q_Close() <= StopLoss:
            retExit, ExitOrderId = A_SendOrder(Enum_Sell(), Enum_Exit(), OrderNum, Q_BidPrice() - MovePoint * MinPoint, ContractId, UserId, Enum_Order_Limit(), Enum_FOK(), Enum_Speculate())
            if retExit == 0:
                LogInfo("定单号：%s, 合约：%s, 卖出平仓数量：%d, 价格: %f\n" %(ExitOrderId, ContractId, OrderNum, Q_BidPrice() - MovePoint * MinPoint))
            else:
                LogInfo("卖出平仓 error: %s\n" % ExitOrderId)
        else:
            LogInfo("卖出平仓不操作，总仓位:%d, 多头仓位:%d, 空头仓位:%d\n" % (A_TotalPosition(), A_BuyPosition(), A_SellPosition()))
    #有空仓的情况
    elif A_SellPosition() > 0:
        StopProfit = MyEnterPrice - TakeProfitSet * MinPoint
        StopLoss = MyEnterPrice + StopLossSet * MinPoint
        #止盈
        if Q_Close() <= StopProfit:
            retExit, ExitOrderId = A_SendOrder(Enum_Buy(), Enum_Exit(), OrderNum, Q_AskPrice() + MovePoint * MinPoint, ContractId, UserId, Enum_Order_Limit(), Enum_FOK(), Enum_Speculate())
            if retExit == 0:
                LogInfo("定单号：%s, 合约：%s, 买入平仓数量：%d, 价格: %f\n" %(ExitOrderId, ContractId, OrderNum, Q_AskPrice() + MovePoint * MinPoint))
            else:
                LogInfo("买入平仓 error: %s\n" % ExitOrderId)
        #止损
        elif Q_Close() >= StopLoss:
            retExit, ExitOrderId = A_SendOrder(Enum_Buy(), Enum_Exit(), OrderNum, Q_AskPrice() + MovePoint * MinPoint, ContractId, UserId, Enum_Order_Limit(), Enum_FOK(), Enum_Speculate())
            if retExit == 0:
                LogInfo("定单号：%s, 合约：%s, 买入平仓数量：%d, 价格: %f\n" %(ExitOrderId, ContractId, OrderNum, Q_AskPrice() - MovePoint * MinPoint))
            else:
                LogInfo("买入平仓 error: %s\n" % ExitOrderId)
        else:
            LogInfo("买入平仓不操作，总仓位:%d, 多头仓位:%d, 空头仓位:%d\n" % (A_TotalPosition(), A_BuyPosition(), A_SellPosition()))
    #没有持仓开仓
    elif A_TotalPosition() == 0:
        if ma1[-1] > ma2[-1]:
            retEnter, EnterOrderId = A_SendOrder(Enum_Buy(), Enum_Entry(), OrderNum, Q_AskPrice() + MovePoint * MinPoint, ContractId, UserId, Enum_Order_Limit(), Enum_FOK(), Enum_Speculate())
            if retEnter == 0:
                LogInfo("定单号：%s, 合约：%s, 买入开仓数量：%d, 价格: %f\n" %(EnterOrderId, ContractId, OrderNum, Q_AskPrice() + MovePoint * MinPoint))
            else:
                LogInfo("买入开仓 error: %s\n" % EnterOrderId)
        elif ma1[-1] < ma2[-1]:
            retEnter, EnterOrderId = A_SendOrder(Enum_Sell(), Enum_Entry(), OrderNum, Q_BidPrice()  - MovePoint * MinPoint, ContractId, UserId, Enum_Order_Limit(), Enum_FOK(), Enum_Speculate())
            if retEnter == 0:
                LogInfo("定单号：%s, 合约：%s, 卖出开仓数量：%d, 价格: %f\n" %(EnterOrderId, ContractId, OrderNum, Q_BidPrice() - MovePoint * MinPoint))
            else:
                LogInfo("卖出开仓 error: %s\n" % EnterOrderId)
    else:
        LogInfo("不操作, 总仓位:%d, 多头仓位:%d, 空头仓位:%d\n" % (A_TotalPosition(), A_BuyPosition(), A_SellPosition()))


