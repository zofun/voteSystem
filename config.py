# coding=utf-8
import logging


class Config():
    """基础配置信息"""
    LOGGIONG_LEVEL = logging.DEBUG

    # jwt相关
    JWT_SECRET_KEY = 'AAAA'

    # json
    JSON_AS_ASCII = False  # 支持中文

    # redis相关配置
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DECODE_RESPONSE = True


class DevelopConfig(Config):
    """开发环境配置信息"""
    # mongoDB相关配置
    MONGODB_URL = 'mongodb://localhost:27017/'
    MONGODB_DB="votedb"

    # redis相关配置
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DECODE_RESPONSE = True

    # jwt相关
    JWT_SECRET_KEY = 'AAAA'

    # json
    JSON_AS_ASCII = False  # 支持中文


class ProductionConfig(Config):
    """生产环境配置信息"""
    MONGODB_URL = "mongodb://userofvotedb:tcw123456@121.199.76.80:27017/votedb"
    MONGODB_DB = "votedb"


configs = {
    'default': Config,
    'develop': DevelopConfig,
    'production': ProductionConfig
}
