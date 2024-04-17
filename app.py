from flask import Flask, render_template, request
from PIL import Image
import io
import tempfile
import os
from peewee import *
import re
import peewee
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, send_from_directory
from authlib.integrations.base_client.errors import OAuthError
from flask_session import Session
from Scanner.MicroQRCodeScanner import scan_qr_codes
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
import random 
import string
import qrcode
import segno

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

#Create oauth connection
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


#Main page
@app.route("/")
def main():
    error = None
    if 'error' in session: 
        error = session['error']
        session.pop('error')
    return render_template(
        "login.html")


#Callback function that is called after the user logs in
@app.route("/callback", methods=["GET", "POST"])
def callback():
    try: 
        token = oauth.auth0.authorize_access_token()
    except OAuthError as e:
        if e.error == "access_denied":
            session['error'] = "You must sign in with a kent.edu email!"
            return redirect(url_for("main"))
    user, created = Users.get_or_create(email = token["userinfo"]["email"])

    #Set the session variables
    session["user"] = token
    session["email"] = user.email
    session["user_id"] = user.user_id
    session["labs"] = getUserLabs()
    session["groups"] = getUserGroups()
    session['labMembers'] = getLabMembers()
    session["name"] = session["user"]["userinfo"]["given_name"]
    return redirect(url_for("homepage"))


#Login function that redirects to the auth0 login page
@app.route("/login")
def login():
    session['labs'] = []
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


#Logout function that clears session data and logs the user out
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

#Hompage
@app.route('/home', methods=['GET', 'POST'])
def homepage():
    if 'user' not in session:
        return redirect(url_for("main"))

    return render_template('home.html', session = session)



#Fetch page
@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if 'user' not in session: 
        return redirect(url_for("main"))
    #If the user uploads an image
    if request.method == 'POST' :
        file = request.files['file']
        if file:

            #Read the image file
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))

            #Save the image to a temporary file
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, 'temp.png')
            image.save(temp_file_path, 'PNG')

            #Call the scan_qr_codes function to process the image, exception occurs if no QR codes are found
            try:
                #Returns the image with the QR codes highlighted, the QR code ids, and the coordinates of the QR codes
                img, ids, coordinate_map = scan_qr_codes(temp_file_path, "./outputs")
            except Exception as e:
                os.remove(temp_file_path)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return render_template('fetch.html', message='Error processing image', session=session)

            #Delete the temporary file
            os.remove(temp_file_path)
            shutil.rmtree(temp_dir, ignore_errors=True)

            #Open the SVG file and encode it to base64
            with open('./outputs/temp.svg', 'r') as file:
                data = file.read()
                encoded = base64.b64encode(data.encode()).decode()

            #Get the QR code values
            qr_values = list(ids.values())
            qr_values = [x.lstrip('0') for x in qr_values]

            #Get the QR code data from the database that matches the QR code values scanned
            qr_data = QRs.select().where((QRs.qr_id.in_(qr_values)) & (QRs.group_id == list(session["selectedGroup"].keys())[0]))
            qr_data = qr_data.execute()

            #Store the image, QR code ids, and coordinates in the session so it can be used after refresh
            session['img'] = encoded
            session['ids'] = ids
            session['squares'] = coordinate_map

            
            return render_template('fetch.html', message='File uploaded successfully', session=session, user = session.get("user"), img = encoded, ids=ids, squares = coordinate_map, qr_data = qr_data, selected_group = list(session["selectedGroup"].values())[0], selected_lab= list(session["selectedLab"].values())[0])
    
    #If the user refreshes the page, the session variables are used to display the image and QR code data
    if 'img' in session and 'ids' in session and 'squares' in session :
        qr_values = list(session['ids'].values())
        qr_values = [x.lstrip('0') for x in qr_values]
        qr_data = QRs.select().where((QRs.qr_id.in_(qr_values)) & (QRs.group_id == list(session["selectedGroup"].keys())[0]))
        qr_data = qr_data.execute()
        #qr_data = QRs.get_or_none(QRs.qr_id.in_(qr_values), QRs.group_id == session["selectedGroup"])
        return render_template('fetch.html', session = session, user=session.get("user"), img = session['img'], ids = session['ids'], squares = session['squares'], qr_data = qr_data,  selected_group = list(session["selectedGroup"].values())[0], selected_lab= list(session["selectedLab"].values())[0])
    
    return render_template('fetch.html', session=session, selected_group = list(session["selectedGroup"].values())[0], selected_lab= list(session["selectedLab"].values())[0])


