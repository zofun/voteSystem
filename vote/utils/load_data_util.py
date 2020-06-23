# coding=utf-8
from vote import db
from vote import redis_conn
from vote.constants import *


def load_rank_to_redis():
    """查询数据库，将处于参赛状态的参赛者<cid,vote_num>加载到redis的zset中
    :return:
    """
    competitors = db.competitors.find()
    for c in competitors:
        if c['state'] == 'join':
            # 只将处于参赛状态的参赛者加入的redis的zset中，做排行处理
            redis_conn.zadd(REDIS_RANKING_LIST_KEY, {c['cid']: c['vote_num']})


def load_vote_info_to_redis(cid):
    """将参赛者所收获的选票信息加载到redis中
    :param cid:
    :return:
    """
    competitor = db.competitors.find_one({"cid": cid})
    for u in competitor['vote']:
        redis_conn.sadd(REDIS_VOTE_PREFIX + cid, u)
