import talib

g_params['lose'] = 3            #止损点
g_params['win'] = 10            #止赢点
g_params['float_start'] = 0     #浮动启动点
g_params['float_dot'] = 5       #浮动止损点
g_params['stop_switch'] = 3     #止损开关，1止损,2止盈,3止损+止盈,4浮动,5止损+浮动,6止盈+浮动,7全部
g_params['single'] = True       #边单持仓

#contNo = 'NYMEX|F|CL|1910'
contNo = 'ZCE|Z|TA|MAIN'

################################################################
buy = True
def single_test(): 
    global buy
    if MarketPosition() == 0:
        if buy:
            Buy(1, Close()[-1])
        else:
            SellShort(1, Close()[-1])
        buy = not buy   

def double_test():
    if BuyPosition() == 0:
        Buy(1, Low()[-1], needCover = False)
    if SellPosition() == 0:
        SellShort(1, High()[-1], needCover = False)   

def set_stop():
    if g_params['stop_switch'] & 1:
        SetStopPoint(g_params['lose'])
    if g_params['stop_switch'] & 2:
        SetWinPoint(g_params['win'])    
    if g_params['stop_switch'] & 4:
        SetFloatStopPoint(g_params['float_start'], g_params['float_dot'])
 

################################################################
def initialize(context): 
    SetBarInterval(contNo , 'M', 1, 2000)
    set_stop()

def handle_data(context):   
    if g_params['single']:
        single_test()
    else:
        double_test()

    
