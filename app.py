import os
from os.path import join, dirname
import flask
from flask import Flask, render_template
import flask_socketio
import flask_sqlalchemy
from dotenv import load_dotenv
import requests
from flask import request
from datetime import datetime

#MAYBE WE DON'T NEED THESE TWO LINES.
from engineio.payload import Payload
Payload.max_decode_packets = 50



app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
server_socket = flask_socketio.SocketIO(app)
server_socket.init_app(app, cors_allowed_origins="*")

dotenv_path = join(dirname(__file__), "sql.env")
load_dotenv(dotenv_path)
database_uri = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

db = flask_sqlalchemy.SQLAlchemy(app)
db.init_app(app)
db.app = app

import models

db.create_all()
db.session.commit()




EMIT_NEWSFEED_CHANNEL = "Home"
GOOGLE_INFO_RECEIVED_CHANNEL = "google info received"
GROUP_PAGE_REQUEST = "group feed"

def emit_newsfeed(channel, sid):
    all_goals = [
        {
            "user_id": db_users.id,
            "username": db_users.name,
            "img_url": db_users.img_url,
            "category": db_goals.category,
            "description": db_goals.description,
            "progress": db_goals.progress,
            "post_text": db_goals.post_text,
            "hearts": db_goals.hearts,
            "smileys": db_goals.smileys,
            "thumbs": db_goals.thumbs

        }
        for db_users, db_goals in\
        db.session.query(models.Userss, models.Goals)\
        .filter(models.Userss.id == models.Goals.user_id)\
        .order_by(models.Goals.date).all()
    ]
    print("running emit_newsfeed")
    server_socket.emit(channel, all_goals, sid)




def emit_group_feed(channel, groupName, sid):
    groupObject = models.Groups.query.filter_by(name=groupName).first()
    if groupObject:
        group_info = {
            "group_description": groupObject.description,
            "sidebar_text": groupObject.sidebar_text,
            "name": groupObject.name,
            "groupId": groupObject.id
        }
        print("in group feed",group_info["name"])
        group_goals = [
            {
                "description": db_goals.description,
                "progress": db_goals.progress,
                "username": db_users.name,
                "img_url": db_users.img_url,
                "category": db_goals.category,
                "post_text": db_goals.post_text,
                "hearts": db_goals.hearts,
                "smileys": db_goals.smileys,
                "thumbs": db_goals.thumbs
            }
            for db_users, db_goals, db_groups_users in\
            db.session.query(models.Userss, models.Goals, models.GroupsUserss)\
            .filter(models.GroupsUserss.group_id == groupObject.id)\
            .filter(models.Userss.id == models.GroupsUserss.user_id)\
            .filter(models.Goals.user_id == models.GroupsUserss.user_id)\
            .order_by(models.Goals.date).all()
        ]
        
        group_messages = [
            {
                "message": db_messages.text,
                "userId": db_messages.user_id
            }
            for db_messages in\
            models.Messages.query\
            .filter_by(group_id = groupObject.id)\
            .order_by(models.Messages.date).all()
        ]
        server_socket.emit(channel, {"group_info": group_info, "group_goals": group_goals, "group_messages": group_messages} , sid)
    else:
        server_socket.emit(channel, None , sid)


def emit_category(channel, sid):
    category_goals = [
        {
            "user_id": db_users.id,
            "username": db_users.name,
            "img_url": db_users.img_url,
            "category": db_goals.category,
            "description": db_goals.description,
            "progress": db_goals.progress,
            "post_text": db_goals.post_text,
            "hearts": db_goals.hearts,
            "smileys": db_goals.smileys,
            "thumbs": db_goals.thumbs
        }
        for db_users, db_goals in\
        db.session.query(models.Userss, models.Goals)\
        .filter(models.Userss.id == models.Goals.user_id)\
        .filter(models.Goals.category == channel)\
        .order_by(models.Goals.date).all()
    ]

    server_socket.emit(channel, category_goals, sid)



