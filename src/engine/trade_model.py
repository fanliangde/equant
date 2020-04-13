from capi.event import *
from copy import *
import threading

# #####################################交易数据模型#########################################
class TLogoinModel:
    '''登录账号信息'''
    def __init__(self, logger, loginNo, data):
        self.logger = logger
        self._loginNo = loginNo
        self._isReady = False
        
        # print("TLogoinModel", data)
        self._metaData = {
            'LoginNo'   : data['LoginNo']    ,  #登录账号
            'Sign'      : data['Sign']       ,  #标识
            'LoginName' : data['LoginName']  ,  #登录名称
            'LoginApi'  : data['LoginApi']   ,  #api类型
            'TradeDate' : data['TradeDate']  ,  #交易日期
            'IsReady'   : data['IsReady']       #是否准备就绪
        }
        
        self._userInfo = {}
        
        if data['IsReady'] == EEQU_READY:
            self._isReady = True
        
        self.logger.info("[LOGIN]%s,%s,%s,%s,%s,%s"%(
            data['LoginNo'], data['Sign'], data['LoginName'],
            data['LoginApi'], data['TradeDate'], data['IsReady']
        ))
        
    def getMetaData(self):
        return self._metaData
        
    def isReady(self):
        return self._isReady
        
    def getLoginNo(self):
        return self._loginNo
        
    def getLoginApi(self):
        return self._metaData['LoginApi']
    
    def getLoginUser(self):
        return self._userInfo
        
    def updateLoginInfo(self, loginNo, data):
        self.logger.info("[LOGIN] update login info: %s"%data)

        for k, v in data.items():
            if k == 'IsReady':
                if v == EEQU_NOTREADY:
                    self._isReady = False
                else:
                    self._isReady = True
            self._metaData[k] = v
            
    def updateUserInfo(self, userNo, userInfo):
        #先不存数据
        self._userInfo[userNo] = None

    def copyLoginInfoMetaData(self):
        return deepcopy(self._metaData) if len(self._metaData) > 0 else {}

class TUserInfoModel:
    '''资金账号信息'''
    def __init__(self, logger, loginInfo, data):
        self.logger = logger
        self._loginInfo = loginInfo
        self._loginNo = loginInfo.getLoginNo()
        self._loginApi = loginInfo.getLoginApi()
        self._userNo = data['UserNo']
        self._isReady = True
        self._isDataReady = False
        
        #print("TUserInfoModel", data)
        
        self._metaData = {
                'UserNo'    : data['UserNo'],
                'Sign'      : data['Sign'],
                'LoginNo'   : data['LoginNo'],
                'UserName'  : data['UserName'],
        }
        
        self._money   = {} #{'currencyNo' : TMoneyModel}
        self._order   = {} #{'OrderNo'    : TOrderModel}
        self._match   = {} #{'OrderNo'    : TMatchModel}
        self._position = {} #{'PositionNo' : TPostionModel}
        
        self.logger.info("[USER]%s,%s,%s,%s"%(
            data['UserNo'], data['Sign'], data['LoginNo'], data['UserName']
        ))
        
    def chkLoginNo(self, loginNo):
        return self._loginNo == loginNo
        
    def setDataReady(self):
        self._isDataReady = True
        
    def isDataReady(self):
        return self._isDataReady
    
    def setUserStatus(self, data):
        '''根据登录信息更新用户信息'''
        if 'LoginNo' not in data:
            return
            
        if data['LoginNo'] != self._loginNo:
            return
            
        if 'IsReady' not in data:
            return
        
        if data['IsReady'] == EEQU_NOTREADY:
            self._isReady = False
        else:
            self._isReady = True
        
    def isReady(self):
        return self._isReady

    def getMetaData(self):
        return self._metaData
        
    def getMoneyDict(self):
        return self._money
        
    def getOrderDict(self):
        return self._order
        
    def getMatchDict(self):
        return self._match
        
    def getPositionDict(self):
        return self._position
        
    def getSign(self):
        return self._metaData['Sign']
        
    def getContPos(self):
        '''获取该账户各合约持仓情况'''
        contPosDict = {}  #cont, bs, h, data
        
        if not self._isReady:
            return  contPosDict
        
        for v in self._position.values():
            data = v.getMetaData()
            if not data: continue
            key = data['Cont'] + data['Direct'] + data['Hedge'] 
            contPosDict[key] = data
            
        return contPosDict
        
    # 内盘有买卖两个方向， 外盘会对冲只有一个方向
    def getPositionInfo(self, contractNo, direct=None):
        isChinese = contractNo.split("|")[0].upper() in ["SHFE", "ZCE", "DCE", "CFFEX", "INE"]
        if not self._isReady or self._position is None:
            return None
        for positionNo, positionObj in self._position.items():
            if isChinese:
                if positionObj.getContractNo() == contractNo and direct==positionObj.getPositionInfo()["Direct"]:
                    return positionObj.getPositionInfo()
            else:
                if positionObj.getContractNo() == contractNo:
                    return positionObj.getPositionInfo()

    def updateMoney(self, data):
        currencyNo = data['CurrencyNo']
        if currencyNo not in self._money:
            money = TMoneyModel(self.logger, data)
            self._money[currencyNo] = money
        else:
            self._money[currencyNo].updateMoney(data)

    def updateOrder(self, data):
        orderId = data['OrderId']
        if orderId not in self._order:
            order = TOrderModel(self.logger, data)
            self._order[orderId] = order
        else:
            self._order[orderId].updateOrder(data)

    def updateMatch(self, data):
        orderNo = data['OrderNo']
        if orderNo not in self._match:
            match = TMatchModel(self.logger, data)
            self._match[orderNo] = match
        else:
            self._match[orderNo].updateMatch(data)

    def updatePosition(self, data):
        #先更新数据，再放队列，可能有线程安全问题
        posNo = data['PositionNo']
        if posNo not in self._position:
            pos = TPositionModel(self.logger, data)
            self._position[posNo] = pos
        else:
            self._position[posNo].updatePosition(data)


