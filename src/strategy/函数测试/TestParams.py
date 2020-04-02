import talib

g_params['Lots'] = 1 #aaa
g_params['AAAA'] = 2 
g_params['BNBB'] = 'CCC'  #####bbbbbb
g_params['dddddd'] = 8.2  #####bbbbbb
g_params['Lots'] = 1
g_params['Zhisun'] = 5
g_params['Zhiying'] = 200
g_params['软件开仓开关'] = True
g_params['移动止盈'] = True
g_params['启动点数'] = 50
g_params['最小回调点数'] = 10
g_params['回调比例'] = 5
g_params['最小获利点数'] = 3
g_params['保本开关'] = True
g_params['保本启动点数'] = 10
g_params['保本点数'] = 2
g_params['放量倍数'] = 3
g_params['反手次数限制'] = 3
g_params['见顶根数'] = 9
g_params['日内平仓'] = False

def initialize(context):
    SetBarInterval("DCE|Z|I|MAIN", 'M', 1, 1)


def handle_data(context):
    LogInfo("Lots",  g_params)
