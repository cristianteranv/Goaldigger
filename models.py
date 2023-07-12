from datetime import datetime
import flask_sqlalchemy
from app import db
from enum import Enum

#When someone logs in, check which auth method they used. If they used google, then check google_id to see if they had created an account. 
#If there aren't any users with that google_id, create one. Same for facebook auth.

#queries

#single table
#models.Users.query.filter_by(name="jokebot").first()
#models.TABLENAME.query.filter_by(COLUMN = "VALUE YOU WANT").first() OR .all() depending if you want the first row or all of the rows

#Join tables         TABLES YOU WANT
#db.session.query(models.Texts, models.Users)\
#.filter(models.Texts.user == models.Users.id)\
#.order_by(models.Texts.date)\
#.all()   OR .first()   depends on what you want again

#when using the python shell to create the tables, call createDummyData() to input rows into the tables after creating the tables.
#from command line: `python`, `import models`, `from app import db`, `db.create_all()`, `db.session.commit()`, `createDummyData()`, `exit()`
'''
def createDummyData():
    db.session.add(Users("johanna@google.com", "Johanna", "imgurl", "false", "I like coding"))
    db.session.add(Users("cristian@google.com", "Cristian", "imgurl", "false", "I like gaming"))
    db.session.add(Users("digna@google.com", "Digna", "imgurl", "false", "I like stuff"))
    db.session.add(Users("joey@google.com", "Joey", "imgurl", "false", "I like things"))
    db.session.commit()
    db.session.add(Goals(1, "Exercise", "I want to deadlift 250 pounds", "Started", "Really happy to start this new goal!"))
    db.session.add(Goals(1, "Exercise", "I want to deadlift 250 pounds", "Completed", "Really happy to have achieved my goal!"))
    db.session.add(Goals(2, "Work", "I want to solve 2 hard leetcodes a day", "Started", "I can do this!"))
    db.session.commit()

def createDummyData2():
    db.session.add(Groups("Exercise", "We like to train our legs", "Turkey Legs", "Please see our routines at www.routines.com!"))
    db.session.add(Groups("Work", "Group for CS490 students", "GoalDigger", "Four students join forces to create a goal oriented social app"))
    db.session.commit()
    #########     MAKE SURE THIS EMAIL EXISTS IN YOUR TABLES, ELSE CHANGE THE NAME TO ONE THAT EXISTS     ##########
    db.session.add(GroupsUsers( Users.query.filter_by(email="johanna@google.com").first().id, 1))
    db.session.add(GroupsUsers( Users.query.filter_by(email="johanna@google.com").first().id, 2))
    db.session.add(GroupsUsers( Users.query.filter_by(email="joey@google.com").first().id, 2))
    db.session.add(GroupsUsers( Users.query.filter_by(email="cristianteranv@gmail.com").first().id, 2))
    db.session.add(GroupsUsers( Users.query.filter_by(email="cdt34@njit.edu").first().id, 2))
    db.session.commit()
'''
class Userss(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    name = db.Column(db.String(50), nullable=False)
    img_url = db.Column(db.String())
    signed_in = db.Column(db.String(5))
    google_id = db.Column(db.String(3000))
    # fb_id = db.Column(db.String())
    # bio = db.Column(db.String())

    def __init__(self, email, name, img_url, signed_in, google_id):
        self.name = name
        self.email = email
        self.img_url = img_url
        self.signed_in = signed_in
        self.google_id = google_id

class Goals(db.Model):
    '''Table for goals'''
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String())
    user_id = db.Column(db.Integer, db.ForeignKey('userss.id'))
    description = db.Column(db.String())
    progress = db.Column(db.String())
    date = db.Column(db.DateTime, default=datetime.now)
    post_text = db.Column(db.String())
    
    hearts = db.Column(db.String())
    smileys = db.Column(db.String())
    thumbs = db.Column(db.String())
    
    def __init__(self, user_id, category, description, progress, post_text, heart, smile, thumb):
        self.user_id = user_id
        self.category = category
        self.description = description
        self.progress = progress
        self.post_text = post_text
        
        self.hearts = heart
        self.smileys = smile
        self.thumbs = thumb
        
        
class Groups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String())
    name = db.Column(db.String())
    description = db.Column(db.String())
    sidebar_text = db.Column(db.String())
    created = db.Column(db.DateTime, default=datetime.now)
    
    def __init__(self, category, name, description, sidebar_text):
        self.category = category
        self.name = name
        self.description = description
        self.sidebar_text = sidebar_text
        
class GroupsUserss(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('userss.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    
    def __init__(self, user_id, group_id):
        self.user_id = user_id
        self.group_id = group_id


# class Posts(db.Model):
#     '''Table for user posts'''
#     id = db.Column(db.Integer, primary_key=True)
#     category = db.Column(db.String())
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#     title = db.Column(db.String())
#     text = db.Column(db.String())
#     date = db.Column(db.DateTime, default=datetime.now)
    
#     def __init__(self, user_id, category, title, text):
#         self.user_id = user_id
#         self.category = category
#         self.title = title
#         self.text = text

class Messages(db.Model):
    '''Table for chat messages.'''
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String())
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('userss.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))

    def __init__(self, text, user_id, group_id):
        self.text = text
        self.user_id = user_id
        self.group_id = group_id

    def __repr__(self):
        return "<Text: {}\nBy: {}>\n".format(self.text, self.user)


# Maybe this Enum is unnecesary.
# class Progress(Enum):
#     IN_PROGRESS = "in progress"
#     FINISHED = "completed"

# class Categories(Enum):
#     WORK = "work"
#     EXERCISE = "exercise"
#     ...