class TMoneyModel:
    '''资金信息'''
    def __init__(self, logger, data):
        self.logger = logger
        self._metaData = {}
        self._lock = threading.Lock()
        self.updateMoney(data)
        
    def updateMoney(self, data):
        with self._lock:
            self._metaData['UserNo']           = data['UserNo']        
            self._metaData['Sign']             = data['Sign']          
            self._metaData['CurrencyNo']       = data['CurrencyNo']       #币种号
            self._metaData['ExchangeRate']     = data['ExchangeRate']     #币种汇率
            self._metaData['FrozenFee']        = data['FrozenFee']        #冻结手续费
            self._metaData['FrozenDeposit']    = data['FrozenDeposit']    #冻结保证金
            self._metaData['Fee']              = data['Fee']              #手续费(包含交割手续费)
            self._metaData['Deposit']          = data['Deposit']          #保证金
            self._metaData['FloatProfit']      = data['FloatProfit']      #盯式盈亏，不含LME持仓盈亏
            self._metaData['FloatProfitTBT']   = data['FloatProfitTBT']   #逐笔浮赢
            self._metaData['CoverProfit']      = data['CoverProfit']      #盯市平盈
            self._metaData['CoverProfitTBT']   = data['CoverProfitTBT']   #逐笔平盈
            self._metaData['Balance']          = data['Balance']          #今资金=PreBalance+Adjust+CashIn-CashOut-Fee(TradeFee+DeliveryFee+ExchangeFee)+CoverProfitTBT+Premium
            self._metaData['Equity']           = data['Equity']           #今权益=Balance+FloatProfitTBT(NewFloatProfit+LmeFloatProfit)+UnExpiredProfit
            self._metaData['Available']        = data['Available']        #今可用=Equity-Deposit-Frozen(FrozenDeposit+FrozenFee)
            self._metaData['UpdateTime']       = data['UpdateTime']       #资金更新时间戳
        
        '''self.logger.info("[MONEY]%s,%f,%f,%f,%f,%f,%f,%f,%f,%f,%s"%(
            data['CurrencyNo'], data['Fee'],data['Deposit'], data['FloatProfit'],
            data['FloatProfitTBT'],data['CoverProfit'],data['CoverProfitTBT'],
            data['Balance'], data['Equity'],data['Available'],data['UpdateTime']
        ))'''
        
    def getMetaData(self):
        data = None
        with self._lock:
            data = deepcopy(self._metaData)
        return data
        