#Set the selected lab and group for the scan function to utilize
@app.route('/set/labandgroup', methods=['POST'])
def setLabandGroup() :
    if 'user' not in session: 
        return redirect(url_for("main"))
    
    if request.method == 'POST' :
        lab = request.form['labSelect']
        group = request.form['grpSelect']

        #Set the selected lab and group in the session
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



#Edit existing QR code data
@app.route('/editQRData', methods=['POST'])
def editQRData() :
    if 'user' not in session: 
        return redirect(url_for("main"))
    
    if request.method == 'POST' :

        #Get the QR code id and group id from form
        qr_id_ = request.form['QR_ID']
        group = list(session['selectedGroup'].keys())[0]

        #Get the QR code data from the database
        qr = QRs.get((QRs.qr_id == qr_id_) & (QRs.group_id == group))

        #If the user clicks save, update the QR code data
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

#Edit QR data but return to the labs page  
#Also adds functionality to delete QR codes 
@app.route('/editQRDatalp', methods=['POST'])
def editQRDataLabPage() : 
    if 'user' not in session: 
        return redirect(url_for("main"))
    if request.method == 'POST' :

        qr_id_ = request.form['QR_ID']
        group = request.form['groupID']

        if request.form['action'] == "save" :

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

        if request.form['action'] == "delete" :
            deleteQuery = QRs.delete().where((QRs.qr_id == qr_id_) & (QRs.group_id == group))
            deleteQuery.execute()


        return redirect(url_for("labsPage"))
    

#Add new QR code data
@app.route('/addQRData', methods=['POST'])
def addQRData() :
    if 'user' not in session: 
        return redirect(url_for("main"))
    
    if request.method == 'POST' :

        #Get the QR code id and group id from form
        qr_id_ = request.form['addQR']
        group = list(session['selectedGroup'].keys())[0]

        #Insert the new QR code data into the database
        qr = QRs.insert(qr_id = qr_id_, group_id = group).execute()

        #Get the QR code data from the database
        qr = QRs.get((QRs.qr_id == qr_id_) & (QRs.group_id == group))

        #Add data the the QR code
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


#Labs page that shows all users labs, groups, and QR codes
@app.route('/labs', methods=['POST', 'GET'])
def labsPage() :
    if 'user' not in session:
        return redirect(url_for("main"))
    
    #Get all QR codes and their data based on group ID
    query = (QRs
             .select(QRs.group_id, QRs.qr_id, QRs.attr_0, QRs.attr_1, QRs.attr_2,
                     QRs.attr_3, QRs.attr_4, QRs.attr_5, QRs.attr_6,
                     QRs.attr_7, QRs.attr_8, QRs.attr_9)
             .join(Groups, on=(QRs.group_id == Groups.group_id))
             .order_by(QRs.group_id))

    #Store the QR code data in a dictionary based on group ID
    qr_data_by_group = {}
    for qr in query:
        group_id = qr.group_id
        qr_info = [qr.qr_id, qr.attr_0, qr.attr_1, qr.attr_2, qr.attr_3,
                   qr.attr_4, qr.attr_5, qr.attr_6, qr.attr_7, qr.attr_8, qr.attr_9]
        if group_id not in qr_data_by_group:
            qr_data_by_group[group_id] = []
        qr_data_by_group[group_id].append(qr_info)
    
    return render_template("labs.html", session = session, qr_data = qr_data_by_group)

    

