from models import Base, User, Category, Item, secret_key
from flask import render_template, Flask, flash, request, url_for, jsonify
from flask import abort, redirect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine, exc

# from flask_httpauth import HTTPBasicAuth
# auth = HTTPBasicAuth()
from flask import session as login_session
from pickle import dump
import json
import random
import string


from login_with_providers import CLIENT_ID, login_with_google, logout_from_google
from login_with_providers import FB_APP_ID, login_with_facebook, logout_from_facebook


engine = create_engine(
    'sqlite:///catalogItems.db',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool, echo=True
    )

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


@app.route('/login/', methods=['POST', 'GET'])
@app.route('/login/<string:provider>/', methods=['POST', 'GET'])
def login(provider=None):
    if request.method == 'POST':
        if provider is None:
            if request.form.get('state') != login_session['state']:
                message = "Invalid state parameter."
                flash(message)
                return redirect(url_for('login'))

            username = request.form.get('username')
            password = request.form.get('password')
            user = session.query(User).filter_by(username=username).first()
            if not user or not user.verify_password(password):
                message = "Username and/or password incorrect"
                print(message)
                flash(message)
                return redirect(url_for('login'))
            login_session['user_id'] = user.id
            login_session['name'] = user.name
            login_session['username'] = user.username
            return redirect(url_for('index'))
        if provider == 'google':
            return login_with_google()
        if provider == 'facebook':
            return login_with_facebook()
    if request.method == "GET":
        if "username" in login_session:
            return redirect(url_for('index'))

        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in range(32))
        login_session['state'] = state
        return render_template('login.html',
                               STATE=state,
                               FB_APP_ID=FB_APP_ID,
                               Google_CLIENT_ID=CLIENT_ID)


@app.route('/logout/')
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            logout_from_google()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            logout_from_facebook()
            del login_session['access_token']

    login_session.pop('user_id', None)
    login_session.pop('username', None)
    login_session.pop('name', None)
    login_session.pop('email', None)
    login_session.pop('picture', None)
    login_session.pop('provider', None)
    login_session.pop('provider_id', None)

    return redirect(url_for('index'))


@app.route('/catalog.json')
def catalogJSON():
    categories = session.query(Category).outerjoin(Item).all()
    # return jsonify(Catalog=[r.serialize for r in categories])
    return jsonify(Catalog=[dict(c.serialize, items=[i.serialize
                            for i in c.items])
                            for c in categories])


@app.route('/')
def index():
    categories = session.query(Category).all()
    # I should implement the pagination later
    # for the instance i display all the items in one page
    latest_items = session.query(Item).order_by("id desc").all()
    """
    Instead of using this code to get the information for the user actif
    I just store the information I need in the session

    user_actif = None
    if "username" in login_session:
        user_actif = session.query(User).filter_by(
                     username= login_session.get('username')
                    ).first()
    """
    return render_template('index.html',
                           categories=categories,
                           items=latest_items)


@app.route('/category/<int:cat_id>/')
def itemsByCategory(cat_id):
    categories = session.query(Category).all()
    current_categorie = session.query(Category).filter_by(id=cat_id).first()
    # I should implement the pagination later
    # for the instance i display all the items in one page
    latest_items = session.query(Item).filter_by(
                   cat_id=cat_id).order_by("id desc").all()
    return render_template('index.html', categories=categories,
                           current_categorie=current_categorie,
                           items=latest_items)


@app.route('/users/', methods=['POST'])
def newUser():
    if request.form.get('state') != login_session['state']:
        message = "Invalid state parameter."
        flash(message)
        return redirect(url_for('login'))
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')
    if username is None or password is None:
        print("missing arguments")
        abort(400)
    if session.query(User).filter_by(username=username).first() is None:
        user = User(username=username, name=name)
        user.hash_password(password)
        session.add(user)
        session.commit()
        message = "User added successfully."
        flash(message)
        return redirect(url_for('index'))

    else:
        message = "Usernam already taken"
        flash(message)
        print(message)
        return redirect(url_for('login'))


@app.route('/new-item/', methods=['GET', 'POST'])
def newItem():
    # The user can only add an item if he logged in
    if "username" not in login_session:
            return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category')
        user_id = int(login_session.get('user_id'))
        # title, description and category_id must not be empty
        if not title or not description or not category_id:
            message = "Please, Enter all the fields"
            flash(message)
            return redirect(url_for('newItem'))
        item = Item(title=title, description=description,
                    cat_id=category_id, user_id=user_id
                    )
        session.add(item)
        try:
            session.commit()
            message = "added successfully"
            flash(message)
        except exc.SQLAlchemyError as e:
            print(str(e))
            message = "Unable to save changes"
            flash(message)
        return redirect(url_for('newItem'))

    if request.method == 'GET':
        categories = session.query(Category).all()
        return render_template('ajoute.html', categories=categories)


@app.route('/item/<int:id>')
def itemView(id):
    try:
        item = session.query(Item).filter_by(id=id).first()
    except exc.SQLAlchemyError as e:
        abort(404)

    return render_template('detail.html', item=item)


@app.route('/item/edit/<int:id>', methods=['GET', 'POST'])
def itemUpdate(id):
    try:
        item = session.query(Item).filter_by(id=id).first()
    except exc.SQLAlchemyError as e:
        # if the item doesn't exist return Not found
        abort(404)

    if "username" not in login_session:
            return redirect(url_for('login'))

    if not item.user or item.user.id != int(login_session.get('user_id')):
        # if the current user doesn't match the user who create
        # the item return Unauthorized
        abort(401)

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category')
        # title, description and category_id must not be empty
        if not title or not description or not category_id:
            message = "Please, Enter all the fields"
            flash(message)
            return redirect(url_for('itemUpdate', id=item.id))

        item.title = title
        item.description = description
        item.cat_id = category_id
        session.add(item)

        try:
            session.commit()
            message = "Updated successfully"
            flash(message)
        except exc.SQLAlchemyError as e:
            print(str(e))
            message = "Unable to save changes"
            flash(message)
        return redirect(url_for('itemUpdate', id=item.id))

    if request.method == 'GET':
        categories = session.query(Category).all()
        return render_template('update.html', categories=categories, item=item)


@app.route('/item/delete/<int:id>', methods=['GET', 'POST'])
def itemDelete(id):
    try:
        item = session.query(Item).filter_by(id=id).first()
    except exc.SQLAlchemyError as e:
        # if the item doesn't exist return Not found
        abort(404)

    if "username" not in login_session:
            return redirect(url_for('login'))

    if not item.user or item.user.id != int(login_session.get('user_id')):
        # if the current user doesn't match the user who create
        # the item return Unauthorized
        abort(401)

    if request.method == "POST":
        session.delete(item)
        try:
            session.commit()
            message = "Deleted successfully"
            flash(message)
        except exc.SQLAlchemyError as e:
            print(str(e))
            message = "Unable to delete item"
            flash(message)
            return redirect(url_for('itemDelete', id=item.id))
        return redirect(url_for('index'))

    if request.method == "GET":
        return render_template('delete.html', item=item)


if __name__ == '__main__':
    app.secret_key = secret_key
    app.debug = True
    app.config['SECRET_KEY'] = secret_key
    app.run(host='0.0.0.0', port=5000)
