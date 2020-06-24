# coding=utf-8
# redis排行榜键
REDIS_RANKING_LIST_KEY = 'rank_list'
# redis存放参赛者信息的hash表key
REDIS_COMPETITOR_HASH_KEY = 'competitors'
REDIS_VOTE_PREFIX = 'vote:'

# 自定义响应状态码

# 成功
SUCCESS = 200
# 请求参数错误
PARAMETER_ERROR = 1
# 非法参数
ILLEGAL_PARAMETER = 2
# 没有权限
NO_PERMISSION = 3
# 没有登录
NOT_LOGIN_IN = 4

# 登录失败
LOGIN_FAILED = 5
