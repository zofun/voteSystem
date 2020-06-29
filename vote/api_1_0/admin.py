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
    except Exception as e:
        current_app.debug(e)
        return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
    # 更新缓存
    if COMPETITOR_STATE_JOIN == int(new_state):
        # 如果更新为参赛状态，那么加入redis排行榜（zset）中
        # 从mongo查询出当天该参赛者的票数，并根据规则计算score

        vote_info = db.competitor_vote_info.find_one({"cid": cid, "day_of_week": day_of_week})
        timestamp = int(vote_info["date"])
        score = vote_info['vote_num'] * 100000 + (100000 - timestamp % 100000)
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

    competitor = db.competitors.find_one({"cid": cid})
    if competitor is None:
        return jsonify({'code': ILLEGAL_PARAMETER, 'msg': '无效的cid'}), 200
    if tel is not None:
        competitor['tel'] = tel
    if nickname is not None:
        competitor['nickname'] = nickname
    if name is not None:
        competitor['name'] = name
    # 将参赛者信息同步到数据库中
    try:
        db.competitors.update({"cid": cid}, competitor)
    except pymongo.errors.DuplicateKeyError as e:
        current_app.logger.warning(e)
        return jsonify({'code': ILLEGAL_PARAMETER, 'msg': 'tel重复'}), 200
    # 将参赛者信息的更改同步到redis
    json_str = json.dumps(
        {'name': competitor['name'], 'nickname': competitor['nickname'], 'tel': competitor['tel'],
         "cid": competitor['cid']},
        ensure_ascii=False)
    redis_conn.setex(competitor['cid'], REDIS_KEY_EXPIRE_COMPETITOR_INFO, json_str)
    # 记录日志
    current_app.logger.info(
        "admin change competitor info: admin username:" + str(get_jwt_identity())
        + "competitor cid+:" + str(competitor['cid']))
    return jsonify({'code': SUCCESS, 'msg': '更新完成'}), 200


@api.route('/add_vote', methods=['POST'])
@jwt_required
def add_vote_to_competitor():
    username = get_jwt_identity()
    claims = get_jwt_claims()
    day_of_week = datetime.now().isoweekday()
    # 只有拥有管理员权限的人才能够加票
    if 'admin' != claims:
        return jsonify({'code': NO_PERMISSION, 'msg': '权限不够'}), 200
    cid = request.json.get('cid', None)
    votes = request.json.get('votes', None)
    # 首先修改redis中的信息
    new_score = zset_score_calculate.get_score(day_of_week, cid, votes)
    redis_conn.zadd(REDIS_RANKING_LIST_KEY + str(day_of_week), {cid: new_score})
    day_of_week = datetime.now().isoweekday()
    # data直接存时间戳
    timestamp = int(time.time())
    db.competitor_vote_info.update({"cid": cid, "day_of_week": day_of_week},
                                   {"$inc": {"vote_num": int(votes)}, "$set": {"date": timestamp}})
    # 将本次管理员加票的信息存放到votes集合中
    db.votes.insert({"cid": cid, "username": username, "vote_num": int(votes), "date": timestamp})
    # 记录日志
    current_app.logger.info(
        "admin add vote: admin username:" + str(get_jwt_identity()) + "competitor cid+:"
        + cid + " votes:" + votes)
    return jsonify({'code': SUCCESS, 'msg': '加票成功'}), 200
