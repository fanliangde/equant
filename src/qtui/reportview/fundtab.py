from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import pandas as pd
import numpy as np
from functools import partial
from qtui.reportview.crosshair import Crosshair


########################################################################
# 键盘鼠标功能
########################################################################
class KeyWraper(QtWidgets.QWidget):
    """键盘鼠标功能支持的元类"""

    # 初始化
    # ----------------------------------------------------------------------
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

    # 重载方法keyPressEvent(self,event),即按键按下事件方法
    # ----------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Up:
            self.onUp()
        elif event.key() == QtCore.Qt.Key_Down:
            self.onDown()
        elif event.key() == QtCore.Qt.Key_Left:
            self.onLeft()
        elif event.key() == QtCore.Qt.Key_Right:
            self.onRight()
        elif event.key() == QtCore.Qt.Key_PageUp:
            self.onPre()
        elif event.key() == QtCore.Qt.Key_PageDown:
            self.onNxt()

    # 重载方法mousePressEvent(self,event),即鼠标点击事件方法
    # ----------------------------------------------------------------------
    def mousePressEvent(self, event):
        # 设置鼠标样式
        # self.setCursor(QtCore.Qt.SizeHorCursor)
        # self.setFocusPolicy(QtCore.Qt.StrongFocus)
        if event.button() == QtCore.Qt.RightButton:
            self.onRClick(event.pos())
        elif event.button() == QtCore.Qt.LeftButton:
            self.onLClick(event.pos())

    # 重载方法mouseReleaseEvent(self,event),即鼠标点击事件方法
    # ----------------------------------------------------------------------
    def mouseReleaseEvent(self, event):
        print("Release")
        self.setCursor(QtCore.Qt.ArrowCursor)
        if event.button() == QtCore.Qt.RightButton:
            self.onRRelease(event.pos())
        elif event.button() == QtCore.Qt.LeftButton:
            self.onLRelease(event.pos())
        self.releaseMouse()

    # 重载方法wheelEvent(self,event),即滚轮事件方法
    # ----------------------------------------------------------------------
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.onUp()
        else:
            self.onDown()

    # 重载方法dragMoveEvent(self,event),即拖动事件方法
    # ----------------------------------------------------------------------
    def paintEvent(self, event):
        self.onPaint()

    # PgDown键
    # ----------------------------------------------------------------------
    def onNxt(self):
        pass

    # PgUp键
    # ----------------------------------------------------------------------
    def onPre(self):
        pass

    # 向上键和滚轮向上
    # ----------------------------------------------------------------------
    def onUp(self):
        pass

    # 向下键和滚轮向下
    # ----------------------------------------------------------------------
    def onDown(self):
        pass

    # 向左键
    # ----------------------------------------------------------------------
    def onLeft(self):
        pass

    # 向右键
    # ----------------------------------------------------------------------
    def onRight(self):
        pass

    # 鼠标左单击
    # ----------------------------------------------------------------------
    def onLClick(self, pos):
        pass

    # 鼠标右单击
    # ----------------------------------------------------------------------
    def onRClick(self, pos):
        pass

    # 鼠标左释放
    # ----------------------------------------------------------------------
    def onLRelease(self, pos):
        pass

    # 鼠标右释放
    # ----------------------------------------------------------------------
    def onRRelease(self, pos):
        pass

    # 画图
    # ----------------------------------------------------------------------
    def onPaint(self):
        pass


