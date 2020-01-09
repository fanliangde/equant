import win32con
import win32api
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebChannel import *
from PyQt5.QtWebEngineWidgets import *


class CodeEditor(QWebEngineView):
    openSignal = pyqtSignal(str, str)
    saveSignal = pyqtSignal(str)
    deleteSignal = pyqtSignal(str)
    renameSignal = pyqtSignal(str, str)
    setThemeSignal = pyqtSignal(str)
    on_switchSignal = pyqtSignal(str)
    on_saveMdySignal = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(CodeEditor, self).__init__(*args, **kwargs)

        self.__mdy_files = []
        self.__save_mdy = False

        # 创建web
        self.channel = QWebChannel(self)
        # 把自身对象传递进去
        self.channel.registerObject('Bridge', self)
        # 设置交互接口
        self.page().setWebChannel(self.channel)


# 向js发送指令
    def sendOpenSignal(self, file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
            self.openSignal.emit(file, text)
        except Exception as e:
            print(e)

    def sendSaveSignal(self, file):
        if file in self.__mdy_files:
            self.saveSignal.emit(file)

    def sendRenameSignal(self, file, newfile):
        self.renameSignal.emit(file, newfile)
        if file in self.__mdy_files:
            self.__mdy_files.append(newfile)
            self.__mdy_files.remove(file)

    def sendDeleteSignal(self, file):
        if file in self.__mdy_files:
            self.__mdy_files.remove(file)
        self.deleteSignal.emit(file)

    def sendSetThemeSignal(self, theme):
        self.setThemeSignal.emit(theme)


# 从js接收指令
    # 注意pyqtSlot用于把该函数暴露给js可以调用
    @pyqtSlot(str, str, bool)
    def do_save_file(self, file, text, confirm):
        if confirm and file in self.__mdy_files and \
            QMessageBox.Cancel == QMessageBox.question(self, '提示', '该策略已被修改，是否保存？', QMessageBox.Ok | QMessageBox.Cancel):
            return

        try:
            with open(file, mode='w', encoding='utf-8') as f:
                f.write(text.replace('\r', ''))
        except Exception as e:
            print(e)    

        self.__mdy_files.remove(file)  

        if self.__save_mdy and not len(self.__mdy_files):
            self.__save_mdy = False
            self.on_saveMdySignal.emit()

    @pyqtSlot(str)
    def on_switch_file(self, path):
        self.on_switchSignal.emit(path)

    @pyqtSlot(str, bool)
    def on_modify_file(self, file, modifyed):
        if modifyed and file not in self.__mdy_files:
            self.__mdy_files.append(file)
        elif not modifyed and (file in self.__mdy_files):
            self.__mdy_files.remove(file)

    @pyqtSlot(list, bool)
    def do_key_event(self, keys, is_group):
        for key in keys:
            win32api.keybd_event(int(key), 0, 0, 0)
            if not is_group:
                win32api.keybd_event(int(key), 0, win32con.KEYEVENTF_KEYUP, 0)

        if not is_group:
            return
        keys.reverse()
        for key in keys:
            win32api.keybd_event(int(key), 0, win32con.KEYEVENTF_KEYUP, 0)


# 常规函数
    def save_mdy(self):
        if not self.__mdy_files:
            return

        self.__save_mdy = True
        for file in self.__mdy_files:
            self.sendSaveSignal(file)

    def modify_count(self):
        return len(self.__mdy_files)
