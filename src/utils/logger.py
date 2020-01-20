import logging
import sys,os
from multiprocessing import Queue, Process
import queue
import time
import psutil
import datetime
from copy import deepcopy


class MyHandlerText(logging.StreamHandler):
    '''put log to Tkinter Text'''
    def __init__(self, textctrl):
        logging.StreamHandler.__init__(self) # initialize parent
        self.textctrl = textctrl

    def emit(self, record):
        msg = self.format(record)
        self.textctrl.config(state="normal")
        self.textctrl.insert("end", msg + "\n")
        self.flush()
        self.textctrl.config(state="disabled")


class MyFileHandler(logging.FileHandler):
    def __init__(self, file, mode):
        self.fileFd = open(file, mode=mode)
        logging.FileHandler.__init__(self, file, mode=mode)

    def emit(self, record):
        tmpRecord = deepcopy(record)
        tmpRecord.msg = record.msg[0]
        msg = self.format(tmpRecord)
        target = record.msg[1]
        # if target != 'T' and target != 'S':
        #     self.fileFd.write(msg+'\n')
        #     self.fileFd.flush()
        if target != "T" and target !="S" and target != "U":
            self.fileFd.write(msg+'\n')
            self.fileFd.flush()


class MyHandlerQueue(logging.StreamHandler):
    def __init__(self, gui_queue, trade_log, user_log):
        logging.StreamHandler.__init__(self)  # initialize parent
        self.gui_queue = gui_queue
        self.trade_log = trade_log
        self.user_log  = user_log

    def emit(self, record):
        #最多等待1秒
        target = record.msg[1]
        record.msg = record.msg[0]
        msg = self.format(record)

        if target == "T":
            self.trade_log.write(msg+"\n")
            self.trade_log.flush()
        elif target == "U":  # 用户日志标志
            self.user_log.write(msg+"\n")
            self.user_log.flush()
            try:
                self.gui_queue.put_nowait([target, msg])
            except queue.Full:
                time.sleep(0.1)
                print("用户日志放入队列时阻塞")
        else:
            try:
                self.gui_queue.put_nowait([target, msg])
            except queue.Full:
                time.sleep(0.1)
                print("界面日志放入队列时阻塞")

        """
        if target == 'S':
            try:
                self.sig_queue.put_nowait(msg)
            except queue.Full:
                time.sleep(0.1)
                print("订单放入队列时阻塞")
        elif target == 'E':
            try:
                self.err_queue.put_nowait(msg)
            except queue.Full:
                time.sleep(0.1)
                print("调试信息放入队列时阻塞")
        elif target == 'T':
            self.trade_log.write(msg+"\n")
            self.trade_log.flush()
        elif target == "U":   # 用户日志标志
            try:
                # 用户日志同时写入文件和界面
                self.user_log.write(msg+"\n")
                self.user_log.flush()
                self.usr_queue.put_nowait(msg)
            except queue.Full:
                time.sleep(0.1)
                print("界面日志放入队列时阻塞")

        else:
            try:
                self.gui_queue.put_nowait(msg)
            except queue.Full:
                time.sleep(0.1)
                print("界面日志放入队列时阻塞")
            # self.gui_queue.put_nowait(msg, block=False, timeout=1)
        """


class Logger(object):
    def __init__(self):
        #process queue
        self.log_queue = Queue(20000)
        self.gui_queue = Queue(20000)
        
    def _initialize(self):

        self.logpath = r"./log/"
        self.hispath = r"./log/his/"
        for path in (self.logpath, self.hispath):
            if not os.path.exists(path):
                os.makedirs(path)

        # 重命名历史日志
        self.renameHisLog()

        trade_path = self.logpath + "trade.dat"
        user_path  = self.logpath + "user.log"
        sys_path   = self.logpath + "equant.log"

        #交易日志
        self.trade_log = open(trade_path, mode='a', encoding='utf-8')
        #用户日志
        self.user_log  = open(user_path, mode='a', encoding='utf-8')
        #系统日志
        # self.sys_log   = open(sys_path, mode='a', encoding='utf-8')

        #logger config
        self.logger = logging.getLogger("equant")
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter("[%(levelname)7s][%(asctime)-15s]: %(message)s")

        self.level_dict = {"DEBUG":logging.DEBUG, "INFO":logging.INFO, "WARN":logging.WARN, "ERROR":logging.ERROR}
        self.level_func = {"DEBUG":self.logger.debug, "INFO":self.logger.info, "WARN": self.logger.warning, "ERROR": self.logger.error}
        
        self.add_handler()

    def run(self):
        #在子进程中做初始化，否则打印失效
        self._initialize()
        '''从log_queue中获取日志，刷新到文件和控件上'''
        while True:
            try:
                data_list = self.log_queue.get(timeout=0.5)
            except:
                ppid = os.getppid()
                if ppid == 1 or ppid not in psutil.pids():
                    os._exit(0)

            if data_list is None: break
            #数据格式不对
            self.level_func[data_list[0]](data_list[1:])

    def renameHisLog(self):
        """重命名历史日志文件"""
        # 重命名历史日志文件
        lognames = ["trade.dat", "equant.log", "user.log"]
        time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        for name in lognames:
            path = self.logpath + name
            his_path = self.hispath + name[:-4] + time_now + name[-4:]

            if os.path.exists(path):
                os.rename(path, his_path)

    def _log(self, level, target, s):
        """s为区分打印信息来源的标志"""
        data = []
        data.append(level)
        data.append(target)
        data.append(s)
        self.log_queue.put(data)

    def get_log_queue(self):
        return self.log_queue

    def getGuiQ(self):
        return self.gui_queue

    def add_handler(self):
        #设置文件句柄
        log_path = self.logpath + "equant.log"
        #file_handler = logging.FileHandler(self.logpath + "equant.log", mode='a')

        file_handler = MyFileHandler(log_path, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
        #设置窗口句柄
        gui_handler = MyHandlerQueue(self.gui_queue, self.trade_log, self.user_log)
        gui_handler.setLevel(logging.DEBUG)
        gui_handler.setFormatter(self.formatter)
        self.logger.addHandler(gui_handler)
        #设置控制台句柄
        cout_handler = logging.StreamHandler(sys.stdout)
        cout_handler.setLevel(logging.DEBUG)
        cout_handler.setFormatter(self.formatter)
        self.logger.addHandler(cout_handler)

    def debug(self, s, target="s"):
        self._log("DEBUG", s, target)

    def info(self, s, target="s"):
        self._log("INFO", s, target)

    def warn(self, s, target="s"):
        self._log("WARN", s, target)

    def error(self, s, target="s"):
        self._log("ERROR", s, target)

    # TODO: sig_info不需要了？
    def sig_info(self, s, target='S'):
        self.info(s, target)

    # 交易日志接口
    def trade_info(self, s, target='T'):
        self.info(s, target)

    # 策略错误
    def err_error(self, s, target='E'):
        self.error(s, target)

    # 用户日志接口
    def user_debug(self, s, target="U"):
        self.debug(s, target)

    def user_info(self, s, target="U"):
        self.info(s, target)

    def user_warn(self, s, target="U"):
        self.warn(s, target)

    def user_error(self, s, target="U"):
        self.error(s, target)