########################################################################
# 选择缩放功能支持
########################################################################
class CustomViewBox(pg.ViewBox):
    # ----------------------------------------------------------------------
    def __init__(self, parent, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.parent = parent
        # 拖动放大模式
        # self.setMouseMode(self.RectMode)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            # self.contextMenuEvent(ev)  # 右键菜单
            pass
        # if ev.button()==QtCore.Qt.LeftButton:
        #     self.autoRange()

    def mousePressEvent(self, event):
        pg.ViewBox.mousePressEvent(self, event)

    def mouseDragEvent(self, ev, axis=None):
        # if ev.start==True and ev.finish==False: ##判断拖拽事件是否结束
        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos

        rect = self.sceneBoundingRect()

        pianyi = dif.x() * self.parent.count * 2 / rect.width()

        self.parent.index -= int(pianyi)
        self.parent.index = max(self.parent.index, 60)
        xMax = self.parent.index + self.parent.count
        xMin = self.parent.index - self.parent.count
        # if xMin < 0:
        #     xMin = 0

        pg.ViewBox.mouseDragEvent(self, ev, axis)

    # 重载方法resizeEvent(self, ev)
    def resizeEvent(self, ev):
        self.linkedXChanged()
        self.linkedYChanged()
        self.updateAutoRange()
        self.updateViewRange()
        self._matrixNeedsUpdate = True
        self.sigStateChanged.emit(self)
        self.background.setRect(self.rect())
        self.sigResized.emit(self)
        # self.parent.refreshHeight()


########################################################################
# 时间序列，横坐标支持
########################################################################
class MyStringAxis(pg.AxisItem):
    """时间序列横坐标支持"""

    # 初始化
    # ----------------------------------------------------------------------
    def __init__(self, xdict, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self.minVal = 0
        self.maxVal = 0
        self.xdict = xdict
        self.x_values = np.asarray(xdict.keys())
        self.x_strings = xdict.values()
        self.setPen(color=(255, 255, 255, 255), width=0.8)
        self.setStyle(tickFont=QtGui.QFont("Roman times", 10, QtGui.QFont.Bold), autoExpandTextSpace=True)

    # 更新坐标映射表
    # ----------------------------------------------------------------------
    def update_xdict(self, xdict):
        self.xdict.update(xdict)
        self.x_values = np.asarray(self.xdict.keys())
        self.x_strings = self.xdict.values()

    # 将原始横坐标转换为时间字符串,第一个坐标包含日期
    # ----------------------------------------------------------------------
    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            vs = v * scale
            if vs in self.x_values:
                vstr = self.x_strings[np.abs(self.x_values - vs).argmin()]
                if (isinstance(vstr, (str))):
                    vstr = vstr
                else:
                    vstr = vstr.strftime('%Y-%m-%d %H:%M:%S')
            else:
                vstr = ""
            strings.append(vstr)
        return strings


class LineWidget(KeyWraper):

    initCompleted = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LineWidget")

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
        self.layout = pg.GraphicsLayout(border=(100, 100, 100))
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

        self.vbox = QtWidgets.QVBoxLayout()
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
        plotItem.hideAxis('left')
        plotItem.showAxis('right')
        # 设置采样模式
        plotItem.setDownsampling(mode='peak')
        plotItem.setRange(xRange=(0, 1), yRange=(0, 1))
        plotItem.getAxis('right').setWidth(60)
        plotItem.getAxis('right').setStyle(tickFont=QtGui.QFont('Roman times', 10, QtGui.QFont.Bold))
        plotItem.getAxis('right').setPen(color=(255, 255, 255, 255), width=0.8)
        plotItem.showGrid(True, True)
        plotItem.hideButtons()

        return plotItem

    def initPlotFund(self):
        """初始化资金曲线图"""
        self.pwFund = self.makePI('PlotFund')
        self.fund = self.pwFund.plot()
        self.pwFund.addItem(self.fund)
        self.pwFund.setMinimumHeight(12)

        self.layout.nextRow()
        self.layout.addItem(self.pwFund)
        self.layout.adjustSize()

    def plotFund(self, xmin=0, xmax=-1):
        """重画资金曲线"""
        if self.initCompleted:
            self.fund.setData(self.datas.DynamicEquity[xmin:xmax] + [0],
                              name="fund", symbol='o')

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
        self.count = min(len(self.datas.DynamicEquity), int(self.count * 1.2) + 1)
        self.refresh()
        if len(self.datas.DynamicEquity) > 0:
            x = self.index - self.count / 2 + 2 if int(
                self.crosshair.xAxis) < self.index - self.count / 2 + 2 else int(self.crosshair.xAxis)
            x = self.index + self.count / 2 - 2 if x > self.index + self.count / 2 - 2 else x
            x = min(x, len(self.datas) - 1)
            y = self.datas.DynamicEquity[int(x)]
            self.crosshair.signal.emit((x, y))

    def onUp(self):
        """缩小显示区间"""
        self.count = max(20, int(self.count / 1.2) - 1)  # 最小显示范围20
        self.refresh()
        if len(self.datas.DynamicEquity) > 0:
            x = self.index - self.count / 2 + 2 if int(
                self.crosshair.xAxis) < self.index - self.count + 2 else int(self.crosshair.xAxis)
            x = self.index + self.count / 2 - 2 if x > self.index + self.count / 2 - 2 else x
            x = min(x, len(self.datas.DynamicEquity) - 1)
            y = self.datas.DynamicEquity[int(x)]
            self.crosshair.signal.emit((x, y))

    def onLeft(self):
        """向左移动"""
        if len(self.datas.DynamicEquity) > 0 and int(self.crosshair.xAxis) > 2:
            x = int(self.crosshair.xAxis) - 1
            y = self.datas.DynamicEquity[x]
            if x <= self.index - self.count / 2 + 2 and self.index > 1:
                self.index -= 1
                self.refresh()
            self.crosshair.signal.emit((x, y))

    def onRight(self):
        """向右移动"""
        if len(self.datas.DynamicEquity) > 0 and int(self.crosshair.xAxis) < len(self.datas.DynamicEquity) - 1:
            x = int(self.crosshair.xAxis) + 1
            y = self.datas.DynamicEquity[x]
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
            xmax = min(xmax, len(datas.DynamicEquity))
            if len(datas.DynamicEquity) > 0 and xmax > xmin:
                ymin = min(datas.DynamicEquity[xmin:xmax])
                ymax = max(datas.DynamicEquity[xmin:xmax])
                if ymin and ymax:
                    self.setRange(yRange=(ymin, ymax))
            else:
                self.setRange(yRange=(0, 1))

        view = self.pwFund.getViewBox()
        view.sigXRangeChanged.connect(partial(viewXRangeChanged, 'low', 'high'))

    def loadData(self, datas):
        """载入数据"""
        self.index = 0

        self.datas = pd.DataFrame(datas)

        self.axisTime.xdict = {}
        xdict = dict(enumerate(datas))
        self.axisTime.update_xdict(xdict)
        self.resignData(self.datas)

        self.plotAll(True, 0, len(self.datas.DynamicEquity))

    def plotAll(self, redraw=True, xMin=0, xMax=-1):
        if redraw:
            xmax = len(self.datas) if xMax < 0 else xMax
            xmin = max(0, xmax - self.count)
            self.index = int((xmax + xmin) / 2)

        self.pwFund.setLimits(xMin=xMin, xMax=xMax)
        self.plotFund(0, len(self.datas))
        self.refresh()













