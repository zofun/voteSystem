# coding=utf-8
from vote import redis_conn
from vote.constants import *
from vote.utils import load_data_util, zset_score_calculate


def update_rank_list(day_of_week, member, new_score):
    """更新zset榜单中成员的score
    :param day_of_week:
    :param member:
    :param new_score:
    :return:
    """
    # 首先判断zset是否存在，不存在则进行加载
    flag = redis_conn.exists(REDIS_RANKING_LIST_KEY + str(day_of_week))
    if flag != 1:
        # redis中还不存在zset排行榜则进行导入
        load_data_util.load_rank_to_redis(day_of_week)
    redis_conn.zadd(REDIS_RANKING_LIST_KEY + str(day_of_week), {member: new_score})


def get_rank_list(day_of_week, start, limit):
    """分页拿到当天的榜单
    :param day_of_week:
    :param start:
    :param limit:
    :return:
    """
    # 首先判断zset是否存在，不存在则进行加载
    flag = redis_conn.exists(REDIS_RANKING_LIST_KEY + str(day_of_week))
    if flag != 1:
        # redis中还不存在zset排行榜则进行导入
        load_data_util.load_rank_to_redis(day_of_week)
    rank_list = redis_conn.zrange(REDIS_RANKING_LIST_KEY + str(day_of_week), start=start, end=start + int(limit) - 1,
                                  desc=True, withscores=True)
    return rank_list


def get_vote_num(day_of_week, cid):
    flag = redis_conn.exists(REDIS_RANKING_LIST_KEY + str(day_of_week))
    if flag != 1:
        # redis中还不存在zset排行榜则进行导入
        load_data_util.load_rank_to_redis(day_of_week)
    score = redis_conn.zscore(REDIS_RANKING_LIST_KEY + str(day_of_week), cid)
    if score is None:
        return 0
    else:
        return zset_score_calculate.get_vote_num(score)


def get_rev_rank(day_of_week,cid):
    key=REDIS_RANKING_LIST_KEY+str(day_of_week)
    flag = redis_conn.exists(key)
    if flag != 1:
        # redis中还不存在zset排行榜则进行导入
        load_data_util.load_rank_to_redis(day_of_week)
    index = redis_conn.zrevrank(key, cid)
    return index




