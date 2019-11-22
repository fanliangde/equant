from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph import QtGui, QtCore
from functools import partial


from qtui.reportview.fundtab import KeyWraper, MyStringAxis, CustomViewBox
from qtui.reportview.crosshair import Crosshair


DIR = {
    "年度分析": [["年度权益", "Equity"], ["年度净利润", "NetProfit"], ["年度盈利率", "Returns"],
             ["年度胜率", "WinRate"], ["年度平均盈亏", "MeanReturns"], ["年度权益增长", "IncSpeed"]],
    "季度分析": [["季度权益", "Equity"], ["季度净利润", "NetProfit"], ["季度盈利率", "Returns"],
             ["季度胜率", "WinRate"], ["季度平均盈亏", "MeanReturns"], ["季度权益增长", "IncSpeed"]],
    "月度分析": [["月度权益", "Equity"], ["月度净利润", "NetProfit"], ["月度盈利率", "Returns"],
             ["月度胜率", "WinRate"], ["月度平均盈亏", "MeanReturns"], ["月度权益增长", "IncSpeed"]],
    "周分析"  : [["周权益", "Equity"], ["周净利润", "NetProfit"], ["周盈利率", "Returns"],
              ["周胜率", "WinRate"], ["周平均盈亏", "MeanReturns"], ["周权益增长", "IncSpeed"]],
    "日分析"  : [["日权益", "Equity"], ["日净利润", "NetProfit"], ["日盈利率", "Returns"],
              ["日胜率", "WinRate"], ["日平均盈亏", "MeanReturns"], ["日权益增长", "IncSpeed"]]
}


GRAPHTYPE = {
    "Equity"      : "柱状图",
    "NetProfit"   : "立体",
    "Returns"     : "立体",
    "WinRate"     : "柱状图",
    "MeanReturns" : "柱状图",
    "IncSpeed"    : "立体"
}


class DirTree(QTreeWidget):

    def __init__(self, graph, parent=None):
        super(DirTree, self).__init__(parent)
        self._parent = parent

        self._graph = graph
        self._graphDatas = None

        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self._addTreeItem()
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setColumnWidth(0, 50)
        self.setFixedWidth(140)

    def _addTreeItem(self):
        for key in DIR.keys():
            root = QTreeWidgetItem(self)
            root.setText(0, key)
            for item in DIR[key]:
                child = QTreeWidgetItem(root)
                child.setText(0, item[0])  # 设置文本
                child.setText(1, item[1])

            self.addTopLevelItem(root)

        self.itemClicked.connect(self.itemClickedCallback)

    def getPlotData(self, key, tag):
        x, y = [], []
        for sd in self._graphDatas[key]:
            x.append(sd.get('Time'))
            y.append(sd.get(tag))
        return x, y

    def itemClickedCallback(self, item):
        if item.parent():
            rootKey = item.parent().text(0)
            key = item.text(0)
            flag = item.text(1)
            x, y = self.getPlotData(rootKey, flag)

            self._graph.loadData(y)
            self._graph.update()

    def setInitialGraph(self, data):
        self._graphDatas = data
        # self._graph.clear()
        x, y = self.getPlotData("年度分析", 'Equity')

        self._graph.loadData(y)
        self._parent.layout().addWidget(self._graph)

    def showGraphDatas(self, datas):
        self._graphDatas = datas
        # self._graph.clear()
        x, y = self.getPlotData("年度分析", 'Equity')

        self._graph.loadData(y)
        self._parent.layout().addWidget(self._graph)


class BarGraph(pg.GraphicsObject):
    """柱状图"""
    def __init__(self, datas):
        super(BarGraph, self).__init__()
        self.data = datas
        self.setFlag(self.ItemUsesExtendedStyleOption)
        self.generatePicture(self.data)

    def generatePicture(self, datas=None):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        w = 0.4
        for i, data in enumerate(datas):
            if data >= 0:
                p.setPen(pg.mkPen('r'))
                p.setBrush(pg.mkBrush('r'))
            else:
                p.setPen(pg.mkPen('g'))
                p.setBrush(pg.mkBrush('g'))
            p.drawRect(QtCore.QRectF(i-w, 0, w * 2, data))
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())


