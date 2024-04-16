import unittest
from peewee import *


test_db = SqliteDatabase(':memory:')

class BaseModel(Model):
    class Meta:
        database = test_db

class Users(BaseModel):
    user_id = AutoField(primary_key=True)
    email = CharField()

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
        first_user = Users.create(email='john@example.com')
        assert first_user.user_id == 1
        second_user = Users.create(email='jane@example.com')
        assert second_user.user_id == 2

        users = Users.select()

        first_user = users[0]
        self.assertEqual(first_user.email, 'john@example.com')

        second_user = users[1]
        self.assertEqual(second_user.email, 'jane@example.com')

        # Create Labs for first user
        lab = Labs.create(lab_name="John Lab")
        Lab_Permissions.create(user_id=first_user, lab_id=lab.lab_id, lab_admin=True)

        # Retrieve the lab permissions
        lab_permissions = Lab_Permissions.get(Lab_Permissions.user_id == first_user)

        self.assertTrue(lab_permissions)

        # Create Groups without a lab to throw an error
        group = Groups.create(lab_id=lab, group_name="Birds" )
        self.assertIsNotNone(group)

        with self.assertRaises(Exception):
            Groups.create(group_name="Birds1")
        






    