import os
from peewee import *
from crypto import *


if os.getenv("TESTING") == "true":
    print("Running in test mode")
    mydb = SqliteDatabase('file:memory?mode=memory&cache=shared', uri=True)
else:
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
    user_id = ForeignKeyField(Users, backref="labs")
    lab_id = IntegerField()
    lab_admin = BooleanField()

class Groups(BaseModel):
    lab_id = ForeignKeyField(Labs, backref="groups")
    group_id = AutoField(primary_key=True)
    group_name = CharField()

class QRs(BaseModel):
    qr_id = CharField()
    group_id = CharField()
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

    class Meta:
        database = db
        db_table='QRs'
        primary_key = CompositeKey('qr_id', 'group_id')

# Drop tables if they exist\
def drop_tables():
    with db:
        db.drop_tables([Users, Labs, Lab_Permissions, Groups, QRs])
drop_tables()

db.connect()
db.create_tables([Users, Labs, Lab_Permissions, Groups, QRs])