class TOrderModel:
    '''委托信息'''
    def __init__(self, logger, data):
        self.logger = logger
        self._metaData = {}
        self.updateOrder(data)
        
    def updateOrder(self, data):
        self._metaData['UserNo']            =  data['UserNo']          #             
        self._metaData['Sign']              =  data['Sign']           
        self._metaData['Cont']              =  data['Cont']              # 行情合约
        self._metaData['OrderType']         =  data['OrderType']         # 定单类型
        self._metaData['ValidType']         =  data['ValidType']         # 有效类型
        self._metaData['ValidTime']         =  data['ValidTime']         # 有效日期时间(GTD情况下使用)
        self._metaData['Direct']            =  data['Direct']            # 买卖方向
        self._metaData['Offset']            =  data['Offset']            # 开仓平仓 或 应价买入开平
        self._metaData['Hedge']             =  data['Hedge']             # 投机保值
        self._metaData['OrderPrice']        =  data['OrderPrice']        # 委托价格 或 期权应价买入价格
        self._metaData['TriggerPrice']      =  data['TriggerPrice']      # 触发价格
        self._metaData['TriggerMode']       =  data['TriggerMode']       # 触发模式
        self._metaData['TriggerCondition']  =  data['TriggerCondition']  # 触发条件
        self._metaData['OrderQty']          =  data['OrderQty']          # 委托数量 或 期权应价数量
        self._metaData['StrategyType']      =  data['StrategyType']      # 策略类型
        self._metaData['Remark']            =  data['Remark']            #下单备注字段，只有下单时生效。
        self._metaData['AddOneIsValid']     =  data['AddOneIsValid']     # T+1时段有效(仅港交所)
        self._metaData['OrderState']        =  data['OrderState']        # 委托状态
        self._metaData['OrderId']           =  data['OrderId']           # 定单号
        self._metaData['OrderNo']           =  data['OrderNo']           # 委托号
        self._metaData['MatchPrice']        =  data['MatchPrice']        # 成交价
        self._metaData['MatchQty']          =  data['MatchQty']          # 成交量
        self._metaData['ErrorCode']         =  data['ErrorCode']         # 最新信息码
        self._metaData['ErrorText']         =  data['ErrorText']         # 最新错误信息
        self._metaData['InsertTime']        =  data['InsertTime']        # 下单时间
        self._metaData['UpdateTime']        =  data['UpdateTime']        # 更新时间
        
        #self.logger.info("ORDER:%s,%f,%d"%(self._metaData['OrderNo'], self._metaData['OrderPrice'], self._metaData['OrderQty']))
        #print('updateOrder', self._metaData['OrderNo'], self._metaData['OrderPrice'], self._metaData['OrderQty'])
        
    def getMetaData(self):
        return self._metaData
        
class TMatchModel:
    '''成交信息'''
    def __init__(self, logger, data):
        self.logger = logger
        self._metaData = {}
        self.updateMatch(data)
        
    def updateMatch(self, data):
        dct = {}
        dct['UserNo'] = data['UserNo']  #
        dct['Sign'] = data['Sign']
        dct['Cont'] = data['Cont']  # 行情合约
        dct['Direct'] = data['Direct']  # 买卖方向
        dct['Offset'] = data['Offset']  # 开仓平仓 或 应价买入开平
        dct['Hedge'] = data['Hedge']  # 投机保值
        dct['OrderNo'] = data['OrderNo']  # 委托号
        dct['MatchPrice'] = data['MatchPrice']  # 成交价
        dct['MatchQty'] = data['MatchQty']  # 成交量
        dct['FeeCurrency'] = data['FeeCurrency']  # 手续费币种
        dct['MatchFee'] = data['MatchFee']  # 手续费
        dct['MatchDateTime'] = data['MatchDateTime']  # 成交时间
        dct['AddOne'] = data['AddOne']  # T+1成交
        dct['Deleted'] = data['Deleted']  # 是否删除
        dct['MatchNo'] = data['MatchNo']  # 成交号

        key = (dct["MatchNo"], dct["Cont"], dct["Direct"])
        self._metaData[key] = dct
        #self.logger.info("MATCH:%s"%self._metaData)
        
    def getMetaData(self):
        return self._metaData
        
