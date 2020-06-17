from . import db


class User(db.Document):
    """用户模型
    用户的角色有两种一种是普通用户，使用符号u表示
    另一种是管理员用户，使用符号a表示

    """
    #user_id = db.StringField(primary_key=True)
    username = db.StringField(required=True)
    password = db.StringField(max_length=30, min_length=6, required=True)
    role = db.StringField(default='u')

    def __str__(self):
        return " username:{} - password:{} -role:{}" \
            .format( self.username, self.password, self.role)
