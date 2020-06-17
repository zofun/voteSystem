import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask
from flask_mongoengine import MongoEngine
from config import configs



# 设置能被外界访问的对象
# redis连接
redis_conn = None
# mongoDB连接
db = None


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
    app.config['MONGODB_SETTINGS'] = {
        'db': conf.MONGODB_DB,
        'host': conf.MONGODB_HOST,
        'port': conf.MONGODB_PORT,
        'authentication_source': conf.MONGODB_AUTHENTICATION_SOURCE,
        'username': conf.MONGODB_USERNAME,
        'password': conf.MONGODB_PASSWORD
    }

    global db
    db = MongoEngine(app)

    # 对redis进行配置，使用连接池
    pool = redis.ConnectionPool(host=conf.REDIS_HOST, port=conf.REDIS_PORT, decode_responses=True)
    redis_conn = redis.Redis(connection_pool=pool)

    # 用的时候再导包，防止出现循环依赖
    from vote.api_1_0 import api
    # 注册到蓝图
    app.register_blueprint(api)
    return app
