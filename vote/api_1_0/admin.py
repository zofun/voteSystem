from flask import jsonify, request, current_app
from flask_jwt_extended import (
    jwt_required, get_jwt_claims, get_jwt_identity)

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
    competitor = Competitor.objects.get(cid=cid)
    if not competitor:
        return jsonify({'code': 400, 'msg': '无效的cid'})
    competitor.state = new_state
    competitor.save()
    # 记录日志
    current_app.logger.info("competitor state change username:" +str(get_jwt_identity())+"cid:"+cid+" new state"+new_state)
    return jsonify({'code': 200, 'msg': '更新成功'})
