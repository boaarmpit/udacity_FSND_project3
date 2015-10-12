import json
from flask import Flask, render_template, request, redirect, \
    url_for, flash, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Class
import xml.etree.ElementTree as et

# Setup flask app
app = Flask(__name__)
import app_oauth
app.register_blueprint(app_oauth.oauth_api, url_prefix='/oauth')

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# HTML VIEWS

# Temporary test function for debugging oauth state.
@app.route('/test/')
def test():
    app_oauth.login_session['state'] = 'unusable'
    if 'providor'in app_oauth.login_session:
        return app_oauth.login_session['provider']
    else:
        return "no providor variable found"

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
                               state=app_oauth.login_session['state'])
    else:
        return render_template('index.html', data=categories_and_classes,
                               logged_in=False)


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

            # Add category if it doesn't already exist:
            category = session.query(Category).filter_by(
                title=category_title).first()
            if not category:
                category = Category(title=category_title)
                session.add(category)
                session.flush()  # so that category.id returns value before commit

            # Add class
            class_to_add = Class(category_id=category.id,
                                 title=title,
                                 description=description,
                                 teacher_id=user_id)
            session.add(class_to_add)
            session.commit()
            flash(u'Added class {0} successfully'.format(title))
        else:
            flash(u'Class category, title, and description required')
        return redirect(url_for('show_all'))
    else:
        flash(u'Unsupported request type.')
        return redirect(url_for('show_all'))


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
                               category_title=category.title)
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
                session.flush()  # so that category.id returns value before commit

            # Edit class:
            edited_class_old_category_id = class_to_edit.category_id
            class_to_edit.category_id = category.id
            class_to_edit.title = title
            class_to_edit.description = description

            # Delete category if there are no longer any classes in it:
            if session.query(Class).filter_by(
                    category_id=edited_class_old_category_id).first() is None:
                category_to_delete = session.query(Category).filter_by(
                    id=edited_class_old_category_id).one()
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
            et.SubElement(xml_class, "description").text = c.description

    xml_out = et.tostring(xml_root, method='xml', encoding='UTF-8')
    return Response(xml_out, mimetype='application/xml')

# Run flask app at http://localhost:5002/ in debug mode
if __name__ == '__main__':
    app.secret_key = json.loads(
        open('private/secrets.json', 'r').read())['app']['secret_key']
    app.debug = True
    app.run(host='localhost', port=5000)
