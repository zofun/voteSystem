# coding=utf-8
import json
import traceback
from datetime import datetime

import pymongo
from flask import jsonify, current_app, request
from flask_jwt_extended import (
    create_access_token
)

from vote import redis_conn, db, REDIS_RANKING_LIST_KEY
from vote.api_1_0 import api
from vote.constants import *
from vote.dao import rank_list_dao


@api.route('/login', methods=['POST'])
def login():
    current_app.logger.info("user login" + str(request.json))
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        return jsonify({'code': PARAMETER_ERROR, 'msg': '数据不完整'}), 200
    # 从数据库中查询，验证用户名密码的正确性
    query = dict(username=username, password=password)
    u = db.users.find_one(query)
    if u is not None:
        # 生成token
        access_token = create_access_token(identity=u['username'], user_claims=u['role'])
        # 记录用户登录的日志
        current_app.logger.info("user login:" + str(u))
        return jsonify({'code': SUCCESS, 'token': access_token}), 200
    else:
        return jsonify({'code': LOGIN_FAILED, 'msg': '账户或密码错误'}), 200


@api.route('register', methods=['POST'])
def register():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        # 验证表单数据的完整性
        return jsonify({'code': PARAMETER_ERROR, 'msg': '数据不完整'}), 200
    try:
        i_data = dict(username=username, password=password, vote=N, role="user")
        insert_res = db.users.insert_one(i_data)
        if insert_res is None:
            return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
    except pymongo.errors.DuplicateKeyError as e:
        current_app.logger.error(traceback.format_exc())
        return jsonify({'code': ILLEGAL_PARAMETER, 'msg': '账号已被占用'}), 200
    except Exception as e:
        current_app.logger.error(traceback.format_exc())
        return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
    # 记录用户注册的日志
    current_app.logger.info("user register:" + str(i_data))
    return jsonify({'code': SUCCESS, 'msg': '注册成功'}), 200


@api.route('/apply', methods=['POST'])
def apply():
    name = request.json.get('name', None)
    nickname = request.json.get('nickname', None)
    tel = request.json.get('tel', None)
    day_of_week = datetime.now().isoweekday()
    if not name or not nickname or not tel:
        return jsonify({'code': PARAMETER_ERROR, 'msg': '请求参数错误'}), 200
    # 利用mongo $inc自增来生成全局唯一的cid
    query = dict(system_id=1)
    u_data = {"$inc": dict(cid=1)}
    c = db.id.find_and_modify(query, u_data, upsert=True, new=True)
    if c is None:
        return jsonify({'code': ERROR, 'msg': '报名失败'})
    cid = str(int(c['cid']))
    try:
        i_data = dict(cid=cid, name=name, nickname=nickname, tel=tel, state=COMPETITOR_STATE_JOIN)
        insert_res = db.competitors.insert_one(i_data)
        if insert_res is None:
            return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
    except pymongo.errors.DuplicateKeyError as e:
        current_app.logger.error(traceback.format_exc())
        return jsonify({'code': ILLEGAL_PARAMETER, 'msg': '电话号重复'}), 200
    except Exception as e:
        current_app.logger.error(traceback.format_exc())
        return jsonify({'code': ERROR, 'msg': '更新数据库失败'}), 200
    # 将新报名的参赛者cid加入到排行榜
    rank_list_dao.update_rank_list(day_of_week, cid, 0)
    current_app.logger.info("apply:" + str(i_data))
    return jsonify({'code': SUCCESS, 'msg': '报名成功', 'cid': cid}), 200
