import os
from peewee import *

from os import environ as env

from crypto import *

import os
from peewee import *

from os import environ as env


from peewee import *

# Define your MySQL database connection parameters
database = MySQLDatabase('your_database_name', user='your_username', password='your_password', host='localhost', port=3306)

# Define your Peewee models
class BaseModel(Model):
    class Meta:
        database = database

class Users(BaseModel):
    user_id = TextField(primary_key=True)
    email = TextField(unique=True)

class Group_Template(BaseModel):
    group_id = IntegerField(primary_key=True)
    attribute_id = TextField()
    attribute_name = TextField()

class Groups(BaseModel):
    group_id = IntegerField(primary_key=True)
    lab_id = IntegerField()
    group_name = TextField()

class Lab_Permissions(BaseModel):
    user_id = TextField()
    lab_id = IntegerField()
    lab_admin = IntegerField(constraints=[Check('lab_admin IN (0, 1)')])

    class Meta:
        primary_key = CompositeKey('user_id', 'lab_id')

class Labs(BaseModel):
    lab_id = TextField(primary_key=True)
    lab_name = TextField(unique=True)

class QR_Template(BaseModel):
    qr_id = IntegerField(primary_key=True)
    attribute_1 = TextField()
    attribute_2 = TextField()
    attribute_3 = TextField()
    attribute_4 = TextField()
    attribute_5 = TextField()
    attribute_6 = TextField()
    attribute_7 = TextField()
    attribute_8 = TextField()
    attribute_9 = TextField()
    attribute_10 = TextField()