class GraphWidget(KeyWraper):

    initCompleted = False

    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.datas = None

        self.count = 90
        self.index = None
        self.oldsize = 0

        # 初始化完成
        self.initCompleted = False
        self.initUI()

    def initUI(self):
        self.pw = pg.PlotWidget()
        self.layout = pg.GraphicsLayout(border=(10, 10, 10))
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setBorder(color=(255, 255, 255, 255), width=0.8)
        self.layout.setZValue(0)
        self.layout.setMinimumHeight(140)
        self.pw.setCentralWidget(self.layout)
        # 设置横坐标
        xdict = {}
        self.axisTime = MyStringAxis(xdict, orientation='bottom')
        # 初始化资金曲线
        self.initPlotFund()
        # 十字光标
        self.crosshair = Crosshair(self.pw, self)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.pw)
        self.setLayout(self.vbox)

        self.initCompleted = True
        self.oldSize = self.rect().height()

    def makePI(self, name):
        """生成PlotItem对象"""
        vb = CustomViewBox(self)
        plotItem = pg.PlotItem(viewBox=vb, name=name, axisItems={'bottom': self.axisTime})
        plotItem.setMenuEnabled(False)
        # 仅绘制ViewBox可见范围内的点
        plotItem.setClipToView(True)
        plotItem.showAxis('left')
        # 设置采样模式
        plotItem.setDownsampling(mode='peak')
        plotItem.setRange(xRange=(0, 1), yRange=(0, 1))
        plotItem.getAxis('left').setWidth(70)
        plotItem.getAxis('left').setStyle(tickFont=QtGui.QFont('Roman times', 10, QtGui.QFont.Bold))
        plotItem.getAxis('left').setPen(color=(255, 255, 255, 255), width=0.8)
        plotItem.showGrid(True, True)
        plotItem.hideButtons()

        return plotItem

    def initPlotFund(self):
        """初始化资金曲线图"""
        self.pwFund = self.makePI('PlotFund')
        self.fund = BarGraph([1, 2, 3, 4, 5, 6, 7])
        self.pwFund.addItem(self.fund)
        self.pwFund.setMinimumHeight(12)

        self.layout.nextRow()
        self.layout.addItem(self.pwFund)
        self.layout.adjustSize()

    def plotFund(self, xmin=0, xmax=-1):
        """重画资金曲线"""
        if self.initCompleted:
            self.fund.generatePicture(self.datas[xmin:xmax] + [0])

    def refresh(self):
        """
        刷新资金曲线的现实范围
        """
        datas = self.datas
        minutes = int(self.count / 2)
        xmin = max(0, self.index - minutes)
        xmax = xmin + 2 * minutes
        self.pwFund.setRange(xRange=(xmin, xmax))

    def onDown(self):
        """放大显示区间"""
        self.count = min(len(self.datas), int(self.count * 1.2) + 1)
        self.refresh()
        if len(self.datas) > 0:
            x = self.index - self.count / 2 + 2 if int(
                self.crosshair.xAxis) < self.index - self.count / 2 + 2 else int(self.crosshair.xAxis)
            x = self.index + self.count / 2 - 2 if x > self.index + self.count / 2 - 2 else x
            x = min(x, len(self.datas) - 1)
            y = self.datas[int(x)]
            self.crosshair.signal.emit((x, y))

    def onUp(self):
        """缩小显示区间"""
        self.count = max(20, int(self.count / 1.2) - 1)  # 最小显示范围20
        self.refresh()
        if len(self.datas) > 0:
            x = self.index - self.count / 2 + 2 if int(
                self.crosshair.xAxis) < self.index - self.count + 2 else int(self.crosshair.xAxis)
            x = self.index + self.count / 2 - 2 if x > self.index + self.count / 2 - 2 else x
            x = min(x, len(self.datas) - 1)
            y = self.datas[int(x)]
            self.crosshair.signal.emit((x, y))

    def onLeft(self):
        """向左移动"""
        if len(self.datas) > 0 and int(self.crosshair.xAxis) > 2:
            x = int(self.crosshair.xAxis) - 1
            y = self.datas[x]
            if x <= self.index - self.count / 2 + 2 and self.index > 1:
                self.index -= 1
                self.refresh()
            self.crosshair.signal.emit((x, y))

    def onRight(self):
        """向右移动"""
        if len(self.datas) > 0 and int(self.crosshair.xAxis) < len(self.datas) - 1:
            x = int(self.crosshair.xAxis) + 1
            y = self.datas[x]
            if x >= self.index + int(self.count / 2) - 2:
                self.index += 1
                self.refresh()
            self.crosshair.signal.emit((x, y))

    def onPaint(self):
        """界面刷新回调"""
        view = self.pwFund.getViewBox()
        vRange = view.viewRange()
        xmin = max(0, int(vRange[0][0]))
        xmax = max(0, int(vRange[0][1]))
        self.index = int((xmin+xmax)/2)+1

    def resignData(self, datas):
        self.crosshair.datas = datas

        def viewXRangeChanged(low, high, self):
            vRange = self.viewRange()
            xmin = max(0, int(vRange[0][0]))
            xmax = max(0, int(vRange[0][1]))
            xmax = min(xmax, len(datas))
            if len(datas) > 0 and xmax > xmin:
                ymin = min(datas[xmin:xmax])
                ymax = max(datas[xmin:xmax])
                if ymin and ymax:
                    self.setRange(yRange=(ymin, ymax))
            else:
                self.setRange(yRange=(0, 1))

        view = self.pwFund.getViewBox()
        view.sigXRangeChanged.connect(partial(viewXRangeChanged, 'low', 'high'))

    def loadData(self, datas):
        """载入数据"""
        self.index = 0

        self.datas = datas

        self.axisTime.xdict = {}
        xdict = dict(enumerate(datas))
        self.axisTime.update_xdict(xdict)
        self.resignData(self.datas)

        self.plotAll(True, 0, len(self.datas))

    def plotAll(self, redraw=True, xMin=0, xMax=-1):
        if redraw:
            xmax = len(self.datas) if xMax < 0 else xMax
            xmin = max(0, xmax - self.count)
            self.index = int((xmax + xmin) / 2)

        self.pwFund.setLimits(xMin=xMin, xMax=xMax)
        self.plotFund(0, len(self.datas))
        self.refresh()



class GraphTab(QWidget):

    def __init__(self, parent=None):
        super(GraphTab, self).__init__(parent)
        self.setObjectName("GraphTab")

        self._initUI()

    def _initUI(self):
        qLayout = QHBoxLayout()
        qLayout.setContentsMargins(0, 0, 0, 0)

        self.graph = GraphWidget(self)
        self.dir = DirTree(self.graph, self)

        qLayout.addWidget(self.dir,  0, Qt.AlignLeft)
        qLayout.addWidget(self.graph, 0, Qt.AlignRight)
        self.setLayout(qLayout)

    def addGraphDatas(self, datas):
        self.dir.showGraphDatas(datas)
