import json
import os
import threading

import pandas as pd
import shutil
# import sys
import traceback
from datetime import datetime

from dateutil.parser import parse
from copy import deepcopy

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QPoint, QUrl, pyqtSignal, pyqtSlot, QSharedMemory, QTimer, QDir, QSettings
from PyQt5.QtGui import QTextCursor, QIcon, QKeySequence
from PyQt5.QtWidgets import *

from engine.strategy_cfg_model_new import StrategyConfig_new
from report.fieldConfigure import RunMode, StrategyStatus

from api.base_api import BaseApi
from api.api_func import _all_func_
from capi.com_types import *
from qtui.utils import parseStrategtParam, Tree, FileIconProvider, MyMessageBox, getText, \
    EmptyDelegate, MySortFilterProxyModel
from utils.utils import save

from qtui.quant.code_editor import CodeEditor

from utils.window.framelesswindow import FramelessWindow, CommonHelper
from utils.window.res.default import *
from api.base_api import BaseApi

strategy_path = os.path.join(os.getcwd(), 'strategy')


class StrategyPolicy(QWidget):
    def __init__(self, control, path, flag=False, master=None, param=None, parent=None):
        super().__init__(parent)

        self._master = master  # 夫父窗口

        self.main_layout = QVBoxLayout()
        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        h_spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.confirm = QPushButton('确定')
        self.cancel = QPushButton('取消')
        self.confirm.setMinimumWidth(80)
        self.cancel.setMinimumWidth(80)

        self.strategyTabWidget = QTabWidget()
        self.strategyTabWidget.setObjectName("StrategyTabWidget")

        self.run_policy()
        self.create_contract_policy()
        self.create_money_policy()
        self.create_sample_policy()
        self.create_param_policy()

        layout1.addWidget(self.strategyTabWidget)

        layout2.addItem(h_spacerItem)
        layout2.addWidget(self.confirm)
        layout2.addWidget(self.cancel)
        layout2.setSpacing(6)
        layout2.setContentsMargins(0, 10, 20, 10)
        self.main_layout.addLayout(layout1)
        self.main_layout.addLayout(layout2)
        self.setLayout(self.main_layout)

        self.contractTableWidget.hideColumn(4)
        self.contractTableWidget.verticalHeader().setVisible(False)
        self.contractTableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.contractTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contractTableWidget.setEditTriggers(QTableView.NoEditTriggers)
        self.cycleLineEdit.setValidator(QtGui.QIntValidator())  # 设置只能输入数字
        self.initFundlineEdit.setValidator(QtGui.QIntValidator())  # 设置只能输入数字
        self.defaultOrderLineEdit.setValidator(QtGui.QIntValidator())  # 设置只能输入数字
        self.miniOrderLineEdit.setValidator(QtGui.QIntValidator(1, 1000))  # 设置只能输入数字
        reg = QtCore.QRegExp("^(((\\d{1,2})[.]((\\d{1,2})?))|100)$")
        marginLimit = QtGui.QRegExpValidator(reg)
        self.marginRateLineEdit.setValidator(marginLimit)  # 设置只能输入数字

        feeLimit = QtGui.QRegExpValidator(reg)
        self.openFeeRateLineEdit.setValidator(feeLimit)  # 设置只能输入数字
        self.closeFeeRateLineEdit.setValidator(feeLimit)  # 设置只能输入数字
        self.slippageLineEdit.setValidator(QtGui.QIntValidator())  # 设置只能输入数字
        self.isConOpenTimesLineEdit.setValidator(QtGui.QIntValidator(1, 100))  # 设置只能输入数字
        self.openTimesLineEdit.setValidator(QtGui.QIntValidator(1, 100))  # 设置只能输入数字
        self.addTimerButton.clicked.connect(self.add_timer)
        self.deleteTimerButton.clicked.connect(self.delete_timer)
        self.addContract.clicked.connect(self.create_contract_win)
        self.deleteContract.clicked.connect(self.delete_contract)
        self.updateContract.clicked.connect(self.update_contract)
        self.confirm.clicked.connect(self.enter)

        self._control = control

        # 用户设置信息
        self.config = {}

        # 获取用户参数
        self._userParam = param if param else {}
        # 策略路径
        self._strategyPath = path
        # 是否时属性设置运行窗口标志位
        self._paramFlag = flag
        self._strConfig = StrategyConfig_new()

        # 设置属性值
        self.setDefaultConfigure()

        self.contractWin = ContractWin()
        self.contractWin.setObjectName("ContractWin")
        self.contractWin.confirm_signal.connect(self.add_contract)
        # self.contractWin.setStyle(self.style())

        self.main_contractWin = FramelessWindow()

        self.main_contractWin.hideTheseBtn()
        self.main_contractWin.titleBar.iconLabel.hide()
        self.main_contractWin.disabledMaximumBtn()
        self.main_contractWin.disabledMinimunBtn()
        self.main_contractWin.setWindowTitle('合约设置')
        self.main_contractWin.titleBar.buttonClose.clicked.connect(self.main_contractWin.close)
        self.main_contractWin.setWidget(self.contractWin)
        self.contractWin.cancel.clicked.connect(self.main_contractWin.close)
        # 设置窗口的大小和位置
        pGeometry = self._master.frameGeometry()
        self.main_contractWin.resize(pGeometry.width() * 0.4, pGeometry.height() * 0.5)
        self.main_contractWin.center(pGeometry)

        if self._control.mainWnd.titleBar.theseState == '浅色':
            style = CommonHelper.readQss(WHITESTYLE)
        else:
            style = CommonHelper.readQss(DARKSTYLE)
        self.main_contractWin.setStyleSheet('')
        self.main_contractWin.setStyleSheet(style)

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def change_line_edit(self):
        if self.defaultOrderComboBox.currentIndex() == 0:
            self.defaultOrderLineEdit.setText('1')
            self.label32.setText('手')
        elif self.defaultOrderComboBox.currentIndex() == 1:
            self.defaultOrderLineEdit.setText('5')
            self.label32.setText('%')
        elif self.defaultOrderComboBox.currentIndex() == 2:
            self.defaultOrderLineEdit.setText('1000000')
            self.label32.setText('元')

    def run_policy(self):
        self.runPolicy = QWidget()
        self.runPolicy.setObjectName("RunPolicy")
        run_layout = QVBoxLayout()
        h_spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        v_spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # --------------------触发方式设置-------------------
        self.trigger = QGroupBox('触发方式')
        trigger_layout = QHBoxLayout()
        # ----左侧部分---
        trigger_left = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        self.KLineCheckBox = QCheckBox('K线触发')
        self.KLineCheckBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.KLineCheckBox.setChecked(True)
        h_layout1.addWidget(self.KLineCheckBox)
        h_layout2 = QHBoxLayout()
        self.snapShotCheckBox = QCheckBox('即时行情触发')
        self.snapShotCheckBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h_layout2.addWidget(self.snapShotCheckBox)
        h_layout3 = QHBoxLayout()
        self.tradeCheckBox = QCheckBox('交易数据触发')
        self.tradeCheckBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h_layout3.addWidget(self.tradeCheckBox)
        h_layout4 = QHBoxLayout()
        self.cycleCheckBox = QCheckBox('每间隔')
        self.cycleCheckBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cycleLineEdit = QLineEdit('200')
        self.cycleCheckBox.stateChanged.connect(self._cycleCheckBoxStateChangedCallback)
        self.cycleLabel = QLabel('毫秒执行代码（100的整数倍）')
        self.cycleLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h_layout4.addWidget(self.cycleCheckBox)
        h_layout4.addWidget(self.cycleLineEdit)
        h_layout4.addWidget(self.cycleLabel)
        h_layout4.addItem(h_spacerItem1)

        trigger_left.addLayout(h_layout1)
        trigger_left.addLayout(h_layout2)
        trigger_left.addLayout(h_layout3)
        trigger_left.addLayout(h_layout4)

        # 右侧部分
        trigger_right = QVBoxLayout()
        rignt_hlayout1 = QHBoxLayout()
        time_label = QLabel('指定时刻')
        self.set_label_size_policy(time_label)
        time_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        rignt_hlayout1.addWidget(time_label)
        rignt_hlayout1.setAlignment(Qt.AlignLeft)

        rignt_hlayout2 = QHBoxLayout()
        self.timerListWidget = QListWidget()
        self.timerListWidget.setFixedHeight(100)
        rignt_hlayout2.addWidget(self.timerListWidget)
        rignt_hlayout3 = QHBoxLayout()
        self.timerEdit = QTimeEdit()
        self.timerEdit.setDisplayFormat('HH:mm:ss')
        self.addTimerButton = QPushButton('增加')
        self.addTimerButton.setFixedWidth(60)
        self.deleteTimerButton = QPushButton('删除')
        self.deleteTimerButton.setFixedWidth(60)
        rignt_hlayout3.addWidget(self.timerEdit)
        rignt_hlayout3.addItem(h_spacerItem2)
        rignt_hlayout3.addWidget(self.addTimerButton)
        rignt_hlayout3.addWidget(self.deleteTimerButton)

        trigger_right.addLayout(rignt_hlayout1)
        trigger_right.addLayout(rignt_hlayout2)
        trigger_right.addLayout(rignt_hlayout3)

        trigger_layout.addLayout(trigger_left, 3)
        trigger_layout.addLayout(trigger_right, 2)
        self.trigger.setLayout(trigger_layout)

        # -----------------------基础设置----------------------------
        self.basePolicy = QGroupBox('基础设置')
        policy_layout = QVBoxLayout()
        policy_layout1 = QHBoxLayout()
        order_label = QLabel('发单时机：')
        self.set_label_size_policy(order_label)
        self.sendOrderRealtime = QRadioButton('实时发单')
        self.sendOrderRealtime.setChecked(True)
        self.sendOrderKStable = QRadioButton('K线稳定后发单')
        policy_layout1.addWidget(order_label)
        policy_layout1.addWidget(self.sendOrderRealtime)
        policy_layout1.addWidget(self.sendOrderKStable)
        policy_layout1.addItem(h_spacerItem3)
        policy_layout2 = QHBoxLayout()
        run_label = QLabel('运行模式：')

        self.set_label_size_policy(run_label)
        self.actualCheckBox = QCheckBox('实盘运行')
        self.alarmCheckBox = QCheckBox('发单报警')
        self.allowCheckBox = QCheckBox('允许弹窗')
        policy_layout2.addWidget(run_label)
        policy_layout2.addWidget(self.actualCheckBox)
        policy_layout2.addWidget(self.alarmCheckBox)
        policy_layout2.addWidget(self.allowCheckBox)
        policy_layout2.addItem(h_spacerItem4)
        policy_layout3 = QHBoxLayout()
        user_label = QLabel('账户：')
        self.set_label_size_policy(user_label)
        self.userComboBox = QComboBox()
        policy_layout3.addWidget(user_label)
        policy_layout3.addWidget(self.userComboBox)
        policy_layout3.addItem(h_spacerItem5)

        # 设置对齐
        order_label.setFixedWidth(80)
        run_label.setFixedWidth(80)
        user_label.setFixedWidth(80)
        self.sendOrderRealtime.setFixedWidth(120)
        self.actualCheckBox.setFixedWidth(120)
        self.sendOrderKStable.setFixedWidth(120)
        self.alarmCheckBox.setFixedWidth(120)
        self.userComboBox.setFixedWidth(120)

        policy_layout.addLayout(policy_layout1)
        policy_layout.addLayout(policy_layout2)
        policy_layout.addLayout(policy_layout3)
        policy_layout.setSpacing(10)
        self.basePolicy.setLayout(policy_layout)
        # ------------------------------------------------------------
        run_layout.addWidget(self.trigger)
        run_layout.addWidget(self.basePolicy)
        run_layout.addItem(v_spacerItem)

        self.runPolicy.setLayout(run_layout)
        self.strategyTabWidget.addTab(self.runPolicy, '运行方式')

    def _cycleCheckBoxStateChangedCallback(self, state):
        """周期触发checkbox回调"""
        if state == Qt.Checked:
            self.cycleLineEdit.setFocus()
            self.cycleLineEdit.selectAll()

    def create_contract_policy(self):
        self.contractPolicy = QWidget()
        self.contractPolicy.setObjectName("ContractPolicy")
        v_spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        left_layout = QHBoxLayout()
        self.contractTableWidget = QTableWidget()
        self.contractTableWidget.setObjectName("ContractTableWidget")
        self.contractTableWidget.setColumnCount(5)
        self.contractTableWidget.setHorizontalHeaderLabels(['合约', 'K线类型', 'K线周期', '运算起始点', 'data'])
        # self.contractTableWidget.horizontalHeader().setStretchLastSection(True)
        self.contractTableWidget.horizontalHeader().setHighlightSections(False)  # 关闭高亮头
        self.contractTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        self.contractTableWidget.setColumnWidth(0, 150)

        left_layout.addWidget(self.contractTableWidget)
        right_layout = QVBoxLayout()
        self.addContract = QPushButton('增加')
        self.addContract.setFixedWidth(70)
        self.deleteContract = QPushButton('删除')
        self.deleteContract.setFixedWidth(70)
        self.updateContract = QPushButton('修改')
        self.updateContract.setFixedWidth(70)
        right_layout.addItem(v_spacerItem)
        right_layout.addWidget(self.addContract)
        right_layout.addWidget(self.deleteContract)
        right_layout.addWidget(self.updateContract)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.contractPolicy.setLayout(main_layout)
        self.strategyTabWidget.addTab(self.contractPolicy, '合约设置')

    def create_money_policy(self):
        self.moneyPolicy = QWidget()
        self.moneyPolicy.setObjectName("MoneyPolicy")
        h_spacerItem1 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem2 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem3 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem4 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem5 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem6 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem7 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem8 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem9 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem10 = QSpacerItem(300, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout = QVBoxLayout()
        h_layout1 = QHBoxLayout()
        label1 = QLabel('初始资金：')
        label1.setFixedWidth(100)
        self.set_label_size_policy(label1)
        self.initFundlineEdit = QLineEdit('1000000')
        label12 = QLabel('元')
        self.set_label_size_policy(label12)
        h_layout1.addWidget(label1)
        h_layout1.addWidget(self.initFundlineEdit)
        h_layout1.addWidget(label12)
        h_layout1.addItem(h_spacerItem1)

        h_layout2 = QHBoxLayout()
        label2 = QLabel('交易方向：')
        label2.setFixedWidth(100)
        self.set_label_size_policy(label2)
        self.tradeDirectionComboBox = QComboBox()
        self.tradeDirectionComboBox.addItems(['双向交易', '仅多头', '仅空头'])
        h_layout2.addWidget(label2)
        h_layout2.addWidget(self.tradeDirectionComboBox)
        h_layout2.addItem(h_spacerItem2)

        h_layout3 = QHBoxLayout()
        label3 = QLabel('默认下单量：')
        label3.setFixedWidth(100)
        self.set_label_size_policy(label3)
        self.defaultOrderComboBox = QComboBox()
        self.defaultOrderComboBox.addItems(['按固定合约数', '按资金比例', '按固定资金'])
        self.defaultOrderComboBox.currentIndexChanged.connect(self.change_line_edit)
        self.defaultOrderLineEdit = QLineEdit('1')
        self.label32 = QLabel('手')
        self.set_label_size_policy(self.label32)
        h_layout3.addWidget(label3)
        h_layout3.addWidget(self.defaultOrderComboBox)
        h_layout3.addWidget(self.defaultOrderLineEdit)
        h_layout3.addWidget(self.label32)
        h_layout3.addItem(h_spacerItem3)

        h_layout4 = QHBoxLayout()
        label4 = QLabel('最小下单量：')
        label4.setFixedWidth(100)
        self.set_label_size_policy(label4)
        self.miniOrderLineEdit = QLineEdit('1')
        label41 = QLabel('手(1-1000)')
        self.set_label_size_policy(label41)
        h_layout4.addWidget(label4)
        h_layout4.addWidget(self.miniOrderLineEdit)
        h_layout4.addWidget(label41)
        h_layout4.addItem(h_spacerItem4)

        h_layout5 = QHBoxLayout()
        label5 = QLabel('保证金率：')
        label5.setFixedWidth(100)
        self.set_label_size_policy(label5)
        self.marginRateLineEdit = QLineEdit('8')
        label51 = QLabel('%')
        self.set_label_size_policy(label51)
        h_layout5.addWidget(label5)
        h_layout5.addWidget(self.marginRateLineEdit)
        h_layout5.addWidget(label51)
        h_layout5.addItem(h_spacerItem5)

        h_layout6 = QHBoxLayout()
        label6 = QLabel('开仓收费方式：')
        label6.setFixedWidth(100)
        self.set_label_size_policy(label6)
        self.openTypeComboBox = QComboBox()
        self.openTypeComboBox.addItems(['固定值', '比例'])
        self.openTypeComboBox.currentIndexChanged.connect(self._openTypeComboBoxSelectCall)
        h_layout6.addWidget(label6)
        h_layout6.addWidget(self.openTypeComboBox)
        h_layout6.addItem(h_spacerItem6)

        h_layout7 = QHBoxLayout()
        label7 = QLabel('开仓手续费(率)：')
        label7.setFixedWidth(100)
        self.set_label_size_policy(label7)
        self.openFeeRateLineEdit = QLineEdit('1')
        self.label71 = QLabel('%')
        self.set_label_size_policy(self.label71)
        h_layout7.addWidget(label7)
        h_layout7.addWidget(self.openFeeRateLineEdit)
        h_layout7.addWidget(self.label71)
        h_layout7.addItem(h_spacerItem7)

        h_layout8 = QHBoxLayout()
        label8 = QLabel('平仓收费方式：')
        label8.setFixedWidth(100)
        self.set_label_size_policy(label8)
        self.closeTypeComboBox = QComboBox()
        self.closeTypeComboBox.addItems(['固定值', '比例'])
        self.closeTypeComboBox.currentIndexChanged.connect(self._closeTypeComboBoxSelectCall)
        h_layout8.addWidget(label8)
        h_layout8.addWidget(self.closeTypeComboBox)
        h_layout8.addItem(h_spacerItem8)

        h_layout9 = QHBoxLayout()
        label9 = QLabel('平仓手续费(率)：')
        label9.setFixedWidth(100)
        self.set_label_size_policy(label9)
        self.closeFeeRateLineEdit = QLineEdit('1')
        self.label91 = QLabel('%')
        self.set_label_size_policy(self.label91)
        h_layout9.addWidget(label9)
        h_layout9.addWidget(self.closeFeeRateLineEdit)
        h_layout9.addWidget(self.label91)
        h_layout9.addItem(h_spacerItem9)

        h_layout10 = QHBoxLayout()
        label10 = QLabel('滑点损耗：')
        label10.setFixedWidth(100)
        self.set_label_size_policy(label10)
        self.slippageLineEdit = QLineEdit('0')
        h_layout10.addWidget(label10)
        h_layout10.addWidget(self.slippageLineEdit)
        h_layout10.addItem(h_spacerItem10)

        self.initFundlineEdit.setFixedWidth(105)
        self.tradeDirectionComboBox.setFixedWidth(105)
        self.defaultOrderComboBox.setFixedWidth(105)

        self.defaultOrderLineEdit.setFixedWidth(105)

        self.miniOrderLineEdit.setFixedWidth(105)
        self.marginRateLineEdit.setFixedWidth(105)
        self.openTypeComboBox.setFixedWidth(105)
        self.openFeeRateLineEdit.setFixedWidth(105)
        self.closeTypeComboBox.setFixedWidth(105)
        self.closeFeeRateLineEdit.setFixedWidth(105)
        self.slippageLineEdit.setFixedWidth(105)

        main_layout.addLayout(h_layout1)
        main_layout.addLayout(h_layout2)
        main_layout.addLayout(h_layout3)
        main_layout.addLayout(h_layout4)
        main_layout.addLayout(h_layout5)
        main_layout.addLayout(h_layout6)
        main_layout.addLayout(h_layout7)
        main_layout.addLayout(h_layout8)
        main_layout.addLayout(h_layout9)
        main_layout.addLayout(h_layout10)

        v_spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(v_spacerItem)

        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 10, 0, 0)

        self.moneyPolicy.setLayout(main_layout)
        self.strategyTabWidget.addTab(self.moneyPolicy, '资金设置')

    def _openTypeComboBoxSelectCall(self, tag):
        if tag == 0:
            self.label71.hide()
        else:
            self.label71.show()

    def _closeTypeComboBoxSelectCall(self, tag):
        if tag == 0:
            self.label91.hide()
        else:
            self.label91.show()


    def create_sample_policy(self):
        send_order_widget = QWidget()
        send_order_widget.setObjectName("SendOrderWidget")
        send_order_layout = QVBoxLayout()
        self.groupBox = QGroupBox('发单设置')
        main_layout = QVBoxLayout()
        h_spacerItem1 = QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem2 = QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem3 = QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem4 = QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        h_layout1 = QHBoxLayout()
        self.isConOpenTimesCheckBox = QCheckBox('最大连续同向开仓次数：')
        self.isConOpenTimesLineEdit = QLineEdit('1')
        label1 = QLabel('次(1-100)')
        self.set_label_size_policy(label1)
        h_layout1.addWidget(self.isConOpenTimesCheckBox)
        h_layout1.addWidget(self.isConOpenTimesLineEdit)
        h_layout1.addWidget(label1)
        h_layout1.addItem(h_spacerItem1)

        h_layout2 = QHBoxLayout()
        self.openTimesCheckBox = QCheckBox('每根K线同向开仓次数：')
        self.openTimesLineEdit = QLineEdit('1')
        label2 = QLabel('次(1-100)')
        self.set_label_size_policy(label2)
        h_layout2.addWidget(self.openTimesCheckBox)
        h_layout2.addWidget(self.openTimesLineEdit)
        h_layout2.addWidget(label2)
        h_layout2.addItem(h_spacerItem2)

        h_layout3 = QHBoxLayout()
        self.canCloseCheckBox = QCheckBox('开仓的当前K线不允许反向下单')
        h_layout3.addWidget(self.canCloseCheckBox)
        h_layout3.addItem(h_spacerItem3)

        h_layout4 = QHBoxLayout()
        self.canOpenCheckBox = QCheckBox('平仓的当前K线不允许开仓')
        h_layout4.addWidget(self.canOpenCheckBox)
        h_layout4.addItem(h_spacerItem4)

        main_layout.addLayout(h_layout1)
        main_layout.addLayout(h_layout2)
        main_layout.addLayout(h_layout3)
        main_layout.addLayout(h_layout4)
        main_layout.setSpacing(15)

        self.isConOpenTimesCheckBox.setFixedWidth(150)
        self.openTimesCheckBox.setFixedWidth(150)
        self.isConOpenTimesLineEdit.setFixedWidth(50)
        self.openTimesLineEdit.setFixedWidth(50)

        self.isConOpenTimesCheckBox.stateChanged.connect(self._conCheckBoxStateChangedCallback)
        self.openTimesCheckBox.stateChanged.connect(self._openCheckBoxStateChangedCallback)

        self.groupBox.setLayout(main_layout)
        send_order_layout.addWidget(self.groupBox)
        v_spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        send_order_layout.addItem(v_spacerItem)
        send_order_widget.setLayout(send_order_layout)
        self.strategyTabWidget.addTab(send_order_widget, '样本设置')

    def _conCheckBoxStateChangedCallback(self, state):
        """最大连续同向开仓次数checkbox回调"""
        if state == Qt.Unchecked:
            self.isConOpenTimesLineEdit.setText("不限制")
            self.isConOpenTimesLineEdit.setEnabled(False)
        else:
            self.isConOpenTimesLineEdit.setText("1")
            self.isConOpenTimesLineEdit.setEnabled(True)
            self.isConOpenTimesLineEdit.setFocus()
            self.isConOpenTimesLineEdit.selectAll()

    def _openCheckBoxStateChangedCallback(self, state):
        """每根K线同向开仓次数checkbox回调"""
        if state == Qt.Unchecked:
            self.openTimesLineEdit.setText("不限制")
            self.openTimesLineEdit.setEnabled(False)
        else:
            self.openTimesLineEdit.setText("1")
            self.openTimesLineEdit.setEnabled(True)
            self.openTimesLineEdit.setFocus()
            self.openTimesLineEdit.selectAll()

    def create_param_policy(self):
        self.paramPolicy = QWidget()
        self.paramPolicy.setObjectName("ParamPolicy")

        main_layout = QVBoxLayout()
        label = QLabel('鼠标单击"当前值"进行参数修改：')
        label.setObjectName("ParamLabel")
        self.set_label_size_policy(label)
        self.paramsTableWidget = QTableWidget()
        self.paramsTableWidget.setSelectionMode(QAbstractItemView.NoSelection)
        self.paramsTableWidget.setColumnCount(4)
        self.paramsTableWidget.setItemDelegateForColumn(0, EmptyDelegate(self))  # 设置第一列不可编辑
        self.paramsTableWidget.setItemDelegateForColumn(2, EmptyDelegate(self))  # 设置第三列不可编辑
        self.paramsTableWidget.setHorizontalHeaderLabels(['参数', '当前值', '类型', '描述'])
        self.paramsTableWidget.verticalHeader().setVisible(False)  # 隐藏行号
        # self.paramsTableWidget.horizontalHeader().setStretchLastSection(True)
        self.paramsTableWidget.horizontalHeader().setHighlightSections(False)  # 关闭高亮头
        self.paramsTableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.paramsTableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.paramsTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        main_layout.addWidget(label)
        main_layout.addWidget(self.paramsTableWidget)

        self.paramPolicy.setLayout(main_layout)
        self.strategyTabWidget.addTab(self.paramPolicy, '参数设置')

    def set_label_size_policy(self, label):
        """设置label标签不伸展"""
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def add_timer(self):
        t = self.timerEdit.text()
        ti = t.replace(':', '')
        if not self.timerListWidget.findItems(ti, Qt.MatchExactly):
            self.timerListWidget.addItem(ti)
        else:
            MyMessageBox.warning(self, "提示", "已存在该时间！请重新提交！", QMessageBox.Ok)

    def delete_timer(self):
        row = self.timerListWidget.currentRow()
        if row != -1:
            self.timerListWidget.removeItemWidget(self.timerListWidget.takeItem(row))

    def create_contract_win(self):
        # 增加合约槽函数，弹出合约设置窗口
        self.set_default_value()
        self.main_contractWin.setWindowModality(Qt.ApplicationModal)  # 阻塞父窗口
        self.main_contractWin.show()

    def set_default_value(self):
        # ------------------设置合约-----------------------------
        self.contractWin.contractCodeLineEdit.setText('')
        self.contractWin.contractCodeLineEdit.setEnabled(True)
        self.contractWin.select.setEnabled(True)
        # ------------------设置k线类型--------------------------
        self.contractWin.kLineTypeComboBox.setCurrentIndex(2)
        # ------------------设置k线周期--------------------------
        self.contractWin.kLinePeriodComboBox.setCurrentIndex(0)
        # ------------------设置运算起始点-----------------------
        self.contractWin.AllkLineRadioButton.setChecked(False)

        self.contractWin.startDateRadioButton.setChecked(False)
        self.contractWin.startDateLineEdit.setText('')
        self.contractWin.historyRadioButton.setChecked(False)
        self.contractWin.qtyRadioButton.setChecked(True)
        self.contractWin.qtylineEdit.setText('2000')
        self.contractWin.row = -1

    def contractSelect(self, exchange, commodity, contract):
        self.contractSelectWin = ContractSelect(exchange, commodity, contract)
        self.contractSelectWin.setObjectName("ContractSelectWin")
        self.main_contractSelectWin = FramelessWindow()
        # self.main_contractSelectWin.setFixedSize(750, 550)
        # 设置窗口的大小和位置
        _pGeometry = self.main_contractWin.frameGeometry()
        self.main_contractSelectWin.resize(_pGeometry.width() * 2, _pGeometry.height() * 2)
        self.main_contractSelectWin.center(_pGeometry)
        self.main_contractSelectWin.titleBar.theseSelect.hide()
        self.main_contractSelectWin.titleBar.iconLabel.hide()
        self.main_contractSelectWin.disabledMaximumBtn()
        self.main_contractSelectWin.disabledMinimunBtn()
        self.main_contractSelectWin.setWindowTitle('选择合约')
        self.main_contractSelectWin.titleBar.buttonClose.clicked.connect(self.main_contractSelectWin.close)
        self.main_contractSelectWin.setWidget(self.contractSelectWin)
        if self._control.mainWnd.getWinThese() == '浅色':
            style = CommonHelper.readQss(WHITESTYLE)
        else:
            style = CommonHelper.readQss(DARKSTYLE)
        self.main_contractSelectWin.setStyleSheet('')
        self.main_contractSelectWin.setStyleSheet(style)
        self.main_contractSelectWin.setWindowModality(Qt.ApplicationModal)  # 阻塞父窗口
        self.main_contractSelectWin.show()
        self.contractSelectWin.confirm.clicked.connect(self.set_contract)
        self.contractSelectWin.cancel.clicked.connect(self.main_contractSelectWin.close)

    def set_contract(self):
        if self.contractSelectWin.choice_tree.topLevelItemCount() == 1:
            self.contractWin.contractCodeLineEdit.setText(self.contractSelectWin.choice_tree.topLevelItem(0).text(0))
            self.main_contractSelectWin.close()

    def add_contract(self, sample_dict):
        KLineType = sample_dict.get('KLineType')
        if KLineType == 'T':
            _KlineType = '分笔'
        elif KLineType == 'M':
            _KlineType = '分钟'
        elif KLineType == 'D':
            _KlineType = '日线'
        else:  # KLineType == 'S'
            _KlineType = '秒'
        if sample_dict.get('AllK'):
            start = '所有K线'
        elif sample_dict.get('BeginTime'):
            start = sample_dict.get('BeginTime')
        elif sample_dict.get('KLineCount'):
            start = sample_dict.get('KLineCount')
        else:
            start = '不执行历史K线'
        items = [sample_dict.get('contract'), _KlineType, sample_dict.get('KLineSlice'), start, json.dumps(sample_dict)]

        if self.contractWin.row != -1:
            row = self.contractWin.row
        else:
            row = self.contractTableWidget.rowCount()
            sample_dict_list = []
            for i in range(row):
                sample_dict_list.append(json.loads(self.contractTableWidget.item(i, 4).text()))

            # row不相同
            d = json.loads(items[4])
            d.pop('row')
            for _items in deepcopy(sample_dict_list):
                _items.pop('row')
                if d == _items:
                    MyMessageBox.warning(self, '提示', '请勿添加重复合约设置！', QMessageBox.Ok)
                    return

            self.contractTableWidget.setRowCount(row + 1)

        for j in range(len(items)):
            item = QTableWidgetItem(str(items[j]))
            item.setTextAlignment(Qt.AlignCenter)
            self.contractTableWidget.setItem(row, j, item)

    def delete_contract(self):
        items = self.contractTableWidget.selectedItems()
        if items:
            self.contractTableWidget.removeRow(items[0].row())

    def update_contract(self):
        items = self.contractTableWidget.selectedItems()
        if not items:
            return
        row = items[0].row()
        item = self.contractTableWidget.item(row, 4)
        sample_dict = json.loads(item.text())
        # ------------------设置合约-----------------------------
        self.contractWin.contractCodeLineEdit.setText(sample_dict.get('contract'))
        self.contractWin.contractCodeLineEdit.setEnabled(False)
        self.contractWin.select.setEnabled(False)
        # ------------------设置k线类型--------------------------
        k_type = ['T', 'S', 'M', 'D']
        t = sample_dict.get('KLineType')
        self.contractWin.kLineTypeComboBox.setCurrentIndex(k_type.index(t))
        # ------------------设置k线周期--------------------------
        if not t == 'T':  # k线类型不是分笔的时候设置k线周期
            k_period = [1, 2, 3, 5, 10, 15, 30, 60, 120]
            self.contractWin.kLinePeriodComboBox.setCurrentIndex(k_period.index(int(sample_dict.get('KLineSlice'))))
        else:  # k线类型为分笔的时候，k线周期设置不可用
            self.contractWin.kLinePeriodComboBox.setEnabled(False)
        # ------------------设置运算起始点-----------------------
        if sample_dict.get('AllK'):
            self.contractWin.AllkLineRadioButton.setChecked(True)
        elif sample_dict.get('BeginTime'):
            self.contractWin.startDateRadioButton.setChecked(True)
            temp = sample_dict.get('BeginTime')
            text = "".join(temp.split("-"))
            self.contractWin.startDateLineEdit.setText(text)
        elif sample_dict.get('UseSample'):  # TODO 确认条件True还是False时候执行
            self.contractWin.historyRadioButton.setChecked(True)
        elif sample_dict.get('KLineCount'):
            self.contractWin.qtyRadioButton.setChecked(True)
            self.contractWin.qtylineEdit.setText(str(sample_dict.get('KLineCount')))
        else:
            pass
        self.contractWin.row = row
        self.main_contractWin.setWindowModality(Qt.ApplicationModal)  # 阻塞父窗口
        self.main_contractWin.show()

    def enter(self):
        # TODO: IntVar()显示时会补充一个0？？？
        user = self.userComboBox.currentText()  # 用户
        initFund = self.initFundlineEdit.text()  # 初始资金
        defaultType = self.defaultOrderComboBox.currentText()  # 默认下单方式
        defaultQty = self.defaultOrderLineEdit.text()  # 默认下单量
        minQty = self.miniOrderLineEdit.text()  # 最小下单量
        # hedge = self.hedge.get()
        margin = self.marginRateLineEdit.text()  # 保证金率

        openType = self.openTypeComboBox.currentText()  # 开仓收费方式
        closeType = self.closeTypeComboBox.currentText()  # 开仓收费方式
        openFee = self.openFeeRateLineEdit.text()  # 开仓手续费（率）
        closeFee = self.closeFeeRateLineEdit.text()  # 平仓手续费（率）

        tradeDirection = self.tradeDirectionComboBox.currentText()  # 交易方向
        slippage = self.slippageLineEdit.text()  # 滑点损耗
        # TODO: contract另外保存了一个变量，不再分解了
        # contractInfo = self.contract.get()

        # contract = (contractInfo.rstrip("\n")).split("\n")

        # if len(contract) == 0:
        #     messagebox.showinfo("提示", "未选择合约")
        #     return
        # else:
        #     contractInfo = (contract.rstrip(", ")).split(", ")

        timer = ''  # 时间
        count = self.timerListWidget.count()
        for i in range(count):
            text = self.timerListWidget.item(i).text() + '\n' if i != count - 1 else self.timerListWidget.item(i).text()
            timer += text

        isCycle = int(self.cycleCheckBox.isChecked())  # 是否按周期触发
        cycle = self.cycleLineEdit.text()  # 周期
        isKLine = int(self.KLineCheckBox.isChecked())  # K线触发
        isSnapShot = int(self.snapShotCheckBox.isChecked())  # 行情触发
        isTrade = int(self.tradeCheckBox.isChecked())  # 交易数据触发

        # beginDate = self.beginDate.get()
        # # beginDateFormatter = parseYMD(beginDate)
        # fixQty = self.fixQty.get()
        # sampleVar = self.sampleVar.get()

        sendOrderMode = 0 if self.sendOrderRealtime.isChecked() else 1  # 发单时机： 0. 实时发单 1. K线稳定后发单

        isActual = int(self.actualCheckBox.isChecked())  # 实时发单
        isAlarm = int(self.alarmCheckBox.isChecked())  # 发单报警
        isPop = int(self.allowCheckBox.isChecked())  # 允许弹窗
        # isContinue = self.isContinue.get()
        isOpenTimes = int(self.openTimesCheckBox.isChecked())  # 每根K线同向开仓次数标志
        openTimes = self.openTimesLineEdit.text()  # 每根K线同向开仓次数

        isConOpenTimes = int(self.isConOpenTimesCheckBox.isChecked())  # 最大连续同向开仓次数标志

        conOpenTimes = self.isConOpenTimesLineEdit.text()  # 最大连续同向开仓次数
        canClose = int(self.canCloseCheckBox.isChecked())  # 开仓的当前K线不允许平仓
        canOpen = int(self.canOpenCheckBox.isChecked())  # 平仓的当前K线不允许开仓

        # -------------转换定时触发的时间形式--------------------------
        time = timer.split("\n")
        timerFormatter = []
        for t in time:
            if t:
                timerFormatter.append(t)

        if cycle == "":
            MyMessageBox.warning(self, "极星量化", "定时触发周期不能为空", QMessageBox.Ok)
            return
        elif int(cycle) % 100 != 0:
            MyMessageBox.warning(self, "极星量化", "定时触发周期为100的整数倍", QMessageBox.Ok)
            return
        else:
            pass

        if not initFund:
            MyMessageBox.warning(self, "极星量化", "初始资金不能为空", QMessageBox.Ok)
            return

        if float(initFund) < 1000:
            MyMessageBox.warning(self, "极星量化", "初始资金不能小于1000元", QMessageBox.Ok)
            return

        if not defaultQty:
            MyMessageBox.warning(self, "极星量化", "默认下单量不能为空", QMessageBox.Ok)
            return

        if not margin:
            MyMessageBox.warning(self, "极星量化", "保证金率不能为空", QMessageBox.Ok)
            return

        if minQty == "":
            MyMessageBox.warning(self, "极星量化", "最小下单量不能为空", QMessageBox.Ok)
            return
        elif int(minQty) > MAXSINGLETRADESIZE:
            MyMessageBox.warning(self, "极星量化", "最小下单量不能大于1000", QMessageBox.Ok)
            return
        else:
            pass

        if not openFee:
            MyMessageBox.warning(self, "极星量化", "开仓手续费不能为空", QMessageBox.Ok)
            return

        if not closeFee:
            MyMessageBox.warning(self, "极星量化", "平仓手续费不能为空", QMessageBox.Ok)
            return

        if isConOpenTimes:
            if conOpenTimes == '' or int(conOpenTimes) < 1 or int(conOpenTimes) > 100:
                MyMessageBox.warning(self, "极星量化", "最大连续同向开仓次数必须介于1-100之间", QMessageBox.Ok)
                return

        if isOpenTimes:
            if openTimes == '' or int(openTimes) < 1 or int(openTimes) > 100:
                MyMessageBox.warning(self, "极星量化", "每根K线同向开仓次数必须介于1-100之间", QMessageBox.Ok)
                return

        # 用户是否确定用新参数重新运行
        if self._paramFlag:
            reply = MyMessageBox.question(self, '提示', '点确定后会重新运行策略？', QMessageBox.Ok | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return

        # TODO: 合约设置，K线类型， K线周期、运算起始点设置
        # 多合约信息：
        contsInfo = []
        for i in range(self.contractTableWidget.rowCount()):
            contValues = []
            for j in range(self.contractTableWidget.columnCount()):
                contValues.append(self.contractTableWidget.item(i, j).text())
            contsInfo.append(contValues)

            kLineTypeDict = {
                "分笔": 'T',
                "秒": 'T',
                "分钟": 'M',
                "日线": 'D',
            }

            contCode = contValues[0]
            kTypeValue = kLineTypeDict[contValues[1]]
            kSliceValue = int(contValues[2])

            samValue = ''
            if contValues[3] == "所有K线":
                samValue = 'A'
            elif contValues[3] == "不执行历史K线":
                samValue = 'N'
            elif json.loads(contValues[4]).get('BeginTime'):
                temp = json.loads(contValues[4]).get('BeginTime')
                samValue = "".join(temp.split("-"))
            elif json.loads(contValues[4]).get('KLineCount'):
                samValue = json.loads(contValues[4]).get('KLineCount')

            self._strConfig.setBarInfoInSample(contCode, kTypeValue, kSliceValue, samValue)

        # K线触发
        if isKLine:
            self._strConfig.setTrigger(5)
        # 即时行情触发
        if isSnapShot:
            self._strConfig.setTrigger(1)
        # 交易数据触发
        if isTrade:
            self._strConfig.setTrigger(2)
        # 周期触发
        if isCycle:
            self._strConfig.setTrigger(3, int(cycle))
        # 指定时刻
        if timer:
            self._strConfig.setTrigger(4, timerFormatter)

        # 发单设置
        if sendOrderMode == 0:
            self._strConfig.setOrderWay('1')
        else:
            self._strConfig.setOrderWay('2')

        # 连续运行
        # self.config["RunMode"]["Simulate"]["Continues"] = True
        # 运行模式
        if isActual:
            self._strConfig.setActual()
        # 发单报警
        self._strConfig.setAlarm(True) if int(isAlarm) else self._strConfig.setAlarm(False)
        # 允许弹窗
        self._strConfig.setPop(True) if int(isPop) else self._strConfig.setPop(False)

        # 账户
        self._strConfig.setUserNo(user)
        # 初始资金
        self._strConfig.setInitCapital(int(initFund))
        # 交易方向
        if tradeDirection == "双向交易":
            self._strConfig.setTradeDirection(0)
        elif tradeDirection == "仅多头":
            self._strConfig.setTradeDirection(1)
        else:
            self._strConfig.setTradeDirection(2)

        # 默认下单量
        if defaultType == "按固定合约数":
            self._strConfig.setOrderQty("1", int(defaultQty))
        elif defaultType == "按固定资金":
            self._strConfig.setOrderQty("2", float(defaultQty))
        elif defaultType == "按资金比例":
            self._strConfig.setOrderQty("3", float(defaultQty) / 100)
        else:
            raise Exception("默认下单量类型异常")

        # 最小下单量
        self._strConfig.setMinQty(int(minQty))
        # 投保标志
        # if hedge == "投机":
        #     self._strConfig.setHedge("T")
        # elif hedge == "套利":
        #     self._strConfig.setHedge("B")
        # elif hedge == "保值":
        #     self._strConfig.setHedge("S")
        # elif hedge == "做市":
        #     self._strConfig.setHedge("M")
        # else:
        #     raise Exception("投保标志异常")

        # # 保证金率
        # TODO: margin类型没有设置！！！！！
        # 比例
        self._strConfig.setMargin('R', float(margin) / 100)

        # 开仓按比例收费
        if openType == "比例":
            self._strConfig.setTradeFee('O', 'R', float(openFee) / 100)
        else:
            self._strConfig.setTradeFee('O', 'F', float(openFee))
        # 平仓按比例收费
        if closeType == "比例":
            self._strConfig.setTradeFee('C', 'R', float(closeFee) / 100)
        else:
            self._strConfig.setTradeFee('C', 'F', float(closeFee))
        # 平今手续费
        # TODO：平今手续费没有设置
        # self.config["Money"]["CloseTodayFee"]["Type"] = "F"
        # self.config["Money"]["CloseTodayFee"]["Type"] = 0
        self._strConfig.setTradeFee('T', "F", 0)

        # 滑点损耗
        self._strConfig.setSlippage(float(slippage))

        # 发单设置
        openT = int(openTimes) if isOpenTimes else -1  # 每根K线同向开仓次数
        cOpenT = int(conOpenTimes) if isConOpenTimes else -1  # 最大连续同向开仓次数
        self._strConfig.setLimit(openT, cOpenT, canClose, canOpen)

        # 用户参数
        params = {}
        for i in range(self.paramsTableWidget.rowCount()):
            paramValues = []
            for j in range(self.paramsTableWidget.columnCount()):
                if j == 1:
                    if self.paramsTableWidget.item(i, 2).text() == 'bool':
                        paramValues.append(self.paramsTableWidget.cells[i].currentText())
                    else:
                        paramValues.append(self.paramsTableWidget.cells[i].text())
                else:
                    paramValues.append(self.paramsTableWidget.item(i, j).text())
            temp = paramValues[1]
            if paramValues[2] == "bool":
                if paramValues[1] == "True":
                    temp = True
                elif paramValues[1] == "False":
                    temp = False

            # TODO: 字符串转换时很麻烦
            if paramValues[2] == "str" or paramValues[2] == "bool" or paramValues[2] == "int":
                params[paramValues[0]] = (eval(paramValues[2])(temp), paramValues[3])
                continue
            else:
                params[paramValues[0]] = (eval(paramValues[2])(eval(temp)), paramValues[3])

        self._strConfig.setParams(params)

        # ----------------持仓设置-------------------
        pos_config = self.readPositionConfig()
        self._strConfig.setAutoSyncPos(pos_config)

        self.config = self._strConfig.getConfig()
        # print("-----------: ", self.config)

        # -------------保存用户配置--------------------------
        # 将绝对路径转为相对路径
        strategyPath = self._strategyPath
        cwdPath = os.getcwd()
        path_ = os.path.relpath(strategyPath, cwdPath)
        userConfig = {
            path_: {
                VUser: user,
                VInitFund: initFund,
                VDefaultType: defaultType,
                VDefaultQty: defaultQty,
                VMinQty: minQty,
                # VHedge: hedge,
                VMargin: margin,
                VOpenType: openType,
                VCloseType: closeType,
                VOpenFee: openFee,
                VCloseFee: closeFee,
                VDirection: tradeDirection,
                VSlippage: slippage,
                VTimer: timer,
                VIsCycle: isCycle,
                VCycle: cycle,
                VIsKLine: isKLine,
                VIsMarket: isSnapShot,
                VIsTrade: isTrade,

                # VSampleVar: sampleVar,
                # VBeginDate: beginDate,
                # VFixQty: fixQty,

                VSendOrderMode: sendOrderMode,
                VIsActual: isActual,
                VIsAlarm: isAlarm,
                VIsPop: isPop,
                VIsOpenTimes: isOpenTimes,
                VOpenTimes: openTimes,
                VIsConOpenTimes: isConOpenTimes,
                VConOpenTimes: conOpenTimes,
                VCanClose: canClose,
                VCanOpen: canOpen,

                # VParams: params,
                VContSettings: contsInfo
            }
        }

        # 将配置信息保存到本地文件
        self.writeConfig(userConfig)
        config = self.getConfig()
        if config:  # 获取到config
            if not self._paramFlag:
                self._control._request.loadRequest(strategyPath, config)
                self._control.logger.info("load strategy")
            else:
                self._control._request.strategyParamRestart(self._paramFlag, config)
                self._control.logger.info("Restarting strategy by new paramters")
        self._master.titleBar.closeWindow()

    def readConfig(self):
        """读取配置文件"""
        if os.path.exists(r"./config/loadconfigure.json"):
            with open(r"./config/loadconfigure.json", "r", encoding="utf-8") as f:
                try:
                    result = json.loads(f.read())
                except json.decoder.JSONDecodeError:
                    return None
                else:
                    return result
        else:
            filePath = os.path.abspath(r"./config/loadconfigure.json")
            f = open(filePath, 'w')
            f.close()

    def writeConfig(self, configure):
        """写入配置文件"""
        # 将文件内容追加到配置文件中
        try:
            config = self.readConfig()
        except:
            config = None
        if config:
            for key in configure:
                config[key] = configure[key]
                break
        else:
            config = configure

        with open(r"./config/loadconfigure.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(config, indent=4))

    def readPositionConfig(self):
        """读取持仓配置文件"""
        if os.path.exists(r"./config/loadposition.json"):
            with open(r"./config/loadposition.json", "r", encoding="utf-8") as f:
                try:
                    result = json.loads(f.read())
                except json.decoder.JSONDecodeError:
                    return None
                else:
                    return result
        else:
            filePath = os.path.abspath(r"./config/loadposition.json")
            f = open(filePath, 'w')
            f.close()

    def getConfig(self):
        """获取用户配置的config"""
        return self.config

    def getTextConfigure(self):
        """从配置文件中得到配置信息"""
        try:
            configure = self.readConfig()
        except EOFError:
            configure = None

        # key = self._control.getEditorText()["path"]
        cwdPath = os.getcwd()
        key = os.path.relpath(self._strategyPath, cwdPath)
        if configure:
            if key in configure:
                return configure[key]
        return None

    def setDefaultConfigure(self):
        conf = self.getTextConfigure()
        if conf:
            # self.user.set(conf[VUser]),
            self.initFundlineEdit.setText(conf[VInitFund]),
            self.defaultOrderComboBox.setCurrentText(conf[VDefaultType]),
            self.defaultOrderLineEdit.setText(conf[VDefaultQty]),
            self.miniOrderLineEdit.setText(conf[VMinQty]),
            # self.hedge.set(conf[VHedge]),
            self.marginRateLineEdit.setText(conf[VMargin]),

            self.openTypeComboBox.setCurrentText(conf[VOpenType]),
            self.closeTypeComboBox.setCurrentText(conf[VCloseType]),
            self.openFeeRateLineEdit.setText(conf[VOpenFee]),
            self.closeFeeRateLineEdit.setText(conf[VCloseFee]),
            self.tradeDirectionComboBox.setCurrentText(conf[VDirection]),
            self.slippageLineEdit.setText(conf[VSlippage]),

            self.cycleCheckBox.setChecked(conf[VIsCycle]),
            self.cycleLineEdit.setText(conf[VCycle]),

            if self.openTypeComboBox.currentText() == "固定值":
                self.label71.hide()
            else:
                self.label71.show()
            if self.closeTypeComboBox.currentText() == "固定值":
                self.label91.hide()
            else:
                self.label91.show()

            # 定时触发通过函数设置
            if conf[VTimer] != '':
                for t in conf[VTimer].split('\n'):
                    self.timerListWidget.addItem(t)   # todo

            self.KLineCheckBox.setChecked(conf[VIsKLine]),
            self.snapShotCheckBox.setChecked(conf[VIsMarket]),
            self.tradeCheckBox.setChecked(conf[VIsTrade]),

            # self.sampleVar.set(conf[VSampleVar]),
            # self.beginDate.set(conf[VBeginDate]),
            # self.fixQty.set(conf[VFixQty]),

            if conf[VSendOrderMode]:
                self.sendOrderRealtime.setChecked(False)
                self.sendOrderKStable.setChecked(True)
            else:
                self.sendOrderRealtime.setChecked(True)
                self.sendOrderKStable.setChecked(False)
            self.actualCheckBox.setChecked(conf[VIsActual]),
            try:
                self.alarmCheckBox.setChecked(conf[VIsAlarm])
            except KeyError as e:
                self.alarmCheckBox.setChecked(0)

            try:
                self.allowCheckBox.setChecked(conf[VIsPop])
            except KeyError as e:
                self.allowCheckBox.setChecked(0)

            self.openTimesCheckBox.setChecked(conf[VIsOpenTimes]),
            self.openTimesLineEdit.setText(conf[VOpenTimes]),
            self.isConOpenTimesCheckBox.setChecked(conf[VIsConOpenTimes]),
            self.isConOpenTimesLineEdit.setText(conf[VConOpenTimes]),
            self.canCloseCheckBox.setChecked(conf[VCanClose]),
            self.canOpenCheckBox.setChecked(conf[VCanOpen]),
            if self.isConOpenTimesCheckBox.checkState() == Qt.Unchecked:
                self.isConOpenTimesLineEdit.setText("不限制")
                self.isConOpenTimesLineEdit.setEnabled(False)
            if self.openTimesCheckBox.checkState() == Qt.Unchecked:
                self.openTimesLineEdit.setText("不限制")
                self.openTimesLineEdit.setEnabled(False)

            # 用户配置参数信息
            # 若保存的设置中用户参数为空，则不对self._userParam赋值
            try:
                if conf[VParams]:
                    self._userParam = conf[VParams]
                    for v in self._userParam:
                        self.insert_params(v)
            except KeyError as e:
                pass
                # traceback.print_exc()
            # TODO: DefaultSample
            try:
                if conf[VContSettings]:
                    self._contsInfo = conf[VContSettings]
                    for v in self._contsInfo:
                        self.insert_contract_row(v)
            except KeyError as e:
                pass
                # traceback.print_exc()

    def insert_contract_row(self, values):
        """在合约table中插入一行"""
        row = self.contractTableWidget.rowCount()
        self.contractTableWidget.setRowCount(row + 1)
        for j in range(len(values)):
            item = QTableWidgetItem(str(values[j]))
            item.setTextAlignment(Qt.AlignCenter)
            self.contractTableWidget.setItem(row, j, item)

    def insert_params(self, values):
        """在参数table中插入一行"""
        row = self.paramsTableWidget.rowCount()
        self.paramsTableWidget.setRowCount(row + 1)
        for j in range(len(values)):
            item = QTableWidgetItem(str(values(j)))
            self.paramsTableWidget.setItem(row, j, item)


class ContractWin(QWidget):
    confirm_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout()  # 主布局

        h_spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        h_spacerItem6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        h_layout1 = QHBoxLayout()
        label1 = QLabel('商品代码：')
        self.contractCodeLineEdit = QLineEdit()
        self.contractCodeLineEdit.setFixedWidth(200)
        self.contractCodeLineEdit.setFocusPolicy(Qt.NoFocus)
        self.select = QPushButton('选择')
        self.select.setFixedWidth(60)
        h_layout1.addWidget(label1)
        h_layout1.addWidget(self.contractCodeLineEdit)
        h_layout1.addWidget(self.select)
        h_layout1.addItem(h_spacerItem1)
        h_layout1.setSpacing(10)
        h_layout1.setContentsMargins(10, 0, 10, 0)

        h_layout2 = QHBoxLayout()
        label2 = QLabel('K线类型：')
        self.kLineTypeComboBox = QComboBox()
        self.kLineTypeComboBox.addItems(['分笔', '秒', '分钟', '日线'])
        self.kLineTypeComboBox.setCurrentIndex(2)
        h_layout2.addWidget(label2)
        h_layout2.addWidget(self.kLineTypeComboBox)
        h_layout2.addItem(h_spacerItem2)
        h_layout2.setSpacing(10)
        h_layout2.setContentsMargins(10, 0, 10, 0)

        h_layout3 = QHBoxLayout()
        label3 = QLabel('K线周期：')
        self.kLinePeriodComboBox = QComboBox()
        self.kLinePeriodComboBox.addItems(['1', '2', '3', '5', '10', '15', '30', '60', '120'])
        h_layout3.addWidget(label3)
        h_layout3.addWidget(self.kLinePeriodComboBox)
        h_layout3.addItem(h_spacerItem3)
        h_layout3.setSpacing(10)
        h_layout3.setContentsMargins(10, 0, 10, 0)

        # label 对齐
        label1.setFixedWidth(80)
        label2.setFixedWidth(80)
        label3.setFixedWidth(80)
        self.kLineTypeComboBox.setFixedWidth(55)
        self.kLinePeriodComboBox.setFixedWidth(55)

        # -------------运算起始点-----------------------------
        h_layout4 = QHBoxLayout()
        self.groupBox = QGroupBox('运算起始点')
        self.groupBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        groupbox_layout = QVBoxLayout()
        h_layout41 = QHBoxLayout()
        self.AllkLineRadioButton = QRadioButton('所有K线')
        h_layout41.addWidget(self.AllkLineRadioButton)

        h_layout42 = QHBoxLayout()
        self.startDateRadioButton = QRadioButton('起始日期')
        self.startDateLineEdit = QLineEdit()
        label42 = QLabel('格式(YYYYMMDD)')
        label42.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h_layout42.addWidget(self.startDateRadioButton)
        h_layout42.addWidget(self.startDateLineEdit)
        h_layout42.addWidget(label42)
        h_layout42.addItem(h_spacerItem4)

        h_layout43 = QHBoxLayout()
        self.qtyRadioButton = QRadioButton('固定根数')
        self.qtyRadioButton.setChecked(True)
        self.qtylineEdit = QLineEdit('2000')
        self.qtylineEdit.setMaximumWidth(60)
        label43 = QLabel('根')
        label43.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h_layout43.addWidget(self.qtyRadioButton)
        h_layout43.addWidget(self.qtylineEdit)
        h_layout43.addWidget(label43)
        h_layout43.addItem(h_spacerItem5)

        h_layout44 = QHBoxLayout()
        self.historyRadioButton = QRadioButton('不执行历史K线')
        h_layout44.addWidget(self.historyRadioButton)

        groupbox_layout.addLayout(h_layout41)
        groupbox_layout.addLayout(h_layout42)
        groupbox_layout.addLayout(h_layout43)
        groupbox_layout.addLayout(h_layout44)
        self.groupBox.setLayout(groupbox_layout)
        h_layout4.addWidget(self.groupBox)

        h_layout4.setSpacing(10)
        h_layout4.setContentsMargins(10, 0, 10, 0)

        h_layout5 = QHBoxLayout()
        self.confirm = QPushButton('确定')
        self.confirm.setMinimumWidth(80)
        self.cancel = QPushButton('取消')
        self.cancel.setMinimumWidth(80)
        h_layout5.setSpacing(10)
        h_layout5.setContentsMargins(0, 10, 20, 0)
        h_layout5.addItem(h_spacerItem6)
        h_layout5.addWidget(self.confirm)
        h_layout5.addWidget(self.cancel)

        main_layout.addLayout(h_layout1)
        main_layout.addLayout(h_layout2)
        main_layout.addLayout(h_layout3)
        main_layout.addLayout(h_layout4)
        main_layout.addLayout(h_layout5)

        self.setLayout(main_layout)
        # self.setMinimumSize(310, 300)

        self.kLineTypeComboBox.currentIndexChanged.connect(self.valid)
        self.qtylineEdit.setValidator(QtGui.QIntValidator())
        self.confirm.clicked.connect(self.valid_contract)
        self.row = -1

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def valid(self, index):
        if index == 0:
            self.kLinePeriodComboBox.setItemText(0, "0")
            self.kLinePeriodComboBox.setCurrentIndex(0)
            self.kLinePeriodComboBox.setEnabled(False)
        else:
            self.kLinePeriodComboBox.setItemText(0, "1")
            self.kLinePeriodComboBox.setEnabled(True)

    def valid_contract(self):
        if not self.contractCodeLineEdit.text():
            MyMessageBox.warning(self, '提示', '请先选择合约！！！', QMessageBox.Ok)
            return
        if self.startDateRadioButton.isChecked():
            dateFormat = self._isDateFormat(self.startDateLineEdit.text())
            if not dateFormat:
                return
        if self.qtyRadioButton.isChecked():
            try:
                assert int(self.qtylineEdit.text())
            except:
                MyMessageBox.warning(self, '提示', '固定根数输入不合法，请重新输入！！！', QMessageBox.Ok)
                return
        self.confirm_signal.emit(self.get_contract_policy())
        self.parent().close()

    def _isDateFormat(self, date):
        """
        判断用户输入的日期格式是否正确，正确则将该日期返回，错误则给出提示信息
        :param date: 标准格式：'YYYYMMDD'
        :return:
        """
        if len(date) > 8 or len(date) < 8:
            MyMessageBox.information(self, "提示", "日期应为8位长度", QMessageBox.Ok)
            return
        else:
            # TODO: 还需要判断日期是否是合法日期
            try:
                time = parse(date)
            except ValueError:
                MyMessageBox.information(self, "提示", "日期为非法日期", QMessageBox.Ok)
                return
            else:
                if time > datetime.now():
                    MyMessageBox.information(self, "提示", "日期不能大于今天", QMessageBox.Ok)
                    return
                else:
                    return date

    def get_contract_policy(self):
        """获取商品属性"""
        kLineCount = 0
        beginTime = ''
        allK = False
        useSample = False
        # ----------------商品代码-------------------
        contract = self.contractCodeLineEdit.text()

        # ----------------K线类型--------------------
        index = self.kLineTypeComboBox.currentIndex()
        rule = {0: 'T', 1: 'S', 2: 'M', 3: 'D'}
        KLineType = rule.get(index)

        # ----------------K线周期--------------------
        KLineSlice = self.kLinePeriodComboBox.currentText()
        if KLineType == 'T':
            KLineSlice = 0
        # TODO K线选择分笔时候K线周期应传的值

        # ----------------运算起始点-----------------
        if self.AllkLineRadioButton.isChecked():
            allK = True
        elif self.startDateRadioButton.isChecked():
            beginTime = self.startDateLineEdit.text()
            beginTime = parse(beginTime).strftime("%Y-%m-%d")
        elif self.qtyRadioButton.isChecked():
            kLineCount = int(self.qtylineEdit.text())
        elif self.historyRadioButton.isChecked():
            useSample = True  # TODO 选中不执行历史K线时候的值为False还是True

        return {
            'row': self.row,  # 标志位，为-1是新增合约，其他为更新合约
            'contract': contract,
            'KLineType': KLineType,
            'KLineSlice': KLineSlice,
            'BeginTime': beginTime,  # 运算起始点-起始日期
            'KLineCount': kLineCount,  # 运算起始点-固定根数
            'AllK': allK,  # 运算起始点-所有K线
            'UseSample': useSample,  # 运算起始点-不执行历史K线
            # 'Trigger': trigger     # 是否订阅历史K线  TODO trigger
        }


class ContractSelect(QWidget):
    exchangeList = ["SPD", "ZCE", "DCE", "SHFE", "INE", "CFFEX",
                    "CME", "COMEX", "LME", "NYMEX", "HKEX", "CBOT", "ICUS", "ICEU", "SGX"]
    commodityType = {"P": "现货", "Y": "现货", "F": "期货", "O": "期权",
                     "S": "跨期套利", "M": "品种套利", "s": "", "m": "",
                     "y": "", "T": "股票", "X": "外汇",
                     "I": "外汇", "C": "外汇"}
    # 外盘保留品种
    FCommodity = {"NYMEX": ["美原油"],
                  "COMEX": ["美铜", "美黄金"],
                  "HKEX": ["恒指", "小恒指", "H股指", "美元兑人民币", "小H股指"],
                  "CME": ["小标普", "小纳指"],
                  "CBOT": ["小道指", "美黄豆", "美豆粕", "美玉米"],
                  "ICUS": ["糖11号", "美棉花"],
                  "ICEU": ["布伦特原油", "富时指数"],
                  "SGX": ["A50指数"]}

    def __init__(self, exchange, commodity, contract, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout()

        h_spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout1 = QHBoxLayout()
        self.contract_tree = QTreeWidget()
        self.contract_child_tree = QTreeWidget()
        self.choice_tree = QTreeWidget()
        layout1.addWidget(self.contract_tree)
        layout1.addWidget(self.contract_child_tree)
        layout1.addWidget(self.choice_tree)
        layout1.setSpacing(1)

        layout2 = QHBoxLayout()
        self.confirm = QPushButton('确定')
        self.confirm.setMinimumWidth(60)
        self.cancel = QPushButton('取消')
        self.cancel.setMinimumWidth(60)
        layout2.setSpacing(0)
        layout2.setContentsMargins(0, 10, 20, 0)
        layout2.addItem(h_spacerItem)
        layout2.addWidget(self.confirm)
        layout2.addWidget(self.cancel)

        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.setContentsMargins(0, 0, 0, 10)

        self.setLayout(main_layout)
        self.contract_tree.setColumnCount(2)
        self.contract_tree.setHeaderHidden(True)
        self.contract_tree.hideColumn(1)
        self.contract_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.contract_child_tree.setColumnCount(1)
        self.contract_child_tree.setHeaderHidden(True)
        self.choice_tree.setColumnCount(1)
        self.choice_tree.setHeaderHidden(True)
        self.contract_tree.clicked.connect(self.load_child_contract)  # 加载分类下的合约
        self.choice_tree.doubleClicked.connect(self.clear_choice)  # 双击选择的合约
        self.contract_child_tree.doubleClicked.connect(self.load_choice)

        self._exchange = pd.DataFrame(exchange).drop_duplicates()
        self._commodity = pd.DataFrame(commodity, columns=["CommodityNo", "CommodityName"]).drop_duplicates()
        self._contract = pd.DataFrame(contract, columns=["ContractNo"]).drop_duplicates()
        self.load_contract()

        # 设置无边框
        self.setWindowFlags(Qt.FramelessWindowHint)

    def load_contract(self):
        for exchangeNo in self.exchangeList:
            exchange = self._exchange.loc[self._exchange.ExchangeNo == exchangeNo]
            root = QTreeWidgetItem(self.contract_tree)
            self.contract_tree.hideColumn(1)
            for _, exch in exchange.iterrows():
                exName = exch.ExchangeNo + "【" + exch.ExchangeName + "】"
                root.setText(0, exName)
                root.setText(1, exch.ExchangeNo)

            ePattern = r"\A" + exchangeNo
            commodity = self._commodity.loc[self._commodity.CommodityNo.str.contains(ePattern)]
            for _, comm in commodity.iterrows():
                # 仅保留外盘支持的品种
                if exchangeNo in self.FCommodity:
                    if comm.CommodityName not in self.FCommodity[exchangeNo]:
                        continue

                tempComm = comm.CommodityNo.split("|")
                if tempComm[1] in self.commodityType.keys():
                    if tempComm[0] == "SPD":
                        text = comm.CommodityName
                    else:
                        text = comm.CommodityName + " [" + self.commodityType[tempComm[1]] + "]"
                    child = QTreeWidgetItem(root)
                    child.setText(0, text)
                    child.setText(1, comm.CommodityNo)

    def load_child_contract(self):
        self.contract_child_tree.clear()
        items = self.contract_tree.selectedItems()
        for item in items:
            commodityNo = []
            exchangeNo = []
            if item.parent():
                commodityNo.append(item.text(1))
                exchangeNo.append(item.parent().text(1))
                commodityNoZ = commodityNo[0]
                temp = commodityNo[0].split("|")
                if temp[1] == "F":
                    temp[1] = "Z"
                    commodityNoZ = "|".join(temp)

                ePattern = r"\A" + exchangeNo[0] + "\|"
                cPattern = r"\A" + "\|".join(commodityNo[0].split("|")) + "\|"
                cZPattern = r"\A" + "\|".join(commodityNoZ.split("|")) + "\|"
                contract = self._contract.loc[
                    (self._contract.ContractNo.str.contains(ePattern))
                    & (
                            (self._contract.ContractNo.str.contains(cPattern))
                            |
                            (self._contract.ContractNo.str.contains(cZPattern))
                    )
                    ]
                for index, row in contract.iterrows():
                    root = QTreeWidgetItem(self.contract_child_tree)
                    root.setText(0, row["ContractNo"])

    def load_choice(self):
        item = self.contract_child_tree.currentItem()
        if self.choice_tree.topLevelItemCount() == 0:
            root = QTreeWidgetItem(self.choice_tree)
            root.setText(0, item.text(0))
        else:
            MyMessageBox.warning(self, '提示', '选择的合约数不能超过1个！！！', QMessageBox.Ok)
        pass

    def clear_choice(self):
        self.choice_tree.clear()


class QuantApplication(QWidget):

    exitSignal = pyqtSignal()
    positionSignal = pyqtSignal(list)
    pathSignal = pyqtSignal(str)

    def __init__(self, control, master=None):
        super().__init__(master)

        self.exitSignal.connect(self.show_warn)
        self.positionSignal.connect(self.updateSyncPosition)
        self.pathSignal.connect(self.focus_tree_item)
        self.init_settings()

        # 初始化控制器
        self._controller = control
        self._master = master
        self._logger = self._controller.get_logger()

        self.reportView = self._controller.reportView
        # 回测报告窗口句柄
        self.reportWnd = self._controller.reportWnd

        self.hbox = QHBoxLayout()
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.hbox.setSpacing(0)
        # self.topLayout = QGridLayout()  # 上方布局
        # self.bottomLayout = QGridLayout()  # 下方布局
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(0)
        self.main_splitter.setChildrenCollapsible(False)  # 设置下限，不隐藏
        self.main_splitter.setContentsMargins(0, 0, 0, 0)
        self.left_splitter = QSplitter(Qt.Vertical)
        self.left_splitter.setHandleWidth(1)
        self.left_splitter.setChildrenCollapsible(False)
        self.left_splitter.setContentsMargins(0, 0, 0, 0)
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.setHandleWidth(0)
        self.right_splitter.setChildrenCollapsible(False)
        self.right_splitter.setContentsMargins(0, 0, 0, 0)

        self.left_top_splitter = QSplitter(Qt.Horizontal)
        self.left_top_splitter.setHandleWidth(0)
        self.left_top_splitter.setChildrenCollapsible(False)
        self.left_top_splitter.setContentsMargins(0, 0, 0, 0)

        self.create_content_vbox()
        self.create_stragety_vbox()
        self.create_func_tab()
        self.create_tab()
        self.create_func_doc()
        # self.mainLayout = QGridLayout()  # 主布局为垂直布局
        # self.mainLayout.setSpacing(5)  # 主布局添加补白
        self.screen = QDesktopWidget().screenGeometry()  # 获取电脑屏幕分辨率
        self.width = self.screen.width()
        self.height = self.screen.height()
        # 左上部布局
        self.left_top_splitter.addWidget(self.strategy_vbox)
        self.left_top_splitter.addWidget(self.content_vbox)
        if self.settings.contains('left_top_splitter'):
            self.left_top_splitter.restoreState(self.settings.value('left_top_splitter'))
        else:
            self.left_top_splitter.setSizes([self.width * 0.8 * 0.2, self.width * 0.8 * 0.6])

        # 左部布局
        self.left_splitter.addWidget(self.left_top_splitter)
        self.left_splitter.addWidget(self.tab_widget)
        if self.settings.contains('left_splitter'):
            self.left_splitter.restoreState(self.settings.value('left_splitter'))
        else:
            self.left_splitter.setSizes([self.height * 0.75, self.height * 0.25])

        # 右部布局
        self.right_splitter.addWidget(self.func_tab)
        self.right_splitter.addWidget(self.func_doc)
        if self.settings.contains('right_splitter'):
            self.right_splitter.restoreState(self.settings.value('right_splitter'))
        else:
            self.right_splitter.setSizes([self.height * 0.75, self.height * 0.25])

        self.main_splitter.addWidget(self.left_splitter)
        self.main_splitter.addWidget(self.right_splitter)
        if self.settings.contains('main_splitter'):
            self.main_splitter.restoreState(self.settings.value('main_splitter'))
        else:
            self.main_splitter.setSizes([self.width * 0.4, self.width * 0.1])

        self.hbox.addWidget(self.main_splitter)
        self.setLayout(self.hbox)
        # self.setGeometry(screen.width() * 0.1, screen.height() * 0.1, screen.width() * 0.8,
        #                  screen.height() * 0.8)  # 设置居中和窗口大小
        # self.setWindowTitle('极星量化')
        # self.setWindowIcon(QIcon('icon/epolestar ix2.ico'))
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.show()

        # 策略信息
        self.strategy_path = None
        # 策略打开记录
        self.strategy_open_record = set()

        # with open(r'ui/qdark.qss', encoding='utf-8') as f:
        #     self.setStyleSheet(f.read())
        # self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._controller.update_log)
        self.timer.timeout.connect(self._controller.update_mon)
        self.timer.start(1000)

    def init_settings(self):
        self.settings = QSettings('config/settings.ini', QSettings.IniFormat)

    def close_app(self):
        self.save_settings()
        self._controller.quitThread()
        self._controller.mainWnd.titleBar.closeWindow()

    def save_edit_strategy(self):
        question = QMessageBox(self)
        if self.contentEdit.modify_count():
            question.setText('有策略已被修改，退出前是否保存？\t\t')
            question.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        else:
            question.setText('您确定要退出本程序吗？\t\t\t')
            question.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        question.setIcon(QMessageBox.Question)
        question.setWindowTitle('极星量化')

        reply = question.exec_()
        if reply == QMessageBox.Yes:
            self.contentEdit.on_saveMdySignal.connect(self.close_app)
            self.contentEdit.save_mdy()
        elif reply == QMessageBox.No or reply == QMessageBox.Ok:
            self.close_app()
        elif reply == QMessageBox.Cancel:
            pass


    def save_settings(self):
        """保存界面设置"""
        self.settings.setValue('left_top_splitter', self.left_top_splitter.saveState())
        self.settings.setValue('left_splitter', self.left_splitter.saveState())
        self.settings.setValue('right_splitter', self.right_splitter.saveState())
        self.settings.setValue('main_splitter', self.main_splitter.saveState())
        self.settings.setValue(
            'theme', 'vs' if self._controller.mainWnd.getWinThese() == '浅色' else 'vs-dark')

    def init_control(self):
        self._exchange = self._controller.model.getExchange()
        self._commodity = self._controller.model.getCommodity()
        self._contract = self._controller.model.getContract()
        self._userNo = self._controller.model.getUserNo()

    def create_stragety_vbox(self):
        # 策略树
        self.strategy_vbox = QFrame()
        label = QLabel(' 策略')
        label.setObjectName("Strategy")
        label.setContentsMargins(0, 0, 0, 0)
        self.strategy_layout = QVBoxLayout()
        self.strategy_layout.setContentsMargins(0, 0, 0, 0)
        self.strategy_layout.setSpacing(0)
        self.model = QFileSystemModel()
        self.strategy_tree = Tree(self.model, self)
        self.strategy_tree.setObjectName("StrategyTree")
        # self.strategy_tree = Tree(strategy_path)
        # self.model.setRootPath(QtCore.QDir.rootPath())
        self.model.setRootPath(strategy_path)
        self.model.setNameFilterDisables(False)
        self.proxyModel = MySortFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.strategy_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.strategy_tree.setModel(self.proxyModel)
        self.strategy_tree.setRootIndex(self.proxyModel.mapFromSource(self.model.index(strategy_path)))
        # self.strategy_tree.setModel(self.model)
        # TODO: 拖动！！
        # self.strategy_tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.strategy_tree.setRootIndex(self.model.index(strategy_path))
        # self.strategy_tree.setColumnCount(1)
        self.model.setReadOnly(False)
        self.model.setNameFilterDisables(False)
        self.model.setFilter(QDir.Dirs | QDir.Files | QDir.NoDotAndDotDot)
        self.model.setIconProvider(FileIconProvider())
        self.strategy_tree.setHeaderHidden(True)
        self.strategy_tree.hideColumn(1)
        self.strategy_tree.hideColumn(2)
        self.strategy_tree.hideColumn(3)

        self.strategy_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.strategy_tree.customContextMenuRequested[QPoint].connect(self.strategy_tree_right_menu)

        self.strategy_tree.doubleClicked.connect(self.strategy_tree_clicked)
        self.strategy_layout.addWidget(label)
        self.strategy_layout.addWidget(self.strategy_tree)
        self.strategy_vbox.setLayout(self.strategy_layout)

    def get_menu_style(self):
        if self._controller.mainWnd.getWinThese() == THESE_STATE_DARK:
            style_path = MENUDARKSTYLE
        else:
            style_path = MENUWHITESTYLE
        with open(style_path, 'r', encoding='utf-8') as f:
            style = f.read()
        return style

    def focus_tree_item(self, path):
        if os.path.exists(path):
            index = self.model.index(path)
            item_path = self.model.filePath(index)
            self.strategy_tree.setCurrentIndex(index)
            self.strategy_path = path
            if not os.path.isdir(item_path):
                self.contentEdit.sendOpenSignal(item_path)

    # 策略右键菜单
    def strategy_tree_right_menu(self, point):
        self.strategy_tree.popMenu = QMenu()
        self.strategy_tree.popMenu.setStyleSheet(self.get_menu_style())

        self.strategy_tree.addType = QMenu(self.strategy_tree.popMenu)
        self.strategy_tree.addType.setTitle('新建')
        import_file = QAction('导入')
        rename = QAction('重命名', self.strategy_tree)
        delete = QAction('删除', self.strategy_tree)
        add_strategy = QAction('新建策略')
        add_group = QAction('新建分组')
        start_file = QAction('打开文件所在位置', self.strategy_tree)
        self.strategy_tree.popMenu.addAction(import_file)
        self.strategy_tree.popMenu.addMenu(self.strategy_tree.addType)
        self.strategy_tree.addType.addAction(add_strategy)
        self.strategy_tree.addType.addAction(add_group)
        self.strategy_tree.popMenu.addAction(rename)
        self.strategy_tree.popMenu.addAction(delete)
        self.strategy_tree.popMenu.addAction(start_file)

        # 右键动作
        action = self.strategy_tree.popMenu.exec_(self.strategy_tree.mapToGlobal(point))
        if action == import_file:
            index = self.strategy_tree.currentIndex()
            model = index.model()  # 请注意这里可以获得model的对象
            index = model.mapToSource(index)  # 将index转化为过滤器的模型的index
            item_path = self.model.filePath(index)
            if item_path:
                if not os.path.isdir(item_path):
                    item_path = os.path.split(item_path)[0]
                desktop = os.path.join(os.path.expanduser("~"), 'Desktop')
                fname, ftype = QFileDialog.getOpenFileName(self, "打开...", desktop, "python文件(*.py *pyw)")
                if fname:
                    _path = item_path + '/' + os.path.split(fname)[1]
                    if os.path.exists(_path):
                        reply = MyMessageBox.question(self, '提示', '所选的分组中存在同名文件，是否覆盖？', QMessageBox.Ok | QMessageBox.Cancel)
                        if reply == QMessageBox.Ok:
                            shutil.copy(fname, _path)
                    else:
                        shutil.copy(fname, _path)
                    self.contentEdit.sendOpenSignal(_path)
                    self.strategy_path = _path
        elif action == add_strategy:
            index = self.strategy_tree.currentIndex()
            model = index.model()  # 请注意这里可以获得model的对象
            index = model.mapToSource(index)  # 将index转化为过滤器的模型的index
            item_path = self.model.filePath(index)
            # item_path = model.filePath(index)
            if item_path and os.path.isdir(item_path):
                value = ''
                while True:
                    value, ok = getText(self, '新增', '策略名称：')
                    if not value.strip().endswith('.py'):
                        path = os.path.join(item_path, value.strip() + '.py')
                    else:
                        path = os.path.join(item_path, value.strip())
                    if os.path.exists(path) and ok:
                        MyMessageBox.warning(self, '提示', '策略名%s在选择的分组已经存在！！！' % value.strip(), QMessageBox.Ok)
                    elif not ok:
                        break
                    else:
                        with open(path, 'w', encoding='utf-8') as w:
                            w.write('import talib\n'
                                    '\n\n'
                                    'def initialize(context): \n    pass\n\n\n'
                                    'def handle_data(context):\n    pass\n\n\n'
                                    'def hisover_callback(context):\n    """历史阶段结束策略调用该函数"""\n    pass\n\n\n'
                                    'def exit_callback(context):\n    """策略停止时调用该函数"""\n    pass\n\n\n'
                                    )
                        self.model.directoryLoaded.connect(lambda: self.focus_tree_item(path))
                        self.strategy_tree.expand(index)
                        break
            elif not os.path.isdir(item_path):
                value = ''
                while True:
                    value, ok = getText(self, '新建', '策略名称：')
                    if not value.strip().endswith('.py'):
                        path = os.path.join(os.path.split(item_path)[0], value.strip() + '.py')
                    else:
                        path = os.path.join(os.path.split(item_path)[0], value.strip())

                    if os.path.exists(path) and ok:
                        MyMessageBox.warning(self, '提示', '策略名在选择的分组%s已经存在！！！' % value, QMessageBox.Ok)
                    elif not ok:
                        break
                    else:
                        with open(path, 'w', encoding='utf-8') as w:
                            w.write('import talib\n'
                                    '\n\n'
                                    'def initialize(context):\n    pass\n\n\n'
                                    'def handle_data(context):\n    pass\n\n\n'
                                    'def hisover_callback(context):\n    """历史阶段结束策略调用该函数"""\n    pass\n\n\n'
                                    'def exit_callback(context):\n    """策略停止时调用该函数"""\n    pass\n\n\n'
                                    )
                        self.model.directoryLoaded.connect(lambda: self.focus_tree_item(path))
                        break
            else:
                MyMessageBox.warning(self, '提示', '请选择分组！！！', QMessageBox.Ok)

        elif action == add_group:
            value = ''
            flag = self.strategy_tree.indexAt(point)  # 判断鼠标点击位置标志位
            while True:
                if not flag.isValid():  # 鼠标点击位置不在目录树叶子上
                    item_path = strategy_path  # 新建文件夹位置在根目录
                else:
                    index = self.strategy_tree.currentIndex()
                    model = index.model()  # 请注意这里可以获得model的对象
                    index = model.mapToSource(index)  # 将index转化为过滤器的模型的index
                    item_path = self.model.filePath(index)
                    # item_path = model.filePath(index)
                value, ok = getText(self, '新建', '分组名称：')
                if os.path.isdir(item_path):
                    path = os.path.join(item_path, value)
                else:
                    path = os.path.join(os.path.split(item_path)[0], value)
                if os.path.exists(path) and ok:
                    MyMessageBox.warning(self, '提示', '分组%s已经存在！！！' % value, QMessageBox.Ok)
                elif not ok:
                    break
                else:
                    os.mkdir(path)
                    self.model.directoryLoaded.connect(lambda: self.focus_tree_item(path))
                    break

        elif action == start_file:
            index = self.strategy_tree.currentIndex()
            model = index.model()  # 请注意这里可以获得model的对象
            index = model.mapToSource(index)  # 将index转化为过滤器的模型的index
            item_path = self.model.filePath(index)
            # item_path = model.filePath(index)
            dir_name = os.path.dirname(item_path)
            os.startfile(dir_name)
        elif action == rename:
            index = self.strategy_tree.currentIndex()
            model = index.model()  # 请注意这里可以获得model的对象
            index = model.mapToSource(index)  # 将index转化为过滤器的模型的index
            item_path = self.model.filePath(index)
            # item_path = model.filePath(index)
            if not os.path.isdir(item_path):  # 修改策略名
                value = ''
                (file_path, filename) = os.path.split(item_path)
                while True:
                    value, ok = getText(self, '修改', '策略名称', filename)
                    if not value.strip().endswith('.py'):
                        new_path = '%s/%s.py' % (file_path, value.strip())
                    else:
                        new_path = '%s/%s' % (file_path, value.strip())
                    if os.path.exists(new_path) and ok:
                        MyMessageBox.warning(self, '提示', '策略名%s在此分组中已经存在！！！' % value.strip(), QMessageBox.Ok)
                    elif not ok:
                        break
                    else:
                        os.rename(item_path, new_path)
                        if item_path == self.strategy_path:
                            self.strategy_path = new_path
                        # 更新策略打开记录
                        if item_path in self.strategy_open_record:
                            self.strategy_open_record.remove(item_path)
                            self.strategy_open_record.add(new_path)
                        self.contentEdit.sendRenameSignal(item_path, new_path)
                        break
            else:
                value = ''
                (dir_path, dir_name) = os.path.split(item_path)
                while True:
                    value, ok = getText(self, '修改', '分组名称', dir_name)
                    new_path = '%s/%s' % (dir_path, value.strip())
                    if os.path.exists(new_path) and ok:
                        MyMessageBox.warning(self, '提示', '分组%s已经存在！！！' % value, QMessageBox.Ok)
                    elif not ok:
                        break
                    else:
                        # def allFilePath(rootDir, newDir):
                        #     """
                        #     :param rootDir: 原根目录
                        #     :param newPath: 修改后的根目录
                        #     :return:
                        #     """
                        #     for root, dirs, files in os.walk(rootDir):
                        #         for file in files:
                        #             print("dddd: ", file)
                        #             filePath = os.path.join(root, file)
                        #             if filePath in self.strategy_open_record:
                        #                 newFilePath = os.path.join(newDir, filePath)
                        #                 self.strategy_open_record.remove(filePath)
                        #                 self.strategy_open_record.add(os.path.join(newDir, filePath))
                        #                 self.contentEdit.sendRenameSignal(filePath, newFilePath)
                        #         for dir in dirs:
                        #             dirPath = os.path.join(root, dir)
                        #             newDirPath = os.path.join(newDir, dir)
                        #             allFilePath(dirPath, newDirPath)

                        os.rename(item_path, new_path)
                        if item_path == self.strategy_path:
                            self.strategy_path = new_path
                        # allFilePath(item_path, new_path)
                        break
        elif action == delete:
            index = self.strategy_tree.currentIndex()
            model = index.model()  # 请注意这里可以获得model的对象
            index = model.mapToSource(index)  # 将index转化为过滤器的模型的index
            item_path = self.model.filePath(index)
            # item_path = model.filePath(index)
            if item_path and os.path.isdir(item_path):
                reply = MyMessageBox.question(self, '提示', '确定删除分组及目录下的所有文件吗？', QMessageBox.Ok | QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    shutil.rmtree(item_path)

            elif item_path and not os.path.isdir(item_path):
                reply = MyMessageBox.question(self, '提示', '确定删除策略%s吗？' % os.path.split(item_path)[1], QMessageBox.Ok | QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.contentEdit.sendDeleteSignal(item_path)
                    os.remove(item_path)
            else:
                pass
        else:
            pass

    # QTextBrowser 右键菜单
    def user_log_right_menu(self, point):
        self.user_log_widget.popMenu = QMenu()
        self.user_log_widget.popMenu.setStyleSheet(self.get_menu_style())
        copy = QAction('复制')
        select_all = QAction('全选')
        clear = QAction('清除')

        self.user_log_widget.popMenu.addAction(copy)
        self.user_log_widget.popMenu.addAction(select_all)
        self.user_log_widget.popMenu.addAction(clear)

        # 右键动作
        action = self.user_log_widget.popMenu.exec_(self.user_log_widget.mapToGlobal(point))
        if action == copy:
            self.user_log_widget.copy()
        elif action == select_all:
            self.user_log_widget.selectAll()
        elif action == clear:
            self.user_log_widget.clear()

    def error_log_right_menu(self, point):
        self.error_info_widget.popMenu = QMenu()
        self.error_info_widget.popMenu.setStyleSheet(self.get_menu_style())
        copy = QAction('复制')
        select_all = QAction('全选')
        clear = QAction('清除')

        self.error_info_widget.popMenu.addAction(copy)
        self.error_info_widget.popMenu.addAction(select_all)
        self.error_info_widget.popMenu.addAction(clear)

        # 右键动作
        action = self.error_info_widget.popMenu.exec_(self.error_info_widget.mapToGlobal(point))
        if action == copy:
            self.error_info_widget.copy()
        elif action == select_all:
            self.error_info_widget.selectAll()
        elif action == clear:
            self.error_info_widget.clear()

    def signal_log_right_menu(self, point):
        self.signal_log_widget.popMenu = QMenu()
        self.signal_log_widget.popMenu.setStyleSheet(self.get_menu_style())
        copy = QAction('复制')
        select_all = QAction('全选')
        clear = QAction('清除')
        refresh = QAction('刷新')

        self.signal_log_widget.popMenu.addAction(copy)
        self.signal_log_widget.popMenu.addAction(select_all)
        self.signal_log_widget.popMenu.addAction(clear)
        self.signal_log_widget.popMenu.addAction(refresh)

        # 右键动作
        action = self.signal_log_widget.popMenu.exec_(self.signal_log_widget.mapToGlobal(point))
        if action == copy:
            self.signal_log_widget.copy()
        elif action == select_all:
            self.signal_log_widget.selectAll()
        elif action == clear:
            self.signal_log_widget.clear()
        elif action == refresh:
            self.loadSigLogFile()

    def sys_log_right_menu(self, point):
        self.sys_log_widget.popMenu = QMenu()
        self.sys_log_widget.popMenu.setStyleSheet(self.get_menu_style())
        copy = QAction('复制')
        select_all = QAction('全选')
        clear = QAction('清除')
        refresh = QAction('刷新')

        self.sys_log_widget.popMenu.addAction(copy)
        self.sys_log_widget.popMenu.addAction(select_all)
        self.sys_log_widget.popMenu.addAction(clear)
        self.sys_log_widget.popMenu.addAction(refresh)

        # 右键动作
        action = self.sys_log_widget.popMenu.exec_(self.sys_log_widget.mapToGlobal(point))
        if action == copy:
            self.sys_log_widget.copy()
        elif action == select_all:
            self.sys_log_widget.selectAll()
        elif action == clear:
            self.sys_log_widget.clear()
        elif action == refresh:
            self.loadSysLogFile()

    def func_doc_right_menu(self, point):
        self.func_content.popMenu = QMenu()
        self.func_content.popMenu.setStyleSheet(self.get_menu_style())
        copy = QAction('复制')
        select_all = QAction('全选')

        self.func_content.popMenu.addAction(copy)
        self.func_content.popMenu.addAction(select_all)

        # 右键动作
        action = self.func_content.popMenu.exec_(self.func_content.mapToGlobal(point))
        if action == copy:
            self.func_content.copy()
        elif action == select_all:
            self.func_content.selectAll()

    def create_content_vbox(self):
        # self.content_vbox = QGroupBox('内容')
        self.content_vbox = QWidget()
        self.content_layout = QGridLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.save_btn = QPushButton('保存')
        self.run_btn = QPushButton('运行')
        self.run_btn.setMaximumWidth(100)
        self.save_btn.setMaximumWidth(100)
        self.run_btn.setEnabled(False)
        # self.contentEdit = MainFrmQt("localhost", 8765, "pyeditor", os.path.join(os.getcwd(), 'quant\python_editor\editor.htm'))
        self.contentEdit = CodeEditor()
        self.contentEdit.setObjectName('contentEdit')
        if self.settings.contains('theme') and self.settings.value('theme') == 'vs-dark':
            self.contentEdit.load(
                QUrl.fromLocalFile(os.path.abspath(r'qtui/quant/python_editor/editor.htm')))
        else:
            self.contentEdit.load(
                QUrl.fromLocalFile(os.path.abspath(r'qtui/quant/python_editor/editor_vs.htm')))
        self.contentEdit.on_switchSignal.connect(self.switch_strategy_path)
        self.statusBar = QLabel()
        self.statusBar.setText("  极星9.5连接失败，请重新打开极星量化！")
        self.statusBar.setStyleSheet('color: #0062A3;')

        self.content_layout.addWidget(self.statusBar, 0, 0, 1, 1)
        self.content_layout.addWidget(self.run_btn, 0, 1, 1, 1)
        self.content_layout.addWidget(self.save_btn, 0, 2, 1, 1)
        self.content_layout.addWidget(self.contentEdit, 2, 0, 20, 3)
        self.content_vbox.setLayout(self.content_layout)
        self.run_btn.clicked.connect(self.emit_custom_signal)  # 改为提示用户保存当前的文件
        self.run_btn.clicked.connect(
            lambda: self.create_strategy_policy_win({}, self.strategy_path, False))
        self.save_btn.clicked.connect(self.emit_custom_signal)
        self.save_btn.setShortcut("Ctrl+S")  # ctrl + s 快捷保存

    def switch_strategy_path(self, path):
        self.strategy_path = path

    def set_run_btn_state(self, status):
        """
        设置运行按钮是否可用
        :param status: bool  (True: 可用, False: 不可用)
        :return:
        """
        self.run_btn.setEnabled(status)

    def emit_custom_signal(self):
        self.contentEdit.sendSaveSignal(self.strategy_path)

    def create_func_tab(self):
        # 函数列表
        # self.func_vbox = QGroupBox('函数')
        self.func_tab = QTabWidget()  # 通过tab切换目录、检索
        self.func_tab.setObjectName("FuncTab")
        self.func_tab.setContentsMargins(0, 0, 0, 0)
        self.search_widget = QWidget()
        self.func_layout = QVBoxLayout()
        self.func_layout.setSpacing(0)
        self.func_layout.setContentsMargins(0, 0, 0, 0)

        # 函数树结构
        self.func_tree = QTreeWidget()
        self.func_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.func_tree.setObjectName("FuncTree")
        self.func_tree.setColumnCount(2)
        self.func_tree.setHeaderLabels(['函数名', '函数介绍'])
        self.func_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)  # 设置列宽自适应
        self.func_tree.setHeaderHidden(True)
        for k, v in _all_func_.items():
            root = QTreeWidgetItem(self.func_tree)
            root.setText(0, k)
            root.setText(1, '')
            for i in v:
                child = QTreeWidgetItem(root)
                child.setText(0, i[0])
                child.setText(1, i[1])
        self.func_tree.clicked.connect(self.func_tree_clicked)

        # 函数检索
        self.search_line = QLineEdit()
        self.search_line.setObjectName("SearchLine")
        self.search_line.setPlaceholderText('请输入要搜索的函数名或介绍')
        self.search_line.textChanged.connect(self.search)
        # self.func_table = QTableWidget()
        # self.func_table.setColumnCount(2)

        # table数据
        func_list = []
        for k, v in _all_func_.items():
            func_list.extend(v)
        func_list.sort(key=lambda x: x[0])
        # self.func_table.setColumnCount(2)
        # self.func_table.setRowCount(len(func_list))
        # self.func_table.setHorizontalHeaderLabels(['函数名', '函数介绍'])
        # self.func_table.verticalHeader().setVisible(False)
        #
        # for i in range(len(func_list)):
        #     for j in range(len(func_list[i])):
        #         item = QTableWidgetItem(func_list[i][j])
        #         self.func_table.setItem(i, j, item)

        #######################################################
        self.search_tree = QTreeWidget()
        self.search_tree.setObjectName("SearchTree")
        self.search_tree.setColumnCount(2)
        self.search_tree.setHeaderLabels(['函数名', '函数介绍'])
        self.search_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.search_tree.setHeaderHidden(True)
        self.search_tree.clicked.connect(self.search_tree_clicked)

        # self.func_tree.setHeaderHidden(True)
        for v in func_list:
            root = QTreeWidgetItem(self.search_tree)
            root.setText(0, v[0])
            root.setText(1, v[1])
        # self.search_tree.setStyleSheet("branch {image:none;}")
        #######################################################

        self.func_layout.addWidget(self.search_line)
        self.func_layout.addWidget(self.search_tree)
        self.search_widget.setLayout(self.func_layout)

        self.func_tab.addTab(self.func_tree, '函数目录')
        self.func_tab.addTab(self.search_widget, '函数检索')

        # self.func_layout.addWidget(self.func_tab)
        # self.func_vbox.setLayout(self.func_layout)

    def create_tab(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setContentsMargins(0, 0, 0, 0)
        # 策略运行table
        self.strategy_table = QTableWidget()
        self.strategy_table.setRowCount(0)  # 行数
        self.strategy_table.setColumnCount(12)  # 列数
        self.strategy_table.verticalHeader().setMinimumSectionSize(5)
        self.strategy_table.verticalHeader().setDefaultSectionSize(25)
        self.strategy_table.horizontalHeader().setDefaultSectionSize(100)
        self.strategy_table.setColumnWidth(0, 40)
        self.strategy_table.setColumnWidth(2, 130)
        self.strategy_table.setColumnWidth(3, 150)
        self.strategy_table.verticalHeader().setVisible(False)
        self.strategy_table.setShowGrid(False)
        # self.strategy_table.horizontalHeader().setStretchLastSection(True)  # 最后一行自适应长度，充满界面
        self.strategy_table.horizontalHeader().setHighlightSections(False)  # 关闭高亮头
        self.strategy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.strategy_table.setEditTriggers(QTableView.NoEditTriggers)  # 不可编辑
        self.strategy_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置只有行选中
        self.strategy_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.strategy_table.setHorizontalHeaderLabels(["编号", "账号", "策略名称", "基准合约", "频率", "运行阶段", "运行模式",
                                                       "初始资金", "可用资金", "最大回撤", "累计收益", "胜率"])

        # ----------------------日志tab----------------------------------
        self.log_widget = QTabWidget()
        self.log_widget.setTabPosition(QTabWidget.South)
        self.user_log_widget = QTextBrowser()
        self.user_log_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.user_log_widget.customContextMenuRequested[QPoint].connect(self.user_log_right_menu)
        self.signal_log_widget = QTextBrowser()
        self.signal_log_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.signal_log_widget.customContextMenuRequested[QPoint].connect(self.signal_log_right_menu)
        self.sys_log_widget = QTextBrowser()
        self.sys_log_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sys_log_widget.customContextMenuRequested[QPoint].connect(self.sys_log_right_menu)
        self.log_widget.addTab(self.user_log_widget, '用户日志')
        self.log_widget.addTab(self.signal_log_widget, '信号日志')
        self.log_widget.addTab(self.sys_log_widget, '系统日志')
        self.log_widget.tabBarClicked.connect(self.loadSysLogFile)
        self.log_widget.tabBarClicked.connect(self.loadSigLogFile)
        # self.log_widget.currentChanged.connect(self.loadSysLogFile)

        # -----------------设置文本框变化的时候滚动条自动滚动到最底部-------------------
        # self.sys_log_widget.textChanged.connect(lambda: self.sys_log_widget.moveCursor(QTextCursor.End))
        # self.sys_log_widget.moveCursor(QTextCursor.End)
        self.error_info_widget = QTextBrowser()
        self.error_info_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.error_info_widget.customContextMenuRequested[QPoint].connect(self.error_log_right_menu)

        # -------------------组合监控----------------------------
        self.union_monitor = QWidget()
        self.union_monitor.setObjectName("UnionMonitor")
        self.union_layout = QGridLayout()
        self.one_key_sync = QPushButton('持仓一键同步')
        self.one_key_sync.setMinimumWidth(100)
        self.cbComboBox = QComboBox()
        self.cbComboBox.addItems(['对盘价', '最新价', '市价'])
        self.cbComboBox.currentIndexChanged.connect(self.valid_spin)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacerItem21 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
        spacerItem22 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
        spacerItem23 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
        spacerItem24 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.spin = QSpinBox()
        self.spin.setMinimum(1)
        self.spin.setMaximum(100)
        self.intervalCheckBox = QCheckBox('自动同步间隔')
        self.intervalCheckBox.stateChanged.connect(self.save_position_config)
        self.intervalCheckBox.stateChanged.connect(self.change_connection)  # 是否连接信号
        self.intervalSpinBox = QSpinBox()
        self.intervalSpinBox.setMinimum(500)
        self.intervalSpinBox.setMaximum(2147483647)
        self.intervalSpinBox.setMaximumWidth(80)
        self.intervalSpinBox.setSingleStep(100)
        self.reducePositionCheckBox = QCheckBox('仅自动减仓')
        self.union_layout.addItem(spacerItem21, 0, 0, 1, 1)
        self.union_layout.addWidget(self.one_key_sync, 0, 1, 1, 1)
        self.union_layout.addItem(spacerItem22, 0, 2, 1, 1)
        self.union_layout.addWidget(QLabel('同步设置：'), 0, 3, 1, 1)
        self.union_layout.addWidget(self.cbComboBox, 0, 4, 1, 1)
        self.union_layout.addWidget(QLabel('+'), 0, 5, 1, 1)
        self.union_layout.addWidget(self.spin, 0, 6, 1, 1)
        self.union_layout.addWidget(QLabel('跳'), 0, 7, 1, 1)
        self.union_layout.addItem(spacerItem23, 0, 8, 1, 1)
        self.union_layout.addWidget(self.intervalCheckBox, 0, 9, 1, 1)
        self.union_layout.addWidget(self.intervalSpinBox, 0, 10, 1, 1)
        self.union_layout.addWidget(QLabel('毫秒'), 0, 11, 1, 1)
        self.union_layout.addItem(spacerItem24, 0, 12, 1, 1)
        self.union_layout.addWidget(self.reducePositionCheckBox, 0, 13, 1, 1)
        self.union_layout.addItem(spacerItem, 0, 14, 1, 1)
        self.union_layout.setSpacing(5)
        self.union_layout.setContentsMargins(0, 0, 0, 0)

        self.one_key_sync.clicked.connect(lambda: self.save_position_config(True))

        # -----根据loadPositionConfig设置持仓更新参数-------
        config = self.readPositionConfig()
        if not config:
            self.intervalSpinBox.setValue(5000)
            config = {
                'OneKeySync': False,  # 一键同步
                'AutoSyncPos': self.intervalCheckBox.isChecked(),  # 是否自动同步
                'PriceType': self.cbComboBox.currentIndex(),  # 价格类型 0:对盘价, 1:最新价, 2:市价
                'PriceTick': self.spin.value(),  # 超价点数
                'OnlyDec': self.reducePositionCheckBox.isChecked(),  # 是否只做减仓同步
                'SyncTick': self.intervalSpinBox.value(),  # 同步间隔，毫秒
            }
            self.writePositionConfig(config)
        else:
            self.intervalCheckBox.setChecked(config.get('AutoSyncPos'))
            self.cbComboBox.setCurrentIndex(config.get('PriceType'))
            self.spin.setValue(config.get('PriceTick'))
            self.reducePositionCheckBox.setChecked(config.get('OnlyDec'))
            self.intervalSpinBox.setValue(config.get('SyncTick'))
        # -----持仓信息--------------
        self.pos_table = QTableWidget()
        self.pos_table.setRowCount(0)  # 行数
        self.pos_table.setColumnCount(13)  # 列数
        self.pos_table.verticalHeader().setMinimumSectionSize(5)
        self.pos_table.verticalHeader().setDefaultSectionSize(25)  # 设置行高
        self.pos_table.horizontalHeader().setDefaultSectionSize(80)
        self.pos_table.setColumnWidth(0, 150)
        self.pos_table.setColumnWidth(1, 150)
        self.pos_table.verticalHeader().setVisible(False)
        self.pos_table.setShowGrid(False)
        # self.pos_table.horizontalHeader().setStretchLastSection(True)  # 最后一列自动拉伸充满界面
        self.pos_table.horizontalHeader().setHighlightSections(False)  # 关闭水平头高亮
        self.pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 所有列自动拉伸，充满界面
        self.pos_table.horizontalHeader().setObjectName("PosTableHeader")
        self.pos_table.setEditTriggers(QTableView.NoEditTriggers)  # 不可编辑
        self.pos_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置只有行选中
        self.pos_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.pos_table.setHorizontalHeaderLabels(["账号", "合约", "账户仓", "策略仓", "仓差",
                                                  "策略多", "策略空", "策略今多", "策略今空", "账户多", "账户空", "账户今多", "账户今空"])
        self.union_layout.addWidget(self.pos_table, 1, 0, 1, 15)
        self.union_monitor.setLayout(self.union_layout)

        self.tab_widget.addTab(self.strategy_table, "策略运行")  # 策略运行tab
        self.tab_widget.addTab(self.log_widget, "运行日志")  # 运行日志tab
        self.tab_widget.addTab(self.error_info_widget, "错误信息")  # 错误信息志tab
        self.tab_widget.addTab(self.union_monitor, "组合监控")  # 组合监控tab

        self.strategy_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.strategy_table.customContextMenuRequested[QPoint].connect(self.strategy_table_right_menu)

    def strategy_table_right_menu(self, point):
        self.strategy_table.popMenu = QMenu()
        self.strategy_table.popMenu.setStyleSheet(self.get_menu_style())
        run = QAction('启动', self.strategy_table)
        stop = QAction('停止', self.strategy_table)
        delete = QAction('删除', self.strategy_table)
        report = QAction('投资报告', self.strategy_table)
        onSignal = QAction('图表展示', self.strategy_table)
        policy = QAction('属性设置', self.strategy_table)
        selectAll = QAction('全选', self.strategy_table)

        self.strategy_table.popMenu.addAction(run)
        self.strategy_table.popMenu.addAction(stop)
        self.strategy_table.popMenu.addAction(delete)
        self.strategy_table.popMenu.addAction(report)
        self.strategy_table.popMenu.addAction(onSignal)
        self.strategy_table.popMenu.addAction(policy)
        self.strategy_table.popMenu.addAction(selectAll)

        action = self.strategy_table.popMenu.exec_(self.strategy_table.mapToGlobal(point))
        items = self.strategy_table.selectedItems()
        # strategy_id = self.strategy_table.item(row, 0).text()
        strategy_id_list = []
        for item in items:
            if self.strategy_table.indexFromItem(item).column() == 0:
                strategy_id_list.append(int(item.text()))
        if action == run:
            self._controller.resumeRequest(strategy_id_list)
        elif action == stop:
            self._controller.quitRequest(strategy_id_list)
        elif action == delete:
            self._controller.delStrategy(strategy_id_list)
        elif action == report:
            self._controller.generateReportReq(strategy_id_list)
        elif action == onSignal:
            self._controller.signalDisplay(strategy_id_list)
        elif action == policy:
            self._controller.paramSetting(strategy_id_list)
        elif action == selectAll:
            self.strategy_table.selectAll()
        else:
            pass

    def create_func_doc(self):
        self.func_doc = QWidget()
        self.func_doc_layout = QVBoxLayout()
        self.func_doc_layout.setSpacing(0)
        self.func_doc_layout.setContentsMargins(0, 0, 0, 0)
        self.func_doc_line = QLabel()
        self.func_doc_line.setText('函数简介')
        self.func_doc_line.setObjectName("FuncDetailLabel")
        self.func_content = QTextBrowser()
        self.func_content.setObjectName("FuncContent")
        self.func_content.setContextMenuPolicy(Qt.CustomContextMenu)
        self.func_content.customContextMenuRequested[QPoint].connect(self.func_doc_right_menu)
        self.func_doc_layout.addWidget(self.func_doc_line)
        self.func_doc_layout.addWidget(self.func_content)
        self.func_doc.setLayout(self.func_doc_layout)
        self.func_doc.setContentsMargins(0, 0, 0, 0)

    def strategy_tree_clicked(self):
        index = self.strategy_tree.currentIndex()
        model = index.model()
        index = model.mapToSource(index)  # 将index转化为过滤器的模型的index
        item_path = self.model.filePath(index)
        if not os.path.isdir(item_path):
            self.contentEdit.sendOpenSignal(item_path)
            self.strategy_open_record.add(item_path)
            self.strategy_path = item_path

    def func_tree_clicked(self):
        item = self.func_tree.currentItem()
        if item.parent():
            item_text = globals()['BaseApi'].__dict__.get(item.text(0), None).__doc__
            text = item_text.lstrip("\n") if item_text else ''
            # self.func_content.setText(text.replace(' ', ''))
            self.func_content.setText(text.replace("        ", ""))
            self.func_doc_line.setText(item.text(0))

    def search_tree_clicked(self):
        item = self.search_tree.currentItem()
        item_text = globals()['BaseApi'].__dict__.get(item.text(0), None).__doc__
        text = item_text.lstrip("\n") if item_text else ''
        # self.func_content.setText(text.replace(' ', ''))
        self.func_content.setText(text.replace("        ", ""))
        self.func_doc_line.setText(item.text(0))

    def search(self, word):
        self.search_tree.clear()
        # table数据
        func_list = []
        for k, v in _all_func_.items():
            for item in v:
                if word.lower() in item[0].lower() or word.lower() in item[1].lower():
                    func_list.append(item)
        func_list.sort(key=lambda x: x[0])

        for v in func_list:
            root = QTreeWidgetItem(self.search_tree)
            root.setText(0, v[0])
            root.setText(1, v[1])

    def create_strategy_policy_win(self, param, path, flag):
        # 运行点击槽函数，弹出策略属性设置窗口
        if path:
            pGeometry = self._controller.mainWnd.frameGeometry()
            self.main_strategy_policy_win = FramelessWindow()
            self.main_strategy_policy_win.resize(pGeometry.width() * 0.4, pGeometry.height() * 0.7)
            # self.main_strategy_policy_win.resize(560, 580)
            self.main_strategy_policy_win.center(pGeometry)
            self.strategy_policy_win = StrategyPolicy(self._controller, path, master=self.main_strategy_policy_win,
                                                      param=param, flag=flag)

            self.main_strategy_policy_win.hideTheseBtn()
            self.main_strategy_policy_win.titleBar.iconLabel.hide()
            self.main_strategy_policy_win.disabledMinimunBtn()
            self.main_strategy_policy_win.disabledMaximumBtn()
            self.main_strategy_policy_win.setWindowTitle('属性设置')
            self.main_strategy_policy_win.titleBar.buttonClose.clicked.connect(self.strategy_policy_win.close)
            self.main_strategy_policy_win.setWidget(self.strategy_policy_win)
            if self._controller.mainWnd.getWinThese() == '浅色':
                style = CommonHelper.readQss(WHITESTYLE)
            else:
                style = CommonHelper.readQss(DARKSTYLE)
            self.main_strategy_policy_win.setStyleSheet('')
            self.main_strategy_policy_win.setStyleSheet(style)
            # self.strategy_policy_win.confirm.clicked.connect(self.main_strategy_policy_win.close)  # todo
            self.strategy_policy_win.cancel.clicked.connect(self.main_strategy_policy_win.titleBar.closeWindow)
            self.strategy_policy_win.contractWin.select.clicked.connect(
                lambda: self.strategy_policy_win.contractSelect(self._exchange, self._commodity, self._contract))

            # ----------------------解析g_params参数----------------------------
            g_params = param
            if not g_params:
                g_params = parseStrategtParam(path)
                if g_params == -1:
                    MyMessageBox.warning(self, '提示', '策略不存在！！！', QMessageBox.Ok)
                    return
            self.strategy_policy_win.paramsTableWidget.setRowCount(len(g_params))
            for i in range(len(self._userNo)):
                self.strategy_policy_win.userComboBox.addItem(self._userNo[i]['UserNo'])
                self.strategy_policy_win.userComboBox.setCurrentIndex(0)
            self.strategy_policy_win.paramsTableWidget.cells = []
            for i, item in enumerate(g_params.items()):
                param_type = ''
                validator = ''
                cell = QLineEdit()
                if isinstance(item[1][0], str):
                    param_type = 'str'
                    cell.setText(item[1][0])
                if isinstance(item[1][0], int):
                    param_type = 'int'
                    validator = QtGui.QIntValidator()
                    cell.setText(str(item[1][0]))
                if isinstance(item[1][0], float):
                    param_type = 'float'
                    validator = QtGui.QDoubleValidator()
                    cell.setText(str(item[1][0]))
                if isinstance(item[1][0], bool):
                    param_type = 'bool'
                    cell = QComboBox()
                    cell.addItems(['True', 'False'])
                    index = 0 if item[1][0] is True else 1
                    cell.setCurrentIndex(index)
                cell.setStyleSheet('border: none; min-height: 30px;')
                self.strategy_policy_win.paramsTableWidget.cells.append(cell)

                self.strategy_policy_win.paramsTableWidget.setItem(i, 0, QTableWidgetItem(str(item[0])))
                self.strategy_policy_win.paramsTableWidget.setCellWidget(i, 1, cell)
                self.strategy_policy_win.paramsTableWidget.setItem(i, 2, QTableWidgetItem(param_type))
                self.strategy_policy_win.paramsTableWidget.setItem(i, 3, QTableWidgetItem(str(item[1][1])))
                if validator:
                    cell.setValidator(validator)
            self.main_strategy_policy_win.setWindowModality(Qt.ApplicationModal)  # 设置阻塞父窗口
            self.main_strategy_policy_win.show()
            self.strategy_policy_win.show()
        else:
            MyMessageBox.warning(self, '提示', '请选择策略！！！', QMessageBox.Ok)

    def updateLogText(self):
        guiQueue = self._controller.get_logger().getGuiQ()
        errData, usrData, sigData = "", "", ""
        flag = True
        try:
            while flag:
                logData = guiQueue.get_nowait()
                if logData[0] == "U":
                    usrData += logData[1] + "\n"
                elif logData[0] == "E":
                    errData += logData[1] + "\n"
                # elif logData[0] == "S":
                #     sigData += logData[1] + "\n"

                if guiQueue.empty():
                    flag = False
        except Exception as e:
            return
        else:
            if usrData:
                self.user_log_widget.append(usrData.strip())
            if errData:
                self.error_info_widget.append(errData.strip())
                self.tab_widget.setCurrentIndex(2)
            # if sigData:
            #     self.signal_log_widget.append(sigData)
        self.timer.start(1000)

    def loadSigLogFile(self):
        """读取本地信号日志并写入界面"""
        sigLogPath = r"./log/trade.dat"
        with open(sigLogPath, "r", encoding="utf-8") as f:
            data = f.read()
        self.signal_log_widget.setText(data)
        self.signal_log_widget.moveCursor(QTextCursor.End)

    def setConnect(self, src):
        if src == 'Q':
            self.statusBar.setText("  即时行情连接成功")
        if src == 'H':
            self.statusBar.setText("  历史行情连接成功")

        if src == 'T':
            self.statusBar.setText("  交易服务连接成功")

        if src == 'S':
            self.statusBar.setText("  极星9.5连接成功")
        self.statusBar.setStyleSheet("""""")

    def setDisconnect(self, src):
        if src == 'Q':
            self.statusBar.setText("  即时行情断连")

        if src == 'H':
            self.statusBar.setText("  历史行情断连")

        if src == 'T':
            self.statusBar.setText("  交易服务断连")

        if src == 'S':
            self.statusBar.setText("  极星9.5客户端退出")
            self.exitSignal.emit()
        self.statusBar.setStyleSheet('color: #0062A3')

    def show_warn(self):
        """极星9.5退出时，弹出窗口槽函数"""
        MyMessageBox.warning(self, "警告", "极星9.5客户端已退出!", QMessageBox.Ok)

    def addExecute(self, dataDict):
        values = self._formatMonitorInfo(dataDict)

        if not values:
            return

        strategyId = dataDict["StrategyId"]
        strategy_id_list = self.get_run_strategy_id()
        try:
            if strategyId in strategy_id_list:
                self.updateRunStage(strategyId, dataDict[5])
                return
        except Exception as e:
            self._logger.warn("addExecute exception")
        else:
            row = self.strategy_table.rowCount()
            self.strategy_table.setRowCount(row + 1)
            for j in range(len(values)):
                item = QTableWidgetItem(str(values[j]))
                if isinstance(values[j], int) or isinstance(values[j], float):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif isinstance(values[j], str):
                    item.setTextAlignment(Qt.AlignCenter)
                self.strategy_table.setItem(row, j, item)

    def _formatMonitorInfo(self, dataDict):
        """
        格式化监控需要的信息
        :param dataDict: 策略的所有信息
        :return: 需要展示的信息
        """

        try:
            Id = dataDict['StrategyId']
            UserNo = dataDict["Config"]["Money"]["UserNo"]
            StName = dataDict['StrategyName']
            BenchCon = dataDict['ContractNo']
            kLineType = dataDict['KLineType']
            kLineSlice = dataDict['KLinceSlice']

            Frequency = str(kLineSlice) + kLineType

            # RunType     = "是" if dataDict['IsActualRun'] else "否"
            RunType = RunMode[dataDict["IsActualRun"]]
            Status = StrategyStatus[dataDict["StrategyState"]]
            InitFund = dataDict['InitialFund']

            Available = eval("{:.2f}".format(InitFund))
            MaxRetrace = 0.0
            TotalProfit = 0.0
            WinRate = 0.0

            return [
                Id,
                UserNo,
                StName,
                BenchCon,
                Frequency,
                Status,
                RunType,
                InitFund,
                Available,
                MaxRetrace,
                TotalProfit,
                WinRate
            ]

        except KeyError:
            traceback.print_exc()
            return []

    def get_run_strategy_id(self):
        strategy_id_list = []
        for i in range(self.strategy_table.rowCount()):
            strategy_id_list.append(int(self.strategy_table.item(i, 0).text()))
        return strategy_id_list

    def updateValue(self, strategyId, dataDict):
        """更新策略ID对应的运行数据"""

        colValues = {
            8: "{:.2f}".format(dataDict["Available"]),
            9: "{:.2f}".format(dataDict["MaxRetrace"]),
            10: "{:.2f}".format(dataDict["NetProfit"]),
            11: "{:.2f}".format(dataDict["WinRate"])
        }

        row = self.get_row_from_strategy_id(strategyId)
        if row != -1:
            for k, v in colValues.items():
                try:
                    item = QTableWidgetItem(str(v))
                    if isinstance(eval(v), int) or isinstance(eval(v), float):
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    elif isinstance(eval(v), str):
                        item.setTextAlignment(Qt.AlignCenter)
                    self.strategy_table.setItem(row, k, item)
                except Exception as e:
                    self._logger.error(f"[UI][{strategyId}]: 更新策略执行数据时出错，执行列表中该策略已删除！")

    def updateRunStage(self, strategyId, status):
        """更新策略运行阶段"""
        row = self.get_row_from_strategy_id(strategyId)
        if row != -1:
            item = QTableWidgetItem(str(StrategyStatus[status]))
            item.setTextAlignment(Qt.AlignCenter)
            self.strategy_table.setItem(row, 5, item)
        self.strategy_table.update()

    def updateRunMode(self, strategyId, status):
        """更新策略运行模式"""
        row = self.get_row_from_strategy_id(strategyId)
        if row != -1:
            item = QTableWidgetItem(str(status))
            item.setTextAlignment(Qt.AlignCenter)
            self.strategy_table.setItem(row, 6, item)

    def delUIStrategy(self, strategy_id):
        """
        删除监控列表中的策略
        :param strategyIdList: 待删除的策略列表
        :return:
        """
        row = self.get_row_from_strategy_id(strategy_id)
        if row != -1:
            self.strategy_table.removeRow(row)

    def get_row_from_strategy_id(self, strategy_id):
        for row in range(self.strategy_table.rowCount()):
            if int(self.strategy_table.item(row, 0).text()) == strategy_id:
                return row
        return -1

    def loadSysLogFile(self):
        """读取本地系统日志"""
        sysLogPath = r"./log/equant.log"
        # with open(sysLogPath, "r", encoding="utf-8") as f:
        with open(sysLogPath, "r") as f:
            data = f.read()
        self.sys_log_widget.setText(data)
        self.sys_log_widget.moveCursor(QTextCursor.End)

    def readPositionConfig(self):
        """读取配置文件"""
        if os.path.exists(r"./config/loadposition.json"):
            with open(r"./config/loadposition.json", "r", encoding="utf-8") as f:
                try:
                    result = json.loads(f.read())
                except json.decoder.JSONDecodeError:
                    return None
                else:
                    return result
        else:
            filePath = os.path.abspath(r"./config/loadposition.json")
            f = open(filePath, 'w')
            f.close()

    def writePositionConfig(self, configure):
        """写入配置文件"""
        # 将文件内容追加到配置文件中
        try:
            config = self.readConfig()
        except:
            config = None
        if config:
            for key in configure:
                config[key] = configure[key]
                break
        else:
            config = configure

        with open(r"./config/loadposition.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(config, indent=4))

    def change_connection(self):
        if self.intervalCheckBox.isChecked():
            self.spin.valueChanged.connect(self.save_position_config)
            self.cbComboBox.currentIndexChanged.connect(self.save_position_config)
            self.intervalSpinBox.valueChanged.connect(self.save_position_config)
            self.reducePositionCheckBox.stateChanged.connect(self.save_position_config)
        else:
            self.spin.valueChanged.disconnect(self.save_position_config)
            self.cbComboBox.currentIndexChanged.disconnect(self.save_position_config)
            self.intervalSpinBox.valueChanged.disconnect(self.save_position_config)
            self.reducePositionCheckBox.stateChanged.disconnect(self.save_position_config)

    def save_position_config(self, OneKeySync=False):
        config = {
            'OneKeySync': True if OneKeySync else False,  # 一键同步
            'AutoSyncPos': self.intervalCheckBox.isChecked(),  # 是否自动同步
            'PriceType': self.cbComboBox.currentIndex(),  # 价格类型 0:对盘价, 1:最新价, 2:市价
            'PriceTick': self.spin.value(),  # 超价点数
            'OnlyDec': self.reducePositionCheckBox.isChecked(),  # 是否只做减仓同步
            'SyncTick': self.intervalSpinBox.value(),  # 同步间隔，毫秒
        }
        self.writePositionConfig(config)
        self._controller._request.resetSyncPosConf(config)

    def valid_spin(self):
        if self.cbComboBox.currentIndex() == 2:
            self.spin.setEnabled(False)
        else:
            self.spin.setEnabled(True)

    def updateSyncPosition(self, positions):
        self.pos_table.setRowCount(len(positions))
        for i in range(len(positions)):
            for j in range(len(positions[i])):
                item = QTableWidgetItem(str(positions[i][j]))
                if isinstance(positions[i][j], int) or isinstance(positions[i][j], float):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif isinstance(positions[i][j], str):
                    item.setTextAlignment(Qt.AlignCenter)
                self.pos_table.setItem(i, j, item)

    def reportDisplay(self, data, id):
        """
        显示回测报告
        :param data: 回测报告数据
        :param id:  对应策略Id
        :return:
        """
        stManager = self._controller.getStManager()
        strategyData = stManager.getSingleStrategy(id)
        strategyPath = strategyData["Path"]

        stName = os.path.basename(strategyPath)

        stData = stManager.getSingleStrategy(id)
        runMode = stData["Config"]["RunMode"]["SendOrder2Actual"]

        # 保存报告数据
        reportPath = save(data, runMode, stName)
        #
        _pGeometry = self._master.frameGeometry()
        # 只在报告窗口关闭后才重新设置位置
        if not self.reportWnd.isVisible():
            self.reportWnd.center(_pGeometry)
        # self.reportWnd.center(_pGeometry)

        self.reportView.reportShowSig.emit([data, reportPath])
        # TODO: 在这里展示报告会导致程序不响应，放到接收信号处展示
        # self.reportWnd.show()
        # self.reportWnd.raise_()

