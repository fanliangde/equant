#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import re
import shutil

from PyQt5.QtCore import QDir, QFileInfo, QFile, QSize, Qt, pyqtSignal, QPoint, QSortFilterProxyModel, QUrl
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QEnterEvent, QPainter, QColor, QPen, QIcon


class Tree(QTreeView):
    def __init__(self, model, quantWin):
        QTreeView.__init__(self)
        self._win = quantWin
        # model.setReadOnly(False)

        # self.setSelectionMode(self.SingleSelection)
        self._model = model
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, event):
        event.ignore()
        return
        m = event.mimeData()
        if m.hasUrls():
            for url in m.urls():
                if url.isLocalFile():
                    event.accept()
                    return
        event.ignore()

    def dropEvent(self, event):
        event.ignore()
        return
        if event.source():
            QTreeView.dropEvent(self, event)
        else:
            ix = self.indexAt(event.pos())
            if not self.model().isDir(ix):
                ix = ix.parent()
            pathDir = self.model().filePath(ix)
            if not pathDir:
                pathDir = self.model().filePath(self.rootIndex())
            m = event.mimeData()
            if m.hasUrls():
                urlLocals = [url for url in m.urls() if url.isLocalFile()]
                accepted = False
                for urlLocal in urlLocals:
                    path = urlLocal.toLocalFile()
                    info = QFileInfo(path)
                    n_path = QDir(pathDir).filePath(info.fileName())
                    o_path = info.absoluteFilePath()
                    if n_path == o_path:
                        continue
                    if info.isDir():
                        if QDir(n_path).exists():
                            reply = QMessageBox.question(self, '提示', '所选的分组中存在同名文件夹，是否全部覆盖？',
                                                         QMessageBox.Yes | QMessageBox.No)
                            if reply == QMessageBox.Yes:
                                shutil.rmtree(n_path)
                                shutil.copytree(o_path, n_path)
                        else:
                            print(o_path)
                            for file in os.walk(o_path):
                                print(file)
                            shutil.copytree(o_path, n_path)
                            self.strategy_filters.append(os.path.split(n_path)[1])
                            self._model.setNameFilters(self.strategy_filters)
                    else:
                        qfile = QFile(o_path)
                        fname = qfile.fileName()
                        if not fname.endswith('.py'):
                            QMessageBox.warning(self, "提示", "暂不支持该类型文件", QMessageBox.Yes)
                        if QFile(n_path).exists():
                            reply = QMessageBox.question(self, '提示', '所选的分组中存在同名文件，是否覆盖？',
                                                         QMessageBox.Yes | QMessageBox.No)
                            if reply == QMessageBox.Yes:
                                shutil.copy(o_path, n_path)
                        # qfile.rename(n_path)
                    accepted = True
                if accepted:
                    event.acceptProposedAction()


class MySortFilterProxyModel(QSortFilterProxyModel):
    """策略列表文件过滤"""
    def __init__(self):
        super(MySortFilterProxyModel, self).__init__()

    def filterAcceptsRow(self, rowProc, parentProc):
        sourceModel = self.sourceModel()
        if not sourceModel:
            return
        index = sourceModel.index(rowProc, 0, parentProc)
        name = sourceModel.fileName(index)
        if sourceModel.isDir(index):
            if name == "__pycache__":
                return False
            return True
        else:
            if name.endswith(".py") or name.endswith(".pyc"):
                return True
        return False


# def get_strategy_filters(root_path):
#     """获取策略根目录下所有可用的文件夹"""
#     strategy_filters = ['*.py', '*.pyc']
#     for current_path, dirs, files in os.walk(root_path):
#         if '__pycache__' not in dirs:
#             strategy_filters.extend(dirs)
#     return strategy_filters


