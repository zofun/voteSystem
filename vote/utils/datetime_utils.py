# coding=utf-8
import time


def get_today():
    """获取今天的日期字符串
    :return:
    """
    return time.strftime("%Y-%m-%d", time.localtime(time.time()))
