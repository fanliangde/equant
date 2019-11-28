import os
import sys
path = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.abspath(path))


import platform
import time
import traceback
import requests
from multiprocessing import Process, Queue

from PyQt5.QtWidgets import QMessageBox

from engine.engine import StrategyEngine
from qtui.control import Controller
from utils.logger import Logger


VERSION = ""

URL = "https://gitee.com/epolestar/equant/raw/master/VerNo.txt"


def excepthook_(exctype, value, tb):
    """
     显示异常的详细信息
    """
    sys.__excepthook__(exctype, value, tb)
    msg = "".join(traceback.format_exception(exctype, value, tb))
    QMessageBox.critical(
        None, "Exception", msg, QMessageBox.Ok
    )


def run_log_process(logger):
    logger.run()


def run_engine_process(engine):
    engine.run()


def checkUpdate(logger):
    try:
        if os.path.exists('../VerNo.txt'):
            with open('../VerNo.txt', 'r') as f:
                VERSION = f.read()

            lvl = VERSION.split('.')[:-1]
            lmv = '.'.join(lvl)

        rsp = requests.get(URL, timeout=10)
        if rsp.status_code == 200:
            rvstr = rsp.content.decode('utf-8')
            rvl = rvstr.split('.')[:-1]
            rmv = '.'.join(rvl)

        if (len(lmv) == len(rmv) > 0 and rmv > lmv) or (0 < len(lmv) != len(rmv)):
            logger.info("Equant version need update local: %s, remote: %s" % (lmv, rmv))
            time.sleep(3)
            cmdstr = '"start %s %s.0"' % (os.path.abspath("..") + "\\update.bat ", rmv)
            logger.info("Update cmdstr:%s" % cmdstr)
            curDir = os.getcwd()
            os.chdir(os.path.abspath(os.path.join(curDir, "..")))
            os.system(cmdstr)
            os.chdir(curDir)
        else:
            logger.info("Equant version don't need update, local:%s, remote:%s" % (lmv, rmv))
    except Exception as e:
        logger.error("checkUpdate Error:%s" % (traceback.format_exc()))


def saveMainPid(pid=""):
    path = os.getcwd()
    logDir = os.path.join(path, "log")
    if not os.path.exists(logDir):
        os.makedirs(logDir)
    with open("log/mainpid.log", 'w') as f:
        f.write(str(pid))


def main():
    # 创建日志模块
    logger = Logger()
    log_process = Process(target=run_log_process, args=(logger,))
    log_process.start()

    saveMainPid(os.getpid())

    # 检查软件更新
    checkUpdate(logger)

    # 创建策略引擎到界面的队列，发送资金数据
    eg2ui_q = Queue(10000)
    # 创建界面到策略引擎的队列，发送策略全路径
    ui2eg_q = Queue(10000)

    # 创建策略引擎
    engine = StrategyEngine(logger, eg2ui_q, ui2eg_q)
    engine_process = Process(target=run_engine_process, args=(engine,))
    engine_process.start()

    control = Controller(logger, ui2eg_q, eg2ui_q)
    control.run()
    time.sleep(3)
    import atexit
    def exitHandler():
        control.receiveEgThread.stop()
        # 1. 先关闭策略进程, 现在策略进程会成为僵尸进程
        # todo 此处需要重载engine的terminate函数
        # 2. 关闭engine进程
        engine_process.terminate()
        engine_process.join()
        log_process.terminate()
        log_process.join()
    atexit.register(exitHandler)


if __name__ == '__main__':
    sys.excepthook = excepthook_
    # ------------任务栏显示app的图标-----------------
    if 'Windows' == platform.system():
        import ctypes
        myappid = 'equant.ui.view.QuantApplication'  # app路径
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # ------------------------------------------------
    main()

