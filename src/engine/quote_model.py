from capi.event import *
from copy import deepcopy
from datetime import datetime,timedelta
        
# 即时行情
class QuoteModel:
    def __init__(self, logger):
        self.logger = logger
        # 全量交易所、品种、合约
        self._exchangeData  = {}  #{key=ExchangeNo,value=ExchangeModel}
        self._commodityData = {}  #{key=CommodityNo, value=CommodityModel}
        self._contractData  = {}  #{key=ContractNo, value=QuoteDataModel}
        self._underlayData  = {}  #{key=ContractNo, value=UnderlayContractNo}

        self._baseDataReady = False
        
    def getExchangeDict(self):
        return self._exchangeData
        
    def getCommodityDict(self):
        return self._commodityData
        
    def getContractDict(self):
        return self._contractData
        
    def getUnderlyDict(self):
        return self._underlayData

    # 交易所
    def updateExchange(self, apiEvent):
        dataList = apiEvent.getData()
        for dataDict in dataList:
            self._exchangeData[dataDict['ExchangeNo']] = ExchangeModel(self.logger, dataDict)
        if apiEvent.isChainEnd():
            self.logger.info('Initialize exchange data(%d) successfully!'%len(self._exchangeData))
            
    # 交易所状态
    def updateExchangeStatus(self, apiEvent):
        dataList = apiEvent.getData()
        strategyId = apiEvent.getStrategyId()

        for dataDict in dataList:
            if dataDict['ExchangeNo'] not in self._exchangeData:
                self._exchangeData[dataDict['ExchangeNo']] = ExchangeModel(self.logger, dataDict)
                self.logger.error("updateExchangeStatus exchangeno(%s) error!"%dataDict['ExchangeNo'])
                continue
            exchangeModel = self._exchangeData[dataDict['ExchangeNo']]
            exchangeModel.updateStatus(strategyId, dataDict)
        if apiEvent.isChainEnd():
            #self.logger.info('Initialize exchange status successfully!') 
            pass

    # 品种
    def updateCommodity(self, apiEvent):
        dataList = apiEvent.getData()
        for dataDict in dataList:
            self._commodityData[dataDict['CommodityNo']] = CommodityModel(self.logger, dataDict)    
        if apiEvent.isChainEnd():
            self.logger.info('Initialize commodity data(%d) successfully!' % len(self._commodityData))

    # 时间模板
    def updateTimeBucket(self, apiEvent):
        dataList = apiEvent.getData()

        if len(dataList) == 0:
            return 0

        dataDict = dataList[0]
        commodity = dataDict['Commodity']
        if commodity in self._commodityData:
            self._commodityData[commodity].updateTimeBucket(dataList)

        if apiEvent.isChainEnd():
            pass

    # 合约映射
    def updateUnderlayMap(self, apiEvent):
        dataList = apiEvent.getData()
        for data in dataList:
            contNo = data['ContractNo']
            underlayContNo = data['UnderlayContractNo']
            self._underlayData[contNo] = underlayContNo
            
        if apiEvent.isChainEnd():
            self.logger.info('Initialize trend conotract data(%d) successfully!'%len(self._underlayData))
            self._baseDataReady = True

    # 合约
    def updateContract(self, apiEvent):
        dataList = apiEvent.getData()
        for dataDict in dataList:
            self._contractData[dataDict['ContractNo']] = QuoteDataModel(self.logger, dataDict)
            
        if apiEvent.isChainEnd():
            self.logger.info('Initialize contract data(%d) successfully!'%len(self._contractData))
            self._baseDataReady = True

    def updateLv1(self, apiEvent):
        '''更新普通行情'''
        self._updateQuote(apiEvent, 'N')
       
    def updateLv2(self, apiEvent):
        '''更新深度行情'''
        self._updateQuote(apiEvent, 'D') 
        
    def _updateQuote(self, apiEvent, lv):
        contractNo = apiEvent.getContractNo()
        if contractNo not in self._contractData:
            #策略模块也使用该函数
            dataDict = {
                'ExchangeNo'  : '',
                'CommodityNo' : '',
                'ContractNo'  : contractNo,
            }
            self._contractData[contractNo] = QuoteDataModel(self.logger, dataDict)
            
        dataList = apiEvent.getData()
        data = self._contractData[contractNo]
        
        for oneDict in dataList:
            if lv == 'N':
                data.updateLv1(oneDict)
            else:
                data.updateLv2(oneDict)
        
