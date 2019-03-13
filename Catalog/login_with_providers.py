from flask import request, url_for, jsonify

from models import Base, User

from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from flask import session as login_session
from flask import make_response

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import requests
import json

engine = create_engine(
    'sqlite:///catalogItems.db',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool, echo=True
    )

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
FB_APP_ID = json.loads(
    open('fb_client_secrets.json', 'r').read())['web']['app_id']

APPLICATION_NAME = "Catalog Item Application"


"""
Google Provider

"""


def login_with_google():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
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
        return response

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
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                    json.dumps('Current user is already connected.'),
                    200
                    )
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = "google_"+data['id']
    login_session['name'] = data['name']
    login_session['email'] = data['email']
    login_session['picture'] = data['picture']
    login_session['provider'] = "google"
    login_session['provider_id'] = data['id']

    # for key, value in data.items():
    #     print(key, value)

    login_session['user_id'] = getUserID(login_session['provider_id'],
                                         login_session['provider'])

    if login_session['user_id'] is None:
        login_session['user_id'] = createUser(login_session)

    response = make_response(json.dumps('OK'),
                             200)
    response.headers['Content-Type'] = 'application/json'
    return response


def logout_from_google():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400)
            )
        response.headers['Content-Type'] = 'application/json'
    return response


"""
Facebook Provider

"""


def login_with_facebook():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print("access token received {%s} " % str(access_token))

    app_id = FB_APP_ID
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token.decode("utf-8"))
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # token = result.split(',')[0].split(':')[1].replace('"', '')
    token = result['access_token']
    # Use token to get user info from API
    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email,picture{url}' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)
    for key, value in data.items():
        print(key, value)
    login_session['username'] = "facebbok_"+data['id']
    login_session['name'] = data["name"]
    login_session['email'] = data["email"]
    login_session['provider'] = 'facebook'
    login_session['provider_id'] = data["id"]
    login_session['picture'] = data['picture']["data"]["url"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # see if user exists
    login_session['user_id'] = getUserID(login_session['provider_id'],
                                         login_session['provider'])

    if login_session['user_id'] is None:
        login_session['user_id'] = createUser(login_session)

    response = make_response(json.dumps('OK'),
                             200)
    response.headers['Content-Type'] = 'application/json'
    return response


def logout_from_facebook():
    facebook_id = login_session['provider_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    print("you have been logged out")
    response = make_response(json.dumps('Successfully disconnected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


def getUserID(provider_id, provider):
    try:
        user = session.query(User).filter_by(provider_id=provider_id,
                                             provider=provider).one()
        return user.id
    except Exception:
        return None


def createUser(login_session):
    newUser = User(username=login_session['username'],
                   name=login_session['name'],
                   email=login_session['email'],
                   picture=login_session['picture'],
                   provider_id=login_session['provider_id'],
                   provider=login_session['provider'])
    session.add(newUser)
    session.commit()
    return getUserID(login_session['provider_id'], login_session['provider'])
