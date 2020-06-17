from . import db


class User(db.Document):
    """用户模型
    用户的角色有两种一种是普通用户，使用符号u表示
    另一种是管理员用户，使用符号a表示
    """
    object_id = db.ObjectIdField(db_field='_id')
    username = db.StringField(required=True)
    password = db.StringField(max_length=30, min_length=6, required=True)
    role = db.StringField(default='u')

    def __str__(self):
        return "object_id:{} - username:{} - password:{} -role:{}" \
            .format(self.object_id, self.username, self.password, self.role)


class Competitor(db.Document):
    """参赛选手模型
    其中cid是参赛选手的唯一编号
    tel为电话号码，且不能重复
    state为参赛选手的状态，参赛（join）和退出（out）
    vote记录所有为该选手投票的用户的objectId
    vote_num 记录选手所获得的所有的票数，选手得票数=用户投票+管理员加上得票数
    """
    cid = db.StringField(required=True)
    nickname = db.StringField()
    tel = db.StringField()
    state = db.StringField(default='join')
    vote_num = db.IntField()
    vote = db.ListField(db.ObjectIdField())

    def __str__(self):
        return "id:{} - nickname:{} - tel:{} - vote_num:{} - state:{}" \
            .format(self.cid, self.nickname, self.tel, self.vote_num,self.state)
