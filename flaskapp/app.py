#!/usr/bin/env python

from flask import Flask
from flaskapp.model import DB


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
DB.init_app(app)

@app.route("/")
def index():
	return('This is the root index.')

@app.route("/about")
def about():
	return('About!')

