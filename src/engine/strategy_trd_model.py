import numpy as np
from capi.com_types import *
from .engine_model import *
import time, sys, datetime
from .trade_model import TradeModel

class StrategyTrade(TradeModel):
    '''交易数据模型'''
    def __init__(self, strategy, config):
        self.logger = strategy.logger
        self._strategy = strategy
        TradeModel.__init__(self, self.logger)
        self._config = config
        #self._selectedUserNo = self._config._metaData['Money']['UserNo']
        # print("===== StrategyTrade ====", self._config._metaData)
        
    def initialize(self):
        self._selectedUserNo = self._config.getUserNo()

    def getAccountId(self):
        '''
        :return:当前公式应用的交易帐户ID
        '''
        if not self._selectedUserNo:
            return ''
        
        if self._selectedUserNo not in self._userInfo:
            return ''
        
        user = self._userInfo[self._selectedUserNo]
        if not user.isReady():
            return ''
        
        return self._selectedUserNo
        
    def getAllAccountId(self):
        '''
        获取所有登录账号ID
        '''
        accList = []
        for k, v in self._userInfo.items():
            if not v.isReady():
                continue
            accList.append(k)
        return accList

    def getAllPositionSymbol(self, userNo):
        '''
        :return:所有持仓合约
        ''' 
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if len(self._userInfo) == 0 or userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return []

        tUserInfoModel = self._userInfo[userNo]
        if not tUserInfoModel.isReady():
            return []
        
        if len(tUserInfoModel._position) == 0:
            return []

        contList = []
        for positionNo in list(tUserInfoModel._position.keys()):
            position = tUserInfoModel._position[positionNo]
            contNo = position._metaData['Cont']
            if contNo not in contList:
                contList.append(contNo)
        return contList

    def getDataFromTMoneyModel(self, userNo, key):
        '''
        获取self._userInfo中当前账户指定的资金信息
        :param key:需要的资金信息的key
        :return:资金信息
        '''       
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo       
        
        if len(self._userInfo) == 0 or userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return 0

        tUserInfoModel = self._userInfo[userNo]
        if not tUserInfoModel.isReady():
            return 0
        
        if len(tUserInfoModel._money) == 0:
            return 0

        tMoneyModel = None
        if 'Base' in tUserInfoModel._money:
            tMoneyModel = tUserInfoModel._money['Base']
        elif len(tUserInfoModel._money) > 0:
            tMoneyModelList = list(tUserInfoModel._money.values())
            tMoneyModel = tMoneyModelList[0]

        if not tMoneyModel or key not in tMoneyModel._metaData:
            return 0

        return tMoneyModel._metaData[key]
        
    def getSign(self, userNo):
        '''
        :return: 获取当前账户的服务器标识
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo

        if userNo not in self._userInfo:
            return None
        return self._userInfo[userNo].getSign()

    def getCost(self, userNo):
        '''
        :return: 当前公式应用的交易帐户的手续费
        '''  
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
        
        return self.getDataFromTMoneyModel(userNo, 'Fee')

    def getCurrentEquity(self, userNo):
        '''
        :return:当前公式应用的交易帐户的动态权益
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getDataFromTMoneyModel(userNo, 'Equity')

    def getFreeMargin(self, userNo):
        '''
        :return:当前公式应用的交易帐户的可用资金
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getDataFromTMoneyModel(userNo, 'Available')

    def getAMargin(self, userNo):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getDataFromTMoneyModel(userNo, 'Deposit')

    def getProfitLoss(self, userNo):
        '''
        :return:当前公式应用的交易帐户的浮动盈亏
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getDataFromTMoneyModel(userNo, 'FloatProfit')

    def getPerProfitLoss(self, userNo):
        '''
        :return:当前公式应用的交易帐户的逐笔浮盈
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo

        return self.getDataFromTMoneyModel(userNo, 'FloatProfitTBT')

    def getCoverProfit(self, userNo):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getDataFromTMoneyModel(userNo, 'CoverProfit')

    def getPerCoverProfit(self, userNo):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo

        return self.getDataFromTMoneyModel(userNo, 'CoverProfitTBT')

    def getTotalFreeze(self, userNo):
        '''
        :return:当前公式应用的交易帐户的冻结资金
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getDataFromTMoneyModel(userNo, 'FrozenFee') + self.getDataFromTMoneyModel(userNo, 'FrozenDeposit')

    def getItemSumFromPositionModel(self, userNo, direct, contNo, key, lastPrice=0, contUnit=0):
        '''
        获取某个账户下所有指定方向、指定合约的指标之和，
        其中指标买浮动盈亏，卖浮动盈亏和总浮动盈亏因由9.5实时传数据数据量较大，这里通过传入最新价和每手乘数自己计算
        :param direct: 买卖方向，为空时表示所有方向
        :param contNo: 合约编号
        :param key: 指标名称
        :param lastPrice: 合约最新价用于浮动盈亏的计算
        :return:
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if len(self._userInfo) == 0 or userNo not in self._userInfo:
            return 0

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._position) == 0:
            return 0

        excDict = ("FloatProfitTBT", "FloatProfit")  # 需要单独计算的关键字
        contractNo = self._config.getBenchmark() if not contNo else contNo
        itemSum = 0.0
        for orderNo in list(tUserInfoModel._position.keys()):
            tPositionModel = tUserInfoModel._position[orderNo]
            if tPositionModel._metaData['Cont'] == contractNo and key in tPositionModel._metaData:
                if key in excDict:
                    if direct == "B" and tPositionModel._metaData["Direct"] == direct:     # 计算买浮动盈亏
                        itemSum += (lastPrice - tPositionModel._metaData["PositionPrice"]) * \
                                   tPositionModel._metaData["PositionQty"] * contUnit
                    elif direct == "S" and tPositionModel._metaData["Direct"] == direct:   # 计算卖浮动盈亏
                        itemSum += (tPositionModel._metaData["PositionPrice"] - lastPrice) * \
                                   tPositionModel._metaData["PositionQty"] * contUnit
                    elif direct == "":    # 计算总浮动盈亏
                        temp = (lastPrice - tPositionModel._metaData["PositionPrice"]) * \
                                   tPositionModel._metaData["PositionQty"] * contUnit
                        if tPositionModel._metaData["Direct"] == "S":  # 卖出持仓上述结果要取反
                            temp = -temp
                        itemSum += temp
                    continue
                if not direct or tPositionModel._metaData['Direct'] == direct:
                    itemSum += tPositionModel._metaData[key]

        return itemSum

    def getBuyAvgPrice(self, userNo, contNo):
        '''
        :return:当前公式应用的帐户下当前商品的买入持仓均价
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if len(self._userInfo) == 0 or userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return 0

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._position) == 0:
            return 0

        contNo = self._config.getBenchmark() if not contNo else contNo
        priceSum = 0.0
        posSum = 0
        for orderNo in list(tUserInfoModel._position.keys()):
            tPositionModel = tUserInfoModel._position[orderNo]
            if tPositionModel._metaData['Cont'] == contNo and tPositionModel._metaData['Direct'] == 'B':
                priceSum += tPositionModel._metaData['PositionPrice'] * tPositionModel._metaData['PositionQty']
                posSum += tPositionModel._metaData['PositionQty']

        return priceSum / posSum if posSum > 0 else 0.0

    def getBuyPosition(self, userNo, contNo):
        '''
        :return:当前公式应用的帐户下当前商品的买入持仓
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return int(self.getItemSumFromPositionModel(userNo, 'B', contNo,  'PositionQty'))

    def getBuyPositionCanCover(self, userNo, contNo):
        '''买仓可平数量'''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if not contNo:
            contNo = self._config.getBenchmark()
        buyPos = self.getBuyPosition(userNo, contNo) - self.getQueueSumFromOrderModel(userNo, 'S', contNo, ('C', 'T'))
        return int(buyPos)

    def getQueueSumFromOrderModel(self, userNo, direct, contNo, offset):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if len(self._userInfo) == 0 or userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return 0
            
        tUserInfoModel = self._userInfo[userNo]

        if len(tUserInfoModel._order) == 0:
            return 0

        queueSum = 0
        for orderKey in list(tUserInfoModel._order.keys()):
            orderModel = tUserInfoModel._order[orderKey]
            if contNo == orderModel._metaData['Cont'] and direct == orderModel._metaData['Direct'] and orderModel._metaData['Offset'] in offset:
                if orderModel._metaData['OrderState'] == '4':
                    # 已排队
                    queueSum += orderModel._metaData['OrderQty']
                elif orderModel._metaData['OrderState'] == '5':
                    # 部分成交
                    queueSum += orderModel._metaData['OrderQty'] - orderModel._metaData['MatchQty']

        return queueSum

    def getBuyProfitLoss(self, userNo, contNo, lastPrice, contUnit):
        '''
        :param userNo: 用户交易账号
        :param contNo: 合约编号
        :param lastPrice: 该合约最新价
        :param contUnit:  该合约的每手乘数
        :return: 当前公式应用的帐户下当前商品的买入持仓盈亏
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getItemSumFromPositionModel(userNo, 'B', contNo, 'FloatProfit', lastPrice, contUnit)

    def getSellAvgPrice(self, userNo, contNo):
        '''
        :return: 当前公式应用的帐户下当前商品的卖出持仓均价
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if len(self._userInfo) == 0 or userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return 0

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._position) == 0:
            return 0

        contNo = self._config.getBenchmark() if not contNo else contNo
        priceSum = 0.0
        posSum = 0
        for orderNo in list(tUserInfoModel._position.keys()):
            tPositionModel = tUserInfoModel._position[orderNo]
            if tPositionModel._metaData['Cont'] == contNo and tPositionModel._metaData['Direct'] == 'S':
                priceSum += tPositionModel._metaData['PositionPrice'] * tPositionModel._metaData['PositionQty']
                posSum += tPositionModel._metaData['PositionQty']

        return priceSum / posSum if posSum > 0 else 0.0

    def getSellPosition(self, userNo, contNo):
        '''
        :return: 当前公式应用的帐户下当前商品的卖出持仓
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return int(self.getItemSumFromPositionModel(userNo, 'S', contNo, 'PositionQty'))

    def getSellPositionCanCover(self, userNo, contNo):
        '''卖仓可平数量'''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if not contNo:
            contNo = self._config.getBenchmark()
        sellPos = self.getSellPosition(userNo, contNo) - self.getQueueSumFromOrderModel(userNo, 'B', contNo, ('C', 'T'))
        return int(sellPos)

    def getSellProfitLoss(self, userNo, contNo, lastPrice, contUnit):
        '''
        :param userNo: 用户交易账号
        :param contNo: 合约编号
        :param lastPrice: 该合约最新价
        :param contUnit:  该合约的每手乘数
        :return: 当前公式应用的帐户下当前商品的卖出持仓盈亏
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getItemSumFromPositionModel(userNo, 'S', contNo, 'FloatProfit', lastPrice, contUnit)

    def getTotalAvgPrice(self, userNo, contNo):
        '''
        :return: 当前公式应用的帐户下当前商品的持仓均价
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if len(self._userInfo) == 0 or userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return 0

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._position) == 0:
            return 0

        contNo = self._config.getBenchmark() if not contNo else contNo
        priceSum = 0.0
        posSum = 0
        for orderNo in list(tUserInfoModel._position.keys()):
            tPositionModel = tUserInfoModel._position[orderNo]
            if tPositionModel._metaData['Cont'] == contNo:
                priceSum += tPositionModel._metaData['PositionPrice'] * tPositionModel._metaData['PositionQty']
                posSum += tPositionModel._metaData['PositionQty']

        return priceSum / posSum if posSum > 0 else 0.0

    def getTotalPosition(self, userNo, contNo):
        '''
        :return: 当前公式应用的帐户下当前商品的总持仓
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        totalPos = int(self.getItemSumFromPositionModel(userNo, 'B', contNo, 'PositionQty')) - int(self.getItemSumFromPositionModel(userNo, 'S', contNo, 'PositionQty'))
        return totalPos

    def getTotalProfitLoss(self, userNo, contNo, lastPrice, contUnit):
        '''
        :param userNo: 用户交易账号
        :param contNo: 合约编号
        :param lastPrice: 该合约最新价
        :param contUnit:  该合约的每手乘数
        :return: 当前公式应用的帐户下当前商品的总持仓盈亏
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        return self.getItemSumFromPositionModel(userNo, '', contNo, 'FloatProfit', lastPrice, contUnit)

    def getTodayBuyPosition(self, userNo, contNo):
        '''
        :return: 当前公式应用的帐户下当前商品的当日买入持仓
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        todayBuyPos = self.getItemSumFromPositionModel(userNo, 'B', contNo, 'PositionQty') - self.getItemSumFromPositionModel(userNo, 'B', contNo, 'PrePositionQty')
        return int(todayBuyPos)

    def getTodaySellPosition(self, userNo, contNo):
        '''
        :return: 当前公式应用的帐户下当前商品的当日卖出持仓
        '''
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        todaySellPos = self.getItemSumFromPositionModel(userNo, 'S', contNo, 'PositionQty') - self.getItemSumFromPositionModel(userNo, 'S', contNo, 'PrePositionQty')
        return int(todaySellPos)
        
    def getDataByOrderId(self, eSession, key, ret):
        if isinstance(eSession, str) and '-' in eSession:
            orderId = self._strategy.getOrderId(eSession)
        else:
            orderId = eSession
        
        if not orderId:
            return ret
            
        realUserNo = self.getUserNoByOrderId(orderId)
        if realUserNo not in self._userInfo:
            if not realUserNo:
                self.logger.error('user(%s) not login!'%realUserNo)
            return ret

        order = self._userInfo[realUserNo].getOrderDict()
        if orderId in order:
            return order[orderId].getMetaData()[key] 
        else:
            return ret

    def getOrderBuyOrSell(self, userNo, eSession):
        '''
        返回当前公式应用的帐户下当前商品的某个委托单的买卖类型。
        :param orderNo: 委托单号
        :return: 当前公式应用的帐户下当前商品的某个委托单的买卖类型
        '''
        # userNo不使用
        return self.getDataByOrderId(eSession, 'Direct', 'N')

    def getOrderEntryOrExit(self, userNo, eSession):
        '''
        返回当前公式应用的帐户下当前商品的某个委托单的开平仓状态
        :param orderNo: 委托单号
        :return: 当前公式应用的帐户下当前商品的某个委托单的开平仓状态
        '''
        return self.getDataByOrderId(eSession, 'Offset', 'N')

    def getOrderFilledLot(self, userNo, eSession):
        '''
        返回当前公式应用的帐户下当前商品的某个委托单的成交数量
        :param orderNo: 委托单号
        :return: 当前公式应用的帐户下当前商品的某个委托单的成交数量
        '''
        return self.getDataByOrderId(eSession, 'MatchQty', 0)

    def getOrderFilledPrice(self, userNo, eSession):
        '''
        返回当前公式应用的帐户下当前商品的某个委托单的成交价格
        :param orderNo: 委托单号
        :return: 当前公式应用的帐户下当前商品的某个委托单的成交价格
        '''
        return self.getDataByOrderId(eSession, 'MatchPrice', 0.0)


    def getOrderLot(self, userNo, eSession):
        '''
        返回当前公式应用的帐户下当前商品的某个委托单的委托数量
        :param orderNo: 委托单号
        :return: 当前公式应用的帐户下当前商品的某个委托单的委托数量
        '''
        return self.getDataByOrderId(eSession, 'OrderQty', 0)

    def getOrderPrice(self, userNo, eSession):
        '''
        返回当前公式应用的帐户下当前商品的某个委托单的委托价格
        :param orderNo: 委托单号
        :return: 当前公式应用的帐户下当前商品的某个委托单的委托价格
        '''
        return self.getDataByOrderId(eSession, 'OrderPrice', 0.0)

    def getOrderStatus(self, userNo, eSession):
        '''
        返回当前公式应用的帐户下当前商品的某个委托单的状态
        :param orderNo: 委托单号
        :return: 当前公式应用的帐户下当前商品的某个委托单的状态
        '''
        return self.getDataByOrderId(eSession, 'OrderState', 'N')

    def getOrderTime(self, userNo, eSession):
        '''
        返回当前公式应用的帐户下当前商品的某个委托单的委托时间
        :param orderNo: 委托单号
        :return: 当前公式应用的帐户下当前商品的某个委托单的委托时间
        '''
        insertTime = self.getDataByOrderId(eSession, 'InsertTime', 0)
        if 0 == insertTime:
            return 0.0

        struct_time = time.strptime(insertTime, "%Y-%m-%d %H:%M:%S")
        timeStamp = time.strftime("%Y%m%d.%H%M%S", struct_time)
        return float(timeStamp)

    def getFirstOrderNo(self, userNo, contNo1, contNo2):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return -1

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._order) == 0:
            return -1

        orderId = -1
        for orderKey in list(tUserInfoModel._order.keys()):
            orderModel = tUserInfoModel._order[orderKey]
            if not contNo1 or contNo1 == orderModel._metaData['Cont']:
                if orderId == -1 or orderId > orderModel._metaData['OrderId']:
                    orderId = orderModel._metaData['OrderId']

        return orderId

    def getNextOrderNo(self, userNo, orderId, contNo1, contNo2):
        if not userNo:
            userNo = self._selectedUserNo
            
        if userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return -1

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._order) == 0:
            return -1

        minOrderId = -1
        for orderKey in list(tUserInfoModel._order.keys()):
            orderModel = tUserInfoModel._order[orderKey]
            if not contNo1 or contNo1 == orderModel._metaData['Cont']:
                if orderModel._metaData['OrderId'] <= orderId:
                    continue
                # 获取大于orderId的值
                if minOrderId == -1:
                    minOrderId = orderModel._metaData['OrderId']
                # 找到大于orderId并最接近orderId的值
                if orderModel._metaData['OrderId'] < minOrderId:
                    minOrderId = orderModel._metaData['OrderId']

        return minOrderId

    def getLastOrderNo(self, userNo, contNo1, contNo2):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if userNo not in self._userInfo:
            #raise Exception("请先在极星客户端登录您的交易账号")
            self.logger.error("请先在极星客户端登录您的交易账号")
            return -1

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._order) == 0:
            return -1

        orderId = -1
        insertSeconds = -1
        for orderKey in list(tUserInfoModel._order.keys()):
            orderModel = tUserInfoModel._order[orderKey]
            if not contNo1 or contNo1 == orderModel._metaData['Cont']:
                #timeDateStr = orderModel._metaData['InsertTime']
                #time1 = datetime.datetime.strptime(timeDateStr, "%Y-%m-%d %H:%M:%S")
                #seconds = float(time.mktime(time1.timetuple()))
                #if seconds >= insertSeconds and orderModel._metaData['OrderId'] > orderId:
                if orderModel._metaData['OrderId'] > orderId:
                    orderId = orderModel._metaData['OrderId']

        return orderId

    def getFirstQueueOrderNo(self, userNo, contNo1, contNo2):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return -1

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._order) == 0:
            return -1

        orderId = -1
        for orderKey in list(tUserInfoModel._order.keys()):
            orderModel = tUserInfoModel._order[orderKey]
            if not contNo1 or contNo1 == orderModel._metaData['Cont']:
                # 待触发,排队中,部分成交
                if orderModel._metaData['OrderState'] not in (osTriggering, osQueued, osFillPart):
                    continue
                if orderId == -1 or orderId > orderModel._metaData['OrderId']:
                    orderId = orderModel._metaData['OrderId']

        return orderId

    def getNextQueueOrderNo(self, userNo, orderId, contNo1, contNo2):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return -1
            
        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._order) == 0:
            return -1

        minOrderId = -1
        for orderKey in list(tUserInfoModel._order.keys()):
            orderModel = tUserInfoModel._order[orderKey]
            if not contNo1 or contNo1 == orderModel._metaData['Cont']:
                # 待触发,排队中,部分成交
                if orderModel._metaData['OrderState'] not in (osTriggering, osQueued, osFillPart):
                    continue
                if orderModel._metaData['OrderId'] <= orderId:
                    continue
                # 获取大于orderId的值
                if minOrderId == -1:
                    minOrderId = orderModel._metaData['OrderId']
                # 找到大于orderId并最接近orderId的值
                if orderModel._metaData['OrderId'] < minOrderId:
                    minOrderId = orderModel._metaData['OrderId']

        return minOrderId

    def getALatestFilledTime(self, userNo, contNo):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return -1

        tUserInfoModel = self._userInfo[userNo]
        latestTime = -1
        for orderId in list(tUserInfoModel._order.keys()):
            tOrderModel = tUserInfoModel._order[orderId]
            if not contNo or tOrderModel._metaData['Cont'] == contNo:
                if tOrderModel._metaData['OrderState'] == osFilled:
                    updateTime = tOrderModel._metaData['UpdateTime']
                    struct_time = time.strptime(updateTime, "%Y-%m-%d %H:%M:%S")
                    timeStamp = time.strftime("%Y%m%d.%H%M%S", struct_time)
                    if float(timeStamp) > latestTime:
                        latestTime = float(timeStamp)
        return latestTime

    def getAllOrderNo(self, userNo, contNo):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
        
        orderIdList = []        
        if userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return orderIdList

        tUserInfoModel = self._userInfo[userNo]
        if len(tUserInfoModel._order) == 0:
            return orderIdList

        for orderKey in list(tUserInfoModel._order.keys()):
            orderModel = tUserInfoModel._order[orderKey]
            if not contNo or contNo == orderModel._metaData['Cont']:
                orderId = orderModel._metaData['OrderId']
                orderIdList.append(orderId)

        return orderIdList

    def getOrderContractNo(self, userNo, eSession):
        return self.getDataByOrderId(eSession, 'Cont', '')

    def deleteOrder(self, userNo, eSession):
        '''
        针对当前公式应用的帐户、商品发送撤单指令。
        :param orderId: 所要撤委托单的定单号
        :return: 发送成功返回True, 发送失败返回False
        '''
        orderId = ''
        if isinstance(eSession, str) and '-' in eSession:
            orderId = self._strategy.getOrderId(eSession)
            if not orderId:
                return False
        else:
            orderId = eSession
            
        realUserNo = self.getUserNoByOrderId(orderId)
        if realUserNo not in self._userInfo:
            if not realUserNo:
                self.logger.error('user(%s) not login!'%realUserNo)
            return False

        return self.deleteOrderByOrderId(realUserNo, orderId)

    def deleteOrderByOrderId(self, userNo, orderId):
        # 默认usrNo为空字符串（''），此时取当前用户
        if not userNo:
            userNo = self._selectedUserNo
            
        if userNo not in self._userInfo:
            self.logger.error("请先在极星客户端登录您的交易账号")
            return -1

        userInfoModel = self._userInfo[userNo]
        if orderId not in userInfoModel._order:
            return False

        aOrder = {
            "OrderId": orderId,
        }
        aOrderEvent = Event({
            "EventCode": EV_ST2EG_ACTUAL_CANCEL_ORDER,
            "StrategyId": self._strategy.getStrategyId(),
            "Data": aOrder
        })
        self._strategy.sendEvent2Engine(aOrderEvent)
        return True

    def modifyOrder(self, userNo, eSession, contNo, orderType, validType, orderDirct, entryOrExit, hedge, orderPrice, orderQty, \
                  triggerType, triggerMode, triggerCondition, triggerPrice):
        '''
        针对当前公式应用的帐户、商品发送改单指令。
        :param eSession: 所要改委托单的定单号
        :return: 发送成功返回True, 发送失败返回False
        '''
        #if not userNo:
        #   userNo = self._selectedUserNo
        
        orderId = ''
        if isinstance(eSession, str) and '-' in eSession:
            orderId = self._strategy.getOrderId(eSession)
            if not orderId:
                return False
        else:
            orderId = eSession
            
        realUserNo = self.getUserNoByOrderId(orderId)
        
        #if userNo != realUserNo:
        #    self.logger.warn('Order modify realUser(%s) not user(%s)!'%(realUserNo, userNo))
        #    return False
        
        if realUserNo not in self._userInfo:
            if not realUserNo:
                self.logger.error('user(%s) not login!'%realUserNo)
            return False

        userInfoModel = self._userInfo[realUserNo]
        if orderId not in userInfoModel._order:
            return False

        aOrder = {
            'UserNo': realUserNo,
            'Sign': self.getSign(realUserNo),
            'Cont': contNo,
            'OrderType': orderType,
            'ValidType': validType,
            'ValidTime': '0',
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
            "OrderId": orderId,
        }
        
        aOrderEvent = Event({
            "EventCode": EV_ST2EG_ACTUAL_MODIFY_ORDER,
            "StrategyId": self._strategy.getStrategyId(),
            "Data": aOrder
        })
        self._strategy.sendEvent2Engine(aOrderEvent)
        
        return True