def parseStrategtParam(strategyPath):
    """解析策略中的用户参数"""
    g_params = {}
    if not os.path.exists(strategyPath):
        return -1 # 策略文件不存在， -1错误码
    with open(strategyPath, 'r', encoding="utf-8") as f:
        content = [line.strip() for line in f]
        for c in content:
            # regex = re.compile(r"^g_params[\[][\"\'](.*)[\"\'][\]]\s*=[\s]*([^\s]*)[\s]*(#[\s]*(.*))?")
            regex1 = re.compile(r"^g_params[\[][\"\'](.*)[\"\'][\]]\s*=[\s]*(.*)[\s]*#[\s]*(.*)?")
            regex2 = re.compile(r"^g_params[\[][\"\'](.*)[\"\'][\]]\s*=[\s]*(.*)[\s]*#?[\s]*(.*)?")

            reg1 = regex1.search(c)
            reg2 = regex2.search(c)
            if reg1 or reg2:
                reg = reg1 if reg1 else reg2
                ret = [reg.groups()[1], reg.groups()[2]]
                # if ret[1] is None: ret[1] = ""
                try:
                    ret[0] = eval(ret[0])
                except:
                    pass
                g_params.update(
                    {
                        reg.groups()[0]: ret
                    }
                )
    return g_params


class FileIconProvider(QFileIconProvider):

    def __init__(self, *args, **kwargs):
        super(FileIconProvider, self).__init__(*args, **kwargs)
        self.DirIcon = QIcon("icon/dir_grey.gif")
        self.PyIcon = QIcon("icon/file_grey.gif")

    def icon(self, type_info):
        '''
        :param fileInfo: 参考http://doc.qt.io/qt-5/qfileinfo.html
        '''
        if isinstance(type_info, QFileInfo):
            # 如果type_info是QFileInfo类型则用getInfoIcon来返回图标
            return self.getInfoIcon(type_info)
        # 如果type_info是QFileIconProvider自身的IconType枚举类型则执行下面的方法
        # 这里只能自定义通用的几种类型，参考http://doc.qt.io/qt-5/qfileiconprovider.html#IconType-enum
        '''
        QFileIconProvider::Computer     0
        QFileIconProvider::Desktop      1
        QFileIconProvider::Trashcan     2
        QFileIconProvider::Network      3
        QFileIconProvider::Drive        4
        QFileIconProvider::Folder       5
        QFileIconProvider::File         6
        '''
        if type_info == QFileIconProvider.Folder:
            # 如果是文件夹
            return self.DirIcon
        return super(FileIconProvider, self).icon(type_info)

    def getInfoIcon(self, type_info):
        if type_info.isDir():  # 文件夹
            return self.DirIcon
        if type_info.isFile() and type_info.suffix() == "py":  # 文件并且是txt
            return self.PyIcon
        return super(FileIconProvider, self).icon(type_info)


class MyMessageBox(QMessageBox):

    # This is a much better way to extend __init__
    def __init__(self, *args, **kwargs):
        super(MyMessageBox, self).__init__(*args, **kwargs)
        # Anything else you want goes below

    # We only need to extend resizeEvent, not every event.
    def resizeEvent(self, event):

        result = super(MyMessageBox, self).resizeEvent(event)

        details_box = self.findChild(QTextEdit)
        # 'is not' is better style than '!=' for None
        if details_box is not None:
            details_box.setFixedSize(details_box.sizeHint())

        return result

def getText(parent,title, label, text=None):
    inputDialog = QInputDialog(parent)
    inputDialog.setMinimumWidth(450)
    inputDialog.setOkButtonText('确定')
    inputDialog.setCancelButtonText('取消')
    if text:
        inputDialog.setTextValue(text)
    inputDialog.setLabelText(label)
    inputDialog.setWindowTitle(title)
    ok = inputDialog.exec_()
    value = inputDialog.textValue()

    return value, ok


class EmptyDelegate(QItemDelegate):
    def __init__(self, parent):
        super(EmptyDelegate, self).__init__(parent)

    def createEditor(self, QWidget, QStyleOptionViewItem, QModelIndex):
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)

    model = QFileSystemModel()
    model.setIconProvider(FileIconProvider())  # 设置为自定义的图标提供类
    model.setRootPath("")
    tree = QTreeView()
    tree.setModel(model)

    tree.setAnimated(False)
    tree.setIndentation(20)
    tree.setSortingEnabled(True)

    tree.setWindowTitle("Dir View")
    tree.resize(640, 480)
    tree.show()

    sys.exit(app.exec_())