class ExchangeModel:
    '''
    _metaData = {
        'ExchangeNo'      : 'ZCE',             #交易所编号
        'ExchangeName'    : '郑州商品交易所'   #简体中文名称
        'Sign'            : 服务器标识
        'ExchangeDateTime': 交易所系统时间
        'LocalDateTime'   : 本地系统时间
        'TradeState'      : 交易所状态
    }
    '''
    def __init__(self, logger, dataDict):
        '''
        dataDict ={
            'ExchangeNo'  : value,
            'ExchangeName': value,
        } 
        '''
        self.logger = logger
        self._exchangeNo = dataDict['ExchangeNo']
        self._metaData = {
            'ExchangeNo'       : dataDict['ExchangeNo'],
            'ExchangeName'     : dataDict['ExchangeName'],
            'Sign'             : '',
            'ExchangeDateTime' : '',
            'LocalDateTime'    : '',
            'TradeState'       : '',
            'CommTradeState'   : {},
        }
        self._timeDiff = 0
        self._delta = 0
        
    def updateStatus(self, strategyId, dataDict):
        #self.logger.debug("UpdateCommTradeState:%s" %dataDict)
        if dataDict['Sign'] != '':
            self._metaData['Sign']  = dataDict['Sign']   
        if dataDict['ExchangeDateTime'] != '' and dataDict['LocalDateTime'] != '':
            self._metaData['ExchangeDateTime'] = dataDict['ExchangeDateTime']
            self._metaData['LocalDateTime']    = dataDict['LocalDateTime'] 
            #计算差值
            exchange = datetime.strptime(dataDict['ExchangeDateTime'],"%Y-%m-%d %H:%M:%S")
            local    = datetime.strptime(dataDict['LocalDateTime'],"%Y-%m-%d %H:%M:%S")
            if exchange > local:
                self._timeDiff = (exchange-local).seconds
            else:
                self._timeDiff = -((local-exchange).seconds)
            self._delta = timedelta(seconds=self._timeDiff)
            #只在引擎中打印
            if strategyId == 0:
                #self.logger.info("Update %s time diff:%d"%(dataDict['ExchangeNo'], self._timeDiff))
                pass
            
        if dataDict['TradeState'] != '': 
            self._metaData['TradeState'] = dataDict['TradeState']
            #只在引擎中打印
            if strategyId == 0:
                #self.logger.info("Update exchange status(%s:%s)"%(dataDict['ExchangeNo'], self._metaData['TradeState']))
                pass
                
        if 'CommTradeState' in dataDict:
            self._metaData["CommTradeState"] = dataDict['CommTradeState']
        elif 'CommodityNo' in dataDict and dataDict['CommodityNo']:
            #self.logger.debug("UpdateCommTradeState:%s:%s" %(dataDict['CommodityNo'], dataDict['TradeState']))
            self._metaData["CommTradeState"][dataDict['CommodityNo']] = dataDict['TradeState']
            

    def getExchangeTime(self):
        '''获取交易所时间'''
        now = datetime.now()
        delta = timedelta(seconds=self._timeDiff)
        sys = now + delta
        return sys.strftime('%Y-%m-%d %H:%M:%S')
        
    def getExchangeStatus(self):
        #self.logger.debug(self._metaData)
        return self._metaData['TradeState']
        
    def getCommodityStatus(self, commNo):
        if commNo not in self._metaData["CommTradeState"]:
            return ""
        else:
            return self._metaData["CommTradeState"][commNo]

    def getExchange(self):
        return self._metaData
        
