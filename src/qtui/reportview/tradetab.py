import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from report.fieldConfigure import *


def formatOrderTime(klineType, order):
    """格式化订单数据"""
    t = str(order['DateTimeStamp'])

    if klineType['KLineType'] == 'D':
        time = t[0:8]

    elif klineType["KLineType"] == 'M':
        time = t[0:8] + " " + t[8:10] + ":" + t[10:12]

    elif klineType["KLineType"] == "T":
        time = t[0:8] + " " + t[8:10] + ":" + t[10:12] + ":" + t[12:14] + '.' + t[-3:]

    else:
        time = t

    return time

class FilterDialog(QWidget):
    """过滤弹窗"""

    filterSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(FilterDialog, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        hLayout = QHBoxLayout()
        self.m_pLineEdit = QLineEdit()
        hLayout.addWidget(self.m_pLineEdit)
        hLayout.setContentsMargins(1, 0, 1, 0)
        hLayout.setSpacing(0)
        self.setLayout(hLayout)
        # 设置模态窗口
        # self.setWindowModality(Qt.ApplicationModal)
        # 回车信号
        self.m_pLineEdit.returnPressed.connect(self.confirmSlot)

        self.m_pLineEdit.installEventFilter(self)
        self.installEventFilter(self)

    def confirmSlot(self):
        # 发送筛选信号并关闭
        self.filterSignal.emit(self.filterMsg())
        self.close()

    def filterMsg(self):
        return self.m_pLineEdit.text().strip()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut and obj in [self, self.m_pLineEdit]:
            if self.m_pLineEdit.hasFocus() or self.hasFocus():
                pass
            else:
                self.close()
        return super(FilterDialog, self).eventFilter(obj, event)


class CustomHeaderView(QWidget):

    sortedUp = pyqtSignal(int)
    sortedDown = pyqtSignal(int)
    filterSignal = pyqtSignal(int, str)

    def __init__(self, index, parent=None):
        super(CustomHeaderView, self).__init__(parent)

        self.m_index = index

        self._sortFlag = 0  # 0: 降序  1: 升序

        self._initUI()

        self.toolButton_filter.setVisible(False)
        self.toolButton_sort.setVisible(False)

        self.m_pFilterDialog = FilterDialog()
        self.m_pFilterDialog.hide()

        self.setObjectName("CustomHeaderView")

        # 事件处理机制
        self.toolButton_sort.clicked.connect(self.sortClick)
        self.toolButton_filter.clicked.connect(self.filterClick)
        self.m_pFilterDialog.filterSignal.connect(self.filterEmit)

        # 事件过滤器
        self.widget_header.installEventFilter(self)
        # self.label_title.installEventFilter(self)
        self.toolButton_filter.installEventFilter(self)
        self.toolButton_sort.installEventFilter(self)

    def _initUI(self):
        self.hl = QHBoxLayout(self)

        self.hLayout = QHBoxLayout(self)
        self.hLayout.setContentsMargins(0, 0, 0, 0)
        self.hLayout.setSpacing(0)
        self.hLayout.setObjectName("hLayout")

        self.widget_header = QWidget(self)
        self.widget_header.setMouseTracking(False)
        self.widget_header.setObjectName("widget_header")

        self.label_title = QLabel(self.widget_header)
        # self.label_title.setStyleSheet("background-color: red")
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setObjectName("label_title")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.label_title.setSizePolicy(sizePolicy)
        self.hLayout.addWidget(self.label_title)

        self.toolButton_filter = QToolButton()
        self.toolButton_filter.setFixedWidth(15)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton_filter.sizePolicy().hasHeightForWidth())
        self.toolButton_filter.setSizePolicy(sizePolicy)
        self.toolButton_filter.setText("")
        icon = QIcon()
        # icon.addPixmap(QPixmap("C:/Users/pjwang/Desktop/TableTest/filter.png"), QIcon.Normal, QIcon.Off)
        icon.addPixmap(QPixmap("icon/filter.png"), QIcon.Normal, QIcon.Off)
        self.toolButton_filter.setIcon(icon)
        self.toolButton_filter.setIconSize(QSize(16, 16))
        self.toolButton_filter.setObjectName("toolButton_filter")

        self.hLayout.addWidget(self.toolButton_filter)

        # QToolButton一般只显示图标，不显示文本
        self.toolButton_sort = QToolButton(self.widget_header)
        self.toolButton_sort.setFixedWidth(15)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton_sort.sizePolicy().hasHeightForWidth())
        self.toolButton_sort.setSizePolicy(sizePolicy)
        self.toolButton_sort.setText("")
        icon1 = QIcon()
        icon1.addPixmap(QPixmap("icon/triangle_hollow.png"), QIcon.Normal, QIcon.Off)
        self.toolButton_sort.setIcon(icon1)
        self.toolButton_sort.setIconSize(QSize(8, 8))
        self.toolButton_sort.setCheckable(True)
        self.toolButton_sort.setAutoExclusive(True)
        self.toolButton_sort.setObjectName("toolButton_sort")
        self.hLayout.addWidget(self.toolButton_sort)

        self.widget_header.setLayout(self.hLayout)
        # self.gridLayout.addWidget(self.widget_header, 0, 0, 1, 1)

        self.hl.addWidget(self.widget_header)
        self.hl.setContentsMargins(0, 0, 0, 0)
        self.hl.setSpacing(0)
        self.setLayout(self.hl)


    def initUI(self):
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")

        self.gridLayout_2 = QGridLayout(self)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.widget_header = QWidget(self)
        self.widget_header.setMouseTracking(False)
        self.widget_header.setObjectName("widget_header")
        self.gridLayout_2 = QGridLayout(self.widget_header)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_title = QLabel(self.widget_header)
        self.label_title.setStyleSheet("background-color: red")
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setObjectName("label_title")
        self.horizontalLayout.addWidget(self.label_title)
        self.toolButton_filter = QToolButton(self.widget_header)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton_filter.sizePolicy().hasHeightForWidth())
        self.toolButton_filter.setSizePolicy(sizePolicy)
        self.toolButton_filter.setText("")
        icon = QIcon()
        icon.addPixmap(QPixmap("icon/filter.png"), QIcon.Normal, QIcon.Off)
        self.toolButton_filter.setIcon(icon)
        self.toolButton_filter.setIconSize(QSize(16, 16))
        self.toolButton_filter.setCheckable(True)
        self.toolButton_filter.setAutoExclusive(True)
        self.toolButton_filter.setAutoRaise(False)
        self.toolButton_filter.setObjectName("toolButton_filter")

        self.horizontalLayout.addWidget(self.toolButton_filter)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        # QToolButton一般只显示图标，不显示文本
        self.toolButton_sort = QToolButton(self.widget_header)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton_sort.sizePolicy().hasHeightForWidth())
        self.toolButton_sort.setSizePolicy(sizePolicy)
        self.toolButton_sort.setText("")
        icon1 = QIcon()
        icon1.addPixmap(QPixmap("icon/triangle_hollow.png"), QIcon.Normal, QIcon.Off)
        self.toolButton_sort.setIcon(icon1)
        self.toolButton_sort.setIconSize(QSize(8, 8))
        self.toolButton_sort.setCheckable(True)
        self.toolButton_sort.setAutoExclusive(True)
        self.toolButton_sort.setObjectName("toolButton_sort")

        self.horizontalLayout.addLayout(self.verticalLayout)
        self.horizontalLayout.setStretch(0, 1)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.widget_header, 0, 0, 1, 1)

    def labelTitleInstallEventFilter(self):
        """动态地给labelTitle安装事件过滤器"""
        self.label_title.installEventFilter(self)

    def sortClick(self):
        if self._sortFlag:
            self.sortUpClick()
        else:
            self.sortDownClick()

    def sortUpClick(self):
        # self.buttonGroup.setExclusive(True)
        # self.toolButton_filter.setChecked(False)
        # self.toolButton_sort.setChecked(True)
        self.sortedUp.emit(self.m_index)
        #
        self._sortFlag = 0
        icon1 = QIcon()
        icon1.addPixmap(QPixmap("icon/triangle_up.png"), QIcon.Normal, QIcon.Off)
        self.toolButton_sort.setIcon(icon1)

    def sortDownClick(self):
        # self.buttonGroup.setExclusive(True)
        # self.toolButton_filter.setChecked(False)
        # self.toolButton_sort.setChecked(False)
        self.sortedDown.emit(self.m_index)
        #
        self._sortFlag = 1
        icon1 = QIcon()
        icon1.addPixmap(QPixmap("icon/triangle_down.png"), QIcon.Normal, QIcon.Off)
        self.toolButton_sort.setIcon(icon1)

    def filterClick(self):
        # self.buttonGroup.setExclusive(True)
        # self.toolButton_filter.setChecked(True)
        # self.toolButton_sort.setChecked(False)
        p = self.mapToGlobal(QPoint(self.label_title.pos().x(), self.label_title.pos().y()))
        self.m_pFilterDialog.move(p.x(), p.y() + self.height())
        self.m_pFilterDialog.resize(self.size() + QSize(5, 0))
        self.m_pFilterDialog.show()

    def filterEmit(self, msg):
        self.filterSignal.emit(self.m_index, msg)

    def setDefaultSortIcon(self):
        # 设置排序默认图标
        if self.toolButton_sort.isVisible():
            self._sortFlag = 0
            icon1 = QIcon()
            icon1.addPixmap(QPixmap("icon/triangle_hollow.png"), QIcon.Normal, QIcon.Off)
            self.toolButton_sort.setIcon(icon1)

    def setTitle(self, text):
        self.label_title.setText(text)

    def title(self):
        self.label_title.text()

    def setAlignment(self, align):
        self.label_title.setAlignment(align)

    def sortVisible(self, status):
        self.toolButton_sort.setVisible(status)

    def filterVisible(self, status):
        self.toolButton_filter.setVisible(status)

    def getFilterMsg(self):
        return self.m_pFilterDialog.filterMsg()

    def eventFilter(self, obj, event):
        if (obj == self.widget_header) or (obj == self.label_title) or (obj == self.toolButton_filter) or (
                obj == self.toolButton_sort):
            self.setCursor(Qt.ArrowCursor)

        # 单击表头排序
        if obj == self.label_title and event.type() == QEvent.MouseButtonRelease:
            self.sortClick()

        return QWidget().eventFilter(obj, event)


