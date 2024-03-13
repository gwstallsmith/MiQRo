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

from cryptography import *
import hashlib
import base64


def hash_password(password):
    password = password.encode('utf-8')

    hash = hashlib.sha256()             # Create Hashing object
    hash.update(password)               # Apply hashing algorithm
    hash_password = hash.hexdigest()    # Use hex representation

    return hash_password