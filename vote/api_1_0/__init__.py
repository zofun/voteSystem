from flask.blueprints import Blueprint


api = Blueprint('api_1_0', __name__, url_prefix='/api/1.0')


from . import user,admin,search,vote_manager
