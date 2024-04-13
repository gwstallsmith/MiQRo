from flask import Flask, render_template, request
from PIL import Image
import io
import tempfile
import os
from peewee import *
import re

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, send_from_directory
from authlib.integrations.base_client.errors import OAuthError

from Scanner.MicroQRCodeScanner import do_stuff
import base64

from database import *
from crypto import *

import os
from peewee import *

from os import environ as env
from playhouse.shortcuts import model_to_dict
from dotenv import load_dotenv

load_dotenv()


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

upload_folder = './uploads'

app.config['UPLOAD_FOLDER'] = upload_folder

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


# Controllers API
@app.route("/")
def main():
    error = None
    if 'error' in session: 
        error = session['error']
        session.pop('error')
    return render_template(
        "login.html",

    )

        #session=session.get("user"),
        #pretty=json.dumps(session.get("user"), indent=4),
        #error=error,
@app.route("/callback", methods=["GET", "POST"])
def callback():
    try: 
        token = oauth.auth0.authorize_access_token()
    except OAuthError as e:
        if e.error == "access_denied":
            session['error'] = "You must sign in with a kent.edu email!"
            return redirect(url_for("main"))
    session["user"] = token
    return redirect(url_for("homepage"))


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/labhome")
def lab_home():
    return render_template('labhome.html')

@app.route("/addlab")
def lab_add():
    return render_template('addlab.html')

@app.route("/createlab")
def lab_create():
    return render_template('createlab.html')

@app.route("/creategroup")
def create_group():
    return render_template('creategroup.html')

@app.route("/editdata")
def edit_data():
    return render_template('editdata.html')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("main", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

#Hompage that allows uploading of files to be extracted and decoded
@app.route('/home', methods=['GET', 'POST'])
def homepage():
    if 'user' not in session:
        return redirect(url_for("main"))
    if request.method == 'POST' :
        file = request.files['file']
        if file:
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, 'temp.jpg')
            image.save(temp_file_path)
            value = do_stuff(temp_file_path, "./outputs")
           # java_command = f"java -jar ./applications.jar BatchScanMicroQrCodes -i {temp_file_path} -o output.json"
           # result = subprocess.run(java_command, shell=True, capture_output=True)
           # print(result.stdout)
           # print(result.stderr)

            os.remove(temp_file_path)
            os.rmdir(temp_dir)
            with open('./outputs/temp.svg', 'r') as file:
                data = file.read()
                encoded = base64.b64encode(data.encode()).decode()

            return render_template('index.html', message='File uploaded successfully', session = session.get("user"), img = encoded)
    return render_template('index.html', session = session.get("user"))


# ==========================================================================
# CREATING ENDPOINTS FOR USER REGISTRATION
@app.route('/api/register', methods=['POST'])
def postUserCreated():
    email = request.form.get('email')
    password = hash_password(request.form.get('password'))
    if not email:
        return {'error': 'Invalid email'}, 400
    if not password:
        return {'error': 'Invalid email'}, 400
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {'error': 'Invalid Email: Please provide a valid email address.'}, 400


    user = Users.create(email = email, password = password)
    userinfo = {
        "email": user.email,
        "user_id": user.user_id
    }
    session["user"] = userinfo


    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def userLogin():
    email = request.form.get('email')
    password = hash_password(request.form.get('password'))
    if not email:
        return {'error': 'Invalid email'}, 400
    if not password:
        return {'error': 'Invalid email'}, 400
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {'error': 'Invalid Email: Please provide a valid email address.'}, 400
    
    try:
        user = Users.get(Users.email == email, Users.password == password)
        
        userinfo = {
            "email": user.email,
            "user_id": user.user_id
        }

        # Need to input session data appropriately
        session["user"] = userinfo


        return render_template('index.html')
        return {'message': 'User logged in successfully'}
    except Users.DoesNotExist:
        return {'message': 'User not found'}
    


@app.route('/api/user', methods=['GET'])
def getUserCreated():
   
    users_created = [
        model_to_dict(p)
        for p in Users
    ]

    if not users_created:
        return {'users_created': len(users_created)}

    return {'users_created': users_created}


@app.route('/api/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = Users.get_by_id(user_id)
        user.delete_instance()
        return {'message': 'User deleted successfully'}
    except Users.DoesNotExist:
        return {'error': 'User with that id not found'}
    
@app.route('/api/labs/', methods=['GET'])
def get_labs():
    labs_created = [
        model_to_dict(l)
        for l in Labs
    ]

    if not labs_created:
        return {'labs_create: ': len(labs_created)}
    
    return {'labs_create: ': labs_created}

@app.route('/api/lab_permissions/', methods=['GET'])
def get_lab_permissions():
    lab_permissions_created = [
        model_to_dict(p)
        for p in Lab_Permissions
    ]

    if not lab_permissions_created:
        return {'lab_permissions: ': len(lab_permissions_created)}
    
    return {'lab_permissions: ': lab_permissions_created}

@app.route("/api/create_lab", methods=['GET', 'POST'])
def create_lab():
    lab_name = request.form.get('lab_name')

    if not lab_name:
        return {'error': 'Invalid lab name'}, 400

    lab = Labs.create(lab_name = lab_name)

    user_id = int(session.get('user').get('user_id'))

    Lab_Permissions.create(lab_user = user_id, lab_id = lab.lab_id, lab_admin = True)
    

    return render_template('labhome.html')

@app.route("/api/create_group", methods=['GET', 'POST'])
def create_group():
    return None


@app.route("/api/groups", methods=['GET'])
def get_groups():
    groups_created = [
        model_to_dict(g)
        for g in Groups
    ]
    return None

# ==========================================================================
if __name__ == "__main__":
    app.run(debug=True)