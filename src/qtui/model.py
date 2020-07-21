import os

import threading
import copy
import traceback
import queue

from utils.utils import load_file
from capi.com_types import *
from capi.event import Event

from PyQt5.QtWidgets import QMessageBox


class QuantModel(object):
    def __init__(self, top, ui2eg_queue, eg2ui_queue, logger):
        self._ui2eg_queue = ui2eg_queue
        self._eg2ui_queue = eg2ui_queue
        self._logger = logger
        self._receive = GetEgData(top, self._eg2ui_queue, self._logger)
        self._stManager = self._receive.getStManager()

        # 数据模型
        self.data = []  # 确定需要选用的数据模型
        # 用户选择加载的合约信息
        self._editor = {"path": "", "code": ""}
        self._strategyId = []   # 策略ID
        self._top = top

    def receiveEgEvent(self):
        """处理engine事件"""
        self._receive.handlerEgEvent()
        
    def receiveExit(self):
        '''处理队列退出'''
        self._receive.handlerExit()

    def getCurStId(self):
        """获取当前运行的策略ID"""
        return self._receive.getCurStId()

    def getEditorText(self):
        return self._editor

    def setEditorTextCode(self, path):
        """设置加载合约的路径信息"""
        try:
            if os.path.isfile(path):
                code = load_file(path)
            else:
                code = ""
        except Exception as e:
            self._logger.error("打开策略失败！！")
            traceback.print_exc(e)
        else:
            self._editor["path"] = path
            self._editor["code"] = code

        # self._editor["path"] = path
        # if os.path.isfile(path):
        #     self._editor["code"] = load_file(path)
        # else:
        #     self._editor["code"] = ""

    def getExchange(self):
        return self._receive.getExchange()

    def getCommodity(self):
        return self._receive.getCommodity()

    def getContract(self):
        return self._receive.getContract()

    def getUserNo(self):
        return self._receive.getUserNo()

    def getStrategyManager(self):
        return self._stManager


