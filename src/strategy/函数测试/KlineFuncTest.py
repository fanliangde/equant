#-*-coding:utf-8
import talib

def initialize(context):
    SetBarInterval('NYMEX|F|CL|2001', 'M',1)
    SetTriggerType(1, None)

def handle_data(context):
    barCount = BarCount()
    LogInfo('barCount=', barCount)
    
    npClose = Close()
    LogInfo('Close=', npClose)
    
    npOpen = Open()
    LogInfo('Open=', npOpen)
    
    npHigh = High()
    LogInfo("High=", npHigh)
    
    npLow = Low()
    LogInfo('Low=', npLow)
    
    npVol = Vol()
    LogInfo("Vol=", npVol)
    
    npOpenInt = OpenInt()
    LogInfo('OpenInt=', npOpenInt)
    
    barStatus = BarStatus()
    LogInfo("BarStatus=", barStatus)
    
    currentBar = CurrentBar()
    LogInfo("currentBar=", currentBar)
    
    npDate = Date()
    LogInfo("Date=", npDate)
    
    npTime = Time()
    LogInfo('Time=', npTime)
    
    npTradeDate = TradeDate()
    LogInfo("TradeDate=", npTradeDate)
    
    LogInfo("context=", context.triggerData)
    