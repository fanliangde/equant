import talib

sentOrder = True
modifyOrder = True
localIdList = []

cnt = 0

def initialize(context): 
    SetBarInterval("NYMEX|Z|CL|MAIN", 'M', 1, 200)

    #SetBarInterval("NYMEX|F|CL|1910", 'D', 50, 200)
    #SetBarInterval("ZCE|F|CF|001", 'M', 1, 200)   
    #SetBarInterval("DCE|F|J|2001", 'D', 30, 10)
    SetActual()


def handle_data(context):
    global sentOrder, localIdList, modifyOrder
    global cnt
    if context.triggerType() == 'H':
        return

    #LogInfo('ac:', A_AccountID())

    if sentOrder:
    #if cnt < 100:
        for i in range(1):
            ret, localId = A_SendOrder(Enum_Buy(), Enum_Entry(), 1, Q_Last()-10)
            if ret == 0: 
                localIdList.append(localId)
                cnt = cnt + 1
        sentOrder = False
    
    if modifyOrder and not sentOrder:
        mret = A_ModifyOrder(localIdList[-1], Enum_Buy(), Enum_Entry(), 3, 10)
        LogInfo("mret: ", mret)
        if mret:
            modifyOrder = False

    #LogInfo("lst:%s, len:%d, ac:%s" %(str(localIdList), len(localIdList), A_AccountID()))
        
    if not A_AccountID():
        return
    
    for lid in localIdList:
        LogInfo("ORDER", lid, A_GetOrderNo(lid), A_OrderContractNo( A_GetOrderNo(lid)[0]), A_OrderStatus(lid), A_FirstOrderNo())
    

