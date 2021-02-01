#-*-:conding:utf-8-*-

from multiprocessing import Process, Queue
from threading import Thread
import time, os, sys
from capi.com_types import *
from api import base_api
from .strategy_model import StrategyModel
from .engine_model import DataModel
from capi.event import Event
import traceback
import importlib
import queue
import datetime
from datetime import datetime
import copy
from collections import OrderedDict
from tkinter import Tk



class StrategyManager(object):
    '''策略进程管理器，负责进程创建、销毁、暂停等'''

    def __init__(self, logger, st2egQueue):
        self.logger = logger

        # 策略进程到引擎的队列
        self._st2egQueue = st2egQueue

        # 进程字典，{'id', Strategy}
        self._strategyDict = {}
        self._strategyInfo = {}
        self._strategyAttribute = {}
        self._isEquantExitStage = False
        self._isEquantExitCom = False

    @staticmethod
    def run(strategy):
        strategy.run()

    def getStrategyName(self, strategyId):
        assert strategyId in self._strategyInfo, 'error '
        return self._strategyDict[strategyId].getStrategyName()

    def getStrategyState(self, strategyId):
        assert strategyId in self._strategyInfo, 'error '
        return self._strategyInfo[strategyId]["StrategyState"]

    def handleStrategyException(self, event):
        strategyId = event.getStrategyId()
        if strategyId not in self._strategyInfo:
            return
        self._strategyInfo[strategyId]["StrategyState"] = ST_STATUS_EXCEPTION
        self.destroyProcessByStrategyId(event.getStrategyId())
        self._strategyInfo[strategyId]["Process"] = None

    def create(self, strategyId, eg2stQueue, eg2uiQueue, st2egQueue, event):
        qdict = {'eg2st': eg2stQueue, 'st2eg': st2egQueue, 'st2ui':eg2uiQueue}
        strategy = Strategy(self.logger, strategyId, qdict, event)
        self._strategyDict[strategyId] = strategy
        process = Process(target=self.run, args=(strategy,))
        process.daemon = True
        process.start()

        args = {
            "Config": event.getData()["Args"],
            # "UIConfig": copy.deepcopy(event.getData()["Args"]),
            "Path": event.getData()["Path"],
            "StrategyName": None,
            "StrategyId": strategyId,
        }

        self.insertNewStrategy(strategyId, process, args)

    # 新建策略、恢复策略调用
    def insertNewStrategy(self, strategyId, process, args):
        self._strategyInfo[strategyId] = {
            "StrategyId": strategyId,
            "Process": process,
            "StrategyState": ST_STATUS_NONE,
        }
        self._strategyAttribute[strategyId] = args

    def insertResumedStrategy(self, strategyId, args):
        self._strategyInfo[strategyId] = {
            "StrategyId": strategyId,
            "Process": None,
            "StrategyState": ST_STATUS_QUIT,
        }
        # 策略恢复的时候用
        self._strategyAttribute[strategyId] = args

    def quitStrategy(self, event):
        strategyId = event.getStrategyId()
        assert strategyId in self._strategyInfo and self._strategyInfo[strategyId]["Process"].is_alive(), " error "
        strategyInfo = self._strategyInfo[strategyId]
        strategyInfo["StrategyState"] = ST_STATUS_QUIT
        self.destroyProcess(self._strategyInfo[strategyId]["Process"], strategyId)
        strategyInfo["Process"] = None

    def removeQuitedStrategy(self, event):
        assert event.getStrategyId() in self._strategyInfo, "error"
        self._strategyInfo.pop(event.getStrategyId())
        self._strategyAttribute.pop(event.getStrategyId())

    def removeRunningStrategy(self, event):
        strategyId = event.getStrategyId()
        if strategyId not in self._strategyInfo:
            self.logger.error(f"策略{strategyId}在engine已经被删除了")
            return
        # assert strategyId in self._strategyInfo, "error"
        self.destroyProcess(self._strategyInfo[strategyId]['Process'], strategyId)
        self._strategyInfo.pop(strategyId)
        self._strategyAttribute.pop(event.getStrategyId())

    def removeExceptionStrategy(self, event):
        self.removeRunningStrategy(event)

    def restartStrategy(self, engineLoadFunc, event):
        assert event.getStrategyId() in self._strategyInfo, "error"
        strategyInfo = self._strategyAttribute[event.getStrategyId()]
        loadStrategyEvent = Event({
            'EventSrc': EEQU_EVSRC_UI,
            'EventCode': EV_UI2EG_LOADSTRATEGY,
            'SessionId': None,
            'StrategyId': 0,
            'UserNo': '',
            'Data': {
                'Path': strategyInfo["Path"],
                'Args': strategyInfo["Config"],
                "NoInitialize": True,
            }
        })
        engineLoadFunc(loadStrategyEvent, strategyId=event.getStrategyId())

    def singleStrategyExitComEquantExit(self, event):
        self._isEquantExitStage = True
        strategyId = event.getStrategyId()
        assert strategyId in self._strategyInfo, " error "
        strategyInfo = self._strategyInfo[event.getStrategyId()]
        strategyInfo["StrategyState"] = ST_STATUS_QUIT
        #

    def isAllStrategyQuit(self):
        result = True
        for k, v in self._strategyInfo.items():
            if v["StrategyState"] != ST_STATUS_QUIT and v["StrategyState"] != ST_STATUS_EXCEPTION:
                result = False
                break
        # print("now is equant exit complete ", result)
        return result

    def stopStrategy(self, strategyId):
        pass

    def resumeStrategy(self, strategyId):
        pass

    def destroyProcessByStrategyId(self, strategyId):
        assert strategyId in self._strategyInfo, " error "
        process = self._strategyInfo[strategyId]["Process"]
        self.destroyProcess(process, strategyId)
        self._strategyInfo[strategyId]["Process"] = None

    def destroyProcess(self, process, strategyId):
        if not process or not process.is_alive:
            self.logger.info(f"策略{strategyId}所在进程已经退出，将忽略")
            return
        try:
            process.terminate()
            process.join(timeout=1)
            self.logger.debug("strategy %d exit success" % strategyId)
        except Exception as e:
            # traceback.print_exc()
            self.logger.debug("strategy %d exit fail" % strategyId)

    def syncStrategyConfig(self, event):
        strategyId = event.getStrategyId()
        self._strategyAttribute[strategyId] = event.getData()

    def getStrategyConfig(self):
        result = {}
        for strategyId, value in self._strategyInfo.items():
            if value["StrategyState"] == ST_STATUS_EXCEPTION:
                continue
            v = self._strategyAttribute[strategyId]
            result[strategyId] = {
                "Config":v["Config"],
                "Path":v["Path"],
                "StrategyName":v["StrategyName"],
                "StrategyId":strategyId,
                #"UIConfig":v["UIConfig"]
            }
        result = OrderedDict(sorted(result.items(), key=lambda obj: str(obj[0])))
        return result

    def getStrategyAttribute(self, strategyId):
        return self._strategyAttribute[strategyId]


