# EQuant策略的基本结构：模块导入、策略参数、全局变量、四个接口函数
# 基本的python语法：变量使用，变量赋值、全局变量、数组操作、list访问、字典使用、条件语句、循环语句

# 导入功能模块
import talib
import numpy as np

# 策略参数
g_params['p1'] = 20
g_params['p2'] = 40
g_params['qty'] = 5

# 全局变量
ord_bar = 0

# 策略初始化函数，策略开始运行时一次
def initialize(context): 
    # K线完成时触发
    SetOrderWay(2)

# 策略执行函数，策略触发事件每次触发时都会调用一次
def handle_data(context):
    # 全局变量, 若要将修改后的变量值保存下来，则需要在
    global ord_bar

    # 局部变量
    ind = CurrentBar()

    # 条件语句1
    if ind > 10 and ind < 15:
        print('A', ind)
    elif ind > 20 and ind < 30:
        print('B', ind)
    elif ind == 18 or ind == 38:
        print('C', ind)
    else:
        print('D', ind)
        
    # 条件语句2
    val = Q_BidPrice() if Q_BidVol() > Q_AskVol() else Q_AskPrice()

    # 循环语句1
    for prc in Close():
        if prc > 2000:
            break
        print(prc)

    # 循环语句2
    for i in Range(0, 9):
        if i == 5:
            continue
        print(i)

    # 策略参数的使用
    ma1 = talib.MA(Close(), g_params['p1'])    
    ma2 = talib.MA(Close(), g_params['p2'])

    # 买入开仓
    Buy(g_params['qty'], Close()[-1], needCover = False)
    # 买入平仓并买入开仓
    Buy(g_params['qty'], Close()[-1])
    # 卖出平仓
    Sell(g_params['qty'], Close()[-1])

    # 卖出开仓
    SellShort(g_params['qty'], Close()[-1], needCover = False)
    # 卖出平仓并卖出开仓
    SellShort(g_params['qty'], Close()[-1])
    # 买入平仓
    BuyToCover(g_params['qty'], Close()[-1])

    # 绘制策略线
    PlotNumeric('ma1', ma1, 0xff0000)
    PlotNumeric('ma2', ma2, 0x0000ff)

# 历史回测阶段结束时执行该函数一次
def hisover_callback(context):    
    # 清空所有历史持仓
    Sell(BuyPosition(), Close()[-1])
    BuyToCover(SellPosition(), Close()[-1])

# 策略退出前执行该函数一次
def exit_callback(context):
    pass