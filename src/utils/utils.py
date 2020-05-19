import os
import pickle
import time
from datetime import datetime

from capi.com_types import *


def rgb_to_hex(r, g, b):
    output = "#"
    tmp = (r, g, b)
    for x in tmp:
        if x < 16:
            output = output + "0" + hex(x)[2:]
        else:
            output = output + hex(x)[2:]
    return output


def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
    # with open(path, "rb") as f:
        data = f.read()
    return data


def int2date(d):
    millisecond = d%1000
    second = int(d/1000)%100
    minute = int(d/100000)%100
    hour = int(d/10000000)%100
    day = int(d/1000000000)%100
    month = int(d/100000000000)%100
    year = int(d/10000000000000)
    time = '{:0>4d}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}:{:0>2d}.{:0>3d}'.format(year, month, day, hour, minute, second, millisecond)
    return time


def save(data, runMode, fileName):
    """
    将回测报告数据保存到本地文件
    :param data: 报告展示数据
    :param runMode: 策略运行模式
    :param fileName: 策略文件名(含后缀）
    :return:
    """
    # 保存回测运行数据
    runType = formatExecuteType(runMode)
    strategyName, extension = os.path.splitext(fileName)
    fileDir = os.path.abspath(r"./reportdata/")
    if not os.path.exists(fileDir):
        os.makedirs(fileDir)

    currentTime = time.strftime('%Y-%m-%d %H.%M.%S', time.localtime(time.time()))
    fileName = fileDir + '\\' + strategyName + '\\' + runType + currentTime + '.pkl'
    strategyPath = fileDir + '\\' + strategyName

    if not os.path.exists(strategyPath):
        os.mkdir(strategyPath)
        with open(fileName, 'wb') as f:
            pickle.dump(data, f)

    else:
        with open(fileName, 'wb') as f:
            pickle.dump(data, f)

    return fileName


def formatExecuteType(flag):
    if flag:
        return "[实盘]"

    else:
        return "[回测]"

# def parseYMD(date):
#     """
#     将日期（20111111）转换为指定格式
#     :param date: 日期
#     :return: 时间组成的字符串：'20110203'
#     """
#     year_, mon_, day_ = date.split("/")
#     tempDate = datetime(int(year_), int(mon_), int(day_))
#     return datetime.strftime(tempDate, '%Y%m%d')

def parseTime(time):
    """
    将时刻转换为指定格式
    :param time: 时刻格式：hhmmss
    :return: 时间组成的字符串：’yyyymmddhhmmss'
    """
    now_ = datetime.now()
    tempTime = datetime.strftime(now_, '%Y%m%d')
    return tempTime + time


# 含中文字符串截断防止乱码
def subString(string, length):
    """
    :param string: utf-8编码字符串
    :param length: 字符数
    :return:
    """
    if length >= len(string):
        return string

    result = ""
    i = 0
    p = 0
    while True:
        ch = ord(string[i]) if type(string[0]) == str else string[i]
        if ch >= 252:
            p = p + 6
        elif ch >= 248:
            p = p + 5
        elif ch >= 240:
            p = p + 4
        elif ch >= 224:
            p = p + 3
        elif ch >= 192:
            p = p + 2
        else:
            p = p + 1

        if p > length:
            break
        else:
            i = p
    return string[0:i]