class StrategyContext:
    def __init__(self):
        self._strategyStatus = None
        self._triggerType = None
        self._conTractNo = None
        self._kLineType = None
        self._kLineSlice = None
        self._tradeDate = None
        self._dateTimeStamp = None
        self._triggerData = None
        self._parameter = {}

    def strategyStatus(self):
        return self._strategyStatus

    def triggerType(self):
        return self._triggerType

    def contractNo(self):
        return self._conTractNo

    def kLineType(self):
        return self._kLineType

    def kLineSlice(self):
        return self._kLineSlice

    def tradeDate(self):
        if self._tradeDate is not None:
            return str(self._tradeDate)
        else:
            return None

    def dateTimeStamp(self):
        if self._dateTimeStamp is not None:
            return str(self._dateTimeStamp)
        else:
            return None

    def triggerData(self):
        return self._triggerData

    def setCurTriggerSourceInfo(self, args):
        self._strategyStatus = copy.deepcopy(args["Status"])
        self._triggerType = copy.deepcopy(args["TriggerType"])
        self._conTractNo = copy.deepcopy(args["ContractNo"])
        self._kLineType = copy.deepcopy(args["KLineType"])
        self._kLineSlice = copy.deepcopy(args["KLineSlice"])
        self._tradeDate = copy.deepcopy(args["TradeDate"])
        self._dateTimeStamp = copy.deepcopy(args["DateTimeStamp"])
        self._triggerData = copy.deepcopy(args["TriggerData"])

    @property
    def params(self):
        return self._parameter

    @params.setter
    def params(self, parameter):
        self._parameter = parameter


class TradeRecord(object):
    def __init__(self, eSessionId, orderData={}):
        self._eSessionId = eSessionId   # eSessionId
        self._barInfo = None # 触发的Bar信息
        # SessionId
        self._sessionId = orderData['SessionId'] if 'SessionId' in orderData else None
        
        #用户编号
        self._userNo = orderData['UserNo'] if 'UserNo' in orderData else None
        # 合约编号
        self._contNo = orderData['Cont'] if 'Cont' in orderData else None
        # 定单号
        self._orderId = orderData['OrderId'] if 'OrderId' in orderData else None
        # 委托单号
        self._orderNo = orderData['OrderNo'] if 'OrderNo' in orderData else None
        # 方向
        self._direct = orderData['Direct'] if 'Direct' in orderData else None
        # 开平
        self._offset = orderData['Offset'] if 'Offset' in orderData else None
        # 订单状态
        self._orderState = orderData['OrderState'] if 'OrderState' in orderData else None
        # 委托成交价
        self._matchPrice = orderData['MatchPrice'] if 'MatchPrice' in orderData else None
        # 委托成交量
        self._matchQty = orderData['MatchQty'] if 'MatchQty' in orderData else None
        # 委托价
        self._orderPrice = orderData['OrderPrice'] if 'OrderPrice' in orderData else None
        # 委托订单量
        self._orderQty = orderData['OrderQty'] if 'OrderQty' in orderData else None
        # 下单时间
        self._insertTime = orderData['InsertTime'] if 'InsertTime' in orderData else None
        # 订单更新时间
        self._updateTime = orderData['UpdateTime'] if 'UpdateTime' in orderData else None


    def updateOrderInfo(self, eSessionId, orderData):
        if eSessionId != self._eSessionId:
            return
            
        if 'UserNo' in orderData:
            self._userNo = orderData['UserNo']

        if 'SessionId' in orderData:
            self._sessionId = orderData['SessionId']
        if 'Cont' in orderData:
            self._contNo = orderData['Cont']
        if 'OrderId' in orderData:
            self._orderId = orderData['OrderId']
        if 'OrderNo' in orderData:
            self._orderNo = orderData['OrderNo']
        if 'Direct' in orderData:
            self._direct = orderData['Direct']
        if 'Offset' in orderData:
            self._offset = orderData['Offset']
        if 'OrderState' in orderData:
            self._orderState = orderData['OrderState']
        if 'MatchPrice' in orderData:
            self._matchPrice = orderData['MatchPrice']
        if 'MatchQty' in orderData:
            self._matchQty = orderData['MatchQty']
        if 'OrderPrice' in orderData:
            self._orderPrice = orderData['OrderPrice']
        if 'OrderQty' in orderData:
            self._orderQty = orderData['OrderQty']
        if 'InsertTime' in orderData:
            self._insertTime = orderData['InsertTime']
        if 'UpdateTime' in orderData:
            self._updateTime = orderData['UpdateTime']    

    def getBarInfo(self):
        return self._barInfo


