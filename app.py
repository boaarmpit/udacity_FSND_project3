import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, \
    url_for, flash, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Class
import xml.etree.ElementTree as et

import app_oauth

# Setup flask app
UPLOAD_FOLDER = 'static/images/upload/'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

app = Flask(__name__)
app.debug = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.register_blueprint(app_oauth.oauth_api, url_prefix='/oauth')

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# HTML VIEWS

# Displays all classes sorted by subject,
# with links to edit/delete if user is logged in
@app.route('/')
def show_all():
    logged_in = 'username' in app_oauth.login_session

    categories = session.query(Category).all()
    categories_and_classes = []

    for category in categories:
        classes = session.query(Class).filter_by(category_id=category.id).all()
        categories_and_classes.append([category.title, classes])

    if logged_in:
        return render_template('index.html', data=categories_and_classes,
                               logged_in=True,
                               state=app_oauth.login_session['state'],
                               UPLOAD_FOLDER=UPLOAD_FOLDER)
    else:
        return render_template('index.html', data=categories_and_classes,
                               logged_in=False,
                               UPLOAD_FOLDER=UPLOAD_FOLDER)


# GET method: Form for registered user to add a new class
# POST method: Accepts submitted data and saves to database
@app.route('/new_class/', methods=['GET', 'POST'])
def new_class():
    if 'user_id' not in app_oauth.login_session:
        return redirect(url_for('oauth_api.login'))
    user_id = app_oauth.login_session['user_id']

    # Validate state token (Anti Forgery State Token)
    invalid_response = app_oauth.validate_token(request.args.get('state'))
    if invalid_response:
        return invalid_response

    if request.method == 'GET':
        return render_template('new_class.html', content='add new class')
    if request.method == 'POST':
        category_title = request.form['category']
        title = request.form['title']
        description = request.form['description']
        if category_title != '' and title != '' and description != '':
            # Save image
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = datetime.now().strftime('img_%Y-%m-%d_%H%M%S.jpg')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                print "saved to ", filepath
            else:
                filename = None

            # Add category if it doesn't already exist:
            category = session.query(Category).filter_by(
                title=category_title).first()
            if not category:
                category = Category(title=category_title)
                session.add(category)
                # flush so that category.id returns value before commit:
                session.flush()

            # Add class
            class_to_add = Class(category_id=category.id,
                                 title=title,
                                 description=description,
                                 teacher_id=user_id,
                                 picture=filename)
            session.add(class_to_add)
            session.commit()
            flash(u'Added class {0} successfully'.format(title))
        else:
            flash(u'Class category, title, and description required')
        return redirect(url_for('show_all'))
    else:
        flash(u'Unsupported request type.')
        return redirect(url_for('show_all'))


# GET method: Form to confirm registered wants to delete class
# POST method: Deletes selected class
# and also category if it no longer contains any classes
@app.route('/delete_class/<int:id>/', methods=['GET', 'POST'])
def delete_class(id):
    if 'user_id' not in app_oauth.login_session:
        return redirect(url_for('oauth_api.login'))
    user_id = app_oauth.login_session['user_id']

    # Validate state token (Anti Forgery State Token)
    invalid_response = app_oauth.validate_token(request.args.get('state'))
    if invalid_response:
        return invalid_response

    class_to_delete = session.query(Class).filter_by(id=id).one()
    if class_to_delete.teacher_id != user_id:
        flash(u'Unauthorized to delete item')
        return redirect(url_for('show_all'))

    if request.method == 'GET':
        return render_template('delete_class.html',
                               class_to_delete=class_to_delete)

    if request.method == 'POST':
        # Delete image if it exists
        if class_to_delete.picture:
            path = UPLOAD_FOLDER + class_to_delete.picture
            os.remove(path)
            print "deleted", path

        # Delete class:
        deleted_class_category_id = class_to_delete.category_id
        session.delete(class_to_delete)

        # Delete category if there are no longer any classes in it:
        if session.query(Class).filter_by(
                category_id=deleted_class_category_id).first() is None:
            category_to_delete = session.query(Category).filter_by(
                id=deleted_class_category_id).one()
            session.delete(category_to_delete)
            print 'deleted category no. {0}'.format(category_to_delete.id)

        session.commit()

        flash(u'Deleted {0} successfully'.format(class_to_delete.title))
        return redirect(url_for('show_all'))
    else:
        flash(u'Unsupported request type.')
        return redirect(url_for('show_all'))


