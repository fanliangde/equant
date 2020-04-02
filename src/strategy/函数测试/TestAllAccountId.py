import talib

#测试场景：
#1. 没有登录时，获取到空列表
#2. 前登录或者后登录,正确获取用户登录列表
#3. 退出登录，清理掉登出的账号

def initialize(context): 
    SetBarInterval('NYMEX|Z|CL|MAIN', 'M', 1, 1)


def handle_data(context):
    # accList = A_AllAccountID()
    # LogInfo(accList)
    test()


def test():
    LogInfo("1111: ", A_AllAccountID())