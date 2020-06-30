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
    key = REDIS_COMPETITOR_INFO_PREFIX + cid
    comp_info = redis_conn.get(key)
    if comp_info is None:
        # redis 中没有查询到，那么查mongo 并写入redis
        comp_info = db.competitors.find_one({"cid": cid})
        if comp_info is None:
            return None
        # 跳过_id
        comp_info["_id"] = None
        comp_info_json = json.dumps(comp_info, skipkeys=True, ensure_ascii=False)
        redis_conn.setex(key, REDIS_KEY_EXPIRE_COMPETITOR_INFO, comp_info_json)
        return comp_info
    return json.loads(comp_info)
