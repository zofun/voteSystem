# coding=utf-8
from datetime import datetime

import redis
from pymongo import MongoClient


def reset(config):
    """重置用户当天的票数，为每个参赛者新建一个当天的票数统计记录
    :return:
    """
    mongo_conn = MongoClient(config["mongo"])
    db = mongo_conn[config["mongo_db"]]

    pool = redis.ConnectionPool(host=config["redis_host"], port=config["redis_port"], decode_responses=True)
    redis_conn = redis.Redis(connection_pool=pool)

    # 重置每个用户拥有的选票数量
    result = db.users.update_many({"_id": {"$exists": True}}, {"$set": {"vote": config["user_vote_num"]}})
    print "重置用户拥有选票，一共影响的文档的数量为：%d" % result.modified_count

    # 清除mongo中的超过七天的榜单数据
    day_of_week = datetime.now().isoweekday()
    result = db.competitor_vote_info.delete_many({"day_of_week": day_of_week})
    print "删除旧的选票数量记录：%d" % result.deleted_count

    # 从redis 中删除超过七天的榜单数据 zset,分次删除
    delete_zset("rank_list" + str(day_of_week), redis_conn)

    # 为每个参赛者维护一个当日选票记录
    competitors = db.competitors.find()
    for competitor in competitors:
        db.competitor_vote_info.insert(
            {"cid": competitor['cid'], "day_of_week": day_of_week, "vote_num": 0, "date": "0"})
    print "当日选票记录建立完毕"


def delete_zset(zset_key, redis_coon):
    """分次删除zset，防止删除时间过长，导致redis阻塞时间过长
    :param zset_key:
    :param redis_coon:
    :return:
    """
    while redis_coon.zcard(zset_key) > 0:
        # 每次只删除100条数据
        redis_coon.zremrangebyrank(zset_key, 0, 99)
    # 将redis中的member删除完之后，还要删除key，因为程序中是通过判断key是否存在来决定是否加载排行榜到zset的
    redis_coon.delete(zset_key)


if __name__ == '__main__':
    config = {
        "mongo": "mongodb://userofvotedb:tcw123456@121.199.76.80:27017/votedb",
        "mongo_db": "votedb",
        "redis_host": "localhost",
        "redis_port": 6379,
        "user_vote_num": 10,  # 每个用户每天可以投的选票数
        "day_of_week": 1,  # 需要初始化星期几的榜单
    }
    reset(config)
