from vote import get_app
from vote import db,redis_conn
from flask import jsonify
from vote import load_data_to_redis


app = get_app('develop')


if __name__ == '__main__':

    print(app.url_map)
    app.run()


