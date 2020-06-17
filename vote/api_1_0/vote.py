from vote.api_1_0 import api


@api.route('/vote/<cid>/<uid>')
def vote(cid,uid):
    print(str(cid)+"  "+str(uid))