HEADER_RIGHT_BORDER = 1


class CustomHorizontalHeaderView(QHeaderView):

    sortedUp = pyqtSignal(int)
    sortedDown = pyqtSignal(int)
    filterSignal = pyqtSignal(int, str)
    displayList = []

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super(CustomHorizontalHeaderView, self).__init__(orientation, parent)
        self.m_pTableFilterList = list()
        self.setSectionsMovable(True)
        self.setSectionsClickable(True)
        self.setStretchLastSection(True)
        self.setObjectName("CustomHorizontalHeader")

        self.sectionResized.connect(self.handleSectionResized)
        self.sectionMoved.connect(self.handleSectionMoved)

    def setModel(self, model):
        super(CustomHorizontalHeaderView, self).setModel(model)
        filterDisplayList = [1, 2, 3]  # 需要添加过滤按钮的列
        sortDisplayList = [0, 4, 5, 6, 7, 8, 9, 10]       # 需要添加排序的列
        for i in range(self.count()):
            pTableFilter = CustomHeaderView(i, self)
            pTableFilter.setTitle(str(self.model().headerData(i, Qt.Horizontal)))
            # 设置筛选图标和单击表头排序
            if i in filterDisplayList:
                pTableFilter.filterVisible(True)
                pTableFilter.labelTitleInstallEventFilter()
            # 设置排序和单击表头排序
            if i in sortDisplayList:
                pTableFilter.sortVisible(True)
                pTableFilter.labelTitleInstallEventFilter()

            pTableFilter.show()
            self.m_pTableFilterList.append(pTableFilter)

            pTableFilter.sortedUp.connect(self.sortedUpSlot)
            pTableFilter.sortedDown.connect(self.sortedDownSlot)
            pTableFilter.filterSignal.connect(self.filterSignalSlot)

    def sortedUpSlot(self, index):
        self.sortedUp.emit(index)
        for i in range(len(self.m_pTableFilterList)):
            if i == index:
                continue
            # 设置排序默认图标
            self.m_pTableFilterList[i].setDefaultSortIcon()

    def sortedDownSlot(self, index):
        self.sortedDown.emit(index)
        for i in range(len(self.m_pTableFilterList)):
            if i == index:
                continue
            # 设置排序默认图标
            self.m_pTableFilterList[i].setDefaultSortIcon()

    def filterSignalSlot(self, index, msg):
        # if not self.m_pTableFilterList[index].getFilterMsg().strip():
        #     self.m_pTableFilterList[index].clearFilterStatus()
        self.filterSignal.emit(index, msg)

    def headerDataChanged(self, orientation, logicalFirst, logicalLast):
        if logicalFirst < 0 or logicalLast > len(self.m_pTableFilterList):
            return

        if orientation == Qt.Horizontal:
            for i in range(logicalFirst, logicalLast+1):
                self.m_pTableFilterList[i].setTitle(str(self.model().headerData(i, Qt.Horizontal)))

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super(CustomHorizontalHeaderView, self).paintSection(painter, QRect(), logicalIndex)
        painter.restore()

        pTableFilter = self.m_pTableFilterList[logicalIndex]
        pTableFilter.setGeometry(self.sectionViewportPosition(logicalIndex), 0,
                                  self.sectionSize(logicalIndex) - HEADER_RIGHT_BORDER, self.height())
        pTableFilter.show()
        startShowIndex = self.visualIndexAt(0)
        for i in range(startShowIndex):
            self.m_pTableFilterList[i].hide()

    def fixSectionPositions(self):
        for i in range(len(self.m_pTableFilterList)):
            self.m_pTableFilterList[i].setGeometry(self.sectionViewportPosition(i), 0,
                                       self.sectionSize(i) - HEADER_RIGHT_BORDER, self.height())

    def handleSectionResized(self, i, oldSize, newSize):
        self.fixSectionPositions()

    def handleSectionMoved(self, logical, oldVisualIndex, newVisualIndex):
        self.fixSectionPositions()

    def resizeEvent(self, event):
        # QHeaderView().resizeEvent(event)
        super(CustomHorizontalHeaderView, self).resizeEvent(event)
        self.fixSectionPositions()


