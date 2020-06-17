from flask import jsonify, current_app, request
from flask_jwt_extended import (
    create_access_token
)
from mongoengine import Q

from vote.api_1_0 import api
from vote.models import Competitor
from vote.models import User


@api.route('/login', methods=['POST'])
def login():
    current_app.logger.info("user login" + str(request.json))
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if not username or not password:
        return jsonify({'code': 400, 'msg': '数据不完整'}), 400
    # 从数据库中查询，验证用户名密码的正确性
    u = User.objects(Q(username=username) & Q(password=password))
    if len(u) >= 1:
        # 生成token
        access_token = create_access_token(identity=u[0].username, user_claims=u[0].role)
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
        count = User.objects(username=username).count()
        if count >= 1:
            return jsonify({'code': 400, 'msg': '账号已被占用'}), 400
        u = User(username=username, password=password)
        # 用户注册成功保存到数据库
        u.save()
        current_app.logger.info("user register" + str(u))
        return jsonify({'code': 200, 'msg': '注册成功'}), 200


@api.route('/apply', methods=['POST'])
def apply():
    name = request.json.get('name', None)
    nickname = request.json.get('nickname', None)
    username = request.json.get('username', None)
    tel = request.json.get('tel', None)
    if not name or not username or not tel:
        return jsonify({'code': 400, 'msg': '请求参数错误'})

    # 确保电话的是唯一的
    count = Competitor.objects(tel=tel).count()
    if count >= 1:
        return jsonify({'code': 400, 'msg': '电话号重复'})
    # 生成唯一的参赛者编号
    # 利用参赛者总是来生成一个6位的id
    c = Competitor.objects.all().count()
    cid = str(c + 1).zfill(6)
    competitor = Competitor(cid=cid, nickname=nickname, tel=tel, vote_num=0)
    # 保存到数据库
    competitor.save()
    return jsonify({'code': 200, 'msg': '报名成功', 'cid': cid})


@api.route('/')
def index():
    u = User.objects.all().limit(1)
    return jsonify({'u': User.objects.all(), 'c': Competitor.objects.all()})