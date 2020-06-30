# coding=utf-8
import time

from vote import redis_conn, REDIS_RANKING_LIST_KEY
from vote.constants import *


def get_score(vote_num, timestamp):
    """根据票数计算zset的score
    :param vote_num: 新的票数
    :param timestamp: 加票时的时间戳
    :return:
    """
    # todo 先去更新，更新后拿到返回值，从数据行中拿cid，vote_num,date然后去拼接score ok
    # 第5位是时间戳，高位是票数
    return int(vote_num) * SCORE_CONST + (SCORE_CONST - int(timestamp) % SCORE_CONST)


def get_vote_num(score):
    """ 通过redis zset中的分数计算出选票数
    :param score:  redis zset的分数
    :return:
    """
    return int(int(score) / 100000)
