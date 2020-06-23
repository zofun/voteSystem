# coding=utf-8
import json

from flask import jsonify, request, current_app
from flask_jwt_extended import (
    jwt_required, get_jwt_claims, get_jwt_identity)
from mongoengine import DoesNotExist

from vote import redis_conn, db
from vote.api_1_0 import api
from vote.constants import *


@api.route('/change_competitor_state', methods=['POST'])
@jwt_required
def change_competitor_state():
    # 获取当前用户的身份
    claims = get_jwt_claims()
    # 只有为管理员身份的时候才能够修改参赛者的状态
    if 'admin' != claims:
        return jsonify({'code': 400, 'msg': '权限不够'})
    cid = request.json.get('cid', None)
    new_state = request.json.get('state', None)
    # 判断cid的有效性
    competitor = db.competitors.find_one({"cid": cid})
    if competitor is None:
        return jsonify({'code': 400, 'msg': '无效的cid'})
    competitor['state'] = new_state
    db.competitors.update({"cid": cid}, {"$set": {"state": new_state}})
    # 更新缓存
    if 'join' == new_state:
        # 如果更新为参赛状态，那么加入redis排行榜中
        redis_conn.zadd(REDIS_RANKING_LIST_KEY, {competitor['cid']: competitor['vote_num']})
    else:
        # 否则从redis排行榜中移除
        redis_conn.zrem(REDIS_RANKING_LIST_KEY, competitor['cid'])
    # 记录日志
    current_app.logger.info(
        "change competitor state:admin username:" + str(get_jwt_identity()) + "cid:" + cid + " new state" + new_state)
    return jsonify({'code': 200, 'msg': '更新成功'})


@api.route('/change_competitor_info', methods=['POST'])
@jwt_required
def change_competitor_info():
    # 获取当前用户的身份
    claims = get_jwt_claims()
    # 只有为管理员身份的时候才能够修改参赛者的信息
    if 'admin' != claims:
        return jsonify({'code': 400, 'msg': '权限不够'})
    cid = request.json.get('cid', None)
    competitor = db.competitors.find_one({"cid": cid})
    if competitor is None:
        return jsonify({'code': 400, 'msg': '无效的cid'})
    # 如果更新了tel的，那么首先尝试更新tel
    tel = request.json.get('tel', None)
    if tel is not None:
        count = db.competitors.find({"tel": tel}).count()
        if count >= 1:
            return jsonify({'code': 400, 'msg': 'tel重复'})
        competitor['tel'] = tel
    # 更新nickname
    nickname = request.json.get('nickname', None)
    if nickname is not None:
        competitor['nickname'] = nickname
    # 更新name
    name = request.json.get('name', None)
    if name is not None:
        competitor['name'] = name
    db.competitors.update({"cid": cid}, competitor)
    # 将参赛者信息的更改同步到redis
    json_str = json.dumps(
        {'name': competitor['name'], 'nickname': competitor['nickname']
            , 'tel': competitor['tel'], 'vote_num': competitor['vote_num'], "cid": competitor['cid']}
        , ensure_ascii=False)
    redis_conn.hset(name=REDIS_COMPETITOR_HASH_KEY, key=competitor['cid'], value=json_str)
    # 记录日志
    current_app.logger.info(
        "admin change competitor info: admin username:" + str(get_jwt_identity())
        + "competitor cid+:" + str(competitor['cid']))
    return jsonify({'code': 200, 'msg': '更新完成'})


@api.route('/add_vote', methods=['POST'])
@jwt_required
def add_vote_to_competitor():
    claims = get_jwt_claims()
    # 只有拥有管理员权限的人才能够加票
    if 'admin' != claims:
        return jsonify({'code': 400, 'msg': '权限不够'})
    cid = request.json.get('cid', None)
    votes = request.json.get('votes', None)
    # 首先修改redis中的信息
    redis_conn.zincrby(REDIS_RANKING_LIST_KEY, votes, cid)
    db.competitors.update({"cid": cid}, {"$inc": {"vote_num": int(votes)}})
    # 记录日志
    current_app.logger.info(
        "admin add vote: admin username:" + str(get_jwt_identity()) + "competitor cid+:"
        + cid + " votes:" + votes)

    return jsonify({'code': 200, 'msg': '加票成功'})
