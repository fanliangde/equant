import talib

code = 'HKEX|F|HSI|2003'
def initialize(context): 
    SetBarInterval(code, 'M', 1, 10)

def handle_data(context):
    LogInfo('资金', A_Assets())
