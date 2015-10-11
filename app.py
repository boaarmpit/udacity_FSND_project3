from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Lesson
from flask import session as login_session

app = Flask(__name__)

#XXX Test
@app.route('/')
def test():
    print "test"
    return render_template('test.html')


if __name__ == '__main__':
    app.secret_key = '71864813625223673536721504869408395782255281482800985325'
    app.debug = True
    app.run(host='localhost', port=5000)