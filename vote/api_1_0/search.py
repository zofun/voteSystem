import json
import re

from flask import request

from vote.api_1_0 import api
from vote.models import Competitor
from vote import redis_conn
from vote.constants import *


@api.route('/search', methods=['GET'])
def search():
    cid = request.args.get('cid', '')
    nickname = request.args.get('nickname', '')
    name = request.args.get('name', '')
    tel = request.args.get('tel', '')

    search = {'__raw__': {'$or': [
        {'name': re.compile(name)},
        {'tel': re.compile(tel)},
        {'nickname': re.compile(nickname)},
        {'cid': re.compile(cid)}
    ]
    }}

    competitors = Competitor.objects(**search)
    res_json = {'count': len(competitors), 'code': 0}
    data = []
    competitor_num=redis_conn.zcard(REDIS_RANKING_LIST_KEY)
    for item in competitors:
        # 从redis,因为redis zset是从小到大进行排序的，因此这里需要计算一下分数从大到小的排名
        rank=competitor_num-redis_conn.zrank(REDIS_RANKING_LIST_KEY,item.cid)
        data.append({'cid': item.cid, 'name': item.name
                        , 'nickname': item.nickname, 'tel': item.tel
                        , 'vote_num': item.vote_num,'rank':rank})
    res_json['data'] = data
    return json.dumps(res_json, ensure_ascii=False)
