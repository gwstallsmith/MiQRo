import os
from peewee import *
from crypto import *



# Initialize database connection as a global variable
db =  MySQLDatabase(os.getenv("MYSQL_DATABASE"),
        user = os.getenv("MYSQL_USER"),
        password = os.getenv("MYSQL_PASSWORD"),
        host = os.getenv("MYSQL_HOST"),
        port = 3306
)

print(db)

class BaseModel(Model):
    class Meta:
        database = db

class Users(BaseModel):
    user_id = AutoField(primary_key=True)
    email = CharField()
    password = CharField()

class Labs(BaseModel):
    lab_id = AutoField(primary_key=True)
    lab_name = CharField()

class Lab_Permissions(BaseModel):
    lab_user = ForeignKeyField(Users, backref="labs")
    lab_id = IntegerField()
    lab_admin = BooleanField()

class Groups(BaseModel):
    lab_id = ForeignKeyField(Labs, backref="groups")
    group_id = AutoField(primary_key=True)
    group_name = CharField()

class QRs(BaseModel):
    qr_id = AutoField(primary_key=True)
    group_id = ForeignKeyField(Groups, backref="qrs")
    attr_0 = CharField()
    attr_1 = CharField()
    attr_2 = CharField()
    attr_3 = CharField()
    attr_4 = CharField()
    attr_5 = CharField()
    attr_6 = CharField()
    attr_7 = CharField()
    attr_8 = CharField()
    attr_9 = CharField()

# Drop tables if they exist
def drop_tables():
    with db:
        db.drop_tables([Labs, Lab_Permissions, Groups, QRs])
#drop_tables()

db.connect()
db.create_tables([Users, Labs, Lab_Permissions, Groups, QRs])
