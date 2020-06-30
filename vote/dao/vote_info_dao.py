# coding=utf-8
from vote import redis_conn
from vote.constants import *
from vote.utils import load_data_util


def get_vote_info(username,cid):
    """查询username给cid的投票情况
    :param username:
    :param cid:
    :return:
    """
    flag = redis_conn.exists(username + REDIS_SPLIT + cid)
    if flag != 1:
        # 加载选手的选票信息
        load_data_util.load_vote_info_to_redis(cid)
    vote_num = redis_conn.get(username + REDIS_SPLIT + cid)
    if vote_num is None:
        return 0
    else:
        return vote_num


def update_vote_info(username,cid,vote_num):
    """更新缓存中的投票信息
    :return:
    """
    redis_conn.set(str(username) + REDIS_SPLIT + str(cid), int(vote_num) )
