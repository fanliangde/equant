import talib

cur_times = 0
order_times = 1
ContractId = "NYMEX|Z|CL|MAIN"

def initialize(context): 
    SetBarInterval(ContractId, 'M', 1, 100)
    SetActual()

def handle_data(context):
    global cur_times
    #回测阶段不下单
    if context.triggerType() == 'H':
        return

    if cur_times < order_times:
        A_SendOrder(Enum_Buy(), Enum_Entry(), 1, Close()[-1])
        A_SendOrder(Enum_Sell(), Enum_Entry(), 1, Close()[-1])
        cur_times += 1

    b2c = A_BuyPositionCanCover()
    s2c = A_SellPositionCanCover()