def push_new_user_to_db(email, username, image, is_signed_in, id_token):
    db.session.add(models.Userss(email, username, image, is_signed_in, id_token));
    db.session.commit();



@server_socket.on('group page')
def send_group_info(data):
    print(data["groupName"])
    emit_group_feed(GROUP_PAGE_REQUEST, data["groupName"], request.sid)
    
    
@server_socket.on("newUserMessage")
def handle_message(data):
    db.session.add(models.Messages(data['newUserMessage'], data['userId'], data['groupId']))
    db.session.commit()
    server_socket.emit("broadcast", {"newMessage": data['newUserMessage'], "groupName": "another group"}, broadcast=True, include_self=False)


@server_socket.on('new google user')
def on_new_google_user(data):
    user = db.session.query(models.Userss).filter_by(email=data["email"]).first()

    if (not user):
        push_new_user_to_db(data['email'], data['username'], data['image'], "Null", data['id_token'])

    user = db.session.query(models.Userss).filter_by(email=data["email"]).first()

    personal_profile = {
        "username": data["username"],
        "image": data["image"],
        "primary_id": user.id
    }

    personal_goals = [
        {
            "description": personal_goal.description,
            "progress": personal_goal.progress
        }
        for personal_goal in models.Goals.query.filter(models.Goals.user_id == user.id).all()
    ]
    ########################################
    ######   EMIT USER'S GROUPS      #######
    ########################################
    user_groups_names=[
        db_groups.name
        for db_groups, db_groups_users in\
        db.session.query(models.Groups, models.GroupsUserss)\
        .filter(models.GroupsUserss.user_id == user.id)\
        .filter(models.GroupsUserss.group_id == models.Groups.id)\
        .order_by(models.Groups.name).all()
    ]
    print("Groups the user belongs to",user_groups_names)
    user_groups_id= [ row.group_id for row in models.GroupsUserss.query.filter(models.GroupsUserss.user_id == user.id).all() ]

    user_groups_goals = [
        {
            "user_id": db_user_id,
            "username": db_users.name,
            "img_url": db_users.img_url,
            "category": db_goals.category,
            "description": db_goals.description,
            "progress": db_goals.progress,
            "post_text": db_goals.post_text
        }
        for db_user_id, db_goals, db_users in\
        db.session.query(models.GroupsUserss.user_id.distinct(), models.Goals, models.Userss)\
        .filter(models.GroupsUserss.group_id.in_(user_groups_id))\
        .join(models.Goals, models.GroupsUserss.user_id == models.Goals.user_id)\
        .join(models.Userss, models.Userss.id == models.GroupsUserss.user_id)\
        .order_by(models.Goals.date.desc()).all()
    ]
    server_socket.emit("user groups", {"user_groups_names": user_groups_names, "user_groups_goals": user_groups_goals}, request.sid)
    server_socket.emit("google info received", personal_profile, request.sid)
    server_socket.emit("user goals", personal_goals, request.sid)



@server_socket.on('add_goal')
def add_goal(data):
    print("TEST DATA: ", data)

    category = data["category"]
    user_id = data["user"]["primary_id"]
    description = data["goal"]
    progress = "Incomplete" #data["progress"]
    post_text = data["postText"]
    
    hearts = "0"
    smileys = "0"
    thumbs = "0"
    
    
    #server_socket.emit("add_goal", data, request.sid)

    db.session.add(models.Goals(user_id, category, description, progress, post_text, hearts, smileys, thumbs))
    db.session.commit()

@server_socket.on('add_group')
def add_group(data):
    print("Received new group info from the client: ", data["groupCategory"], data["groupName"], data["groupDescription"], data["groupSidebarText"])
    groupCategory = data["groupCategory"]
    groupName = data["groupName"]
    groupDescription = data["groupDescription"]
    groupSidebarText = data["groupSidebarText"]
    server_socket.emit("add_group", data)
    db.session.add(models.Groups(groupCategory, groupName, groupDescription, groupSidebarText))
    db.session.commit()
    

