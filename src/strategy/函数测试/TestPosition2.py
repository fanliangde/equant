import talib

cur_times = 0
order_times = 1
ContractId = "NYMEX|F|CL|1909"

def initialize(context): 
    SetBarInterval(ContractId, 'M', 1, 100)
    #SetActual()

def handle_data(context):
    global cur_times
    #回测阶段不下单
    if context.triggerType() == 'H':
        return

    if cur_times < order_times:
        Buy( 1, Close()[-1])
        SellShort(1, Close()[-1])
        cur_times += 1


