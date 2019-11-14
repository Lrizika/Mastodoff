#!/usr/bin/env python

import os
import flaskapp

from flask import Flask, render_template, request
from flaskapp.model import DB
from flaskapp.mastodon_bot import instantiate_basilica, instantiate_bot, add_account, get_db_account
from flaskapp.log import startLog


APP_LOG = startLog(None)


APP_LOG.info('Creating app...')
app = Flask(__name__)
APP_LOG.info('Initializing DB...')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
DB.init_app(app)

mastodon_client = instantiate_bot()
basilica_client = instantiate_basilica()

APP_LOG.info('App initialization completed.')


@app.route("/")
@app.route("/index")
@app.route("/index/")
@app.route("/index.html")
def index(success=True):
	return (render_template('index.html.j2', success=success))


@app.route("/add")
def add():
	try:
		username = request.values['username']
		APP_LOG.info(f'/add called with username {username}')
		add_account(DB, basilica_client, mastodon_client, username)
		success = True
	except Exception as e:
		APP_LOG.error(f'Exception in /add: {e}')
		success = False
	return (index(success))


@app.route("/get")
def get():
	try:
		username = request.values['username']
		APP_LOG.info(f'/get called with username {username}')
		success = True
	except Exception as e:
		APP_LOG.error(f'Exception in /get: {e}')
		success = False
	return (str(get_db_account(DB, mastodon_client, username)))


@app.route("/reset")
@app.route("/reset/")
def reset():
	try:
		APP_LOG.info(f'/reset called')
		DB.drop_all()
		DB.create_all()
		success = True
	except Exception as e:
		APP_LOG.error(f'Exception in /reset: {e}')
		success = False
	return (index(success))

