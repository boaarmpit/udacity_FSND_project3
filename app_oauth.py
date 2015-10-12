import random
import string
import httplib2
import json
import requests
from flask import Blueprint, render_template, request, redirect, flash, \
    make_response
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError, \
    OAuth2Credentials

from database_setup import Base, User

oauth_api = Blueprint('oauth_api', __name__)

CLIENT_ID = json.loads(
    open('private/google_client_secret.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def create_user(login_session):
    new_user = User(name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def validate_token(token):
    if token != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        return


# Test state DEBUGGING ONLY
@oauth_api.route('/test')
def test():
    print "Anti Forgery State Token: ", login_session['state']
    credentials = OAuth2Credentials.from_json(login_session['credentials'])
    access_token = credentials.access_token
    print "Google Access Token:", access_token
    return ""


# Clear session DEBUGGING ONLY
@oauth_api.route('/clear_session')
def clear_session():
    login_session.clear()
    return "Session cleared"


# Create a state token to prevent request forgery.
# Store it in the session for later validation.
@oauth_api.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for _ in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@oauth_api.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token (Anti Forgery State Token)
    invalid_response = validate_token(request.args.get('state'))
    if invalid_response:
        return invalid_response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            'private/google_client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists and if it doesnt, make a new one
    user_id = get_user_id(data['email'])
    if not user_id:
        user_id = create_user(login_session)
        print "created user with id", user_id
    else:
        print "user with id", user_id, "already registered"
    login_session['user_id'] = user_id
    print "user with id", user_id, "logged in"

    output = ''
    output += '<h2>Welcome, '
    output += login_session['username']
    output += '!</h2>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "user %s successfully connected!" % data['name']
    return output


# DISCONNECT - Revoke a current user's token and reset their login session.
def gdisconnect():
    # Only disconnect a connected user.
    try:
        credentials = OAuth2Credentials.from_json(login_session['credentials'])
    except:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    print access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        name = login_session['username']
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']

        response = make_response(
            json.dumps('Successfully disconnected (gmail).'), 200)
        response.headers['Content-Type'] = 'application/json'
        print "user %s successfully disconnected!" % name
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user (gmail).', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@oauth_api.route('/fbconnect', methods=['POST'])
def fbconnect():
    # Validate state token (Anti Forgery State Token)
    invalid_response = validate_token(request.args.get('state'))
    if invalid_response:
        return invalid_response

    access_token = request.data
    print "access token received %s " % access_token

    app_id = \
        json.loads(open('private/fb_client_secrets.json', 'r').read())['web'][
            'app_id']
    app_secret = \
        json.loads(open('private/fb_client_secrets.json', 'r').read())['web'][
            'app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?' \
          'grant_type=fb_exchange_token&client_id=%s&client_secret=%s&' \
          'fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # print "app secret",app_secret
    # print "result", result

    # Use token to get user info from API
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print "url sent for API access:%s" % url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    # let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?' \
          '%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    print "url", url
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    print "result", result
    # name = login_session['username']
    del login_session['facebook_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    return "you have been logged out (from facebook oauth)"


@oauth_api.route('/disconnect')
def disconnect():
    # Validate state token (Anti Forgery State Token)
    invalid_response = validate_token(request.args.get('state'))
    if invalid_response:
        return invalid_response

    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['provider']
            flash("you have successfully logged out (from google oauth)")
        elif login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['provider']
            flash("you have successfully logged out (from facebook oauth)")
        else:
            flash("logged in with unknown provider")
    else:
        flash("you were not logged in to begin with")
    return redirect('/')