#Function to get all labs a user is a part of
def getUserLabs() :

    #Get all lab information
    query = (Labs
             .select(Labs.lab_id, Labs.lab_name, Labs.invite_code)
             .join(Lab_Permissions, on=(Labs.lab_id == Lab_Permissions.lab_id))
             .where(Lab_Permissions.user_id == session['user_id']))
    
    #Get informtion on which labs the user is an admin of
    query2 = (Lab_Permissions.select(Lab_Permissions.lab_id, Lab_Permissions.lab_admin)
              .where(Lab_Permissions.user_id == session['user_id']))
    

    #Create a list of all labs the user is a part of and if they are an admin
    labs = [[lab.lab_id, lab.lab_name, lab.invite_code] for lab in query]
    admin_labs = [(lab.lab_id, lab.lab_admin) for lab in query2]
    lab_admins_dict = {lab_id: isAdmin for lab_id, isAdmin in admin_labs}
    for lab in labs:
        lab_id = lab[0]
        lab.append(lab_admins_dict.get(lab_id, False))

    return labs


#Get all groups a user is a part of
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


@app.route('/api/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = Users.get_by_id(user_id)
        user.delete_instance()
        return {'message': 'User deleted successfully'}
    except Users.DoesNotExist:
        return {'error': 'User with that id not found'}
    


#Create a new lab
@app.route("/api/create_lab", methods=['GET', 'POST'])
def create_lab():
    #Get the lab name from the form
    lab_name = request.form.get('lab_name')

    #Generate a random invite code
    invite_code_ = ''.join(random.choices(string.ascii_uppercase, k=5))

    #Make sure the invite code is unique
    existing_lab = Labs.select().where(Labs.invite_code == invite_code_).first()
    while existing_lab is not None :
        invite_code_ = ''.join(random.choices(string.ascii_uppercase, k=5))
        existing_lab = Labs.select().where(Labs.invite_code == invite_code_).first()

    if not lab_name:
        return {'error': 'Invalid lab name'}, 400

    #Get the user ID from the session
    user_id_ = session['user_id']

    try:
        user = Users.get(Users.user_id == user_id_)
    except Users.DoesNotExist:
        return {'error:' 'Invalid User'}, 400
    
    #Create the lab and add the user as an admin
    lab = Labs.create(lab_name = lab_name, invite_code = invite_code_)
    Lab_Permissions.create(user_id = int(user_id_), lab_id = lab.lab_id, lab_admin = True)

    #Update the session variables
    session['labs'] = getUserLabs()
    

    if (request.form.get('returnTo') == "labPage") :
        return redirect(url_for("labsPage"))
    else:
        return redirect(url_for('homepage'))
    

#Join a lab with an invite code   
@app.route('/api/join_lab', methods=['POST'])
def join_lab():
    #Get the invite code from the form
    invite_code = request.form.get('invite_code')

    #Get the lab with the invite code
    lab = Labs.select().where(Labs.invite_code == invite_code).first()

    #If the lab exists, add the user to the lab
    if lab :
        new_lab, created = Lab_Permissions.get_or_create(user_id = session["user_id"], lab_id = lab.lab_id, lab_admin = False)

    #Add new labs and groups to the session
    session['labs'] = getUserLabs()
    session['groups'] = getUserGroups()
    

    return redirect(url_for('labsPage'))


#Delete a lab
@app.route('/api/deleteLab', methods=['POST'])
def delete_lab():

    lab_id_ = request.form['action']

    QRs.delete().where(QRs.group_id << Groups.select(Groups.group_id).where(Groups.lab_id == lab_id_)).execute()

    # Delete rows from the Groups table
    Groups.delete().where(Groups.lab_id == lab_id_).execute()

    # Delete rows from the Lab_Permissions table
    Lab_Permissions.delete().where(Lab_Permissions.lab_id == lab_id_).execute()

    # Delete row from the Labs table
    Labs.delete().where(Labs.lab_id == lab_id_).execute()

    session['labs'] = getUserLabs()

    return redirect(url_for("labsPage"))


#Leave a lab
@app.route('/api/leaveLab', methods=['POST'])
def leave_lab(): 

    lab_id_ = request.form['action']

    query = Lab_Permissions.delete().where((Lab_Permissions.lab_id == lab_id_) & (Lab_Permissions.user_id == session["user_id"]))
    query.execute()

    session['labs'] = getUserLabs()
    session['groups'] = getUserGroups()

    return redirect(url_for('labsPage'))


#Delete group
@app.route('/api/deleteGroup', methods=['POST'])
def delete_group():

    group_id_ = request.form['action']

    QRs.delete().where(QRs.group_id << Groups.select(Groups.group_id).where(Groups.group_id == group_id_)).execute()

    # Delete rows from the Groups table
    Groups.delete().where(Groups.group_id == group_id_).execute()

    session['labs'] = getUserLabs()
    session["groups"] = getUserGroups()

    return redirect(url_for("labsPage"))


#Create a group
@app.route("/api/create_group", methods=['GET', 'POST'])
def create_group():

    #Get group name and lab ID from the form
    group_name = request.form.get('group_name')
    lab_id = request.form.get('lab_id')

    if not group_name:
        return {'error': 'Invalid group name'}, 400

    #Create the group
    group = Groups.create(lab_id = lab_id, group_name = group_name)

    userinfo = {
        "email": session.get('email'),
        "user_id": session.get('user_id'),
        "lab_id": session.get('lab_id'),
        "group_id": group.group_id
    }

    session["groups"] = getUserGroups()

    if (request.form.get('returnTo') == "labPage") :
        return redirect(url_for("labsPage"))
    else:
        return redirect(url_for('homepage'))


#Get all non admin lab members for a lab
def getLabMembers():
    
    #Get all labs the user is an admin of
    query = (Lab_Permissions.select(Lab_Permissions.lab_id).where((Lab_Permissions.user_id == session['user_id']) & (Lab_Permissions.lab_admin == True))).execute()
    user_labs = [lab.lab_id for lab in query]


    #Get all non admin lab members for the labs the user is an admin of
    query = (Lab_Permissions.select(Lab_Permissions.user_id, Lab_Permissions.lab_id).where((Lab_Permissions.lab_id.in_(user_labs)) & (Lab_Permissions.lab_admin == False))).execute()

    #Create a dictionary of lab members based on lab ID
    user_data = defaultdict(list)
    for entry in query: 
        query = Users.select(Users.email).where(Users.user_id == entry.user_id).execute()
        email = [user.email for user in query]
        user_data[str(entry.lab_id)].append([str(entry.user_id), str(email[0])])

   

    return user_data

#Remove a lab member from a lab
@app.route('/api/removeLabMember', methods=['POST'])
def removeLabMember():
    lab_id = request.form['lab_id']
    user_id = request.form['action']

    query = Lab_Permissions.delete().where((Lab_Permissions.lab_id == lab_id) & (Lab_Permissions.user_id == user_id))
    query.execute()

    session['labMembers'] = getLabMembers()

    return redirect(url_for('labsPage'))
    



#QR CODE GENERATION

@app.route("/generate_qrs")
def render_generate_qrs():
    return render_template('qr_generate.html')

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

    qr_width = 32

    qr_codes = []  # List to store QR code PIL images

    # Loop to generate QR codes
    for i in range(get_highest_qr_id(), number_of_codes + get_highest_qr_id()):

        qr = segno.make(str(i), micro=True)
        QRs.create(qr_id=str(i))
        img = qr.to_pil(scale=qr_size)
        qr_codes.append(img)

    rows = int((number_of_codes - 1) / 6) + 1
    cols = min(number_of_codes, 6)

    total_width = max(816, int(qr_size * qr_width + border_size/2) * cols + qr_width)
    total_height = max(1056, int(qr_size * qr_width + border_size) * rows + qr_width)

    # Create a new image with a white background
    combined_image = Image.new('RGB', (total_width, total_height), color='white')


    for i, qr_code_img in enumerate(qr_codes):
        row = int(i / cols)
        col = i % cols

        x_offset = col * (qr_size * qr_width + border_size) + qr_width
        y_offset = row * (qr_size * qr_width + border_size) + qr_width

        combined_image.paste(qr_code_img, (x_offset, y_offset))

    # Save the combined image as PDF
    file_name = 'qr.pdf'
    combined_image.save('static/' + file_name, 'PDF', resolution=100.0)

    return render_template('qr_generate.html', file_name=file_name)

# ==========================================================================
if __name__ == "__main__":
    app.run(debug=True)
