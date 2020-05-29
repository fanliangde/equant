import talib


def initialize(context): 
    SetBarInterval("ZCE|F|TA|012", 'M', 1, 1)
    SetTriggerType(5)
    #SetBarInterval("SHFE|F|RB|1910", 'M', 1, 2000)
    #SetBarInterval("DCE|F|I|1909", 'M', 1, 2000)
    #SetBarInterval("NYMEX|F|CL|1908", 'M', 1, 2000)

def handle_data(context):
    
    vol = talib.MA(Vol().astype(float), timeperiod=20, matype=0)
    PlotNumeric("VOL", vol[-1], main=False, color=RGB_Yellow())
    LogInfo(Date(), Time(), TradeDate(), Q_UpdateTime(), Vol()[-1], context.dateTimeStamp())
