# coding=utf-8
import time

from vote import redis_conn, REDIS_RANKING_LIST_KEY


def get_score(day_of_week, cid, add_vote_num):
    """ 计算zset的分数
    这个方法计算分数的时候需要依赖于zset，因此在调用该方法的时候需要确保zset已经被加载
    :param day_of_week:当前是星期几
    :param cid: 参赛者的id
    :param add_vote_num: 新加的票数
    :return:
    """
    # todo 先去更新，更新后拿到返回值，从数据行中拿cid，vote_num,date然后去拼接score
    old_score = redis_conn.zscore(REDIS_RANKING_LIST_KEY + str(day_of_week), cid)
    if old_score is None:
        old_score = 0
    # 取出的旧的票数
    old_vote = int(int(old_score) / 100000)
    # 获取当前秒级时间戳
    timestamp = int(time.time())
    # 拼接得到新的score
    new_score = (old_vote + int(add_vote_num)) * 100000 + (100000 - timestamp % 100000)
    return new_score


def get_vote_num(score):
    """ 通过redis zset中的分数计算出选票数
    :param score:  redis zset的分数
    :return:
    """
    return int(int(score) / 100000)