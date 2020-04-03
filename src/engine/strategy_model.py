import numpy as np
from capi.com_types import *
from .engine_model import *
import talib
import time, sys
import math
import pandas as pd
from .strategy_cfg_model_new import StrategyConfig_new
from .strategy_his_model import StrategyHisQuote
from .strategy_qte_model import StrategyQuote
from .strategy_trd_model import StrategyTrade
from .statistics_model import StatisticsModel
import copy

from engine.calc import CalcCenter
from datetime import datetime, timedelta
from .popup_win import *
import winsound


class StrategyModel(object):
    def __init__(self, strategy):
        self._strategy = strategy
        self.logger = strategy.logger
        self._argsDict = strategy._argsDict

        self._strategyName = strategy.getStrategyName()
        self._signalName = self._strategyName + "_Signal"
        self._textName = self._strategyName + "_Text"
        self._plotedDict = {}

        # Notice：会抛异常
        self._cfgModel = StrategyConfig_new(self._argsDict)
        self._config = self._cfgModel
        # 回测计算
        self._calcCenter = CalcCenter(self.logger, self)

        self._qteModel = StrategyQuote(strategy, self._cfgModel)
        self._hisModel = StrategyHisQuote(strategy, self._cfgModel, self._calcCenter, self)
        self._trdModel = StrategyTrade(strategy, self._cfgModel)
        self._staModel = StatisticsModel(strategy, self._cfgModel)
        
        self._bsMap = {dBuy : '买', dSell: '卖', dBoth: '双边'}
        self._ocMap = {oNone: '无', oOpen: '开仓', oCover: '平仓', oCoverT: '平今', oOpenCover: '开平', oCoverOpen: '平开'}
        
        
        self._audioDict = {
            'Signal' : r'./audio/Signal.wav',
            'Info'   : r'./audio/Info.wav',
            'Warn'   : r'./audio/Warn.wav',
            'Error'   : r'./audio/Error.wav',
        }
        

    def setRunStatus(self, status):
        self._runStatus = status

    def getTradeModel(self):
        return self._trdModel

    def getConfigData(self):
        return self._cfgModel.getConfig()

    def getConfigTimer(self):
        return self._cfgModel.getTimerTrigger()

    def getConfigCycle(self):
        return self._cfgModel.getCycleTrigger()

    def getConfigModel(self):
        return self._cfgModel

    def getHisQuoteModel(self):
        return self._hisModel

    def getMonResult(self):
        return self._calcCenter.getMonResult()

    def getQuoteModel(self):
        return self._qteModel

    # +++++++++++++++++++++++内部接口++++++++++++++++++++++++++++
    def getCalcCenter(self):
        return self._calcCenter

    def initialize(self):
        '''加载完策略初始化函数之后再初始化'''
        self._hisModel.initialize()
        self._trdModel.initialize()

    def initializeCalc(self):
        contNo = self._cfgModel.getBenchmark()
        strategyParam = {
            "InitialFunds": float(self._cfgModel.getInitCapital()),  # 初始资金
            "StrategyName": self._strategy.getStrategyName(),  # 策略名称
            "StartTime": "2019-04-01",  # 回测开始时间
            "EndTime": "2019-04-17",  # 回测结束时间
            "Margin": self._cfgModel.getMarginValue(),  # 保证金
            "Slippage": self._cfgModel.getSlippage(),  # 滑点
            "OpenRatio": self._cfgModel.getOpenRatio(),
            "CloseRatio": self._cfgModel.getCloseRatio(),
            "OpenFixed": self._cfgModel.getOpenFixed(),
            "CloseFixed": self._cfgModel.getCloseFixed(),
            "CloseTodayRatio": self._cfgModel.getCloseTodayRatio(),
            "CloseTodayFixed": self._cfgModel.getCloseTodayFixed(),
            "KLineType": self._hisModel._getKLineType(),
            "KLineSlice": self._hisModel._getKLineSlice(),
            "TradeDot": self.getContractUnit(contNo),  # 每手乘数
            "PriceTick": self.getPriceScale(contNo),  # 最小变动价位
            "Limit": self._config.getLimit(),
        }
        self._calcCenter.initArgs(strategyParam)

    # ++++++++++++++++++++++策略接口++++++++++++++++++++++++++++++
    # //////////////////////历史行情接口//////////////////////////
    def runReport(self, context, handle_data):
        self._hisModel.runReport(context, handle_data)

    def runRealTime(self, context, handle_data, event):
        code = event.getEventCode()
        if code == ST_TRIGGER_FILL_DATA:
            self._hisModel.runFillData(context, handle_data, event)
        elif code == ST_TRIGGER_HIS_KLINE:
            self._hisModel.runVirtualReport(context, handle_data, event)
        else:
            self._hisModel.runRealTime(context, handle_data, event)

    # ////////////////////////配置接口////////////////////////////
    def continueTrigger(self):
        return self._cfgModel.continues()

    # ++++++++++++++++++++++base api接口++++++++++++++++++++++++++
    # ////////////////////////K线函数/////////////////////////////
    def getKey(self, contNo, kLineType, kLineValue):
        # 空合约取默认展示的合约
        if contNo == "" or kLineType == '' or kLineValue == 0:
            return self._cfgModel.getDefaultKey()

        # if contNo not in 合约没有订阅
        if kLineType not in (EEQU_KLINE_TIMEDIVISION, EEQU_KLINE_TICK,
                             EEQU_KLINE_SECOND, EEQU_KLINE_MINUTE,
                             EEQU_KLINE_HOUR, EEQU_KLINE_DAY,
                             EEQU_KLINE_WEEK, EEQU_KLINE_MONTH,
                             EEQU_KLINE_YEAR):
            raise Exception("输入K线类型异常，请参阅枚举函数-周期类型枚举函数")
        if not isinstance(kLineValue, int) or kLineValue < 0:
            raise Exception("输入K线周期异常，请确保输入的K线周期是正整数")
        return (contNo, kLineType, kLineValue)

    def getBarOpenInt(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        return self._hisModel.getBarOpenInt(multiContKey)

    def getBarTradeDate(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        return self._hisModel.getBarTradeDate(multiContKey)

    def getBarCount(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        return self._hisModel.getBarCount(multiContKey)

    def getCurrentBar(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        curBar = self._hisModel.getCurBar(multiContKey)
        if not curBar:
            return -1
        return curBar['KLineIndex']

    def getCurrentBarEntity(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        curBar = self._hisModel.getCurBar(multiContKey)
        return curBar

    def getBarStatus(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        return self._hisModel.getBarStatus(multiContKey)

    def isHistoryDataExist(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        return self._hisModel.isHistoryDataExist(multiContKey)

    def getBarDate(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        return self._hisModel.getBarDate(multiContKey)

    def getBarTime(self, contNo, kLineType, kLineValue):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        return self._hisModel.getBarTime(multiContKey)

    def getBarOpen(self, contractNo, kLineType, kLineValue):
        multiContKey = self.getKey(contractNo, kLineType, kLineValue)
        return self._hisModel.getBarOpen(multiContKey)

    def getBarClose(self, contractNo, kLineType, kLineValue):
        multiContKey = self.getKey(contractNo, kLineType, kLineValue)
        return self._hisModel.getBarClose(multiContKey)

    def getOpenD(self, daysAgo, contractNo):
        contNo = self._cfgModel.getBenchmark() if not contractNo else contractNo
        multiContKey = self.getKey(contNo, 'D', 1)
        return self._hisModel.getOpenD(daysAgo, multiContKey)

    def getCloseD(self, daysAgo, contractNo):
        contNo = self._cfgModel.getBenchmark() if not contractNo else contractNo
        multiContKey = self.getKey(contNo, 'D', 1)
        return self._hisModel.getCloseD(daysAgo, multiContKey)

    def getHighD(self, daysAgo, contractNo):
        contNo = self._cfgModel.getBenchmark() if not contractNo else contractNo
        multiContKey = self.getKey(contNo, 'D', 1)
        return self._hisModel.getHighD(daysAgo, multiContKey)

    def getLowD(self, daysAgo, contractNo):
        contNo = self._cfgModel.getBenchmark() if not contractNo else contractNo
        multiContKey = self.getKey(contNo, 'D', 1)
        return self._hisModel.getLowD(daysAgo, multiContKey)

    def getBarVol(self, contractNo, kLineType, kLineValue):
        multiContKey = self.getKey(contractNo, kLineType, kLineValue)
        return self._hisModel.getBarVol(multiContKey)

    def getBarHigh(self, contractNo, kLineType, kLineValue):
        multiContKey = self.getKey(contractNo, kLineType, kLineValue)
        return self._hisModel.getBarHigh(multiContKey)

    def getBarLow(self, contractNo, kLineType, kLineValue):
        multiContKey = self.getKey(contractNo, kLineType, kLineValue)
        return self._hisModel.getBarLow(multiContKey)

    def getHisData(self, dataType, kLineType, kLineValue, contractNo, maxLength):
        multiContKey = self.getKey(contractNo, kLineType, kLineValue)
        return self._hisModel.getHisData(dataType, multiContKey, maxLength)

    def getHisBarsInfo(self, contNo, kLineType, kLineValue, maxLength):
        multiContKey = self.getKey(contNo, kLineType, kLineValue)
        return self._hisModel.getHisBarsInfo(multiContKey, maxLength)

    def getBarsLast(self, condition):
        conLen = len(condition)
        if conLen == 0:
            return 0

        count = 0
        for i in range(conLen-1, -1, -1):
            if condition[i]:
                break
            else:
                count += 1
        return count

    # ////////////////////////即时行情////////////////////////////
    def subQuoteList(self, contNoList):
        self._qteModel.subQuoteList(contNoList)

    def unsubQuoteList(self, contNoList):
        # TODO: 退订即使行情时，是否需要删除已经得到的即时行情信息
        self._qteModel.unsubQuoteList(contNoList)
    
    def getQUpdateTime(self, symbol):
        return self._qteModel.getQUpdateTime(symbol)

    def getQAskPrice(self, symbol, level):
        return self._qteModel.getQAskPrice(symbol, level)

    def getQAskPriceFlag(self, symbol):
        return self._qteModel.getQAskPriceFlag(symbol)

    def getQAskVol(self, symbol, level):
        return self._qteModel.getQAskVol(symbol, level)

    def getQAvgPrice(self, symbol):
        return self._qteModel.getQAvgPrice(symbol)

    def getQBidPrice(self, symbol, level):
        return self._qteModel.getQBidPrice(symbol, level)

    def getQBidPriceFlag(self, symbol):
        return self._qteModel.getQBidPriceFlag(symbol)

    def getQBidVol(self, symbol, level):
        return self._qteModel.getQBidVol(symbol, level)

    def getQClose(self, symbol):
        return self._qteModel.getQClose(symbol)

    def getQHigh(self, symbol):
        return self._qteModel.getQHigh(symbol)

    def getQHisHigh(self, symbol):
        return self._qteModel.getQHisHigh(symbol)

    def getQHisLow(self, symbol):
        return self._qteModel.getQHisLow(symbol)

    def getQInsideVol(self, symbol):
        return self._qteModel.getQInsideVol(symbol)

    def getQLast(self, symbol):
        return self._qteModel.getQLast(symbol)

    def getQLastDate(self, symbol):
        symbol = self._config.getBenchmark() if not symbol else symbol
        key = None
        for keyTuple in self._hisModel._kLineNoticeData.keys():
            if keyTuple[0] == symbol and keyTuple[1] == 'T':
                key = keyTuple
                break
        if not key:
            raise Exception(
                "在使用Q_LastDate方法时，请确保已经在设置界面或者在策略代码中添加了SetBarInterval('%s', 'T', 1)为合约%s订阅了Tick行情！" % (symbol, symbol))
        tickInfo = self._hisModel.getLastStoredKLine(key)[0]
        dateTimeStamp = tickInfo['DateTimeStamp']
        return int(dateTimeStamp) // 1000000000

    def getQLastTime(self, symbol):
        symbol = self._config.getBenchmark() if not symbol else symbol
        key = None
        for keyTuple in self._hisModel._kLineNoticeData.keys():
            if keyTuple[0] == symbol and keyTuple[1] == 'T':
                key = keyTuple
                break
        if not key:
            raise Exception(
                "在使用Q_LastTime方法时，请确保已经在设置界面或者在策略代码中添加了SetBarInterval('%s', 'T', 1)为合约%s订阅了Tick行情！" % (symbol, symbol))
        tickInfo = self._hisModel.getLastStoredKLine(key)[0]
        dateTimeStamp = tickInfo['DateTimeStamp']
        return float(int(dateTimeStamp) % 1000000000) / 1000000000

    def getQLastVol(self, symbol):
        return self._qteModel.getQLastVol(symbol)

    def getQLow(self, symbol):
        return self._qteModel.getQLow(symbol)

    def getQLowLimit(self, symbol):
        return self._qteModel.getQLowLimit(symbol)

    def getQOpen(self, symbol):
        return self._qteModel.getQOpen(symbol)

    def getQOpenInt(self, symbol):
        return self._qteModel.getQOpenInt(symbol)

    def getQOpenIntFlag(self, symbol):
        return self._qteModel.getQOpenIntFlag(symbol)

    def getQOutsideVol(self, symbol):
        return self._qteModel.getQOutsideVol(symbol)

    def getQPreOpenInt(self, symbol):
        return self._qteModel.getQPreOpenInt(symbol)

    def getQPreSettlePrice(self, symbol):
        return self._qteModel.getQPreSettlePrice(symbol)

    def getQPriceChg(self, symbol):
        return self._qteModel.getQPriceChg(symbol)

    def getQPriceChgRadio(self, symbol):
        return self._qteModel.getQPriceChgRadio(symbol)

    def getQTodayEntryVol(self, symbol):
        return self._qteModel.getQTodayEntryVol(symbol)

    def getQTodayExitVol(self, symbol):
        return self._qteModel.getQTodayExitVol(symbol)

    def getQTotalVol(self, symbol):
        return self._qteModel.getQTotalVol(symbol)

    def getQTurnOver(self, symbol):
        return self._qteModel.getQTurnOver(symbol)

    def getQUpperLimit(self, symbol):
        return self._qteModel.getQUpperLimit(symbol)

    def getQTheoryPrice(self, symbol):
        return self._qteModel.getQTheoryPrice(symbol)

    def getQSigma(self, symbol):
        return self._qteModel.getQSigma(symbol)

    def getQDelta(self, symbol):
        return self._qteModel.getQDelta(symbol)
        
    def getQGamma(self, symbol):
        return self._qteModel.getQGamma(symbol)
        
    def getQVega(self, symbol):
        return self._qteModel.getQVega(symbol)
        
    def getQTheta(self, symbol):
        return self._qteModel.getQTheta(symbol)
    
    def getQRho(self, symbol):
        return self._qteModel.getQRho(symbol)

    def getQuoteDataExist(self, symbol):
        return self._qteModel.getQuoteDataExist(symbol)

    # ////////////////////////策略函数////////////////////////////
    def setBuy(self, userNo, contractNo, share, price, needCover=True, orderType=otLimit):
        if self._cfgModel.getTradeDirection() == 2:
            return
        
        contNo = contractNo if contractNo else self._cfgModel.getBenchmark()
        
        if contNo not in self._cfgModel.getContract():
            raise Exception(f"请先在设置界面获知使用SetBarInterval方法订阅 {contNo} 合约！")

        underlayContNo = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayContNo) > 0:
            contNo = underlayContNo

        if share <= 0:
            share = self.getDefaultShare(contNo, price)
        defaultPrice = self._qteModel.getQLast(contNo) if price <= 0 else -1

        # 非K线触发的策略，不使用Bar
        curBar = None
        # 计算考虑滑点损耗后的价格
        if defaultPrice > 0:
            price = defaultPrice
        price = self._calcCenter.calcOrderPrice(contNo, dBuy, price)

        userNo = self._cfgModel.getUserNo() if not userNo else userNo
        if not userNo:
            userNo = "Default"
        # 对于开仓，需要平掉反向持仓
        qty = self._calcCenter.needCover(userNo, contNo, dBuy, share, price)
        exchg = contNo.split('|')[0]
        if qty > 0:
            if exchg in ('ZCE', 'DCE', 'SHFE', 'INE', 'CFFEX'):
                if needCover:
                    self.buySellOrder(userNo, contNo, orderType, vtGFD, dBuy, oCoverA, hSpeculate, price, qty, curBar, (defaultPrice > 0))
            else:
                self.buySellOrder(userNo, contNo, orderType, vtGFD, dBuy, oCoverA, hSpeculate, price, qty, curBar, (defaultPrice > 0))
            
        # 交易计算、生成回测报告
        self.buySellOrder(userNo, contNo, orderType, vtGFD, dBuy, oOpen, hSpeculate, price, share, curBar, (defaultPrice > 0))

    def setBuyToCover(self, userNo, contractNo, share, price, coverFlag='A', orderType=otLimit):
        if self._cfgModel.getTradeDirection() == 1:
            return
    
        contNo = contractNo if contractNo is not None else self._cfgModel.getBenchmark()

        if contNo not in self._cfgModel.getContract():
            raise Exception(f"请先在设置界面获知使用SetBarInterval方法订阅 {contNo} 合约！")

        underlayContNo = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayContNo) > 0:
            contNo = underlayContNo

        if share <= 0:
            share = self.getDefaultShare(contNo, price)
        defaultPrice = self._qteModel.getQLast(contNo) if price <= 0 else -1

        curBar = None

        # 计算考虑滑点损耗后的价格
        if defaultPrice > 0:
            price = defaultPrice
        price = self._calcCenter.calcOrderPrice(contNo, dBuy, price)

        userNo = self._cfgModel.getUserNo() if not userNo else userNo
        if not userNo:
            userNo = "Default"

        # 交易计算、生成回测报告
        self.buySellOrder(userNo, contNo, orderType, vtGFD, dBuy, coverFlag, hSpeculate,price, share, curBar, (defaultPrice > 0))


    def setSell(self, userNo, contractNo, share, price, coverFlag='A', orderType=otLimit):
        if self._cfgModel.getTradeDirection() == 1:
            return
    
        contNo = contractNo if contractNo is not None else self._cfgModel.getBenchmark()

        if contNo not in self._cfgModel.getContract():
            raise Exception(f"请先在设置界面获知使用SetBarInterval方法订阅 {contNo} 合约！")

        underlayContNo = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayContNo) > 0:
            contNo = underlayContNo

        if share <= 0:
            share = self.getDefaultShare(contNo, price)
        defaultPrice = self._qteModel.getQLast(contNo) if price <= 0 else -1

        curBar = None

        # 计算考虑滑点损耗后的价格
        if defaultPrice > 0:
            price = defaultPrice
        price = self._calcCenter.calcOrderPrice(contNo, dSell, price)

        userNo = self._cfgModel.getUserNo() if not userNo else userNo
        if not userNo:
            userNo = "Default"
            
        # 交易计算、生成回测报告
        self.buySellOrder(userNo, contNo, orderType, vtGFD, dSell, coverFlag, hSpeculate, price, share, curBar, (defaultPrice > 0))

    def setSellShort(self, userNo, contractNo, share, price, needCover=True, orderType=otLimit):
        if self._cfgModel.getTradeDirection() == 2:
            return
    
        contNo = contractNo if contractNo is not None else self._cfgModel.getBenchmark()

        if contNo not in self._cfgModel.getContract():
            raise Exception(f"请先在设置界面获知使用SetBarInterval方法订阅 {contNo} 合约！")

        underlayContNo = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayContNo) > 0:
            contNo = underlayContNo

        if share <= 0:
            share = self.getDefaultShare(contNo, price)
        defaultPrice = self._qteModel.getQLast(contNo) if price <= 0 else -1

        curBar = None

        # 计算考虑滑点损耗后的价格
        if defaultPrice > 0:
            price = defaultPrice
        price = self._calcCenter.calcOrderPrice(contNo, dSell, price)

        userNo = self._cfgModel.getUserNo() if not userNo else userNo
        if not userNo:
            userNo = "Default"
        qty = self._calcCenter.needCover(userNo, contNo, dSell, share, price)
        exchg = contNo.split('|')[0]
        if qty > 0:
            if exchg in ('ZCE', 'DCE', 'SHFE', 'INE', 'CFFEX'):
                if needCover:
                    self.buySellOrder(userNo, contNo, orderType, vtGFD, dSell, oCoverA, hSpeculate, price, qty, curBar, (defaultPrice > 0))
            else:
                self.buySellOrder(userNo, contNo, orderType, vtGFD, dSell, oCoverA, hSpeculate, price, qty, curBar, (defaultPrice > 0))
        
        # 交易计算、生成回测报告
        self.buySellOrder(userNo, contNo, orderType, vtGFD, dSell, oOpen, hSpeculate,price, share, curBar, (defaultPrice > 0))

    def getDefaultShare(self, contNo, price):
        defaultPrice = self._qteModel.getQLast(contNo)
        defaultOrderType = self._cfgModel.getOrderQtyType()
        minQty = self._cfgModel.getMinQty()

        if defaultOrderType == '1':
            # 按固定合约数
            defaultShare = self._cfgModel.getOrderQtyCount()
            # 异常处理
            if defaultShare < minQty:
                raise Exception(f"请确保您设置的默认下单量 {defaultShare} 对应的手数不小于您设置的最小下单量 {minQty} ！")
            fixCapital = self._calcCenter.getAvailableFund()
            if price <= 0:
                if fixCapital < defaultPrice * defaultShare:
                    raise Exception(f"您当前的可用资金 {fixCapital} 小于当前最新价 {defaultPrice} 与您设置的默认下单量 {defaultShare} 的乘积！")
            else:
                if fixCapital < price * defaultShare:
                    raise Exception(f"您当前的可用资金 {fixCapital} 小于您设置的价格 {price} 与您设置的默认下单量 {defaultShare} 的乘积！")
            return defaultShare
        elif defaultOrderType == '2':
            # 按固定资金
            fixCapital = self._cfgModel.getOrderQtyCount()
            # 异常处理
            if price <= 0:
                if fixCapital < defaultPrice * minQty:
                    raise Exception(f"请确保您设置的默认下单量对应的固定资金 {fixCapital} 不小于当前最新价 {defaultPrice} 与您设置的最小下单量 {minQty} 的乘积！")
            else:
                if fixCapital < price * minQty:
                    raise Exception(f"请确保您设置的默认下单量对应的固定资金 {fixCapital} 不小于您设置的价格 {price} 与您设置的最小下单量 {minQty} 的乘积！")

            return fixCapital // price if price > 0 else fixCapital // defaultPrice
        elif defaultOrderType == '3':
            # 按资金比例
            capitalRatio = self._cfgModel.getOrderQtyCount()
            fixCapital = capitalRatio * self._calcCenter.getAvailableFund()

            # 异常处理
            if price <= 0:
                if fixCapital < defaultPrice * minQty:
                    raise Exception(f"请确保您当前的资金 {fixCapital} 不小于当前最新价 {defaultPrice} 与您设置的最小下单量 {minQty} 的乘积！")
            else:
                if fixCapital < price * minQty:
                    raise Exception(f"请确保您当前的资金 {fixCapital} 不小于您设置的价格 {price} 与您设置的最小下单量 {minQty} 的乘积！")

            return fixCapital // price if price > 0 else fixCapital // defaultPrice
        return -1

    def sendFlushEvent(self):
        flushEvent = Event({
            "EventCode": EV_ST2EG_UPDATE_STRATEGYDATA,
            "StrategyId": self._strategy.getStrategyId(),
        })
        self._strategy.sendEvent2Engine(flushEvent)

    def sendSignalEvent(self, signalName, userNo, contNo, direct, offset, price, share, curBar):
        if not curBar:
            return

        data = [{
            'KLineIndex': curBar['KLineIndex'],
            'ContractNo': contNo,
            'Direct': direct,
            'Offset': offset,
            'Price': price,
            'Qty': share,
        }]
        #
        eventCode = EV_ST2EG_UPDATE_KLINESIGNAL if self._strategy.isRealTimeStatus() else EV_ST2EG_NOTICE_KLINESIGNAL
        signalNoticeEvent = Event({
            "EventCode": eventCode,
            "StrategyId": self._strategy.getStrategyId(),
            "Data": {
                'SeriesName': signalName,
                'Count': len(data),
                'Data': data,
            }
        })
        self._strategy.sendEvent2Engine(signalNoticeEvent)
        
        if not userNo:
            userNo = self._cfgModel.getUserNo()
        
        #处理报警
        if self._strategy.isRealTimeStatus() and self._cfgModel.getAlarm():
        #if self._cfgModel.getAlarm():
            #出声音
            audioName = self._audioDict['Signal']
            winsound.PlaySound(audioName, winsound.SND_ASYNC)
            #弹窗,合约，方向，手数，价格
            alarmStr = '策略: ' + str(self._strategy.getStrategyId()) + '\n' +\
                       '账户: ' + userNo + '\n' +\
                       '合约: ' + contNo + '\n' +\
                       '方向: ' + self._bsMap[direct] + self._ocMap[offset] + '\n' +\
                       '数量: ' + str(share) + '\n' +\
                       '价格: ' + str(price) + '\n' +\
                       '时间: ' + str(curBar['DateTimeStamp']) + '\n'
            #允许弹窗
            if self._cfgModel.getPop():
                createAlarmWin(alarmStr, self._strategy.getStrategyId(), self._strategy.getStrategyName())

    def setStartTrade(self):
        #状态未变化不做处理
        if not self._cfgModel.getPending():
            return
        self._cfgModel.setPending(False)
        # TODO: 通知界面策略状态发生变化
        event = Event({
            'StrategyId' : self._strategy.getStrategyId(),
            'EventCode'  : EV_EG2UI_RUNMODE_SWITCH,
            'Data'       : {
                'Status' : 1     #表示实盘运行
            }
        })
        self._strategy.sendEvent2UI(event)
        
    def setStopTrade(self):
        if self._cfgModel.getPending():
            return
        
        self._cfgModel.setPending(True)
        # TODO：通知界面策略状态发生变化
        event = Event({
            'StrategyId' : self._strategy.getStrategyId(),
            'EventCode'  : EV_EG2UI_RUNMODE_SWITCH,
            'Data'       : {
                'Status' : 0     #表示虚拟运行
            }
        })
        self._strategy.sendEvent2UI(event)
        

    def isTradeAllowed(self):
        if self._cfgModel.isActualRun() and self._strategy.isRealTimeStatus() and not self._cfgModel.getPending():
            return True
        return False

    # ////////////////////////设置函数////////////////////////////
    def getConfig(self):
        return self._cfgModel._metaData

    def setUserNo(self, userNo):
        self._cfgModel.setUserNo(userNo)

    def setBarInterval(self, contractNo, barType, barInterval, sampleConfig, trigger=True):
        #contractNo1 = self.getIndexMap(contractNo)
        #self.logger.debug("ContractNo:%s, %s" %(contractNo, contractNo1))
        self._cfgModel.setBarInterval(contractNo, barType, barInterval, sampleConfig, trigger)

    def setSample(self, sampleType, sampleValue):
        return self._cfgModel.setSample(sampleType, sampleValue)

    def setInitCapital(self, capital):
        initFund = capital if capital else 1000000
        self._cfgModel.setInitCapital(initFund)
        return 0

    def setMargin(self, type, value, contNo):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()
            
        if type not in (0, 1):
            return -1

        if type == 0:
            # 按比例
            if not value or value == 0:
                return self._cfgModel.setMargin(EEQU_FEE_TYPE_RATIO, 0.08, contNo)

            if value > 1:
                return -1
            return self._cfgModel.setMargin(EEQU_FEE_TYPE_RATIO, value, contNo)

        if type == 1:
            # 按固定值
            if not value or value <= 0:
                return -1
            return self._cfgModel.setMargin(EEQU_FEE_TYPE_FIXED, value, contNo)

    def setTradeFee(self, type, feeType, feeValue, contNo):
        if type not in ('A', 'O', 'C', 'T'):
            return -1

        if feeType not in (1, 2):
            return -1

        feeType = EEQU_FEE_TYPE_RATIO if feeType == 1 else EEQU_FEE_TYPE_FIXED
        return self._cfgModel.setTradeFee(type, feeType, feeValue, contNo)

    def setActual(self):
        return self._cfgModel.setActual()

    def setOrderWay(self, type):
        if type not in (1, 2):
            return -1
        self._cfgModel.setOrderWay(type)
        return 0

    def setTradeDirection(self, tradeDirection):
        if tradeDirection not in (0, 1, 2):
            return -1

        self._cfgModel.setTradeDirection(tradeDirection)
        return 0

    def setMinTradeQuantity(self, tradeQty):
        if tradeQty <= 0 or tradeQty > MAXSINGLETRADESIZE:
            return -1

        self._cfgModel.setMinQty(tradeQty)
        return 0

    def setHedge(self, hedge):
        if hedge not in ('T', 'B', 'S', 'M'):
            return -1

        self._cfgModel.setHedge(hedge)
        return 0

    def setSlippage(self, slippage):
        self._cfgModel.setSlippage(slippage)
        return 0

    def setTriggerMode(self, type, value):
        return self._cfgModel.setTrigger(type, value, False)

    def setWinPoint(self, winPoint, nPriceType, nAddTick, contNo):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()
        return self._cfgModel.setWinPoint(winPoint, nPriceType, nAddTick, contNo)

    def setStopPoint(self, stopPoint, nPriceType, nAddTick, contNo):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()
        return self._cfgModel.setStopPoint(stopPoint, nPriceType, nAddTick, contNo)

    def setFloatStopPoint(self, startPoint, stopPoint, nPriceType, nAddTick, contNo):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()
        return self._cfgModel.setFloatStopPoint(startPoint, stopPoint, nPriceType, nAddTick, contNo)

    def subscribeQuote(self, contNoTuple):
        if len(contNoTuple) <= 0:
            return

        contNoList = list(contNoTuple)
        self._cfgModel.updateSubQuoteContract(contNoList)
        return self.subQuoteList(contNoList)

    def unsubscribeQuote(self, contNoTuple):
        if len(contNoTuple) <= 0:
            return
        contNoList = list(contNoTuple)
        self._cfgModel.updateUnsubQuoteContract(contNoList)
        return self.unsubQuoteList(contNoList)

    # ///////////////////////账户函数///////////////////////////
    def getAccountId(self):
        return self._trdModel.getAccountId()
        
    def getAllAccountId(self):
        return self._trdModel.getAllAccountId()

    def getAllPositionSymbol(self, userNo):
        return self._trdModel.getAllPositionSymbol(userNo)

    def getCost(self, userNo):
        return self._trdModel.getCost(userNo)

    def getCurrentEquity(self, userNo):
        return self._trdModel.getCurrentEquity(userNo)

    def getFreeMargin(self, userNo):
        return self._trdModel.getFreeMargin(userNo)

    def getAMargin(self, userNo):
        return self._trdModel.getAMargin(userNo)

    def getProfitLoss(self, userNo):
        return self._trdModel.getProfitLoss(userNo)

    def getCoverProfit(self, userNo):
        return self._trdModel.getCoverProfit(userNo)

    def getTotalFreeze(self, userNo):
        return self._trdModel.getTotalFreeze(userNo)

    def getBuyAvgPrice(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getBuyAvgPrice(userNo, contNo)

    def getBuyPosition(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getBuyPosition(userNo, contNo)

    def getBuyPositionCanCover(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getBuyPositionCanCover(userNo, contNo)

    def getBuyProfitLoss(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        # 获取每手乘数、最新价用于计算浮动盈亏
        contUnit = self.getContractUnit(contNo)
        lastPrice = self.getQLast(contNo)
        return self._trdModel.getBuyProfitLoss(userNo, contNo, lastPrice, contUnit)

    def getSellAvgPrice(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getSellAvgPrice(userNo, contNo)

    def getSellPosition(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getSellPosition(userNo, contNo)

    def getSellPositionCanCover(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)

        return self._trdModel.getSellPositionCanCover(userNo, contNo)

    def getSellProfitLoss(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        # 获取每手乘数、最新价用于计算浮动盈亏
        contUnit = self.getContractUnit(contNo)
        lastPrice = self.getQLast(contNo)
        return self._trdModel.getSellProfitLoss(userNo, contNo, lastPrice, contUnit)

    def getTotalAvgPrice(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getTotalAvgPrice(userNo, contNo)

    def getTotalPosition(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getTotalPosition(userNo, contNo)

    def getTotalProfitLoss(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        # 获取每手乘数、最新价用于计算浮动盈亏
        contUnit = self.getContractUnit(contNo)
        lastPrice = self.getQLast(contNo)
        return self._trdModel.getTotalProfitLoss(userNo, contNo, lastPrice, contUnit)

    def getTodayBuyPosition(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getTodayBuyPosition(userNo, contNo)

    def getTodaySellPosition(self, userNo, contNo):
        contNo = self.getIndexMap(contNo)
        return self._trdModel.getTodaySellPosition(userNo, contNo)

    def getOrderBuyOrSell(self, userNo, eSession):
        return self._trdModel.getOrderBuyOrSell(userNo, eSession)

    def getOrderEntryOrExit(self, userNo, eSession):
        return self._trdModel.getOrderEntryOrExit(userNo, eSession)

    def getOrderFilledLot(self, userNo, eSession):
        return self._trdModel.getOrderFilledLot(userNo, eSession)

    def getOrderFilledPrice(self, userNo, eSession):
        return self._trdModel.getOrderFilledPrice(userNo, eSession)

    def getOrderLot(self, userNo, eSession):
        return self._trdModel.getOrderLot(userNo, eSession)

    def getOrderPrice(self, userNo, eSession):
        return self._trdModel.getOrderPrice(userNo, eSession)

    def getOrderStatus(self, userNo, eSession):
        return self._trdModel.getOrderStatus(userNo, eSession)

    def getOrderIsClose(self, userNo, eSession):
        orderStatus = self.getOrderStatus(userNo, eSession)
        
        if orderStatus in ('N', '1', '2', '3', '4', '7', '8', 'C', 'E'):
            return False
        
        return True

    def getOrderTime(self, userNo, eSession):
        return self._trdModel.getOrderTime(userNo, eSession)

    def getFirstOrderNo(self, userNo, contNo1, contNo2):
        underlayCont1 = self._qteModel.getUnderlayContractNo(contNo1)
        if len(underlayCont1) > 0:
            contNo1 = underlayCont1
        underlayCont2 = self._qteModel.getUnderlayContractNo(contNo2)
        if len(underlayCont2) > 0:
            contNo2 = underlayCont2

        return self._trdModel.getFirstOrderNo(userNo, contNo1, contNo2)

    def getNextOrderNo(self, userNo, orderId, contNo1, contNo2):
        underlayCont1 = self._qteModel.getUnderlayContractNo(contNo1)
        if len(underlayCont1) > 0:
            contNo1 = underlayCont1
        underlayCont2 = self._qteModel.getUnderlayContractNo(contNo2)
        if len(underlayCont2) > 0:
            contNo2 = underlayCont2

        return self._trdModel.getNextOrderNo(userNo, orderId, contNo1, contNo2)

    def getLastOrderNo(self, userNo, contNo1, contNo2):
        underlayCont1 = self._qteModel.getUnderlayContractNo(contNo1)
        if len(underlayCont1) > 0:
            contNo1 = underlayCont1
        underlayCont2 = self._qteModel.getUnderlayContractNo(contNo2)
        if len(underlayCont2) > 0:
            contNo2 = underlayCont2

        return self._trdModel.getLastOrderNo(userNo, contNo1, contNo2)

    def getFirstQueueOrderNo(self, userNo, contNo1, contNo2=''):
        underlayCont1 = self._qteModel.getUnderlayContractNo(contNo1)
        if len(underlayCont1) > 0:
            contNo1 = underlayCont1
        underlayCont2 = self._qteModel.getUnderlayContractNo(contNo2)
        if len(underlayCont2) > 0:
            contNo2 = underlayCont2

        return self._trdModel.getFirstQueueOrderNo(userNo, contNo1, contNo2)

    def getNextQueueOrderNo(self, userNo, orderId, contNo1, contNo2=''):
        underlayCont1 = self._qteModel.getUnderlayContractNo(contNo1)
        if len(underlayCont1) > 0:
            contNo1 = underlayCont1
        underlayCont2 = self._qteModel.getUnderlayContractNo(contNo2)
        if len(underlayCont2) > 0:
            contNo2 = underlayCont2

        return self._trdModel.getNextQueueOrderNo(userNo, orderId, contNo1, contNo2)

    def getAllQueueOrderNo(self, userNo, contNo):
        underlayCont = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayCont) > 0:
            contNo = underlayCont

        orderIdList = []
        orderId = self.getFirstQueueOrderNo(userNo, contNo)
        if orderId != -1:
            orderIdList.append(orderId)
        while (orderId != -1):
            orderId = self.getNextQueueOrderNo(userNo, orderId, contNo)
            if orderId != -1:
                orderIdList.append(orderId)
        return orderIdList

    def getALatestFilledTime(self, userNo, contNo):
        underlayCont = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayCont) > 0:
            contNo = underlayCont
        return self._trdModel.getALatestFilledTime(userNo, contNo)

    def getAllOrderNo(self, userNo, contNo):
        underlayCont = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayCont) > 0:
            contNo = underlayCont
        return self._trdModel.getAllOrderNo(userNo, contNo)

    def getOrderContractNo(self, userNo, orderId):
        return self._trdModel.getOrderContractNo(userNo, orderId)

    def deleteOrder(self, userNo, eSession):
        return self._trdModel.deleteOrder(userNo, eSession)
        
    def modifyOrder(self, userNo, eSession, contNo, orderType, validType, orderDirct, entryOrExit, hedge, \
                    orderPrice, orderQty, triggerType=stNone, triggerMode=tmNone, triggerCondition=tcNone, triggerPrice=0):
        
        return self._trdModel.modifyOrder(userNo, eSession, contNo, orderType, validType, orderDirct, entryOrExit, \
                                            hedge, orderPrice, orderQty, triggerType, triggerMode, triggerCondition, triggerPrice)

    def buySellOrder(self, userNo, contNo, orderType, validType, orderDirct, \
                     entryOrExit, hedge, orderPrice, orderQty, curBar, isPriceZero = False, signal=True):
        '''
            1. buySell下单，经过calc模块，会判断虚拟资金，会产生平仓单
            2. 如果支持K线触发，会产生下单信号
            3. 对于即时行情和委托触发，在日志中分析下单信号
        '''
        triggerInfo = self._strategy.getCurTriggerSourceInfo()
        dateTime = triggerInfo["DateTimeStamp"]
        tradeDate = triggerInfo["TradeDate"]
        triggerType = triggerInfo["TriggerType"]
        triggerData = triggerInfo["TriggerData"]

        curBarIndex = None
        curBar = None
        key = self._config.getKLineShowInfoSimple()
        curShowBar = self.getHisQuoteModel().getCurBar(key)
        if curShowBar:
            curBar = copy.deepcopy(curShowBar)
            curBarIndex = curBar["KLineIndex"]

        orderParam = {
            "UserNo": userNo,  # 账户编号
            "OrderType": orderType,  # 定单类型
            "ValidType": validType,  # 有效类型
            "ValidTime": '',  # 有效日期时间(GTD情况下使用)
            "Cont": contNo,  # 合约
            "Direct": orderDirct,  # 买卖方向：买、卖
            "Offset": entryOrExit,  # 开仓、平仓、平今
            "Hedge": hedge,  # 投机套保
            "OrderPrice": orderPrice,  # 委托价格 或 期权应价买入价格
            "OrderQty": orderQty,  # 委托数量 或 期权应价数量
            "DateTimeStamp": dateTime,  # 时间戳（基准合约）
            "TradeDate": tradeDate,  # 交易日（基准合约）
            "TriggerType": triggerType,
            "CurBar": curBar,
            "CurBarIndex": curBarIndex,  #
            "StrategyId": self._strategy.getStrategyId(),
            "StrategyName": self._strategy.getStrategyName(),
            "StrategyStage": self._strategy.getStatus()
        }

        coverMap = [(orderQty, entryOrExit)]

        tflag = self._strategy.isRealTimeStatus()
        exchg = contNo.split('|')[0]
        # 针对SHFE, INE平仓单做自适应拆分，默认先平昨再平今
        if tflag and entryOrExit == oCoverA and (exchg in ['SHFE', 'INE']):
            if orderDirct == dBuy:
                holdTd = self.getTodaySellPosition(userNo, contNo)
                holdYs = self.getSellPosition(userNo, contNo) - holdTd
                #holdCC = self.getSellPositionCanCover(userNo, contNo)
            else:
                holdTd = self.getTodayBuyPosition(userNo, contNo)
                holdYs = self.getBuyPosition(userNo, contNo) - holdTd
                #holdCC = self.getBuyPositionCanCover(userNo, contNo)
                
            # prior cover yestoday
            #if orderQty <= min(holdYs, holdCC):
            if orderQty <= holdYs:
                # cover yestoday quantity
                coverYs = orderQty
                # cover today quantity
                coverTd = 0
            else:
                # cover yestoday quantity
                coverYs = holdYs
                # cover today quantity
                #coverTd = min(holdTd, holdCC - coverYs)
                coverTd = min(holdTd, orderQty - coverYs)
                
            # cover remaining quantity
            coverOt = orderQty - coverYs - coverTd
            coverMap = [(coverTd, oCoverT), (coverYs, oCover), (coverOt, oCover)]
        # 其他交易所平仓时设置为平昨
        elif entryOrExit in (oCoverA, oCoverT):
            coverMap = [(orderQty, oCover)]
            
        for qtyCoverPair in coverMap:
            kOrderQty = qtyCoverPair[0]
            vCoverFlag = qtyCoverPair[1]
            
            # self.logger.debug("[aaaa]direct:%c, qty:%d, cover:%c" %(orderDirct, kOrderQty, vCoverFlag))
            
            if kOrderQty <= 0:
                continue
            
            if vCoverFlag in (oCover, oCoverT):
                orderParam['OrderQty'] = kOrderQty
                orderParam['Offset'] = vCoverFlag

                isVaildOrder = self._calcCenter.coverJudge(orderParam)
                if isVaildOrder < 0:
                    continue   

            canAdded = self._calcCenter.addOrder(orderParam)
            if canAdded < 1:
                continue 

            '''buy/sell 信号，
            历史阶段：一定没有委托
            实时数据：不一定有委托发
            '''
            curBar = self.getHisQuoteModel().getCurBar(self._config.getKLineShowInfoSimple())
            if self._config.hasKLineTrigger() and curBar:
                self.sendSignalEvent(self._signalName, userNo, contNo, orderDirct, vCoverFlag, orderPrice, kOrderQty, curBar)

            realPrice = 0 if isPriceZero else orderPrice
            
            retCode = None
            eSessionId = None
            if self._strategy.isRealTimeStatus():
                retCode, eSessionId = self.sendOrder(userNo, contNo, orderType, validType, orderDirct, vCoverFlag, hedge, realPrice, kOrderQty)
            
            if retCode == 0:
                self._strategy.updateBarInfoInLocalOrder(eSessionId, curBar)

    def sendOrder(self, userNo, contNo, orderType, validType, orderDirct, entryOrExit, hedge, orderPrice, orderQty, \
                  triggerType=stNone, triggerMode=tmNone, triggerCondition=tcNone, triggerPrice=0, aFunc=False):
        '''A账户下单函数，不经过calc模块，直接发单'''
        if entryOrExit in (oCover, oCoverA) and self._cfgModel.getTradeDirection() == 1:
            return -6, "当前设置仅允许开仓"
            
        if entryOrExit == oOpen and self._cfgModel.getTradeDirection() == 2:
            return -7, "当前设置仅允许平仓"
        
        if not userNo:
            userNo = self._cfgModel.getUserNo()
            
        if not userNo:
            userNo = "Default"

        if not contNo:
            contNo = self._cfgModel.getBenchmark() 
        
        if not self._strategy.isRealTimeStatus():
            # self.logger.warn(f"策略当前状态不是实盘运行状态， 不会产生实盘订单")
            #return -2, "策略当前状态不是实盘运行状态， 不会产生实盘订单"
            self.buySellOrder(userNo, contNo, orderType, validType, orderDirct, \
                            entryOrExit, hedge, orderPrice, orderQty, None)

            return -2, "当前处于历史回测阶段，将使用buySell发送模拟单"

        # 是否暂停实盘下单
        if self._cfgModel.getPending():
            self.logger.warn(f"请调用StartTrade方法开启实盘下单功能")
            return -5, "请调用StartTrade方法开启实盘下单功能"

        # 发送下单信号,K线触发、即时行情触发
        # 未选择实盘运行
        if not self._cfgModel.isActualRun():
            # self.logger.warn(f"未选择实盘运行，请在设置界面勾选'实盘运行'，或者在策略代码中调用SetActual()")
            return -1, '未选择实盘运行，请在设置界面勾选"实盘运行"，或者在策略代码中调用SetActual()方法选择实盘运行'

        # 账户错误
        if not userNo or userNo == 'Default':
            #self.logger.warn(f"未指定下单账户信息")
            return -3, "未指定下单账户信息"

        # 指定的用户未登录
        if not self._trdModel.getSign(userNo):
            #self.logger.warn(f"输入的账户没有在极星客户端登录")
            return -4, "输入的账户没有在极星客户端登录"

        underlayContNo = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayContNo) > 0:
            contNo = underlayContNo

        eId = str(self._strategy.getStrategyId()) + '-' + str(self._strategy.getESessionId())
        # 上期所特殊处理, 只对buy/sell函数生效
        # 暂时屏蔽buysell函数上期平今和平昨自适应逻辑

        # 发送定单到实盘
        aOrder = {
            'UserNo': userNo,
            'Sign': self._trdModel.getSign(userNo),
            'Cont': contNo,
            'OrderType': orderType,
            'ValidType': validType,
            'ValidTime': '',
            'Direct': orderDirct,
            'Offset': entryOrExit,
            'Hedge': hedge,
            'OrderPrice': orderPrice,
            'TriggerPrice': triggerPrice,
            'TriggerMode': triggerMode,
            'TriggerCondition': triggerCondition,
            'OrderQty': orderQty,
            'StrategyType': triggerType,
            'Remark': '',
            'AddOneIsValid': tsDay,
        }

        self.sendActualOrder2Engine(userNo, aOrder, eId, self._strategy.getStrategyId(), aFunc)
        # self.logger.trade_info(self._strategy.getStrategyId(), aOrder)
        # 更新策略的订单信息
        self._strategy.setESessionId(self._strategy.getESessionId() + 1)
        self._strategy.updateLocalOrder(eId, aOrder)
        return 0, eId

    # afunc表明是由A函数调用的，还是buy/sell调用的
    def sendActualOrder2Engine(self, userNo, aOrder, eId, strategyId, aFunc):
        if int(aOrder["OrderQty"] + 0.5) <= 0:
            return
        aOrder["OrderQty"] = int(aOrder["OrderQty"] + 0.5)
        aOrderEvent = Event({
            "EventCode": EV_ST2EG_ACTUAL_ORDER,
            "StrategyId": strategyId,
            "Data": aOrder,
            "ESessionId": eId,
        })
        self._strategy.sendEvent2Engine(aOrderEvent)
        '''A函数 发送实盘信号'''
        curBar = self.getHisQuoteModel().getCurBar(self._config.getKLineShowInfoSimple())
        if aFunc and self._config.hasKLineTrigger() and curBar:
            #self.logger.debug(f"实盘信号已经发送，k线时间戳：{curBar['DateTimeStamp']}")
            self.sendSignalEvent(self._signalName, userNo, aOrder["Cont"], aOrder["Direct"], aOrder["Offset"],
                                 aOrder["OrderPrice"], aOrder["OrderQty"], curBar)
        self.logger.trade_info(f"发送实盘订单，策略Id:{strategyId}, 本地订单号：{eId}, 订单数据：{repr(aOrder)}")

    def getAOrderNo(self, eId):
        if not (isinstance(eId, str) and '-' in eId):
            return ('', '')

        orderId = self._strategy.getOrderId(eId)
        if not orderId:
            orderId = ''
        orderNo = self._strategy.getOrderNo(eId)
        if not orderNo:
            orderNo = ''
        return orderId, orderNo

    def deleteAllOrders(self, userNo, contNo):
        underlayCont = self._qteModel.getUnderlayContractNo(contNo)
        if len(underlayCont) > 0:
            contNo = underlayCont

        orderList = self.getAllQueueOrderNo(userNo, contNo)
        if len(orderList) == 0:
            return True

        for orderId in orderList:
            self._trdModel.deleteOrderByOrderId(userNo, orderId)

        return True

    # ///////////////////////枚举函数///////////////////////////
    def getEnumBuy(self):
        return dBuy

    def getEnumSell(self):
        return dSell

    def getEnumEntry(self):
        return oOpen

    def getEnumExit(self):
        return oCover

    def getEnumExitToday(self):
        return oCoverT

    def getEnumEntryExitIgnore(self):
        return oNone

    def getEnumSended(self):
        return osSended

    def getEnumAccept(self):
        return osAccept

    def getEnumTriggering(self):
        return osTriggering

    def getEnumActive(self):
        return osActive

    def getEnumQueued(self):
        return osQueued

    def getEnumFillPart(self):
        return osFillPart

    def getEnumFilled(self):
        return osFilled

    def getEnumCanceling(self):
        return osCanceling

    def getEnumModifying(self):
        return osModifying

    def getEnumCanceled(self):
        return osCanceled

    def getEnumPartCanceled(self):
        return osPartCanceled

    def getEnumFail(self):
        return osFail

    def getEnumSuspended(self):
        return osSuspended

    def getEnumApply(self):
        return osApply

    def getEnumPeriodTick(self):
        return EEQU_KLINE_TICK

    def getEnumPeriodDyna(self):
        return EEQU_KLINE_TIMEDIVISION

    def getEnumPeriodSecond(self):
        return EEQU_KLINE_TICK

    def getEnumPeriodMin(self):
        return EEQU_KLINE_MINUTE

    def getEnumPeriodHour(self):
        return EEQU_KLINE_HOUR

    def getEnumPeriodDay(self):
        return EEQU_KLINE_DAY

    def getEnumPeriodWeek(self):
        return EEQU_KLINE_WEEK

    def getEnumPeriodMonth(self):
        return EEQU_KLINE_MONTH

    def getEnumPeriodYear(self):
        return EEQU_KLINE_YEAR

    def getEnumPeriodDayX(self):
        return EEQU_KLINE_DayX

    def getEnumOrderMarket(self):
        return otMarket

    def getEnumOrderLimit(self):
        return otLimit

    def getEnumOrderMarketStop(self):
        return otMarketStop

    def getEnumOrderLimitStop(self):
        return otLimitStop

    def getEnumOrderExecute(self):
        return otExecute

    def getEnumOrderAbandon(self):
        return otAbandon

    def getEnumOrderEnquiry(self):
        return otEnquiry

    def getEnumOrderOffer(self):
        return otOffer

    def getEnumOrderIceberg(self):
        return otIceberg

    def getEnumOrderGhost(self):
        return otGhost

    def getEnumOrderSwap(self):
        return otSwap

    def getEnumOrderSpreadApply(self):
        return otSpreadApply

    def getEnumOrderHedgApply(self):
        return otHedgApply

    def getEnumOrderOptionAutoClose(self):
        return otOptionAutoClose

    def getEnumOrderFutureAutoClose(self):
        return otFutureAutoClose

    def getEnumOrderMarketOptionKeep(self):
        return otMarketOptionKeep

    def getEnumGFD(self):
        return vtGFD

    def getEnumGTC(self):
        return vtGTC

    def getEnumGTD(self):
        return vtGTD

    def getEnumIOC(self):
        return vtIOC

    def getEnumFOK(self):
        return vtFOK

    def getEnumSpeculate(self):
        return hSpeculate

    def getEnumHedge(self):
        return hHedge

    def getEnumSpread(self):
        return hSpread

    def getEnumMarket(self):
        return hMarket

    def getRed(self):
        return 0xFF0000

    def getGreen(self):
        return 0x00AA00

    def getBlue(self):
        return 0x0000FF

    def getYellow(self):
        return 0xFFFF00

    def getPurple(self):
        return 0x9900FF

    def getGray(self):
        return 0x999999

    def getBrown(self):
        return 0x996600

    def getEnumClose(self):
        return BarDataClose

    def getEnumOpen(self):
        return BarDataOpen

    def getEnumHigh(self):
        return BarDataHigh

    def getEnumLow(self):
        return BarDataLow

    def getEnumMedian(self):
        return BarDataMedian

    def getEnumTypical(self):
        return BarDataTypical

    def getEnumWeighted(self):
        return BarDataWeighted

    def getEnumVol(self):
        return BarDataVol

    def getEnumOpi(self):
        return BarDataOpi

    def getEnumTime(self):
        return BarDataTime

    # ///////////////////////其他函数///////////////////////////
    def _addSeries(self, name, value, color, main, axis, type):
        addSeriesEvent = Event({
            "EventCode": EV_ST2EG_ADD_KLINESERIES,
            "StrategyId": self._strategy.getStrategyId(),
            "Data": {
                'ItemName': name,
                'Type': type,
                'Color': color,
                'Thick': 1,
                'OwnAxis': axis,
                'Param': [],
                'ParamNum': 0,
                'Groupid': 0,
                'GroupName': name,
                'Main': main,
            }
        })

        self._strategy.sendEvent2Engine(addSeriesEvent)

    def _plotNumeric(self, name, value, color, main, axis, type, barsback, data):
        if name not in self._plotedDict:
            self._addSeries(name, value, color, main, axis, type)
            self._plotedDict[name] = (name, value, color, main, axis, type, barsback)

        if self._strategy.isRealTimeStatus():
            eventCode = EV_ST2EG_UPDATE_KLINESERIES
        else:
            eventCode = EV_ST2EG_NOTICE_KLINESERIES
        serialEvent = Event({
            "EventCode": eventCode,
            "StrategyId": self._strategy.getStrategyId(),
            "Data": {
                "SeriesName": name,
                "SeriesType": type,
                "IsMain": main,
                "Count": len(data),
                "Data": data
            }
        })
        self._strategy.sendEvent2Engine(serialEvent)

    def setPlotText(self, value, text, color, main, barsback):
        main = '0' if main else '1'
        curBar = self._hisModel.getCurBar()

        klineIndex = curBar['KLineIndex'] - barsback
        if klineIndex <= 0:
            return

        data = [{
            'KLineIndex': klineIndex,
            'Value': value,
            'Text': text
        }]

        self._plotNumeric(self._textName, value, color, main, EEQU_ISNOT_AXIS, EEQU_TEXT, barsback, data)

    def setUnPlotText(self, main, barsback):
        main = '0' if main else '1'
        curBar = self._hisModel.getCurBar()

        klineIndex = curBar['KLineIndex'] - barsback
        if klineIndex <= 0:
            return

        data = [{
            'KLineIndex': klineIndex,
            'Value': np.nan,
            'Text': ""
        }]

        self._plotNumeric(self._textName, np.nan, 0, main, EEQU_ISNOT_AXIS, EEQU_TEXT, barsback, data)

    def setPlotIcon(self, value, icon, main, barsback):
        main = '0' if main else '1'
        curBar = self._hisModel.getCurBar()

        klineIndex = curBar['KLineIndex'] - barsback
        if klineIndex <= 0:
            return

        data = [{
            'KLineIndex': klineIndex,
            'Value': value,
            'Icon': icon
        }]

        self._plotNumeric(self._strategyName, value, 0, main, EEQU_ISNOT_AXIS, EEQU_ICON, barsback, data)

    def setUnPlotIcon(self, main, barsback):
        return self.setPlotIcon(np.nan, 0, main, barsback)

    def setPlotDot(self, name, value, icon, color, main, barsback):
        main = '0' if main else '1'
        curBar = self._hisModel.getCurBar()

        klineIndex = curBar['KLineIndex'] - barsback
        if klineIndex <= 0:
            return

        data = [{
            'KLineIndex': klineIndex,
            'Value': value,
            'Icon': icon
        }]

        self._plotNumeric(name, value, color, main, EEQU_ISNOT_AXIS, EEQU_DOT, barsback, data)

    def setUnPlotDot(self, name, main, barsback):
        return self.setPlotDot(name, np.nan, 0, 0, main, barsback)

    def setPlotBar(self, name, vol1, vol2, color, main, filled, barsback):
        main = '0' if main else '1'
        filled = 1 if filled else 0
        curBar = self._hisModel.getCurBar()
        klineIndex = curBar['KLineIndex'] - barsback

        if klineIndex <= 0:
            return

        data = [{
            'KLineIndex': klineIndex,
            'Value': vol1,
            'ClrBar': color,
            'BarValue': vol2,
            'Filled': filled
        }]

        self._plotNumeric(name, 0, color, main, EEQU_ISNOT_AXIS, EEQU_BAR, barsback, data)

    def setUnPlotBar(self, name, main, barsback):
        return self.setPlotBar(name, np.nan, np.nan, 0, main, True, barsback)

    def setPlotNumeric(self, name, value, color, main, axis, type, barsback):
        main = '0' if main else '1'
        axis = '0' if axis else '1'

        curBar = self._hisModel.getCurBar()

        klineIndex = curBar['KLineIndex'] - barsback
        if klineIndex <= 0:
            return

        data = [{
            'KLineIndex': klineIndex,
            'Value': value
        }]
        self._plotNumeric(name, value, color, main, axis, type, barsback, data)

    def setUnPlotNumeric(self, name, main, barsback):
        return self.setPlotNumeric(name, np.nan, 0, main, EEQU_ISNOT_AXIS, 1, barsback)

    def setPlotVertLine(self, color, main, axis, barsback):
        main = '0' if main else '1'
        axis = '0' if axis else '1'

        curBar = self._hisModel.getCurBar()
        klineIndex = curBar['KLineIndex'] - barsback

        if klineIndex <= 0:
            return

        value = curBar['LastPrice']
        data = [{
            'KLineIndex': klineIndex,
            'Value': value,
            'ClrK': color
        }]

        self._plotNumeric(self._strategyName, value, color, main, axis, EEQU_VERTLINE, barsback, data)

    def setUnPlotVertLine(self, main, barsback):
        main = '0' if main else '1'

        curBar = self._hisModel.getCurBar()
        klineIndex = curBar['KLineIndex'] - barsback

        if klineIndex <= 0:
            return

        value = curBar['LastPrice']
        data = [{
            'KLineIndex': klineIndex,
            'Value': np.nan,
            'ClrK': 0
        }]

        self._plotNumeric(self._strategyName, np.nan, 0, main, EEQU_ISNOT_AXIS, EEQU_VERTLINE, barsback, data)

    def setPlotPartLine(self, name, index1, price1, count, price2, color, main, axis, width):
        main = '0' if main else '1'
        axis = '0' if axis else '1'

        if index1 <= 0 or count <= 0:
            return

        data = [{
            'KLineIndex': index1,
            'Value': price1,
            'Idx2': count,
            'LineValue': price2,
            'ClrLine': color,
            'LinWid': width
        }]

        self._plotNumeric(name, 0, color, main, axis, EEQU_PARTLINE, 0, data)

    def setUnPlotPartLine(self, name, index1, count, main):
        main = '0' if main else '1'

        if index1 <= 0 or count <= 0:
            return

        data = [{
            'KLineIndex': index1,
            'Value': np.nan,
            'Idx2': count,
            'LineValue': np.nan,
            'ClrLine': 0,
            'LinWid': 1
        }]

        self._plotNumeric(name, np.nan, 0, main, EEQU_ISNOT_AXIS, EEQU_PARTLINE, 0, data)

    def setPlotStickLine(self, name, price1, price2, color, main, axis, barsback):
        main = '0' if main else '1'
        axis = '0' if axis else '1'

        curBar = self._hisModel.getCurBar()
        klineIndex = curBar['KLineIndex'] - barsback

        if klineIndex <= 0:
            return

        data = [{
            'KLineIndex': klineIndex,
            'Value': price1,
            'StickValue': price2,
            'ClrStick': color
        }]

        self._plotNumeric(name, 0, color, main, axis, EEQU_STICKLINE, barsback, data)

    def setUnPlotStickLine(self, name, main, barsback):
        return self.setPlotStickLine(name, np.nan, np.nan, 0, main, EEQU_ISNOT_AXIS, barsback)

    def formatArgs(self, args):
        if len(args) == 0:
            return None

        argStr = ""
        for arg in args:
            if isinstance(arg, str):
                argStr = argStr + ' ' + arg
            else:
                argStr = argStr + ' ' + str(arg)

        return '[User][%d]:%s' % (self.getStrategyId(), argStr)

    def LogDebug(self, args):
        logInfo = self.formatArgs(args)
        self.logger.user_debug(logInfo)

    def LogInfo(self, args):
        logInfo = self.formatArgs(args)
        self.logger.user_info(logInfo)

    def LogWarn(self, args):
        logInfo = self.formatArgs(args)
        self.logger.user_warn(logInfo)

    def LogError(self, args):
        logInfo = self.formatArgs(args)
        self.logger.user_error(logInfo)

    # ///////////////////////属性函数///////////////////////////
    def getBarInterval(self):
        barInfo = self._cfgModel.getKLineShowInfo()
        if 'KLineSlice' not in barInfo:
            return None
        return barInfo['KLineSlice']

    def getBarType(self):
        barInfo = self._cfgModel.getKLineShowInfo()
        if 'KLineType' not in barInfo:
            return None
        return barInfo['KLineType']

    def getBidAskSize(self, contNo):
        contractNo = contNo
        if not contNo:
            contractTuple = self._cfgModel.getContract()
            if len(contractTuple) == 0:
                return 0
            else:
                contractNo = contractTuple[0]

        quoteModel = self._qteModel._contractData[contractNo]
        bidList = quoteModel._metaData['Lv2BidData']

        isNotAllZero = False
        for bidData in bidList:
            isNotAllZero = isNotAllZero or bidData != 0

        return len(bidList) if isNotAllZero else 0

    def getCommodityInfoFromContNo(self, contNo):
        '''
        从合约编号中提取交易所编码/商品编码/合约到期日期
        :param contNo: 合约编号
        :return: {}
        '''
        ret = {
            'ExchangeCode': '',  # 交易所编码
            'CommodityCode': '',  # 商品编码
            'CommodityNo': '',  # 合约到期日期
        }
        contractNo = contNo
        if not contNo:
            contractNo = self._cfgModel.getBenchmark()

        contList = contractNo.split('|')
        if len(contList) == 0:
            return ret

        #if contNo not in self._qteModel._contractData:
        #    return ret

        ret['ExchangeCode'] = contList[0]
        ret['CommodityCode'] = '|'.join(contList[0:3])
        #ret['CommodityCode'] = self._qteModel._contractData[contNo].getContract()['CommodityNo']
        ret['CommodityNo'] = contList[-1]
        return ret

    def setStopWinKtBlack(self, op, kt):
        return self._cfgModel.setStopWinKtBlack(op, kt)
        
    def getStopWinKtBlack(self):
        return self._cfgModel.getStopWinKtBlack()

    def getCanTrade(self, contNo):
        return 0

    def getContractUnit(self, contNo):
        commodityNo = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        #if contNo == 'ZCE|S|OI|001|005':
        #    self.logger.debug("222222:commNo:%s,%s" %(commodityNo, self._qteModel._commodityData))
        if commodityNo not in self._qteModel._commodityData:
            return 0

        commodityModel = self._qteModel._commodityData[commodityNo]
        return commodityModel._metaData['TradeDot']

    def getExchangeName(self, contNo):
        exchangeNo = self.getCommodityInfoFromContNo(contNo)['ExchangeCode']
        return exchangeNo
        # if exchangeNo not in self._qteModel._exchangeData:
        #    return None

        # exchangeModel = self._qteModel._exchangeData[exchangeNo]
        # return exchangeModel._metaData['ExchangeName']

    def getExchangeTime(self, exgNo):
        return self._qteModel.getExchangeTime(exgNo)

    def getExchangeStatus(self, exgNo):
        return self._qteModel.getExchangeStatus(exgNo)
        
    def getCommodityStatus(self, commodityNo):
        return self._qteModel.getCommodityStatus(commodityNo)

    def getExpiredDate(self, contNo):
        return 0

    def getGetSessionCount(self, contNo):
        commodity = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodity not in self._qteModel._commodityData:
            return 0

        sessionCount = 0
        timeBucket = self._qteModel._commodityData[commodity]._metaData['TimeBucket']
        for data in timeBucket:
            if data['TradeState'] == EEQU_TRADESTATE_BID or data['TradeState'] == EEQU_TRADESTATE_CONTINUOUS:
                sessionCount += 1
        return sessionCount

    def getSessionEndTime(self, contNo, index):
        commodity = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodity not in self._qteModel._commodityData:
            return 0

        timeBucket = self._qteModel._commodityData[commodity]._metaData['TimeBucket']
        if not isinstance(index, int):
            raise IndexError("交易时段索引应为整数")
        if 2 * index + 1 >= len(timeBucket) or 2 * index + 1 < -len(timeBucket):
            self.logger.warn("GetSessionEndTime()函数交易时段索引超限")
            return 0.0
        endTime = timeBucket[2 * index + 1]["BeginTime"]
        return float(endTime) / 1000000000

    def getGetSessionStartTime(self, contNo, index):
        commodity = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodity not in self._qteModel._commodityData:
            return 0

        timeBucket = self._qteModel._commodityData[commodity]._metaData['TimeBucket']
        if not isinstance(index, int):
            raise IndexError("交易时段索引应为整数")
        if 2 * index >= len(timeBucket) or 2 * index < -len(timeBucket):
            self.logger.warn("GetSessionStartTime()函数交易时段索引超限")
            return 0.0
        beginTime = timeBucket[2 * index]["BeginTime"]
        return float(beginTime) / 1000000000

    def getNextTimeInfo(self, contNo, timeStr):
        commodity = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodity not in self._qteModel._commodityData:
            return {}

        timeInt = float(timeStr) * 1000000000

        timeBucket = self._qteModel._commodityData[commodity]._metaData['TimeBucket']
        if len(timeBucket) == 0:
            return {}

        timeList = []
        for timeDict in timeBucket:
            timeList.append((timeDict['BeginTime'], timeDict['TradeState']))
        list.sort(timeList, key=lambda t: t[0])

        for timeTuple in timeList:
            if timeTuple[0] >= timeInt:
                return {'Time': float(timeTuple[0]) / 1000000000, 'TradeState': timeTuple[1]}

        return {'Time': float(timeList[0][0]) / 1000000000, 'TradeState': timeList[0][1]}
        
    def getCurrentDate(self):
        if not self._strategy.isRealTimeStatus():
            return self.getBarDate('', '', 0)
            
        date = datetime.now().strftime('%Y%m%d')
        return int(date)

    def getCurrentTime(self):
        if not self._strategy.isRealTimeStatus():
            return self.getBarTime('', '', 0)
            
        currentTime = datetime.now().strftime('0.%H%M%S')
        return float(currentTime)
        
    def _gethms(self, time):
        itime = round((time + 1e-9) * 1000000)
        hh,mm,ss = 0, 0, 0
        if itime > 0:
            hh = int(itime / 10000)
            mm = int((itime % (10000)) / 100)
            ss = itime % 100
            
        return hh, mm, ss
        
    def getTimeDiff(self, time1, time2):
        if not isinstance(time1, float):
            return 0
            
        if not isinstance(time2, float):
            return 0    
         
        ftime1 = math.modf(time1)[0]
        ftime2 = math.modf(time2)[0]
        
        hh1,mm1,ss1 = self._gethms(ftime1)
        hh2,mm2,ss2 = self._gethms(ftime2)

        now = datetime.now()
        
        mtime1 = datetime(now.year, now.month, now.day, hh1, mm1, ss1)
        mtime2 = datetime(now.year, now.month, now.day, hh2, mm2, ss2)
        if time2 + 1.0 < 1e-9:
            mtime2 = now
        
        if mtime2 > mtime1:
            delta = (mtime2 - mtime1).seconds
        else:
            delta = -(mtime1 - mtime2).seconds

        return delta
    
    def _addDay(self, dt, n):
        x = datetime.strptime(str(dt), "%Y%m%d")
        while True:
            x = x + timedelta(days=n)
            if x.isoweekday() != 6 and x.isoweekday() != 7:
                break

        return int(x.strftime("%Y%m%d"))
    
    def _testAndAddDay(self, dt):
        x = datetime.strptime(str(dt), "%Y%m%d")
        while x.isoweekday() == 6 or x.isoweekday() == 7:
            x = x + timedelta(days=1)

        return int(x.strftime("%Y%m%d"))
    
    def _calTradeDate(self, dt, tf):
        #self.logger.debug('dt:%d, tbflag:%c' %(dt, tf))
        if tf == EEQU_DATEFLAG_PRE:
            return self._addDay(dt, 1)
        elif tf == EEQU_DATEFLAG_NEXT:
            return self._addDay(dt, -1)
        else:
            return self._testAndAddDay(dt)
    
    def getTradeDate(self, contNo, dateTimeStamp):
        contNo = self._config.getBenchmark() if not contNo else contNo
        commodity = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodity not in self._qteModel._commodityData:
            # commodity not found
            return -1
        
        dt = dateTimeStamp % 1000000000
        currentTime = dt*1.0/1000000000
        
        idx = -1
        
        sessionCount = self.getGetSessionCount(contNo)
        for index in range(0, sessionCount):
            startTime = self.getGetSessionStartTime(contNo, index)
            endTime = self.getSessionEndTime(contNo, index)
            
            delta = 0.0
            if startTime >= endTime:
                endTime += 0.24
                if currentTime <= startTime:
                     delta = 0.24
            if currentTime + delta >= startTime and currentTime + delta < endTime:
                idx = index
        
        if idx == -1:
            # not in trade period
            return -2
        
        timeBucket = self._qteModel._commodityData[commodity]._metaData['TimeBucket']
        
        tbflag = timeBucket[2 * idx]["DateFlag"]
        
        return self._calTradeDate(int(dateTimeStamp/1000000000), tbflag)
        
    def getTradeSessionBeginTime(self, contNo, tradeDate, sessionIdx):
        contNo = self._config.getBenchmark() if not contNo else contNo
        commodity = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodity not in self._qteModel._commodityData:
            # commodity not found
            return -1

        sessionCount = self.getGetSessionCount(contNo)
        if abs(sessionIdx) >= sessionCount:
            return -2

        timeBucket = self._qteModel._commodityData[commodity]._metaData['TimeBucket']
        
        tbflag = timeBucket[2 * sessionIdx]["DateFlag"]
        newflag = EEQU_DATEFLAG_CUR
        if tbflag == EEQU_DATEFLAG_PRE:
            newflag = EEQU_DATEFLAG_NEXT
        elif tbflag == EEQU_DATEFLAG_NEXT:
            newflag = EEQU_DATEFLAG_PRE
            
        datepart = self._calTradeDate(tradeDate, newflag)
        timepart = timeBucket[2 * sessionIdx]["BeginTime"]
        
        return datepart*1000000000 + timepart
        
    def getTradeSessionEndTime(self, contNo, tradeDate, sessionIdx):
        contNo = self._config.getBenchmark() if not contNo else contNo
        commodity = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodity not in self._qteModel._commodityData:
            # commodity not found
            return -1

        sessionCount = self.getGetSessionCount(contNo)
        if abs(sessionIdx) >= sessionCount:
            return -2

        timeBucket = self._qteModel._commodityData[commodity]._metaData['TimeBucket']
        
        tbflag = timeBucket[2 * sessionIdx]["DateFlag"]
        newflag = EEQU_DATEFLAG_CUR
        if tbflag == EEQU_DATEFLAG_PRE:
            newflag = EEQU_DATEFLAG_NEXT
        elif tbflag == EEQU_DATEFLAG_NEXT:
            newflag = EEQU_DATEFLAG_PRE
            
        datepart = self._calTradeDate(tradeDate, newflag)
        timepart = timeBucket[2 * sessionIdx+1]["BeginTime"]
        
        return datepart*1000000000 + timepart

    def isInSession(self, contNo):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()

        # 兼容跨期套利
        contNoInfo = contNo.split('|')
        if len(contNoInfo) >= 4 and (contNoInfo[1] == 'S' or contNoInfo[1] == 's'):
            contNo = contNoInfo[0] + '|F|' + contNoInfo[2] + '|' + contNoInfo[3]

        # TODO：使用交易时间
        #currentTime = float(datetime.now().strftime('0.%H%M%S'))
        exgTime = datetime.strptime(self.getExchangeTime(contNoInfo[0]), "%Y-%m-%d %H:%M:%S")
        currentTime = float(exgTime.strftime('0.%H%M%S'))
        
        sessionCount = self.getGetSessionCount(contNo)
        for index in range(0, sessionCount):
            startTime = self.getGetSessionStartTime(contNo, index)
            endTime = self.getSessionEndTime(contNo, index)
            
            #eg1. 0.21, 0.023, 0.142854
            #eg1. 0.1330, 0.1500, 0.142854
            #eg2. 0.06, 0.05, 0.03
            #eg3. 0.06, 0.05, 0.052
            delta = 0.0
            if startTime >= endTime:
                endTime += 0.24
                if currentTime <= startTime:
                     delta = 0.24
            if currentTime + delta >= startTime and currentTime + delta < endTime:
                return True

        return False

    def getMarginRatio(self, contNo):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()

        marginValue = self._cfgModel.getMarginValue(contNo)
        return marginValue if marginValue else 0.08

    def getMaxBarsBack(self):
        return self._hisModel.getHisLength()

    def getMaxSingleTradeSize(self):
        return MAXSINGLETRADESIZE

    def getPriceTick(self, contNo):
        commodityNo = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodityNo not in self._qteModel._commodityData:
            return 0

        commodityModel = self._qteModel._commodityData[commodityNo]
        priceTick = commodityModel._metaData['PriceTick']
        return priceTick

    def getOptionStyle(self, contNo):
        return 0

    def getOptionType(self, contNo):
        contractNo = contNo
        if not contNo:
            contractTuple = self._cfgModel.getContract()
            if len(contractTuple) == 0:
                return -1
            else:
                contractNo = contractTuple[0]

        contInfo = contractNo.split('|')
        if len(contInfo) < 4 or contInfo[1] != EEQU_COMMODITYTYPE_OPTION:
            return -1

        commodityMo = contInfo[3]
        if 'C' in commodityMo or 'c' in commodityMo:
            return 0
        elif 'P' in commodityMo or 'p' in commodityMo:
            return 1
        return -1

    def getPriceScale(self, contNo):
        commodityNo = self.getCommodityInfoFromContNo(contNo)['CommodityCode']
        if commodityNo not in self._qteModel._commodityData:
            return 0

        commodityModel = self._qteModel._commodityData[commodityNo]
        pricePrec = commodityModel._metaData['PricePrec']

        return math.pow(0.1, pricePrec)

    def getRelativeSymbol(self):
        return 0

    def getStrikePrice(self):
        return 0

    def getSymbol(self):
        return self._cfgModel.getBenchmark()

    def getSymbolName(self, contNo):
        commodityInfo = self.getCommodityInfoFromContNo(contNo)
        commodityNo = commodityInfo['CommodityCode']
        if commodityNo not in self._qteModel._commodityData:
            return None

        commodityModel = self._qteModel._commodityData[commodityNo]
        commodityName = commodityModel._metaData['CommodityName']
        return commodityName + commodityInfo['CommodityNo']

    def getSymbolType(self, contNo):
        return self.getCommodityInfoFromContNo(contNo)['CommodityCode']

    def getIndexMap(self, contNo=''):
        if not contNo:
            contNo = self._config.getBenchmark()

        underlayCont = self._qteModel.getUnderlayContractNo(contNo)
        #self.logger.debug("GetIndexMap----contNo:%s, underCont:%s" %(contNo, underlayCont))
        return contNo if len(underlayCont) == 0 else underlayCont

    # ///////////////////////策略状态///////////////////////////
    def getAvgEntryPrice(self, contNo):
        '''当前持仓的平均建仓价格'''
        contNo = self.getIndexMap(contNo)

        posInfo = self._calcCenter.getPositionInfo(contNo)
        if not posInfo:
            return 0

        totalPrice = posInfo['BuyPrice'] * posInfo['TotalBuy'] + posInfo['SellPrice'] * posInfo['TotalSell']
        totalQty = posInfo['TotalBuy'] + posInfo['TotalSell']

        return totalPrice / totalQty if totalQty > 0 else 0

    def getFirstOpenOrderInfo(self, contNo, key):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()

        #if self.getMarketPosition(contNo) == 0:
        #    return -1

        orderInfo = self._calcCenter.getFirstOpenOrder(contNo)
        if not orderInfo or key not in orderInfo:
            return -1

        return orderInfo[key]

    def getLatestCoverOrderInfo(self, contNo, key):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()

        if self.getMarketPosition(contNo) == 0:
            return -1

        orderInfo = self._calcCenter.getLatestCoverOrder(contNo)
        if not orderInfo or key not in orderInfo:
            return -1

        return orderInfo[key]

    def getBarsSinceEntry(self, contNo):
        '''获得当前持仓中指定合约的第一个建仓位置到当前位置的Bar计数'''
        contNo = self.getIndexMap(contNo)
        barIndex = self.getFirstOpenOrderInfo(contNo, 'CurBarIndex')
        if barIndex == -1:
            return barIndex

        curBar = self._hisModel.getCurBar()
        return int(curBar['KLineIndex'] - barIndex)

    def getBarsSinceExit(self, contNo):
        '''获得当前持仓中指定合约的最近平仓位置到当前位置的Bar计数'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestCoverOrder(contNo)
        if not orderInfo or 'CurBarIndex' not in orderInfo:
            return -1

        barIndex = orderInfo['CurBarIndex']

        curBar = self._hisModel.getCurBar()
        return (curBar['KLineIndex'] - barIndex)

    def getBarsSinceLastEntry(self, contNo):
        '''获得当前持仓的最后一个建仓位置到当前位置的Bar计数'''
        contNo = self.getIndexMap(contNo)

        #if self.getMarketPosition(contNo) == 0:
        #    return -1

        orderInfo = self._calcCenter.getLatestOpenOrder(contNo)
        if not orderInfo or 'CurBarIndex' not in orderInfo:
            return -1

        barIndex = orderInfo['CurBarIndex']

        curBar = self._hisModel.getCurBar()
        return (int(curBar['KLineIndex']) - barIndex)
    
    def getBarsSinceLastBuyEntry(self, contNo):
        '''获得当前持仓的最后一个Buy建仓位置到当前位置的Bar计数'''
        contNo = self.getIndexMap(contNo)

        #if self.getMarketPosition(contNo) == 0:
        #    return -1

        orderInfo = self._calcCenter.getLatestBuyOpenOrder(contNo)["Order"]
        if not orderInfo or 'CurBarIndex' not in orderInfo:
            return -1

        barIndex = orderInfo['CurBarIndex']

        curBar = self._hisModel.getCurBar()
        return (int(curBar['KLineIndex']) - barIndex)
    
    def getBarsSinceLastSellEntry(self, contNo):
        '''获得当前持仓的最后一个Sell建仓位置到当前位置的Bar计数'''
        contNo = self.getIndexMap(contNo)

        #if self.getMarketPosition(contNo) == 0:
        #    return -1

        orderInfo = self._calcCenter.getLatestSellOpenOrder(contNo)["Order"]
        if not orderInfo or 'CurBarIndex' not in orderInfo:
            return -1

        barIndex = orderInfo['CurBarIndex']

        curBar = self._hisModel.getCurBar()
        return (int(curBar['KLineIndex']) - barIndex)

    def getBarsSinceToday(self, contractNo, barType, barValue):
        contNo = self.getIndexMap(contractNo)
        key = self.getKey(contNo, barType, barValue)
        curBar = self._hisModel.getCurBar(key)
        tradeDate = curBar['TradeDate']
        barList = self._hisModel._curBarDict[key].getTradeDateKLine(tradeDate)
        if len(barList) == 0:
            return 0

        firstBar = barList[0]
        res = curBar['KLineIndex'] - firstBar['KLineIndex']
        return res if res > 0 else 0

    def getPositionValue(self, contNo, key):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()

        pos = self.getMarketPosition(contNo)
        if pos == 0:
            return -1

        positionInfo = self._calcCenter.getPositionInfo(contNo)
        if not positionInfo or key not in positionInfo:
            return -1

        return positionInfo[key]

    def getContractProfit(self, contNo):
        '''获得当前持仓的每手浮动盈亏'''
        contNo = self.getIndexMap(contNo)
        holdProfit = self.getPositionValue(contNo, 'HoldProfit')
        if holdProfit == -1:
            return 0

        totalBuy = self.getPositionValue(contNo, 'TotalBuy')
        totalSell = self.getPositionValue(contNo, 'TotalSell')
        totalQty = totalBuy + totalSell
        return holdProfit / totalQty if totalQty > 0 else 0

    def getCurrentContracts(self, contNo):
        '''获得策略当前的持仓合约数(净持仓)'''
        contNo = self.getIndexMap(contNo)
        totalBuy = self.getPositionValue(contNo, 'TotalBuy')
        totalSell = self.getPositionValue(contNo, 'TotalSell')

        totalBuy = 0 if totalBuy == -1 else totalBuy
        totalSell = 0 if totalSell == -1 else totalSell

        return totalBuy - totalSell

    def getEntryDate(self, contNo):
        '''获得当前持仓的第一个建仓位置的日期'''
        contNo = self.getIndexMap(contNo)
        entryDate = self.getFirstOpenOrderInfo(contNo, 'TradeDate')
        if entryDate == -1:
            return 19700101
        return entryDate

    def getBuyPositionInStrategy(self, contNo):
        '''获得当前持仓的买入方向的持仓量'''
        contNo = self.getIndexMap(contNo)

        positionInfo = self._calcCenter.getPositionInfo(contNo)
        if not positionInfo or 'TotalBuy' not in positionInfo:
            return -1

        return positionInfo['TotalBuy']

    def getSellPositionInStrategy(self, contNo):
        '''当前持仓的卖出持仓量'''
        contNo = self.getIndexMap(contNo)

        positionInfo = self._calcCenter.getPositionInfo(contNo)
        if not positionInfo or 'TotalSell' not in positionInfo:
            return -1

        return positionInfo['TotalSell']

    def getEntryPrice(self, contNo):
        '''获得当前持仓的第一次建仓的委托价格'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getFirstOpenOrder(contNo)
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        return float(orderInfo['OrderPrice'])

    def getEntryTime(self, contNo):
        '''获得当前持仓的第一个建仓位置的时间'''
        contNo = self.getIndexMap(contNo)
        dateTimeStamp = self.getFirstOpenOrderInfo(contNo, 'DateTimeStamp')
        if dateTimeStamp == -1:
            return 0
        return (int(dateTimeStamp) % 1000000000) / 1000000000

    def getExitDate(self, contNo):
        ''' 获得最近平仓位置Bar日期'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestCoverOrder(contNo)
        if not orderInfo or 'TradeDate' not in orderInfo:
            return 19700101

        return int(orderInfo['TradeDate'])

    def getExitPrice(self, contNo):
        '''获得合约最近一次平仓的委托价格'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestCoverOrder(contNo)
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        return orderInfo['OrderPrice']

    def getExitTime(self, contNo):
        '''获得最近平仓位置Bar时间'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestCoverOrder(contNo)
        if not orderInfo or 'DateTimeStamp' not in orderInfo:
            return 0

        dateTimeStamp = orderInfo['DateTimeStamp']
        return (int(dateTimeStamp) % 1000000000) / 1000000000

    def getLastEntryDate(self, contNo):
        '''获得当前持仓的最后一个建仓位置的日期'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestOpenOrder(contNo)
        if not orderInfo or 'TradeDate' not in orderInfo:
            return 19700101

        return int(orderInfo['TradeDate'])

    def getLastEntryPrice(self, contNo):
        '''获得当前持仓的最后一次建仓的委托价格'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestOpenOrder(contNo)
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        return float(orderInfo['OrderPrice'])
    
    def getLastBuyEntryPrice(self, contNo):
        '''获得当前Buy持仓的最后一次建仓的委托价格'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestBuyOpenOrder(contNo)["Order"]
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        return float(orderInfo['OrderPrice'])
        
    def getLastSellEntryPrice(self, contNo):
        '''获得当前Sell持仓的最后一次建仓的委托价格'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestSellOpenOrder(contNo)["Order"]
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        return float(orderInfo['OrderPrice'])
        
    def getHighestSinceLastBuyEntry(self, contNo):
        '''获得当前Buy持仓的最后一次建仓以来的最高价'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestBuyOpenOrder(contNo)["Order"]
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        price = self._calcCenter.getLatestBuyOpenOrder(contNo)["LastEntryHPrice"]

        return float(price)
        
    def getHighestSinceLastSellEntry(self, contNo):
        '''获得当前Sell持仓的最后一次建仓以来的最高价'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestSellOpenOrder(contNo)["Order"]
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        price = self._calcCenter.getLatestSellOpenOrder(contNo)["LastEntryHPrice"]

        return float(price)
        
    def getLowestSinceLastBuyEntry(self, contNo):
        '''获得当前Buy持仓的最后一次建仓以来的最低价'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestBuyOpenOrder(contNo)["Order"]
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        price = self._calcCenter.getLatestBuyOpenOrder(contNo)["LastEntryLPrice"]

        return float(price)
        
    def getLowestSinceLastSellEntry(self, contNo):
        '''获得当前Sell持仓的最后一次建仓以来的最低价'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestSellOpenOrder(contNo)["Order"]
        if not orderInfo or 'OrderPrice' not in orderInfo:
            return 0

        price = self._calcCenter.getLatestSellOpenOrder(contNo)["LastEntryLPrice"]

        return float(price)

    def getLastEntryTime(self, contNo):
        '''获得当前持仓的最后一个建仓位置的时间'''
        contNo = self.getIndexMap(contNo)

        orderInfo = self._calcCenter.getLatestOpenOrder(contNo)
        if not orderInfo or 'DateTimeStamp' not in orderInfo:
            return 0

        dateTimeStamp = orderInfo['DateTimeStamp']
        return (int(dateTimeStamp) % 1000000000) / 1000000000

    def getMarketPosition(self, contNo):
        contNo = self.getIndexMap(contNo)

        positionInfo = self._calcCenter.getPositionInfo(contNo)
        if not positionInfo:
            return -1

        buy = positionInfo['TotalBuy']
        sell = positionInfo['TotalSell']
        if buy == sell:
            return 0
        return 1 if buy > sell else -1

    def getPositionProfit(self, contNo):
        contNo = self.getIndexMap(contNo)

        #self.logger.debug("PositionProfit1: %s, %s"  %(contNo, self._calcCenter.getPositionInfo()))
        
        if contNo not in list(self._calcCenter.getPositionInfo()):
            return 0.0

        positionInfo = self._calcCenter.getPositionInfo(contNo)
        return positionInfo['HoldProfit']

    # ///////////////////////策略性能///////////////////////////
    def getAvailable(self):
        return self._calcCenter.getProfit()['Available']

    def getEquity(self):
        fundRecodeList = self._calcCenter.getFundRecord()
        if not fundRecodeList:
            return self.getAvailable()

        fundRecordDict = fundRecodeList[-1]
        return fundRecordDict['DynamicEquity']

    def getFloatProfit(self, contNo):
        contNo = self.getIndexMap(contNo)
        return self._calcCenter._getHoldProfit(contNo)

    def getGrossLoss(self):
        return self._calcCenter.getProfit()["TotalLose"]

    def getGrossProfit(self):
        return self._calcCenter.getProfit()["TotalProfit"]

    def getMargin(self, contNo):
        if not contNo:
            contNo = self._cfgModel.getBenchmark()
        return self._calcCenter._getHoldMargin(contNo)

    def getNetProfit(self):
        '''平仓盈亏'''
        return self._calcCenter.getProfit()["LiquidateProfit"]

    def getNumEvenTrades(self):
        '''保本交易总手数'''
        # return self._calcCenter.getProfit()["EventTrade"]
        return 0

    def getNumLosTrades(self):
        '''亏损交易总手数'''
        # return self._calcCenter.getProfit()["LoseTrade"]
        return 0

    def getNumWinTrades(self):
        '''盈利交易的总手数'''
        # return self._calcCenter.getProfit()["WinTrade"]
        return 0

    def getNumAllTimes(self):
        '''开仓次数'''
        return self._calcCenter.getProfit()["AllTimes"]

    def getNumWinTimes(self):
        '''盈利次数'''
        return self._calcCenter.getProfit()["WinTimes"]

    def getNumLoseTimes(self):
        '''亏损次数'''
        return self._calcCenter.getProfit()["LoseTimes"]

    def getNumEventTimes(self):
        '''保本次数'''
        return self._calcCenter.getProfit()["EventTimes"]

    def getPercentProfit(self):
        '''盈利成功率'''
        winTimes = self._calcCenter.getProfit()["WinTimes"]
        allTimes = self._calcCenter.getProfit()["AllTimes"]
        return winTimes / allTimes if allTimes > 0 else 0

    def getTradeCost(self):
        '''交易产生的手续费'''
        return self._calcCenter.getProfit()["Cost"]

    def getTotalTrades(self):
        '''交易总开仓手数'''
        # return self._calcCenter.getProfit()["AllTrade"]
        return 0

    def SMA(self, price, period, weight):
        '''计算加权移动平均值'''
        return self._staModel.SMA(price, period, weight)

    def ParabolicSAR(self, high, low, afstep, aflimit):
        '''计算抛物线转向'''
        return self._staModel.ParabolicSAR(high, low, afstep, aflimit)
        
    def getRef(self, price, length):
        if length >= len(price):
            return price[0]
        else:
            return price[-length-1]

    def getHighest(self, price, length):
        if (not isinstance(price, np.ndarray) and not isinstance(price, list)) or len(price) == 0:
            return np.array([])

        arr = np.array(price) if isinstance(price, list) else price
        if length <= 1:
            return arr

        return talib.MAX(arr, length)

    def getLowest(self, price, length):
        if (not isinstance(price, np.ndarray) and not isinstance(price, list)) or len(price) == 0:
            return np.array([])

        arr = np.array(price) if isinstance(price, list) else price
        if length <= 1:
            return arr

        return talib.MIN(arr, length)
        
    def getCountIf(self, cond, peroid):
        sum = 0
        for i in range(len(cond)-1, len(cond)-peroid-1, -1):
            if cond[i]: sum += 1
            if i == 0: break
            
        return sum
        
    def getCrossOver(self, price1, price2):
        '''price1是否上穿price2,前一个在下，当前跟在上'''
        if price1[-1] <= price2[-1]:
            return False
        #只有一根线，不做比较
        if len(price1) <= 1:
            return False
            
        #如果前一根相等，则继续往前找上一根
        pos = -2
        while price1[pos] == price2[pos]:
            pos = pos -1
            if pos <= -len(price1):
                break
        return price1[pos] < price2[pos]

    def getCrossUnder(self, price1, price2):
        '''price1是否下破price2,前一个在上，当前跟在下'''
        if price1[-1]  >= price2[-1]:
            return False
            
        #只有一根线，不做比较
        if len(price1) <= 1:
            return False
            
        #如果前一根相等，则继续往前找上一根
        pos = -2;
        while price1[pos] == price2[pos]:
            pos = pos -1
            if pos <= -len(price1):
                break
        return price1[pos] > price2[pos]
        
    def getSwingHigh(self, Price, Length, Instance, Strength):
        ispivot, pivot, bar = self._staModel.Pivot(Price,Length,Strength,Strength,Instance,1);
        return pivot;
        
    def getSwingLow(self, Price, Length, Instance, Strength):
        ispivot, pivot, bar = self._staModel.Pivot(Price,Length,Strength,Strength,Instance,-1);
        return pivot;
        
    def setAlert(self, Info, bKeep, level):
        #出声音
        if bKeep:
            if level in self._audioDict:
                audioName = self._audioDict[level]
            else:
                audioName = 'SystemQuestion'
            winsound.PlaySound(audioName, winsound.SND_ASYNC) 
        #弹窗        
        createAlarmWin(Info, self._strategy.getStrategyId(), self._strategy.getStrategyName());
        
    def getStrategyId(self):
        return self._strategy.getStrategyId()
