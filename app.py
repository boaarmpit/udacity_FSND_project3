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
    classes = session.query(Class).all()
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
            flash('Class successfully added')
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