def emit_group_names(channel):
    all_group_names = [{
        "groupName": group.name,
    } for group in db.session.query(models.Groups).all()]
    
    server_socket.emit(channel, { "all_group_names" : all_group_names }, request.sid)

@server_socket.on('new complete input')
def on_new_complete(data):
    ''' gets user input '''
    print("Got an event for completion with data:", data)
    
    completion = data["completion"]
    queue = db.session.query(models.Goals).filter(models.Goals.description==completion).first();
    queue.progress="Complete"
    db.session.commit();
    
    emit_newsfeed(EMIT_NEWSFEED_CHANNEL, request.sid)
    
    
@server_socket.on('new delete input')
def on_new_delete(data):
    ''' gets user input '''
    print("Got an event for deletion with data:", data)
    
    deletion = data["deletion"]
    queue = db.session.query(models.Goals).filter(models.Goals.description==deletion).first();
    db.session.delete(queue);
    db.session.commit();
    
    emit_newsfeed(EMIT_NEWSFEED_CHANNEL, request.sid)
   
  
@server_socket.on('new hearts input')
def on_new_heart(data):
    ''' gets user input '''
    print("Got an event for heart with data:", data)
    
    heart = data["heart"]
    queue = db.session.query(models.Goals).filter(models.Goals.description==heart).first();
    x = queue.hearts
    y=int(x)
    z=y+1
    queue.hearts = z
    db.session.commit();
    
    emit_newsfeed(EMIT_NEWSFEED_CHANNEL, request.sid)
    

@server_socket.on('new smileys input')
def on_new_smiley(data):
    ''' gets user input '''
    print("Got an event for smiley with data:", data)
    
    smiley = data["smiley"]
    queue = db.session.query(models.Goals).filter(models.Goals.description==smiley).first();
    x = queue.smileys
    y=int(x)
    z=y+1
    queue.smileys = z
    db.session.commit();
    
    emit_newsfeed(EMIT_NEWSFEED_CHANNEL, request.sid)
    
@server_socket.on('new thumbs input')
def on_new_thumb(data):
    ''' gets user input '''
    print("Got an event for thumb with data:", data)
    
    thumb = data["thumb"]
    queue = db.session.query(models.Goals).filter(models.Goals.description==thumb).first();
    x = queue.thumbs
    y=int(x)
    z=y+1
    queue.thumbs = z
    db.session.commit();

    emit_newsfeed(EMIT_NEWSFEED_CHANNEL, request.sid)

def emit_google_info(channel):
    all_users = [{
        "username": user.name,
        "img_url": user.img_url,
        "user_id": user.id
        } for user in db.session.query(models.Userss).all()]

    server_socket.emit(channel, {
        'allusers' : all_users
    })

@server_socket.on("join")
def join(data):
    print(data)
    row = db.session.query(models.GroupsUserss)\
    .filter(models.GroupsUserss.group_id == data["groupId"], models.GroupsUserss.user_id == data["userId"]).first()
    print("row",row)
    if not row:
        db.session.add(models.GroupsUserss(data["userId"], data["groupId"]))
        db.session.commit()

@server_socket.on("get_data")
def on_data(category):
    if category == "Home":
        emit_newsfeed(EMIT_NEWSFEED_CHANNEL, request.sid)
    else:
        emit_category(category, request.sid)
    


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")

@app.route('/groups/<path:filename>')
def send_img(filename):
    if filename[-4:] == ".png":
        try:
            return flask.send_from_directory('./', filename)
        except:
            return "File not found", 404
    return render_template("index.html")
    

@app.errorhandler(404)
def page_not_found(_e):
    return render_template("index.html")


if __name__ == "__main__":
    server_socket.run(
        app,
        host=os.getenv("IP", "0.0.0.0"),
        port=int(os.getenv("PORT", 8080)),
        debug=True,
    )