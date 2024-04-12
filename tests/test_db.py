import unittest
from peewee import *


test_db = SqliteDatabase(':memory:')

class BaseModel(Model):
    class Meta:
        database = test_db

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

MODELS = [Users, Labs, Lab_Permissions, Groups, QRs]


class TestUserCreation(unittest.TestCase):
    def setUp(self):
        test_db.bind(MODELS, bind_refs=False, bind_backrefs=False)
        test_db.connect()
        test_db.create_tables(MODELS)

    def tearDown(self):
        test_db.drop_tables(MODELS)
        test_db.close()

    def test_user_creation(self):
        first_user = Users.create(email='john@example.com', password='123456')
        assert first_user.user_id == 1
        second_user = Users.create(email='jane@example.com', password='1234567')
        assert second_user.user_id == 2

        users = Users.select()

        first_user = users[0]
        self.assertEqual(first_user.email, 'john@example.com')
        self.assertEqual(first_user.password, '123456')

        second_user = users[1]
        self.assertEqual(second_user.email, 'jane@example.com')
        self.assertEqual(second_user.password, '1234567')
