# coding=utf-8

from vote import db
from vote import redis_conn
from vote.constants import *


def load_rank_to_redis(day_of_week):
    """查询数据库，将处于参赛状态的参赛者<cid,vote_num>加载到redis的zset中，
    :param day_of_week: 按照哪一天的票数进行排行
    :return:
    """
    competitors = db.competitors.find()
    for c in competitors:
        if int(c['state']) == COMPETITOR_STATE_JOIN:
            # 获取它的票数和最近一次获得投票的时间
            last_vote_info = db.competitor_vote_info.find_one({"cid": c['cid'], "day_of_week": day_of_week})
            if last_vote_info is None:
                redis_conn.zadd(REDIS_RANKING_LIST_KEY + str(day_of_week), {c['cid']: 0})
            else:
                vote_num = int(last_vote_info['vote_num'])
                # 低8位是时间戳，其余是票数
                timestamp = int(last_vote_info["date"])
                if vote_num == 0 and timestamp == 0:
                    score = 0
                else:
                    score = vote_num * 100000 + (100000 - timestamp % 100000)
                redis_conn.zadd(REDIS_RANKING_LIST_KEY + str(day_of_week), {c['cid']: score})

