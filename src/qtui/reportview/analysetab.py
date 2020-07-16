import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


ITEMS = {
    "资金"                                    : "",
    "合约信息"                                : "",
    "周期"                                    : "",
    "计算开始时间"                            : "",
    "计算结束时间"                            : "",
    "测试天数"                                : "从测试数据开始到结束的天数",
    ""                                        : "",
    "最终权益"                                : "包括当前的可用资金和浮动盈亏",
    #"空仓周期数"                              : "空仓的周期数",
    #"最长连续空仓周期数"                      : "最长连续空仓的周期数",
    "标准离差"                                : "盈亏的标准离差",
    "标准离差率"                              : "盈亏的标准离差率",
    "夏普比率"                                : "（平均年收益率-无风险率)/收益率的标准差",
    "盈亏总平均/亏损平均"                     : "平均盈亏和平均亏损的比值",
    "权益最大回撤"                            : "权益最大回撤",
    "权益最大回撤开始时间"                    : "权益最大回撤出现的开始时间",
    "权益最大回撤结束时间"                    : "权益最大回撤出现的结束时间",
    "权益最大回撤比"                          : "权益最大回撤和权益最大回撤时的最大权益的比值的最大值",
    "权益最大回撤比开始时间"                  : "权益最大回撤比出现的开始时间",
    "权益最大回撤比结束时间"                  : "权益最大回撤比出现的结束时间",
    "风险率"                                  : "最大亏损/本金",
    "收益率/风险率"                           : "收益率/风险率",

    "盈利率"                                  : "盈利占资金分配量的百分比",
    "实际盈利率"                              : "累计资金收益率",
    "年化单利收益率"                          : "单利收益率/(交易天数/365)",
    "月化单利收益率"                          : "单利收益率/(交易天数/30)",
    "年化复利收益率"                          : "(期末权益/期初权益)^(365/交易天数) - 1",
    "月化复利收益率"                          : "(期末权益/期初权益)^(365/交易天数) - 1",
    "胜率"                                    : "盈利次数占总交易次数的百分比",
    "平均盈利/平均亏损"                       : "平均盈利和平均亏损的比值",
    "平均盈利率/平均亏损率"                   : "平均盈利率和平均亏损率的比值",
    "净利润"                                  : "总盈利 - 总亏损",
    "总盈利"                                  : "盈利的总和",
    "总亏损"                                  : "亏损的总和",
    "总盈利/总亏损"                           : "总盈利和总亏损的比值",
    "其中持仓浮盈"                            : "其中持仓的浮动盈亏",
    "交易次数"                                : "发生交易的次数",
    "盈利比率"                                : "盈利次数占总交易次数的百分比",
    "盈利次数"                                : "盈利的交易次数",
    "亏损次数"                                : "亏损的交易次数",
    "持平次数"                                : "持平的交易次数",

    "平均盈亏"                                : "平均每笔交易的盈亏",
    "平均盈利"                                : "平均每笔盈利交易的盈利",
    "平均亏损"                                : "平均每笔亏损交易的亏损",

    "盈利持续最大天数"                        : "盈利的持续最大天数",
    "盈利持续最大天数出现时间"                : "盈利持续最大天数出现的时间",
    "亏损持续最大天数"                        : "亏损的持续最大天数",
    "亏损持续最大天数出现时间"                : "亏损持续最大天数出现的时间",

    "盈利环比增加持续最大天数"                : "盈利环比增加的持续最大天数",
    "盈利环比增加持续最大天数出现时间"        : "盈利环比增加持续最大天数出现的时间",
    "亏损环比增加持续最大天数"                : "亏损环比增加的持续最大天数",
    "亏损环比增加持续最大天数出现时间"        : "亏损环比增加持续最大天数出现的时间",

    "期间最大权益"                            : "测试期间出现的最大权益",
    "期间最小权益"                            : "测试期间出现的最小权益",
    "手续费"                                  : "手续费",
    "滑点损耗"                                : "滑点损耗",
    "成交额"                                  : "成交额",
}



class BaseCell(QTableWidgetItem):
    """"""
    def __init__(self, content):
        super(BaseCell, self).__init__()
        self.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.set_content(content)
        if ITEMS[content]:
            self.setToolTip(content+": "+ITEMS[content])

    def set_content(self, content):
        self.setText(str(content))


class DataCell(QTableWidgetItem):
    def __init__(self, content):
        super(DataCell, self).__init__()
        self.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.set_content(content)

    def set_content(self, content):
        self.setText(str(content))


class AnalyseTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setRowCount(55)
        self.setColumnCount(2)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.horizontalHeader().setDefaultSectionSize(250)
        self.verticalHeader().setDefaultSectionSize(20)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        # 去除边框
        self.setFrameShape(QFrame.NoFrame)

        for row, item in enumerate(ITEMS.keys()):
            self.setItem(row, 0, BaseCell(item))

    def addAnalyseResult(self, detail):
        """增加回测结果数据"""
        if not detail:
            return

        detailFormatter = [
            '{:.2f}'.format(float(detail["InitialFund"])),
            detail["Contract"],
            detail["Period"],
            detail["StartTime"],
            detail["EndTime"],
            detail["TestDay"],
            '{:.2f}'.format(float(detail["FinalEquity"])),
            #detail["EmptyPeriod"],
            #detail["MaxContinueEmpty"],
            '{:.2f}'.format(float(detail["StdDev"])),
            detail["StdDevRate"] if isinstance(detail["StdDevRate"], str) else '{:.2f}'.format(
                float(detail["StdDevRate"])),
            '{:.2f}'.format(float(detail["Sharpe"])),
            '{:.2f}'.format(float(detail["PlmLm"])) if isinstance(detail["PlmLm"], float) else detail["PlmLm"],
            '{:.2f}'.format(float(detail["MaxRetrace"])),
            detail.get('MaxRetraceStartTime', ''),
            detail["MaxRetraceTime"],
            '{:.2f}'.format(float(detail["MaxRetraceRate"])),
            detail.get('MaxRetraceRateStartTime', ''),
            detail["MaxRetraceRateTime"],
            '{:.2f}'.format(float(detail["Risky"])),
            '{:.2f}'.format(float(detail["RateofReturnRisk"])) \
                if isinstance(detail["RateofReturnRisk"], float) else detail["RateofReturnRisk"],
            '{:.2f}'.format(float(detail["Returns"])),
            '{:.2f}'.format(float(detail["RealReturns"])),
            '{:.2f}'.format(float(detail["AnnualizedSimple"])),
            '{:.2f}'.format(float(detail["MonthlySimple"])),
            '{:.2f}'.format(float(detail["AnnualizedCompound"])) \
                if isinstance(detail["AnnualizedCompound"], float) else detail["AnnualizedCompound"],
            '{:.2f}'.format(float(detail["MonthlyCompound"])) \
                if isinstance(detail["MonthlyCompound"], float) else detail["MonthlyCompound"],
            '{:.2f}'.format(float(detail["WinRate"])) if isinstance(detail["WinRate"], float) else detail["WinRate"],
            '{:.2f}'.format(float(detail["MeanWinLose"])) \
                if isinstance(detail["MeanWinLose"], float) else detail["MeanWinLose"],
            '{:.2f}'.format(float(detail["MeanWinLoseRate"])) \
                if isinstance(detail["MeanWinLoseRate"], float) else detail["MeanWinLoseRate"],
            '{:.2f}'.format(float(detail["NetProfit"])) \
                if isinstance(detail["NetProfit"], float) else detail["NetProfit"],
            '{:.2f}'.format(float(detail["TotalWin"])),
            '{:.2f}'.format(float(detail["TotalLose"])),
            '{:.2f}'.format(float(detail["RatioofWinLose"])) \
                if isinstance(detail["RatioofWinLose"], float) else detail["RatioofWinLose"],
            '{:.2f}'.format(float(detail["HoldProfit"])),
            detail["TradeTimes"],
            '{:.2f}'.format(float(detail["WinPercentage"])),
            detail["WinTimes"],
            detail["LoseTimes"],
            detail["EventTimes"],
            '{:.2f}'.format(float(detail["MeanProfit"])),
            '{:.2f}'.format(float(detail["MeanWin"])),
            '{:.2f}'.format(float(detail["MeanLose"])),
            detail["MaxWinContinueDays"],
            detail["MaxWinContinueDaysTime"],
            detail["MaxLoseContinueDays"],
            detail["MaxLoseContinueDaysTime"],
            detail["MaxWinComparedIncreaseContinueDays"],
            detail["MaxWinComparedIncreaseContinueDaysTime"],
            detail["MaxLoseComparedIncreaseContinueDays"],
            detail["MaxLoseComparedIncreaseContinueDaysTime"],
            '{:.2f}'.format(float(detail["MaxEquity"])),
            '{:.2f}'.format(float(detail["MinEquity"])),
            '{:.2f}'.format(float(detail["Cost"])),
            '{:.2f}'.format(float(detail["SlippageCost"])),
            '{:.2f}'.format(float(detail["Turnover"])),
        ]

        for index, data in enumerate(detailFormatter):
            if index >= 6: index += 1
            self.setItem(index, 1, DataCell(data))

