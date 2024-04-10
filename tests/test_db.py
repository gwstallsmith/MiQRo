import unittest
from peewee import *

from database import *


MODELS = [Users, Labs, Lab_Permissions, Groups, QRs]


test_db = SqliteDatabase(':memory:', pragmas={'foreign_keys': 1})

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
        assert first_user.id == 1
        second_user = Users.create(email='jane@example.com', password='1234567')
        assert second_user.id == 2

        users = Users.select()

        first_user = users[0]
        self.assertEqual(first_user.email, 'john@example.com')
        self.assertEqual(first_user.password, '123456')

        second_user = users[1]
        self.assertEqual(second_user.email, 'jane@example.com')
        self.assertEqual(second_user.password, '1234567')
