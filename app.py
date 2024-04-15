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
from flask_session import Session

from Scanner.MicroQRCodeScanner import do_stuff
import base64

from database import *
from crypto import *

import os
from peewee import *

from os import environ as env
from playhouse.shortcuts import model_to_dict
from dotenv import load_dotenv

import shutil
import json

from collections import defaultdict
from redis import Redis

import qrcode

load_dotenv()


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
#app.secret_key = env.get("APP_SECRET_KEY")

upload_folder = './uploads'

app.config['UPLOAD_FOLDER'] = upload_folder
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(host='redis', port=6379)
app.config['SESSION_PERMANENT'] = False
app.config['SECRET_KEY'] = os.urandom(24)
app.config.update(SESSION_COOKIE_NAME=os.urandom(24).hex())

oauth = OAuth(app)
server_session = Session(app)

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
    user, created = Users.get_or_create(email = token["userinfo"]["email"], password = "")
    session["user"] = token
    session["email"] = user.email
    session["user_id"] = user.user_id
    session["labs"] = getUserLabs()
    session["groups"] = getUserGroups()
    return redirect(url_for("homepage"))


@app.route("/login")
def login():
    session['labs'] = []
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/labhome")
def lab_home():
    return render_template('labs.html')

@app.route("/addlab")
def lab_add():
    return render_template('addlab.html')

@app.route("/createlab")
def lab_create():
    return render_template('createlab.html')

@app.route("/creategroup")
def render_create_group():
    return render_template('creategroup.html')

@app.route("/editdata")
def edit_data():
    return render_template('editdata.html')

@app.route("/generate_qrs")
def render_generate_qrs():
    return render_template('qr.html')

def get_highest_qr_id():
    highest_qr_id = QRs.select(fn.MAX(SQL('CAST(qr_id AS UNSIGNED)')))
    highest_qr_id = highest_qr_id.scalar()
    
    if highest_qr_id is not None:
        return int(highest_qr_id) + 1
    else:
        return 1



@app.route('/generate_codes', methods=['GET', 'POST'])
def generate_qr_code():
    number_of_codes = int(request.form['number_of_codes'])
    qr_size = int(request.form['code_size'])
    border_size = 1

    qr_codes = []  # List to store QR code PIL images

    # Loop to generate QR codes
    for i in range(get_highest_qr_id(), number_of_codes + get_highest_qr_id()):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=qr_size,
            border=border_size,
        )

        QRs.create(qr_id = str(i))

        qr.add_data(str(i))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qr_codes.append(img)  # Append QR code image to list

    rows = int((number_of_codes - 1) / 6) + 1
    cols = min(number_of_codes, 6)

    total_width = int(qr_size * 32 + border_size/2) * cols
    total_height = int(qr_size * 32 + border_size) * rows

    combined_image = Image.new('RGB', (total_width, total_height), color='white')


    for i, qr_code_img in enumerate(qr_codes):
        row = int(i/cols)
        col = i % cols

        x_offset = col * (qr_size * 32 + border_size)
        y_offset = row * (qr_size * 32 + border_size)

        combined_image.paste(qr_code_img, (x_offset, y_offset))

    # Save the combined image
    file_name = 'qr.png'
    combined_image.save('static/' + file_name)

    return render_template('qr.html', file_name=file_name)

 
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

    return render_template('home.html', session = session)


