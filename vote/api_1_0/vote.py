import json

from flask import jsonify,request
from flask_jwt_extended import jwt_required, get_jwt_identity

from vote import redis_conn
from vote.api_1_0 import api
from vote.constants import *
from vote.models import Competitor


@api.route('/vote/<cid>')
@jwt_required
def vote(cid):
    competitor_info = redis_conn.hget(REDIS_COMPETITOR_HASH_KEY, cid)
    if competitor_info is None:
        return jsonify({'code': 400, "msg": '没有该参赛者'})
    dict_json = json.loads(competitor_info)
    identity = get_jwt_identity()
    if redis_conn.sadd(REDIS_VOTE_PREFIX + cid, identity):
        # 投票数量加一
        redis_conn.zincrby(REDIS_RANKING_LIST_KEY, 1, cid)
        # 修改数据库中参赛者的信息
        competitor = Competitor.objects.get(cid=cid)
        competitor.vote_num += 1
        competitor.vote.append(identity)
        competitor.save()
        return jsonify({'code': 200, 'msg': '投票成功'})
    return jsonify({'code': 200, 'msg': '已经投过票了'})


@api.route('/get_ranking_list', methods=['GET'])
def get_ranking_list():
    page=request.args.get('page')
    limit=request.args.get('limit')
    begin = (int(page) - 1) * int(limit)
    rank_list = redis_conn.zrange(REDIS_RANKING_LIST_KEY, start=begin, end=begin + int(limit) - 1, desc=True)
    res_json = {'count': len(rank_list)}
    data = []
    # 计算排名
    rank=begin
    for cid in rank_list:
        print(cid)
        competitor_info = redis_conn.hget(REDIS_COMPETITOR_HASH_KEY, cid)
        dict = json.loads(competitor_info)
        # 将cid也补充上
        dict['cid'] = cid
        rank += 1
        dict['rank']=rank
        dict['vote_num']=redis_conn.zscore(REDIS_RANKING_LIST_KEY,cid)
        data.append(dict)
    res_json['data'] = data
    res_json['code']=0
    return json.dumps(res_json,ensure_ascii=False)