class CustomTableView(QTableView):
    def __init__(self, parent=None):
        super(CustomTableView, self).__init__(parent)
        self.m_pHHeaderView = CustomHorizontalHeaderView()
        self.m_pSortFilterModel = CustomFilterModel(self)
        self.initConnect()
        # self.setAlternatingRowColors(True)
        self.setHorizontalHeader(self.m_pHHeaderView)
        # self.horizontalHeader().setMinimumHeight(25)
        # self.horizontalHeader().setMaximumHeight(25)
        self.verticalHeader().hide()
        self.setObjectName("CustomTableView")

    def initConnect(self):
        self.m_pHHeaderView.sortedUp.connect(self.sortedUpSlot)
        self.m_pHHeaderView.sortedDown.connect(self.sortedDownSlot)
        self.m_pHHeaderView.filterSignal.connect(self.filterSignalSlot)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def setModel(self, model):
        self.m_pSortFilterModel.setSourceModel(model)
        super(CustomTableView, self).setModel(self.m_pSortFilterModel)

    def sortedUpSlot(self, index):
        self.m_pSortFilterModel.setFilterKeyColumn(index)
        self.m_pSortFilterModel.sort(index, Qt.AscendingOrder)

    def sortedDownSlot(self, index):
        self.m_pSortFilterModel.setFilterKeyColumn(index)
        self.m_pSortFilterModel.sort(index, Qt.DescendingOrder)

    def filterSignalSlot(self, index, msg):
        self.m_pSortFilterModel.setFilterKeyColumn(index)
        self.m_pSortFilterModel.setFilterFixedString(msg)


