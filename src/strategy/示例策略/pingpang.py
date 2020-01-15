######################################################
# 乒乓策略
# 下单数量可以由用户设置
# 买入、卖出时的价格偏移点数可以分别设置
# 可以设置最大下单次数
# 策略启动一秒钟后下出第一笔定单，第一笔定单为买单，其价格为行情价买加一跳
# 之后只要上笔定单完全成交就会在其成交价的基础上偏移指定价位发出一笔反向定单
# 如此循环，达到最大下单次数为止
######################################################

import talib

g_params['qty'] = 1           # 下单数量
g_params['buy_dot'] = 10      # 买入偏移点数
g_params['sell_dot'] = 10     # 卖出偏移点数
g_params['max_count'] = 12    # 最大下单次数

ord_id = 'init'
ord_prc = 0
count = 0

def send_ord(direct, price):
    global ord_id
    err, ord_id =  A_SendOrder(direct, Enum_Entry(), g_params['qty'], price)
    if err:
        ord_id = 'buy' if direct == Enum_Buy() else 'sell'
        LogError('下单失败：ord: %s, err:%-4d' % (ord_id, err))

######################################################
def initialize(context):
    # 交易触发 
    SetTriggerType(2)
    # 固定1秒触发1次
    SetTriggerType(3, 1000)

def handle_data(context):
    global ord_id, count, ord_prc
    # 达到下单次数，停止交易
    if count >= g_params['max_count']:
        StopTrade()
        return
    
    # 收到已排队时增加下单计数，收到完全成交时反向下单
    if context.triggerType() == 'O':
        if A_OrderStatus(ord_id) == '4':
            count += 1
            return
        elif A_OrderStatus(ord_id) != '6':
            return
        order = context.triggerData()
        dot = g_params['sell_dot'] if A_OrderBuyOrSell(ord_id) == Enum_Buy() else -g_params['buy_dot']
        direct = Enum_Buy() if A_OrderBuyOrSell(ord_id) == Enum_Sell() else Enum_Sell()
        ord_prc = A_OrderFilledPrice(ord_id) + dot * PriceTick()
        send_ord(direct, ord_prc)
    # 初始状态或下单失败时
    elif context.triggerType() == 'C':
        # 不在交易时段则退出
        if not IsInSession():
            return
        if ord_id == 'init' and Q_BidPrice() > 0.0001:
            ord_prc = Q_BidPrice() + PriceTick()
            send_ord(Enum_Buy(), ord_prc)
        elif ord_id in ['buy', 'sell']:
            direct = Enum_Sell() if ord_id == 'sell' else Enum_Buy()
            send_ord(direct, ord_prc)
            
    # 绘制盈亏曲线
    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xFF00FF, False)
