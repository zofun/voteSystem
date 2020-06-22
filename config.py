# coding=utf-8
import logging


class Config:
    """基础配置信息"""
    LOGGIONG_LEVEL = logging.DEBUG


class DevelopConfig(Config):
    """开发环境配置信息"""
    # mongoDB相关配置
    MONGODB_DB = "votedb"
    MONGODB_HOST = "121.199.76.80"
    MONGODB_PORT = 27017
    MONGODB_AUTHENTICATION_SOURCE = 'admin'
    MONGODB_USERNAME = 'userofvotedb'
    MONGODB_PASSWORD = 'userofvotedb'

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


configs = {
    'default': Config,
    'develop': DevelopConfig,
    'production': ProductionConfig
}
