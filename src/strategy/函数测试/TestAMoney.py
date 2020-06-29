import talib


def initialize(context):
    SetBarInterval("NYMEX|Z|CL|MAIN", 'M', 1, 200)


def handle_data(context):
    avail = A_Available()
    margin = A_Margin("ET001")
    assets = A_Assets("ET001")

    # LogInfo(avail, margin, assets)
    LogInfo(avail, margin, assets)
