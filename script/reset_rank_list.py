# coding=utf-8
from datetime import datetime

from pymongo import MongoClient

def reset():
    """重置用户当天的票数，和参赛者的票数
    :return:
    """
    mongo_conn = MongoClient('mongodb://localhost:27017/')
    db = mongo_conn['votedb']
    # 重置每个用户拥有的选票数量
    result=db.users.update_many({"_id":{"$exists":True}},{"$set":{"vote":10}})
    print "重置用户拥有选票，一共影响的文档的数量为：%d"%result.modified_count

    day_of_week=datetime.now().isoweekday()
    # 删除旧数据
    result=db.competitor_vote_info.delete_many({"day_of_week":day_of_week})
    print "删除旧的选票数量记录：%d"%result.deleted_count

    # 为每个参赛者维护一个当日选票记录
    competitors=db.competitors.find()
    for competitor in  competitors:
        db.competitor_vote_info.insert({"cid":competitor['cid'],"day_of_week":day_of_week,"vote_num":0})
    print "当日选票记录建立完毕"

if __name__=='__main__':
    reset()