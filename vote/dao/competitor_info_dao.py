# coding=utf-8
import json

from vote import redis_conn
from vote.constants import *
from vote import db


def get_competitor_info_by_cid(cid):
    """获取参数者的信息
    :param cid:
    :return:
    """
    flag = redis_conn.exists(cid)
    if flag != 1:
        # 加载参赛者信息到redis中
        comp_info = db.competitors.find_one({"cid": cid})
        print type(comp_info)
        # 跳过_id
        comp_info["_id"]=None
        comp_info_json = json.dumps(comp_info,skipkeys=True,ensure_ascii=False)
        redis_conn.setex(cid, REDIS_KEY_EXPIRE_COMPETITOR_INFO, comp_info_json)
        return comp_info
    return json.loads(redis_conn.get(cid))
