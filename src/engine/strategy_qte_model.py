import numpy as np
from capi.com_types import *
from .quote_model import *
import time, sys
import math


class StrategyQuote(QuoteModel):
    '''即时行情数据模型'''
    def __init__(self, strategy, config):
        '''
        self._exchangeData  = {}  #{key=ExchangeNo,value=ExchangeModel}
        self._commodityData = {}  #{key=CommodityNo, value=CommodityModel}
        self._contractData  = {}  #{key=ContractNo, value=QuoteDataModel}
        '''
        self._strategy = strategy
        self.logger = strategy.logger
        QuoteModel.__init__(self, self.logger)
        self._config = config
        self._contractTuple = self._config.getContract()
        

    def subQuoteList(self, contNoList):
        if not contNoList:
            return

        event = Event({
            'EventCode': EV_ST2EG_SUB_QUOTE,
            'StrategyId': self._strategy.getStrategyId(),
            'Data': contNoList,
        })

        self._strategy.sendEvent2Engine(event)

    def unsubQuoteList(self, contNoList):
        if not contNoList:
            return

        event = Event({
            'EventCode': EV_ST2EG_UNSUB_QUOTE,
            'StrategyId': self._strategy.getStrategyId(),
            'Data': contNoList,
        })

        self._strategy.sendEvent2Engine(event)

    # /////////////////////////////应答消息处理///////////////////
    def onExchange(self, event):
        dataDict = event.getData()
        strategyId = event.getStrategyId()
        #self.logger.debug("QteModelOnExchange:%s" %dataDict)
        for k, v in dataDict.items():
            self._exchangeData[k] = ExchangeModel(self.logger, v)
            self._exchangeData[k].updateStatus(strategyId, v)
       
    def onExchangeStatus(self, event):
        dataList = event.getData()
        strategyId = event.getStrategyId()
        for dataDict in dataList:
            if dataDict['ExchangeNo'] not in self._exchangeData:
                continue
            exchangeModel = self._exchangeData[dataDict['ExchangeNo']]
            exchangeModel.updateStatus(strategyId, dataDict) 
        
    def onCommodity(self, event):
        dataDict = event.getData()
        for k, v in dataDict.items():
            self._commodityData[k] = CommodityModel(self.logger, v)

    def onContract(self, event):
        dataDict = event.getData()
        for k, v in dataDict.items():
            #if 'ZCE|S|OI' in k:
            #    self.logger.debug("333333333:k:%s,v:%s" %(k, v))
            self._contractData[k] = QuoteDataModel(self.logger, v)

    def onUnderlayMap(self, event):
        self._underlayData = event.getData()

    def onQuoteRsp(self, event):
        '''
        event.Data = {
            'ExchangeNo' : dataDict['ExchangeNo'],
            'CommodityNo': dataDict['CommodityNo'],
            'ContractNo' : dataDict['ContractNo']
            'UpdateTime' : 20190401090130888, # 时间戳
            'Lv1Data'    : {                  # 普通行情
                '0'      : 5074,              # 昨收盘
                '1'      : 5052,              # 昨结算
                '2'      : 269272,            # 昨持仓
                '3'      : 5067,              # 开盘价
                '4'      : 5084,              # 最新价
                ...
                '126'    : 1                  # 套利行情系数
                },
            'Lv2BidData' :[
                5083,                         # 买1
                5082,                         # 买2
                5082,                         # 买3
                5080,                         # 买4
                5079,                         # 买5
            ],
            'Lv2AskData':[
                5084,                         # 卖1
                5085,                         # 卖2
                5086,                         # 卖3
                5087,                         # 卖4
                5088,                         # 卖5
            ]
        }
        '''
        data = event.getData()

        if not isinstance(data, dict):
            return

        contractNo = data['ContractNo']
        if contractNo not in self._contractData:
            self._contractData[contractNo] = QuoteDataModel(self.logger, data)

        self._contractData[contractNo].deepSetContract(data)

    def onQuoteNotice(self, event):
        QuoteModel.updateLv1(self, event)

    def onDepthNotice(self, event):
        QuoteModel.updateLv2(self, event)
        
    def getExchangeTime(self, exchangeNo):
        if exchangeNo not in self._exchangeData:
            return ""
        return self._exchangeData[exchangeNo].getExchangeTime()
        
    def getExchangeStatus(self, exchangeNo):
        #self.logger.debug(str(self._exchangeData))
        if exchangeNo not in self._exchangeData:
            return ""
        return self._exchangeData[exchangeNo].getExchangeStatus()

    def getCommodityStatus(self, commNo):
        commSplit =  commNo.split('|')
        if len(commSplit) < 3:
            return ""
        exchangeNo = commSplit[0]
        commNo = commSplit[2]
        if exchangeNo not in self._exchangeData:
            return ""
        return self._exchangeData[exchangeNo].getCommodityStatus(commNo)

    def getLv1DataAndUpdateTime(self, contNo):
        if not contNo:
            return
        if contNo in self._contractData:
            metaData = self._contractData[contNo]._metaData
            resDict = { 'UpdateTime' : metaData['UpdateTime'],
                       'Lv1Data' : deepcopy(metaData['Lv1Data'])
            }
            return resDict
            
    def getUnderlayContractNo(self, contNo):
        if contNo not in self._underlayData:
            return ''
        return self._underlayData[contNo]

    # ////////////////////////即时行情////////////////////////////
    # 参数验装饰器
    def paramValidatorFactory(abnormalRet):
        def paramValidator(func):
            def validator(*args, **kwargs):
                if len(args) == 0:
                    return abnormalRet
                if len(args) == 1:
                    return func(*args, **kwargs)

                model = args[0]
                contNo = args[1]
                if not contNo:
                    contNo = model._config.getBenchmark()

                if contNo not in model._contractData:
                    return abnormalRet
                elif not isinstance(model._contractData[contNo], QuoteDataModel):
                    return abnormalRet

                if len(args) == 2:
                    return func(model, contNo)

                if len(args) == 3:
                    if args[2] > 10:
                        return abnormalRet
                    return func(model, contNo, args[2])
            return validator
        return paramValidator

    # 即时行情的更新时间
    @paramValidatorFactory("")
    def getQUpdateTime(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return str(quoteDataModel._metaData['UpdateTime'])

    # 合约最新卖价
    @paramValidatorFactory(0)
    def getQAskPrice(self, contNo, level=1):
        quoteDataModel = self._contractData[contNo]
        if level == 1:
            return quoteDataModel.getLv1Data(19, 0.0)

        lv2AskData = quoteDataModel._metaData["Lv2AskData"]
        if (level > len(lv2AskData)) or (not isinstance(lv2AskData[level-1], dict)):
            return 0

        return lv2AskData[level-1].get('Price')

    # 卖盘价格变化标志
    @paramValidatorFactory(0)
    def getQAskPriceFlag(self, contNo):
        # TODO: 增加卖盘价格比较逻辑
        return 1

    # 合约最新卖量
    @paramValidatorFactory(0)
    def getQAskVol(self, contNo, level=1):
        quoteDataModel = self._contractData[contNo]
        if level == 1:
            return quoteDataModel.getLv1Data(20, 0)

        lv2AskData = quoteDataModel._metaData["Lv2AskData"]
        if (level > len(lv2AskData)) or (not isinstance(lv2AskData[level - 1], dict)):
            return 0

        return lv2AskData[level - 1].get('Qty')

    # 实时均价即结算价
    @paramValidatorFactory(0)
    def getQAvgPrice(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(13, 0.0)

    # 合约最新买价
    @paramValidatorFactory(0)
    def getQBidPrice(self, contNo, level):
        quoteDataModel = self._contractData[contNo]
        if level == 1:
            return quoteDataModel.getLv1Data(17, 0.0)

        lv2BidData = quoteDataModel._metaData["Lv2BidData"]
        if (level > len(lv2BidData)) or (not isinstance(lv2BidData[level-1], dict)):
            return 0

        return lv2BidData[level-1].get('Price')

    # 买价变化标志
    @paramValidatorFactory(0)
    def getQBidPriceFlag(self, contNo):
        # TODO: 增加买价比较逻辑
        return 1

    # 指定合约,指定深度的最新买量
    @paramValidatorFactory(0)
    def getQBidVol(self, contNo, level):
        quoteDataModel = self._contractData[contNo]
        if level == 1:
            return quoteDataModel.getLv1Data(18, 0)

        lv2BidData = quoteDataModel._metaData["Lv2BidData"]
        if (level > len(lv2BidData)) or (not isinstance(lv2BidData[level - 1], dict)):
            return 0

        return lv2BidData[level - 1].get('Qty')

    # 当日收盘价，未收盘则取昨收盘
    @paramValidatorFactory(0)
    def getQClose(self, contNo):
        quoteDataModel = self._contractData[contNo]
        
        if 14 in quoteDataModel._metaData["Lv1Data"] and quoteDataModel._metaData["Lv1Data"][14] > 0:
            return quoteDataModel._metaData["Lv1Data"][14]
        else:
            return quoteDataModel._metaData["Lv1Data"][0]

    # 当日最高价
    @paramValidatorFactory(0)
    def getQHigh(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(5, 0.0)

    # 历史最高价
    @paramValidatorFactory(0)
    def getQHisHigh(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(7, 0.0)

    # 历史最低价
    @paramValidatorFactory(0)
    def getQHisLow(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(8, 0.0)

    # 内盘量，买入价成交为内盘
    @paramValidatorFactory(0)
    def getQInsideVol(self, contNo):
        # TODO: 计算买入价成交量逻辑
        return 0

    # 最新价
    @paramValidatorFactory(0)
    def getQLast(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(4, 0.0)

    # 现手
    @paramValidatorFactory(0)
    def getQLastVol(self, contNo):
        # TODO: 增加现手计算逻辑
        return 0

    # 当日最低价
    @paramValidatorFactory(0)
    def getQLow(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(6, 0.0)

    # 当日跌停板价
    @paramValidatorFactory(0)
    def getQLowLimit(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(10, 0.0)

    # 当日开盘价
    @paramValidatorFactory(0)
    def getQOpen(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(3, 0.0)

    # 持仓量
    @paramValidatorFactory(0)
    def getQOpenInt(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(12, 0)

    # 持仓量变化标志
    @paramValidatorFactory(0)
    def getQOpenIntFlag(self, contNo):
        # TODO: 增加持仓量变化比较逻辑
        return 1

    # 外盘量
    @paramValidatorFactory(0)
    def getQOutsideVol(self, contNo):
        # TODO: 增加外盘量计算逻辑
        return 0

    # 昨持仓量
    @paramValidatorFactory(0)
    def getQPreOpenInt(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(2, 0)

    # 昨结算
    @paramValidatorFactory(0)
    def getQPreSettlePrice(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(1, 0.0)

    # 当日涨跌
    @paramValidatorFactory(0)
    def getQPriceChg(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(112, 0.0)

    # 当日涨跌幅
    @paramValidatorFactory(0)
    def getQPriceChgRadio(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(113, 0)

    # 当日开仓量
    @paramValidatorFactory(0)
    def getQTodayEntryVol(self, contNo):
        # TODO: 增加当日开仓量的计算逻辑
        return 0

    # 当日平仓量
    @paramValidatorFactory(0)
    def getQTodayExitVol(self, contNo):
        # TODO: 增加当日平仓量的计算逻辑
        return 0

    # 当日成交量
    @paramValidatorFactory(0)
    def getQTotalVol(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(11, 0)

    # 当日成交额
    @paramValidatorFactory(0)
    def getQTurnOver(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(27, 0.0)

    # 当日涨停板价
    @paramValidatorFactory(0)
    def getQUpperLimit(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(9, 0.0)
        
    # 当日期权理论价
    @paramValidatorFactory(None)
    def getQTheoryPrice(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(30, None)

    # 当日期权波动率
    @paramValidatorFactory(None)
    def getQSigma(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(31, None)

    # 当日期权Delta
    @paramValidatorFactory(None)
    def getQDelta(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(32, None)

    # 当日期权Gamma
    @paramValidatorFactory(None)
    def getQGamma(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(33, None)

    # 当日期权Vega
    @paramValidatorFactory(None)
    def getQVega(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(34, None)

    # 当日期权Theta
    @paramValidatorFactory(None)
    def getQTheta(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(35, None)

    # 当日期权Rho
    @paramValidatorFactory(None)
    def getQRho(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return quoteDataModel.getLv1Data(36, None)

    # 行情数据是否有效
    @paramValidatorFactory(False)
    def getQuoteDataExist(self, contNo):
        quoteDataModel = self._contractData[contNo]
        return True if len(quoteDataModel._metaData["Lv1Data"]) > 0 else False
