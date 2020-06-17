from flask import jsonify,current_app
from vote.api_1_0 import api
from vote.models import User


@api.route('/getusername')
def get_username():
    current_app.logger.info("收到请求")
    return jsonify({'userinfo': User.objects.all()}), 201


@api.route('/')
def index():
    return "hello world"


