# coding=utf-8
import json
import time
from datetime import datetime

import pymongo
from flask import jsonify, request, current_app
from flask_jwt_extended import (
    jwt_required, get_jwt_claims, get_jwt_identity)

from vote import redis_conn, db
from vote.api_1_0 import api
from vote.constants import *
from vote.utils import zset_score_calculate


@api.route('/change_competitor_state', methods=['POST'])
@jwt_required
def change_competitor_state():
    # 获取当前用户的身份
    claims = get_jwt_claims()
    day_of_week = datetime.now().isoweekday()
    # 只有为管理员身份的时候才能够修改参赛者的状态
    if 'admin' != claims:
        return jsonify({'code': NO_PERMISSION, 'msg': '权限不够'}), 200
    cid = request.json.get('cid', None)
    new_state = request.json.get('state', None)
    # 判断cid的有效性
    competitor = db.competitors.find_one({"cid": cid})
    if competitor is None:
        return jsonify({'code': ILLEGAL_PARAMETER, 'msg': '无效的cid'}), 200
    competitor['state'] = new_state
    try:
        result = db.competitors.update({"cid": cid}, {"$set": {"state": new_state}})
        if result.matched_count == 0:
            return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
    except Exception as e:
        current_app.debug(e)
        return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
    # 更新缓存
    if COMPETITOR_STATE_JOIN == int(new_state):
        # 如果更新为参赛状态，那么加入redis排行榜（zset）中
        # 从mongo查询出当天该参赛者的票数，并根据规则计算score
        vote_info = db.competitor_vote_info.find_one({"cid": cid, "day_of_week": day_of_week})
        timestamp = int(vote_info["date"])
        # todo 抽取常量 使用工具类计算 ok
        score = zset_score_calculate.get_score(vote_info['vote_num'], timestamp)
        redis_conn.zadd(REDIS_RANKING_LIST_KEY + str(day_of_week), {cid: score})
    # 记录日志
    current_app.logger.info(
        "change competitor state:admin username:" + str(get_jwt_identity()) + "cid:" + cid + " new state" + new_state)
    return jsonify({'code': SUCCESS, 'msg': '更新成功'}), 200


@api.route('/change_competitor_info', methods=['POST'])
@jwt_required
def change_competitor_info():
    # 获取当前用户的身份
    claims = get_jwt_claims()
    # 获取请求数据
    cid = request.json.get('cid', None)
    tel = request.json.get('tel', None)
    nickname = request.json.get('nickname', None)
    name = request.json.get('name', None)
    # 只有为管理员身份的时候才能够修改参赛者的信息
    if 'admin' != claims:
        return jsonify({'code': NO_PERMISSION, 'msg': '权限不够'}), 200

    update = {}
    if tel is not None:
        update["tel"]=tel
    if nickname is not None:
        update["nickname"]=nickname
    if name is not None:
        update["name"]=nickname
    # 将参赛者信息同步到数据库中
    try:
        # todo 通过返回值判断更新是否成功 ok
        update_result = db.competitors.find_and_modify({"cid": cid}, {"$set":[]})
        if update_result is None:
            return jsonify({'code': ERROR, 'msg': '修改失败'}), 200
    except pymongo.errors.DuplicateKeyError as e:
        current_app.logger.warning(e)
        return jsonify({'code': ILLEGAL_PARAMETER, 'msg': 'tel重复'}), 200
    except Exception as e:
        current_app.logger.warning(e)
        return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200

    # 将参赛者信息的更改同步到redis
    json_str = json.dumps(
        {'name': update_result.get("name"), 'nickname': update_result.get("nickname"), 'tel': update_result.get("tel"),
         "cid": update_result.get("cid")},
        ensure_ascii=False)
    redis_conn.setex(update_result.get("cid"), REDIS_KEY_EXPIRE_COMPETITOR_INFO, json_str)
    # 记录日志
    current_app.logger.info(
        "admin change competitor info: admin username:" + str(get_jwt_identity())
        + "competitor cid+:" + str(update_result.get("cid")))
    return jsonify({'code': SUCCESS, 'msg': '更新完成'}), 200


@api.route('/add_vote', methods=['POST'])
@jwt_required
def add_vote_to_competitor():
    cid = request.json.get('cid', None)
    votes = request.json.get('votes', None)

    username = get_jwt_identity()
    claims = get_jwt_claims()
    day_of_week = datetime.now().isoweekday()
    # 只有拥有管理员权限的人才能够加票
    if 'admin' != claims:
        return jsonify({'code': NO_PERMISSION, 'msg': '权限不够'}), 200
    # todo 先更新mongo 通过mongo中更新的结果去计算分数，再去更新redis ok
    # 首先修改mongo，根据mongo中的返回信息来决定是否更新redis
    # data直接存时间戳
    timestamp = int(time.time())
    update_result = None
    try:
        update_result = db.competitor_vote_info.find_and_modify({"cid": cid, "day_of_week": day_of_week},
                                                                {"$inc": {"vote_num": int(votes)},
                                                                 "$set": {"date": timestamp}})
        # 将本次管理员加票的信息存放到votes集合中
        db.votes.insert({"cid": cid, "username": username, "vote_num": int(votes), "date": timestamp})
        if update_result is None:
            return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
    except Exception as e:
        current_app.logger.warning(e)
    # 计算新的score
    score = zset_score_calculate.get_score(update_result.get("vote_num"),
                                           update_result.get("date"))
    # 更新redis
    redis_conn.zadd(REDIS_RANKING_LIST_KEY + str(day_of_week), {cid: score})

    # 记录日志
    current_app.logger.info(
        "admin add vote: admin username:" + str(get_jwt_identity()) + "competitor cid+:"
        + cid + " votes:" + votes)
    return jsonify({'code': SUCCESS, 'msg': '加票成功'}), 200