class Strategy:
    def __init__(self, logger, id, args, event):
        self._strategyId = id
        self.logger = logger
        self._dataModel = None
        
        data = event.getData()
        self._filePath = data['Path']
        self._argsDict = data['Args']

        # 是否运行initialize函数
        self._noInitialize = "NoInitialize" in data and data["NoInitialize"]
        self._uiConfig = copy.deepcopy(data['Args'])

        self._eg2stQueue = args['eg2st']
        self._st2egQueue = args['st2eg']

        self._isSt2EgQueueEffective = True
        self._st2uiQueue = args['st2ui']
        moduleDir, moduleName = os.path.split(self._filePath)
        self._strategyName = ''.join(moduleName.split('.')[:-1])

        # 策略所在进程状态, Ready、Running、Exit、Pause
        self._strategyState = StrategyStatusReady

        # 策略异常时策略是否在界面上的策略列表中显示
        # 当策略没有执行handle_data就引起异常时，策略将不会在界面上显示
        # 辅助更新本地保存的最大策略编号
        self._isShowForException = True

        self._runStatus = ST_STATUS_NONE
        self._curTriggerSourceInfo = None
        self._firstTriggerQueueEmpty = True

        # self._strategyId+"-"+self._eSessionId 组成本地生成的eSessionId
        self._eSessionId = 1
        # 该策略的所有下单信息
        self._eSessionIdList = [] # 存储本地生成的eSessionId，为了保存下单顺序信息
        self._localOrder = {} # {本地生成的eSessionId : TradeRecode对象}
        
        self._moneyLastTime = 0
        self._virtualPosTime = 0
        # self._userModelDict = {}

    # ////////////////////////////对外接口////////////////////
    def _initialize(self):
        self._strategyState = StrategyStatusRunning
        # 用户模板函数路径加入系统路径，并扩展baseapi的作用域
        workPath = os.path.abspath('.')
        userPath = workPath + r"\strategy\扩展函数"
        if userPath not in sys.path:
            sys.path.insert(0, userPath)
        
        moduleDir, moduleName = os.path.split(self._filePath)
        moduleName = os.path.splitext(moduleName)[0]

        if moduleDir not in sys.path:
            sys.path.insert(0, moduleDir)
            
        # 3. 创建数据模块
        self._dataModel = StrategyModel(self)
        self._cfgModel  = self._dataModel.getConfigModel()
        self._hisModel  = self._dataModel.getHisQuoteModel()
        self._qteModel  = self._dataModel.getQuoteModel()
        self._trdModel  = self._dataModel.getTradeModel()
        
        self._userModelDict = {}

        # 4. 初始化系统函数
        self._baseApi = base_api.baseApi.updateData(self, self._dataModel)
        # 扩展用户模板函数作用域
        if os.path.exists(userPath):
            userDir = os.listdir(userPath)
            for file in userDir:
                modelFile = os.path.splitext(file)[0]
                model = importlib.import_module(modelFile)
                model.__dict__.update(base_api.__dict__)
                self._userModelDict[modelFile] = model

        # 1. 加载用户策略
        import builtins
        builtins.g_params = {}
        userModule = importlib.import_module(moduleName)
        userModule.__dict__.update(base_api.__dict__)
        # 2. 创建策略上下文
        self._context = StrategyContext()

        self._cfgModel.setParams(self._argsDict["Params"])

        builtins.g_params = {k:v[0] for k,v in self._argsDict["Params"].items()}

        # 5. 初始化用户策略参数
        if not self._noInitialize:
            userModule.initialize(self._context)

        # self._cfgModel.setParams(self._argsDict["Params"])
        #
        # builtins.g_params = {k:v[0] for k,v in self._argsDict["Params"].items()}
        #     self._argsDict["Params"] = self._context.params
        #     self._dataModel.getConfigModel().setParams(self._context.params)
        # else:
        #     self._context.params = self._argsDict["Params"]

        self._userModule = userModule
        # 5.1 同步配置
        self._sendConfig2Engine()
        # 6. 初始化model
        self._dataModel.initialize()

        # 7.  注册处理函数
        self._regEgCallback()

        # 8. 启动策略运行线程
        self._triggerQueue = queue.Queue()
        self._startStrategyThread()

        # 9. 启动策略心跳线程
        self._startStrategyTimer()
        
    def _regEgCallback(self):
        self._egCallbackDict = {
            #//////////////////////引擎发送的数据/////////////////////////
            EV_EG2ST_EXCHANGE_RSP           : self._onExchange               ,
            EV_EG2ST_COMMODITY_RSP          : self._onCommodity              ,
            EV_EG2ST_CONTRACT_RSP           : self._onContract               ,
            EV_EG2ST_UNDERLAYMAPPING_RSP    : self._onUnderlayMap            ,
            EV_EG2ST_SUBQUOTE_RSP           : self._onQuoteRsp               ,
            EV_EG2ST_SNAPSHOT_NOTICE        : self._onQuoteNotice            ,
            EV_EG2ST_DEPTH_NOTICE           : self._onDepthNotice            ,
            EV_EG2ST_HISQUOTE_RSP           : self._onHisQuoteRsp            ,
            EV_EG2ST_HISQUOTE_NOTICE        : self._onHisQuoteNotice         ,
            
            EV_EG2ST_LOGINNO_RSP            : self._onLoginInfo              ,
            EV_EG2ST_USERNO_RSP             : self._onUserInfo               ,
            EV_EG2ST_MONEY_RSP              : self._onMoneyInfo              ,
            EV_EG2ST_ORDER_RSP              : self._onOrderInfo              ,
            EV_EG2ST_MATCH_RSP              : self._onMatchInfo              ,
            EV_EG2ST_POSITION_RSP           : self._onPositionInfo           ,
            EV_EG2ST_USER_NOTICE            : self._onUserRedayInfo          ,

            #//////////////////////API直接推送的数据/////////////////////
            EEQU_SRVEVENT_TRADE_LOGINQRY    : self._onTradeLoginQry    ,
            EEQU_SRVEVENT_TRADE_LOGINNOTICE : self._onTradeLoginNotice       ,
            EEQU_SRVEVENT_TRADE_USERQRY     : self._onTradeUserQry           ,
            EEQU_SRVEVENT_TRADE_MATCHQRY    : self._onTradeMatchQry          ,
            EEQU_SRVEVENT_TRADE_MATCH       : self._onTradeMatch             ,
            EEQU_SRVEVENT_TRADE_POSITQRY    : self._onTradePositionQry       ,
            EEQU_SRVEVENT_TRADE_POSITION    : self._onTradePosition          ,
            EEQU_SRVEVENT_TRADE_FUNDQRY     : self._onTradeMoney           ,
            EEQU_SRVEVENT_TRADE_ORDERQRY    : self._onTradeOrderQry          ,
            EEQU_SRVEVENT_TRADE_ORDER       : self._onTradeOrder             ,
            EEQU_SRVEVENT_TRADE_EXCSTATEQRY : self._onExchangeStateNotice    ,
            EEQU_SRVEVENT_TRADE_EXCSTATE    : self._onExchangeStateNotice    ,
            
            #//////////////////////UI推送的数据/////////////////////////
            EV_UI2EG_REPORT                 : self._onReport                 ,
            EV_UI2EG_LOADSTRATEGY           : self._onLoadStrategyResponse   ,
            EV_UI2EG_STRATEGY_QUIT          : self._onStrategyQuit           ,
            EV_UI2EG_EQUANT_EXIT            : self._onEquantExit             ,
            EV_UI2EG_STRATEGY_FIGURE        : self._switchStrategy           ,
            EV_UI2EG_STRATEGY_REMOVE        : self._onStrategyRemove         ,
            EV_UI2EG_SYNCPOS_CONF           : self._onSyncPosConf            ,
        }
        
    def _actualRun(self):
        try:
            # 1. 内部初始化
            self._initialize()
            # 1.1 请求交易所、品种、合约等
            self._reqExchange()
            self._reqCommodity()
            # self._reqContract()
            # 1.2 请求主力/近月/指数合约映射合约信息
            self._reqUnderlayMap()
            # 2. 订阅即时行情
            self._subQuote()
            # 3. 请求历史行情
            self._reqHisQuote()
            # 4. 查询交易数据
            self._reqLoginInfo()
            # 5. 数据处理
            self._mainLoop()
        except Exception as e:
            self._strategyState = StrategyStatusExit
            self._isSt2EgQueueEffective = False
            self._isShowForException = False
            errorText = traceback.format_exc()
            # traceback.print_exc()
            self._exit(-1, errorText)

    def run(self):
        self._actualThread = Thread(target=self._actualRun)
        self._actualThread.start()
    
        self.top = Tk()
        self.top.withdraw()
        self.top.mainloop()
    
    # ////////////////////////////内部接口////////////////////
    def _isExit(self):
        return self._strategyState == StrategyStatusExit

    def _isPause(self):
        return self._strategyState == StrategyStatusPause

    # 从engine进程接受事件并处理
    def _mainLoop(self):
        while True:
            if self._isExit():
                time.sleep(0.2)
                self._clearQueue(self._eg2stQueue)
                continue
            event = self._eg2stQueue.get()
            code = event.getEventCode()
            if code not in self._egCallbackDict:
                self.logger.warn("_egCallbackDict code(%d) not register!"%code)
                continue
            self._egCallbackDict[code](event) 

    def _clearQueue(self, someQueue):
        try:
            while True:
                someQueue.get_nowait()
        except queue.Empty:
            pass

    def _runStrategy(self):
        try:
            # 等待回测阶段
            self._runStatus = ST_STATUS_HISTORY
            self._send2UiEgStatus(self._runStatus)
            # runReport中会有等待

            self._dataModel.runReport(self._context, self._userModule.handle_data)

            if not self._dataModel.getConfigModel().isActualRun():
                self.logger.warn(f"未选择实盘运行，如果需要请在设置界面勾选'实盘运行'，或者在策略代码中调用SetActual()")

            while not self._isExit():
                try:
                    # 账号数据未准备就绪就停止实盘运行
                    userNo = self._cfgModel.getUserNo()
                    if userNo:
                        if userNo not in self._trdModel.getUserInfo():
                            continue
                        elif not self._trdModel.getUserInfo()[userNo].isDataReady():

                            continue

                    event = self._triggerQueue.get(timeout=0.1)
                    # 发单方式，实时发单、k线稳定后发单。
                    self._dataModel.runRealTime(self._context, self._userModule.handle_data, event)
                except queue.Empty:
                    if self._firstTriggerQueueEmpty:
                        self._clearHisPos()
                        self._atHisOver()
                        # 撮合成交时清除历史阶段排队单
                        if self._cfgModel.isMatchMode():
                            self._clearWaitOrder()

                        self._runStatus = ST_STATUS_CONTINUES
                        self._send2UiEgStatus(self._runStatus)
                        self._firstTriggerQueueEmpty = False
        except Exception as e:
                self._strategyState = StrategyStatusExit
                self._isSt2EgQueueEffective = False
                errorText = traceback.format_exc()
                # traceback.print_exc()
                self._exit(-1, errorText)

    def _clearHisPos(self):
        '''清空历史持仓'''
        if self._runStatus == ST_STATUS_CONTINUES:
            return
            
        if not self._cfgModel.isActualRun():
            return
            
        if not self._cfgModel.getAutoSyncPos():
            return
    
        calc = self._dataModel.getCalcCenter()
        # 获取该策略所有合约的虚拟持仓
        posDict = calc.getUsersPosition()
        #self.logger.debug("PosDict1:%s" %posDict)
        trd = self._dataModel.getTradeModel()
        users = trd.getAllAccountId()
        
        for id in posDict:
            conts = posDict[id]
            for ct in conts:
                buyPos = conts[ct]['TotalBuy']
                buyPrice = conts[ct]['BuyPrice']
                if buyPos > 0:
                    self._dataModel.setSell(id, ct, buyPos, buyPrice)
                    
                sellPos = conts[ct]['TotalSell']
                sellPrice = conts[ct]['SellPrice']
                if sellPos > 0:
                    self._dataModel.setBuyToCover(id, ct, sellPos, sellPrice)

        posDict = calc.getUsersPosition()
        #self.logger.debug("PosDict2:%s" %posDict)

    def _clearWaitOrder(self):
        """清除历史阶段按撮合成交的排队的订单"""
        self._dataModel.getHisQuoteModel().clearWaitOrdersWhenHisOver()

    def _startStrategyThread(self):
        '''历史数据准备完成后，运行策略'''
        self._stThread = Thread(target=self._runStrategy)
        self._stThread.start()
        
    def _triggerTime(self):
        '''检查定时触发'''
        if not self._dataModel.getConfigModel().hasTimerTrigger() or not self.isRealTimeStatus():
            return

        nowTime = datetime.now()
        for i,timeSecond in enumerate(self._dataModel.getConfigTimer()):
            specifiedTime = datetime.strptime(timeSecond, "%H%M%S")
            if 0<=(nowTime-specifiedTime).seconds<1 and not self._isTimeTriggered[i]:
                self._isTimeTriggered[i] = True
                key = self._dataModel.getConfigModel().getKLineShowInfoSimple()
                dateTimeStamp, tradeDate, lv1Data = self.getTriggerTimeAndData(key[0])
                event = Event({
                    "EventCode" : ST_TRIGGER_TIMER,
                    "ContractNo": None,
                    "KLineType" : None,
                    "KLineSlice": None,
                    "Data":{
                        "TradeDate": tradeDate,
                        "DateTimeStamp": dateTimeStamp,
                        "Data":timeSecond
                    }
                })
                self._triggerQueue.put(event)
        
    def _triggerCycle(self):
        '''检查周期性触发'''
        if not self._dataModel.getConfigModel().hasCycleTrigger():
            return

        if not self.isRealTimeStatus():
            return

        nowTime = datetime.now()
        cycle = self._dataModel.getConfigCycle()
        if (nowTime - self._nowTime).total_seconds()*1000>cycle:
            self._nowTime = nowTime
            key = self._dataModel.getConfigModel().getKLineShowInfoSimple()
            dateTimeStamp, tradeDate, lv1Data = self.getTriggerTimeAndData(key[0])
            event = Event({
                "EventCode": ST_TRIGGER_CYCLE,
                "ContractNo": None,
                "KLineType" : None,
                "KLineSlice": None,
                "Data":{
                    "TradeDate": tradeDate,
                    "DateTimeStamp": dateTimeStamp,
                    "Data": None,
                }
            })
            self._triggerQueue.put(event)
            
    def _triggerMoney(self):
        nowTime = datetime.now()
        if self._moneyLastTime == 0 or (nowTime - self._moneyLastTime).total_seconds() > 1:
            self._moneyLastTime = nowTime
            data = self._dataModel.getMonResult()
            if len(data) == 0:
                return
            event = Event({
                "StrategyId" : self._strategyId,
                "EventCode": EV_EG2ST_MONITOR_INFO,
                "Data": self._dataModel.getMonResult()
            })

            self.sendEvent2UI(event)

    def _reportStrategyPosition(self):
        nowTime = datetime.now()
        if self._virtualPosTime == 0 or (nowTime - self._virtualPosTime).total_seconds() >= 1:
            self._virtualPosTime = nowTime
            calc = self._dataModel.getCalcCenter()
            # 获取该策略所有合约的虚拟持仓
            posDict = calc.getUsersPosition()
            if len(posDict) == 0:
                return
            event = Event({
                "StrategyId" : self._strategyId,
                "EventCode"   : EV_ST2EG_POSITION_NOTICE,
                "Data"        : posDict
            })
            
            self.sendEvent2Engine(event)


    def _runTimer(self):
        timeList = self._dataModel.getConfigTimer()
        if timeList is None:
            timeList = []
        # self._isTimeTriggered = [False for i in timeList]
        timeListLength = len(timeList)
        self.setDefaultIsTimeTriggered(timeListLength)
        self._nowTime = datetime.now()
        # 用于判断定时触发是否切换日期了
        self._timeTriggerStartTime = datetime.now()
        '''秒级定时器'''
        while not self._isExit() and not self._isPause():
            # 定时触发
            self._triggerTime()
            # 周期性触发
            self._triggerCycle()
            # 通知资金变化
            self._triggerMoney()
            # 发送持仓变化
            self._reportStrategyPosition()
            # 休眠100ms
            time.sleep(0.1)
            # 日期切换时重置self._isTimeTriggerd
            if (datetime.now() - self._timeTriggerStartTime).days >= 1:
                self.setDefaultIsTimeTriggered(timeListLength)
                self._timeTriggerStartTime = datetime.now()

    def setDefaultIsTimeTriggered(self, length):
        self._isTimeTriggered = [False for _ in range(length)]


    def _startStrategyTimer(self):
        self._stTimer = Thread(target=self._runTimer)
        self._stTimer.start()
        
    def _send2UiEgStatus(self, status):
        '''通知界面和引擎策略运行状态'''
        event = Event({
            "StrategyId" : self._strategyId,
            "EventCode"  : EV_EG2UI_STRATEGY_STATUS,
            "Data"       : {
                'Status' : status
            }
        })
        self.sendEvent2UI(event)
        self.sendEvent2Engine(event)
    
    # ////////////////////////////内部数据请求接口////////////////////
    def _reqData(self, code, data=''):
        event = Event({
            'EventCode': code,
            'StrategyId': self._strategyId,
            'Data': data,
        })
        self.sendEvent2Engine(event)
    
    def _reqExchange(self):
        self._reqData(EV_ST2EG_EXCHANGE_REQ)

    def _reqCommodity(self):
        self._reqData(EV_ST2EG_COMMODITY_REQ)

    def _reqContract(self):
        self._reqData(EV_ST2EG_CONTRACT_REQ)

    def _reqUnderlayMap(self):
        self._reqData(EV_ST2EG_UNDERLAYMAPPING_REQ)

    # 订阅即时tick、 k线
    def _subQuote(self):
        '''需要根据配置列表'''
        contList = []
        self._contractTuple = self._cfgModel.getContract()
        for cno in self._contractTuple:
            contList.append(cno)
            
        self._reqData(EV_ST2EG_SUB_QUOTE, contList)

    # 请求历史tick、k线数据
    def _reqHisQuote(self):
        #暂时先不修改
        self._hisModel.reqAndSubKLine()
        
    # 查询登录账号
    def _reqLoginInfo(self):
        self._reqData(EV_ST2EG_LOGINNO_REQ)
        
    # 查询资金账号
    def _reqUserInfo(self):
        self._reqData(EV_ST2EG_USERNO_REQ)
        
    def _reqMoney(self):
        self._reqData(EV_ST2EG_MONEY_REQ)

        # self.logger.info("request money 0")
        self.logger.info("request account money!")
        
    # 查询委托数据
    def _reqOrder(self):
        self._reqData(EV_ST2EG_ORDER_REQ)
        
    # 查询成交数据
    def _reqMatch(self):
        self._reqData(EV_ST2EG_MATCH_REQ)
        
    # 查询持仓数据
    def _reqPosition(self):
        self._reqData(EV_ST2EG_POSITION_REQ)

    def _reqUserReday(self):
        self._reqData(EV_ST2EG_USERREADY_REQ)
        
    # ////////////////////////////内部数据应答接口////////////////////
    def _onExchange(self, event):
        '''交易所信息应答'''
        self._qteModel.onExchange(event)

    def _onCommodity(self, event):
        '''品种查询应答'''
        self._qteModel.onCommodity(event)
        #self.logger.debug("1111111:%s" %self._dataModel.getContractUnit('ZCE|S|OI|001|005'))
        self._dataModel.initializeCalc()

    def _onContract(self, event):
        self._qteModel.onContract(event)

    def _onUnderlayMap(self, event):
        self._qteModel.onUnderlayMap(event)
       
    def _onExchangeStateNotice(self, event):
        '''交易所状态'''
        self._qteModel.onExchangeStatus(event)
            
    def _onQuoteRsp(self, event):
        '''行情应答，来着策略引擎'''
        self._qteModel.onQuoteRsp(event)
        
    def _onQuoteNotice(self, event):
        self._qteModel.onQuoteNotice(event)
        self._snapShotTrigger(event)

    def _onDepthNotice(self, event):
        self._qteModel.onDepthNotice(event)

    def _onHisQuoteRsp(self, event):
        '''历史数据请求应答'''
        self._hisModel.onHisQuoteRsp(event)
        
    def _onHisQuoteNotice(self, event):
        self._hisModel.onHisQuoteNotice(event)

    # 报告事件, 发到engine进程中，engine进程 再发到ui进程。
    def _onReport(self, event):
        data = self._dataModel.getCalcCenter().testResult()
        responseEvent = Event({
            "EventCode":EV_EG2UI_REPORT_RESPONSE,
            "StrategyId":self._strategyId,
            "Data":{
                "Result":data,
            }
        })
        self.sendEvent2UI(responseEvent)

    def _onLoadStrategyResponse(self, event):
        '''向界面返回策略加载应答'''
        cfg = self._dataModel.getConfigData()
        key = self._dataModel.getConfigModel().getKLineShowInfoSimple()

        revent = Event({
            "EventCode" : EV_EG2UI_LOADSTRATEGY_RESPONSE,
            "StrategyId": self._strategyId,
            "Data":{
                "StrategyId"   : self._strategyId,
                "StrategyName" : self._strategyName,
                "StrategyState": self._runStatus,
                "ContractNo"   : key[0],
                "KLineType"    : key[1],
                "KLinceSlice"  : key[2],
                "IsActualRun"  : self._dataModel.getConfigModel().isActualRun(),
                "InitialFund"  : self._dataModel.getConfigModel().getInitCapital(),
                "Config"       : cfg,
                "Params"       : self._dataModel.getConfigModel().getParams(),
                "Path"         : self._filePath,
            }
        })
        self.sendEvent2UI(revent)
        
    def _onLoginInfo(self, event):
        self._onTradeLoginQry(event)
        #查询资金账户
        self._reqUserInfo()
     
    def _onUserInfo(self, event):
        self._onTradeUserQry(event)
        #查询所有用户资金信息
        self._reqMoney()
        
    def _onMoneyInfo(self, event):
        self._onTradeMoney(event)
        #查询所有委托信息
        self._reqOrder()
        
    def _onOrderInfo(self, event):
        #self.logger.debug("_onOrderInfo:%s"%event.getData())
        self._onTradeOrderQry(event)
        #委托信息可能会有很多笔，最后一笔查询下一个数据
        if event.isChainEnd():
            self._reqMatch()
        
    def _onMatchInfo(self, event):
        #self.logger.debug("_onMatchInfo:%s"%event.getData())
        self._onTradeMatch(event)
        #委托信息可能会有很多笔，最后一笔查询下一个数据
        if event.isChainEnd():
            self._reqPosition()
        
    def _onPositionInfo(self, event):
        #self.logger.debug("_onPositionInfo:%s"%event.getData())
        self._onTradePosition(event)
        #持仓信息可能会有很多笔，最后一笔设置数据准备完成标志
        if event.isChainEnd():
            self._reqUserReday()

    def _onUserRedayInfo(self, event):
        userList = event.getData()
        for user in userList:
            self._trdModel.setDataReady(user)

    def _onTradeLoginQry(self, apiEvent):
        self._trdModel.updateLoginInfo(apiEvent)

    def _onTradeLoginNotice(self, apiEvent):
        #ret = self._trdModel.updateLoginInfoEg(apiEvent)
        dataList  = apiEvent.getData()
        loginInfo = self._trdModel.getLoginInfo() 
        
        #不用重新查询交易数据，引擎会推送
        for data in dataList:
            #新登录账号
            loginNo = data['LoginNo']
            if loginNo not in loginInfo:
                self._trdModel.addLoginInfo(data)
            #登出，清理登录账号和资金账号
            elif data['IsReady'] == EEQU_NOTREADY:
                self._trdModel.delLoginInfo(data)
                self._trdModel.delUserInfo(loginNo)
            #交易日切换，清理所有资金账号及本地委托数据
            elif self._trdModel.chkTradeDate(data):
                userDict = self._trdModel.getLoginUser(loginNo)
                self.delLocalOrder(userDict)
                self._trdModel.delUserInfo(loginNo)
            else:
                self.logger.warn("Unknown login status: %s"%data)
    
        #self._trdModel.updateLoginInfo(apiEvent)

    def _onTradeUserQry(self, apiEvent):
        self._trdModel.updateUserInfo(apiEvent)
        self._trdModel.updateLoginInfo(apiEvent)

    def _onTradeMatchQry(self, apiEvent):
        self._trdModel.updateMatchData(apiEvent)

    def _onTradePositionQry(self, apiEvent):
        self._trdModel.updatePosData(apiEvent)

        # 数据接收完成，置标志位
        if apiEvent.isChainEnd():
            dataList = apiEvent.getData()
            for data in dataList:
                self._trdModel.setDataReady(data['UserNo'])

    def _onTradeOrderQry(self, apiEvent):
        self._trdModel.updateOrderData(apiEvent)
        
    def _onTradeOrder(self, apiEvent):
        
        self._trdModel.updateOrderData(apiEvent)

        # 更新本地订单信息
        dataList = apiEvent.getData()
        eSessionId = apiEvent.getESessionId()
        for data in dataList:
            self.updateLocalOrder(eSessionId, data)
            
        if self.isRealTimeStatus():
            self._tradeTriggerOrder(apiEvent)
        

    def _onTradeMatch(self, apiEvent):
        '''
        交易成交信息发生变化时，更新交易模型信息
        :param apiEvent: 引擎返回事件
        :return: None
        '''
        self._trdModel.updateMatchData(apiEvent)
        # self._tradeTriggerMatch(apiEvent) # 去掉成交触发

    def _onTradePosition(self, apiEvent):
        '''
        交易持仓信息发生变化时，更新交易模型信息
        :param apiEvent: 引擎返回事件
        :return: None
        '''
        self._trdModel.updatePosData(apiEvent)

    def _onTradeMoney(self, apiEvent):
        '''
        交易资金信息发生变化时，更新交易模型信息
        :param apiEvent: 引擎返回事件
        :return: None
        '''
        self._trdModel.updateMoney(apiEvent)

    def getStrategyId(self):
        return self._strategyId

    def getESessionId(self):
        return self._eSessionId

    def setESessionId(self, eSessionId):
        if eSessionId <= 0:
            return 0
        self._eSessionId = eSessionId

    def getLocalOrder(self):
        return self._localOrder

    def getESessionIdList(self):
        return self._eSessionIdList

    def updateLocalOrder(self, eSesnId, data):
        # 更新本地订单信息
        #self.logger.debug("AAAAA:%s,%s"%(eSesnId, data))
        if eSesnId in self._localOrder:
            tradeRecode = self._localOrder[eSesnId]
            tradeRecode.updateOrderInfo(eSesnId, data)
        else:
            self._localOrder[eSesnId] = TradeRecord(eSesnId, data)
            self._eSessionIdList.append(eSesnId)
            
    def delLocalOrder(self, userDict):
        popSessionList  = []
        
        for k, v in self._localOrder.items():
            if v in userDict:
                popSessionList.append(k)
                    
        for eid in popSessionList:
            self._localOrder.pop(eid)
            

    def updateBarInfoInLocalOrder(self, eSessionId, barInfo):
        if not barInfo:
            return
        if eSessionId not in self._localOrder:
            return
        tradeRecode = self._localOrder[eSessionId]
        tradeRecode._barInfo = barInfo

    def getOrderBuyOrSell(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 'N'
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._direct

    def getOrderEntryOrExit(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 'N'
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._offset
        
    def getOrderFilledLot(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 0
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._matchQty
        
    def getOrderFilledPrice(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 0
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._matchPrice

    def getOrderFilledList(self, eSessionId):
        if eSessionId not in self._localOrder:
            return {}
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._matchPrice

    def getOrderLot(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 0
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._orderQty
        
    def getOrderPrice(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 0
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._orderPrice    
    
    def getOrderStatus(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 'N'
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._orderState

    def getOrderTime(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 0
        tradeRecord = self._localOrder[eSessionId]

        insertTime =  tradeRecord._insertTime
        if not insertTime:
            return 0

        struct_time = time.strptime(insertTime, "%Y-%m-%d %H:%M:%S")
        timeStamp = time.strftime("%Y%m%d.%H%M%S", struct_time)
        return float(timeStamp)        

    def getOrderUpdateTime(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 0
        tradeRecord = self._localOrder[eSessionId]

        updateTime =  tradeRecord._updateTime
        if not updateTime:
            return 0

        struct_time = time.strptime(updateTime, "%Y-%m-%d %H:%M:%S")
        timeStamp = time.strftime("%Y%m%d.%H%M%S", struct_time)
        return float(timeStamp)
        
    def deleteOrder(self, eSessionId):
        orderId = ''
        if isinstance(eSessionId, str) and '-' in eSessionId:
            orderId = self.getOrderId(eSessionId)
            if not orderId:
                return False
        else:
            orderId = eSessionId
            
        return self.deleteOrderByOrderId(orderId)        
        
    def deleteOrderByOrderId(self, orderId):
        aOrder = {
            "OrderId": orderId,
        }
        aOrderEvent = Event({
            "EventCode": EV_ST2EG_ACTUAL_CANCEL_ORDER,
            "StrategyId": self.getStrategyId(),
            "Data": aOrder
        })
        self.sendEvent2Engine(aOrderEvent)
        
        return True
        
    def getContNo(self, eSessionId):
        if eSessionId not in self._localOrder:
            return ''
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._contNo
        
    def getContNoByOrderId(self, orderId):
        for k, v in self._localOrder.items():
            if v._orderId == orderId:
                return v._contNo
        
        return ''

    def getOrderNo(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 0
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._orderNo

    def getOrderId(self, eSessionId):
        if eSessionId not in self._localOrder:
            return 0
        tradeRecord = self._localOrder[eSessionId]
        return tradeRecord._orderId

    def getStrategyName(self):
        return self._strategyName

    def isRealTimeStatus(self):
        return self._runStatus == ST_STATUS_CONTINUES

    def isHisStatus(self):
        return self._runStatus == ST_STATUS_HISTORY

    def getStatus(self):
        return self._runStatus

    def sendEvent2Engine(self, event):
        if self._isSt2EgQueueEffective:
            while True:
                try:
                    self._st2egQueue.put_nowait(event)
                    break
                except queue.Full:
                    time.sleep(0.1)
                    #self.logger.error(f"策略{self._strategyId}向引擎传递事件{event.getEventCode()}时卡住")

    def sendEvent2EngineForce(self, event):
        while True:
            try:
                self._st2egQueue.put_nowait(event)
                break
            except queue.Full:
                time.sleep(0.1)
                #self.logger.error(f"策略{self._strategyId}强制向引擎传递事件{event.getEventCode()}时阻塞")

    def sendEvent2UI(self, event):
        while True:
            try:
                self._st2uiQueue.put_nowait(event)
                break
            except queue.Full:
                time.sleep(0.1)
                #self.logger.error(f"策略{self._strategyId}制向UI传递事件{event.getEventCode()}时阻塞")

    def sendTriggerQueue(self, event):
        self._triggerQueue.put(event)

    def _exit(self, errorCode, errorText):
        # "IsShowFlag"表示策略异常时是否在界面上
        event = Event({
            "EventCode": EV_EG2UI_CHECK_RESULT,
            "StrategyId": self._strategyId,
            "Data": {
                "IsShowFlag": self._isShowForException,
                "ErrorCode": errorCode,
                "ErrorText": errorText,
            }
        })
        # 策略调试信息发送到引擎，由引擎发送到界面
        self.sendEvent2EngineForce(event)

        self._onStrategyQuit(None, ST_STATUS_EXCEPTION)

    # 停止策略
    def _onStrategyQuit(self, event=None, status=ST_STATUS_QUIT):
        try:
            #回调退出函数
            if hasattr(self._userModule, 'exit_callback'):
                self._userModule.exit_callback(self._context)
        except Exception as e:
            self.logger.error('onStrategyStop callback error: %s' % str(e))

        self._isSt2EgQueueEffective = False
        self._strategyState = StrategyStatusExit
        config = None if self._dataModel is None else self._dataModel.getConfigData()
        result = None
        if self._dataModel and self._dataModel.getCalcCenter():
            result = self._dataModel.getCalcCenter().testResult()
        quitEvent = Event({
            "EventCode": EV_EG2UI_STRATEGY_STATUS,
            "StrategyId": self._strategyId,
            "Data":{
                "Status":status,
                "Config":config,
                "Pid":os.getpid(),
                "Path":self._filePath,
                "StrategyName": self._strategyName,
                "Result":result
            }
        })
        self.sendEvent2UI(quitEvent)
        self.sendEvent2EngineForce(quitEvent)
        self.logger.info(f"策略已经将停止完成信号发送到UI和engine,策略{self._strategyId}")
        # 保证该进程is_alive， 使得队列可用
        while True:
            time.sleep(2)

    def _onEquantExit(self, event):
        try:
            #回调退出函数
            if hasattr(self._userModule, 'exit_callback'):
                self._userModule.exit_callback(self._context)
        except Exception as e:
            self.logger.error('onEquantExit callback error: %s' % str(e))

        self._isSt2EgQueueEffective = False
        self._strategyState = StrategyStatusExit
        config = None if self._dataModel is None else self._dataModel.getConfigData()
        responseEvent = Event({
            "EventCode": EV_EG2UI_STRATEGY_STATUS,
            "StrategyId": self._strategyId,
            "Data": {
                "Status": event.getEventCode(),
                "Config": config,
                "Pid": os.getpid(),
                "Path": self._filePath,
                "StrategyName":self._strategyName,
            }
        })
        self.sendEvent2EngineForce(responseEvent)

    def _atHisOver(self):
        try:
            # 历史回测结束回调
            if hasattr(self._userModule, 'hisover_callback'):
                self._userModule.hisover_callback(self._context)
        except Exception as e:
            self.logger.error('atHisOver callback error: %s' % str(e))

    def _switchStrategy(self, event):
        self._dataModel.getHisQuoteModel()._switchKLine()

    def _onSyncPosConf(self, event):
        conf = event.getData()
        self._cfgModel.setAutoSyncPos(conf)

    def _onStrategyRemove(self, event):
        self._isSt2EgQueueEffective = False
        self._strategyState = StrategyStatusExit
        config = None if self._dataModel is None else self._dataModel.getConfigData()
        responseEvent = Event({
            "EventCode": EV_EG2UI_STRATEGY_STATUS,
            "StrategyId": self._strategyId,
            "Data": {
                "Status": ST_STATUS_REMOVE,
                "Config": config,
                "Pid": os.getpid(),
                "Path": self._filePath,
                "StrategyName": self._strategyName,
            }
        })
        self.sendEvent2UI(responseEvent)
        self.sendEvent2EngineForce(responseEvent)
        self.logger.info(f"策略已经将删除完成信号发送到UI和engine,策略{self._strategyId}, {EV_EG2UI_STRATEGY_STATUS}")

        # 保证该进程is_alive， 使得队列可用
        while True:
            time.sleep(2)

    def _snapShotTrigger(self, event):
        # 未选择即时行情触发
        # if not self._dataModel.getConfigModel().hasSnapShotTrigger() or not self.isRealTimeStatus():
        #     return
        #
        # # 该合约不触发
        # if event.getContractNo() not in self._dataModel.getConfigModel().getTriggerContract():
        #     return

        if not self.isRealTimeStatus():
            return

        # 对应字段没有变化不触发
        data = event.getData()
        if len(data)==0 or (not set(data[0]["FieldData"].keys())&set([4, 11, 17, 18, 19, 20])):
            # 4:最新价 11:成交量 17:最优买价 18:买量 19:最优卖价 20:卖量
            return

        dateTimeStamp, tradeDate, lv1Data = self.getTriggerTimeAndData(event.getContractNo())
        event = Event({
            "EventCode" : ST_TRIGGER_SANPSHOT_FILL,
            "ContractNo": event.getContractNo(),
            "KLineType" : None,
            "KLineSlice": None,
            "Data":{
                "Data": lv1Data,
                "DateTimeStamp": dateTimeStamp,
                "TradeDate": tradeDate,
                "IsLastPriceChanged": 4 in data[0]["FieldData"],   # 最新价是否改变
            }
        })
        self.sendTriggerQueue(event)

    def setCurTriggerSourceInfo(self, args):
        self._curTriggerSourceInfo = args

    def getCurTriggerSourceInfo(self):
        return self._curTriggerSourceInfo

    #
    def _tradeTriggerOrder(self, apiEvent):
        if not self._dataModel.getConfigModel().hasTradeTrigger() or len(apiEvent.getData()) == 0:
            return

        if apiEvent.getEventCode() == EEQU_SRVEVENT_TRADE_ORDER and str(apiEvent.getStrategyId()) == str(self._strategyId):
            contractNo = apiEvent.getData()[0]["Cont"]
            dateTimeStamp, tradeDate, lv1Data = self.getTriggerTimeAndData(contractNo)

            tradeTriggerEvent = Event({
                "EventCode":ST_TRIGGER_TRADE_ORDER,
                "ContractNo": contractNo,
                "KLineType" : None,
                "KLineSlice": None,
                "Data":{
                    "Data": apiEvent.getData()[0],
                    "DateTimeStamp": dateTimeStamp,
                    "TradeDate": tradeDate,
                }
            })
            # 交易触发
            self.sendTriggerQueue(tradeTriggerEvent)

    def _tradeTriggerMatch(self, apiEvent):
        if not self._dataModel.getConfigModel().hasTradeTrigger() or len(apiEvent.getData()) == 0:
            return

        if apiEvent.getEventCode() == EEQU_SRVEVENT_TRADE_MATCH and str(apiEvent.getStrategyId()) == str(self._strategyId):
            contractNo = apiEvent.getData()[0]["Cont"]
            dateTimeStamp, tradeDate, lv1Data = self.getTriggerTimeAndData(contractNo)

            tradeTriggerEvent = Event({
                "EventCode":ST_TRIGGER_TRADE_MATCH,
                "ContractNo": contractNo,
                "KLineType" : None,
                "KLineSlice": None,
                "Data":{
                    "Data": apiEvent.getData()[0],
                    "DateTimeStamp": dateTimeStamp,
                    "TradeDate": tradeDate,
                }
            })

            # 交易触发
            self.sendTriggerQueue(tradeTriggerEvent)

    def getTriggerTimeAndData(self, contractNo):
        lv1DataAndUpdateTime = self._dataModel.getQuoteModel().getLv1DataAndUpdateTime(contractNo)
        if lv1DataAndUpdateTime is not None:
            dateTimeStamp = lv1DataAndUpdateTime["UpdateTime"]
            tradeDate = dateTimeStamp // 1000000000
            lv1Data = lv1DataAndUpdateTime["Lv1Data"]
        else:
            dateTimeStamp = None
            tradeDate = None
            lv1Data = None

        return dateTimeStamp, tradeDate, lv1Data

    def _sendConfig2Engine(self):
        event = Event({
            "EventCode": ST_ST2EG_SYNC_CONFIG,
            "StrategyId": self._strategyId,
            "ContractNo": None,
            "KLineType": None,
            "KLineSlice": None,
            "Data": {
                "UIConfig": self._uiConfig,
                "Config": self._dataModel.getConfigModel().getConfig(),
                "Path": self._filePath,
                "StrategyName": self._strategyName,
                "StrategyId": self._strategyId,
            }
        })
        self.sendEvent2Engine(event)