class TPositionModel:
    '''持仓信息'''
    def __init__(self, logger, data):
        self.logger = logger
        self._lock = threading.Lock()
        self._metaData = {}
        self.updatePosition(data)
        
    def updatePosition(self, data):
        #多线程访问
        with self._lock:
            self._metaData['PositionNo']        =  data['PositionNo']
            self._metaData['UserNo']            =  data['UserNo']            #             
            self._metaData['Sign']              =  data['Sign']           
            self._metaData['Cont']              =  data['Cont']              # 行情合约
            self._metaData['Direct']            =  data['Direct']            # 买卖方向
            self._metaData['Hedge']             =  data['Hedge']             # 投机保值
            self._metaData['Deposit']           =  data['Deposit']           # 初始保证金
            self._metaData['PositionQty']       =  data['PositionQty']        # 总持仓
            self._metaData['PrePositionQty']    =  data['PrePositionQty']          # 昨持仓数量
            self._metaData['PositionPrice']     =  data['PositionPrice']       # 价格
            self._metaData['ProfitCalcPrice']   =  data['ProfitCalcPrice']          # 浮盈计算价
            self._metaData['FloatProfit']       =  data['FloatProfit']     # 浮盈
            self._metaData['FloatProfitTBT']    =  data['FloatProfitTBT']            # 逐笔浮盈
            
            #self.logger.info("Position:%s"%self._metaData)
            
    def getMetaData(self):
        data = None
        with self._lock:
            data = deepcopy(self._metaData)    
        return data

    def getContractNo(self):
        return self._metaData["Cont"]

    def getPositionDirect(self):
        return self._metaData["Direct"]

    def getPositionInfo(self):
        return {
            "TotalPos":self._metaData["PositionQty"],
            "TodayPos":self._metaData["PositionQty"]-self._metaData["PrePositionQty"],
            "PrePos"  :self._metaData["PrePositionQty"],
            "Direct"  :self._metaData["Direct"]
        }


