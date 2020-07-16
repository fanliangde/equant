import copy
from datetime import datetime
from dateutil.parser import parse
from collections import defaultdict

from capi.com_types import *
from report.reportdetail import ReportDetail
from report.fieldConfigure import *

from engine.orderctl import LimitCtl, DirectionCtl


class CalcCenter(object):
    def __init__(self, logger, strategyModel):
        self._logger = logger
        self._stModel = strategyModel

        self._orderId = 0
        # self._curTradeDate = self._strategy["StartTime"]  # 当前交易日
        self._curTradeDate = None  # 当前交易日
        self._beginDate = None  # 回测开始日期
        self._endDate = None  # 回测结束日期

        self._continueWin = 0  # 当前连续盈利次数
        self._continueLose = 0  # 当前连续亏损次数
        self._continueEmptyPeriod = 0  # 连续空仓周期数
        self._testDays = 0  # 测试天数

        self._firstHoldPosition = 0  # 所有合约第一个有仓未平的开仓单位置
        self._firstOpenOrder = {}  # 交易合约第一个有持仓的订单
        self._latestOpenOrder = {}  # 交易合约最近一个有持仓的订单
        self._latestCoverOrder = {}  # 交易合约最近一个平仓单
        #
        self._latestBuyOpenOrder = {}   # 交易合约最近一个有买持仓的买开仓单信息
        self._latestSellOpenOrder = {}  # 交易合约最近一个有卖持仓的卖开仓单信息

        self._runSet = defaultdict(int)  # 配置
        self._costs = defaultdict()  # 费率，存放所有合约的费率
        self._profit = defaultdict(int)  # 策略收益统计信息
        self._positions = {}
        self._usersPos  = {}     # 持仓信息按账户统计

        self._orders = []  # 订单列表
        self._prices = defaultdict(dict)  # 每个合约的最新价信息
        self._fundRecords = []  # 资金记录
        self._riskInfo = defaultdict(float)

        # _tradeTimeInfo 从开仓到平仓为0记为一次交易
        self._tradeTimeInfo = {
            "TradeTimes"  : 0,    # 交易次数
            "TradeWins"   : 0,    # 盈利次数
            "TradeLoses"  : 0,    # 亏损次数
            "TradeEvents" : 0     # 持平次数
        }

        self._yearStatis = []  # 年统计
        self._quarterStatis = []  # 季度统计
        self._monthStatis = []  # 月统计
        self._weekStatis = []  # 周统计
        self._dailyStatis = []  # 日统计

        self._tradeInfo = defaultdict(int)  # 交易信息
        self._continueTradePeriod = 0  # 连续交易周期数
        self._continueWinDays = 0  # 连续盈利天数
        self._continueWinDaysStartTime = None  # 连续盈利天数开始时间
        self._continueWinDaysEndTime = None  # 连续盈利天数结束时间
        self._continueLoseDays = 0  # 连续亏损天数
        self._continueLoseDaysStartTime = None  # 连续亏损天数开始时间
        self._continueLoseDaysEndTime = None  # 连续亏损天数结束时间

        # ---------计算环比增加减小数据时使用---------------
        self._winComparedIncreaseContinueDays = 0  # 盈利环比增加天数
        self._winComparedIncreaseContinueDaysStartTime = None  # 盈利环比增加天数开始时间
        self._winComparedIncreaseContinueDaysEndTime = None  # 盈利环比增加天数结束时间
        self._loseComparedIncreaseContinueDays = 0  # 亏损环比增加天数
        self._loseComparedIncreaseContinueDaysStartTime = None  # 亏损环比增加天数开始时间
        self._loseComparedIncreaseContinueDaysEndTime = None  # 亏损环比增加天数结束时间

        self._reportDetails = {}  # 回测报告详情

        # limits
        self._limit = {}  # 下单限制

        self._contStat = {}    

    def _updateContStat(self, ord_ex):
        '''
        {
            'Profit':0.0,         # 平仓盈亏
            'TradeCost':0.0,      # 手续费
            'TotalLoss': 0.0,     # 总亏损
            'TotalProfit'         # 总利润
        }
        '''
        cont = ord_ex["Order"]["Cont"]
        if cont not in self._contStat:
            self._contStat[cont] = {'Profit':0.0, 'TradeCost':0.0, 'TotalLoss': 0.0, 'TotalProfit': 0.0}
        stat = self._contStat[cont]

        stat['Profit'] += ord_ex['LiquidateProfit'] 
        stat['TradeCost'] += ord_ex['Cost']
        stat['TotalLoss'] += 0.0   # 暂时先不计算
        stat['TotalProfit'] += ord_ex['Profit']

    def getcontStat(self, contNo):
        if contNo in  self._contStat:
            return self._contStat[contNo]
        else:
            return None    

    def initArgs(self, args):
        """初始化参数"""
        self._strategyArgs = args
        self._setProfitInitialFundInfo(int(self._strategyArgs["InitialFunds"]) - self._runSet["StartFund"])
        self._setExpertSetting()
        self._limit = copy.copy(self._strategyArgs["Limit"])

        self._initOrderCtl()

    def _initOrderCtl(self):
        self._limitCtl = LimitCtl(self._logger, self._limit["ContinueOpenTimes"], self._limit["OpenTimes"],
                                  self._limit["OpenAllowClose"], self._limit["CloseAllowOpen"])

        #TODO: 没起作用？
        self._dirCtl = DirectionCtl(self._logger, 0)

    def _updateTradeDate(self, tradedate):
        """更新当前交易日信息"""
        if self._curTradeDate is None:
            return

        self._curTradeDate = tradedate

    def _setExpertSetting(self):
        """
        交易设置
        :return: None
        """
        self._runSet = {
            "StartFund": self._strategyArgs["InitialFunds"],
            "Strategy": self._strategyArgs["StrategyName"],
            "KLineType": self._strategyArgs["KLineType"],
            "KLineSlice": self._strategyArgs["KLineSlice"],
            "StartTime": self._strategyArgs["StartTime"],
            "EndTime": self._strategyArgs["EndTime"]
        }

    def _setProfitInitialFundInfo(self, initialFund):
        """设置self._profit初始资金信息"""
        self._profit["MaxAssets"] += initialFund  # 最大资产
        self._profit["MinAssets"] += initialFund  # 最小资产
        self._profit["StartFund"] += initialFund  # 期初资产
        self._profit["LastAssets"] += initialFund  # 期末资产
        self._profit["Available"] += initialFund  # 当前可用资金
        self._profit["EmptyAssets"] += initialFund  # 空仓资产
        self._profit["EmptyPositionEquity"] += initialFund  # 期初空仓资产

        self._profit["Highest"] = initialFund
        self._profit["Lowest"] = initialFund

    def __initRetracementTm(self, time_):
        """初始化回撤时间"""
        if not self._profit["MaxRetracementStartTm"]:
            self._profit["MaxRetracementStartTm"] = time_       # 权益最大回撤开始时间
            self._profit["MaxRetracementEndTm"] = time_         # 权益最大回撤结束时间

            self._profit["MaxRetracementRateStartTm"] = time_   # 权益最大回撤比开始时间
            self._profit["MaxRetracementRateEndTm"] = time_     # 权益最大回撤比结束时间

    def _getCostRate(self, contract):
        """
        获取合约费率，找不到就返回默认值
        :param contract: string 合约
        :return: dict, 费率
        """
        if contract in self._costs:
            return self._costs[contract]
        else:
            self._costs[contract] = {
                "TradeDot"        :   self._stModel.getContractUnit(contract),
                "PriceTick"       :   self._stModel.getPriceScale(contract),
                "Margin"          :   self._stModel.getMarginRatio(contract),
                "OpenRatio"       :   self._stModel.getOpenRatio_(contract),
                "CloseRatio"      :   self._stModel.getCloseRatio_(contract),
                "OpenFixed"       :   self._stModel.getOpenFixed_(contract),
                "CloseFixed"      :   self._stModel.getCloseFixed_(contract),
                "CloseTodayRatio" :   self._stModel.getCloseTodayRatio_(contract),
                "CloseTodayFixed" :   self._stModel.getCloseTodayFixed_(contract),
                 "Slippage"       :   self._stModel.getSlippage_()
            }

            return self._costs[contract]

    def getPositionInfo(self, contract=None):
        """
        获取contract所对应的持仓
        :param contract: 合约
        :return: 持仓信息
        {
             "Cont"       :   合约编号
             "TodayBuy"   :   今持买开手数
             "TotalBuy"   :   总持买开手数
             "BuyPrice"   :   买持仓均价

             "TodaySell"  :  今持卖开手数
             "TotalSell"  :  总持卖开手数
             "SellPrice"  :  卖持仓均价

             "LongMargin" :  多头保证金
             "ShorMargin" :  空头保证金
             "HoldProfit" :  持仓盈亏（浮动盈亏）

             "Cost"       :  平掉所持仓位所需手续费
         }
        """
        positions = dict()
        for user in self._positions:
            for cont in self._positions[user]:
                if cont not in positions:
                    positions[cont] = self._positions[user][cont]
                else:
                    positions[cont]["TodayBuy"] += self._positions[user][cont]["TodayBuy"]
                    positions[cont]["TotalBuy"] += self._positions[user][cont]["TotalBuy"]
                    positions[cont]["BuyPrice"] = (positions["BuyPrice"] + self._positions[user][cont][
                        "BuyPrice"]) / 2

                    positions[cont]["TodaySell"] += self._positions[user][cont]["TodaySell"]
                    positions[cont]["TotalSell"] += self._positions[user][cont]["TotalSell"]
                    positions[cont]["SellPrice"] = (positions["SellPrice"] + self._positions[user][cont][
                        "SellPrice"]) / 2

                    positions[cont]["LongMargin"] += self._positions[user][cont]["LongMargin"]
                    positions[cont]["ShorMargin"] += self._positions[user][cont]["ShorMargin"]

                    positions[cont]["HoldProfit"] += self._positions[user][cont]["HoldProfit"]
                    positions[cont]["Cost"] += self._positions[user][cont]["Cost"]
        if not contract:
            return copy.copy(positions)
        elif contract in positions:
            return copy.copy(positions[contract])
        else:
            return {
                "Cont": contract,
                "TodayBuy": 0,
                "TotalBuy": 0,
                "BuyPrice": 0.0,

                "TodaySell": 0,
                "TotalSell": 0,
                "SellPrice": 0.0,

                "LongMargin": 0.0,
                "ShortMargin": 0.0,
                "HoldProfit": 0.0,

                "Cost": 0.0  # 平仓所需手续费
            }

    def getUsersPosition(self):
        """获取包含账户信息的持仓信息"""
        return copy.deepcopy(self._positions)

    def _getSpecificPositionInfo(self, user, contract):
        """
        获取账户下特定合约的持仓信息
        :param contract: 合约
        :param user:  账户
        :return:
        """
        defaultInfo = {
             "Cont": contract,
             "TodayBuy": 0,
             "TotalBuy": 0,
             "BuyPrice": 0.0,

             "TodaySell": 0,
             "TotalSell": 0,
             "SellPrice": 0.0,

             "LongMargin": 0.0,
             "ShortMargin": 0.0,
             "HoldProfit": 0.0,

             "Cost": 0.0  # 平仓所需手续费
        }
        if user not in self._positions:
            return defaultInfo
        else:
            if contract not in self._positions[user]:
                return defaultInfo
            else:
                return copy.deepcopy(self._positions[user][contract])

    def __calcCoverTCharge(self, cost, qty, orderPrice):
        """计算平今手续费"""
        if cost["CloseTodayRatio"]:
            coverTCharge = orderPrice * qty * cost["TradeDot"] * cost["CloseTodayRatio"]
        else:
            coverTCharge = qty * cost["CloseTodayFixed"]
        return coverTCharge

    def __calcCoverCharge(self, cost, qty, orderPrice):
        """计算平仓手续费"""
        if cost["CloseRatio"]:
            coverCharge = orderPrice * qty * cost["TradeDot"] * cost["CloseRatio"]
        else:
            coverCharge = qty * cost["CloseFixed"]

        return coverCharge

    def __calcOpenCharge(self, cost, qty, orderPrice):
        """计算开仓手续费"""
        if cost["OpenRatio"]:
            openCharge = orderPrice * qty * cost["TradeDot"] * cost["OpenRatio"]
        else:
            openCharge = qty * cost["OpenFixed"]
        return openCharge

    def __isSHFEorINE(self, cont):
        """判断是否支持平今"""
        type = cont.split("|")[0]
        if type == "SHFE" or type == "INE":
            return True
        return False

    def needCover(self, userNo, contNo, direct, orderQty, orderPrice):
        """
        开仓单信号先平对手仓再开仓，判断能否平对手仓以及能否开仓
        :param userNo:     用户账户
        :param contNo:     合约编号
        :param direct:     买卖方向
        :param orderQty:   订单数量
        :param orderPrice: 订单价格
        :return:
                -1:       平对手仓失败
                -2:       开仓失败
                0或其他:  成功
        """
        pInfo = self._getSpecificPositionInfo(userNo, contNo)
        availableFund = self.getAvailableFund()
        cost = self._getCostRate(contNo)

        ret = -1

        if orderQty <= 0:
            self._logger.error(f"[{userNo}] [{contNo}] 订单手数不大于0")
            return ret

        if direct == dBuy:  # 买开
            if pInfo["TotalSell"] > 0:
                if self.__isSHFEorINE(contNo):  # 上期所和能交所要区分平今平昨的手续费
                    #平今手续费
                    coverTCharge = self.__calcCoverTCharge(cost, pInfo["TodaySell"], orderPrice)
                    #平昨手续费
                    coverBCharge = self.__calcCoverCharge(cost, pInfo["TotalSell"] - pInfo["TodaySell"], orderPrice)

                    coverCharge = coverTCharge + coverBCharge

                else:     # 其他交易所不区分平今平昨
                    coverCharge = self.__calcCoverCharge(cost, pInfo["TotalSell"], orderPrice)

                if availableFund < coverCharge:
                    self._logger.error(f"自动平仓：[{userNo}] [{contNo}] 平卖开仓失败")
                    return -1  # 平卖开仓失败
                else:
                    # 开仓手续费
                    openCharge = self.__calcOpenCharge(cost, orderQty, orderPrice)

                    # 需要将平仓盈亏和保证金考虑进去

                    beforePrice = pInfo["SellPrice"]  # 未平之前的持仓价
                    # 平仓盈亏
                    liquidateprofit = (beforePrice * pInfo["TotalSell"] - orderPrice * pInfo["TotalSell"]) * cost[
                        "TradeDot"]
                    turnover = orderPrice * pInfo["TotalSell"] * cost["TradeDot"]
                    margin = turnover * cost["Margin"]

                    if availableFund + liquidateprofit - margin - coverCharge < openCharge:
                        self._logger.error(f"自动平仓：[{userNo}] [{contNo}] 开买开仓失败")
                        ret = -2  # 开买开仓失败
                    else:
                        ret = pInfo["TotalSell"]

        else:
            if pInfo["TotalBuy"] > 0:
                if self.__isSHFEorINE(contNo):  # 上期所和能交所要区分平今平昨的手续费
                    # 平今手续费
                    coverTCharge = self.__calcCoverTCharge(cost, pInfo["TodayBuy"], orderPrice)
                    # 平昨手续费
                    coverBCharge = self.__calcCoverCharge(cost, pInfo["TotalBuy"] - pInfo["TodayBuy"], orderPrice)

                    coverCharge = coverTCharge + coverBCharge

                else:     # 其他交易所不区分平今平昨
                    coverCharge = self.__calcOpenCharge(cost, pInfo["TotalBuy"], orderPrice)

                if availableFund < coverCharge:
                    self._logger.error(f"自动平仓：[{userNo}] [{contNo}] 平买开仓失败")
                    ret = -1  # 平买开仓失败
                else:
                    openCharge = self.__calcOpenCharge(cost, orderQty, orderPrice)

                    # 需要将平仓盈亏和保证金考虑进去

                    beforePrice = pInfo["BuyPrice"]  # 未平之前的持仓价
                    # 平仓盈亏
                    liquidateprofit = (orderPrice * pInfo["TotalBuy"] - beforePrice * pInfo["TotalBuy"]) * cost[
                        "TradeDot"]
                    turnover = orderPrice * pInfo["TotalBuy"] * cost["TradeDot"]
                    margin = turnover * cost["Margin"]

                    if availableFund + liquidateprofit - margin - coverCharge < openCharge:
                        self._logger.error(f"自动平仓：[{userNo}] [{contNo}] 开卖开仓失败")
                        ret = -2  # 开卖开仓失败
                    else:
                        ret = pInfo["TotalBuy"]

        return ret

    def coverJudge(self, order):
        """
        平仓单是否合法判断
        :param order:        订单详情
        :return:
                -1:          平仓失败， 仓位不足
                -2:          平仓失败，资金不足
                1:           允许平仓

        """
        pInfo = self._getSpecificPositionInfo(order["UserNo"], order["Cont"])

        ret = -1

        ftOrder = self._formatOrder(order)

        if order["OrderQty"] <= 0:
            self._logger.error(f"订单手数不大于0，订单数据：{ftOrder}")
            return ret

        if order["Direct"] == dBuy and order["Offset"] == oCover:  # 买平
            if pInfo["TotalSell"] > 0:
                # 判断持仓
                if pInfo["TotalSell"] < order["OrderQty"]:
                    self._logger.error(f"平卖仓失败，仓位不足，订单数据：{ftOrder}")
                else: ret = 1

            else:
                self._logger.error(f"平卖仓失败，仓位不足，订单数据：{ftOrder}")

        elif order["Direct"] == dSell and order["Offset"] == oCover:  # 卖平
            if pInfo["TotalBuy"] > 0:
                # 判断持仓
                if pInfo["TotalBuy"] < order["OrderQty"]:
                    self._logger.error(f"平买仓失败，仓位不足，订单数据：{ftOrder}")
                else: ret = 1

            else:
                self._logger.error(f"平买仓失败，仓位不足，订单数据：{ftOrder}")

        elif order["Direct"] == dBuy and order["Offset"] == oCoverT:  # 买平今
            if pInfo["TodaySell"] > 0:
                # 判断持仓
                if pInfo["TodaySell"] < order["OrderQty"]:
                    self._logger.error(f"买平今失败，仓位不足，订单数据：{ftOrder}")
                else: ret = 1

            else:
                self._logger.error(f"买平今失败，仓位不足，订单数据：{ftOrder}")

        else:  # 卖平今
            if pInfo["TodayBuy"] > 0:
                # 判断持仓
                if pInfo["TodayBuy"] < order["OrderQty"]:
                    self._logger.error(f"卖平今失败，仓位不足，订单数据：{ftOrder}")
                else: ret = 1

            else:
                self._logger.error(f"卖平今失败，仓位不足，订单数据：{ftOrder}")

        return ret

    def calcOrderPrice(self, contract, direct, orderprice):
        """
        计算订单的成交价(考虑滑点损耗)
        :param contract: 合约
        :param direct: 买卖方向
        :param orderprice: 订单委托价格
        :return: 计算滑点之后的订单成交价
        """
        if not isinstance(contract, str):
            self._logger.error("考虑滑点计算订单成交价时出错，contract类型错误!")
            raise TypeError

        if direct not in (dBuy, dSell):
            self._logger.error("考虑滑点计算订单成交价时出错，direct类型错误!")
            raise TypeError

        cost = self._getCostRate(contract)
        slippage = cost["Slippage"]
        priceTick = cost["PriceTick"]
        if direct == dBuy:
            price = orderprice + slippage * priceTick
        else:
            price = orderprice - slippage * priceTick

        return price

    def addOrder(self, order):
        """
        有订单时，触发此函数
        :param order: 订单
        order:
        {
        "UserNo":         # 用户编号
        "OrderType":      # 定单类型
        "ValidType":      # 有效类型
        "ValidTime":      # 有效日期时间(GTD情况下使用)
        "Cont":           # 合约
        "Direct":         # 买卖方向
        "Offset":         # 开仓平仓 或 应价买入开平
        "Hedge":          # 投机套保
        "OrderPrice":     # 委托价格 或 期权应价买入价格
        "OrderQty" :      # 委托数量 或 期权应价数量
        "DateTimeStamp":  # 时间戳（基准合约）
        "TradeDate":      # 交易日（基准合约）
        "TriggerType":    # 触发方式
        "CurBar":         # K线信息
        "CurBarIndex":    # K线索引
        "StrategyId":     # 策略Id
        "StrategyName":   # 策略名称
        "StrategyStage":  # 策略运行阶段
        }
        :return: 1, 0, addOrder 成功  失败标志
        """
        if not self._beginDate:
            self._beginDate = order["TradeDate"]
        self._endDate = order["TradeDate"]
        if self._curTradeDate is None:
            self._curTradeDate = order["TradeDate"]

        self.__initRetracementTm(order["DateTimeStamp"])

        # TODO:限制信息写在这里
        # TODO: 应该先判断下面的限制再判断needCover 和 coverJudge
        if len(self._orders) < 1:
            lmtRet = self._limitCtl.allowOrder(order, [])
        else:
            lmtRet = self._limitCtl.allowOrder(order, self._orders[-1]["Order"])

        # TODO：是否起作用？
        dirRet = self._dirCtl.handleDirCtl(order)
        if lmtRet == 0 or dirRet == 0:
            return 0

        order.update({"OrderId": self._orderId})
        self._orderId += 1
        self._costs[order["Cont"]] = self._getCostRate(order["Cont"])
        # self._updateTradeDate(order["TradeDate"])

        ftOrder = self._formatOrder(order)

        if order["OrderQty"] <= 0:
            self._logger.error(f"订单手数不大于0，订单数据：{ftOrder}")
            return 0

        self._logger.trade_info("[%3s] [%4s] [%5s], %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" % (
            ftOrder["StrategyId"],
            ftOrder["StrategyStage"],
            ftOrder["OrderId"],
            ftOrder["TradeDate"],
            ftOrder["DateTimeStamp"],
            ftOrder["UserNo"],
            ftOrder["Cont"],
            ftOrder["Direct"],
            ftOrder["Offset"],
            ftOrder["OrderPrice"],
            ftOrder["OrderQty"],
            ftOrder["OrderType"],
            ftOrder["Hedge"])
            )

        self._calcOrder(order)

        self._updateFirstHoldPosition()

        # 1ms-2ms
        self._calcPosition(order)

        # 4ms
        self._updateFirstOrder(order["UserNo"], order["Cont"])
        # -------------------4ms----------------------------------
        # 更新最近一笔开仓单
        self._updateLatestOpenOrder(order["UserNo"], order["Cont"])
        # 更新最近一笔平仓单
        self._updateLatestCoverOrder(order["Cont"])

        eo = self._orders[-1]
        self._calcOrderProfit(eo)  # self._calcSingleReturns（eo)是不是可以放在calcOrderProfit中呢？？？

        # TODO：该函数作用??????????????????????????????????
        self._calcSingleReturns(eo)
        # 计算交易次数(从开仓到平仓为0记为一次交易)
        self._calcTradeTimes(eo)

        self._updateOtherProfit(order["DateTimeStamp"])

        # self._calcTradeInfo()
        self._updateFundRecord(order["DateTimeStamp"], eo["Profit"], eo["Cost"], order["TradeDate"])
        self._stageStatistics()  # 计算阶段总结
        self._calcTradeInfo()    # 计算交易信息
        self._updateTradeDate(order["TradeDate"])
        # print("end:", datetime.now().strftime('%H:%M:%S.%f'))
        
        self._updateContStat(eo)

        return 1  # 订单发送成功

    def _formatOrder(self, order):
        if "OrderId" in order:
            return {
                "StrategyId"   :    order["StrategyId"],
                "StrategyStage":    StrategyStatus[order["StrategyStage"]],
                "OrderId"      :    order["OrderId"],
                "TradeDate":        order["TradeDate"],
                "DateTimeStamp":    order["DateTimeStamp"],
                "UserNo"       :    order["UserNo"],
                "Cont"         :    order["Cont"],
                "Direct"       :    DirectDict[order["Direct"]],
                "Offset"       :    OffsetDict[order["Offset"]],
                "OrderPrice"   :    '{:.7f}'.format(order["OrderPrice"]),
                "OrderQty"     :    order["OrderQty"],
                "OrderType"    :    OrderTypeDict[order["OrderType"]],
                "Hedge"        :    HedgeDict[order["Hedge"]],

            }
        return {
                "StrategyName" :    order["StrategyName"],
                "StrategyId"   :    order["StrategyId"],
                "StrategyStage":    StrategyStatus[order["StrategyStage"]],
                "TradeDate":        order["TradeDate"],
                "DateTimeStamp":    order["DateTimeStamp"],
                "UserNo"       :    order["UserNo"],
                "OrderCont"    :    order["Cont"],
                "Direct"       :    DirectDict[order["Direct"]],
                "Offset"       :    OffsetDict[order["Offset"]],
                "OrderPrice"   :    '{:.2f}'.format(order["OrderPrice"]),
                "OrderQty"     :    order["OrderQty"],
                "OrderType"    :    OrderTypeDict[order["OrderType"]],
                "Hedge"        :    HedgeDict[order["Hedge"]],
            }

    def _calcOrder(self, order):
        """"
        计算订单的扩展信息
        :return:
        """
        charge = 0  # 手续费
        charge1 = 0  # 手续费1
        margin = 0  # 保证金
        turnover = 0
        profit = 0  # 净利润
        liquidateProfit = 0  # 平仓盈亏
        slipLoss = 0  # 滑点损耗
        linkList = []  # value = {id, vol}

        pInfo = self._getSpecificPositionInfo(order["UserNo"], order["Cont"])
        eo = defaultdict(int)

        if order["Direct"] == dBuy and order["Offset"] == oOpen or \
                order["Direct"] == dSell and order["Offset"] == oOpen:  # 买开、卖开
            qty = order["OrderQty"]
            charge, turnover, margin, profit, slipLoss = self.__calcOpenInfo(order, qty)

        elif order["Direct"] == dBuy and order["Offset"] == oCover:  # 买平
            qty = order["OrderQty"] if pInfo["TotalSell"] > order["OrderQty"] else pInfo["TotalSell"]
            charge, charge1, turnover, liquidateProfit, profit, linkList, slipLoss = self.__calcCloseInfo(order, pInfo,
                                                                                                          qty, False)

        elif order["Direct"] == dSell and order["Offset"] == oCover:  # 卖平
            qty = order["OrderQty"] if pInfo["TotalBuy"] > order["OrderQty"] else pInfo["TotalBuy"]
            charge, charge1, turnover, liquidateProfit, profit, linkList, slipLoss = self.__calcCloseInfo(order, pInfo,
                                                                                                          qty, True)

        elif order["Direct"] == dBuy and order["Offset"] == oCoverT:  # 买平今
            qty = order["OrderQty"] if pInfo["TodaySell"] > order["OrderQty"] else pInfo["TodaySell"]
            charge, charge1, turnover, liquidateProfit, profit, linkList, slipLoss = self.__calcCloseTInfo(order, pInfo,
                                                                                                          qty, False)

        elif order["Direct"] == dSell and order["Offset"] == oCoverT:  # 卖平今
            qty = order["OrderQty"] if pInfo["TodayBuy"] > order["OrderQty"] else pInfo["TodayBuy"]
            charge, charge1, turnover, liquidateProfit, profit, linkList, slipLoss = self.__calcCloseTInfo(order, pInfo,
                                                                                                           qty, True)

        eo.update({
            "Order": order,
            "Cost": charge,
            "Margin": margin,
            "Turnover": turnover,
            "LiquidateProfit": liquidateProfit,
            "Profit": profit,
            "SlippageLoss": slipLoss
        })
        if (eo["Order"]["Direct"] == dBuy and eo["Order"]["Offset"] == oCover) \
                or (eo["Order"]["Direct"] == dSell and eo["Order"]["Offset"] == oCover) \
                or (eo["Order"]["Direct"] == dBuy and eo["Order"]["Offset"] == oCoverT) \
                or (eo["Order"]["Direct"] == dSell and eo["Order"]["Offset"] == oCoverT):  # 平仓单

            eo["OpenLink"] = []
            for i in range(len(linkList)):
                # eoi["Openlink"][i] = linkList[i]
                eo["OpenLink"].append(linkList[i])
                self._orders[linkList[i]["id"]]["LeftNum"] -= linkList[i]["vol"]
            eo["LinkNum"] = len(linkList)
            eo["LeftNum"] = 0
        elif (eo["Order"]["Direct"] == dBuy and eo["Order"]["Offset"] == oOpen) \
                or (eo["Order"]["Direct"] == dSell and eo["Order"]["Offset"] == oOpen):  # 开仓单:
            eo["OpenLink"] = None
            eo["LinkNum"] = 0
            eo["LeftNum"] = order["OrderQty"]
            # eoi["MaxPrice"] = order["OrderPrice"]
            # eoi["MaxTime"] = order["DateTimeStamp"]
            # eoi["MinPrice"] = order["OrderPrice"]
            # eoi["MinTime"] = order["DateTimeStamp"]

        self._orders.append(eo)

        return

    def _calcPosition(self, order):
        """ 持仓信息"""
        # 用订单的成交价作为最新价来进行相关计算
        lastPrice = order["OrderPrice"]
        cost = self._getCostRate(order["Cont"])
        pInfo = self._getSpecificPositionInfo(order["UserNo"], order["Cont"])

        # TODO: 计算持仓时默认是优先平今，后期可能会存在优先平今、优先平昨可选的情况
        if order["Direct"] == dBuy and order["Offset"] == oOpen:  # 买入开仓(买开）
            pInfo["BuyPrice"] = (pInfo["TotalBuy"] * pInfo["BuyPrice"] + order["OrderQty"]
                                 * order["OrderPrice"]) / (pInfo["TotalBuy"] + order["OrderQty"])
            pInfo["TodayBuy"] = self._calcTodayPosition(order, pInfo, False)
            pInfo["TotalBuy"] += order["OrderQty"]

        elif order["Direct"] == dBuy and order["Offset"] == oCover:  # 买入平仓（买平）
            vol = order["OrderQty"] if pInfo["TotalSell"] > order["OrderQty"] else pInfo["TotalSell"]
            pInfo["TotalSell"] -= vol
            # 今持卖
            pInfo["TodaySell"] = pInfo["TotalSell"] if pInfo["TotalSell"] < pInfo["TodaySell"] else pInfo["TodaySell"]
            pInfo["SellPrice"] = self._getHoldPrice(order["Cont"], pInfo["TotalSell"], False)  # 平仓之后剩余持仓的持仓均价

        elif order["Direct"] == dBuy and order["Offset"] == oCoverT:  # 买平今
            vol = order["OrderQty"] if pInfo["TodaySell"] > order["OrderQty"] else pInfo["TodaySell"]
            pInfo["TotalSell"] -= vol
            pInfo["TodaySell"] -= vol
            pInfo["SellPrice"] = self._getHoldPrice(order["Cont"], pInfo["TotalSell"] - vol, False)

        elif order["Direct"] == dSell and order["Offset"] == oOpen:  # 卖出开仓
            pInfo["SellPrice"] = (pInfo["TotalSell"] * pInfo["SellPrice"] + order["OrderQty"]
                                  * order["OrderPrice"]) / (pInfo["TotalSell"] + order["OrderQty"])
            pInfo["TotalSell"] += order["OrderQty"]
            pInfo["TodaySell"] = self._calcTodayPosition(order, pInfo, True)

        elif order["Direct"] == dSell and order["Offset"] == oCover:  # 卖出平仓
            vol = order["OrderQty"] if pInfo["TotalBuy"] > order["OrderQty"] else pInfo["TotalBuy"]
            pInfo["TotalBuy"] -= vol
            pInfo["TodayBuy"] = pInfo["TotalBuy"] if pInfo["TotalBuy"] < pInfo["TodayBuy"] else pInfo["TodayBuy"]
            pInfo["BuyPrice"] = self._getHoldPrice(order["Cont"], pInfo["TotalBuy"], True)  # 持仓均价

        elif order["Direct"] == dSell and order["Offset"] == oCoverT:  # 卖平今
            vol = order["OrderQty"] if pInfo["TodayBuy"] > order["OrderQty"] else pInfo["TodayBuy"]
            pInfo["TotalBuy"] -= vol
            pInfo["TodayBuy"] -= vol
            pInfo["BuyPrice"] = self._getHoldPrice(order["Cont"], pInfo["TotalBuy"] - vol, True)

        #self._logger.debug("Margin1:%.2f, %d, %d, %d, %.2f" %(lastPrice, pInfo["TotalBuy"], pInfo["TotalSell"], cost["TradeDot"], cost["Margin"]))
        pInfo["LongMargin"] = lastPrice * pInfo["TotalBuy"] * cost["TradeDot"] * cost["Margin"]
        pInfo["ShortMargin"] = lastPrice * pInfo["TotalSell"] * cost["TradeDot"] * cost["Margin"]
        # 持仓盈亏（浮动盈亏）
        pInfo["HoldProfit"] = ((lastPrice - pInfo["BuyPrice"]) * pInfo["TotalBuy"]
                               + (pInfo["SellPrice"] - lastPrice) * pInfo["TotalSell"]) * cost["TradeDot"]

        charge = 0

        # 多头平仓手续费
        pInfo["Cost"] = 0  # 将上次记录的手续费清零
        if self.__isSHFEorINE(order["Cont"]):
            bCharge = self.__calcCoverCharge(cost, pInfo["TotalBuy"] - pInfo["TodayBuy"], lastPrice)
            tCharge = self.__calcCoverTCharge(cost, pInfo["TodayBuy"], lastPrice)
            charge = bCharge + tCharge
        else:
            charge = self.__calcCoverCharge(cost, pInfo["TotalBuy"], lastPrice)

        pInfo["Cost"] += charge

        # 空头平仓手续费
        if self.__isSHFEorINE(order["Cont"]):
            bCharge = self.__calcCoverCharge(cost, pInfo["TotalSell"] - pInfo["TodaySell"], lastPrice)  # 平昨手续费
            tCharge = self.__calcCoverTCharge(cost, pInfo["TodaySell"], lastPrice)  # 平今手续费
            charge = bCharge + tCharge
        else:
            charge = self.__calcCoverCharge(cost, pInfo["TotalSell"], lastPrice)

        pInfo["Cost"] += charge

        if order["UserNo"] not in self._positions:
            self._positions.update(
                {
                    order["UserNo"]: {
                        order["Cont"]: pInfo
                    }
                }
            )
        else:
            self._positions[order["UserNo"]][order["Cont"]] = pInfo

        return

    def _updateFirstOrder(self, user, contract):
        pInfo = self._getSpecificPositionInfo(user, contract)
        if pInfo["TotalBuy"] > 0 or pInfo["TotalSell"] > 0:
            for eo in self._orders[self._firstHoldPosition:]:
                if eo["Order"]["Cont"] == contract and eo["LeftNum"] > 0:
                    self._firstOpenOrder[contract] = eo["Order"]
                    return
        else:
            self._firstOpenOrder[contract] = {}
            return

    def getFirstOpenOrder(self, contract):
        """
        获取第一个有仓未平的开仓单
        :param contract: 合约代码
        :return: 开仓单的订单详情
        """
        if contract in self._firstOpenOrder:
            return self._firstOpenOrder[contract]
        return {}

    def _updateLatestOpenOrder(self, user, contract):
        """
        更新最近一笔开仓单，以及最近一笔买方向开仓单和卖方向开仓单
        {
          "Order": 订单详情,
          "LastEntryHPrice": 行情最高价,
          "LastEntryLPrice": 行情最低价
        """
        pInfo = self._getSpecificPositionInfo(user, contract)
        order = self._orders[-1]["Order"]

        if order["Offset"] == oOpen:
            self._latestOpenOrder[order["Cont"]] = order
            if order["Direct"] == dBuy:
                self._latestBuyOpenOrder[order["Cont"]] = {
                    "Order": order,
                    "LastEntryHPrice": order["OrderPrice"],
                    "LastEntryLPrice": order["OrderPrice"]
                }
                # 更新卖开仓的持仓价
                self._updateSellOpenOrderPrice(order["OrderPrice"], order["OrderPrice"], order["Cont"])

            elif order["Direct"] == dSell:
                self._latestSellOpenOrder[order["Cont"]] = {
                    "Order": order,
                    "LastEntryHPrice": order["OrderPrice"],
                    "LastEntryLPrice": order["OrderPrice"]
                }
                # 更新买开仓的持仓价
                self._updateBuyOpenOrderPrice(order["OrderPrice"], order["OrderPrice"],  order["Cont"])
        #TODO: 没有考虑外盘
        elif order["Offset"] == oCover or order["Offset"] == oCoverT:
            if pInfo["TotalBuy"] == 0 and pInfo["TotalSell"] == 0:
                self._latestOpenOrder[order["Cont"]] = {}
            if pInfo["TotalBuy"] == 0:
                self._latestBuyOpenOrder[order["Cont"]] = {
                    "Order": {},
                    "LastEntryHPrice": 0,
                    "LastEntryLPrice": 0
                }
            else:
                self._updateBuyOpenOrderPrice(order["OrderPrice"], order["OrderPrice"],  order["Cont"])
            if pInfo["TotalSell"] == 0:
                self._latestSellOpenOrder[order["Cont"]] = {
                    "Order": {},
                    "LastEntryHPrice": 0,
                    "LastEntryLPrice": 0
                }
            else:
                self._updateSellOpenOrderPrice(order["OrderPrice"], order["OrderPrice"],  order["Cont"])


    def _updateBuyOpenOrderPrice(self, price1, price2, contract):
        """
        更新买开仓单的最高价最低价
        :param price1:  最高价
        :param price2:  最低价
        :param contract: 合约
        :return:
        """
        if contract in self._latestBuyOpenOrder:
            if self._latestBuyOpenOrder[contract]["Order"]:
                if price1 > self._latestBuyOpenOrder[contract]["LastEntryHPrice"]:
                    self._latestBuyOpenOrder[contract]["LastEntryHPrice"] = price1
                if price2 < self._latestBuyOpenOrder[contract]["LastEntryLPrice"]:
                    self._latestBuyOpenOrder[contract]["LastEntryLPrice"] = price2

    def _updateSellOpenOrderPrice(self, price1, price2, contract):
        """
        更新卖开仓单的最高价最低价
        :param price1: 最高价
        :param price2: 最低价
        :param contract: 合约
        :return:
        """
        if contract in self._latestSellOpenOrder:
            if self._latestSellOpenOrder[contract]["Order"]:
                if price1 > self._latestSellOpenOrder[contract]["LastEntryHPrice"]:
                    self._latestSellOpenOrder[contract]["LastEntryHPrice"] = price1
                if price2 < self._latestSellOpenOrder[contract]["LastEntryLPrice"]:
                    self._latestSellOpenOrder[contract]["LastEntryLPrice"] = price2

    def getLatestOpenOrder(self, contract):
        """
        获取最近一个有仓未平的开仓单
        :param contract: 合约代码
        :return: 开仓单的订单详情
        """
        if contract in self._latestOpenOrder:
            return self._latestOpenOrder[contract]
        return {}

    def getLatestBuyOpenOrder(self, contract):
        if contract in self._latestBuyOpenOrder:
            return self._latestBuyOpenOrder[contract]
        return {
            "Order": {},
            "LastEntryHPrice": 0,
            "LastEntryLPrice": 0
        }

    def getLatestSellOpenOrder(self, contract):
        if contract in self._latestSellOpenOrder:
            return self._latestSellOpenOrder[contract]
        return {
            "Order": {},
            "LastEntryHPrice": 0,
            "LastEntryLPrice": 0
        }

    def _updateLatestCoverOrder(self, contract):
        """更新最近一笔平仓单"""
        tempOrder = {}

        for eo in self._orders[::-1]:
            if eo["Order"]["Cont"] == contract:
                if eo["Order"]["Direct"] == dBuy and eo["Order"]["Offset"] == oCover \
                        or eo["Order"]["Direct"] == dSell and eo["Order"]["Offset"] == oCover \
                        or eo["Order"]["Direct"] == dBuy and eo["Order"]["Offset"] == oCoverT \
                        or eo["Order"]["Direct"] == dSell and eo["Order"]["Offset"] == oCoverT:
                    self._latestCoverOrder[contract] = eo["Order"]
                    return

    def getLatestCoverOrder(self, contract):
        """
        获取最近一个平仓单
        :param contract: 合约代码
        :return: 开仓单的订单详情
        """
        if contract in self._latestCoverOrder:
            return self._latestCoverOrder[contract]
        return {}

    def _getOpenCharge(self, contract, num, offset, flag, linkList):
        """

        :param contract:合约
        :param num: 平仓量
        :param offset:合约总的剩余持仓量（卖开或买开）
        :param flag:标志订单类型（减小循环次数，提高效率）
        :param linkList:储存开平仓配对信息
        :return:
        """
        charge = 0
        leftOrderQty = num
        index = len(self._orders)

        for eo in self._orders[::-1]:  # 反向遍历
            index -= 1
            if leftOrderQty > 0 and contract == eo["Order"]["Cont"] \
                    and (eo["Order"]["Direct"] == dBuy and eo["Order"]["Offset"] == oOpen and flag) \
                    or (eo["Order"]["Direct"] == dSell and eo["Order"]["Offset"] == oOpen and not flag):
                # 找到contract合约对应的开仓单(卖开或买开）
                if offset < eo["LeftNum"] and eo["LeftNum"] > 0:
                    validNum = eo["LeftNum"] - offset if offset > 0 else eo["LeftNum"]  # 表示temp订单中平了多少手
                    realNum = validNum if leftOrderQty >= validNum else leftOrderQty
                    singleCharge = eo["Cost"] / eo["LeftNum"]
                    charge += singleCharge * realNum
                    leftOrderQty -= realNum
                    linkOrder = {"id": index, "vol": realNum}
                    linkList.append(linkOrder)
                    if leftOrderQty <= 0:
                        break
                offset -= eo["LeftNum"]
        return charge

    def _getHoldPrice(self, contract, holdNum, flag):
        """
        计算持仓均价
        :param contract:
        :param hold_num: 持仓量
        :param flag: 标志位， True为卖平， False为买平
        :return: 卖方向持仓均价
        """
        positions = self.getPositionInfo()
        if contract in positions:
            pInfo = positions[contract]
        else:
            return 0

        totalPrice = 0
        num = holdNum

        if flag and pInfo["TotalBuy"] > 0:  # 有买持仓
            for eo in self._orders[::-1]:  # 后序遍历
                if contract == eo["Order"]["Cont"] and (
                        (eo["Order"]["Direct"] == dBuy and eo["Order"]["Offset"] == oOpen)):  # contract合约对应的买开订单
                    vol = eo["LeftNum"] if num > eo["LeftNum"] else num
                    totalPrice += vol * eo["Order"]["OrderPrice"]
                    num -= vol
                    if num <= 0:
                        break
            if holdNum > 0:
                return totalPrice / holdNum
            else:
                # return pInfo["BuyPrice"]
                return 0

        elif not flag and pInfo["TotalSell"] > 0:  # 有卖持仓
            for eo in self._orders[::-1]:
                if num > 0 and contract == eo["Order"]["Cont"] and (
                        eo["Order"]["Direct"] == dSell and eo["Order"]["Offset"] == oOpen):  # contract合约对应的卖开订单
                    vol = eo["LeftNum"] if num > eo["LeftNum"] else num
                    totalPrice += vol * eo["Order"]["OrderPrice"]
                    num -= vol
            if holdNum > 0:
                return totalPrice / holdNum
            else:
                # return pInfo["SellPrice"]
                return 0

        return 0

    def _getHoldProfit(self, contract=None):
        """
        获取某个合约或全部合约的持仓盈亏
        :param contract: 合约
        :return: 持仓盈亏
        """
        positions = self.getPositionInfo()
        #print("HoldProfit1:%s" %str(positions))
        if not contract:
            profit = 0
            for pInfo in positions.values():
                profit += pInfo["HoldProfit"]
            return profit
        else:
            if contract in positions:
                return positions[contract]["HoldProfit"]
            else:
                return 0

    # 没用
    def _getCurrentPrice(self, contract):
        if contract in self._prices:
            return self._prices[contract]
        else:
            # TODO: "CurrentBarIndex"为0不对
            return {"Cont": contract,
                    "Price": 0,
                    "Time": 0,
                    "CurrentBarIndex": 0}

    def _getHoldMargin(self, contract=None):
        """
        获取某个合约或全部合约的持仓保证金
        :param contract: 合约
        :return: 持仓保证金
        """
        positions = self.getPositionInfo()
        if not contract:  # 全部合约
            margin = 0
            for pInfo in positions.values():
                margin += pInfo["LongMargin"]
                margin += pInfo["ShortMargin"]
            return margin
        else:  # 某个合约
            if contract in positions:
                return positions[contract]["LongMargin"] + positions[contract]["ShortMargin"]
            else:
                return 0

    def _updateFirstHoldPosition(self):
        """
        根据当前持仓位置计算下一个持仓位置
        :return:
        """
        while self._firstHoldPosition < len(self._orders):
            if self._orders[self._firstHoldPosition]["LeftNum"] > 0:
                break
            self._firstHoldPosition += 1

    def _calcOrderProfit(self, extendOrder):
        """

        :param extendOrder: 扩展订单信息
        :return:
        """
        pInfo = self._getSpecificPositionInfo(extendOrder["Order"]["UserNo"], extendOrder["Order"]["Cont"])
        if (extendOrder["Order"]["Direct"] == dBuy and extendOrder["Order"]["Offset"] == oOpen) \
                or (extendOrder["Order"]["Direct"] == dSell and extendOrder["Order"]["Offset"] == oOpen):
            # self._profit["AllTrade"] += extendOrder["Order"]["OrderQty"]  # 开仓手数
            # TODO: AllTimes不正确
            self._profit["AllTimes"] += 1  # 开仓次数
            self._profit["TotalLose"] += - extendOrder["Profit"]  # 总亏损
            self._profit["TotalProfit"] += extendOrder["Profit"]  # 累计盈利
        if (extendOrder["Order"]["Direct"] == dBuy and extendOrder["Order"]["Offset"] == oCover) \
                or (extendOrder["Order"]["Direct"] == dSell and extendOrder["Order"]["Offset"] == oCover) \
                or (extendOrder["Order"]["Direct"] == dBuy and extendOrder["Order"]["Offset"] == oCoverT) \
                or (extendOrder["Order"]["Direct"] == dSell and extendOrder["Order"]["Offset"] == oCoverT):
            if extendOrder["Profit"] > 0:  # 盈利，纯利润盈利了
                self._continueWin += 1
                self._continueLose = 0
                self._profit["TotalWin"] += extendOrder["Profit"]    # 总盈利
                if extendOrder["Profit"] > self._profit["MaxTradeWin"]:
                    self._profit["MaxTradeWin"] = extendOrder["Profit"]
                # self._profit["WinTrade"] += extendOrder["Order"]["OrderQty"]
                self._profit["WinTimes"] += 1
                if self._continueWin > self._profit["ContinueTradeWin"]:
                    self._profit["ContinueTradeWin"] = self._continueWin
            elif extendOrder["Profit"] < 0:  # 亏损
                self._continueWin = 0
                self._continueLose += 1
                self._profit["TotalLose"] += -extendOrder["Profit"]
                if -extendOrder["Profit"] > self._profit["MaxTradeLose"]:
                    self._profit["MaxTradeLose"] = extendOrder["Profit"]
                # self._profit["LoseTrade"] += extendOrder["Order"]["OrderQty"]
                self._profit["LoseTimes"] += 1
                if self._continueLose > self._profit["ContinueTradeLose"]:
                    self._profit["ContinueTradeLose"] = self._continueLose
            else:  # 持平
                # self._profit["EventTrade"] += extendOrder["Order"]["OrderQty"]
                self._profit["EventTimes"] += 1

            self._profit["TotalProfit"] = self._profit["TotalWin"] - self._profit["TotalLose"]  # 累计盈亏
            self._profit["TradeTimes"] += 1  # 交易次数，有一次下单就记录一次交易

            # 胜率WinRate定义为：非亏损交易次数 / 总交易次数，其中一次平仓操作记一次交易
            self._profit["WinRate"] = (self._profit['TradeTimes'] - self._profit['LoseTimes']) / self._profit['TradeTimes']

        self._profit["LiquidateProfit"] += extendOrder["LiquidateProfit"]  # 累计平仓盈亏
        self._profit["Turnover"] += extendOrder["Turnover"]   # 累计成交额
        self._profit["Cost"] += extendOrder["Cost"]    # 累计手续费
        self._profit["SlippageLoss"] += extendOrder["SlippageLoss"]  # 总滑点损耗

    def _updateOtherProfit(self, time):
        """
        更新行情相关的实时收益字段
        :param time:
        :return:
        """
        #记录上一个LastAssets
        preAssets = self._profit["LastAssets"]
        self._profit["Margin"] = self._getHoldMargin()
        self._profit["HoldProfit"] = self._getHoldProfit()
        #####################################################################
        # 一般期货公司都设置Available不包含浮动盈亏
        #####################################################################
        # TotalProfit表示的是累计盈亏
        # 可用资金 = 期初资金 + 总盈亏 + 浮动盈亏 - 保证金（不采用）
        # self._profit["Available"] = self._profit["StartFund"] + self._profit["TotalProfit"] + self._profit[
        #     "HoldProfit"] - self._profit["Margin"]

        # 可用资金 = 期初资金 + 总盈亏 - 保证金
        self._profit["Available"] = self._profit["StartFund"] + self._profit["TotalProfit"] - self._profit["Margin"]
        # 期末资产 = 期初资金 + 总盈亏 + 浮动盈亏
        self._profit["LastAssets"] = self._profit["StartFund"] + self._profit["TotalProfit"] + self._profit[
            "HoldProfit"]

        # 收益率 = 累计盈亏 / 期初资金
        if self._runSet["StartFund"] != 0:
            self._profit["YieldRate"] = self._profit['TotalProfit'] / int(self._runSet['StartFund'])
        else:
            self._profit["YieldRate"] = 0

        # 盈利率Returns = 净利润 / 期初资金，其中净利润 = 累计盈亏
        self._profit["Returns"] = self._profit["YieldRate"]

        # 年化单利收益率
        try:
            # 年化单利收益率 = 盈利率 * 365 / (交易天数 / 365)
            self._profit["AnnualizedSimple"] = self._profit["Returns"] * 365 / self._calcTestDay(self._beginDate,
                                                                                                 self._endDate)
        except ZeroDivisionError as e:
            testDay = self._calcTestDay(self._beginDate, self._endDate)
            self._logger.error(f"计算年化收益时出错，数据详情: {self._beginDate}, {self._endDate}, {testDay}")

        totalCost = 0
        positions = self.getPositionInfo()
        for pInfo in positions.values():
            totalCost += pInfo["Cost"]

        # 空仓资产 = 期末资产 - 清仓手续费
        self._profit["EmptyAssets"] = self._profit["LastAsset"] - totalCost
        temp = self._profit["LastAssets"]

        if temp >= self._profit["StartFund"]:
            if temp > self._profit["MaxAssets"]:
                self._profit["MaxAssets"] = temp     # 期间最大资产
                self._profit["MaxAssetsTm"] = time   # 最大资产出现时间
        else:
            if temp < self._profit["MinAssets"]:
                self._profit["MinAssets"] = temp     # 期间最小资产
                self._profit["MinAssetsTm"] = time   # 最小资产出现时间
                # 风险率Risky: 本金最大回调/本金
                self._profit["Risky"] = 1 - self._profit["MinAssets"] / self._profit["StartFund"] if self._profit[
                                                                                "StartFund"] != 0 else 0  # 风险率

        if preAssets < self._profit["LastAssets"]:
            if self._profit["LastAssets"] > self._profit["Highest"]:
                self._profit["Highest"] = self._profit["LastAssets"]
                self._profit["MaxRetracementStartTm"] = time
                # self._profit["MaxRetracementRateStartTm"] = time
        elif preAssets > self._profit["LastAssets"]:
            self._profit["Lowest"] = self._profit["LastAssets"]
            if self._profit["Highest"] - self._profit["Lowest"] > self._profit["MaxRetracement"]:
                self._profit["MaxRetracement"] = self._profit["Highest"] - self._profit["Lowest"]
                self._profit["MaxRetracementEndTm"] = time
                # 权益最大回撤比 = 最大回撤和最大回撤时的权益的比值
                retracementRate = 0
                # TODO: 权益为负值或者为0时怎么处理呢？
                if self._profit["LastAssets"] != 0:
                    retracementRate = self._profit["MaxRetracement"] / self._profit["LastAssets"]

                if retracementRate > self._profit["MaxRetracementRate"]:
                    self._profit["MaxRetracementRate"] = retracementRate
                    self._profit["MaxRetracementRateStartTm"] = self._profit["MaxRetracementStartTm"]
                    self._profit["MaxRetracementRateEndTm"] = time

    def calcProfit(self, contractList, barInfo):
        """
        该函数在每次行情变化时调用，行情变动时更新信息
        计算策略实时收益信息，参数为合约的最新价信息
        :param contractList: 合约代码列表
        :param barInfo: 合约的bar信息，类型为字典类型，键值是合约代码
        :return:
        """
        if not contractList or not barInfo:
            self._logger.error("calcProfit(): contractList error")
            raise ImportError("args error")

        if len(contractList) != len(barInfo):
            self._logger.error("calcProfit(): length error")
            raise ImportError("args error")

        # 计算空仓周期
        #TODO：计算空仓周期放在这里calcProfit中计算不正确
        #self._calcEmptyPositionPeriod()

        contPrices = {}

        benchmarkNo = contractList[0]

        if not self._beginDate:
            self._beginDate = barInfo[benchmarkNo]["TradeDate"]
        self._endDate = barInfo[benchmarkNo]["TradeDate"]

        tradedate = barInfo[benchmarkNo]["TradeDate"]
        timeStamp = barInfo[benchmarkNo]["DateTimeStamp"]

        self.__initRetracementTm(timeStamp)

        if self._curTradeDate is None:
            self._curTradeDate = tradedate

        for contract in contractList:

            contPrice = {
                "Cont": contract,
                "Price": barInfo[contract]['LastPrice'],  # 收盘价格
                "Time": barInfo[contract]["DateTimeStamp"],  # 当前时间戳
                # "CurrentBarIndex": barInfo[contract]["KLineIndex"],  # 基准合约的bar索引
                "TradeDate": barInfo[contract]["TradeDate"],
            }
            contPrices[contract] = contPrice

            if not contPrice["Price"] == 0:
                self._prices[contract] = contPrice

        self._updatePosition(contPrices)
        self._updateOtherProfit(timeStamp)

        # 更新最近一笔有仓未平的开仓单的最高价、最低价
        for c in contractList:
            self._updateBuyOpenOrderPrice(barInfo[c]["HighPrice"], barInfo[c]["LowPrice"], c)
            self._updateSellOpenOrderPrice(barInfo[c]["HighPrice"], barInfo[c]["LowPrice"], c)

        self._updateFundRecord(timeStamp, 0, 0, tradedate)
        self._stageStatistics()  # 计算阶段总结
        self._calcTradeInfo()    # 计算交易信息
        self._updateTradeDate(tradedate)
        # ----------1ms或小于1ms-----------------------
        return

    # #######################
    # 这个函数是不是有问题
    # ######################
    def _updatePosition(self, contPrices):
        for user in self._positions:
            for contract in self._positions[user]:
                if contPrices.get(contract):
                    pInfo = self._positions[user][contract]
                    lastPrice = contPrices.get(contract)["Price"]

                    pInfo = self._updateTodayPosition(pInfo)

                    cost = self._getCostRate(contract)
                    pInfo["LongMargin"] = lastPrice * cost["TradeDot"] * pInfo["TotalBuy"] * cost["Margin"]
                    pInfo["ShortMargin"] = lastPrice * cost["TradeDot"] * pInfo["TotalSell"] * cost["Margin"]
                    pInfo["HoldProfit"] = ((lastPrice - pInfo["BuyPrice"])
                                           * pInfo["TotalBuy"] + (pInfo["SellPrice"] - lastPrice)
                                           * pInfo["TotalSell"]) * cost["TradeDot"]

                    charge = 0
                    pInfo["Cost"] = 0

                    if self.__isSHFEorINE(contract):
                        bCharge = self.__calcCoverCharge(cost, pInfo["TotalBuy"] - pInfo["TodayBuy"], lastPrice)
                        tCharge = self.__calcCoverTCharge(cost, pInfo["TodayBuy"], lastPrice)
                        charge = bCharge + tCharge
                    else:
                        charge = self.__calcCoverCharge(cost, pInfo["TotalBuy"], lastPrice)

                    pInfo["Cost"] += charge

                    # 空头平仓手续费
                    if self.__isSHFEorINE(contract):
                        bCharge = self.__calcCoverCharge(cost, pInfo["TotalSell"] - pInfo["TodaySell"],
                                                         lastPrice)  # 平昨手续费
                        tCharge = self.__calcCoverTCharge(cost, pInfo["TodaySell"], lastPrice)  # 平今手续费
                        charge = bCharge + tCharge
                    else:
                        charge = self.__calcCoverCharge(cost, pInfo["TotalSell"], lastPrice)

                    pInfo["Cost"] += charge

                    self._positions[user][contract] = pInfo

    def _updateFundRecord(self, time, profit, cost, tradeDate):
        """
        更新资金记录数据
        :param time:
        :param profit:
        :param cost:
        :return:
        """
        beFound = False  # 判断是否和上一条记录重复标志，如果时间重复，则覆盖
        lastFundRecord = defaultdict(int)
        fundRecord = defaultdict(int)
        longMargin = 0
        shortMargin = 0
        totalCost = 0  # 平仓的手续费合计
        lastFundRecord["StaticEquity"] = self._profit["StartFund"]
        if len(self._fundRecords) > 0:
            lastFundRecord = self._fundRecords[-1]
            if lastFundRecord["Time"] == time:
                beFound = True

        positions = self.getPositionInfo()
        for pInfo in positions.values():
            longMargin += pInfo["LongMargin"]
            shortMargin += pInfo["ShortMargin"]
            totalCost += pInfo["Cost"]

        if beFound:
            fundRecord = copy.copy(lastFundRecord)
            fundRecord["TradeCost"] = lastFundRecord["TradeCost"] + cost
        else:
            fundRecord["id"] = len(self._fundRecords)
            fundRecord["Time"] = time
            fundRecord["TradeDate"] = tradeDate  # 交易日
            fundRecord["TradeCost"] = cost  # 当前bar进行的交易产生的手续费

        fundRecord.update({
            "LongMargin": longMargin,
            "ShortMargin": shortMargin,
            "Available": self._profit["Available"],
            "StaticEquity": lastFundRecord["StaticEquity"] + profit,
            "DynamicEquity": self._profit["LastAssets"],
            "YieldRate": self._profit["YieldRate"],
        })

        if beFound:
            self._fundRecords[-1] = copy.copy(fundRecord)
        else:
            if self._fundRecords:  # 判断是否为空
                if self._fundRecords[-1]["Time"] > fundRecord["Time"]:
                    fundRecord["TradeCost"] += self._fundRecords[-1]["TradeCost"]
                    self._fundRecords[-1] = copy.copy(fundRecord)
                else:
                    self._fundRecords.append(fundRecord)
            else:
                self._fundRecords.append(fundRecord)

    def getFundRecord(self):
        """
        获取可用资金记录
        每条记录内容注释：
        {
          "id": 编号
          "Time": 时间
          "TradeDate": 交易日
          "TradeCost": 当前bar进行的交易产生的手续费
          "LongMargin": 多头保证金,
          "ShortMargin": 空头保证金,
          "Available": 可用资金,
          "StaticEquity": 静态权益,
          "DynamicEquity": 动态权益,
          "YieldRate": 收益率,
        }
        :return:
        """
        if self._fundRecords:
            return self._fundRecords
        else:
            return []

    def getProfit(self):
        return self._profit

    def __calcTurnover(self, price, qty, tradedot):
        """计算成交额"""
        return price * qty * tradedot  # 价格 * 手数 * 每手乘数

    def __calcMargin(self, turnover, marginratio):
        """计算保证金"""
        return turnover * marginratio  # 成交额 * 保证金率

    def __calcSlippage(self, qty, slippageratio, pricetick, tradedot):
        """计算滑点损耗"""
        return qty * slippageratio * pricetick * tradedot   # 手数 * 滑点 * 最小变动价位 * 每手乘数

    # def __calcLiquidateProfit(self, cont, pInfo, price, qty, tradedot, flag):
    def __calcLiquidateProfit(self, cont, beforeavgprice, beforeqty, price, qty, tradedot, flag):
        """
        # 计算平仓盈亏
        :param
        :param cont: 合约
        :param pInfo: 仓位信息
        :param price: 订单价格
        :param qty: 订单数量
        :param tradedot: 每手乘数
        :param flag:  标志位， True为卖平， False为买平
        :return:
        """
        beforePrice = beforeavgprice  # 未平之前的持仓价
        afterPrice = self._getHoldPrice(cont, beforeqty - qty, flag)  # 平过之后的持仓价
        # 平仓盈亏
        if flag:
            liquidateProfit = (price * qty - (beforePrice * beforeqty - afterPrice * (beforeqty - qty))) * tradedot
        else:
            liquidateProfit = ((beforePrice * beforeqty - afterPrice * (beforeqty - qty)) - price * qty) * tradedot

        return liquidateProfit

    def __calcOpenInfo(self, order, qty):
        """
        计算开仓相关信息（包括买开、卖开）
        :param order: 订单
        :param qty:  手数
        :return:
            charge: 开仓手续费
            turnover: 成交额
            margin: 保证金
            profit: 订单利润
            slipLoss: 滑点损耗
        """
        cost = self._getCostRate(order["Cont"])

        charge = self.__calcOpenCharge(cost, qty, order["OrderPrice"])

        turnover = self.__calcTurnover(order["OrderPrice"], qty, cost["TradeDot"])  # 成交额
        margin = self.__calcMargin(turnover, cost["Margin"])   # 保证金
        profit = -charge  # 净利润需要扣除手续费
        slipLoss = self.__calcSlippage(qty, cost["Slippage"], cost["PriceTick"], cost["TradeDot"]) # 滑点损耗

        return charge, turnover, margin, profit, slipLoss

    def __calcCloseInfo(self, order, pInfo, qty, flag):
        """
        计算平仓相关信息（包括买平、卖平）
        :param order: 订单详情
        :param pInfo:
        :param qty:
        :param flag 标志位， True为卖平， False为买平
        :return:
            charge: 平仓手续费
            charge1,
            turnover: 成交额
            liquidateprofit: 平仓盈亏
            profit: 订单利润
            linkList
            slipLoss: 滑点损耗
        """
        cost = self._getCostRate(order["Cont"])
        linkList = []
        # 手续费
        charge = self.__calcCoverCharge(cost, qty, order["OrderPrice"])

        turnover = self.__calcTurnover(order["OrderPrice"], qty, cost["TradeDot"])  # 成交额
        if flag:
            charge1 = self._getOpenCharge(order["Cont"], qty, (pInfo["TotalBuy"] - qty), flag, linkList)
            liquidateprofit = self.__calcLiquidateProfit(order["Cont"], pInfo["BuyPrice"], pInfo["TotalBuy"],
                                                         order["OrderPrice"], qty,
                                                         cost["TradeDot"],
                                                         flag)

        else:
            charge1 = self._getOpenCharge(order["Cont"], qty, (pInfo["TotalSell"] - qty), flag, linkList)
            liquidateprofit = self.__calcLiquidateProfit(order["Cont"], pInfo["SellPrice"], pInfo["TotalSell"],
                                                         order["OrderPrice"], qty,
                                                         cost["TradeDot"],
                                                         flag)

        profit = liquidateprofit - charge
        slipLoss = self.__calcSlippage(qty, cost["Slippage"], cost["PriceTick"], cost["TradeDot"])  # 滑点损耗

        return charge, charge1, turnover, liquidateprofit, profit, linkList, slipLoss

    def __calcCloseTInfo(self, order, pInfo, qty, flag):
        """
        计算平今仓相关信息（包括买平今、卖平今）
        :param pInfo:
        :param qty:
        :param flag 标志位， True为卖平今， False为买平今
        :return:
            charge: 平仓手续费
            charge1,
            turnover: 成交额
            liquidateprofit: 平仓盈亏
            profit: 订单利润
            linkList
            slipLoss: 滑点损耗
        """
        cost = self._getCostRate(order["Cont"])
        linkList = []
        # 手续费
        charge = self.__calcCoverTCharge(cost, qty, order["OrderPrice"])

        turnover = self.__calcTurnover(order["OrderPrice"], qty, cost["TradeDot"])  # 成交额
        if flag:
            charge1 = self._getOpenCharge(order["Cont"], qty, (pInfo["TodayBuy"] - qty), flag, linkList)
            liquidateprofit = self.__calcLiquidateProfit(order["Cont"], pInfo["BuyPrice"], pInfo["TotalBuy"],
                                                         order["OrderPrice"], qty,
                                                         cost["TradeDot"],
                                                         flag)
        else:
            charge1 = self._getOpenCharge(order["Cont"], qty, (pInfo["TodaySell"] - qty), flag, linkList)
            liquidateprofit = self.__calcLiquidateProfit(order["Cont"], pInfo["SellPrice"], pInfo["TotalSell"],
                                                         order["OrderPrice"], qty,
                                                         cost["TradeDot"],
                                                         flag)

        profit = liquidateprofit - charge
        slipLoss = self.__calcSlippage(qty, cost["Slippage"], cost["PriceTick"], cost["TradeDot"])  # 滑点损耗

        return charge, charge1, turnover, liquidateprofit, profit, linkList, slipLoss

    def _calcTodayPosition(self, order, pInfo, flag):
        """
        计算order的今持仓
        :param order: 订单
        :param pInfo: 该订单对应的合约的持仓信息
        :param flag: 为False表示买今持仓，True为卖今持仓
        :return:
        """
        if not flag:
            if len(self._orders) > 1:
                for eo in self._orders[-2::-1]:
                    if order["Cont"] == eo["Order"]["Cont"] and (
                            eo["Order"]["Direct"] == dBuy and eo["Order"]["Offset"] == oOpen):
                        if order["TradeDate"] == self._curTradeDate:
                            return pInfo["TodayBuy"] + order["OrderQty"]
                        else:
                            return order["OrderQty"]
                        # break
                    if eo == self._orders[0]:
                        return order["OrderQty"]
            else:
                return order["OrderQty"]

        if flag:
            if len(self._orders) > 1:
                for eo in self._orders[-2::-1]:
                    if order["Cont"] == eo["Order"]["Cont"] and (
                            eo["Order"]["Direct"] == dSell and eo["Order"]["Offset"] == oOpen):
                        if order["TradeDate"] == self._curTradeDate:
                            return pInfo["TodaySell"] + order["OrderQty"]
                        else:
                            return order["OrderQty"]
                        # break
                    if eo == self._orders[0]:
                        return order["OrderQty"]
            else:
                return order["OrderQty"]

    def _updateTodayPosition(self, pInfo):
        if not self._fundRecords:
            return pInfo
        else:
            if self._fundRecords[-1]["TradeDate"] == self._curTradeDate:
                return pInfo
            else:
                pInfo["TodayBuy"] = 0
                pInfo["TodaySell"] = 0
                return pInfo

    def _calcTestDay(self, start, end):
        """
        计算测试天使
        :param start: 信号计算开始时间
        :param end: 信号计算结束时间
        """
        # 回测没有进行
        if start is None or end is None:
            return -1

        s = parse(str(start))
        e = parse(str(end))
        self._testDays = (e - s).days + 1

        return self._testDays

    @property
    def getInitSetting(self):
        """获取回测的初始参数设定"""
        return self._runSet

    @property
    def firstOpenOrder(self):
        return self._firstOpenOrder

    # 这个函数应该放在外部调用还是在类内部调用比较好呢
    # 内部用的话就把tradedate传进类中。
    def _stageStatistics(self):
        """
        阶段统计计算
        :param uflag: 更新最后一条记录标志位 True: 增加记录， False: 更新记录
        """
        if self._runSet["StartFund"] == 0:
            return
        if not self._fundRecords:
            return

        day = str(self._fundRecords[-1]["TradeDate"])
        week = parse(day).isocalendar()[1]
        month = parse(day).month
        quarter = int(month / 3 if month % 3 == 0 else month / 3 + 1)
        year = parse(day).year

        # 交易次数记下来了，但是会不会存在总盈利和交易次数不匹配的情况呢：比如记录day_statis，
        # 在天的某一时刻有交易次数记录了，此时的总盈利和总亏损为某一值
        # 但是接下来仍然存在交易，但是接下来的交易只是没有满足一次交易的条件(意思是没有全平完)，
        # 但是总盈利和总亏损却变化了，这样会不会对计算有很大影响
        # 判断是否满一天或回测时间结束
        uflag = True if day != str(self._curTradeDate) else False
        self._calcStageStaticInfo(self._dailyStatis, uflag)

        # 判断是否满一星期了或回测时间结束
        # theDay = parse(str(self._fundRecords[-1]["TradeDate"]))
        uflag = True if parse(str(self._curTradeDate)).isocalendar()[1] != week else False
        self._calcStageStaticInfo(self._weekStatis, uflag)

        # 判读是否满一个月了或回测时间结束
        uflag = True if parse(str(self._curTradeDate)).month != month else False
        self._calcStageStaticInfo(self._monthStatis, uflag)

        # 判断是否满一季度了或回测时间结束
        theMonth = parse(str(self._curTradeDate)).month
        uflag = True if int(theMonth / 3 if theMonth % 3 == 0 else theMonth / 3 + 1) != quarter else False
        self._calcStageStaticInfo(self._quarterStatis, uflag)

        # 判断是否满一年了或回测时间结束
        uflag = True if parse(str(self._curTradeDate)).year != year else False
        self._calcStageStaticInfo(self._yearStatis, uflag)

    # def getLastStaticData1(self, periodStatis):
    #     if len(periodStatis) > 1:  # 是否为空
    #         lastData = periodStatis[-2]
    #     else:
    #         lastData = defaultdict(int)
    #         lastData["Equity"] = self._runSet["StartFund"]
    #     return lastData

    def getLastStaticData(self, periodStatis, flag):
        if flag:
            lastData = periodStatis[-1]
        else:
            if len(periodStatis) > 1:  # 是否为空
                lastData = periodStatis[-2]
            else:
                lastData = defaultdict(int)
                lastData["Equity"] = self._runSet["StartFund"]

        return lastData

    def _calcStageStaticInfo(self, periodStatis, uflag):
        if not self._fundRecords:
            return

        lastPeriodData = self.getLastStaticData(periodStatis, uflag)
        tt, wt, lt, et, tw, tl = 0, 0, 0, 0, 0, 0
        for p in periodStatis:
            tt += p["TradeTimes"]  # 截止目前的总交易次数
            wt += p["WinTimes"]  # 截止目前的总盈利次数
            lt += p["LoseTimes"]  # 截止目前的总亏损次数
            et += p["EventTimes"]  # 截止目前的最持平次数
            tw += p["TotalWin"]  # 截止目前的总盈利
            tl += p["TotalLose"]  # 截止目前的总亏损

        statis = defaultdict(int)
        statis["Time"] = self._fundRecords[-1]["TradeDate"]  # 日期
        statis["Equity"] = self._fundRecords[-1]["DynamicEquity"]  # 权益
        statis["NetProfit"] = statis["Equity"] - lastPeriodData["Equity"]  # 净利润
        # --------------------------------------------- #
        statis["TradeTimes"] = self._tradeTimeInfo["TradeTimes"] - tt  # 该阶段交易次数
        statis["WinTimes"] = self._tradeTimeInfo["TradeWins"] - wt  # 该阶段盈利次数
        statis["LoseTimes"] = self._tradeTimeInfo["TradeLoses"] - lt  # 该阶段亏损次数
        statis["EventTimes"] = self._tradeTimeInfo["TradeEvents"] - et  # 该阶段持平次数
        statis["TotalWin"] = self._profit["TotalWin"] - tw  # 该阶段总盈利
        statis["TotalLose"] = self._profit["TotalLose"] - tl  # 该阶段总亏损
        # ---------------------------------------------- #
        # 盈利率
        statis["Returns"] = statis["NetProfit"] / self._runSet["StartFund"] if self._runSet["StartFund"] != 0 else 0
        if statis["TradeTimes"] == 0:
            statis["WinRate"] = 0.0
        else:
            # 胜率: 非亏损交易次数/总交易次数
            statis["WinRate"] = (statis["EventTimes"] + statis["WinTimes"]) / statis["TradeTimes"]

        # 平均盈利率： 平均盈利/平均亏损
        if statis["WinTimes"] == 0:
            statis["MeanReturns"] = 0.0
        elif statis["WinTimes"] != 0:
            if statis["LoseTimes"] == 0:
                # statis["MeanReturns"] = float("inf")
                # 亏损次数是0的时候，亏损率置为1
                statis["MeanReturns"] = (statis["TotalWin"] / statis["WinTimes"])
            else:
                statis["MeanReturns"] = (statis["TotalWin"] * statis["LoseTimes"]) / (
                        statis["WinTimes"] * statis["TotalLose"])

        # 净利润增长速度：本次的盈利率 - 上次的盈利率
        # statis["IncSpeed"] = (statis["NetProfit"] - lastPeriodData["NetProfit"]) / self._runSet["StartFund"]
        statis["IncSpeed"] = statis["Returns"] - lastPeriodData["Returns"]
        if uflag:
            periodStatis.append(statis)

        else:
            if len(periodStatis) == 0:
                periodStatis.append(statis)
                return
            periodStatis[-1] = statis

    # 这个函数是不是需要整理一下呢？？？
    def _calcSingleReturns(self, extendOrder):
        """
        计算总单次盈利率
        "SumSingleWinReturns":
        "SumSingleLoseReturns":
        "EmptyPositionEquity":
        """
        pInfo = self._getSpecificPositionInfo(extendOrder["Order"]["UserNo"], extendOrder["Order"]["Cont"])
        if (extendOrder["Order"]["Direct"] == dBuy and extendOrder["Order"]["Offset"] == oCover) \
                or (extendOrder["Order"]["Direct"] == dBuy and extendOrder["Order"]["Offset"] == oCoverT):
            if pInfo["TotalSell"] == 0:
                if extendOrder["Profit"] > 0:
                    # EmptyPositionEquity不会为0，因为这种情况下，不能再继续下单了
                    singleReturns = self._profit["LastAssets"] / self._profit["EmptyPositionEquity"] - 1
                    self._profit["SumSingleWinReturns"] = self._profit["SumSingleReturns"] + singleReturns
                    self._profit["EmptyPositionEquity"] = self._profit["LastAssets"]
                if extendOrder["Profit"] < 0:
                    singleReturns = self._profit["LastAssets"] / self._profit["EmptyPositionEquity"] - 1
                    self._profit["SumSingleLoseReturns"] = self._profit["SumSingleReturns"] + singleReturns
                    self._profit["EmptyPositionEquity"] = self._profit["LastAssets"]

        elif (extendOrder["Order"]["Direct"] == dSell and extendOrder["Order"]["Offset"] == oCover) \
                or (extendOrder["Order"]["Direct"] == dSell and extendOrder["Order"]["Offset"] == oCoverT):
            if pInfo["TotalBuy"] == 0:
                if extendOrder["Profit"] > 0:
                    # EmptyPositionEquity不会为0，因为这种情况下，不能再继续下单了(有可能为0)
                    singleReturns = self._profit["LastAssets"] / self._profit["EmptyPositionEquity"] - 1
                    self._profit["SumSingleWinReturns"] = self._profit["SumSingleReturns"] + singleReturns
                    self._profit["EmptyPositionEquity"] = self._profit["LastAssets"]
                if extendOrder["Profit"] < 0:
                    singleReturns = self._profit["LastAssets"] / self._profit["EmptyPositionEquity"] - 1
                    self._profit["SumSingleLoseReturns"] = self._profit["SumSingleReturns"] + singleReturns
                    self._profit["EmptyPositionEquity"] = self._profit["LastAssets"]

    def _calcTradeTimes(self, extendOrder):
        """
        计算交易信息self._tradeTimeInfo
        :param extendOrder:
        :return:
        """
        pInfo = self._getSpecificPositionInfo(extendOrder["Order"]["UserNo"], extendOrder["Order"]["Cont"])
        # 平仓单
        if (extendOrder["Order"]["Direct"] == dBuy and extendOrder["Order"]["Offset"] == oCover) \
                or (extendOrder["Order"]["Direct"] == dBuy and extendOrder["Order"]["Offset"] == oCoverT):
            if pInfo["TotalSell"] == 0:
                self._updateTradeTimes(extendOrder)
        elif (extendOrder["Order"]["Direct"] == dSell and extendOrder["Order"]["Offset"] == oCover) \
                or (extendOrder["Order"]["Direct"] == dSell and extendOrder["Order"]["Offset"] == oCoverT):
            if pInfo["TotalBuy"] == 0:
                self._updateTradeTimes(extendOrder)

    def _updateTradeTimes(self, extendOrder):
        self._tradeTimeInfo["TradeTimes"] += 1
        if extendOrder["Profit"] > 0:
            self._tradeTimeInfo["TradeWins"] += 1
        if extendOrder["Profit"] < 0:
            self._tradeTimeInfo["TradeLoses"] += 1
        if extendOrder["Profit"] == 0:
            self._tradeTimeInfo["TradeEvents"] += 1

    # 暂时不用
    def _calcEmptyPositionPeriod(self):
        """计算空仓信息"""
        # 统计k线上有无持仓时，当在当根k线上发生了开仓又平完的操作时，
        # 暂时将该k线也记做空仓的周期吧（这样记是不是错误的呀）
        # if self._strategy["CurrentBarIndex"] == self._currentBar:  # 确保在收盘时统计空仓信
        positions = self.getPositionInfo()
        for pInfo in positions.values():
            if pInfo["TotalBuy"] != 0 or pInfo["TotalSell"] != 0:
                self._continueEmptyPeriod = 0
                return
        self._continueEmptyPeriod += 1
        self._tradeInfo["EmptyPeriod"] += 1

    @property
    def getYearStatis(self):
        return self._yearStatis

    @property
    def getQuarterStatis(self):
        return self._quarterStatis

    @property
    def getMonthStatis(self):
        return self._monthStatis

    @property
    def getWeekStatis(self):
        return self._weekStatis

    @property
    def getDailyStatis(self):
        return self._dailyStatis

    @property
    def getOrders(self):
        return self._orders

    def getReportDetail(self):
        # 先暂时把计算self._testDays的方法放在这里吧，没想好放在哪里比较合适
        ret = self._calcTestDay(self._beginDate, self._endDate)
        if ret <= 0: return []
        # TODO: 回测开始日期和回测结束日期在calcProfit中更新，所以把self._beginDate和self._endDate传进类中
        positions = self.getPositionInfo()
        self._reportDetails = ReportDetail(self._runSet, positions, self._profit, self._testDays,
                                           self._fundRecords, self._tradeTimeInfo, self._orders,
                                           self._tradeInfo, self._beginDate, self._endDate).all()
        return self._reportDetails

    def _calcTradeInfo(self):
        # TODO: 这个函数好好看下
        # 如果数据不满一天的话怎么办呢？？？（从开始有数据时就使天数加一）
        # 在计算最大、最小这类数据的时候建立了这么多类的私有变量，
        # 是不是可以用局部变量表示呢？

        # 最长空仓周期先不考虑
        # if self._continueEmptyPeriod > self._tradeInfo["MaxContinuousEmptyPeriod"]:
        #     self._tradeInfo["MaxContinuousEmptyPeriod"] = self._continueEmptyPeriod

        if not self._fundRecords:
            self._tradeInfo["MaxWinContinueDays"] = 0
            self._tradeInfo["MaxWinContinueDaysTime"] = "-"
            self._tradeInfo["MaxLoseContinueDays"] = 0
            self._tradeInfo["MaxLoseContinueDaysTime"] = "-"
            return

        # 每次都先更新了fund_records，所以下面的条件根本就不可能满足？？？一直盈利或一直亏损的时候信息不完整怎么办
        # 存在最后一个记录无法更新的问题。。。
        if self._curTradeDate != self._fundRecords[-1]["TradeDate"]:
            if self._profit["LastAssets"] > self._runSet["StartFund"]:  # 盈利
                if self._continueWinDays == 0:
                    self._continueWinDaysStartTime = self._fundRecords[-1]["TradeDate"]
                self._continueWinDays += 1
                self._continueWinDaysEndTime = self._fundRecords[-1]["TradeDate"]
                self._continueLoseDays = 0
                if self._continueWinDays > self._tradeInfo["MaxWinContinueDays"]:
                    self._tradeInfo["MaxWinContinueDays"] = self._continueWinDays
                    self._tradeInfo["MaxWinContinueDaysTime"] = str(self._continueWinDaysStartTime) + \
                                                                " - " + str(self._continueWinDaysEndTime)

            elif self._profit["LastAssets"] < self._runSet["StartFund"]:  # 亏损
                if self._continueLoseDays == 0:
                    self._continueLoseDaysStartTime = self._fundRecords[-1]["TradeDate"]
                self._continueLoseDays += 1
                self._continueLoseDaysEndTime = self._fundRecords[-1]["TradeDate"]
                self._continueWinDays = 0
                if self._continueLoseDays > self._tradeInfo["MaxLoseContinueDays"]:
                    self._tradeInfo["MaxLoseContinueDays"] = self._continueLoseDays
                    self._tradeInfo["MaxLoseContinueDaysTime"] = str(self._continueLoseDaysStartTime) + \
                                                                 " - " + str(self._continueLoseDaysEndTime)

            else:  # 持平
                self._continueWinDays = 0
                self._continueLoseDays = 0

        if self._curTradeDate != self._fundRecords[-1]["TradeDate"]:
            self._tradeInfo["CurrentDayEquity"] = self._fundRecords[-1]["DynamicEquity"]
            if self._tradeInfo["PreviousDayEquity"]:
                if self._tradeInfo["CurrentDayEquity"] > self._tradeInfo["PreviousDayEquity"]:
                    if self._winComparedIncreaseContinueDays == 0:
                        self._winComparedIncreaseContinueDaysStartTime = self._fundRecords[-1]["TradeDate"]
                    self._winComparedIncreaseContinueDaysEndTime = self._fundRecords[-1]["TradeDate"]
                    self._winComparedIncreaseContinueDays += 1
                    self._loseComparedIncreaseContinueDays = 0
                    if self._winComparedIncreaseContinueDays > self._tradeInfo["MaxWinComparedIncreaseContinueDays"]:
                        self._tradeInfo["MaxWinComparedIncreaseContinueDays"] = self._winComparedIncreaseContinueDays
                        self._tradeInfo["MaxWinComparedIncreaseContinueDaysTime"] = str(
                            self._winComparedIncreaseContinueDaysStartTime) + \
                                                                                    " - " + str(
                            self._winComparedIncreaseContinueDaysEndTime)
                elif self._tradeInfo["CurrentDayEquity"] < self._tradeInfo["PreviousDayEquity"]:
                    if self._loseComparedIncreaseContinueDays == 0:
                        self._loseComparedIncreaseContinueDaysStartTime = self._fundRecords[-1]["TradeDate"]
                    self._loseComparedIncreaseContinueDaysEndTime = self._fundRecords[-1]["TradeDate"]
                    self._loseComparedIncreaseContinueDays += 1
                    self._winComparedIncreaseContinueDays = 0
                    if self._loseComparedIncreaseContinueDays > self._tradeInfo["MaxLoseComparedIncreaseContinueDays"]:
                        self._tradeInfo["MaxLoseComparedIncreaseContinueDays"] = self._loseComparedIncreaseContinueDays
                        self._tradeInfo["MaxLoseComparedIncreaseContinueDaysTime"] = str(
                            self._loseComparedIncreaseContinueDaysStartTime) + \
                                                                                     " - " + str(
                            self._loseComparedIncreaseContinueDaysEndTime)
                else:
                    self._winComparedIncreaseContinueDays = 0
                    self._loseComparedIncreaseContinueDays = 0
            else:
                self._tradeInfo["MaxWinComparedIncreaseContinueDays"] = 0
                self._tradeInfo["MaxWinComparedIncreaseContinueDaysTime"] = "-"
                self._tradeInfo["MaxLoseComparedIncreaseContinueDays"] = 0
                self._tradeInfo["MaxLoseComparedIncreaseContinueDaysTime"] = "-"

            self._tradeInfo["PreviousDayEquity"] = self._fundRecords[-1]["DynamicEquity"]

    def getAvailableFund(self):
        """
        :return: 返回最新的资金记录信息，若资金记录为空，则返回初始资金
        """
        if self._fundRecords:
            return self._fundRecords[-1]['Available']
        return self._runSet["StartFund"]

    def getKLineType(self):
        return {
            "KLineType": self._runSet["KLineType"],
            "KLineSlice": self._runSet["KLineSlice"]
        }

    def testResult(self):
        """
        获取回测报告所需的数据
        :return:
        """
        result = {}

        result["Fund"] = self.getFundRecord()
        result["Stage"] = {
            "年度分析": self.getYearStatis,
            "季度分析": self.getQuarterStatis,
            "月度分析": self.getMonthStatis,
            "周分析": self.getWeekStatis,
            "日分析": self.getDailyStatis
        }
        result["Orders"] = self.getOrders
        result["Detail"] = self.getReportDetail()
        result["KLineType"] = {
            "KLineType": self._runSet["KLineType"],
            "KLineSlice": self._runSet["KLineSlice"]
        }

        return copy.deepcopy(result)

    def getMonResult(self):
        """获取量化界面策略运行监控所需数据"""

        result = {}

        result.update(
            {
                "MaxRetrace": self._profit['MaxRetracement'],
                "NetProfit": self._profit["TotalProfit"],
                "WinRate": self._profit["WinRate"],
                "Available": self._fundRecords[-1]['Available'] if len(self._fundRecords) > 0 else self._runSet[
                    "StartFund"]
            }
        )
        return result
