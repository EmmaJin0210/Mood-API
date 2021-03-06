"""
Small backend REST API that:
1. Allows both authenticated and anonymous users to POST mood values
2. Returns latest mood value and streak to authenticated users
--------------------------------------------------------------------------------
Emma Jin
03/17/2021
"""
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from http import cookies
import datetime

############################### INITIALIZATION #################################
app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth() # Performs a basic check for credentials (username + pwd)

C = cookies.SimpleCookie() # Cookie used to store current user

parser = reqparse.RequestParser()
parser.add_argument("mood", type=int, help="Rate your mood on scale 1-10")

################################### DATA #######################################
# Dictionary to store credentials for valid users and their streak
USER_DATA = {
    "admin":{"pwd":"SecretPassword", "latest":None, "streak":0},
    "Emma":{"pwd":"SecretPassword2", "latest":None, "streak":0}
}
# Dictionary to store the lasted mood value POSTed
# Using separate dictionary to let anonymous user (not logged in) post as well
moods = {"mood": None}

############################### AUTHENTICATION #################################
@auth.verify_password
def verify(username, password):
    if "current_user" not in C: # If no one has logged in/ POSTed yet
        result = login_user(username, password) # Check user credentials
    else: # If someone has already logged in or POSTed
        # If username is blank this time, whoever logged in last stays logged in
        if not username:
            return True
        # If username is not in our user data
        elif username not in USER_DATA:
            return "User does not exist", 404
        # If username is different from current logged in user, log in new user
        elif username != C["current_user"].value:
            result = login_user(username, password)
        # If username is the same as current logged in user, stay as that user
        else: # if username == C['current_user'].value
            return True
    if result == False:
        return "Wrong credentials!", 401
    else:
        return True # authentication success

def login_user(username, password):
    if not (username and password): # If empty username/password, stay anonymous
        C["current_user"] = "anonymous"
        return True
    if USER_DATA[username]["pwd"] == password: # If password matches data
        C["current_user"] = username # Update current_user
        return True
    else: # If entered both username and pwd, but didn't match data
        return False

################################# API: MOOD ####################################
class Mood(Resource):

    def get(self):
        """
        If anonymous user (not logged in): return "User not logged in" message
        If logged in user: return POSTed latest mood value and streak
        """
        if "current_user" in C:
            user = C["current_user"].value # get current user from cookie
            if user != "anonymous":
                # Need to check streak again, so if user had not POSTED the day
                # before, the streak is set to 0 and we return up-to-date info
                update_streak(user)
                return {"GET value": moods["mood"], "streak":USER_DATA[user]["streak"]}
            else:
                return "User not logged in", 403
        else:
            return "There is no POSTed value to return", 404

    @auth.login_required
    def post(self):
        """
        If anonymous user: return POSTed lastest mood value
        If logged in user: return POSTed latest mood value and update streak
        """
        args = parser.parse_args()
        moods["mood"] = args["mood"]

        if "current_user" in C:
            user = C["current_user"].value
            if user != "anonymous":
                update_streak(user)
        print(USER_DATA) # check if corresponding streak is updated
        return {"POSTed value": moods["mood"]}, 201

api.add_resource(Mood, "/mood") # Add the resouce to API, endpoint = '/mood'

############################## HELPER FUNCTIONS ################################
# These are helper funtions to update the streak of logged in users
def update_streak(user):
    """
    Updates the streak of a logged in user
    --------------------------------------
    Params: user (type str), the current logged_in user
    """
    current = datetime.date.today()
    latest = USER_DATA[user]["latest"]
    if current != latest: # if requests not on the same day, check
        if check_streak(current, latest): # if two consecutive days
            USER_DATA[user]["streak"] += 1
        else: # if not two consecutive days, reset streak
            USER_DATA[user]["streak"] = 0
    USER_DATA[user]["latest"] = datetime.date.today()

def check_streak(current, latest):
    """
    Check whether we should append user streak or reset user streak
    ---------------------------------------------------------------
    Params: current (datetime.date object), current time
            latest (datetime.date object), time of last POST stored
    returns: True if we should append streak by 1,
             False if we should reset streak to 0
    """
    if latest == None: # if this is 1st POST, then streak will be 1
        return True
    d = datetime.timedelta(days=1)
    if current == latest + d: # if two consecutive days
        return True
    else: # if not two consecutive days
        return False

################################################################################
if __name__ == "__main__":
    app.run(debug=True)
