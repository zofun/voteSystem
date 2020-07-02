# coding=utf-8
import json
import time

from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from vote import db
from vote import redis_conn
from vote.api_1_0 import api
from vote.constants import *
from vote.utils import load_data_util
from datetime import datetime
from vote.utils import zset_score_calculate, datetime_utils
from vote.dao import rank_list_dao, user_vote_info_dao, competitor_info_dao


@api.route('/vote/<cid>')
@jwt_required
def vote(cid):
    competitor_info = redis_conn.get(REDIS_COMPETITOR_INFO_PREFIX + cid)
    day_of_week = datetime.now().isoweekday()
    if competitor_info is None:
        return jsonify({'code': ILLEGAL_PARAMETER, "msg": '没有该参赛者'}), 200
    identity = get_jwt_identity()

    # 一个用户每天只有N个选票的逻辑
    query = dict(username=identity, vote={"$gt": 0})
    u_data = {"$inc": dict(vote=-1)}
    user = db.users.find_and_modify(query, u_data, new=True)
    if user is None:
        return jsonify({'code': SUCCESS, 'msg': '今日选票已用完'}), 200

    # 一个用户每天给一个参赛者的投票不能超过M票的逻辑
    query = dict(username=identity, cid=cid, date=datetime_utils.get_today(), vote_num={"$lt": M})
    u_data = {"$inc": dict(vote_num=1)}
    vote_info = db.user_vote_info.find_and_modify(query, u_data, new=True, upsert=True)
    if vote_info is None:
        # 回滚
        u = db.users.find_and_modify({"username": identity}, {"$inc": {"vote": 1}})
        return jsonify({'code': SUCCESS, 'msg': '给该参赛者的投票已经达到最大了'}), 200

    try:
        # 更新参数者当天所获选票总数
        query = dict(cid=cid, day_of_week=day_of_week)
        u_data = {"$inc": dict(vote_num=1), "$set": dict(date=timestamp)}
        update_cvf_res = db.competitor_vote_info.find_and_modify(query, u_data, new=True, upsert=True)

        if update_cvf_res is None:
            return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200

        # 更新投票记录表
        i_data = dict(cid=cid, username=identity, vote_num=1, date=timestamp)
        db.votes.insert(i_data)
    except Exception as e:
        # 日志打印，应该携带调用入口等信息
        current_app.logger.error(traceback.format_exc())
        return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200

    # 将投票更新到mongo 之后，更新redis
    new_score = zset_score_calculate.get_score(update_cvf_res.get("vote_num"), update_cvf_res.get("date"))
    rank_list_dao.update_rank_list(day_of_week, cid, new_score)
    vote_info_dao.update_vote_info(identity, cid, update_cvf_res.get("vote_num"))
    user_vote_info_dao.update_user_vote_num(identity, -1)
    # 记录日志
    current_app.logger.info("vote:" + identity + "to" + cid)
    return jsonify({'code': SUCCESS, 'msg': '投票成功'}), 200


@api.route('/get_ranking_list', methods=['GET'])
def get_ranking_list():
    page = request.args.get('page')
    limit = request.args.get('limit')
    day_of_week = request.args.get('day_of_week', datetime.now().isoweekday())
    begin = (int(page) - 1) * int(limit)
    # 从redis zset中分页获取排行榜
    rank_list = rank_list_dao.get_rank_list(day_of_week, begin, limit)
    # 返回的json中应该包含参赛者总数
    res_json = {'count': redis_conn.zcard(REDIS_RANKING_LIST_KEY + str(day_of_week))}
    data = []
    # 计算排名
    rank = begin
    for item in rank_list:
        c_dict = competitor_info_dao.get_competitor_info_by_cid(item[0])
        rank += 1
        c_dict['rank'] = rank
        # 从zset score中计算出票数
        c_dict['vote_num'] = zset_score_calculate.get_vote_num(item[1])
        data.append(c_dict)
    res_json['data'] = data
    res_json['code'] = 0
    return json.dumps(res_json, ensure_ascii=False), 200
