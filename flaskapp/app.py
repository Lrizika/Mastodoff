#!/usr/bin/env python

import logging
import os
import flaskapp

from flask import Flask, render_template, request
from flaskapp.model import DB
from flaskapp.mastodon_bot import instantiate_basilica, instantiate_bot, add_account, get_db_statuses
from flaskapp.log import startLog
from flaskapp.exceptions import MastodoffError
from flaskapp.predict import predict_account


startLog(None)
APP_LOG = logging.getLogger('root')


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
def index(success=False, message=None):
	return (render_template('index.html.j2', success=success, message=message))


@app.route("/add", methods=['POST'])
def add():
	try:
		username = request.values.get('username', None)
		APP_LOG.info(f'/add called with username {username}')
		account = add_account(DB, basilica_client, mastodon_client, username, count=120)
		message = f'Successfully added account {account}'
		success = True
	except Exception as e:
		APP_LOG.exception(f'Exception in /add: {e}')
		APP_LOG.exception(e)
		message = f'Unknown failure adding account with username {username}'
		if isinstance(e, MastodoffError):
			message = str(e)
		success = False
	return (index(success=success, message=message))


@app.route("/get", methods=['GET'])
def get():
	try:
		username = request.values.get('username', None)
		APP_LOG.info(f'/get called with username {username}')
		message = get_db_statuses(mastodon_client, username)
		success = True
	except Exception as e:
		APP_LOG.exception(f'Exception in /get: {e}')
		APP_LOG.exception(e)
		message = f'Unknown failure getting statuses for username {username}'
		if isinstance(e, MastodoffError):
			message = str(e)
		success = False
	return (index(success=success, message=message))


@app.route("/predict", methods=['POST'])
def predict():
	try:
		username1 = request.values.get('username1', None)
		username2 = request.values.get('username2', None)
		content = request.values.get('content', None)
		APP_LOG.info(f'/predict called with usernames: {username1, username2}, content: {content}')
		prediction = predict_account(basilica_client, mastodon_client, username1, username2, content)
		message = f'Account with username {prediction} is more likely to post "{content}".'
		success = True
	except Exception as e:
		APP_LOG.exception(f'Exception in /predict: {e}')
		APP_LOG.exception(e)
		message = f'Unknown failure getting predictions for usernames: {username1, username2}, content: {content}'
		if isinstance(e, MastodoffError):
			message = str(e)
		success = False
	return (index(success=success, message=message))


@app.route("/reset", methods=['POST'])
def reset():
	try:
		APP_LOG.info(f'/reset called')
		DB.drop_all()
		DB.create_all()
		message = 'Successfully reset database.'
		success = True
	except Exception as e:
		APP_LOG.exception(f'Exception in /reset: {e}')
		APP_LOG.exception(e)
		message = 'Unknown failure resetting database.'
		if isinstance(e, MastodoffError):
			message = str(e)
		success = False
	return (index(success=success, message=message))