class CommodityModel:
    '''
    _metaData = {
        'ExchangeNo'   : 'ZCE'             # value,str 交易所编号
        'CommodityNo'  : 'ZCE|F|SR'        # value,str 品种编号
        'CommodityType': 'F'               # value,str 品种类型
        'CommodityName': '白糖'            # value,str 品种名称
        'PriceNume'    : 1                 # value,float 报价分子
        'PriceDeno'    : 1                 # value,float 报价分母
        'PriceTick'    : 1                 # value,float 最小变动价
        'PricePrec'    : 1                 # value,float 价格精度
        'TradeDot'     : 10                # value,float 每手乘数
        'CoverMode'    : 'C'               # value,str 平仓方式，区分开平
        'TimeBucket'   : []                # 时间模板信息
    }
    '''
    def __init__(self, logger, dataDict):
        self.logger = logger
        self.commdityNo = dataDict['CommodityNo']
        timeBucket = dataDict['TimeBucket'] if 'TimeBucket' in dataDict else []

        self._metaData = {
            'ExchangeNo'    : dataDict['ExchangeNo'],
            'CommodityNo'   : dataDict['CommodityNo'],
            'CommodityType' : dataDict['CommodityType'],
            'CommodityName' : dataDict['CommodityName'],
            'PriceNume'     : dataDict['PriceNume'],
            'PriceDeno'     : dataDict['PriceDeno'],
            'PriceTick'     : dataDict['PriceTick'],
            'PricePrec'     : dataDict['PricePrec'],
            'TradeDot'      : dataDict['TradeDot'],
            'CoverMode'     : dataDict['CoverMode'],
            'TimeBucket'    : timeBucket,
        }
        
    def getCommodity(self):
        return self._metaData

    def updateTimeBucket(self, dataList):
        self._metaData['TimeBucket'] = dataList
        #self.logger.debug("commd:%s, len:%d, tblist:%s" %(self._metaData['CommodityNo'], len(dataList), str(dataList)))

class QuoteDataModel:
    '''
    _metaData = {
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
        
    def __init__(self, logger, dataDict):
        '''
        dataDict ={
            'ExchangeNo' : value,
            'CommodityNo': value,
            'ContractNo' : value,
        } 
        '''
        
        self.logger = logger
        self._contractNo = dataDict['ContractNo']
        self._metaData = {
            'ExchangeNo' : dataDict['ExchangeNo'],    # 交易所编号
            'CommodityNo': dataDict['CommodityNo'],   # 品种编号
            'ContractNo' : dataDict['ContractNo'],    # 合约编号
            'UpdateTime' : 0,                         # 行情时间戳
            'Lv1Data'    : {},                        # 普通行情
            'Lv2BidData' : [0 for i in range(10)],    # 买深度
            'Lv2AskData' : [0 for i in range(10)]     # 卖深度
        }

    def getContract(self):
        return self._metaData
        
    def deepSetContract(self, dataDict):
        self._metaData = deepcopy(dataDict)
        
    def updateLv1(self, oneDict):
        '''
        功能：更新普通行情
        参数: oneDict = {
            UpdateTime : value,
            FieldData  : {
                'FidMean1' : 'FidValue1',
                'FidMean2' : 'FidValue2'
                ...
            }
        }
        '''
        self._metaData['UpdateTime'] = oneDict['UpdateTime']
        fieldDict = oneDict['FieldData']
        
        for k, v in fieldDict.items():
            self._metaData['Lv1Data'][k] = v
        
    def updateLv2(self, oneDict):
        '''
        功能：更新深度行情
        参数：oneDict = {
            'Bid' : [
                {'Price' : Price1,  'Qty' : Qty1},
                {'Price' : Price2,  'Qty' : Qty2},
                ...
                {'Price' : Price10, 'Qty' : Qty10}
            ], 
            
            'Ask' : [
                {'Price' : Price1,  'Qty' : Qty1},
                {'Price' : Price2,  'Qty' : Qty2},
                ...
                {'Price' : Price10, 'Qty' : Qty10}
            ],
        }
        '''
        # 9.5传递全量深度，直接拷贝
        self._metaData['Lv2BidData'] = oneDict['Bid'][:]
        self._metaData['Lv2AskData'] = oneDict['Ask'][:]

    def getLv1Data(self, key, errRet):
        if key not in self._metaData['Lv1Data']:
            return errRet
        #self.logger.debug("%d:%s" %(key, str(self._metaData['Lv1Data'][key])))
        return self._metaData['Lv1Data'][key]