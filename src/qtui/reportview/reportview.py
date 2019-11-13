import sys
sys.path.append(".")

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qtui.reportview.dir import Dir
from qtui.reportview.tab import Tab
from qtui.reportview.commonhelper import CommonHelper


class ReportView(QWidget):

    # 显示回测报告窗口信号
    reportShowSig = pyqtSignal(dict)

    def __init__(self):
        super(ReportView, self).__init__()
        self._windowTitle = "回测报告"
        self._objName = "Report"
        self._iconPath = r"icon/epolestar ix2.ico"
        self.styleFile = r"qtui/reportview/style.qss"

        self._datas = None

        self.setWindowTitle(self._windowTitle)
        self.setWindowIcon(QIcon(self._iconPath))
        self.resize(1000, 600)
        self.setMinimumSize(600, 600)
        self.setMaximumSize(1000, 600)
        self.setObjectName(self._objName)
        self.reportShowSig.connect(self.showCallback)

        # self._initUI()

    def _initUI(self):
        style = CommonHelper.readQss(self.styleFile)
        self.setStyleSheet(style)

        vLayout = QHBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)
        vLayout.setSpacing(0)

        dir = Dir()
        tab = Tab(self._datas)
        vLayout.addSpacing(0)
        vLayout.addWidget(dir)
        vLayout.setSpacing(1)
        vLayout.addWidget(tab)
        vLayout.setSpacing(2)

        self.setLayout(vLayout)

    def showCallback(self, datas):
        self._datas = datas
        self._initUI()
        self.show()


#
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     win = ReportView()
#     win.show()
#     sys.exit(app.exec_())