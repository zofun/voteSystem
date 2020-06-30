# coding=utf-8
from vote import redis_conn
from vote.constants import *
from vote.utils import load_data_util


def get_vote_info(username, cid):
    """查询username给cid的投票情况
    :param username:
    :param cid:
    :return:
    """
    key = username + REDIS_SPLIT + cid
    vote_num = redis_conn.get(key)
    if vote_num is None:
        load_data_util.load_vote_info_to_redis(cid)
        vote_num = redis_conn.get(key)
        if vote_num is None:
            return 0
        else:
            return int(vote_num)
    return int(vote_num)


def update_vote_info(username, cid, vote_num):
    """更新缓存中的投票信息
    :return:
    """
    redis_conn.set(str(username) + REDIS_SPLIT + str(cid), int(vote_num))
