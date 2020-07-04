import datetime

from flask import request, current_app


def logger_wrapper(func):
    """记录请求详细的装饰器
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        method = request.method
        url = request.url
        data = request.data
        args = request.args
        cur_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        request_info = "%s,%s,%s,%s,%s" % (cur_time, method, url, str(args), str(data))
        current_app.logger.info(request_info)
        return func(*args, **kwargs)

    return wrapper