@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if 'user' not in session: 
        return redirect(url_for("main"))
    if request.method == 'POST' :
        file = request.files['file']
        if file:
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, 'temp.png')
            image.save(temp_file_path)
            img, ids, coordinate_map = do_stuff(temp_file_path, "./outputs")

            os.remove(temp_file_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
            with open('./outputs/temp.svg', 'r') as file:
                data = file.read()
                encoded = base64.b64encode(data.encode()).decode()


            qr_values = list(ids.values())
            qr_values = [x.lstrip('0') for x in qr_values]

            qr_data = QRs.select().where((QRs.qr_id.in_(qr_values)) & (QRs.group_id == list(session["selectedGroup"].keys())[0]))
            qr_data = qr_data.execute()


            session['img'] = encoded
            session['ids'] = ids
            session['squares'] = coordinate_map

            
            return render_template('fetch.html', message='File uploaded successfully', session = session.get("user"), img = encoded, ids=ids, squares = coordinate_map, qr_data = qr_data, selected_group = list(session["selectedGroup"].values())[0], selected_lab= list(session["selectedLab"].values())[0])
    
    if 'img' in session and 'ids' in session and 'squares' in session :
        qr_values = list(session['ids'].values())
        qr_values = [x.lstrip('0') for x in qr_values]
        qr_data = QRs.select().where((QRs.qr_id.in_(qr_values)) & (QRs.group_id == list(session["selectedGroup"].keys())[0]))
        qr_data = qr_data.execute()
        #qr_data = QRs.get_or_none(QRs.qr_id.in_(qr_values), QRs.group_id == session["selectedGroup"])
        return render_template('fetch.html', session=session.get("user"), img = session['img'], ids = session['ids'], squares = session['squares'], qr_data = qr_data,  selected_group = list(session["selectedGroup"].values())[0], selected_lab= list(session["selectedLab"].values())[0])
    
    return render_template('fetch.html',  selected_group = list(session["selectedGroup"].values())[0], selected_lab= list(session["selectedLab"].values())[0])


@app.route('/set/labandgroup', methods=['POST'])
def setLabandGroup() :
    if 'user' not in session: 
        return redirect(url_for("main"))
    if request.method == 'POST' :
        lab = request.form['labSelect']
        group = request.form['grpSelect']

        try: 
            selLab = Labs.get(Labs.lab_id == lab)
            session['selectedLab'] = {selLab.lab_id: selLab.lab_name}
        except Labs.DoesNotExist:
            return None
        

        selGroup = Groups.get(Groups.group_id == group)
        session['selectedGroup'] = {selGroup.group_id: selGroup.group_name}

        if 'img' in session: 
            session.pop('img')
        if 'ids' in session:
            session.pop('ids')
        if 'squares' in session:
            session.pop('squares')

        return redirect(url_for('scan'))


@app.route('/editQRData', methods=['POST'])
def editQRData() :
    if 'user' not in session: 
        return redirect(url_for("main"))
    if request.method == 'POST' :

        qr_id_ = request.form['QR_ID']
        group = list(session['selectedGroup'].keys())[0]

        #print("QR_ID", qr_id, flush=True)

        qr = QRs.get((QRs.qr_id == qr_id_) & (QRs.group_id == group))

        if request.form['attr_0'] != "" :
            qr.attr_0 = request.form['attr_0']
        if request.form['attr_1'] != "" :
            qr.attr_1 = request.form['attr_1']
        if request.form['attr_2'] != "" :
            qr.attr_2 = request.form['attr_2']
        if request.form['attr_3'] != "" :
            qr.attr_3 = request.form['attr_3']
        if request.form['attr_4'] != "" :
            qr.attr_4 = request.form['attr_4']
        if request.form['attr_5'] != "" :
            qr.attr_5 = request.form['attr_5']
        if request.form['attr_6'] != "" :
            qr.attr_6 = request.form['attr_6']
        if request.form['attr_7'] != "" :
            qr.attr_7 = request.form['attr_7']
        if request.form['attr_8'] != "" :
            qr.attr_8 = request.form['attr_8']
        if request.form['attr_9'] != "" :
            qr.attr_9 = request.form['attr_9']

        qr.save()

        return redirect(url_for("scan"))
    

@app.route('/addQRData', methods=['POST'])
def addQRData() :
    if 'user' not in session: 
        return redirect(url_for("main"))
    if request.method == 'POST' :

        qr_id_ = request.form['addQR']
        group = list(session['selectedGroup'].keys())[0]

        qr = QRs.insert(qr_id = qr_id_, group_id = group).execute()

        qr = QRs.get((QRs.qr_id == qr_id_) & (QRs.group_id == group))


        if request.form['attr_0'] != "" :
            qr.attr_0 = request.form['attr_0']
        if request.form['attr_1'] != "" :
            qr.attr_1 = request.form['attr_1']
        if request.form['attr_2'] != "" :
            qr.attr_2 = request.form['attr_2']
        if request.form['attr_3'] != "" :
            qr.attr_3 = request.form['attr_3']
        if request.form['attr_4'] != "" :
            qr.attr_4 = request.form['attr_4']
        if request.form['attr_5'] != "" :
            qr.attr_5 = request.form['attr_5']
        if request.form['attr_6'] != "" :
            qr.attr_6 = request.form['attr_6']
        if request.form['attr_7'] != "" :
            qr.attr_7 = request.form['attr_7']
        if request.form['attr_8'] != "" :
            qr.attr_8 = request.form['attr_8']
        if request.form['attr_9'] != "" :
            qr.attr_9 = request.form['attr_9']

        qr.save()

        return redirect(url_for("scan"))


    
        

@app.route('/labs', methods=['POST', 'GET'])
def labsPage() :
    if 'user' not in session:
        return redirect(url_for("main"))
    

    
    return render_template("labs.html", session = session)


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
    

#@app.route('/api/getUserLabs', methods=['GET'])
def getUserLabs() :
    query = (Labs
             .select(Labs.lab_id, Labs.lab_name)
             .join(Lab_Permissions, on=(Labs.lab_id == Lab_Permissions.lab_id))
             .where(Lab_Permissions.user_id == session['user_id']))
    
    labs = [(lab.lab_id, lab.lab_name) for lab in query]


    return labs

@app.route('/api/getUserGroups')
def getUserGroups() :
    lab_groups = defaultdict()

    user_labs = (Labs
             .select(Labs.lab_id, Labs.lab_name)
             .join(Lab_Permissions, on=(Labs.lab_id == Lab_Permissions.lab_id))
             .where(Lab_Permissions.user_id == session['user_id']))
    
    for lab in user_labs:
        groups = [{'id': group.group_id, 'name': group.group_name} for group in lab.groups]
        lab_groups[lab.lab_id] = {'name': lab.lab_name, 'groups': groups}

    return lab_groups

@app.route('/api/getUserGroupsD')
def getUserGroupsD() :
    lab_groups = defaultdict()

    user_labs = (Labs
             .select(Labs.lab_id, Labs.lab_name)
             .join(Lab_Permissions, on=(Labs.lab_id == Lab_Permissions.lab_id))
             .where(Lab_Permissions.user_id == session['user_id']))
    
    for lab in user_labs:
        groups = [{'id': group.group_id, 'name': group.group_name} for group in lab.groups]
        lab_groups[lab.lab_id] = {'name': lab.lab_name, 'groups': groups}

    return {"Lab Groups": lab_groups}

    


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

    user_id_ = session['user_id']

    try:
        user = Users.get(Users.user_id == user_id_)
    except Users.DoesNotExist:
        return {'error:' 'Invalid User'}, 400
    
    lab = Labs.create(lab_name = lab_name)

    print("USERID: ", int(user_id_), flush=True)

    Lab_Permissions.create(user_id = int(user_id_), lab_id = lab.lab_id, lab_admin = True)

    session['labs'] = getUserLabs()
    

    if (request.form.get('returnTo') == "labPage") :
        return redirect(url_for("labsPage"))
    else:
        return redirect(url_for('homepage'))

@app.route("/api/create_group", methods=['GET', 'POST'])
def create_group():

    group_name = request.form.get('group_name')
    lab_id = request.form.get('lab_id')

    if not group_name:
        return {'error': 'Invalid group name'}, 400

    group = Groups.create(lab_id = lab_id, group_name = group_name)

    userinfo = {
        "email": session.get('email'),
        "user_id": session.get('user_id'),
        "lab_id": session.get('lab_id'),
        "group_id": group.group_id
    }

   # session["user"] = userinfo
    session["groups"] = getUserGroups()

    if (request.form.get('returnTo') == "labPage") :
        return redirect(url_for("labsPage"))
    else:
        return redirect(url_for('homepage'))

@app.route("/api/groups", methods=['GET'])
def get_groups():
    groups_created = [
        model_to_dict(g)
        for g in Groups
    ]
    return None


@app.route('/api/qrs/', methods=['GET'])
def get_qrs():
    qrs = [
        model_to_dict(p)
        for p in QRs
    ]

    if not qrs:
        return {'qrs: ': len(qrs)}
    
    return {'qrs: ': qrs}
    

@app.route('/getCurrentUser')
def getCurrentUser(): 
    return {"User: ": session['user']}

@app.route('/qrbygroup')
def qrbygroup(): 
    query = (QRs
             .select(QRs.group_id, QRs.qr_id, QRs.attr_0, QRs.attr_1, QRs.attr_2,
                     QRs.attr_3, QRs.attr_4, QRs.attr_5, QRs.attr_6,
                     QRs.attr_7, QRs.attr_8, QRs.attr_9)
             .join(Groups, on=(QRs.group_id == Groups.group_id))
             .order_by(QRs.group_id))

    qr_data_by_group = {}
    for qr in query:
        group_id = qr.group_id.group_id
        qr_info = [qr.qr_id, qr.attr_0, qr.attr_1, qr.attr_2, qr.attr_3,
                   qr.attr_4, qr.attr_5, qr.attr_6, qr.attr_7, qr.attr_8, qr.attr_9]
        if group_id not in qr_data_by_group:
            qr_data_by_group[group_id] = []
        qr_data_by_group[group_id].append(qr_info)

    return {"Result":qr_data_by_group}

# ==========================================================================
if __name__ == "__main__":
    app.run(debug=True)
