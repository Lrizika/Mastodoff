#!/usr/bin/env python

import os
import flaskapp

from flask import Flask, render_template, request
from flaskapp.model import DB
from flaskapp.mastodon_bot import instantiate_basilica, instantiate_bot, add_account, get_db_account


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
DB.init_app(app)

mastodon_client = instantiate_bot()
basilica_client = instantiate_basilica()


@app.route("/")
@app.route("/index")
@app.route("/index/")
@app.route("/index.html")
def index():
	return (render_template('index.html.j2'))


@app.route("/add")
def add():
	username = request.values['username']
	add_account(DB, basilica_client, mastodon_client, username)
	return (index())


@app.route("/get")
def get():
	username = request.values['username']
	return (str(get_db_account(DB, mastodon_client, username)))


@app.route("/reset")
@app.route("/reset/")
def reset():
	DB.drop_all()
	DB.create_all()
	return (index())

