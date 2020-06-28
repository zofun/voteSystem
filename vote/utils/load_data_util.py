# coding=utf-8

from vote import db
from vote import redis_conn
from vote.constants import *


def load_rank_to_redis():
    """查询数据库，将处于参赛状态的参赛者<cid,vote_num>加载到redis的zset中
    一次加载100位参赛者的信息到redis中
    100条数据为一页
    :return:
    """
    competitors = db.competitors.find()
    for c in competitors:
        if int(c['state']) == COMPETITOR_STATE_JOIN:
            # 只将处于参赛状态的参赛者加入的redis的zset中，做排行处理
            last_vote_infos = db.votes.find({"cid": c['cid']}).sort([("date", -1)]).limit(1)
            vote_num = int(c['vote_num'])
            if last_vote_infos.count() != 0:
                # 低8位是时间戳，其余是票数
                timestamp = int(last_vote_infos[0]["date"])
                score = vote_num * 100000000 + (100000000 - timestamp % 100000000)
                redis_conn.zadd(REDIS_RANKING_LIST_KEY, {c['cid']: score})


def load_vote_info_to_redis(cid):
    """将参赛者所收获的选票信息加载到redis中
    :param cid:
    :return:
    """
    votes = db.votes.find({"cid": cid})
    for vote in votes:
        # 做累加
        vote_num = redis_conn.get(vote['username'] + REDIS_SPLIT + cid)
        if vote_num is None:
            vote_num = 0
        redis_conn.set(vote['username'] + REDIS_SPLIT + cid, int(vote['vote_num']) + int(vote_num))
        # 设置过期时间
        redis_conn.expire(vote['username'] + REDIS_SPLIT + cid, REDIS_KEY_EXPIRE_VOTE_SET)