class CustomModel(QAbstractItemModel):
    _headers = [
        "时间",
        "合约",
        "交易类型",
        "下单类型",
        "成交数量",
        "成交价",
        "成交额",
        "委托数量",
        "平仓盈亏",
        "手续费",
        "滑点损耗"
    ]

    def __init__(self, orders, kLineInfo, parent=None):
        super(CustomModel, self).__init__(parent)
        self._orders = orders
        self._kLineInfo = kLineInfo

    def rowCount(self, parent):
        return len(self._orders)

    def columnCount(self, parent):
        return len(self._headers)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if index.row() > len(self._orders) or index.column() > len(self._headers):
            return QVariant()

        if role == Qt.DisplayRole:        # 数据被渲染为文本(数据为QString类型)

            eo = self._orders[index.row()]
            time = formatOrderTime(self._kLineInfo, eo["Order"])
            direct = DirectDict[eo["Order"]["Direct"]]
            offset = OffsetDict[eo["Order"]["Offset"]]
            cont = eo["Order"]["Cont"]
            tradeType = direct + offset
            orderType = OrderTypeDict[eo["Order"]["OrderType"]]
            orderQty = eo['Order']['OrderQty']
            orderPrice = '{:.2f}'.format(float(eo['Order']['OrderPrice']))
            turnover = '{:.1f}'.format(float(eo['Turnover']))
            liqProfit = '{:.1f}'.format(float(eo['LiquidateProfit']))
            cost = '{:.1f}'.format(float(eo['Cost']))
            slippage = '{:.1f}'.format(float(eo["SlippageLoss"]))
            stock = [time, cont, tradeType, orderType, orderQty, orderPrice, turnover, orderQty, liqProfit, cost,
                        slippage]

            return QVariant() if index.column() > len(stock) or index.column() < 0 else stock[index.column()]

        # elif role == Qt.EditRole:          # 数据可以在编辑器中进行编辑(数据为QString类型)
        #     stock = self._orders[index.row()]
        #     return QVariant() if index.column() > len(stock) or index.column() < 0 else stock[index.column()]

        return QVariant()

    def setData(self, index, value, role):
        if not index.isValid():
            print("index is valid: ")
            return False

        if role == Qt.EditRole:
            stock = self._orders[index.row()]
            stock[index.column()] = value
            self.dataChanged.emit(index, index)
            return True

        return False

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            if section < 0 or section > len(self._headers):
                return QVariant()
            return QVariant(self._headers[section])
        else:
            #TODO:
            return QVariant(str(section))

    def setHeaderData(self, section: int, orientation, value, role: int = ...):
        if role != Qt.EditRole:
            return False

        if orientation == Qt.Horizontal:
            self._headers[section] = str(value)
            # self._headers.replace(section, str(value))
            self.headerDataChanged.emit(Qt.Horizontal, section, section)
            return True
        else:
            return False

    def flags(self, index):
        if index.isValid():
            # 设置双击单元格可编辑
            # flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren | Qt.ItemIsEditable
            # 设置双击单元格不可编辑
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren
            return flags

        return QAbstractItemModel.flags(index)

    def index(self, row: int, column: int, parent: QModelIndex = ...):
        if row < 0 or column < 0 or column >= self.columnCount(parent) or column > len(self._headers):
            return QModelIndex()

        return self.createIndex(row, column)

    def parent(self, child: QModelIndex):
        return QModelIndex()

    #TODO: 该方法有问题
    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()

        if 0 <= column <= len(self._headers):
            if 0 <= column <= len(self._headers):
                self._datas.sort(key=lambda k: float(k[column]), reverse=order)

        self.layoutChanged.emit()


class CustomFilterModel(QSortFilterProxyModel):
    def __init__(self, parent):
        super(CustomFilterModel, self).__init__(parent)

    # def sort(self, column, order):
    #     self.sourceModel().sort(column, order)
    #     super(CustomFilterModel, self).sort(column, order)

    def lessThan(self, left_index, right_index):
        """
        比较方法
        用于判断紧邻的两个数据的大小
        """
        left_var = left_index.data(Qt.DisplayRole)
        right_var = right_index.data(Qt.DisplayRole)

        try:
            # 将字符串转化为数字
            left_int = eval(left_var)
            right_int = eval(right_var)
        except:
            left_int = left_var
            right_int = right_var

        return (left_int < right_int)