class TradeModel:
    
    def __init__(self, logger):
        self.logger = logger
        
        self._loginInfo = {} #登录账号{'LoginNo': {:}}
        self._userInfo = {}  #资金账号{'UserNo' : {:}}
        self._orderUserMap = {}
        
    ###################################################################
    def getLoginInfo(self):
        return self._loginInfo

    def getUserInfo(self):
        return self._userInfo
        
    def getLoginUser(self, loginNo):
        if loginNo not in self._loginInfo:
            return {}
        return self._loginInfo[loginNo].getLoginUser()
        
    def setDataReady(self, userNo):
        if userNo in self._userInfo:
            self._userInfo[userNo].setDataReady()
            
    def isAllDataReady(self):
        if not self._userInfo:
            return False
            
        for v in self._userInfo.values():
            if not v.isDataReady():
                return False
                
        return True
        
    def getUserNoByOrderId(self, orderId):
        if orderId not in self._orderUserMap:
            return ''
        return self._orderUserMap[orderId]
        
    ###################################################################
    def setUserStatus(self, loginDict):
        for v in self._userInfo.values():
            v.setUserStatus(loginDict)
            
    def addLoginInfo(self, data):
        '''增加登录信息，有则更新'''
        loginNo = data['LoginNo']
        if loginNo not in self._loginInfo:
            self._loginInfo[loginNo] = TLogoinModel(self.logger, loginNo, data)
        else:
            self._loginInfo[loginNo].updateLoginInfo(loginNo, data)
            
    def delLoginInfo(self, login):
        '''删除登录信息'''
        loginNo = login['LoginNo']
        if loginNo not in self._loginInfo:
            return
        self._loginInfo.pop(loginNo)
        
    def delUserInfo(self, loginNo):
        '''删除该登录账户下的所有用户信息'''
        popUserList = []
        
        for k, v in self._userInfo.items():
            if v.chkLoginNo(loginNo):
                popUserList.append(k)
                
        for user in popUserList:
            self._userInfo.pop(user)
            
    def getLoginApi(self, userNo):
        if userNo not in self._userInfo:
            return ''
            
        return self._userInfo[userNo]._loginApi
        
    def chkTradeDate(self, data):
        if data['LoginNo'] not in self._loginInfo:
            return False
            
        login = self._loginInfo[data['LoginNo']]
        meta  = login.getMetaData()
        #当前的交易日和上一交易日不一样
        return (data['TradeDate'] != meta['TradeDate'])
              

    # 更新登录信息
    def updateLoginInfo(self, apiEvent):
        ''''''
        dataList = apiEvent.getData()
        #self.logger.debug("updateLoginInfo:%s"%dataList)
        for data in dataList:
            loginNo = data['LoginNo']
            if loginNo not in self._loginInfo:
                self._loginInfo[loginNo] = TLogoinModel(self.logger, loginNo, data)
            else:
                self._loginInfo[loginNo].updateLoginInfo(loginNo, data)
                self.setUserStatus(data)

    def updateUserInfo(self, apiEvent):
        dataList = apiEvent.getData()
        #self.logger.debug("updateUserInfo:%s"%dataList)
        for data in dataList:
            loginNo = data['LoginNo']
            if loginNo not in self._loginInfo:
                self.logger.error("The login account(%s) doesn't login!"%loginNo)
                continue
                
            userNo = data['UserNo']
            userInfo = TUserInfoModel(self.logger, self._loginInfo[loginNo], data)

            self._loginInfo[loginNo].updateUserInfo(userNo, userInfo)
            self._userInfo[userNo] = userInfo
        
        # print(apiEvent.getData())
        
    def getSign(self, userNo):
        if userNo not in self._userInfo:
            return ''
        
        return self._userInfo[userNo].getSign()

    def updateMoney(self, apiEvent):
        dataList = apiEvent.getData()
        #self.logger.debug("updateMoney:%s"%dataList)
        for data in dataList:
            userNo = data['UserNo']
            if userNo not in self._userInfo:
                self.logger.error("[updateMoney]The user account(%s) doesn't login!"%userNo)
                continue
            self._userInfo[userNo].updateMoney(data)
            
        #print(apiEvent.getData())
        
    def updateOrderData(self, apiEvent):
        dataList = apiEvent.getData()
        #self.logger.debug("updateOrderData:%s"%dataList)
        for data in dataList:
            userNo = data['UserNo']
            if userNo not in self._userInfo:
                self.logger.error("[updateOrderData]The user account(%s) doesn't login!"%userNo)
                continue
            self._orderUserMap[data['OrderId']] = userNo
            #self.logger.debug('[ORDER]%s'%data)
            self._userInfo[userNo].updateOrder(data)

            
    def updateMatchData(self, apiEvent):
        dataList = apiEvent.getData()
        #self.logger.debug("updateMatchData:%s"%dataList)
        for dct in dataList:
            for key in dct:
                userNo = dct[key]['UserNo']
                if userNo not in self._userInfo:
                    self.logger.error("[updateMatchData]The user account(%s) doesn't login!" % userNo)
                    continue
                    # self.logger.debug('[MATCH]%s'%data)
                self._userInfo[userNo].updateMatch(dct[key])
            
    def updatePosData(self, apiEvent):
        dataList = apiEvent.getData()
        #self.logger.debug("updatePosData:%s"%dataList)
        for data in dataList:
            userNo = data['UserNo']
            if userNo not in self._userInfo:
                self.logger.error("[updatePosData]The user account(%s) doesn't login!"%userNo)
                continue
                
            #self.logger.debug('[POS]%s'%data)
        
            self._userInfo[userNo].updatePosition(data)