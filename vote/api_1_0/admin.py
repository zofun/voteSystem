# coding=utf-8
import json

from flask import jsonify, request, current_app
from flask_jwt_extended import (
    jwt_required, get_jwt_claims, get_jwt_identity)
from mongoengine import DoesNotExist

from vote import redis_conn
from vote.api_1_0 import api
from vote.constants import *
from vote.models import Competitor


@api.route('/change_competitor_state', methods=['POST'])
@jwt_required
def change_competitor_state():
    # 获取当前用户的身份
    claims = get_jwt_claims()
    # 只有为管理员身份的时候才能够修改参赛者的状态
    if 'admin'!=claims:
        return jsonify({'code': 400, 'msg': '权限不够'})
    cid = request.json.get('cid', None)
    new_state = request.json.get('state', None)
    # 判断cid的有效性
    try:
        competitor = Competitor.objects.get(cid=cid)
    except DoesNotExist:
        return jsonify({'code': 400, 'msg': '无效的cid'})
    competitor.state = new_state
    competitor.save()
    # 更新缓存
    if 'join' == new_state:
        # 如果更新为参赛状态，那么加入redis排行榜中
        redis_conn.zadd(REDIS_RANKING_LIST_KEY, {competitor.cid: competitor.vote_num})
    else:
        # 否则从redis排行榜中移除
        redis_conn.zrem(REDIS_RANKING_LIST_KEY, competitor.cid)
    # 记录日志
    current_app.logger.info(
        "competitor state change username:" + str(get_jwt_identity()) + "cid:" + cid + " new state" + new_state)
    return jsonify({'code': 200, 'msg': '更新成功'})


@api.route('/change_competitor_info', methods=['POST'])
@jwt_required
def change_competitor_info():
    # 获取当前用户的身份
    claims = get_jwt_claims()
    # 只有为管理员身份的时候才能够修改参赛者的信息
    if 'admin'!=claims:
        return jsonify({'code': 400, 'msg': '权限不够'})
    cid = request.json.get('cid', None)
    try:
        competitor = Competitor.objects.get(cid=cid)
    except DoesNotExist:
        return jsonify({'code': 400, 'msg': '无效的cid'})

    # 如果更新了tel的，那么首先尝试更新tel
    tel = request.json.get('tel', None)
    if tel is not None:
        # 更新电话之前，需要验证新的电话是否重复
        count = Competitor.objects(tel=tel).count()
        if count >= 1:
            return jsonify({'code': 400, 'msg': 'tel重复'})
        competitor.tel = tel
    # 更新nickname
    nickname = request.json.get('nickname', None)
    if nickname is not None:
        competitor.nickname = nickname
    # 更新name
    name = request.json.get('name', None)
    if name is not None:
        competitor.name = name
    # 将更新保存到数据库中
    competitor.save()
    # 将参赛者信息的更改同步到redis
    json_str = json.dumps(
        {'name': competitor.name, 'nickname': competitor.nickname, 'tel': competitor.tel,
         'vote_num': competitor.vote_num},
        ensure_ascii=False)
    redis_conn.hset(name=REDIS_COMPETITOR_HASH_KEY, key=competitor.cid, value=json_str)
    # 记录日志
    # current_app.logger.info(
    #    "admin change competitor info:" + str(get_jwt_identity()) + str(competitor))
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
    # 修改数据库
    competitor = Competitor.objects().get(cid=cid)
    competitor.vote_num += int(votes)
    competitor.save()
    return jsonify({'code': 200, 'msg': '加票成功'})
