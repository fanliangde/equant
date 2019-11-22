import os
import sys
import shutil
import pickle
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class FileSystemModel(QFileSystemModel):
    """Overwrite columnCount"""
    def columnCount(self, parent: QModelIndex = ...):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        # 鼠标悬停显示目录名称
        if role == Qt.ToolTipRole:
            filePath = self.filePath(index)
            if filePath and not os.path.isdir(filePath):
                return os.path.basename(filePath)
        elif role == Qt.DisplayRole:
            filePath = self.filePath(index)
            return os.path.basename(filePath)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable


class Dir(QTreeView):
    """The directory of report data"""
    def __init__(self, parent=None):
        super(Dir, self).__init__(parent)

        self._win = parent
        self._dirPath = r"./reportdata"
        self._initUI()
        self.setHeaderHidden(True)
        self.sizeHint()

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setMaximumWidth(200)

        # 选中多行
        # self.setSelectionMode(self.MultiSelection)  # 鼠标点击多选
        self.setSelectionMode(self.ExtendedSelection)

        self.doubleClicked.connect(self.doubleClickedCallback)

        # 允许右键菜单
        # self.setContextMenuPolicy(Qt.CustomContextMenu)

    def _initUI(self):
        self.model = FileSystemModel()
        self.model.setRootPath(self._dirPath)

        self.setAnimated(False)
        self.setSortingEnabled(True)

        self.setModel(self.model)
        # 需要加上这句setRootPath才生效
        self.setRootIndex(self.model.index(self._dirPath))


    def contextMenuEvent(self, evt):
        menu = QMenu(self)

        deleteMenu = QAction(QIcon(r'icon/delete_transparent.png'), "删除", menu)
        deleteMenu.triggered.connect(self.deleteItems)

        menu.addAction(deleteMenu)
        menu.exec_(evt.globalPos())

    def deleteItems(self):
        indexList = self.selectionModel().selectedIndexes()
        for modelIndex in indexList:
            filePath = self.model.filePath(modelIndex)
            if filePath and os.path.isdir(filePath):
                shutil.rmtree(filePath)
            else:
                os.remove(filePath)

    def doubleClickedCallback(self, QModelIndex):
        if self.model.fileInfo(QModelIndex).isDir():
            return

        filePath = self.model.filePath(QModelIndex)
        # fileName = self.model.fileName(QModelIndex)
        datas = self._parseData(filePath)
        self.showResult(datas)

    @staticmethod
    def _parseData(filePath):
        with open(filePath, 'rb') as f:
            data = pickle.load(f)
            return data
        return None

    def showResult(self, datas):
        """
        更新回测报告数据
        """
        self._win.tab.showData(datas)


