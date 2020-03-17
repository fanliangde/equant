import talib

def initialize(context): 
    SetOrderWay(2)

def handle_data(context):   
    LogInfo('状态:', ExchangeStatus('DCE'))
    
    if MarketPosition() != 1:
        Buy(1, Close()[-1] )       
    elif MarketPosition() != -1:
        SellShort(1, Close()[-1] ) 

    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xFF00FF, False)
	