class SendRequest(object):
    """用于向engine_queue发送请求"""
    def __init__(self, queue, logger):
        self._ui2egQueue = queue
        self._logger = logger

        # 注册发送请求事件
        # self._regRequestCallback()

    def loadRequest(self, path, config):
        """加载请求"""
        msg = {
            'EventSrc'   : EEQU_EVSRC_UI,
            'EventCode'  : EV_UI2EG_LOADSTRATEGY,
            'SessionId'  : None,
            'StrategyId' : 0,
            'UserNo'     : '',
            'Data': {
                'Path' : path,
                'Args' : config,
            }
        }
        event = Event(msg)
        # TODO: 下面队列会阻塞
        try:
            self._ui2egQueue.put(event)
            self._logger.info("[UI]: Running request Send Completely！")
        except:
            print("队列已满, 现在已有消息%s条" % self._ui2egQueue.qsize())

    def reportRequest(self, strategyId):
        """报告"""
        msg = {
            "EventSrc": EEQU_EVSRC_UI,
            "EventCode": EV_UI2EG_REPORT,
            "SessionId": 0,
            "StrategyId": strategyId,
            "UserNo": "",
            "Data": {}
        }
        event = Event(msg)
        try:
            self._ui2egQueue.put(event)
            self._logger.info(f"[UI][{strategyId}]: Report request send completely!")
        except:
            print("队列已满，现在已有消息%s条" % self._ui2egQueue.qsize())

    def quantExitRequest(self):
        """量化界面关闭事件"""
        msg = {
            "EventSrc": EEQU_EVSRC_UI,
            "EventCode": EV_UI2EG_EQUANT_EXIT,
            "SessionId": 0,
            "Data": {}
        }
        event = Event(msg)

        try:
            self._ui2egQueue.put(event)
            self._logger.info("[UI]: GUI close request send completely！")
        except:
            print("队列已满，现在已有消息%s条" % self._ui2egQueue.qsize())

    def strategyPause(self, strategyId):
        """策略暂停事件"""
        msg = {
            "EventSrc"    :   EEQU_EVSRC_UI,
            "EventCode"   :   EV_UI2EG_STRATEGY_PAUSE,
            "StrategyId"  :   strategyId,
            "SessionId"   :   0,
            "Data"        :   {}
        }

        event = Event(msg)

        self._ui2egQueue.put(event)
        self._logger.info(f"[UI][{strategyId}]: Strategy pause request send completely!")

    def strategyResume(self, strategyId):
        """策略运行恢复"""
        msg = {
            "EventSrc"    :   EEQU_EVSRC_UI,
            "EventCode"   :   EV_UI2EG_STRATEGY_RESUME,
            "SessionId"   :   0,
            "StrategyId"  :   strategyId,
            "Data"        :   {}
        }

        event = Event(msg)
        self._ui2egQueue.put(event)
        self._logger.info(f"[UI]{strategyId}: Strategy resume request send completely!")

    def strategyQuit(self, strategyId):
        """策略停止运行"""
        msg = {
            "EventSrc"    :   EEQU_EVSRC_UI,
            "EventCode"   :   EV_UI2EG_STRATEGY_QUIT,
            "SessionId"   :   0,
            "StrategyId"  :   strategyId,
            "Data"        :   {}
        }

        event = Event(msg)
        self._ui2egQueue.put(event)
        self._logger.info(f"[UI][{strategyId}]: Strategy quit request send completely")

    def strategySignal(self, strategyId):
        """策略信号和指标图"""
        msg = {
            "EventSrc"     :    EEQU_EVSRC_UI,
            "EventCode"    :    EV_UI2EG_STRATEGY_FIGURE,
            "SessionId"    :    0,
            "StrategyId"   :    strategyId,
            "Data"         :    {}
        }

        event = Event(msg)
        self._ui2egQueue.put(event)
        self._logger.info(f"[UI][{strategyId}]: Strategy Signal and index figure request send completely!")

    def strategyRemove(self, strategyId):
        """移除策略"""
        msg = {
            "EventSrc": EEQU_EVSRC_UI,
            "EventCode": EV_UI2EG_STRATEGY_REMOVE,
            "SessionId": 0,
            "StrategyId": strategyId,
            "Data": {}
        }

        event = Event(msg)
        self._ui2egQueue.put(event)
        self._logger.info(f"[UI][{strategyId}]: Strategy remove request send completely!")

    def strategyParamRestart(self, strategyId, config):
        """属性设置"""
        msg = {
            "EventSrc"  :   EEQU_EVSRC_UI,
            "EventCode" :   EV_UI2EG_STRATEGY_RESTART,
            "SessionId" :   0,
            "StrategyId":   strategyId,
            "Data"      :   {"Config": config}
        }
        event = Event(msg)
        self._ui2egQueue.put(event)
        self._logger.info(f"[UI][{strategyId}]: Strategy Param setting send completely!")

    def resetSyncPosConf(self, config):
        msg = {
            "EventSrc": EEQU_EVSRC_UI,
            "EventCode": EV_UI2EG_SYNCPOS_CONF,
            "Data": config
        }
        event = Event(msg)
        self._ui2egQueue.put(event)
        self._logger.info(f"[UI]: Reset position setting send completely!")


