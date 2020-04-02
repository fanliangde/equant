import talib

sentOrder = True
localIdList = []

cnt = 0

def initialize(context): 
    SetBarInterval("NYMEX|Z|CL|MAIN", 'M', 1, 200)
    SetActual()


def handle_data(context):
    global sentOrder, localIdList
    global cnt
    if context.triggerType() == 'H':
        return

    if sentOrder:
        for i in range(2):
            ret, localId = A_SendOrder(Enum_Buy(), Enum_Entry(), 1, Q_Last())
            if ret == 0: 
                localIdList.append(localId)
                cnt = cnt + 1
        sentOrder = False
    

    if not A_AccountID():
        return
    
    for lid in localIdList:
        LogInfo("ORDER", lid, A_GetOrderNo(lid), A_OrderContractNo( A_GetOrderNo(lid)[0]), A_OrderStatus(lid), A_FirstOrderNo())
    
