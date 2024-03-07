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


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# Connect app to mysql server
mydb =  MySQLDatabase(os.getenv("MYSQL_DATABASE"),
        user = os.getenv("MYSQL_USER"),
        password = os.getenv("MYSQL_PASSWORD"),
        host = os.getenv("MYSQL_HOST"),
        port = 3306
)
print(mydb)


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
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
        error=error,
    )


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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 8080))