class GetEgData(object):
    """从engine_queue中取数据"""
    def __init__(self, app, queue, logger):
        self._logger = logger
        self._eg2uiQueue = queue
        self._curStId = None  # 当前加载的策略ID
        self._reportData = {}  # 回测报告请求数据
        self._stManager = StrategyManager(app, logger)  # 策略管理器
        self._exchangeList = []
        self._commodityList = []
        self._contractList = []
        self._userNo = []      # 资金账户
        self._app = app

        # 注册引擎事件应答函数
        self._regAskCallback()

    def _regAskCallback(self):
        self._egAskCallbackDict = {
            EV_EG2UI_LOADSTRATEGY_RESPONSE:   self._onEgLoadAnswer,
            EV_EG2UI_REPORT_RESPONSE:         self._onEgReportAnswer,
            EV_EG2UI_CHECK_RESULT:            self._onEgDebugInfo,
            EV_EG2ST_MONITOR_INFO:            self._onEgMonitorInfo,
            EV_EG2UI_STRATEGY_STATUS:         self._onEgStrategyStatus,
            EV_EG2UI_POSITION_NOTICE:         self._onEgPositionNotice,
            EV_EG2UI_RUNMODE_SWITCH:          self._onEgRunmodeSwitch,
            EV_EG2UI_USER_LOGOUT_NOTICE:      self._onEgLogoutUser,
            EEQU_SRVEVENT_EXCHANGE:           self._onEgExchangeInfo,
            EEQU_SRVEVENT_COMMODITY:          self._onEgCommodityInfo,
            EEQU_SRVEVENT_CONTRACT:           self._onEgContractInfo,
            EEQU_SRVEVENT_TRADE_USERQRY:      self._onEgUserInfo,
            EEQU_SRVEVENT_TRADE_EXCSTATEQRY:  self._onEgExchangeStatus,
            EEQU_SRVEVENT_TRADE_EXCSTATE:     self._onEgExchangeStatus,

            EEQU_SRVEVENT_CONNECT:            self._onEgConnect,
            EEQU_SRVEVENT_DISCONNECT:         self._onEgDisconnect
        }

    # TODO: event.getChian()的类型为字符串：'1', '0'
    def _onEgLoadAnswer(self, event):
        """获取引擎加载应答数据"""
        self._curStId = event.getStrategyId()
        data = event.getData()
        self._stManager.addStrategy(data)
        self._logger.info(f"[UI][{self._curStId}]: Receiveing running answer successfully!")

    def _onEgReportAnswer(self, event):
        """获取引擎报告应答数据并显示报告"""
        data = event.getData()
        id = event.getStrategyId()

        tempResult = data["Result"]
        if not tempResult["Fund"]:
            self._logger.info(f"[UI][{id}]: Report data is empty!")
            # QMessageBox.information(None, '提示', '回测数据为空！', QMessageBox.Yes)
            return

        self._reportData = tempResult

        # 取到报告数据弹出报告
        if self._reportData:
            self._logger.info(f"[UI][{id}]: Receiving report data answer successfully!")
            self._app.reportDisplay(self._reportData, id)
            return

        self._logger.info(f"[UI][{id}]: Report data received is empty!")

    def _onEgDebugInfo(self, event):
        """获取引擎策略调试信息"""
        data = event.getData()
        stId = event.getStrategyId()
        if data:
            errText = data["ErrorText"]
            self._logger.err_error(errText)
            self._logger.info(f"[UI][{stId}]: Receiving strategy debuging info successfully!")
        else:   # TODO：没有错误信息时接收不到消息，所以这里不会被执行
            self._app.clearError()
            self._logger.info(f"[UI][{stId}]: Clearing last debuging info successfully!")

    def _onEgMonitorInfo(self, event):
        """获取引擎实时推送监控信息"""
        stId = event.getStrategyId()
        data = event.getData()
        # 实时更新监控界面信息
        self._stManager.addStrategyRunData(stId, data)
        #TODO： 引擎实时信息太多先不打印吧

    def _onEgExchangeInfo(self, event):
        """获取引擎推送交易所信息"""
        exData = event.getData()
        self._exchangeList.extend(exData)

    def _onEgExchangeStatus(self, event):
        '''获取交易所状态及时间'''
        pass

    def _onEgCommodityInfo(self, event):
        """获取引擎推送品种信息"""
        commData = event.getData()
        self._commodityList.extend(commData)

    def _onEgContractInfo(self, event):
        """获取引擎推送合约信息"""
        contData = event.getData()
        self._contractList.extend(contData)
        #TODO: contract信息太多和userinfo一起打印

    def _onEgUserInfo(self, event):
        """获取引擎推送资金账户"""
        userInfo = event.getData()

        for user in userInfo:
            if user not in self._userNo:
                self._userNo.append(user)

        self._app.set_run_btn_state(True)
        #TODO: 接收exchange、commodity、contract、user信息一起打印
        self._logger.info(f"[UI]: Receiving exchange, commodity, contract and user info successfully!")

    def _onEgLogoutUser(self, event):
        """Update self._userNo when user logouts"""
        logoutUser = event.getData()
        for userNo in logoutUser:
            for uInfo in self._userNo:
                if uInfo["UserNo"] == userNo:
                    self._userNo.remove(uInfo)
                    self._logger.info(f"[UI]: 账号{uInfo}登出")
                    # 账号列表中可能存在重复账号
                    if uInfo not in self._userNo:
                        break

    def _onEgRunmodeSwitch(self, event):
        """update Running Actual/Virtual status"""
        id = event.getStrategyId()
        runStatus = event.getData()["Status"]

        if id not in self._stManager.getStrategyDict():
            return

        # 策略状态改变后要通知监控界面
        self._stManager.updateStrategyRunMode(id, runStatus)
        # 更新策略Id的运行状态
        self._app.updateRunMode(id, runStatus)

        self._logger.info(f"[UI][{id}]: Receiving Runmode Switch {runStatus} successfully!")

    def _onEgStrategyStatus(self, event):
        """接收引擎推送策略状态改变信息"""
        id = event.getStrategyId()
        sStatus = event.getData()["Status"]

        self._logger.info(f"[UI][{id}]: Receiving strategy status %s successfully!"%(sStatus))

        #TODO: if需要改下
        if id not in self._stManager.getStrategyDict() and sStatus != ST_STATUS_REMOVE:
            dataDict = {
                "StrategyId":   id,
                "Status":       sStatus
            }
            self._stManager.add_(dataDict)
        else:
            # 策略状态改变后要通知监控界面
            self._stManager.updateStrategyStatus(id, sStatus)
            # 更新策略Id的运行状态
            self._app.updateRunStage(id, sStatus)
            if sStatus == ST_STATUS_QUIT:
                # 策略停止时接收策略数据
                self._stManager.addResultData(id, event.getData()["Result"])
                self._logger.info(f"[UI][{id}]: Receiving strategy data successfully when strategy quit!")
            # TODO：引擎发了两遍remove事件
            if sStatus == ST_STATUS_REMOVE:
                # 删除策略需要接到通知之后再进行删除
                self._stManager.removeStrategy(id)
                # 更新界面
                self._logger.info(f"[UI][{id}]: Receiving strategy removing answer info successfully!")
                self._app.delUIStrategy(id)

    def _onEgPositionNotice(self, event):
        #TODO：没有登录交易账户时接收不到该事件
        self._app.updateSyncPosition(event)

    def _onEgConnect(self, event):
        src = event.getEventSrc()
        self._app.setConnect(src)
        self._logger.info(f"[UI]: Receiving engine connect successfully!")

    def _onEgDisconnect(self, event):
        src = event.getEventSrc()
        self._app.setDisconnect(src)
        self._logger.info(f"[UI]: Receiving engine disconnect successfully!")
                
    def handlerExit(self):
        self._eg2uiQueue.put(Event({"EventCode":999}))
        self._logger.info(f"[UI]: handlerExit")

    def handlerEgEvent(self):
        try:
            # 如果不给出超时则会导致线程退出时阻塞
            event = self._eg2uiQueue.get(timeout=0.01)
            # event = self._eg2uiQueue.get_nowait()
            eventCode = event.getEventCode()

            if eventCode not in self._egAskCallbackDict:
                self._logger.error(f"[UI]: Unknown engine event{eventCode}")
            else:
                self._egAskCallbackDict[eventCode](event)
        except queue.Empty:
            #self._logger.debug("[UI]handlerEgEvent _eg2uiQueue empty!")
            pass

    def getReportData(self):
        if self._reportData:
            return self._reportData
        return None

    def getCurStId(self):
        if self._curStId:
            return self._curStId
        return None

    def getStManager(self):
        return self._stManager

    def getExchange(self):
        """取得接收到的交易所信息"""
        # 去重
        # exchangeList = []
        # [exchangeList.append(ex) for ex in self._exchangeList if not ex in exchangeList]
        return self._exchangeList

    def getCommodity(self):
        """品种"""
        return self._commodityList

    def getContract(self):
        """合约"""
        return self._contractList

    def getUserNo(self):
        """资金账户"""
        return self._userNo


