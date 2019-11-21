import sys
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QEnterEvent, QPainter, QColor, QPen, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QPushButton

import ctypes

from utils.window.res.default import *
from utils.window.titlebar import *

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")


# 枚举左上右下以及四个定点
Left, Top, Right, Bottom, LeftTop, RightTop, LeftBottom, RightBottom = range(8)


class FramelessWindow(QWidget):

    def __init__(self, *args, **kwargs):
        super(FramelessWindow, self).__init__(*args, **kwargs)

        self._pressed = False
        self.Direction = None
        # 背景透明
        # self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 无标题栏和边框
        self.setWindowFlags(Qt.FramelessWindowHint)
        # 鼠标跟踪
        self.setMouseTracking(True)
        self.setObjectName("Framless")
        # # 布局
        layout = QVBoxLayout(self, spacing=0)
        # 预留边界用于实现无边框窗口调整大小
        layout.setContentsMargins(MARGINS, MARGINS, MARGINS, MARGINS)
        # 标题栏
        self.titleBar = TitleBar(self)
        layout.addWidget(self.titleBar)

        self.resize(QSize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT))

        self.windowTitleChanged.connect(self.titleBar.setTitle)
        self.windowIconChanged.connect(self.titleBar.setIcon)

    def closeWindow(self):
        self.close()

    def getWinThese(self):
        """获取标题栏的配色风格"""
        return self.titleBar.theseState

    def setWinThese(self, theme):
        self.titleBar.theseState = theme

    def hideTheseBtn(self):
        """隐藏换肤按钮"""
        self.titleBar.theseSelect.hide()

    def showTheseBtn(self):
        """显示换肤按钮"""
        self.titleBar.theseSelect.show()

    def setTitleBarHeight(self, height=TITLE_BAR_HEIGHT):
        """设置标题栏高度"""
        self.titleBar.setHeight(height)

    def setIconSize(self, size):
        """设置图标的大小"""
        self.titleBar.setIconSize(size)

    def setIcon(self, icon):
        self.titleBar.setIcon(icon)

    def setWidget(self, widget):
        """设置自己的控件"""
        if hasattr(self, '_widget'):
            return
        self._widget = widget
        # 设置默认背景颜色， 否则由于受到父窗口的影响导致透明
        self._widget.setAutoFillBackground(True)
        # palette = self._widget.palette()
        # palette.setColor(palette.Window, QColor(250, 250, 250))
        # self._widget.setPalette(palette)
        self._widget.installEventFilter(self)
        self.layout().addWidget(self._widget)

    def showMaximized(self):
        """最大化,要去除上下左右边界,如果不去除则边框地方会有空隙"""
        super(FramelessWindow, self).showMaximized()
        self.layout().setContentsMargins(0, 0, 0, 0)

    def showNormal(self):
        """还原,要保留上下左右边界,否则没有边框无法调整"""
        super(FramelessWindow, self).showNormal()
        self.layout().setContentsMargins(
            MARGINS, MARGINS, MARGINS, MARGINS)

    def showMinimized(self):
        super(FramelessWindow, self).showMinimized()

    def eventFilter(self, obj, event):
        """事件过滤器,用于解决鼠标进入其它控件后还原为标准鼠标样式"""
        if isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)
        return super(FramelessWindow, self).eventFilter(obj, event)

    def paintEvent(self, event):
        """由于是全透明背景窗口,重绘事件中绘制透明度为1的难以发现的边框,用于调整窗口大小"""
        super(FramelessWindow, self).paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 1), 2 * MARGINS))
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super(FramelessWindow, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._mpos = event.pos()
            self._pressed = True

    def mouseReleaseEvent(self, event):
        '''鼠标弹起事件'''
        super(FramelessWindow, self).mouseReleaseEvent(event)
        self._pressed = False
        self.Direction = None

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # super(FramelessWindow, self).mouseMoveEvent(event)
        pos = event.pos()
        xPos, yPos = pos.x(), pos.y()
        wm, hm = self.width() - MARGINS, self.height() - MARGINS
        if self.isMaximized() or self.isFullScreen():
            self.Direction = None
            self.setCursor(Qt.ArrowCursor)
            return
        if event.buttons() == Qt.LeftButton and self._pressed:
            self._resizeWidget(pos)
            return
        if xPos <= MARGINS and yPos <= MARGINS:
            # 左上角
            self.Direction = LeftTop
            self.setCursor(Qt.SizeFDiagCursor)
        elif wm <= xPos <= self.width() and hm <= yPos <= self.height():
            # 右下角
            self.Direction = RightBottom
            self.setCursor(Qt.SizeFDiagCursor)
        elif wm <= xPos and yPos <= MARGINS:
            # 右上角
            self.Direction = RightTop
            self.setCursor(Qt.SizeBDiagCursor)
        elif xPos <= MARGINS and hm <= yPos:
            # 左下角
            self.Direction = LeftBottom
            self.setCursor(Qt.SizeBDiagCursor)
        elif 0 <= xPos <= MARGINS and MARGINS <= yPos <= hm:
            # 左边
            self.Direction = Left
            self.setCursor(Qt.SizeHorCursor)
        elif wm <= xPos <= self.width() and MARGINS <= yPos <= hm:
            # 右边
            self.Direction = Right
            self.setCursor(Qt.SizeHorCursor)
        elif MARGINS <= xPos <= wm and 0 <= yPos <= MARGINS:
            # 上面
            self.Direction = Top
            self.setCursor(Qt.SizeVerCursor)
        elif MARGINS <= xPos <= wm and hm <= yPos <= self.height():
            # 下面
            self.Direction = Bottom
            self.setCursor(Qt.SizeVerCursor)

    def _resizeWidget(self, pos):
        """调整窗口大小"""
        if self.Direction == None:
            return
        mpos = pos - self._mpos
        xPos, yPos = mpos.x(), mpos.y()
        geometry = self.geometry()
        x, y, w, h = geometry.x(), geometry.y(), geometry.width(), geometry.height()
        if self.Direction == LeftTop:  # 左上角
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
        elif self.Direction == RightBottom:  # 右下角
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos = pos
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos = pos
        elif self.Direction == RightTop:  # 右上角
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos.setX(pos.x())
        elif self.Direction == LeftBottom:  # 左下角
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos.setY(pos.y())
        elif self.Direction == Left:  # 左边
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            else:
                return
        elif self.Direction == Right:  # 右边
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos = pos
            else:
                return
        elif self.Direction == Top:  # 上面
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            else:
                return
        elif self.Direction == Bottom:  # 下面
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos = pos
            else:
                return
        self.setGeometry(x, y, w, h)


class MainWindow(QWidget):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        layout = QVBoxLayout(self, spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    style = CommonHelper.readQss("./res/whitethese.qss")
    app.setStyleSheet(style)
    mainWnd = FramelessWindow()
    mainWnd.setWindowTitle('测试标题栏')
    mainWnd.setWindowIcon(QIcon('epolestar ix0.ico'))
    mainWnd.setIcon(QIcon('epolestar ix0.ico'))
    mainWnd.setWidget(QWidget())
    mainWnd.show()
    sys.exit(app.exec_())





