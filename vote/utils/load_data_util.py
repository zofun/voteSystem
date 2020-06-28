# coding=utf-8

from vote import db
from vote import redis_conn
from vote.constants import *


def load_rank_to_redis(day_of_week):
    """查询数据库，将处于参赛状态的参赛者<cid,vote_num>加载到redis的zset中
    :param day_of_week: 按照哪一天的票数进行排行
    :return:
    """
    competitors = db.competitors.find()
    for c in competitors:
        if int(c['state']) == COMPETITOR_STATE_JOIN:
            # 只将处于参赛状态的参赛者加入的redis的zset中，做排行处理
            last_vote_infos = db.votes.find({"cid": c['cid']}).sort([("date", -1)]).limit(1)
            vote_info = db.competitor_vote_info.find_one({"cid": c['cid'], "day_of_week": day_of_week})
            if vote_info is None:
                vote_num=0
            else:
                vote_num = int(vote_info['vote_num'])
            if last_vote_infos.count() != 0:
                # 低8位是时间戳，其余是票数
                timestamp = int(last_vote_infos[0]["date"])
                score = vote_num * 100000 + (100000 - timestamp % 100000)
                redis_conn.zadd(REDIS_RANKING_LIST_KEY, {c['cid']: score})
            else:
                redis_conn.zadd(REDIS_RANKING_LIST_KEY, {c['cid']: 0})


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
