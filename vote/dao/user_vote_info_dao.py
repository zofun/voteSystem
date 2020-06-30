# coding=utf-8
from vote import redis_conn
from vote.constants import *
from vote import db


def get_user_vote_num(username):
    """获取用户的剩余选票信息
    :param username:
    :return:
    """
    flag = redis_conn.exists(REDIS_USER_VOTE_PREFIX + username)
    if flag != 1:
        # 如果用户的剩余选票信息在redis中没有，那么就进行加载
        user = db.users.find_one({"username": username})
        redis_conn.setex(REDIS_USER_VOTE_PREFIX + username, REDIS_KEY_EXPIRE_VOTE_SET,
                         user["vote"])
    return int(redis_conn.get(REDIS_USER_VOTE_PREFIX + username))


def update_user_vote_num(username, vote_num):
    """更新用户所拥有的选票信息
    :param username:
    :param vote_num: 当前拥有的选票的数量
    :return:
    """
    redis_conn.setex(REDIS_USER_VOTE_PREFIX + username, REDIS_KEY_EXPIRE_VOTE_SET,vote_num)

