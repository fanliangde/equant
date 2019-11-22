import os
import sys
import threading
import time
import importlib
import traceback
import re

from PyQt5.QtCore import Qt, qInstallMessageHandler
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QDesktopWidget

from qtui.model import QuantModel, SendRequest
from qtui.view import QuantApplication
from utils.language import *
from capi.com_types import *
from utils.window.framelesswindow import FramelessWindow, CommonHelper, DARKSTYLE, WHITESTYLE, THESE_STATE_DARK, \
    THESE_STATE_WHITE
from qtui.reportview.reportview import ReportView


class Controller(object):
    '''程序化入口类'''

    def __init__(self, logger, ui2eg_q, eg2ui_q):

        # 日志对象
        self.logger = logger
        # 初始化多语言
        # load_language("config")
        self._ui2egQueue = ui2eg_q
        self._eg2uiQueue = eg2ui_q

        # UI2EG发送请求对象
        self._request = SendRequest(self._ui2egQueue, self.logger)
        # 高分辨率支持
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        qInstallMessageHandler(lambda x, y, z: None)
        self.mainApp = QApplication(sys.argv)

        # 根据分辨率调整字体
        font = QFont("Microsoft YaHei UI", 10)
        pointsize = font.pointSize()
        font.setPixelSize(pointsize * 90 / 72)
        self.mainApp.setFont(font)

        ################创建回测报告####################
        self._createReportWin()
        ################################################

        self.app = QuantApplication(self)
        if self.app.settings.contains('theme') and self.app.settings.value('theme') == 'vs-dark':
            qss_path = DARKSTYLE
            theme = THESE_STATE_DARK
        else:
            qss_path = WHITESTYLE
            theme = THESE_STATE_WHITE

        self.mainWnd = FramelessWindow()
        style = CommonHelper.readQss(qss_path)
        self.mainWnd.setStyleSheet(style)
        self.mainWnd.setWindowTitle('极星量化')
        self.mainWnd.setWinThese(theme)
        self.mainWnd.setWindowIcon(QIcon('icon/epolestar ix2.ico'))
        screen = QDesktopWidget().screenGeometry()
        self.mainWnd.setGeometry(screen.width() * 0.1, screen.height() * 0.1, screen.width() * 0.8,
                                 screen.height() * 0.8)
        # self.mainWnd.titleBar.buttonClose.clicked.connect(self.quitThread)
        self.mainWnd.titleBar.buttonClose.clicked.disconnect(self.mainWnd.titleBar.closeWindow)
        self.mainWnd.titleBar.buttonClose.clicked.connect(self.app.save_edit_strategy)
        self.mainWnd.setWidget(self.app)

        # 创建模块
        self.model = QuantModel(self.app, self._ui2egQueue, self._eg2uiQueue, self.logger)
        self.app.init_control()
        self.logger.info("Create quant model!")

        # 策略管理器
        self.strategyManager = self.getStManager()

        # 创建接收引擎数据线程
        self.receiveEgThread = ChildThread(self.model.receiveEgEvent)

        # 设置日志更新
        # self.update_log()
        # self.update_mon()

    def _createReportWin(self, *args):
        style = CommonHelper.readQss(WHITESTYLE)
        self.reportWnd = FramelessWindow()
        self.reportWnd.resize(1000, 600)
        self.reportWnd.setMinimumSize(600, 600)
        self.reportWnd.setMaximumSize(1000, 600)
        self.reportWnd.hideTheseBtn()
        self.reportWnd.setStyleSheet(style)
        self.reportWnd.setWindowTitle("回测报告")
        self.reportWnd.setWinThese(THESE_STATE_WHITE)
        self.reportWnd.setWindowIcon(QIcon('icon/epolestar ix2.ico'))
        self.reportView = ReportView()
        self.reportView.setObjectName("ReportView")
        self.reportWnd.setWidget(self.reportView)

    def get_logger(self):
        return self.logger

    def update_log(self):
        try:
            self.app.updateLogText()
        except Exception as e:
            # self.logger.warn("异常", "程序退出异常")
            pass

    def update_mon(self):
        try:
            self.updateMonitor()
        except Exception as e:
            pass

    # def updateSig(self):
    #     self.app.updateSigText()
    #
    # def updateUsr(self):
    #     self.app.updateUsrText()

    def updateMonitor(self):
        # 更新监控界面策略信息
        try:
            strategyDict = self.strategyManager.getStrategyDict()
            # TODO: strategyDict的异常策略应该怎么处理?
            for stId in strategyDict:
                if "RunningData" not in strategyDict[stId]:
                    continue
                try:
                    # TODO：StrategyState为什么会不存在呢？
                    if strategyDict[stId]["StrategyState"] == ST_STATUS_PAUSE or strategyDict[stId][
                        "StrategyState"] == ST_STATUS_QUIT or strategyDict[stId][
                        "StrategyState"] == ST_STATUS_EXCEPTION:
                        continue
                except KeyError as e:
                    self.logger.warn(f"策略数据错误: {stId}, {strategyDict[stId]}")
                self.app.updateValue(stId, strategyDict[stId]["RunningData"])
        except PermissionError as e:
            self.logger.error("更新监控信息时出错")

    def quitThread(self):
        self.logger.info("quitThread exit")
        # 停止更新界面子线程
        # self.monitorThread.stop()
        # self.monitorThread.join()

        # 停止更新信号记录
        # self.sigThread.stop()
        # self.sigThread.join()

        # 停止更新用户日志
        # self.usrThread.stop()
        # self.usrThread.join()

        # 向引擎发送退出事件
        self.sendExitRequest()

        # 停止接收策略引擎队列数据
        self.receiveEgThread.stop()
        self.model.receiveExit()
        self.receiveEgThread.join()

        self.logger.info("before app.close")
        self.app.close()
        self.logger.info("after app.close")

    def run(self):
        # 启动监控策略线程
        # self.monitorThread.start()
        # 启动接收数据线程
        self.receiveEgThread.start()

        # self.sigThread.start()

        # self.usrThread.start()

        #启动主界面线程

        self.mainWnd.show()
        self.mainApp.exec_()
        
    def set_help_text(self, funcName, text):
        self.app.set_help_text(funcName, text)

    def setEditorTextCode(self, path):
        """设置当前编辑的策略路径和代码信息"""
        self.model.setEditorTextCode(path)

    def getEditorText(self):
        return self.model.getEditorText()

    def getStManager(self):
        """获取策略管理器"""
        return self.model.getStrategyManager()

    def saveStrategy(self):
        """保存当前策略"""
        self.app.quant_editor.saveEditor()

    def parseStrategtParam(self, strategyPath):
        """解析策略中的用户参数"""
        g_params = {}
        with open(strategyPath, 'r', encoding="utf-8") as f:
            content = [line.strip() for line in f]
            for c in content:
                # regex = re.compile(r"^g_params[\[][\"\'](.*)[\"\'][\]]\s*=[\s]*([^\s]*)[\s]*(#[\s]*(.*))?")
                regex1 = re.compile(r"^g_params[\[][\"\'](.*)[\"\'][\]]\s*=[\s]*(.*)[\s]*#[\s]*(.*)?")
                regex2 = re.compile(r"^g_params[\[][\"\'](.*)[\"\'][\]]\s*=[\s]*(.*)[\s]*#?[\s]*(.*)?")

                reg1 = regex1.search(c)
                reg2 = regex2.search(c)
                if reg1 or reg2:
                    reg = reg1 if reg1 else reg2
                    ret = [reg.groups()[1], reg.groups()[2]]
                    # if ret[1] is None: ret[1] = ""
                    try:
                        ret[0] = eval(ret[0])
                    except:
                        pass
                    g_params.update(
                        {
                            reg.groups()[0]: ret
                        }
                    )
        return g_params

    def load(self, strategyPath, param={}):
        # TODO：新增param参数，用于接收用户策略的参数
        """
        加载合约事件
        :param strategyPath: 策略路径
        :param param: 策略参数信息
        :return:
        """
        # 运行策略前将用户修改保存
        self.saveStrategy()
        # 解析策略参数
        param = self.parseStrategtParam(strategyPath)
        self.app.create_strategy_policy_win(param=param)

        config = self.app.getConfig()
        if config:  # 获取到config
            self._request.loadRequest(strategyPath, config)
            self.logger.info("load strategy")

    def paramLoad(self, id):
        """用户参数修改后策略重新启动"""
        param = self.getUserParam(id)
        strategyPath = self.strategyManager.getSingleStrategy(id)["Path"]
        self.app.create_strategy_policy_win(param, strategyPath, id)

    def generateReportReq(self, strategyIdList):
        """发送生成报告请求"""
        # 量化启动时的恢复策略列表中的策略没有回测数据
        # 策略停止之后的报告数据从本地获取，不发送请求
        # 策略启动时查看数据发送报告请求，从engine获取数据
        # 查看策略的投资报告(不支持查看多个)
        if len(strategyIdList) >= 1:
            id = strategyIdList[0]
            status = self.strategyManager.queryStrategyStatus(id)
            strategyData = self.strategyManager.getSingleStrategy(id)
            if status == ST_STATUS_QUIT:  # 策略已停止，从本地获取数据
                if "ResultData" not in strategyData:  # 程序启动时恢复的策略没有回测数据
                    QMessageBox.warning(None, '警告', '策略未启动，报告数据不存在')
                    return
                reportData = strategyData["ResultData"]
                self.app.reportDisplay(reportData, id)
                return
            self._request.reportRequest(id)

    def newStrategy(self, path):
        """右键新建策略"""
        if not os.path.exists(path):
            f = open(path, "w")
            f.write('import talib\n'
                    '\n\n'
                    'def initialize(context): \n    pass\n\n\n'
                    'def handle_data(context):\n    pass\n\n\n'
                    'def exit_callback(context):\n    pass')
            f.close()

        self.app.updateEditorModifyTime(os.path.getmtime(path))

        # 更新策略路径
        self.setEditorTextCode(path)

        self.app.updateStrategyTree(path)

        # 更新策略编辑界面内容
        self.updateEditor(path)

    def newDir(self, path):
        """策略目录右键新建文件夹"""
        if not os.path.exists(path):
            os.makedirs(path)
        self.app.updateStrategyTree(path)

    def updateEditor(self, path):
        """
        更新策略编辑的内容和表头
        :param path: 策略路径，为空则将编辑界面内容置为空
        :return:
        """
        editor = self.getEditorText()
        fileName = os.path.basename(path)

        self.updateEditorHead(fileName)
        self.app.updateEditorText(editor["code"])

    def updateEditorHead(self, text):
        """更新策略表头"""
        self.app.updateEditorHead(text)

    def sendExitRequest(self):
        """发送量化界面退出请求"""
        self._request.quantExitRequest()

    def pauseRequest(self, strategyIdList):
        """
        发送所选策略暂停请求
        :param strategyId: 所选策略Id列表
        :return:
        """
        for id in strategyIdList:
            self._request.strategyPause(id)

    def resumeRequest(self, strategyIdList):
        """
        发送所选策略恢复运行请求
        :param strategyId: 所选策略Id列表
        :return:
        """
        for id in strategyIdList:
            # 策略如果是启动状态，则忽略此次启动请求
            strategyDict = self.strategyManager.getStrategyDict()
            if id in strategyDict:
                status = self.strategyManager.queryStrategyStatus(id)
                if status == ST_STATUS_HISTORY or status == ST_STATUS_CONTINUES:
                    self.logger.info("策略重复启动！")
                    continue
            self._request.strategyResume(id)

    def quitRequest(self, strategyIdList):
        """
        发送所选策略停止请求
        :param strategyId:  所选策略Id列表
        :return:
        """
        for id in strategyIdList:
            strategyDict = self.strategyManager.getStrategyDict()
            if id in strategyDict:
                status = self.strategyManager.queryStrategyStatus(id)
                if status == ST_STATUS_QUIT:
                    self.logger.info("策略%s已停止!" % (id))
                    continue
                self._request.strategyQuit(id)
            else:
                self.logger.info("策略管理器中不存在策略%s" % (id))

    def delStrategy(self, strategyIdList):
        # 获取策略管理器
        for id in strategyIdList:
            strategyDict = self.strategyManager.getStrategyDict()
            if id in strategyDict:
                if strategyDict[id]["StrategyState"] == ST_STATUS_QUIT or \
                        strategyDict[id]["StrategyState"] == ST_STATUS_EXCEPTION:  # 策略已经停止或策略异常
                    self.strategyManager.removeStrategy(id)
                    self.app.delUIStrategy(id)
                self._request.strategyRemove(id)
            else:
                self.app.delUIStrategy(id)

    def signalDisplay(self, strategyIdList):
        """查看策略的信号及指标图(默认查看一个)"""
        if len(strategyIdList) >= 1:
            id = strategyIdList[0]
            self._request.strategySignal(id)

    def getUserParam(self, id):
        """获取用户设置的参数信息"""
        return self.strategyManager.getStrategyParamData(id)

    def paramSetting(self, strategyIdList):
        """发送属性设置事件"""
        if len(strategyIdList) >= 1:
            id = strategyIdList[0]

            self.paramLoad(id)


class ChildThread(threading.Thread):
    """带停止标志位的线程"""

    def __init__(self, target, wait=0):
        threading.Thread.__init__(self)

        self.target = target
        self.sleepTime = wait

        # self.cond = threading.Condition()
        self.isStopped = False

    def run(self):
        # while not self.isStopped:
        while True:
            if self.isStopped:
                break
            self.target()
            time.sleep(self.sleepTime)

    def stop(self):
        # 设置停止标志位
        self.isStopped = True