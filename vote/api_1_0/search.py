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
    cid = request.args.get('cid', '')
    nickname = request.args.get('nickname', '')
    name = request.args.get('name', '')
    tel = request.args.get('tel', '')
    day_of_week = datetime.now().isoweekday()

    search = {'$or': [
        {'name': re.compile(name)},
        {'tel': re.compile(tel)},
        {'nickname': re.compile(nickname)},
        {'cid': re.compile(cid)}
    ]
    }
    competitors = db.competitors.find(search)
    res_json = {'count': competitors.count(), 'code': 0}
    data = []
    competitor_num = redis_conn.zcard(REDIS_RANKING_LIST_KEY)
    for item in competitors:
        # 从redis,因为redis zset是从小到大进行排序的，因此这里需要计算一下分数从大到小的排名
        index = redis_conn.zrank(REDIS_RANKING_LIST_KEY+str(day_of_week), item['cid'])
        if index is not None:
            rank = competitor_num - index
        else:
            rank = -1  # 如果已经退赛，则排名使用-1来表示

        vote_info=db.competitor_vote_info.find_one({"cid":item['cid'],"day_of_week":day_of_week})
        data.append({'cid': item['cid'], 'name': item['name']
                        , 'nickname': item['nickname'], 'tel': item['tel']
                        , 'vote_num': vote_info['vote_num'], 'rank': rank})
    res_json['data'] = data
    return json.dumps(res_json, ensure_ascii=False), 200
