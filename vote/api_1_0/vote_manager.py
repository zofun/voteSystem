# coding=utf-8
import datetime
import json
import time

from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from vote import redis_conn
from vote.api_1_0 import api
from vote.constants import *
from vote.utils import load_data_util
from vote import db


@api.route('/vote/<cid>')
@jwt_required
def vote(cid):
    competitor_info = redis_conn.get(cid)
    if competitor_info is None:
        return jsonify({'code': ILLEGAL_PARAMETER, "msg": '没有该参赛者'}), 200
    identity = get_jwt_identity()
    # 首先判断该用户是否还有选票
    user=db.users.find_one({"username":identity})
    if int(user['vote'])==0:
        return jsonify({'code': SUCCESS, 'msg': '今日选票已用完'}), 200
    # 如果redis中还没有缓存该参赛者选票信息，需要首先将数据加载到redis中
    flag = redis_conn.exists(identity+REDIS_SPLIT+cid)
    if flag != 1:
        # 加载选手的选票信息
        load_data_util.load_vote_info_to_redis(cid)
    # 拿到今天该用户给该参数者的投票数量
    vote_num=redis_conn.get(identity+REDIS_SPLIT+cid)
    # 给该用户的投票还没达到阈值
    if vote_num is None or vote_num<M:
        # 更新分值，更新zset排行榜。（票数）+（低8位的时间戳）
        old_score=redis_conn.zscore(REDIS_RANKING_LIST_KEY,cid)
        if old_score is None:
            old_score=0
        # 取出的旧的分数
        old_vote=old_score/100000000
        # 获取当前微级时间戳
        timestamp=int(round(time.time() * 1000000))
        # 拼接得到新的score

        new_socre=(old_vote+1)*100000000+timestamp%100000000
        # 设置或更新
        # todo 这里报错
        redis_conn.zadd(REDIS_RANKING_LIST_KEY, new_socre, cid)
        # 修改数据库中参赛者的信息
        db.competitors.update({"cid": cid}, {"$inc": {"vote_num": 1}})
        # data直接存时间戳
        timestamp = int(round(time.time() * 1000000))
        db.votes.insert({"cid": cid, "username": identity, "vote_num": 1, "date": timestamp})
        # 更新用户所拥有的选票
        db.users.update({"username":identity},{"$inc":{"vote":-1}})
        # 记录日志
        current_app.logger.info("vote:" + identity + "to" + cid)
        return jsonify({'code': SUCCESS, 'msg': '投票成功'}), 200
    return jsonify({'code': SUCCESS, 'msg': '给该参赛者的投票已经达到最大了'}), 200


@api.route('/get_ranking_list', methods=['GET'])
def get_ranking_list():
    page = request.args.get('page')
    limit = request.args.get('limit')
    begin = (int(page) - 1) * int(limit)
    # 首先判断redis中zset是否存在，如果不存在就查询数据库，将数据导入redis的zset中
    flag = redis_conn.exists(REDIS_RANKING_LIST_KEY)
    if flag != 1:
        # redis中还不存在zset排行榜则进行导入
        load_data_util.load_rank_to_redis()
    rank_list = redis_conn.zrange(REDIS_RANKING_LIST_KEY, start=begin, end=begin + int(limit) - 1, desc=True)
    # 返回的json中应该包含参赛者总数
    res_json = {'count': redis_conn.zcard(REDIS_RANKING_LIST_KEY)}
    data = []
    # 计算排名
    rank = begin
    for cid in rank_list:
        # 首先尝试从redis中获取用户的详细信息，获取不到再从数据库中查询，然后存入redis
        competitor_info = redis_conn.get(cid)
        if competitor_info is None:
            # redis中没查到，从数据库中查询
            competitor = db.competitors.find_one({"cid": cid})
            # 存入redis中
            competitor_info = json.dumps(
                {'name': competitor['name'], 'nickname': competitor['nickname']
                    , 'tel': competitor['tel'], 'vote_num': competitor['vote_num'], "cid": competitor['cid']}
                , ensure_ascii=False)
            redis_conn.set(competitor['cid'], competitor_info)
            redis_conn.expire(competitor['cid'], REDIS_KEY_EXPIRE_COMPETITOR_INFO)
        dict = json.loads(competitor_info)
        rank += 1
        dict['rank'] = rank
        dict['vote_num'] = redis_conn.zscore(REDIS_RANKING_LIST_KEY, cid)/100000000
        data.append(dict)
    res_json['data'] = data
    res_json['code'] = 0
    return json.dumps(res_json, ensure_ascii=False), 200
