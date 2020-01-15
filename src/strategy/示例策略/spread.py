######################################################
# 基于布林带策略的内外盘套利
######################################################

import talib
import numpy as np

code1  = 'DCE|F|A|MAIN'   # 盘内合约
code2  = 'CBOT|F|S|MAIN'  # 外盘合约

#参数定义
g_params['user1']  = '54001'          # 内盘账户
g_params['user2']  = 'ES002'          # 外盘账户
g_params['rate']   = 7.08             # 美元汇率
g_params['qty']    = 1                # 下单数量
g_params['period'] = 10               # 计算周期

def float_cmp(val1, val2):
    val = val1 - val2
    if val > 0.000001:
        return 1
    elif val < -0.000001:
        return -1
    else:
        return 0

# 判断合约code在时间点tim时是否处于开盘阶段
def is_trading(code, tim):
    count = GetSessionCount(code)
    for i in range(0, count):
        b = GetSessionStartTime(code, i)
        e = GetSessionEndTime(code, i)
        if e < b:
            if b <= tim <= 0.24 or 0 <= tim < e:
                return True
        elif b <= tim < e:
            return True
    return False

def initialize(context):
    # 订阅行情
    SetBarInterval(code1, 'M', 1, 3000)
    SetBarInterval(code2, 'M', 1, 3000)
    # K线稳定后发单
    SetOrderWay(2)

# K线索引
old_ind = -1
# 价差队列
spds = []        
def handle_data(context):
    # 不在交易时段则不运行
    if not is_trading(code1, Time(code1, 'M', 1)) or not is_trading(code2, Time(code2, 'M', 1)):
        return

    # 获得参数
    global g_params
    user1 = g_params['user1']
    user2 = g_params['user2']
    rate = g_params['rate']
    qty = g_params['qty']
    p = g_params['period']
 
    # 数据不足时结果为异常值  
    count1 = len(Close(code1, 'M', 1))
    count2 = len(Close(code2, 'M', 1))  
    if count1 == 0 or count2 == 0:
        return
    if not (count1 >= p or count2 >= p):
        return
    
    # 生成价差队列
    spd_c = Close(code1, 'M', 1)[-1] - Close(code2, 'M', 1)[-1] * rate

    global spds, old_ind    
    if CurrentBar(code1, 'M', 1) > old_ind:
        spds.append(spd_c)
        old_ind = CurrentBar(code1, 'M', 1)
    else:
        spds[-1] = spd_c

    # 用布林函数计算布林带上中下轨
    upp, mid, low = talib.BBANDS(np.array(spds), p, 2, 2)
    
    # 布林带震荡区间下单    
    # 取下单价，历史阶段取收盘价，实盘截断取行情挂单价
    is_his = BarStatus(code1, 'M', 1) != 2 or BarStatus(code2, 'M', 1) != 2
    bid1 = Close(code1, 'M', 1)[-1] if is_his else Q_BidPrice(code1)
    ask1 = Close(code1, 'M', 1)[-1] if is_his else Q_AskPrice(code1)
    bid2 = Close(code2, 'M', 1)[-1] if is_his else Q_BidPrice(code2)
    ask2 = Close(code2, 'M', 1)[-1] if is_his else Q_AskPrice(code2)
    # 高抛低收
    if MarketPosition(code1) != -1 and float_cmp(spds[-1], upp[-1]) > 0:
        SellShort(qty, bid1, code1, userNo=user1)
        Buy(qty, ask2, code2, userNo=user2)
        LogInfo('sell spd', bid1, ask2)
    elif MarketPosition(code1) != 1 and float_cmp(spds[-1], low[-1]) < 0:
        Buy(qty, ask1, code1, userNo=user1)
        SellShort(qty, bid2, code2, userNo=user2)
        LogInfo('buy  spd', ask1, bid2)

    # 绘制曲线
    PlotNumeric('upp', upp[-1], RGB_Red(), False)
    PlotNumeric('mid', mid[-1], RGB_Blue(), False)
    PlotNumeric('low', low[-1], RGB_Green(), False)
    PlotNumeric('spd', spds[-1], RGB_Purple(), False)
    PlotNumeric("fit", NetProfit() + TradeCost(), RGB_Brown(), False, True)
