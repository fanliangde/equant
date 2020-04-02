import talib


def initialize(context): 
    SetBarInterval("NYMEX|Z|CL|MAIN", 'M', 1, 200)


def handle_data(context):
    avail = A_Available()
    margin = A_Margin()
    assets = A_Assets()

    LogInfo(avail, margin, assets)
