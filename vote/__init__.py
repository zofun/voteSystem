# coding=utf-8
import json
import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

from config import configs
from vote.constants import *

# 设置能被外界访问的对象
# redis连接
redis_conn = None
# mongoDB连接
mongo_conn = None
# mongoDB数据库对象
db = None
# 配置信息
conf = None


def setup_logging(levle):
    """初始化日志记录器
    :param levle: 日志记录等级
    :return:
    """
    # 设置日志记录等级
    logging.basicConfig(level=levle)
    # 创建日志记录器
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100)
    logging.getLogger().addHandler(file_log_handler)


def load_data_to_redis():
    """将参赛者信息加载到redis中
    包括排名zset
    记录参赛者信息的hash
    为参赛者维护一个投票set，记录所有给他投票的用户信息
    :return:
    """


def get_app(config_name):
    """app工厂函数
    :param config_name: 当前环境名称
    :return:
    """
    # 配置信息
    conf = configs[config_name]
    setup_logging(conf.LOGGIONG_LEVEL)
    # 创建app
    app = Flask(__name__)
    # 加载配置文件
    app.config.from_object(configs[config_name])
    # 对mongoDB进行配置

    global mongo_conn
    mongo_conn = MongoClient('mongodb://localhost:27017/')
    global db
    db = mongo_conn[conf.MONGODB_DB]
    # mongo_conn = MongoClient("mongodb://"+conf.MONGODB_USERNAME+":"+conf.MONGODB_PASSWORD+"@"+conf.MONGODB_HOST+":"+str(conf.MONGODB_PORT)+"/"+conf.MONGODB_DB)

    # 对jwt进行配置
    app.config['JWT_SECRET_KEY'] = conf.JWT_SECRET_KEY
    jwt = JWTManager(app)

    # 对redis进行配置，使用连接池
    pool = redis.ConnectionPool(host=conf.REDIS_HOST, port=conf.REDIS_PORT, decode_responses=True)
    global redis_conn
    redis_conn = redis.Redis(connection_pool=pool)

    # 用的时候再导包，防止出现循环依赖
    from vote.api_1_0 import api
    # 注册到蓝图
    app.register_blueprint(api)
    return app
