# coding=utf-8
import json
import re
from datetime import datetime

from flask import request

from vote.api_1_0 import api
from vote import redis_conn, db
from vote.constants import *


@api.route('/search', methods=['GET'])
def search():
    cid = request.args.get('cid', None)
    nickname = request.args.get('nickname', None)
    name = request.args.get('name', None)
    tel = request.args.get('tel', None)
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

    search = {'$or': w}
    # todo 查询可能很多，需要进行分页
    competitors = db.competitors.find(search)
    res_json = {'count': competitors.count(), 'code': 0}
    data = []
    for item in competitors:
        # 从redis,因为redis zset是从小到大进行排序的，因此这里需要计算一下分数从大到小的排名
        index = redis_conn.zrevrank(REDIS_RANKING_LIST_KEY + str(day_of_week), item['cid'])
        if index is not None:
            rank = index + 1
        else:
            rank = -1  # 如果已经退赛，则排名使用-1来表示
        # todo 这里分数可以直接从zset中查询，无需查询mongo
        vote_info = db.competitor_vote_info.find_one({"cid": item['cid'], "day_of_week": day_of_week})
        data.append({'cid': item['cid'], 'name': item['name']
                        , 'nickname': item['nickname'], 'tel': item['tel']
                        , 'vote_num': vote_info['vote_num'], 'rank': rank})
    res_json['data'] = data
    return json.dumps(res_json, ensure_ascii=False), 200
