import json
from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Class
from flask import session as login_session

# Setup flask app
app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# VIEWS


@app.route('/')
def show_all():
    classes = session.query(Class).order_by('category').all()
    return render_template('index.html', classes=classes)


@app.route('/new_class/', methods=['GET', 'POST'])
def new_class():
    if request.method == 'GET':
        return render_template('new_class.html', content='add new class')
    if request.method == 'POST':
        category = request.form['category']
        title = request.form['title']
        description = request.form['description']
        if category != '' and title != '' and description != '':
            class_to_add = Class(category=category,
                                 title=title,
                                 description=description)
            session.add(class_to_add)
            session.commit()
            flash('Added class {0} successfully'.format(title))
        else:
            flash('Class category, title, and description required')
        return redirect(url_for('show_all'))
    else:
        flash('Unsupported request type.')
        return redirect(url_for('show_all'))

@app.route('/delete_class/<int:id>/', methods=['GET', 'POST'])
def delete_class(id):
    if request.method == 'GET':
        class_to_delete = session.query(Class).filter_by(id=id).one()
        return render_template('delete_class.html',
                               class_to_delete=class_to_delete)
    if request.method == 'POST':
        class_to_delete = session.query(Class).filter_by(id=id).one()
        session.delete(class_to_delete)
        session.commit()
        flash ('Deleted {0} successfully'.format(class_to_delete.title))
        return redirect(url_for('show_all'))
    else:
        flash('Unsupported request type.')
        return redirect(url_for('show_all'))


@app.route('/edit_class/<int:id>/', methods=['GET', 'POST'])
def edit_class(id):
    if request.method == 'GET':
        class_to_edit = session.query(Class).filter_by(id=id).one()
        return render_template('edit_class.html',
                               class_to_edit=class_to_edit)
    if request.method == 'POST':
        category = request.form['category']
        title = request.form['title']
        description = request.form['description']
        if category != '' and title != '' and description != '':
            class_to_edit = session.query(Class).filter_by(id=id).one()
            class_to_edit.category = category
            class_to_edit.title = title
            class_to_edit.description = description
            session.commit()
            flash ('Edited {0} successfully'.format(class_to_edit.title))
        else:
            flash('Class category, title, and description required')
        return redirect(url_for('show_all'))
    else:
        flash('Unsupported request type.')
        return redirect(url_for('show_all'))


# Run flask app at http://localhost:5002/ in debug mode
if __name__ == '__main__':
    app.secret_key = json.loads(
        open('private/secrets.json', 'r').read())['app']['secret_key']
    app.debug = True
    app.run(host='localhost', port=5002)