# GET method: Form for registered user to edit a class (that they added)
# POST method: Accepts submitted data and saves to database
@app.route('/edit_class/<int:id>/', methods=['GET', 'POST'])
def edit_class(id):
    if 'user_id' not in app_oauth.login_session:
        return redirect(url_for('oauth_api.login'))
    user_id = app_oauth.login_session['user_id']

    # Validate state token (Anti Forgery State Token)
    invalid_response = app_oauth.validate_token(request.args.get('state'))
    if invalid_response:
        return invalid_response

    class_to_edit = session.query(Class).filter_by(id=id).one()
    if class_to_edit.teacher_id != user_id:
        flash(u'Unauthorized to edit item')
        return redirect(url_for('show_all'))

    if request.method == 'GET':
        category = session.query(Category).filter_by(
            id=class_to_edit.category_id).one()
        return render_template('edit_class.html',
                               class_to_edit=class_to_edit,
                               category_title=category.title,
                               UPLOAD_FOLDER=UPLOAD_FOLDER)
    if request.method == 'POST':
        category_title = request.form['category_title']
        title = request.form['title']
        description = request.form['description']
        if category_title != '' and title != '' and description != '':

            # Add category if it doesn't already exist:
            category = session.query(Category).filter_by(
                title=category_title).first()
            if not category:
                category = Category(title=category_title)
                session.add(category)
                # flush so that category.id returns value before commit:
                session.flush()

            # Save new image if it exists and delete old image if it exists
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = datetime.now().strftime('img_%Y-%m-%d_%H%M%S.jpg')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                print "saved to", filepath
                if class_to_edit.picture:
                    old_picture_path = UPLOAD_FOLDER + class_to_edit.picture
                    os.remove(old_picture_path)
                    print "deleted", old_picture_path
                class_to_edit.picture = filename

            # Edit class:
            old_category_id = class_to_edit.category_id
            class_to_edit.category_id = category.id
            class_to_edit.title = title
            class_to_edit.description = description

            # Delete category if there are no longer any classes in it:
            if session.query(Class).filter_by(
                    category_id=old_category_id).first() is None:
                category_to_delete = session.query(Category).filter_by(
                    id=old_category_id).one()
                session.delete(category_to_delete)
                print 'deleted category no. {0}'.format(category_to_delete.id)

            session.commit()
            flash(u'Edited {0} successfully'.format(class_to_edit.title))
        else:
            flash(u'Class category, title, and description required')
        return redirect(url_for('show_all'))
    else:
        flash(u'Unsupported request type.')
        return redirect(url_for('show_all'))


# JSON Endpoint(s)
@app.route('/JSON/')
def show_all_json():
    categories = session.query(Category).all()
    categories_and_classes = {}

    for category in categories:
        classes = session.query(Class).filter_by(category_id=category.id).all()
        categories_and_classes[category.title] = [i.serialize for i in classes]

    return Response(json.dumps(categories_and_classes, indent=2,
                               sort_keys=False), mimetype='application/json')


# XML Endpoint(s)
@app.route('/XML/')
def show_all_xml():
    categories = session.query(Category).all()
    xml_root = et.Element("root")

    for category in categories:
        xml_category = et.SubElement(xml_root, "category", id=str(category.id))
        et.SubElement(xml_category, "title").text = category.title
        xml_category_classes = et.SubElement(xml_category, "classes")
        classes = session.query(Class).filter_by(category_id=category.id).all()
        for c in classes:
            xml_class = et.SubElement(xml_category_classes, "class",
                                      id=str(c.id))
            et.SubElement(xml_class, "title").text = c.title
            et.SubElement(xml_class, "teacher_id").text = str(c.teacher_id)
            et.SubElement(xml_class, "description").text = c.description
            et.SubElement(xml_class, "picture").text = c.picture

    xml_out = et.tostring(xml_root, method='xml', encoding='UTF-8')
    return Response(xml_out, mimetype='application/xml')

# Run flask app at http://localhost:5000/
if __name__ == '__main__':
    app.secret_key = json.loads(
        open('private/secrets.json', 'r').read())['app']['secret_key']
    app.debug = False
    app.run(host='localhost', port=5000)
