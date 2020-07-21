#-*-:conding:utf-8-*-

from multiprocessing import Process, Queue
import multiprocessing
from threading import Thread
from .strategy import StrategyManager
from capi.py2c import PyAPI
from capi.event import *
from capi.com_types import *
import time, queue
from .engine_model import DataModel
import copy
import psutil
import os, json
from collections import OrderedDict
import traceback
from .engine_order_model import EngineOrderModel, EnginePosModel
from .strategy_cfg_model_new import StrategyConfig_new as StrategyConfig
from datetime import datetime


class StrategyEngine(object):
    '''策略引擎'''
    def __init__(self, logger, eg2uiQueue, ui2egQueue):
        self.logger = logger
        
        # Engine->Ui, 包括资金，权益等
        self._eg2uiQueue = eg2uiQueue
        # Ui->Engine, 包括策略加载等
        self._ui2egQueue = ui2egQueue
        self._commdityFilter = []
        
    def _initialize(self):
        '''进程中初始化函数'''
        self.logger.info('Initialize strategy engine!')

        # _commodityFilter的位置有可能会影响交易所状态更新
        self._commdityFilter = [
            'SPD', 'DCE', 'SHFE', 'CFFEX', 'INE', 'LME',
            'ZCE|F', 'ZCE|O', 'ZCE|M', 'ZCE|S', 'ZCE|Z',
            'CBOT|F|YM', 'CBOT|F|S', 'CBOT|F|ZM', 'CBOT|F|C',
            'CBOT|Z|YM', 'CBOT|Z|S', 'CBOT|Z|ZM', 'CBOT|Z|C',
            'CME|F|ES', 'CME|F|NQ', 'COMEX|F|HG', 'COMEX|F|GC', 'COMEX|F|SI',
            'CME|Z|ES', 'CME|Z|NQ', 'COMEX|Z|HG', 'COMEX|Z|GC', 'COMEX|Z|SI',
            'NYMEX|F|CL', 'ICUS|F|SB', 'ICUS|F|CT',
            'NYMEX|Z|CL', 'ICUS|Z|SB', 'ICUS|Z|CT',
            'NYMEX|O|CL', 'COMEX|O|GC',
            'ICEU|F|B', 'ICEU|F|Z', 'SGX|F|CN',
            'ICEU|Z|B', 'ICEU|Z|Z', 'SGX|Z|CN',
            'HKEX|F|HSI', 'HKEX|F|MHI', 'HKEX|F|HHI', 'HKEX|F|ICUS', 'HKEX|F|MCH',
            'HKEX|Z|HSI', 'HKEX|Z|MHI', 'HKEX|Z|HHI', 'HKEX|Z|ICUS', 'HKEX|Z|MCH',
            'SGE',
        ]
        
        # 数据模型
        self._dataModel = DataModel(self.logger)
        self._qteModel = self._dataModel.getQuoteModel()
        self._trdModel = self._dataModel.getTradeModel()
        
        # api回调函数
        self._regApiCallback()
        # 策略发送函数
        self._regMainWorkFunc()
        
        # Api->Engine, 品种、行情、K线、交易等
        self._api2egQueue = Queue()
        # Strategy->Engine, 初始化、行情、K线、交易等
        self._st2egQueue = Queue()

        # 创建_pyApi对象
        self._pyApi = PyAPI(self.logger, self._api2egQueue) 
        
        # 策略编号，自增
        self._maxStrategyId = 1
        # 创建策略管理器
        self._strategyMgr = StrategyManager(self.logger, self._st2egQueue)
        
        # 策略进程队列列表
        self._eg2stQueueDict = {} #{strategy_id, queue}
        self._isEffective = {}
        self._isSt2EngineDataEffective= {} 
        self._isStActualRun = {}             # 实盘运行
        self._stRunStatus = {}               # 运行状态
        
        # 持仓同步参数
        self._isAutoSyncPos = False
        self._isOneKeySyncPos = False
        self._autoSyncPosConf = {
            'OneKeySync': self._isOneKeySyncPos,     # 一键同步
            'AutoSyncPos': self._isAutoSyncPos,      # 是否自动同步
            'PriceType': 0,                          # 价格类型 0:对盘价, 1:最新价, 2:市价
            'PriceTick': 0,                          # 超价点数
            'OnlyDec': False,                        # 是否只做减仓同步
            'SyncTick': 500,                         # 同步间隔，毫秒
        }
        self._eSessionId = 0
        
        # 查询sessionId和账号对应关系
        self._SessionUserMap = {}

        # 策略在UI显示情况
        self._isShowInUIDict = {}
        
        # 策略虚拟持仓
        self._strategyPosDict = {}
        
        # 即时行情订阅列表
        self._quoteOberverDict = {} #{'contractNo' : [strategyId1, strategyId2...]}
        # 历史K线订阅列表
        self._hisKLineOberverDict = {} #{'contractNo' : [strategyId1, strategyId2...]}
        
        self._lastMoneyTime = 0      #资金查询时间
        self._lastPosTime   = datetime.now()      #持仓同步差异计算时间
        self._lastDoPosDiffTime = datetime.now()  #处理持仓差异时间
        
        #恢复策略
        self._resumeStrategy()

        # 创建主处理线程, 从api和策略进程收数据处理
        self._startMainThread()
        
        # 启动1秒定时器
        self._start1secondsTimer()
        
        self.logger.debug('Initialize strategy engine ok!')

    def _resumeStrategy(self):
        if not os.path.exists('config/StrategyContext.json'):
            return
        with open("config/StrategyContext.json", 'r', encoding="utf-8") as resumeFile:
            try:
                strategyContext = json.load(resumeFile)
            except:
                self.logger.warn("Resume strategy failed!!!")
                return

            for k,v in strategyContext.items():
                if k == "MaxStrategyId":
                    self._maxStrategyId = int(v)
                    self.logger.debug("恢复策略最大Id成功")
                elif k == "StrategyConfig":
                    self.resumeAllStrategyConfig(v)
                    self.logger.debug("恢复策略配置成功")
                else:
                    pass

    def resumeAllStrategyConfig(self, strategyConfig):
        # self.logger.info(strategyConfig)
        copyConfig = {}
        for k, v in strategyConfig.items():
            copyConfig[int(k)] = None
            
        sortedList = sorted(copyConfig)
        # self.logger.info(sortedList)
        for strategyId in sortedList:
            strategyIni = strategyConfig[str(strategyId)]
            config = StrategyConfig(strategyIni["Config"])
            key = config.getKLineShowInfoSimple()

            fakeEvent = Event({
                "EventCode": EV_EG2UI_LOADSTRATEGY_RESPONSE,
                "StrategyId": strategyId,
                "ErrorCode": 0,
                "ErrorText": "",
                "Data": {
                    "StrategyId": strategyId,
                    "StrategyName": strategyIni["StrategyName"],
                    "StrategyState": ST_STATUS_QUIT,
                    "ContractNo": key[0],
                    "KLineType": key[1],
                    "KLinceSlice": key[2],
                    "IsActualRun": config.isActualRun(),
                    "InitialFund": config.getInitCapital(),
                    "Config": strategyIni["Config"],
                    "Path": strategyIni["Path"],
                    "Params":config.getParams(),
                }
            })
            self.sendEvent2UI(fakeEvent)
            self._strategyMgr.insertResumedStrategy(strategyId, fakeEvent.getData())
            self._isShowInUIDict[strategyId] = True

    def _regApiCallback(self):
        self._apiCallbackDict = {
            EEQU_SRVEVENT_CONNECT           : self._onApiConnect               ,
            EEQU_SRVEVENT_DISCONNECT        : self._onApiDisconnect            ,
            EEQU_SRVEVENT_EXCHANGE          : self._onApiExchange              ,
            EEQU_SRVEVENT_COMMODITY         : self._onApiCommodity             ,
            EEQU_SRVEVENT_UNDERLAYMAPPING   : self._onApiUnderlayMapping       ,
            EEQU_SRVEVENT_CONTRACT          : self._onApiContract              ,
            EEQU_SRVEVENT_TIMEBUCKET        : self._onApiTimeBucket            ,
            EEQU_SRVEVENT_QUOTESNAP         : self._onApiSnapshot              ,
            EEQU_SRVEVENT_QUOTESNAPLV2      : self._onApiDepthQuote            ,
            EEQU_SRVEVENT_HISQUOTEDATA      : self._onApiKlinedataRsp          ,
            EEQU_SRVEVENT_HISQUOTENOTICE    : self._onApiKlinedataNotice       ,
            EEQU_SRVEVENT_TRADE_LOGINQRY    : self._onApiLoginInfoRsp          ,
            EEQU_SRVEVENT_TRADE_USERQRY     : self._onApiUserInfo              ,
            EEQU_SRVEVENT_TRADE_LOGINNOTICE : self._onApiLoginInfoNotice       ,
            EEQU_SRVEVENT_TRADE_ORDERQRY    : self._onApiOrderDataQry          ,
            EEQU_SRVEVENT_TRADE_ORDER       : self._onApiOrderDataNotice       ,
            EEQU_SRVEVENT_TRADE_MATCHQRY    : self._onApiMatchDataQry          ,
            EEQU_SRVEVENT_TRADE_MATCH       : self._onApiMatchData             ,
            EEQU_SRVEVENT_TRADE_POSITQRY    : self._onApiPosDataQry            ,
            EEQU_SRVEVENT_TRADE_POSITION    : self._onApiPosData               ,
            EEQU_SRVEVENT_TRADE_FUNDQRY     : self._onApiMoney                 ,
            EEQU_SRVEVENT_TRADE_EXCSTATEQRY : self._onApiExchangeStateQry      ,
            EEQU_SRVEVENT_TRADE_EXCSTATE    : self._onExchangeStateNotice      ,
        }
        
    def _regMainWorkFunc(self):
        self._mainWorkFuncDict = {
            EV_ST2EG_EXCHANGE_REQ           : self._reqExchange                ,
            EV_ST2EG_COMMODITY_REQ          : self._reqCommodity               ,
            EV_ST2EG_CONTRACT_REQ           : self._reqContract                ,
            EV_ST2EG_UNDERLAYMAPPING_REQ    : self._reqUnderlayMap             ,
            EV_ST2EG_SUB_QUOTE              : self._reqSubQuote                ,
            EV_ST2EG_UNSUB_QUOTE            : self._reqUnsubQuote              ,
            EV_ST2EG_SUB_HISQUOTE           : self._reqSubHisquote             ,
            EV_ST2EG_UNSUB_HISQUOTE         : self._reqUnsubHisquote           ,
            EV_ST2EG_SWITCH_STRATEGY        : self._reqKLineStrategySwitch     ,
            #
            EV_ST2EG_NOTICE_KLINEDATA       : self._sendKLineData              ,
            EV_ST2EG_UPDATE_KLINEDATA       : self._sendKLineData              ,

            # k line series
            EV_ST2EG_ADD_KLINESERIES        : self._addSeries                  ,
            EV_ST2EG_NOTICE_KLINESERIES     : self._sendKLineSeries            ,
            EV_ST2EG_UPDATE_KLINESERIES     : self._sendKLineSeries            ,

            # k line signal
            EV_ST2EG_ADD_KLINESIGNAL        : self._addSignal                  ,
            EV_ST2EG_NOTICE_KLINESIGNAL     : self._sendKLineSignal            ,
            EV_ST2EG_UPDATE_KLINESIGNAL     : self._sendKLineSignal            ,
            
            ST_ST2EG_SYNC_CONFIG            : self._syncStrategyConfig         ,

            EV_ST2EG_LOGINNO_REQ            : self._onLoginInfoReq             , 
            EV_ST2EG_USERNO_REQ             : self._onUserInfoReq              ,
            EV_ST2EG_MONEY_REQ              : self._onMoneyReq                 ,
            EV_ST2EG_ORDER_REQ              : self._onOrderReq                 ,
            EV_ST2EG_MATCH_REQ              : self._onMatchReq                 ,
            EV_ST2EG_POSITION_REQ           : self._onPositionReq              ,
            EV_ST2EG_POSITION_NOTICE        : self._onPositionNotice           ,      
            
            EV_ST2EG_ACTUAL_ORDER           : self._sendOrder                  ,
            EV_ST2EG_ACTUAL_CANCEL_ORDER    : self._deleteOrder                ,
            EV_ST2EG_ACTUAL_MODIFY_ORDER    : self._modifyOrder                ,
            
            EV_ST2EG_UPDATE_STRATEGYDATA    : self._reqStrategyDataUpdateNotice,

            # 暂停、恢复、与退出
            EV_UI2EG_STRATEGY_QUIT          : self._onStrategyQuit             ,
            EV_UI2EG_STRATEGY_RESUME        : self._onStrategyResume           ,
            EV_UI2EG_EQUANT_EXIT            : self._onEquantExit               ,
            EV_UI2EG_STRATEGY_FIGURE        : self._switchStrategy             ,
            EV_UI2EG_STRATEGY_RESTART       : self._restartStrategyWhenParamsChanged,

            EV_EG2UI_REPORT_RESPONSE        : self._reportResponse             ,
            EV_EG2UI_CHECK_RESULT           : self._checkResponse              ,
            EV_EG2ST_MONITOR_INFO           : self._monitorResponse            ,

            # load strategy
            EV_EG2UI_LOADSTRATEGY_RESPONSE  : self._loadStrategyResponse       ,
            EV_EG2UI_STRATEGY_STATUS        : self._onStrategyStatus           ,
        }
            
    def run(self):
        # 在当前进程中初始化
        self._initialize()

        while True:
            try:
                self._handleUIData()

                ppid = os.getppid()
                if ppid == 1 or not psutil.pid_exists(ppid):
                    self.saveStrategyContext2File()
                    os._exit(0)

            except Exception as e:
                errorText = traceback.format_exc()
                self.sendErrorMsg(-1, errorText)

    def _sendEvent2Strategy(self, strategyId, event):
        if strategyId not in self._eg2stQueueDict or strategyId not in self._isEffective or not self._isEffective[strategyId]:
            return
        if event is None:
            return
        eg2stQueue = self._eg2stQueueDict[strategyId]
        while True:
            try:
                eg2stQueue.put_nowait(event)
                break
            except queue.Full:
                time.sleep(0.1)
                self.logger.warn(f"engine向策略发事件时阻塞，策略id:{strategyId}, 事件号: {event.getEventCode()}")

    def _sendEvent2StrategyForce(self, strategyId, event):
        eg2stQueue = self._eg2stQueueDict[strategyId]
        while True:
            try:
                eg2stQueue.put_nowait(event)
                break
            except queue.Full:
                time.sleep(0.1)
                self.logger.warn(f"engine向策略发事件时阻塞，策略id:{strategyId}, 事件号: {event.getEventCode()}")

    def _sendEvent2AllStrategy(self, event):
        # eg2stQueueDict = copy.deepcopy(self._eg2stQueueDict)
        # for strategyId in eg2stQueueDict:
        for strategyId in self._eg2stQueueDict:
            eventCopy = copy.deepcopy(event)
            eventCopy.setStrategyId(strategyId)
            self._sendEvent2Strategy(strategyId, eventCopy)

    def _dispathQuote2Strategy(self, code, apiEvent):
        '''分发即时行情'''
        contractNo = apiEvent.getContractNo()
        contStList = self._quoteOberverDict[contractNo]
        apiEvent.setEventCode(code)

        for id in contStList:
            self._sendEvent2Strategy(id, apiEvent)
            
    # //////////////////////UI事件处理函数/////////////////////
    def _handleUIData(self):
        try:
            event = self._ui2egQueue.get(timeout=0.5)
            code = event.getEventCode()

            if code == EV_UI2EG_LOADSTRATEGY:
                # 加载策略事件
                self._loadStrategy(event)
            elif code == EV_UI2EG_REPORT:
                self._noticeStrategyReport(event)
            elif code == EV_UI2EG_STRATEGY_QUIT:
                self._onStrategyQuit(event)
            elif code == EV_UI2EG_STRATEGY_RESUME:
                self._onStrategyResume(event)
            elif code == EV_UI2EG_EQUANT_EXIT:
                self._onEquantExit(event)
            elif code == EV_UI2EG_STRATEGY_REMOVE:
                self.logger.info(f"收到策略删除信号，策略id:{event.getStrategyId()}")
                self._onStrategyRemove(event)
            elif code == EV_UI2EG_STRATEGY_FIGURE:
                self._switchStrategy(event)
            elif code == EV_UI2EG_STRATEGY_RESTART:
                self._restartStrategyWhenParamsChanged(event)
            elif code == EV_UI2EG_SYNCPOS_CONF:
                self._onSyncPosConf(event)
        except queue.Empty:
            return

    #
    def _noticeStrategyReport(self, event):
        self._sendEvent2Strategy(event.getStrategyId(), event)

    def _getStrategyId(self):
        id = self._maxStrategyId
        self._maxStrategyId += 1
        return id

    def _loadStrategy(self, event, strategyId = None):
        # 加载策略前先更新策略最大Id
        self._updateMaxStrategyId()
        id = self._getStrategyId() if strategyId is None else strategyId
        eg2stQueue = Queue(20000)
        self._eg2stQueueDict[id] = eg2stQueue
        self._strategyMgr.create(id, eg2stQueue, self._eg2uiQueue, self._st2egQueue, event)
        # broken pip error 修复
        self._isEffective[id] = True
        self._isSt2EngineDataEffective[id] = True
        # 策略创建成功后在界面上显示的标志位设为True
        self._isShowInUIDict[id] = True

        # =================
        self._sendEvent2Strategy(id, event)

    def _updateMaxStrategyId(self):
        ids = [k for k, v in self._isShowInUIDict.items() if v]

        self._maxStrategyId = max(ids) + 1 if ids else 1


    def _loadStrategyResponse(self, event):
        self.sendEvent2UI(event)

    def _onStrategyStatus(self, event):
        stat = event.getData()["Status"]
        if stat == ST_STATUS_QUIT:
            self._onStrategyQuitCom(event)
        elif stat == EV_UI2EG_EQUANT_EXIT:
            self._singleStrategyExitComEquantExit(event)
        elif stat == ST_STATUS_CONTINUES:
            self.sendEvent2UI(event)
        elif stat == ST_STATUS_REMOVE:
            self._onStrategyRemoveCom(event)
            self.logger.info(f"策略删除完成，策略id:{event.getStrategyId()}")
        elif stat == ST_STATUS_EXCEPTION:
            self._onStrategyExceptionCom(event)
            
        self._stRunStatus[event.getStrategyId()] = stat

    def _onStrategyExceptionCom(self, event):
        self.sendEvent2UI(event)
        self._cleanStrategyInfo(event.getStrategyId())
        self._strategyMgr.handleStrategyException(event)
        
    def _onSyncPosConf(self, event):
        conf = event.getData()
        self._isAutoSyncPos = conf['AutoSyncPos']
        self._isOneKeySyncPos = conf['OneKeySync']
        self._autoSyncPosConf = conf
        if conf['SyncTick'] <= 500:
            self._autoSyncPosConf['SyncTick'] = 500
            
        for id in self._isStActualRun:
            self._sendEvent2Strategy(id, event)

    # ////////////////api回调及策略请求事件处理//////////////////
    def _apiThreadFunc(self):
        while True:
            try:
                apiEvent = self._api2egQueue.get(timeout=0.1)
                code = apiEvent.getEventCode()
                if code not in self._apiCallbackDict:
                    return

                # 处理api event及异常
                try:
                    self._apiCallbackDict[code](apiEvent)
                except Exception as e:
                    traceback.print_exc()
                    self.logger.error("处理 c api 发来的数据出现错误, event code = {}".format(code))
                    errorText = traceback.format_exc()
                    errorText = errorText + "When handle C API in engine, EventCode: {}".format(code)
                    self.sendErrorMsg(-1, errorText)
            except queue.Empty:
                pass

    def _stThreadFunc(self):
        while True:
            try:
                event = self._st2egQueue.get(timeout=0.1)
                code = event.getEventCode()
                if code not in self._mainWorkFuncDict:
                    self.logger.debug('Event %d not register in _mainWorkFuncDict'%code)
                    return

                # 处理策略 event及异常
                try:
                    strategyId = event.getStrategyId()
                    if strategyId in self._isSt2EngineDataEffective and not self._isSt2EngineDataEffective[strategyId]:
                        return
                    self._mainWorkFuncDict[code](event)
                except Exception as e:
                    # traceback.print_exc()
                    errorText = traceback.format_exc()
                    errorText = errorText + f"When handle strategy:{strategyId} in engine, EventCode: {code}. stop stratey {strategyId}!"
                    self._handleEngineExceptionCausedByStrategy(strategyId)
                    self.sendErrorMsg(-1, errorText)
            except queue.Empty:
                pass
            
    def _startMainThread(self):
        '''从api队列及策略队列中接收数据'''
        self._apiThreadH = Thread(target=self._apiThreadFunc)
        self._apiThreadH.start()

        self._stThreadH = Thread(target=self._stThreadFunc)
        self._stThreadH.start()
        
    def _1SecondsThreadFunc(self):
        while True:
            # TODO: 去掉主动去查资金方式，改为由9.5推送资金信息
            # self._queryMoney()
            self._syncPosition()                
            time.sleep(0.1)
                
    def _start1secondsTimer(self):
        '''资金查询线程'''
        self._1SecondsThreadH = Thread(target=self._1SecondsThreadFunc)
        self._1SecondsThreadH.start()
        
    def _queryMoney(self):
        userDict = self._trdModel.getUserInfo()
        if len(userDict) <= 0:
            return

        # 查询所有账户下的资金, 30秒一次
        nowTime = datetime.now()
        if self._lastMoneyTime == 0 or (nowTime - self._lastMoneyTime).total_seconds() >= 1:
            self._reqUserMoney()
            self._lastMoneyTime = nowTime

    def _updateStrategyName(self, strategyPos):
        newPositions = {}
        for key, value in strategyPos.items():
            newKey = self._strategyMgr.getStrategyName(key)
            newPositions["[" + str(key) + "] " + newKey] = value
        return newPositions

    def _calPosDiff(self, positions):
        '''计算账户仓和策略仓差异'''
        strategyPos = {}
        accountPos  = {}
        strategyAccount = set()
        # 重组策略仓
        for sid in positions["Strategy"]:
            for user in positions["Strategy"][sid]:
                strategyAccount.add(user)

                if user not in strategyPos:
                    strategyPos.update(
                        {
                            #TODO：结构和下面的不一致
                            user: positions["Strategy"][sid][user]
                        }
                    )
                else:
                    for pCont, pInfo in positions["Strategy"][sid][user].items():
                        if pCont not in strategyPos[user]:
                            strategyPos[user].update(
                                {
                                    pCont: pInfo
                                }
                            )
                        else:
                            strategyPos[user][pCont]["TotalBuy"] += pInfo["TotalBuy"]
                            strategyPos[user][pCont]["TotalSell"] += pInfo["TotalSell"]
                            strategyPos[user][pCont]["TodayBuy"] += pInfo["TodayBuy"]
                            strategyPos[user][pCont]["TodaySell"] += pInfo["TodaySell"]
        #print("sssssss: ", strategyPos)

        # 重组账户仓
        for user in positions["Account"]:
            if user not in strategyAccount:
                continue

            if user not in accountPos:
                accountPos[user] = {}

            for pCont, pInfo in positions["Account"][user].items():
                if pCont[-1] == "T":    # 只关注账户中的投机单的持仓
                    if pCont[:-2] not in accountPos[user]:
                        if pCont[-2] == "S":
                            accountPos[user][pCont[:-2]] = {
                                "TotalSell": pInfo["PositionQty"],
                                "TodaySell": pInfo["PositionQty"] - pInfo["PrePositionQty"],
                                "TotalBuy" : 0,
                                "TodayBuy" : 0
                            }
                        else:
                            accountPos[user][pCont[:-2]] = {
                                "TotalBuy" : pInfo["PositionQty"],
                                "TodayBuy" : pInfo["PositionQty"] - pInfo["PrePositionQty"],
                                "TotalSell": 0,
                                "TodaySell": 0
                            }

                    else:
                        if pCont[-2] == "S":
                            accountPos[user][pCont[:-2]]["TotalSell"] += pInfo["PositionQty"]
                            accountPos[user][pCont[:-2]]["TodaySell"] += pInfo["PositionQty"] - pInfo["PrePositionQty"]

                        else:
                            accountPos[user][pCont[:-2]]["TotalBuy"] += pInfo["PositionQty"]
                            accountPos[user][pCont[:-2]]["TodayBuy"] += pInfo["PositionQty"] - pInfo["PrePositionQty"]

        #print("tttttttttt: ", accountPos)

        rlt = []

        for user in strategyAccount:
            for c, p in strategyPos[user].items():

                if user in accountPos:
                    if c in accountPos[user]:
                        aTPos = accountPos[user][c]["TotalBuy"] - (-accountPos[user][c]["TotalSell"]) # 账户仓
                        sTPos = p["TotalBuy"] - (-p["TotalSell"])   # 策略仓
                        posDif = sTPos - aTPos                      # 仓差
                        rlt.append([user, c, aTPos, sTPos, posDif,
                                    p["TotalBuy"], p["TotalSell"], p["TodayBuy"], p["TodaySell"],
                                    accountPos[user][c]["TotalBuy"], accountPos[user][c]["TotalSell"],
                                    accountPos[user][c]["TodayBuy"], accountPos[user][c]["TodaySell"]])
                        continue

                rlt.append([user, c, 0, p["TotalBuy"] - (-p["TotalSell"]), p["TotalBuy"] - (-p["TotalSell"]),
                            p["TotalBuy"], p["TotalSell"], p["TodayBuy"], p["TodaySell"], 0, 0, 0, 0])
                            
        return rlt
        
    def _timeDiffMs(self, beg, end):
        diff = end - beg
        ret = diff.seconds*1000000 + diff.microseconds
        
        return ret/1000
        
    def _syncPosition(self):
        # 未登录，不同步持仓
        userDict = self._trdModel.getUserInfo()
        if len(userDict) <= 0:
            return

        nowTime = datetime.now()            
        if self._isOneKeySyncPos or self._timeDiffMs(self._lastPosTime, nowTime) >= 400:
            self._lastPosTime = nowTime
            
            accPos = {}
            #查询所有账户持仓情况
            for k,v in userDict.items():
                accPos[k] = v.getContPos()
            
            #获取所有策略的虚拟持仓
            strategyPos = {}
            for id in self._strategyPosDict:
                if not self._isEffective[id]:
                    continue
                    
                if not self._isSt2EngineDataEffective[id]:
                    continue
                
                if not self._isStActualRun[id]:
                    continue
                    
                if self._stRunStatus[id] != ST_STATUS_CONTINUES:
                    continue

                strategyPos[id] = copy.deepcopy(self._strategyPosDict[id])
            
            posInfo = {
                    "Account"  : accPos,
                    "Strategy" : copy.deepcopy(strategyPos),
                }
            
            posDiff = self._calPosDiff(posInfo)
            eventData = copy.deepcopy(posDiff)
            eventData.append(self._updateStrategyName(strategyPos))

            event = Event({
                "EventCode"   : EV_EG2UI_POSITION_NOTICE,
                "Data"        : eventData,
            })
            
            #self.logger.debug("Sync position to ui:%s"%event.getData())
            self._send2uiQueue(event)
            
            if self._isOneKeySyncPos or self._isAutoSyncPos:
                if self._isOneKeySyncPos or self._timeDiffMs(self._lastDoPosDiffTime, nowTime)>= self._autoSyncPosConf['SyncTick']:
                    self._doPosDiff(posDiff)
                    self._lastDoPosDiffTime = nowTime
                    self._isOneKeySyncPos = False
            
            
    def _doPosDiff(self, posDiff):
        for pos in posDiff:
            contNo = pos[1]
            
            contDict = self._qteModel.getContractDict()
            if contNo not in contDict:
                continue
                
            exchgNo = contDict[contNo].getContract()['ExchangeNo']
            commNo = contDict[contNo].getContract()['CommodityNo']
            commNo = commNo.split('|')[-1]
            exchgDict = self._qteModel.getExchangeDict()
            if exchgNo not in exchgDict:
                continue
            else:
                # 判断是否在交易时段
                #self.logger.debug("CommStat:%s, commNo:%s" %(exchgDict[exchgNo].getExchange(), commNo))
                commStat = exchgDict[exchgNo].getCommodityStatus(commNo)
                exchgStat = exchgDict[exchgNo].getExchangeStatus()
                if commStat and commStat != '3':
                    continue
                else:
                    #self.logger.debug("111commNo Ok:%s" %commStat)
                    pass
                
                if exchgStat != '3':
                    continue
                else:
                    #self.logger.debug("222exchage Ok:%s" %exchgStat)
                    pass
            
            stBuyPos = pos[5]
            stSellPos = pos[6]
            acBuyPos = pos[-4]
            acSellPos = pos[-3]
            
            stTdBuyPos = pos[7]
            stTdSellPos = pos[8]
            acTdBuyPos = pos[-2]
            acTdSellPos = pos[-1]
            
            # 内盘可以双向持仓
            if exchgNo in ('ZCE', 'DCE', 'SHFE', 'INE', 'CFFEX'):
                buyDiff = stBuyPos - acBuyPos
                sellDiff = stSellPos - acSellPos
                
                buyTdDiff = stTdBuyPos - acTdBuyPos
                sellTdDiff = stTdSellPos - acTdSellPos
                
                buyYsDiff = buyDiff - buyTdDiff
                sellYsDiff = sellDiff - sellTdDiff
            
                # 处理买仓, 账户仓少开多平
                if buyDiff > 0:
                    if not self._autoSyncPosConf['OnlyDec']:
                        self._sendSyncPosOrder(pos, buyDiff, dBuy, oOpen)
                elif buyDiff < 0:
                    # 上期区分平今平昨
                    if exchgNo in ('SHFE', 'INE'):
                        # 账户昨仓多, 平昨
                        if buyYsDiff < 0:
                            self._sendSyncPosOrder(pos, -buyYsDiff, dSell, oCover)
                        # 账户今仓多, 平今
                        if buyTdDiff < 0:
                            self._sendSyncPosOrder(pos, -buyTdDiff, dSell, oCoverT)
                    else:
                        self._sendSyncPosOrder(pos, -buyDiff, dSell, oCover)
                
                # 处理卖仓, 账户仓少开多平
                if sellDiff > 0:
                    if not self._autoSyncPosConf['OnlyDec']:
                        self._sendSyncPosOrder(pos, sellDiff, dSell, oOpen)
                elif sellDiff < 0:
                    if exchgNo in ('SHFE', 'INE'):
                        # 账户昨仓多, 平昨
                        if sellYsDiff < 0:
                            self._sendSyncPosOrder(pos, -sellYsDiff, dBuy, oCover)
                        # 账户今仓多, 平今
                        if sellTdDiff < 0:
                            self._sendSyncPosOrder(pos, -sellTdDiff, dBuy, oCoverT)
                    else:
                        self._sendSyncPosOrder(pos, -sellDiff, dBuy, oCover)
                        
            # 外盘不存在双向持仓      
            else:
                stPos = stBuyPos - stSellPos
                acPos = acBuyPos - acSellPos
                totalDiff = stPos - acPos
                
                if totalDiff < 0:
                    self._sendSyncPosOrder(pos, -totalDiff, dSell, oOpen)
                elif totalDiff > 0:
                    self._sendSyncPosOrder(pos, totalDiff, dBuy, oOpen)

            
    def _sendSyncPosOrder(self, pos, orderQty, orderDirct, entryOrExit):
        userNo = pos[0]
        contNo = pos[1]
        
        orderType = otLimit
        orderPrice = 0
        # 如果市价同步
        if self._autoSyncPosConf["PriceType"] == 2:
            orderType = otMarket
        else:    
            orderPrice = self._getSyncPosPrice(contNo, orderDirct)
        
            if orderPrice == 0:
                self.logger.warn("Sync Position Price can not get!")
                return
        
        aOrder = {
            'UserNo': userNo,
            'Sign': self._trdModel.getSign(userNo),
            'Cont': contNo,
            'OrderType': orderType,
            'ValidType': '0',
            'ValidTime': '0',
            'Direct': orderDirct,
            'Offset': entryOrExit,
            'Hedge': 'T',
            'OrderPrice': orderPrice,
            'TriggerPrice': 0,
            'TriggerMode': 'N',
            'TriggerCondition': 'N',
            'OrderQty': orderQty,
            'StrategyType': 'N',
            'Remark': '',
            'AddOneIsValid': tsDay,
        }
        
        stId = 0
        eId = str(stId) + '-' + str(self._getESessionId())
        aOrderEvent = Event({
            "EventCode": EV_ST2EG_ACTUAL_ORDER,
            "StrategyId": stId,
            "Data": aOrder,
            "ESessionId": eId,
        })
        
        #self.logger.debug("SendSyncOrder:%s" %aOrderEvent)
        self._st2egQueue.put_nowait(aOrderEvent)
    
    def _getESessionId(self):
        self._eSessionId += 1
        return self._eSessionId
    
    def _getSyncPosPrice(self, contNo, orderDirct):
        syncPrice = 0
        priceType = self._autoSyncPosConf['PriceType']
        nTicks = self._autoSyncPosConf['PriceTick']
        
        # 市价
        if priceType == 2:
            return 0
            
        contDict = self._qteModel.getContractDict()
        if contNo not in contDict:
                return 0
        # 对价
        if priceType == 0:
            if orderDirct == dBuy:
                syncPrice = contDict[contNo].getLv1Data(19, 0)
            else:
                syncPrice = contDict[contNo].getLv1Data(17, 0)
                
        # 最新价
        if priceType == 1:
            syncPrice = contDict[contNo].getLv1Data(4, 0)
            
        if syncPrice == 0:
            return 0
        
        # 获取priceTick
        commNo = contDict[contNo].getContract()['CommodityNo']
        commDict = self._qteModel.getCommodityDict()
        if commNo not in commDict:
            self.logger.warn("Sync Position not found commodity!")
            return 0
            
        priceTick = commDict[commNo].getCommodity()['PriceTick']
        
        # 考虑超价点数
        if orderDirct == dBuy:
            syncPrice += nTicks*priceTick
        else:
            syncPrice -= nTicks*priceTick
            
        return syncPrice
        
    def _send2uiQueue(self, event):
        # self.logger.info("[ENGINE] Send event(%d,%d) to UI!"%(event.getEventCode(), event.getStrategyId()))
        self.sendEvent2UI(event)

    #////////////////api回调事件//////////////////////////////
    def _onApiConnect(self, apiEvent):
        self._pyApi.reqSpreadContractMapping()
        self._pyApi.reqExchange(Event({'StrategyId':0, 'Data':''}))
        self._send2uiQueue(apiEvent)

    def _onApiDisconnect(self, apiEvent):
        self._send2uiQueue(apiEvent)
        '''
        断连事件：区分与9.5/交易/即时行情/历史行情
            1. 与9.5断连：
                a. 停止所有策略(包括回测与运行)
                b. 通知界面断连状态
                c. 设置引擎状态为与9.5断连
                d. 清理所有数据，重置数据状态
            2. 与即时行情断连
                a. 停止所有策略(运行)
                b  通知界面断连状态
                c. 设置引擎状态为与即时行情断连
                d. 清理所有即时行情数据
                
            3. 与历史行情断连
                a. 停止所有策略（包括回测和运行）
                b. 通知界面断连状态
                c. 设置引擎状态为与历史行情断连
                d. 清理所有历史K线数据
                
            4. 与交易断连
                a. 停止所有策略(运行)
                b. 通知界面断连状态
                c. 设置引擎状态为与交易断开链接
                d. 清理所有交易数据
                
            说明：策略停止后，所有相关数据清理
                
        '''
        #
        dataList = apiEvent.getData()
        eventSrc = apiEvent.getEventSrc()
        
        self.logger.info('Service %s disconnect: %s'%(eventSrc, dataList))
        
        
    def _filterExg(self, dataList):
        dlist = []
        for data in dataList:
            for commstr in self._commdityFilter:
                if commstr.find(data['ExchangeNo']) >= 0:
                    dlist.append(data)
                    break
                    
        return dlist
        
    def _filterCont(self, dataList, key):
        dlist, contList = [], []
        for data in dataList:
            for commstr in self._commdityFilter:
                if data[key].find(commstr) >= 0:
                    dlist.append(data)
                    if   key == 'CommodityNo':
                        contList.append([data[key],  data['CommodityName']])
                    elif key == 'ContractNo':
                        contList.append(data[key])
                    
        return contList, dlist

    def _onApiExchange(self, apiEvent):
        dataList = self._filterExg(apiEvent.getData())
        if len(dataList) > 0:
            apiEvent.setData(dataList)
        
            uiEvent = Event({
                'StrategyId' : 0,
                'EventCode'  : apiEvent.getEventCode(), 
                'Data'       : dataList
            })
        
            self._send2uiQueue(uiEvent)
            self._qteModel.updateExchange(apiEvent)
            # self._sendEvent2Strategy(apiEvent.getStrategyId(), apiEvent)

        if apiEvent.isChainEnd():
            self._pyApi.reqExchangeStatus(Event({'StrategyId':0, 'Data':''}))
            
    def _onApiExchangeStateQry(self, apiEvent):
        self._onExchangeStateNotice(apiEvent)
        if apiEvent.isChainEnd():
            self._pyApi.reqCommodity(Event({'StrategyId':0, 'Data':''}))
        
    def _onExchangeStateNotice(self, apiEvent):
        self._qteModel.updateExchangeStatus(apiEvent)
        #self._sendEvent2Strategy(apiEvent.getStrategyId(), apiEvent)
        self._sendEvent2AllStrategy(apiEvent)
        self._send2uiQueue(apiEvent)
        
    def _onApiCommodity(self, apiEvent):
        #过滤品种
        commList,dataList = self._filterCont(apiEvent.getData(), 'CommodityNo')

        if len(dataList) > 0:
            apiEvent.setData(dataList)
            
            uiEvent = Event({
                'StrategyId' : 0,
                'EventCode'  : apiEvent.getEventCode(), 
                'Data'       : commList
            })
            self._send2uiQueue(uiEvent)
        
            self._qteModel.updateCommodity(apiEvent)

            # self._sendEvent2AllStrategy(apiEvent)

        if apiEvent.isChainEnd():
            #self._pyApi.reqContract(Event({'StrategyId':0, 'Data':''}))
            self._pyApi.reqTrendContractMapping(Event({'StrategyId':0, 'Data':''}))   

        # 发送商品交易时间模板请求
        for dataDict in apiEvent.getData():
            event = Event({
                'EventCode': EV_ST2EG_TIMEBUCKET_REQ,
                'StrategyId': apiEvent.getStrategyId(),
                'Data': dataDict['CommodityNo'],
            })
            self._pyApi.reqTimebucket(event)

    def _onApiUnderlayMapping(self, apiEvent):
        self._qteModel.updateUnderlayMap(apiEvent)
        if apiEvent.isChainEnd():
            self._pyApi.reqContract(Event({'StrategyId':0, 'Data':''}))
        
    def _onApiContract(self, apiEvent):
        contList, dataList = self._filterCont(apiEvent.getData(), 'ContractNo')
        if len(dataList) > 0:
            apiEvent.setData(dataList)
        
            uiEvent = Event({
                'StrategyId' : 0,
                'EventCode'  : apiEvent.getEventCode(), 
                'Data'       : contList
            })
            self._qteModel.updateContract(apiEvent)
            self._send2uiQueue(uiEvent)
        
        if apiEvent.isChainEnd():
            self._pyApi.reqQryLoginInfo(Event({'StrategyId':0, 'Data':''}))
        
    def _onApiTimeBucket(self, apiEvent):
        self._qteModel.updateTimeBucket(apiEvent)
        
    def _onApiSnapshot(self, apiEvent):
        self._qteModel.updateLv1(apiEvent)
        self._dispathQuote2Strategy(EV_EG2ST_SNAPSHOT_NOTICE, apiEvent)
        
    def _onApiDepthQuote(self, apiEvent):
        self._qteModel.updateLv2(apiEvent)
        self._dispathQuote2Strategy(EV_EG2ST_DEPTH_NOTICE, apiEvent)
        
    def _onApiKlinedataRsp(self, apiEvent):
        self._onApiKlinedata(apiEvent, EV_EG2ST_HISQUOTE_RSP)
        
    def _onApiKlinedataNotice(self, apiEvent):
        self._onApiKlinedata(apiEvent, EV_EG2ST_HISQUOTE_NOTICE)
        
    def _onApiKlinedata(self, apiEvent, code):
        #self._hisModel.updateKline(apiEvent)
        strategyId = apiEvent.getStrategyId()
        # 策略号为0，认为是推送数据
        apiEvent.setEventCode(code)

        if strategyId > 0:
            self._sendEvent2Strategy(strategyId, apiEvent)
            return

        # 推送数据，分发
        key = (apiEvent.getContractNo(), apiEvent.getKLineType(), apiEvent.getKLineSlice())
        if key not in self._hisKLineOberverDict:
            return

        stDict = self._hisKLineOberverDict[key]
        for someStrategy in stDict:
            self._sendEvent2Strategy(someStrategy, apiEvent)

    # 用户登录信息
    def _onApiLoginInfoRsp(self, apiEvent):
        #self.logger.debug("_onApiLoginInfoRsp:%s"%apiEvent.getData())
        self._trdModel.updateLoginInfo(apiEvent)
        self._sendEvent2AllStrategy(apiEvent)
        
        for data in apiEvent.getData():
            self._reqUserInfoByLogin(data)
        
        #没有账号登录，先向界面发送一包用户信息
        if len(apiEvent.getData()) == 0:
            event = Event({
                'StragetgyId' : 0,
                'EventCode': EEQU_SRVEVENT_TRADE_USERQRY,
                'Data' : ''
            })
            self._send2uiQueue(event)
        
    def _reqUserInfoByLogin(self, login):
        event = Event({
            'StrategyId' : 0,
            'Data'       : {
                'UserNo'      : login['LoginNo'],
                'Sign'        : login['Sign'],
            }
        })
        self._reqUserInfo(event)
        
    def _onApiLoginInfoNotice(self, apiEvent):
        '''
        1. 账号登出，推送账号登录状态变化， IsReady = 0
          (1) 清理该登录账号下，所有资金账号的数据
          (2) 委托、资金、委托、持仓清空
          (3) 本地委托信息保留
          (4) 不定时查询资金信息
          
        2. 账号登录，推送账号登录状态变化， IsReady = 1
          (1) 重新查询该登录账号下的资金账号
          (2) 查询各资金账号下的交易数据
          (3) 整理本地委托数据
          (4) 恢复定时查询资金信息
          
        3. 切换交易日，推送账户交易日变化
          (1) 清理登录账户，本地所有交易数据
          (2) 本地委托信息清空
          (3) 重新查询登录账号下，所有用户的交易数据
        '''
        #self.logger.debug("_onApiLoginInfoNotice:%s"%apiEvent.getData())
        self._sendEvent2AllStrategy(apiEvent)
        #ret = self._trdModel.updateLoginInfoEg(apiEvent)
        dataList  = apiEvent.getData()
        loginInfo = self._trdModel.getLoginInfo() 
        
        for data in dataList:
            #登出，清理登录账号和资金账号
            loginNo = data['LoginNo']
            if data['IsReady'] == EEQU_NOTREADY:
                #通知UI，登出所有账号
                loginUser = self._trdModel.getLoginUser(loginNo)
                
                event = Event({
                    'StragetgyId' : 0,
                    'EventCode'   : EV_EG2UI_USER_LOGOUT_NOTICE,
                    'Data' : loginUser
                })
            
                self._send2uiQueue(event)
            
                self._trdModel.delLoginInfo(data)
                self._trdModel.delUserInfo(loginNo)
            
            #交易日切换，清理所有资金账号及本地委托数据
            elif self._trdModel.chkTradeDate(data):
                self.logger.info("Change trade date:%s"%data)
                self._trdModel.delUserInfo(loginNo)
                self._reqUserInfoByLogin(data)
             
            #新账号登录
            elif loginNo not in loginInfo:
                self._trdModel.addLoginInfo(data)
                #查询账户信息
                self._reqUserInfoByLogin(data)
            else:
                self.logger.warn("Unknown login status: %s"%data)

    # 账户信息
    def _onApiUserInfo(self, apiEvent): 
        #分用户 分批次请求交易数据，否则队列会阻塞
        #self.logger.debug("_onApiUserInfo:%s"%apiEvent.getData())
        self._trdModel.updateUserInfo(apiEvent)
        self._send2uiQueue(apiEvent)
        # print("++++++ 账户信息 引擎 ++++++", apiEvent.getData())
        self._sendEvent2AllStrategy(apiEvent)
        
        
        #查询登录账号下的所有资金
        for data in apiEvent.getData():
            #查询资金
            loginApi = self._trdModel.getLoginApi(data['UserNo'])
            currencyNo = 'Base' if loginApi == 'DipperTradeApi' else 'CNY'
            
            event = Event({
                'StrategyId' : 0,
                'Data'       : {
                    'UserNo'      : data['UserNo'],
                    'Sign'        : data['Sign'],
                    'CurrencyNo'  : currencyNo
                }
            })
            self._reqMoney(event)
            
            #查询委托
            event = Event({
                'StrategyId' : 0,
                'Data'       : {
                    'UserNo'      : data['UserNo'],
                    'Sign'        : data['Sign'],
                }
            })
            
            sid = self._reqOrder(event)
            self._SessionUserMap[sid] = data
        
    def _onApiOrderDataQry(self, apiEvent):
        #userNo = self._SessionUserMap[apiEvent.getSessionId()]
        #self.logger.debug("_onApiOrderDataQry:%d,%s,%s"%(apiEvent.getSessionId(), userNo, apiEvent.getData()))
        self._trdModel.updateOrderData(apiEvent)
        self._sendEvent2AllStrategy(apiEvent)
        
        if apiEvent.isChainEnd():
            sid = apiEvent.getSessionId()
            if sid not in self._SessionUserMap:
                self.logger.error('_onApiOrderDataQry: session id error!')
                return
                
            data = self._SessionUserMap[sid]
            
            event = Event({
                'StrategyId' : 0,
                'Data'       : {
                    'UserNo'      : data['UserNo'],
                    'Sign'        : data['Sign'],
                }
            })
            
            sid = self._reqMatch(event)
            self._SessionUserMap[sid] = data
        
        
    def _onApiOrderDataNotice(self, apiEvent):
        #self.logger.debug("_onApiOrderDataNotice:%s"%apiEvent.getData())
        self._trdModel.updateOrderData(apiEvent)
        contractNo = apiEvent.getContractNo()
        # 客户端手动开仓平仓
        if not contractNo:
            contractNo = apiEvent.getData()[0]["Cont"]
        if not contractNo:
            return
        apiEvent.setContractNo(contractNo)
        self._sendEvent2AllStrategy(apiEvent)

    def _onApiMatchDataQry(self, apiEvent):
        #userNo = self._SessionUserMap[apiEvent.getSessionId()]
        #self.logger.debug("_onApiMatchDataQry:%d,%s,%s"%(apiEvent.getSessionId(), userNo, apiEvent.getData()))
        self._trdModel.updateMatchData(apiEvent)
        self._sendEvent2AllStrategy(apiEvent)
        
        if apiEvent.isChainEnd():
            sid = apiEvent.getSessionId()
            if sid not in self._SessionUserMap:
                self.logger.error('_onApiMatchDataQry: session id error!')
                return
                
            data = self._SessionUserMap[sid]
            
            event = Event({
                'StrategyId' : 0,
                'Data'       : {
                    'UserNo'      : data['UserNo'],
                    'Sign'        : data['Sign'],
                }
            })
            
            sid = self._reqPosition(event)
            self._SessionUserMap[sid] = data
            
    def _onApiMatchData(self, apiEvent):
        # 成交信息
        #self.logger.debug("_onApiMatchData:%s"%apiEvent.getData())
        self._trdModel.updateMatchData(apiEvent)
        # print("++++++ 成交信息 引擎 变化 ++++++", apiEvent.getData())
        # TODO: 分块传递
        self._sendEvent2AllStrategy(apiEvent)
        
    def _onApiPosDataQry(self, apiEvent):
        #userNo = self._SessionUserMap[apiEvent.getSessionId()]
        #self.logger.debug("_onApiPosDataQry:%d,%s,%s"%(apiEvent.getSessionId(), userNo, apiEvent.getData()))
        self._trdModel.updatePosData(apiEvent)
        # print("++++++ 持仓信息 引擎 查询 ++++++", apiEvent.getData())
        self._sendEvent2AllStrategy(apiEvent)
        
        if apiEvent.isChainEnd():
            sid = apiEvent.getSessionId()
            if sid not in self._SessionUserMap:
                self.logger.error('_onApiOrderDataQry: session id error!')
                return
            data = self._SessionUserMap[sid]
            self._trdModel.setDataReady(data['UserNo'])

    def _onApiPosData(self, apiEvent):
        #self.logger.debug("_onApiPosData:%s"%apiEvent.getData())
        # 持仓信息
        self._trdModel.updatePosData(apiEvent)
        # print("++++++ 持仓信息 引擎 变化 ++++++", apiEvent.getData())
        # TODO: 分块传递
        self._sendEvent2AllStrategy(apiEvent)

    def _onApiMoney(self, apiEvent):
        # 资金信息
        #self.logger.debug("_onApiMoney:%s"%apiEvent.getData())
        self._trdModel.updateMoney(apiEvent)
        # print("++++++ 资金信息 引擎 ++++++", apiEvent.getData())
        self._sendEvent2AllStrategy(apiEvent)

    # ///////////////策略进程事件//////////////////////////////
    def _getContractList(self, contList):
        contractList = []
        for subContNo in contList:
            if not subContNo or len(subContNo) == 0:
                continue

            if subContNo in self._qteModel._contractData:
                contractList.append(subContNo)
                continue

            # 根据品种获取该品种的所有合约
            for contractNo in list(self._qteModel._contractData.keys()):
                if subContNo in contractNo:
                    contractList.append(contractNo)

        return contractList
        
    # def _reqTimebucket(self, event):
    #     '''查询时间模板'''
    #     self._pyApi.reqTimebucket(event)
    
    def _sendData2Strategy(self, id, code, data='', chain=EEQU_SRVCHAIN_END):
        event = Event({
            'EventSrc'   : EEQU_EVSRC_ENGINE  ,  
            'EventCode'  : code               ,
            'StrategyId' : id                 ,
            'SessionId'  : 0                  ,
            'ChainEnd'   : chain  ,
            'Data'       : data               ,
        })
        
        self._sendEvent2Strategy(id, event)
    
    def _addSubscribe(self, contractNo, strategyId):
        stDict = self._quoteOberverDict[contractNo]
        # 重复订阅
        if strategyId in stDict:
            return
        stDict[strategyId] = None
            
    def _sendQuote(self, contractNo, strategyId):
        dataDict = self._qteModel.getContractDict()
        if contractNo not in dataDict:
            return
        data = dataDict[contractNo].getContract()
        self._sendData2Strategy(strategyId, EV_EG2ST_SUBQUOTE_RSP, data)

    def _reqExchange(self, event):
        '''查询交易所信息'''
        dataDict = self._qteModel.getExchangeDict()
        rspDict = {}
        for k, v in dataDict.items():
            rspDict[k] = v.getExchange()            
        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_EXCHANGE_RSP, rspDict)

    def _reqCommodity(self, event):
        '''查询品种信息'''
        dataDict = self._qteModel.getCommodityDict()
        rspDict = {}
        for k, v in dataDict.items():
            rspDict[k] = v.getCommodity()            
        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_COMMODITY_RSP, rspDict)

    def _reqContract(self, event):
        '''查询合约信息'''
        #合约太多，小字典传输
        dataDict = self._qteModel.getContractDict()
        rspDict = {}
        sendCount = 0
        for k, v in dataDict.items():
            #只用'ExchangeNo', 'CommodityNo', 'ContractNo'
            meta = v.getContract()
            rspDict[k] = {
                'ExchangeNo'  : meta['ExchangeNo'], 
                'CommodityNo' : meta['CommodityNo'],
                'ContractNo'  : meta['ContractNo']
            }
            
            sendCount += 1
            if sendCount >= 500:
                self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_CONTRACT_RSP, rspDict, EEQU_SRVCHAIN_NOTEND)
                rspDict.clear()
                sendCount = 0
                
        if sendCount > 0:
            self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_CONTRACT_RSP, rspDict)
                
    def _reqUnderlayMap(self, event):
        '''查询主力/近月合约映射关系'''
        dataDict = self._qteModel.getUnderlyDict()     
        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_UNDERLAYMAPPING_RSP, dataDict)  
    
    def _reqSubQuote(self, event):
        '''订阅即时行情'''
        contractList = self._getContractList(event.getData())
        strategyId = event.getStrategyId()
        
        subList = []
        for contractNo in contractList:
            if contractNo not in self._quoteOberverDict:
                subList.append(contractNo)
                self._quoteOberverDict[contractNo] = {strategyId:None}
            else:
                if strategyId in self._quoteOberverDict[contractNo]:
                    continue  # 重复订阅，不做任何处理
                self._quoteOberverDict[contractNo][strategyId] = None
                self._sendQuote(contractNo, strategyId)
        
        if len(subList) > 0:
            event.setData(subList)
            self._pyApi.reqSubQuote(event)
    
    def _reqUnsubQuote(self, event):
        '''退订即时行情'''
        strategyId = event.getStrategyId()
        contractList = contractList = self._getContractList(event.getData())
        
        unSubList = []
        for contNo in contractList:
            if contNo not in self._quoteOberverDict:
                continue #该合约没有订阅
            stDict = self._quoteOberverDict[contNo]
            if strategyId not in stDict:
                continue #该策略没有订阅
            stDict.pop(strategyId)
            #已经没有人订阅了，退订吧
            if len(stDict) <= 0:
                unSubList.append(contNo)
                
        if len(unSubList) > 0:
            event.setData(unSubList)
            self._pyApi.reqUnsubQuote(event)
        
    def _reqSubHisquote(self, event): 
        '''订阅历史行情'''
        data = event.getData()
        if data['NeedNotice'] == EEQU_NOTICE_NOTNEED:
            self._pyApi.reqSubHisquote(event)
            return
        
        strategyId = event.getStrategyId()
        key = (data['ContractNo'], data['KLineType'], data['KLineSlice'])

        if key not in self._hisKLineOberverDict:
            self._hisKLineOberverDict[key] = {}

        self._hisKLineOberverDict[key].update({strategyId:True})
        self._pyApi.reqSubHisquote(event)

    def _reqUnsubHisquote(self, event):
        '''退订历史行情'''
        strategyId = event.getStrategyId()
        data = event.getData()

        key = (data['ContractNo'], data['KLineType'], data['KLineSlice'])
        if key not in self._hisKLineOberverDict or strategyId not in self._hisKLineOberverDict[key]:
            return
        stDict = self._hisKLineOberverDict[key]
        stDict.pop(strategyId)
        
    def _onLoginInfoReq(self, event):
        '''保持同步，事件仍使用API事件'''
        dataDict = self._trdModel.getLoginInfo()
        dataList = []
        for v in dataDict.values():
            if v.isReady():
                dataList.append(v.getMetaData())
        #没有数据，发送空列表
        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_LOGINNO_RSP, dataList)
    
    def _onUserInfoReq(self, event):
        dataDict = self._trdModel.getUserInfo()
        dataList = []
        for v in dataDict.values():
            if v.isReady():
                dataList.append(v.getMetaData())
        
        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_USERNO_RSP, dataList)
            
    def _onMoneyReq(self, event):
        dataDict = self._trdModel.getUserInfo()
        dataList = []
        for v in dataDict.values():
            if not v.isReady():
                continue
                
            data = v.getMoneyDict()
            for vv in data.values():
                dataList.append(vv.getMetaData())

        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_MONEY_RSP, dataList)

    def _onOrderReq(self, event):  
        if not self._trdModel.isAllDataReady():
            self.logger.warn("_onOrderReq: data not ready")
            
        #委托信息可能较多，分批次发送，最后发一个空包结束
        dataDict = self._trdModel.getUserInfo()
        for v in dataDict.values():
            if not v.isReady():
                continue

            dataList = []
            sendCount = 0
            data = v.getOrderDict()
            
            for vv in data.values():
                dataList.append(vv.getMetaData())
                sendCount += 1
                if sendCount >= 20:
                    sendCount = 0
                    self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_ORDER_RSP, dataList[:], EEQU_SRVCHAIN_NOTEND)
                    dataList.clear()
                    
            if sendCount > 0:
                self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_ORDER_RSP, dataList[:], EEQU_SRVCHAIN_NOTEND)
                
        #多发一个空结束包
        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_ORDER_RSP, [])
        
    def _onMatchReq(self, event):
        dataDict = self._trdModel.getUserInfo()
        for v in dataDict.values():
            if not v.isReady():
                continue

            dataList = []
            sendCount = 0
            data = v.getMatchDict()
            
            for vv in data.values():
                dataList.append(vv.getMetaData())
                sendCount += 1
                if sendCount >= 20:
                    sendCount = 0
                    self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_MATCH_RSP, dataList[:], EEQU_SRVCHAIN_NOTEND)
                    dataList.clear()
                    
            if sendCount > 0:
                self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_MATCH_RSP, dataList[:], EEQU_SRVCHAIN_NOTEND)
                
        #多发一个空结束包
        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_MATCH_RSP, [])
        
    def _onPositionReq(self, event):
        dataDict = self._trdModel.getUserInfo()
        for v in dataDict.values():
            if not v.isReady():
                continue

            dataList = []
            sendCount = 0
            data = v.getPositionDict()
            
            for vv in data.values():
                dataList.append(vv.getMetaData())
                sendCount += 1
                if sendCount >= 20:
                    sendCount = 0
                    self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_POSITION_RSP, dataList[:], EEQU_SRVCHAIN_NOTEND)
                    dataList.clear()
                    
            if sendCount > 0:
                self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_POSITION_RSP, dataList[:], EEQU_SRVCHAIN_NOTEND)
                
        #多发一个空结束包
        self._sendData2Strategy(event.getStrategyId(), EV_EG2ST_POSITION_RSP, [])
        
    def _onPositionNotice(self, event):
        # 策略虚拟持仓变化通知
        stragetyId = event.getStrategyId()
        self._strategyPosDict[stragetyId] = event.getData()
        
    def _reqKLineStrategySwitch(self, event):
        '''切换策略图'''
        self._pyApi.reqKLineStrategySwitch(event)
        
    def _reqKLineDataResult(self, event):
        '''推送回测K线数据'''
        self._pyApi.reqKLineDataResult(event)
        
    def _reqKLineDataResultNotice(self, event):
        '''更新实盘K线数据'''
        self._pyApi.reqKLineDataResultNotice(event)
        
    def _reqAddKLineSeriesInfo(self, event):
        '''增加指标数据'''
        self._pyApi.addSeries(event)
        
    def _reqKLineSeriesResult(self, event):
        '''推送回测指标数据'''
        self._pyApi.sendSeries(event)
        
    def _reqAddKLineSignalInfo(self, event):
        '''增加信号数据'''
        self._pyApi.addSignal(event)
        
    def _reqKLineSignalResult(self, event):
        '''推送回测信号数据'''
        self._pyApi.sendSignal(event)
        
    def _reqStrategyDataUpdateNotice(self, event):
        '''刷新指标、信号通知'''
        self._pyApi.reqStrategyDataUpdateNotice(event)

    def _reportResponse(self, event):
        self.sendEvent2UI(event)

    def _checkResponse(self, event):
        # 记录策略因为异常是否在界面上显示
        sid = event.getStrategyId()
        data = event.getData()
        self._isShowInUIDict[sid] = data["IsShowFlag"]

        self.sendEvent2UI(event)

    def _monitorResponse(self, event):
        self.sendEvent2UI(event)

    ################################交易请求#########################
    
    def _reqUserInfo(self, event):
        return self._pyApi.reqQryUserInfo(event)
        
    def _reqOrder(self, event):
        self.logger.info("request order:%s"%event.getData())
        return self._pyApi.reqQryOrder(event)
        
    def _reqMatch(self, event):
        #self.logger.info("request match")
        return self._pyApi.reqQryMatch(event)
        
    def _reqPosition(self, event):
        #self.logger.info("request position")
        return self._pyApi.reqQryPosition(event)

    def _reqUserMoney(self):
        userDict = self._trdModel.getUserInfo()
        for v in userDict.values():
            meta = v.getMetaData()
            loginApi = self._trdModel.getLoginApi(meta['UserNo'])
            currencyNo = 'Base' if loginApi == 'DipperTradeApi' else 'CNY'
            
            event = Event({
                'StrategyId' : 0,
                'Data'       : {
                    'UserNo'      : meta['UserNo'],
                    'Sign'        : meta['Sign'],
                    'CurrencyNo'  : currencyNo
                }
            })
            self._reqMoney(event)
         
    def _reqMoney(self, event):
        return self._pyApi.reqQryMoney(event)

    def _sendOrder(self, event):
        # 委托下单，发送委托单
        self._pyApi.reqInsertOrder(event)
        #self._engineOrderModel.updateLocalOrder(event)

    def _deleteOrder(self, event):
        # 委托撤单
        self._pyApi.reqCancelOrder(event)

    def _modifyOrder(self, event):
        # 委托改单
        self._pyApi.reqModifyOrder(event)

    def _sendKLineData(self, event):
        '''推送K线数据'''
        if event.getEventCode() == EV_ST2EG_NOTICE_KLINEDATA:
            self._pyApi.sendKLineData(event, 'N')
        elif event.getEventCode() == EV_ST2EG_UPDATE_KLINEDATA:
            self._pyApi.sendKLineData(event, 'U')

    def _addSeries(self, event):
        '''增加指标线'''
        self._pyApi.addSeries(event)

    def _sendKLineSeries(self, event):
        '''推送指标数据'''
        if event.getEventCode() == EV_ST2EG_NOTICE_KLINESERIES:
            self._pyApi.sendKLineSeries(event, 'N')
        elif event.getEventCode() == EV_ST2EG_UPDATE_KLINESERIES:
            self._pyApi.sendKLineSeries(event, 'U')

    def _addSignal(self, event):
        '''增加信号线'''
        self._pyApi.addSignal(event)

    def _sendKLineSignal(self, event):
        '''推送信号数据'''
        if event.getEventCode() == EV_ST2EG_NOTICE_KLINESIGNAL:
            self._pyApi.sendKLineSignal(event, 'N')
        elif event.getEventCode() == EV_ST2EG_UPDATE_KLINESIGNAL:
            self._pyApi.sendKLineSignal(event, 'U')

    # 停止当前策略
    def _onStrategyQuit(self, event):
        # prevent other threads put data in the queue
        # make sure quit event is the last
        strategyId = event.getStrategyId()
        self.logger.info(f"策略{strategyId}收到停止信号")
        if strategyId not in self._eg2stQueueDict or self._isEffective[strategyId] is False:
            return
        self._isEffective[strategyId] = False

        # to solve broken pip error
        eg2stQueue = self._eg2stQueueDict[strategyId]
        eg2stQueue.put(event)

    # 当策略退出成功时
    def _cleanStrategyInfo(self, strategyId):
        self._isEffective[strategyId] = False
        self._isSt2EngineDataEffective[strategyId] = False
        # 清除即时行情数据观察者
        for k, v in self._quoteOberverDict.items():
            if strategyId in v:
                v.pop(strategyId)
        # 策略停止，通知9.5清理数据
        apiEvent = Event({'StrategyId': strategyId, 'Data': EEQU_STATE_STOP})
        self._pyApi.reqKLineStrategyStateNotice(apiEvent)

    # 队列里面不会有其他事件
    def _onStrategyQuitCom(self, event):
        self.sendEvent2UI(event)
        self._cleanStrategyInfo(event.getStrategyId())
        self._strategyMgr.quitStrategy(event)

    # 启动当前策略
    def _onStrategyResume(self, event):
        strategyId = event.getStrategyId()
        if strategyId in self._eg2stQueueDict and strategyId in self._isEffective and self._isEffective[strategyId]:
            self.logger.info("策略 %d 已经存在" % event.getStrategyId())
            return
        self._strategyMgr.restartStrategy(self._loadStrategy, event)

    #  当量化退出时，发事件给所有的策略
    def _onEquantExit(self, event):
        if self._strategyMgr.isAllStrategyQuit():
            self.saveStrategyContext2File()
        else:
            self._sendEvent2AllStrategy(event)

    # 某个策略退出成功，当量化整个退出时
    def _singleStrategyExitComEquantExit(self, event):
        self._cleanStrategyInfo(event.getStrategyId())
        self._strategyMgr.singleStrategyExitComEquantExit(event)
        if self._strategyMgr.isAllStrategyQuit():
            self.saveStrategyContext2File()

    def _onStrategyRemove(self, event):
        strategyId = event.getStrategyId()
        # 还在正常运行
        if strategyId in self._isEffective and self._isEffective[strategyId]:
            self._isEffective[strategyId] = False
            self._sendEvent2StrategyForce(strategyId, event)
        # 停止
        elif self._strategyMgr.getStrategyState(strategyId) == ST_STATUS_QUIT:
            self._strategyMgr.removeQuitedStrategy(event)
        # 异常状态
        elif self._strategyMgr.getStrategyState(strategyId) == ST_STATUS_EXCEPTION:
            self._strategyMgr.removeExceptionStrategy(event)

        # 策略移除时更新
        if event.getStrategyId() in self._isShowInUIDict.keys():
            self._isShowInUIDict.pop(event.getStrategyId())
        self._updateMaxStrategyId()

    def _onStrategyRemoveCom(self, event):
        self.sendEvent2UI(event)
        self._cleanStrategyInfo(event.getStrategyId())
        self._strategyMgr.removeRunningStrategy(event)

    def _switchStrategy(self, event):
        self._sendEvent2Strategy(event.getStrategyId(), event)

    def _restartStrategyWhenParamsChanged(self, event):
        strategyId = event.getStrategyId()
        if strategyId in self._eg2stQueueDict and strategyId in self._isEffective and self._isEffective[strategyId]:
            self._isEffective[strategyId] = False
            self._isSt2EngineDataEffective[strategyId] = False
            self._cleanStrategyInfo(strategyId)
            self._strategyMgr.destroyProcessByStrategyId(strategyId)

        allConfig = copy.deepcopy(self._strategyMgr.getStrategyAttribute(strategyId)["Config"])
        #allConfig = copy.deepcopy(event.getData()["Config"])
        allConfig["Params"] = event.getData()["Config"]["Params"]
        self._strategyMgr.getStrategyAttribute(strategyId)['Config'] = allConfig
        loadEvent = Event({
            "EventCode":EV_UI2EG_LOADSTRATEGY,
            "StragetgyId":strategyId,
            "Data":{
                "Path"  : self._strategyMgr.getStrategyAttribute(strategyId)["Path"],
                "Args": allConfig,
                "NoInitialize": True
            }
        })
        self._loadStrategy(loadEvent, strategyId)

    def saveStrategyContext2File(self):
        self.logger.debug("save strategy context to file")
        jsonFile = open('config/StrategyContext.json', 'w', encoding='utf-8')
        result = {}
        result["StrategyConfig"] = self._strategyMgr.getStrategyConfig()
        result["MaxStrategyId"] = self._maxStrategyId
        #result["StrategyOrder"] = self._engineOrderModel.getData()
        json.dump(result, jsonFile, ensure_ascii=False, indent=4)
        for child in multiprocessing.active_children():
            try:
                child.terminate()
                child.join(timeout=0.5)
            except Exception as e:
                pass
        self.logger.debug("saveStrategyContext2File exit")

    def sendErrorMsg(self, errorCode, errorText):
        event = Event({
            "EventCode": EV_EG2UI_CHECK_RESULT,
            "StrategyId": 0,
            "Data": {
                "ErrorCode": errorCode,
                "ErrorText": errorText,
            }
        })
        self.sendEvent2UI(event)

    def _clearQueue(self, someQueue):
        try:
            while True:
                someQueue.get_nowait()
        except queue.Empty:
            pass

    def _handleEngineExceptionCausedByStrategy(self, strategyId):
        self._cleanStrategyInfo(strategyId)
        self._strategyMgr._strategyInfo[strategyId]['StrategyState'] = ST_STATUS_EXCEPTION
        self._strategyMgr.destroyProcessByStrategyId(strategyId)
        quitEvent = Event({
            "EventCode": EV_EG2UI_STRATEGY_STATUS,
            "StrategyId": strategyId,
            "Data": {
                "Status": ST_STATUS_EXCEPTION,

            }
        })
        self.sendEvent2UI(quitEvent)

    def _syncStrategyConfig(self, event):
        self._strategyMgr.syncStrategyConfig(event)
        strategyId = event.getStrategyId()
        stconf = event.getData()["Config"]
        actRun = stconf['RunMode']['SendOrder2Actual']
        self._isStActualRun[strategyId] = actRun
        

    def sendEvent2UI(self, event):
        while True:
            try:
                self._eg2uiQueue.put_nowait(event)
                break
            except queue.Full:
                time.sleep(0.1)
                self.logger.error(f"engine向UI传递事件{event.getEventCode()}时阻塞")
