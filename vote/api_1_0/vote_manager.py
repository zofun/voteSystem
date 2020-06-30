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
from vote.utils import zset_score_calculate
from vote.dao import rank_list_dao, vote_info_dao, user_vote_info_dao, competitor_info_dao


@api.route('/vote/<cid>')
@jwt_required
def vote(cid):
    competitor_info = redis_conn.get(cid)
    day_of_week = datetime.now().isoweekday()
    if competitor_info is None:
        return jsonify({'code': ILLEGAL_PARAMETER, "msg": '没有该参赛者'}), 200
    identity = get_jwt_identity()
    query = dict(username=identity, vote={"$gt": 0})
    u_data = {"$inc": dict(vote=-1)}
    user = db.users.find_and_modify(query, u_data, new=True)
    if user is None:
        return jsonify({'code': SUCCESS, 'msg': '今日选票已用完'}), 200

    # 拿到今天该用户给该参数者的投票数量
    vote_num = vote_info_dao.get_vote_info(identity, cid)
    # 给该用户的投票还没达到阈值
    if int(vote_num) < M:
        # 修改数据库中参赛者的信息
        # data直接存时间戳
        timestamp = int(time.time())
        update_result = None
        try:
            query = dict(cid=cid, day_of_week=day_of_week)
            u_data = {"$inc": dict(vote_num=1), "$set": dict(date=timestamp)}
            update_cvf_res = db.competitor_vote_info.find_and_modify(query, u_data, new=True, upsert=True)

            i_data = dict(cid=cid, username=identity, vote_num=1, date=timestamp)
            insert_res = db.votes.insert(i_data)

            update_u_res = db.users.find_and_modify({"username": identity}, {"$inc": dict(vote=-1)}, new=True)
            if update_cvf_res is None or update_u_res is None or insert_res is None:
                return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
        except Exception as e:
            current_app.logger.warning(e)
            return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200

        # 将投票更新到mongo 之后，更新redis
        new_score = zset_score_calculate.get_score(update_cvf_res.get("vote_num"), update_cvf_res.get("date"))
        rank_list_dao.update_rank_list(day_of_week, cid, new_score)
        vote_info_dao.update_vote_info(identity, cid, update_cvf_res.get("vote_num"))
        user_vote_info_dao.update_user_vote_num(identity, -1)
        # 记录日志
        current_app.logger.info("vote:" + identity + "to" + cid)
        return jsonify({'code': SUCCESS, 'msg': '投票成功'}), 200
    return jsonify({'code': SUCCESS, 'msg': '给该参赛者的投票已经达到最大了'}), 200


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
