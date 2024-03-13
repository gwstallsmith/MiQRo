import os
from peewee import *

from os import environ as env

from crypto import *

import os
from peewee import *

from os import environ as env


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
    user_id = CharField(primary_key=True)
    email = CharField(unique=True)
    password = CharField()


# Create tables if they do not exist
#def create_tables():
#    with database:
#        database.create_tables([Users])

# Drop tables if they exist
def drop_tables():
    with db:
        db.drop_tables([Users])


db.connect()
db.create_tables([Users])


