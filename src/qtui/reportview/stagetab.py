import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


LABELS = [
    "年度分析",
    "季度分析",
    "月度分析",
    "周分析",
    "日分析",
]


class BaseCell(QTableWidgetItem):
    def __init__(self, content):
        super(BaseCell, self).__init__()
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setContent(content)

    def setContent(self, content):
        self.setText(str(content))


class VLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super(VLayout, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 15)
        self.setSpacing(0)


class BaseTable(QTableWidget):
    def __init__(self, headers, parent=None):
        super(BaseTable, self).__init__(parent)
        self.headers = headers
        self.initTable()

    def initTable(self):
        self.setColumnCount(7)
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalHeaderLabels(self.headers)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setShowGrid(False)
        self.horizontalHeader().setFixedHeight(25)
        # 去除边框
        self.setFrameShape(QFrame.NoFrame)


class Label(QWidget):
    """Label bar"""
    def __init__(self, content, table, parent=None):
        super(Label, self).__init__(parent)
        self._content = content
        self._table = table
        self._parent = parent
        self._pixUp = QPixmap("icon/up.gif")
        self._pixDn = QPixmap("icon/down.gif")

        self._isOpend = True
        self.initLabel()

    def initLabel(self):
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(0)
        label = QLabel(self._content)
        label.setObjectName("StageLabel")
        label.setAlignment(Qt.AlignCenter)
        label.setFixedHeight(20)
        # label.setStyleSheet("background: rgb(44, 110, 173)")
        icon = QPushButton()
        icon.setObjectName("StageIcon")
        icon.setFixedSize(20, 20)
        icon.setStyleSheet("background: #0E6393;"
                           "border-style: flat;")
        icon.setIcon(QIcon(self._pixUp))
        icon.clicked.connect(self._toggle)

        self.icon = icon

        hbox.addWidget(label)
        hbox.addWidget(icon)

        self.setLayout(hbox)

    def _toggle(self):
        pHeight = self._parent.height()
        pLayout = self._parent.layout()
        fixheight = 100 + 75
        print("AAAAA: ", self._table.rowCount())
        print("BBBBB: ", self._table.verticalHeader().width)
        space = pHeight - fixheight
        rowCount = self._table.rowCount()
        width = self._table.verticalHeader().height()
        width = 45
        print("CCCCC: ", width)
        # self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self._table.setFixedHeight(pHeight - fixheight)

        if self._isOpend:
            self.icon.setIcon(QIcon(self._pixDn))
            self._table.hide()
        else:
            self.icon.setIcon(QIcon(self._pixUp))
            self._table.show()
        self._isOpend = not self._isOpend


class StageTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initStage()

    def initStage(self):
        vbox = VLayout()
        yvbox = VLayout()
        qvbox = VLayout()
        mvbox = VLayout()
        wvbox = VLayout()
        dvbox = VLayout()
        headers = ["年份", "权益", "净利润", "盈利率", "胜率", "平均盈利/亏损", "净利润增长速度"]
        self.ytable = BaseTable(headers)
        ylabel = Label("年度分析", self.ytable, self)
        yvbox.addWidget(ylabel)
        yvbox.addWidget(self.ytable)

        self.qtable = BaseTable(headers)
        qlabel = Label("季度分析", self.qtable, self)
        qvbox.addWidget(qlabel)
        qvbox.addWidget(self.qtable)

        self.mtable = BaseTable(headers)
        mlabel = Label("月度分析", self.mtable, self)
        mvbox.addWidget(mlabel)
        mvbox.addWidget(self.mtable)

        self.wtable = BaseTable(headers)
        wlabel = Label("周分析", self.wtable, self)
        wvbox.addWidget(wlabel)
        wvbox.addWidget(self.wtable)

        self.dtable = BaseTable(headers)
        dlabel = Label("日分析", self.dtable, self)
        dvbox.addWidget(dlabel)
        dvbox.addWidget(self.dtable)

        vbox.addLayout(yvbox)
        vbox.addLayout(qvbox)
        vbox.addLayout(mvbox)
        vbox.addLayout(wvbox)
        vbox.addLayout(dvbox)
        vbox.addStretch(1)

        self.setLayout(vbox)

    def addStageDatas(self, datas):
        tables = (self.ytable, self.qtable, self.mtable, self.wtable, self.dtable)
        for table, data in zip(tables, datas.values()):
            table.setRowCount(len(data))
            row = 0
            for d in data:
                cell1 = BaseCell(d['Time'])
                cell2 = BaseCell('{:.2f}'.format(float(d['Equity'])))
                cell3 = BaseCell('{:.2f}'.format(float(d['NetProfit'])))
                cell4 = BaseCell('{:.2%}'.format(float(d['Returns'])))
                cell5 = BaseCell('{:.2%}'.format(float(d['WinRate'])))
                cell6 = BaseCell('{:.2f}'.format(float(d['MeanReturns'])))
                cell7 = BaseCell('{:.2%}'.format(float(d['IncSpeed'])))
                table.setItem(row, 0, cell1)
                table.setItem(row, 1, cell2)
                table.setItem(row, 2, cell3)
                table.setItem(row, 3, cell4)
                table.setItem(row, 4, cell5)
                table.setItem(row, 5, cell6)
                table.setItem(row, 6, cell7)
                row += 1





