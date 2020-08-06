import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qtui.reportview.fundtab import LineWidget
from qtui.reportview.analysetab import AnalyseTable
from qtui.reportview.tradetab import CustomTableView, CustomModel
from qtui.reportview.stagetab import StageTab
from qtui.reportview.graphtab import GraphTab


class Tab(QTabWidget):

    def __init__(self, parent=None):
        super(Tab, self).__init__(parent)
        self._createTab()

    def _createTab(self):
        self.fundTab = LineWidget()
        self.analyseTab = AnalyseTable()
        self.stageTab = StageTab()
        # self.tradeTab = TradeTab()
        self.tradeTab = CustomTableView()
        self.graphTab = GraphTab()

        self.addTab(self.fundTab, "资金详情")
        self.addTab(self.analyseTab, "分析报告")
        self.addTab(self.stageTab, "阶段总结")
        self.addTab(self.tradeTab, "交易详情")
        self.addTab(self.graphTab, "图表分析")

    def showData(self, datas):
        """显示回测结果"""
        self._addFundData(datas)
        self._addAnalyseData(datas)
        self._addStageData(datas)
        self._addTradeData(datas)
        self._addGraphData(datas)

    def _addFundData(self, datas):
        try:
            fundDatas = datas['Fund']
        except Exception as e:
            raise e
        self.fundTab.loadData(fundDatas)

    def _addAnalyseData(self, datas):
        try:
            details = datas["Detail"]
        except Exception as e:
            raise e
        self.analyseTab.addAnalyseResult(details)

    def _addStageData(self, datas):
        try:
            stage = datas["Stage"]
        except Exception as e:
            raise e
        self.stageTab.addStageDatas(stage)

    def _addTradeData(self, datas):
        try:
            orders = datas["Orders"]
            kLineInfo = datas["KLineType"]
        except Exception as e:
            raise e
        model = CustomModel(orders, kLineInfo)
        self.tradeTab.setModel(model)
        # self.tradeTab.addTradeDatas(orders, kLineInfo)

    def _addGraphData(self, datas):
        try:
            stage = datas["Stage"]
        except Exception as e:
            raise e
        self.graphTab.addGraphDatas(stage)