from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QEnterEvent, QPainter, QColor, QPen, QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QPushButton, QComboBox

from utils.window.res.default import *


class CommonHelper(object):
    def __init__(self):
        pass

    @staticmethod
    def readQss(stylePath):
        with open(stylePath, 'r', encoding="utf-8") as f:
            return f.read()


class TitleBar(QWidget):

    def __init__(self, parent=None):
        super(TitleBar, self).__init__(parent)
        self.win = parent
        # widget背景样式不被父窗体覆盖
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.mPos = None
        self.nheight = 20
        # 图标的默认大小
        self.iconSize = TITLE_ICON_SIZE
        self.theseState = THESE_STATE_WHITE  # 换肤按钮状态标记(深色, 浅色)
        # 设置默认背景颜色，否则由于受到父窗口的影响导致透明？？
        self.setAutoFillBackground(True)

        self._initViews()

    def _initViews(self):
        self.setFixedHeight(TITLE_BAR_HEIGHT)

        palette = self.palette()
        palette.setColor(palette.Window, QColor(240, 240, 240))
        self.setPalette(palette)
        # 布局
        layout = QHBoxLayout(self, spacing=0)
        layout.setContentsMargins(0, 0, 0, 0)
        # 窗口图标
        self.iconLabel = QLabel(self, objectName='iconLabel')
        # 窗口标题
        self.titleLabel = QLabel(self, objectName='titleLabel')
        self.titleLabel.setMargin(5)

        # 利用webdings字体来显示图标
        font = self.font() or QFont()
        font.setFamily('Webdings')
        # 最小化按钮
        self.buttonMinimum = QPushButton('0', self, font=font, objectName='buttonMinimum')
        # 最大化/还原按钮
        self.buttonMaximum = QPushButton('1', self, font=font, objectName='buttonMaximum')
        # 关闭按钮
        self.buttonClose = QPushButton('r', self, font=font, objectName='buttonClose')

        self.theseSelect = QPushButton()
        self.theseSelect.setObjectName("theseSelect")
        self.theseSelect.setIcon(QIcon("icon/whitethese.png"))
        self.theseSelect.clicked.connect(self._theseCallback)

        self.buttonMinimum.setFixedSize(TITLE_BUTTON_SIZE, TITLE_BUTTON_SIZE)
        self.buttonMaximum.setFixedSize(TITLE_BUTTON_SIZE, TITLE_BUTTON_SIZE)
        self.buttonClose.setFixedSize(TITLE_BUTTON_SIZE, TITLE_BUTTON_SIZE)

        self.iconLabel.setFixedSize(TITLE_LABEL_SIZE, TITLE_LABEL_SIZE)
        self.titleLabel.setFixedHeight(TITLE_LABEL_SIZE)
        self.iconLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setAlignment(Qt.AlignCenter)

        self.buttonMinimum.clicked.connect(self.win.showMinimized)
        self.buttonMaximum.clicked.connect(self.showMaximized)
        self.buttonClose.clicked.connect(self.closeWindow)

        layout.addWidget(self.iconLabel)
        layout.addWidget(self.titleLabel)
        # 中间伸缩条
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addWidget(self.theseSelect)
        layout.addWidget(self.buttonMinimum)
        layout.addWidget(self.buttonMaximum)
        layout.addWidget(self.buttonClose)
        layout.setSpacing(2)
        # self.setHeight()

    def _theseCallback(self):
        if self.theseState == THESE_STATE_DARK:
            self.win.setStyleSheet("""""")
            self.win._widget.contentEdit.sendSetThemeSignal('vs')

            self.win.setWinThese(THESE_STATE_WHITE)
        elif self.theseState == THESE_STATE_WHITE:
            self.win.setStyleSheet("""""")
            self.win._widget.contentEdit.sendSetThemeSignal('vs-dark')

            self.win.setWinThese(THESE_STATE_DARK)

    def showMaximized(self):
        """最大化、还原"""
        if self.buttonMaximum.text() == '1':
            # 最大化
            self.buttonMaximum.setText('2')
            self.win.showMaximized()
            self.win.setWindowState(Qt.WindowMaximized)
        else: #还原
            self.buttonMaximum.setText('1')
            self.win.showNormal()
            # self.win.setWindowState(Qt.WindowNoState)

    def closeWindow(self):
        """关闭窗口"""
        self.win.close()

    def setHeight(self, height=TITLE_BAR_HEIGHT):
        """设置标题栏高度"""
        self.setFixedHeight(height)
        # 设置右边按钮的大小
        self.buttonMinimum.setMinimumSize(height, height)
        self.buttonMinimum.setMaximumSize(height, height)
        self.buttonMaximum.setMinimumSize(height, height)
        self.buttonMaximum.setMaximumSize(height, height)
        self.buttonClose.setMinimumSize(height, height)
        self.buttonClose.setMaximumSize(height, height)

    def setTitle(self, title):
        """设置标题"""
        self.titleLabel.setText(title)

    def setIcon(self, icon):
        """设置图标"""
        self.iconLabel.setPixmap(icon.pixmap(self.iconSize, self.iconSize))

    def setIconSize(self, size):
        """"设置图标大小"""
        self.iconSize = size

    def enterEvent(self, event):
        """重写鼠标进入事件"""
        self.setCursor(Qt.ArrowCursor)
        super(TitleBar, self).enterEvent(event)

    def mouseDoubleClickEvent(self, event):
        """双击标题栏事件"""
        #TODO:
        if self.titleLabel.text() == '极星量化':
            self.showMaximized()
        return QWidget().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.mPos = event.globalPos()
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标弹起事件"""
        self.mPos = None
        return QWidget().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.win.windowState() == Qt.WindowNoState:
            self.nheight = self.win.geometry().height()

        if event.buttons() == Qt.LeftButton and self.mPos:
            if event.pos() == self.mPos:
                return
            if self.win.windowState() == Qt.WindowMaximized:
                MaxWinWidth = self.width()        # 窗口最大化宽度
                WinX = self.win.geometry().x()    # 窗口屏幕左上角x坐标
                self.win.showNormal()
                self.buttonMaximum.setText('1')
                # 还原后的窗口宽和高
                nwidth = self.width()
                nheight = self.nheight
                x, y = event.globalPos().x(), event.globalPos().y()
                x = x - nwidth * (x-WinX)/MaxWinWidth

                self.win.setGeometry(x, 1, nwidth, nheight)
                return

            movePos = event.globalPos() - self.mPos
            self.mPos = event.globalPos()
            self.win.move(self.win.pos() + movePos)
        return QWidget().mouseMoveEvent(event)