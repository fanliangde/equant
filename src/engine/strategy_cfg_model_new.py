import numpy as np
from capi.com_types import *
from .engine_model import *
from copy import deepcopy
import talib
import time, sys
import datetime
from dateutil.relativedelta import relativedelta
import copy
import math
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


from datetime import datetime, timedelta

class StrategyConfig_new(object):
    '''
    {
            'SubContract': ['DCE|F|M|1909', 'ZCE|F|TA|909', 'ZCE|F|SR|001'],
            'Sample': {
                'DCE|F|M|1909': [{
                    'KLineType': 'M',
                    'KLineSlice': 1,
                    'BeginTime': '',
                    'KLineCount': 2,
                    'AllK': False,
                    'UseSample': True,
                    'Trigger': True
                }, {
                    'KLineType': 'D',
                    'KLineSlice': 1,
                    'BeginTime': '',
                    'KLineCount': 2,
                    'AllK': False,
                    'UseSample': True,
                    'Trigger': True
                }],
                'ZCE|F|TA|909': [{
                    'KLineType': 'M',
                    'KLineSlice': 1,
                    'BeginTime': '',
                    'KLineCount': 2,
                    'AllK': False,
                    'UseSample': True,
                    'Trigger': True
                }],
                'ZCE|F|SR|001': [{
                    'KLineType': 'D',
                    'KLineSlice': 1,
                    'BeginTime': '',
                    'KLineCount': 2,
                    'AllK': False,
                    'UseSample': True,
                    'Trigger': True
                }]
            },
            'Trigger': {
                'SetByUI': True,
                'Timer': ['20190625121212', '20190625111111'],
                'Cycle': 200,
                'KLine': True,
                'SnapShot': True,
                'Trade': True
            },
            'RunMode': {
                'SendOrder': '1',
                'SendOrder2Actual': True
            },
            'Money': {
                'UserNo': 'Q912526205',
                'InitFunds': 10000000.0,
                'TradeDirection': 0,
                'OrderQty': {
                    'Type': '1',
                    'Count': 1
                },
                'MinQty': 88,
                'Hedge': 'T',
                'Margin': {
                    'DCE|F|M|1909' : {
                    'Type': 'R',
                    'Value': 0.88
                    }
                    ...
                },
                'OpenFee': {
                    'DCE|F|M|1909' : {
                    'Type': 'F',
                    'Value': 1.0
                    }
                    ...
                },
                'CloseFee': {
                    'DCE|F|M|1909' : {
                    'Type': 'F',
                    'Value': 1.0
                    }
                    ...
                },
                'CloseTodayFee': {
                    'DCE|F|M|1909' : {
                    'Type': 'F',
                    'Value': 1.0
                    }
                    ...
                },
                'Slippage': 5.0,
            },
            'Limit': {
                'OpenTimes': -1,
                'ContinueOpenTimes': -1,
                'OpenAllowClose': 0,
                'CloseAllowOpen': 0
            },
            'WinPoint' : {
                'DCE|F|M|1909' : {
                    'StopPoint': winPoint,
                    'AddPoint': nAddTick,
                    'CoverPosOrderType': nPriceType,
                },
                ...
            },
            'StopPoint' : {
                'DCE|F|M|1909' : {
                    'StopPoint': winPoint,
                    'AddPoint': nAddTick,
                    'CoverPosOrderType': nPriceType,
                },
                ...
            },
            'FloatStopPoint' : {
                'DCE|F|M|1909' : {
                    'StartPoint': 20,
                    'StopPoint': 10,
                    'AddPoint': nAddTick,
                    'CoverPosOrderType': nPriceType,
                },
                ...
            },
            'SubQuoteContract' : ['ZCE|F|SR|001']
            'Params': {},
            'Pending': False,
        }
    '''
    def __init__(self, argDict=None):
        if argDict and isinstance(argDict, dict):
            self._metaData = deepcopy(argDict)
            return

        self._metaData = {
            'SubContract' : [],     # 订阅的合约信息，列表中的第一个合约为基准合约
            'Sample'      : {
                'SetByUI': True,  # 由界面设置
            },
            'Trigger': {    # 触发方式
                'SetByUI': True,    # 由界面设置
                'Timer': [],        # 指定时刻
                'Cycle': 0,         # 每隔固定毫秒数触发
                'KLine': False,     # K线触发
                'SnapShot': False,  # 即时行情触发
                'Trade': False,     # 交易数据触发
            },
            'RunMode': {    # 基础设置
                'SendOrder': '',            # 发单方式
                'SendOrder2Actual': False   # 运行模式-是否实盘运行
            },
            'Money': {      # 资金设置
                'UserNo': '', # 账户
                'InitFunds': 0, # 初始资金
                'TradeDirection': 0, # 交易方向
                'OrderQty': { # 默认下单量
                    'Type': '', # 1:按固定合约数; 2:按固定资金; 3:按资金比例
                    'Count': 0
                },
                'MinQty': 0,    # 最小下单量
                'Hedge': '',    # 投保标志
                'Margin': {},   # 保证金
                'OpenFee': {},  # 开仓手续费
                'CloseFee': {}, # 平仓手续费
                'CloseTodayFee': {},    # 平今手续费
                'Slippage': 0,    # 滑点损耗
            },
            'Limit': {  # 发单设置
                'OpenTimes': -1,        # 每根K线开仓次数
                'ContinueOpenTimes': -1, # 最大连续开仓次数
                'OpenAllowClose': 0, # 开仓的K线不允许反向下单
                'CloseAllowOpen': 0 # 平仓的K线不允许开仓
            },
            'WinPoint' : {},         # 止盈信息
            'StopPoint' : {},        # 止损信息
            'FloatStopPoint' : {},   # 浮动止损信息
            'StopWinKtBlack': [],    # 不触发止损止盈浮动K线类型
            'SubQuoteContract' : [], # 即时行情订阅合约列表
            'Params': {}, # 用户设置参数
            'Pending': False,  # 是否允许向实盘下单
            'Alarm': False, # 是否开启警报
            'PopOn': False, # 是否允许弹窗
            'AutoSyncPos': False, #是否自动同步持仓, 和引擎设置一致
        }

    # ----------------------- 合约/K线类型/K线周期 ----------------------
    def setBarInterval(self, contNo, barType, barInterval, sampleConfig, trigger=True, setByUI=False):
        self.setBarInfoInSample(contNo, barType, barInterval, sampleConfig, trigger, setByUI)

    def setBarInfoInSample(self, contNo, kLineType, kLineSlice, sampleConfig, trigger=True, setByUI=True):
        '''设置订阅的合约、K线类型和周期'''
        if not contNo:
            raise Exception("请确保在设置界面或者SetBarInterval方法中设置的合约编号不为空！")
            # if barType not in ('t', 'T', 'S', 'M', 'H', 'D', 'W', 'm', 'Y'):
        if kLineType not in ('T', 'M', 'D'):
            raise Exception("请确保设置的K线类型为 'T':分笔，'M':分钟，'D':日线 中的一个！")

        # 清空界面设置信息
        if (not setByUI and self._metaData['Sample']['SetByUI']) or (setByUI and not self._metaData['Sample']['SetByUI']):
            self._metaData['SubContract'] = []
            self._metaData['Sample'] = {}
            self._metaData['Sample']['SetByUI'] = False

        # 设置订阅的合约列表
        if contNo not in self._metaData['SubContract']:
            self._metaData['SubContract'].append(contNo)

        # 设置合约的K线类型和周期
        sampleDict = self.getSampleDict(kLineType, kLineSlice, sampleConfig, trigger)
        self.updateSampleDict(contNo, sampleDict)

    def deleteBarInfoInSample(self, contNo, kLineType, kLineSlice, sampleConfig, trigger=True):
        oldSampleDict = self.getSampleDict(kLineType, kLineSlice, sampleConfig, trigger)

        sample = self._metaData['Sample']
        if contNo not in sample:
            raise Exception("修改的合约/K线类型/K线周期/回测起始点信息不存在！")

        sampleDictList = sample[contNo]
        sameDict = self.getSameDictInList(oldSampleDict, sampleDictList)
        if sameDict:
            del sameDict

        if len(sample[contNo]) > 0:
            return

        # 更新订阅的合约列表
        del sample[contNo]
        subContractList = self._metaData['SubContract']
        if contNo in subContractList:
            subContractList.remove(contNo)

    def getSampleDict(self, kLineType, kLineSlice, sampleConfig, trigger=True):
        # 回测起始点信息
        kLineCount = 0
        beginTime = ''
        allK = False
        useSample = True
        if isinstance(sampleConfig, int):
            # 固定根数K线
            if sampleConfig > 0:
                kLineCount = sampleConfig
            else:
                kLineCount = 1
        elif sampleConfig == 'N':
            # 不使用K线
            kLineCount = 1
            # useSample = False
        elif isinstance(sampleConfig, str) and self.isVaildDate(sampleConfig, "%Y%m%d"):
            # 日期
            beginTime = sampleConfig
        elif sampleConfig == 'A':
            allK = True
        return {
                    'KLineType': kLineType,
                    'KLineSlice': kLineSlice,
                    'BeginTime': beginTime,    # 运算起始点-起始日期
                    'KLineCount': kLineCount,    # 运算起始点-固定根数
                    'AllK': allK,      # 运算起始点-所有K线
                    'UseSample': useSample, # 运算起始点-不执行历史K线
                    'Trigger': trigger     # 是否订阅历史K线
                }

    def setAutoSyncPos(self, conf):
        self._metaData['AutoSyncPos'] = conf['AutoSyncPos']
        
    def getAutoSyncPos(self):
        return self._metaData['AutoSyncPos']

    def isVaildDate(self, date, format):
        try:
            time.strptime(date, format)
            return True
        except:
            return False

    def updateSampleDict(self, contNo, sampleDict):
        sample = self._metaData['Sample']
        if contNo not in sample:
            sample[contNo] = [sampleDict,]
            return

        sampleList = sample[contNo]
        isExist = True if self.getSameDictInList(sampleDict, sampleList) else False
        if not isExist:
            sampleList.append(sampleDict)

    def getSameDictInList(self, sampleDict, sampleList):
        sameDict = None
        for sampleInfo in sampleList:
            isEqual = True
            for key in sampleDict.keys():
                if sampleInfo[key] != sampleDict[key]:
                    isEqual = False
                    break
            if isEqual:
                # 存在相同的字典
                sameDict = sampleInfo
                break

        return sameDict

    # ----------------------- 触发方式 ----------------------
    def setTrigger(self, type, value=None, setByUI=True):
        '''设置触发方式'''
        if type not in (1, 2, 3, 4, 5):
            raise Exception("触发方式可选的值只能 1: 即时行情触发，2: 交易数据触发，3: 每隔固定时间触发，4: 指定时刻触发 5:K线触发 是中的一个！")
        if type == 3 and value%100 != 0:
            raise Exception("当触发方式是 3: 每隔固定时间触发 时，指定的时间间隔必须是100的整数倍！")
        if type == 4:
            if not isinstance(value, list):
                raise Exception("当触发方式是 4: 指定时刻触发 时，时刻列表必须保存在一个列表中！")
            for timeStr in value:
                if len(timeStr) != 6 or not self.isVaildDate(timeStr, "%H%M%S"):
                    raise Exception("当触发方式是 4: 指定时刻触发 时，指定的时刻格式必须是HHMMSS！")

        trigger = self._metaData['Trigger']

        # if (setByUI and not trigger['SetByUI']) or (not setByUI and trigger['SetByUI']):
        #     # 清空原有Trigger设置信息
        #     trigger['SetByUI'] = setByUI
        #     trigger['SnapShot'] = False
        #     trigger['Trade'] = False
        #     trigger['Cycle'] = None
        #     trigger['Timer'] = []
        #
        # if type == 1:
        #     trigger['SnapShot'] = True
        # elif type == 2:
        #     trigger['Trade'] = True
        # elif type == 3:
        #     trigger['Cycle'] = value
        # elif type == 4:
        #     trigger['Timer'] = value
        # elif type == 5:
        #     trigger['KLine'] = True

        if type == 1:
            trigger['SnapShot'] = True
        elif type == 2:
            trigger['Trade'] = True
        elif type == 3:
            trigger['Cycle'] = value
        elif type == 4:
            for item in value:
                if item not in trigger['Timer']:
                    trigger['Timer'].append(item)
        elif type == 5:
            trigger['KLine'] = True

    def hasTimerTrigger(self):
        return bool(self._metaData['Trigger']['Timer'])

    def getTimerTrigger(self):
        return self._metaData['Trigger']['Timer']

    def hasCycleTrigger(self):
        return bool(self._metaData['Trigger']['Cycle'])

    def getCycleTrigger(self):
        return self._metaData['Trigger']['Cycle']

    def hasKLineTrigger(self):
        return bool(self._metaData['Trigger']['KLine'])

    def hasSnapShotTrigger(self):
        return bool(self._metaData['Trigger']['SnapShot'])

    def hasTradeTrigger(self):
        return bool(self._metaData['Trigger']['Trade'])

    # ----------------------- 运行模式 ----------------------
    def setActual(self):
        '''设置是否实盘运行'''
        self._metaData['RunMode']['SendOrder2Actual'] = True

    def isActualRun(self):
        '''获取是否实盘运行标志位'''
        return bool(self._metaData['RunMode']['SendOrder2Actual'])

    # ----------------------- 发单方式 ----------------------
    def setOrderWay(self, type):
        '''设置发单方式'''
        if type not in (1, 2, '1', '2'):
            raise Exception("发单方式只能选择 1: 实时发单, 2: K线稳定后发单 中的一个！")
        self._metaData['RunMode']['SendOrder'] = str(type)

    def getSendOrder(self):
        '''获取发单方式'''
        return self._metaData['RunMode']['SendOrder']

    # ----------------------- 交易账户 ----------------------
    def setUserNo(self, userNo):
        '''设置交易账户'''
        self._metaData['Money']['UserNo'] = userNo

    def getUserNo(self):
        '''获取交易使用的账户'''
        return self._metaData['Money']['UserNo']

    # ----------------------- 初始资金 ----------------------
    def setInitCapital(self, capital):
        '''设置初始资金'''
        self._metaData['Money']['InitFunds'] = capital

    def getInitCapital(self):
        '''获取初始资金'''
        return self._metaData['Money']['InitFunds']

    # ----------------------- 交易方向 ----------------------
    def setTradeDirection(self, tradeDirection):
        '''设置交易方向'''
        if tradeDirection not in (0, 1, 2):
            raise Exception("交易方向只能是 0: 双向交易，1: 仅多头，2: 仅空头 中的一个！")
        self._metaData['Money']['TradeDirection'] = tradeDirection

    def getTradeDirection(self):
        '''获取交易方向'''
        return self._metaData['Money']['TradeDirection']

    # ----------------------- 默认下单量 ----------------------
    def setOrderQty(self, type, count):
        '''设置默认下单量'''
        self._metaData['Money']['OrderQty']['Type'] = type
        self._metaData['Money']['OrderQty']['Count'] = count

    def getOrderQtyType(self):
        '''设置默认下单量类型'''
        return self._metaData['Money']['OrderQty']['Type']

    def getOrderQtyCount(self):
        '''设置默认下单量数量'''
        return self._metaData['Money']['OrderQty']['Count']

    # ----------------------- 最小下单量 ----------------------
    def setMinQty(self, minQty):
        '''设置最小下单量'''
        if minQty <= 0:
            raise Exception("最小下单量必须为正数！")

        self._metaData['Money']['MinQty'] = minQty

    def getMinQty(self):
        '''获取最小下单量'''
        return self._metaData['Money']['MinQty']

    # ----------------------- 投保标志 ----------------------
    def setHedge(self, hedge):
        '''设置投保标志'''
        if hedge not in ('T', 'B', 'S', 'M'):
            raise Exception("投保标志只能是 'T': 投机，'B': 套保，'S': 套利，'M': 做市 中的一个！")

        self._metaData['Money']['Hedge'] = hedge

    def getHedge(self):
        '''获取投保标志'''
        return self._metaData['Money']['Hedge']

    # ----------------------- 保证金 ----------------------
    def setMargin(self, type, value, contNo=''):
        '''设置保证金的类型及比例/额度'''
        if value < 0 or type not in (EEQU_FEE_TYPE_RATIO, EEQU_FEE_TYPE_FIXED):
            raise Exception("保证金类型只能是 'R': 按比例收取，'F': 按定额收取 中的一个，并且保证金比例/额度不能小于0！")

        if contNo not in self._metaData['Money']['Margin']:
            self._metaData['Money']['Margin'][contNo] = {}

        self._metaData['Money']['Margin'][contNo]['Type'] = type
        self._metaData['Money']['Margin'][contNo]['Value'] = value
        return 0

    def getMarginType(self, contNo=''):
        '''获取保证金类型'''
        if not contNo:
            contNo = self.getBenchmark()

        if contNo not in self._metaData['Money']['Margin']:
            #raise Exception("请确保为合约%s设置了保证金类型！"%contNo)
            return self._metaData['Money']['Margin']['']['Type']

        return self._metaData['Money']['Margin'][contNo]['Type']

    def getMarginValue(self, contNo=''):
        '''获取保证金比例值'''
        if not contNo:
            contNo = self.getBenchmark()

        if contNo not in self._metaData['Money']['Margin']:
            #raise Exception("请确保为合约%s设置了保证金比例/额度！"%contNo)
            return self._metaData['Money']['Margin']['']['Value']

        return self._metaData['Money']['Margin'][contNo]['Value']

    # ----------------------- 交易手续费 ----------------------
    def setTradeFee(self, type, feeType, feeValue, contNo=''):
        '''设置交易手续费'''
        if not contNo:
            contNo = self.getBenchmarkNo()
            
        typeMap = {
            'A': ('OpenFee', 'CloseFee', 'CloseTodayFee'),
            'O': ('OpenFee',),
            'C': ('CloseFee',),
            'T': ('CloseTodayFee',),
        }
        if type not in typeMap:
            raise Exception("手续费类型只能取 'A': 全部，'O': 开仓，'C': 平仓，'T': 平今 中的一个！")

        if feeType not in (EEQU_FEE_TYPE_RATIO, EEQU_FEE_TYPE_FIXED):
            raise Exception("手续费收取方式只能取 'R': 按比例收取，'F': 按定额收取 中的一个！")

        keyList = typeMap[type]
        for key in keyList:
            feeDict = self._metaData['Money'][key]
            if contNo not in feeDict:
                feeDict[contNo] = {}
            #print("[0000000000]SetTradeFee:%s" %feeDict)    
            feeDict[contNo]['Type'] = feeType
            feeDict[contNo]['Value'] = feeValue
            #print("[11111111]SetTradeFee:%s" %feeDict)
             
        return 0

    def getRatioOrFixedFee(self, feeType, isRatio, contNo=''):
        '''获取 开仓/平仓/今平 手续费率或固定手续费'''
        if not contNo:
            contNo = self.getBenchmarkNo()
        
        typeDict = {'OpenFee':'开仓', 'CloseFee':'平仓', 'CloseTodayFee':'平今'}
        if feeType not in typeDict:
            return 0

        openFeeType = EEQU_FEE_TYPE_RATIO if isRatio else EEQU_FEE_TYPE_FIXED
        if contNo not in self._metaData['Money'][feeType]:
            contList = list(self._metaData['Money'][feeType].keys())
            if len(contList) > 0:
                contNo = contList[0]
            else:
                raise Exception("请确保为合约%s设置了%s手续费！"%(contNo, typeDict[feeType]))

        return self._metaData['Money'][feeType][contNo]['Value'] if self._metaData['Money'][feeType][contNo]['Type'] == openFeeType else 0

    def getOpenRatio(self, contNo=''):
        '''获取开仓手续费率'''
        return self.getRatioOrFixedFee('OpenFee', True, contNo)

    def getOpenFixed(self, contNo=''):
        '''获取开仓固定手续费'''
        return self.getRatioOrFixedFee('OpenFee', False, contNo)

    def getCloseRatio(self, contNo=''):
        '''获取平仓手续费率'''
        return self.getRatioOrFixedFee('CloseFee', True, contNo)

    def getCloseFixed(self, contNo=''):
        '''获取平仓固定手续费'''
        return self.getRatioOrFixedFee('CloseFee', False, contNo)

    def getCloseTodayRatio(self, contNo=''):
        '''获取今平手续费率'''
        return self.getRatioOrFixedFee('CloseTodayFee', True, contNo)

    def getCloseTodayFixed(self, contNo=''):
        '''获取今平固定手续费'''
        return self.getRatioOrFixedFee('CloseTodayFee', False, contNo)

    # ----------------------- 滑点损耗 ----------------------
    def setSlippage(self, slippage):
        '''设置滑点损耗'''
        self._metaData['Money']['Slippage'] = slippage

    def getSlippage(self):
        '''滑点损耗'''
        return self._metaData['Money']['Slippage']

    # ----------------------- 发单设置 ----------------------
    def setLimit(self, openTimes, continueOpenTimes, openAllowClose, closeAllowOpen):
        '''设置发单参数'''
        limitDict = self._metaData['Limit']
        limitDict['OpenTimes'] = openTimes          # 每根K线开仓次数
        limitDict['ContinueOpenTimes'] = continueOpenTimes  # 最大连续开仓次数
        limitDict['OpenAllowClose'] = openAllowClose    # 开仓的K线不允许反向下单
        limitDict['CloseAllowOpen'] = closeAllowOpen    # 平仓的K线不允许开仓

    def getLimit(self):
        '''获取发单设置'''
        return self._metaData['Limit']

    # ----------------------- 止盈信息 ----------------------
    def setWinPoint(self, winPoint, nPriceType, nAddTick, contractNo):
        '''设置止盈信息'''
        if nPriceType not in (0, 1, 2, 3, 4):
            raise Exception("设置止盈点平仓下单价格类型必须为 0: 最新价，1：对盘价，2：挂单价，3：市价，4：停板价 中的一个！")

        if nAddTick not in (0, 1, 2):
            raise Exception("止盈点的超价点数仅能为0，1，2中的一个！")

        self._metaData['WinPoint'][contractNo] = {
            "StopPoint": winPoint,
            "AddPoint": nAddTick,
            "CoverPosOrderType": nPriceType,
            "StopType": '0',
        }

    def setStopWinKtBlack(self, op, kt):
        if kt not in ('D', 'M', 'T'):
            raise Exception("设置的K线类型必须为 'D', 'M', 'T'中的一个")
            
        if op not in (0, 1):
            raise Exception("设置的操作类型必须为 0: 取消, 1: 增加 中的一个")
            
        if op == 0:
            if kt in self._metaData["StopWinKtBlack"]:
                self._metaData["StopWinKtBlack"].remove(kt)
        else:
            if kt not in self._metaData["StopWinKtBlack"]:
                self._metaData["StopWinKtBlack"].append(kt)
                
        return 0
                
    def getStopWinKtBlack(self):
        return self._metaData["StopWinKtBlack"]
            
    def getStopWinParams(self, contractNo=None):
        '''获取止盈信息'''
        contNo = self.getBenchmark() if not contractNo else contractNo

        if contNo not in self._metaData['WinPoint']:
            return None

        return self._metaData['WinPoint'][contNo]
    # ----------------------- 止损信息 ----------------------
    def setStopPoint(self, stopPoint, nPriceType, nAddTick, contractNo):
        '''设置止损信息'''
        if nPriceType not in (0, 1, 2, 3, 4):
            raise Exception("设置止损点平仓下单价格类型必须为 0: 最新价，1：对盘价，2：挂单价，3：市价，4：停板价 中的一个！")

        if nAddTick not in (0, 1, 2):
            raise Exception("止损点的超价点数仅能为0，1，2中的一个！")

        self._metaData['StopPoint'][contractNo] = {
            "StopPoint": stopPoint,
            "AddPoint": nAddTick,
            "CoverPosOrderType": nPriceType,
            "StopType": '1',
        }

    def getStopLoseParams(self, contractNo=None):
        '''获取止损信息'''
        contNo = self.getBenchmark() if not contractNo else contractNo

        if contNo not in self._metaData['StopPoint']:
            return None

        return self._metaData['StopPoint'][contNo]

    # ----------------------- 浮动止损信息 ----------------------
    def setFloatStopPoint(self, startPoint, stopPoint, nPriceType, nAddTick, contractNo):
        '''设置止损信息'''
        if nPriceType not in (0, 1, 2, 3, 4):
            raise Exception("设置止损点平仓下单价格类型必须为 0: 最新价，1：对盘价，2：挂单价，3：市价，4：停板价 中的一个！")

        if nAddTick not in (0, 1, 2):
            raise Exception("止损点的超价点数仅能为0，1，2中的一个！")

        self._metaData['FloatStopPoint'][contractNo] = {
            "StartPoint" : startPoint,
            "StopPoint": stopPoint,
            "AddPoint": nAddTick,
            "CoverPosOrderType": nPriceType,
            "StopType": '1', 
        }

    def getFloatStopPoint(self, contractNo=None):
        contractNo = self.getBenchmark() if not contractNo else contractNo
        if contractNo not in self._metaData['FloatStopPoint']:
            return None

        return self._metaData['FloatStopPoint'][contractNo]

    # ----------------------- 用户设置参数 ----------------------
    def setParams(self, params):
        '''设置用户设置参数'''
        self._metaData["Params"] = params

    def getParams(self):
        '''获取用户设置参数'''
        if "Params" not in self._metaData:
            return {}
        return self._metaData["Params"]

    # ----------------------- 允许实盘交易 ----------------------
    def setPending(self, pending):
        '''设置是否暂停向实盘下单标志'''
        self._metaData['Pending'] = pending

    def getPending(self):
        '''获取是否暂停向实盘下单标志'''
        return self._metaData['Pending']

    # ----------------------- 警报开关状态 ----------------------
    def setAlarm(self, alarmOn):
        '''设置警报开关'''
        self._metaData['Alarm'] = alarmOn
    # ----------------------  允许弹窗 --------------------------
    def setPop(self, popOn):
        '''设置允许弹窗开关'''
        self._metaData["PopOn"] = popOn

    def getAlarm(self):
        '''获取警报开启状态'''
        return bool(self._metaData['Alarm'])
        
    def getPop(self):
        return bool(self._metaData['PopOn'])
        
    # --------------------- 订阅/退订即时行情 --------------------
    def updateSubQuoteContract(self, contNoList):
        pass

    def updateUnsubQuoteContract(self, contNoList):
        pass

    # -----------------------------------------------------------
    def getConfig(self):
        return self._metaData

    def getBenchmark(self):
        '''获取基准合约'''
        # 1、取界面设置的第一个合约 2、取SetBarinterval第一个设置的合约
        subContract = self._metaData['SubContract']
        if not subContract or len(subContract) == 0:
            raise Exception("请确保在设置界面或者在策略中调用SetBarInterval方法设置展示的合约、K线类型和周期")

        return subContract[0]
        
    def getBenchmarkNo(self):
        '''获取基准合约'''
        # 1、取界面设置的第一个合约 2、取SetBarinterval第一个设置的合约
        subContract = self._metaData['SubContract']
        if not subContract or len(subContract) == 0:
            return 'Default'

        return subContract[0]

    def getTriggerContract(self):
        return self._metaData['SubContract']

    def getSampleInfo(self):
        kLineTypetupleList = []
        kLineTypeDictList = []
        subDict = {}
        for contNo in self._metaData['Sample']:
            barList = self._metaData['Sample'][contNo]
            if not isinstance(barList, list):
                continue
            for barInfo in barList:
                triggerTuple = (contNo, barInfo['KLineType'], barInfo['KLineSlice'])
                if triggerTuple not in kLineTypetupleList:
                    kLineTypetupleList.append(triggerTuple)
                    kLineTypeDictList.append({"ContractNo": contNo, "KLineType": barInfo['KLineType'], "KLineSlice": barInfo['KLineSlice']})

                if barInfo['UseSample']:
                    # 需要订阅历史K线
                    sampleInfo = self._getKLineCount(barInfo)
                    subDict[triggerTuple] = {"ContractNo": contNo, "KLineType": barInfo['KLineType'], "KLineSlice": barInfo['KLineSlice'], "BarCount": sampleInfo}
                elif triggerTuple in subDict:
                    # 不需要
                    del subDict[triggerTuple]

        return kLineTypetupleList, kLineTypeDictList, subDict

    def _getKLineCount(self, sampleDict):
        if not sampleDict['UseSample']:
            return 1

        if sampleDict['KLineCount'] > 0:
            return sampleDict['KLineCount']

        if len(sampleDict['BeginTime']) > 0:
            return sampleDict['BeginTime']

        if sampleDict['AllK']:
            nowDateTime = datetime.now()
            if self.getKLineType() == EEQU_KLINE_DAY:
                threeYearsBeforeDateTime = nowDateTime - relativedelta(years=3)
                threeYearsBeforeStr = datetime.strftime(threeYearsBeforeDateTime, "%Y%m%d")
                return threeYearsBeforeStr
            elif self.getKLineType() == EEQU_KLINE_HOUR or self.getKLineType() == EEQU_KLINE_MINUTE:
                oneMonthBeforeDateTime = nowDateTime - relativedelta(months=1)
                oneMonthBeforeStr = datetime.strftime(oneMonthBeforeDateTime, "%Y%m%d")
                return oneMonthBeforeStr
            elif self.getKLineType() == EEQU_KLINE_SECOND:
                oneWeekBeforeDateTime = nowDateTime - relativedelta(days=7)
                oneWeekBeforeStr = datetime.strftime(oneWeekBeforeDateTime, "%Y%m%d")
                return oneWeekBeforeStr
            else:
                raise NotImplementedError

    def getKLineSubsInfo(self):
        kLineTypetupleList, kLineTypeDictList, subDict = self.getSampleInfo()
        return subDict.values()

    def getKLineKindsInfo(self):
        kLineTypetupleList, kLineTypeDictList, subDict = self.getSampleInfo()
        for value in subDict.values():
            del value['BarCount']

        return subDict.values()

    #
    periodSize = {
        EEQU_KLINE_DAY: 24*3600,
        EEQU_KLINE_MINUTE: 60,
        EEQU_KLINE_TICK: 1,
    }
    def getKLineTriggerInfoSimple(self):
        if hasattr(self, "_triggerKLine"):
            return getattr(self, "_triggerKLine")
        kLineTypetupleList, kLineTypeDictList, subDict = self.getSampleInfo()

        result = {}
        for key in kLineTypetupleList:
            result.setdefault(key[0], key)
            lastKey = result.get(key[0])
            if self.periodSize[key[1]]*key[2] < self.periodSize[lastKey[1]]*lastKey[2]:
                result[key[0]] = key

        setattr(self, "_triggerKLine", set(result.values()))
        return getattr(self, "_triggerKLine")


    def getKLineShowInfo(self):
        displayCont = self.getBenchmark()
        kLineInfo = self._metaData['Sample'][displayCont][0]

        return {
            'ContractNo': displayCont,
            'KLineType': kLineInfo['KLineType'],
            'KLineSlice': kLineInfo['KLineSlice']
        }

    def getKLineShowInfoSimple(self):
        showInfoSimple = []
        showInfo = self.getKLineShowInfo()
        for value in showInfo.values():
            showInfoSimple.append(value)

        return tuple(showInfoSimple)

    priorityDict = {
        EEQU_KLINE_DAY: 50000,
        EEQU_KLINE_MINUTE: 30000,
        EEQU_KLINE_TICK: 10000,

    }

    def getPriority(self, key):
        kLineKindsInfo = self.getKLineKindsInfo()
        kLineTypetupleList = [(record["ContractNo"], record["KLineType"], record["KLineSlice"]) for record in kLineKindsInfo]
        return len(kLineTypetupleList)-kLineTypetupleList.index(key) + self.priorityDict[key[1]] + int(key[2])

    def getContract(self):
        '''获取合约列表'''
        return self._metaData['SubContract']

    def getKLineType(self):
        '''获取K线类型'''
        kLineInfo = self.getKLineShowInfo()
        if 'KLineType' in kLineInfo:
            return kLineInfo['KLineType']

    def getKLineSlice(self):
        '''获取K线间隔'''
        kLineInfo = self.getKLineShowInfo()
        if 'KLineSlice' in kLineInfo:
            return kLineInfo['KLineSlice']

    def getDefaultKey(self):
        '''获取基准合约配置'''
        showInfo = self.getKLineShowInfo()
        return (showInfo['ContractNo'], showInfo['KLineType'], showInfo['KLineSlice'])