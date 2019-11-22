import sys
sys.path.append(".")

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qtui.reportview.dir import Dir
from qtui.reportview.tab import Tab


class ReportView(QWidget):

    # 显示回测报告窗口信号
    reportShowSig = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ReportView, self).__init__(parent)
        self.parent=parent
        self._windowTitle = "回测报告"
        self._iconPath = r"icon/epolestar ix2.ico"
        self.styleFile = r"qtui/reportview/style.qss"

        self._datas = None

        self.setWindowTitle(self._windowTitle)
        self.setWindowIcon(QIcon(self._iconPath))
        # self.resize(1000, 600)
        # self.setMinimumSize(600, 600)
        # self.setMaximumSize(1000, 600)
        # self.setObjectName(self._objName)

        # 初始化界面
        self._initUI()
        # 接收报告显示信号
        self.reportShowSig.connect(self.showCallback)

    def _initUI(self):
        # style = CommonHelper.readQss(self.styleFile)
        # self.setStyleSheet(style)

        vLayout = QHBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)
        vLayout.setSpacing(0)

        self.tab = Tab()
        self.tab.setObjectName("ReportTab")
        dir = Dir(self)

        vLayout.addSpacing(0)
        vLayout.addWidget(dir)
        vLayout.setSpacing(1)
        vLayout.addWidget(self.tab)
        vLayout.setSpacing(2)

        self.setLayout(vLayout)

    def showCallback(self, datas):
        # 传入回测数据
        self._datas = datas

        self.tab.showData(self._datas)
        print("BBB")
        self.parent.show()
        self.parent.raise_()
        # self.show()