class StrategyManager(object):

    """
    self._strategyDict = {
        "id" : {
                "StrategyId": id,        # 策略Id
                "StrategyName": None,    # 策略名
                "StrategyState: None,    # 策略状态
                "Config": {},            # 运行设置信息
                "RunningData": {},       # 监控数据
                "TestResult" :{},        # 回测结果数据

    }
    """

    def __init__(self, app, logger):
        self._app = app
        self._logger = logger
        self._strategyDict = {}
        self.lock = threading.RLock()

    def addStrategy(self, dataDict):
        id = dataDict['StrategyId']
        self.lock.acquire()
        try:
            self._strategyDict[id] = dataDict
        except Exception as e:
            self._logger.error("addStrategy方法出错")
        finally:
            self.lock.release()
        self._app.addExecute(dataDict)

    def add_(self, dataDict):
        #TODO: 策略状态传过来事件问题
        id = dataDict['StrategyId']
        self.lock.acquire()
        try:
            self._strategyDict[id] = dataDict
        except Exception as e:
            self._logger.error("add_方法出错")
        finally:
            self.lock.release()

    def addStrategyRunData(self, id, data):
        """策略运行数据实时更新"""
        self.lock.acquire()
        try:
            self._strategyDict[id].update({"RunningData": data})
        except Exception as e:
            self._logger.error("addStrategyRunData方法出错")
        finally:
            self.lock.release()

    def removeStrategy(self, id):
        self.lock.acquire()
        try:
            if id in self._strategyDict:
                self._strategyDict.pop(id)
        except Exception as e:
            self._logger.error("removeStrategy方法出错")
        finally:
            self.lock.release()

    def queryStrategyStatus(self, id):
        self.lock.acquire()
        try:
            return self._strategyDict[id]["StrategyState"]
        except Exception as e:
            self._logger.error("queryStrategyStatus方法出错")
        finally:
            self.lock.release()
        # return self._strategyDict[id]["StrategyState"]

    def queryStrategyRunType(self, id):
        self.lock.acquire()
        try:
            return self._strategyDict[id]["RunType"]
        except Exception as e:
            self._logger.error("queryStrategyRunType方法出错")
        finally:
            self.lock.release()

    def queryStrategyName(self, id):
        self.lock.acquire()
        try:
            return self._strategyDict[id]["StrategyName"]
        except Exception as e:
            self._logger.error("queryStrategyName方法出错")
        finally:
            self.lock.release()

    def updateStrategyStatus(self, id, status):
        self.lock.acquire()
        try:
            if id in self._strategyDict:
                self._strategyDict[id]["StrategyState"] = status
        except Exception as e:
            self._logger.error("updateStrategyStatus方法出错")
        finally:
            self.lock.release()

    def updateStrategyRunMode(self, id, status):
        """运行模式更新"""
        self.lock.acquire()
        try:
            if id in self._strategyDict:
                self._strategyDict[id]["IsActualRun"] = status
        except Exception as e:
            self._logger.error("updateStrategyRunMode方法出错")
        finally:
            self.lock.release()

    def getStrategyConfigData(self, id):
        """获取运行设置信息"""
        self.lock.acquire()
        try:
            return self._strategyDict[id]["Config"]
        except Exception as e:
            self._logger.error("getStrategyConfigData方法出错")
        finally:
            self.lock.release()

    def getStrategyParamData(self, id):
        """获取用户参数设置信息"""
        self.lock.acquire()
        try:
            return self._strategyDict[id]["Params"]
        except Exception as e:
            self._logger.error("getStrategyParamData方法出错")
        finally:
            self.lock.release()

    def getStrategyDict(self):
        """获取全部运行策略"""
        self.lock.acquire()
        try:
            return copy.deepcopy(self._strategyDict)
        except RuntimeError:
            self._logger.warn("strategyDict在访问过程中更改")
        finally:
            self.lock.release()

    def getSingleStrategy(self, id):
        """获取某个运行策略"""
        self.lock.acquire()
        try:
            return self._strategyDict[id]
        except Exception as e:
            self._logger.error("getSingleStrategy方法出错")
        finally:
            self.lock.release()

    def addResultData(self, id, data):
        """用于保存策略停止时的测试数据"""
        self.lock.acquire()
        try:
            self._strategyDict[id].update({"ResultData": data})
        except Exception as e:
            self._logger.error("addResultData方法出错")
        finally:
            self.lock.release()