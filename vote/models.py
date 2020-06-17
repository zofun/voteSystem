from . import db


class User(db.Document):
    name = db.StringField(max_length=30, required=True)
    password = db.StringField(max_length=30, min_length=6, required=True)
    phone = db.StringField()

    def __str__(self):
        return "name:{} - phone:{} - password:{}".format(self.name, self.phone, self.password)
