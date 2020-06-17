from flask import jsonify, request, current_app
from flask_jwt_extended import (
    jwt_required, get_jwt_claims, get_jwt_identity)
from mongoengine import DoesNotExist

from vote.api_1_0 import api
from vote.models import Competitor


@api.route('/change_competitor_state', methods=['POST'])
@jwt_required
def change_competitor_state():
    # 获取当前用户的身份
    claims = get_jwt_claims()
    # 只有为管理员身份的时候才能够修改参赛者的状态
    if not 'admin'.__eq__(claims):
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
    if not 'admin'.__eq__(claims):
        return jsonify({'code': 400, 'msg': '权限不够'})
    cid = request.json.get('cid', None)
    try:
        competitor = Competitor.objects.get(cid=cid)
    except DoesNotExist:
        return jsonify({'code': 400, 'msg': '无效的cid'})

    # 如果更新了tel的化，那么首先尝试更新tel
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
    # 记录日志
    current_app.logger.info(
        "admin change competitor info:" + str(get_jwt_identity()) + str(competitor))
    return jsonify({'code': 200, 'msg': '更新完成'})
