from flask import Flask, render_template, request
from PIL import Image
import io
import tempfile
import subprocess
import os
from peewee import *

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for
from authlib.integrations.base_client.errors import OAuthError

from Scanner.MicroQRCodeScanner import do_stuff
import base64


# Initialize database connection as a global variable
database =  MySQLDatabase(os.getenv("MYSQL_DATABASE"),
        user = os.getenv("MYSQL_USER"),
        password = os.getenv("MYSQL_PASSWORD"),
        host = os.getenv("MYSQL_HOST"),
        port = 3306
)



class BaseModel(Model):
    class Meta:
        database = database

class Users(BaseModel):
    user_id = CharField(primarykey=True)
    email = CharField(unique=True)
    password = CharField(unique=True)

class Groups(BaseModel):
    group_id = AutoField(primary_key=True)
    lab_id = IntegerField()
    group_name = CharField()

    class Meta:
        indexes = (
            (('lab_id', 'group_name'), True),
        )

class LabPermissions(BaseModel):
    user_id = ForeignKeyField(Users)
    lab_id = ForeignKeyField(Groups)
    lab_admin = BooleanField()

    class Meta:
        primary_key = CompositeKey('user_id', 'lab_id')

class Labs(BaseModel):
    lab_id = AutoField(primary_key=True)
    lab_name = CharField(unique=True)


database.connect()

# Create tables if they do not exist
def create_tables():
    with database:
        database.create_tables([Users, Groups, LabPermissions, Labs])

# Drop tables if they exist
def drop_tables():
    with database:
        database.drop_tables([Users, Groups, LabPermissions, Labs])

