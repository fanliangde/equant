import talib

def initialize(context): 
    SetOrderWay(2)

def handle_data(context):    
    if context.strategyStatus() == 'C':         
        bid = Q_BidPrice()
        ask = Q_AskPrice()
    else:
        bid = ask = Close()[-1] 
    
    if MarketPosition() != 1:
        Buy(1, bid)       
    elif MarketPosition() != -1:
        SellShort(1, ask) 

    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xFF00FF, False)
	
