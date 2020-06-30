# coding=utf-8
import json
import re
from datetime import datetime

from flask import request

from vote.api_1_0 import api
from vote import redis_conn, db
from vote.constants import *
from vote.dao import rank_list_dao
from vote.utils import load_data_util


@api.route('/search', methods=['GET'])
def search():
    cid = request.args.get('cid', None)
    nickname = request.args.get('nickname', None)
    name = request.args.get('name', None)
    tel = request.args.get('tel', None)
    page = request.args.get('page', 1)
    limit = request.args.get('limit', 10)
    day_of_week = datetime.now().isoweekday()

    w = []
    if cid is not None and cid != "":
        w.append({"cid": re.compile(cid)})
    if tel is not None and tel != "":
        w.append({"tel": re.compile(tel)})
    if name is not None and name != "":
        w.append({"name": re.compile(name)})
    if nickname is not None and nickname != "":
        w.append({"nickname": re.compile(nickname)})

    start = (int(page) - 1) * int(limit)
    query = {"$or": w}
    competitors = db.competitors.find(query).skip(start).limit(int(limit))
    res_json = {'count': 2, 'code': 0}
    data = []
    # 确保zset已经被加载
    flag = redis_conn.exists(REDIS_RANKING_LIST_KEY + str(day_of_week))
    if flag != 1:
        # redis中还不存在zset排行榜则进行导入
        load_data_util.load_rank_to_redis(day_of_week)
    for item in competitors:
        index = redis_conn.zrevrank(REDIS_RANKING_LIST_KEY + str(day_of_week), item['cid'])
        if index is not None:
            rank = index + 1
        else:
            rank = -1  # 如果已经退赛，则排名使用-1来表示
        vote_num = rank_list_dao.get_vote_num(day_of_week, cid)

        item['_id'] = None
        item['vote_num'] = vote_num
        item['rank'] = rank
        data.append(item)
    res_json['data'] = data
    return json.dumps(res_json, ensure_ascii=False, skipkeys=True), 200
