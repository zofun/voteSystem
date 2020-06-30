# coding=utf-8
from vote import redis_conn
from vote.constants import *
from vote import db


def get_user_vote_num(username):
    """获取用户的剩余选票信息
    :param username:
    :return:
    """

    key = REDIS_USER_VOTE_PREFIX + username
    vote_num = redis_conn.get(key)
    if vote_num is None:
        user = db.users.find_one({"username": username})
        if user is None:
            return None
        redis_conn.setex(REDIS_USER_VOTE_PREFIX + username, REDIS_KEY_EXPIRE_VOTE_SET,
                         user["vote"])
        return int(user["vote"])
    return int(vote_num)


def update_user_vote_num(username, vote_num):
    """更新用户所拥有的选票信息
    :param username:
    :param vote_num: 当前拥有的选票的数量
    :return:
    """
    redis_conn.setex(REDIS_USER_VOTE_PREFIX + username, REDIS_KEY_EXPIRE_VOTE_SET, vote_num)
