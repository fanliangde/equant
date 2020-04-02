import talib

def getV2(a):
    return a[-1] if len(a) < 2 else a[-2]

def getAvg(high, low):
    avg = []
    for i in range(len(high)):
        middle = (high[i] + low[i]) / 2
        avg.append(middle)

    return avg

def initialize(context): 
    SetBarInterval("DCE|Z|I|MAIN", 'M', 1, 100)


def handle_data(context):
    avg = getAvg(High(), Low())
    avg2 = getV2(avg)
    LogInfo(avg2)
