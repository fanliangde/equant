######################################################################
# 阶段突破策略:
#   记录早上split_tim时间点前的高低点
#   split_tim时间点之后突破就开仓，止损stop_dot点
#   当日闭市前cover_min分钟开始清仓，实盘清仓会自动追价，每秒一次，先撤后平
######################################################################
import math

split_tim = 0.10  # 分割点时间，统计分割点之前的高低点，分割点之后突破就开仓
stop_dot = 20     # 开仓后的止损点数
cover_min = 10    # 当日闭市前10分钟开始仓清
qty = 1           # 单笔开仓量

hi = 0            # 最高
lo = 100000000    # 最低
curr_date = -1    # 前当交易日

def initialize(context): 
    # K线稳定后发单
    SetOrderWay(2)
    # 一秒钟执行一次的定时器
    SetTriggerType(3, 1000)
    # 设置止损
    SetStopPoint(stop_dot, 2, 1)

# 分钟数转小数时间
def min2float(val):
    return (math.ceil(val / 60) * 40 + val) * 0.0001  

def handle_data(context):    
    global hi, lo, curr_date
    #换日时初始化最高最低数值
    if curr_date != TradeDate():
        hi = 0
        lo = 100000000
        curr_date = TradeDate()

    # 获得当前时间及合约的开闭市时间
    mid_tim = split_tim
    tim = Time()
    count = GetSessionCount()
    if count <= 0:
        LogError('时间节点获取错误', context.contractNo())
        return 
    op_tim = GetSessionStartTime(index = 0)
    cl_tim = GetSessionEndTime(index = count - 1) 
    if op_tim > cl_tim:
        if tim <= cl_tim:
            tim += 0.24
        if mid_tim <= cl_tim:
            mid_tim += 0.24
        cl_tim += 0.24  
        
    # 尾盘清仓
    if cl_tim - min2float(cover_min) <= tim <= cl_tim:       
        b_qty = BuyPosition()
        s_qty = SellPosition()
        if b_qty > 0:
            Sell(b_qty, Close()[-1])
        if s_qty > 0:
            BuyToCover(s_qty, Close()[-1])

        # 实盘阶段，清仓追价，每1秒判断一次，先撤再平
        if context.triggerType() == 'C':
            DeleteAllOrders()
            b_qty = A_BuyPosition()
            s_qty = A_SellPosition()
            if b_qty > 0:
                A_SendOrder(Enum_Sell(), Enum_ExitToday(), b_qty, Q_BidPrice())
            if s_qty > 0:
                A_SendOrder(Enum_Buy(), Enum_ExitToday(), s_qty, Q_AskPrice())
    
    # 忽略其他时段的定时器消息
    elif context.triggerType() == 'C': 
        return
            
    # 记录时间分割点之前的高低值，支持夜盘阶段
    elif op_tim <= tim < mid_tim:
        hi = max(hi, High()[-1])
        lo = min(lo, Low()[-1])

    # 时间分割点之后，突破下单, 并设置止损
    elif hi != 0:
        if Close()[-1] > hi:
            Buy(qty, Open()[-1], context.contractNo(), False)
        elif Close()[-1] < lo:
            SellShort(qty, Open()[-1], context.contractNo(), False)  

    if hi == 0:
        return
    # 绘制最高最低曲线
    PlotNumeric('hi', hi, RGB_Red())
    PlotNumeric('lo', lo, RGB_Blue())
    # 绘制盈亏曲线
    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xFF00FF, False)         
    
