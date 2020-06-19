import json
import re

from flask import request,jsonify
from mongoengine import Q

from vote.api_1_0 import api
from vote.models import Competitor


@api.route('/search',methods=['POST'])
def search():

    # 如果参数为None，则使用长空格代替，方便模糊搜索
    cid=request.json.get('cid','    ')
    nickname=request.json.get('nickname','    ')
    name=request.json.get('name','     ')
    tel=request.json.get('tel','     ')

    search = {'__raw__': {'$or': [
            {'name': re.compile(name)},
            {'tel': re.compile(tel)},
            {'nickname': re.compile(nickname)},
            {'cid': re.compile(cid)}
        ]
    }}

    competitors=Competitor.objects(**search)
    res_json= {'count': len(competitors)}
    data=[]
    for item in competitors:
        data.append({'cid':item.cid,'name':item.name
                        ,'nickname':item.nickname,'tel':item.tel,'votes':item.vote_num})
    res_json['data']=data
    return json.dumps(res_json,ensure_ascii=False)
