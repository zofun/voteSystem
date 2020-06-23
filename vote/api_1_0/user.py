# coding=utf-8
import json

from flask import jsonify, current_app, request
from flask_jwt_extended import (
    create_access_token
)

from vote import redis_conn, db, REDIS_RANKING_LIST_KEY, REDIS_COMPETITOR_HASH_KEY
from vote.api_1_0 import api


@api.route('/login', methods=['POST'])
def login():
    current_app.logger.info("user login" + str(request.json))
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        return jsonify({'code': 400, 'msg': '数据不完整'}), 400
    # 从数据库中查询，验证用户名密码的正确性
    u = db.users.find_one({"username": username, "password": password})
    if u is not None:
        # 生成token
        access_token = create_access_token(identity=u['username'], user_claims=u['role'])
        # 记录用户登录的日志
        current_app.logger.info("user login:" + str(u))
        return jsonify({'code': 200, 'token': access_token}), 200
    else:
        return jsonify({'code': 400, 'msg': '账户或密码错误'}), 400


@api.route('register', methods=['POST'])
def register():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        return jsonify({'code': 400, 'msg': '数据不完整'}), 400
    else:
        # 确保username是唯一的
        count = db.users.find({"username": username}).count()
        if count >= 1:
            return jsonify({'code': 400, 'msg': '账号已被占用'}), 400
        # 用户注册成功保存到数据库
        user = {"username": username, "password": password, "role": "user"}
        db.users.insert_one(user)
        # 记录用户注册的日志
        current_app.logger.info("user register:" + str(user))
        return jsonify({'code': 200, 'msg': '注册成功'}), 200


@api.route('/apply', methods=['POST'])
def apply():
    name = request.json.get('name', None)
    nickname = request.json.get('nickname', None)
    tel = request.json.get('tel', None)
    if not name or not nickname or not tel:
        return jsonify({'code': 400, 'msg': '请求参数错误'})
    # 确保电话的是唯一的
    count = db.competitors.find({"tel": tel}).count()
    if count >= 1:
        return jsonify({'code': 400, 'msg': '电话号重复'})
    # 生成唯一的参赛者编号
    # 利用参赛者总是来生成一个6位的id
    c = db.competitors.find().count()
    cid = str(c + 1).zfill(6)
    competitor = {"cid": cid, "name": name, "nickname": nickname, "tel": tel, "vote_num": 0, "state": "join"}
    db.competitors.insert_one(competitor)
    # 将新报名的参赛者cid加入到排行榜
    redis_conn.zadd(REDIS_RANKING_LIST_KEY, {cid: 0})
    current_app.logger.info("apply:" + str(competitor))
    return jsonify({'code': 200, 'msg': '报名成功', 'cid': cid})
