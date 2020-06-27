# coding=utf-8
# redis排行榜键
REDIS_RANKING_LIST_KEY = 'rank_list'
# redis存放参赛者信息的hash表key
REDIS_COMPETITOR_HASH_KEY = 'competitors'
REDIS_VOTE_PREFIX = 'vote:'

# redis分割符
REDIS_SPLIT=':'

# redis中一些键的过期时间
# 参赛者信息的过期时间
REDIS_KEY_EXPIRE_COMPETITOR_INFO = 10000
# 每个参赛者的选票集合的过期时间
REDIS_KEY_EXPIRE_VOTE_SET = 10000

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

# 参赛者状态
# 参赛状态
COMPETITOR_STATE_JOIN = 1
# 退赛状态
COMPETITOR_STATE_OUT = 0


# 用户每天最多能投的票数
N=10
# 用户每天最多给一个用户的最大票数
M=5
