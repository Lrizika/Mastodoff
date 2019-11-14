#!/usr/bin/env python

import basilica
import os

from decouple import config
from mastodon import Mastodon
from flaskapp.model import Account, Status
from flaskapp.log import startLog, LOGFILE


BOT_LOG = startLog(LOGFILE)


def instantiate_bot() -> Mastodon:
	if not os.path.exists(config('MASTODON_SECRET_LOCATION')):
		BOT_LOG.info(f'Creating Mastodon app...')
		Mastodon.create_app(
			'mastodoff',
			api_base_url=config('MASTODON_API'),
			to_file=config('MASTODON_SECRET_LOCATION'),
		)

	if not os.path.exists(config('MASTODON_TOKEN_LOCATION')):
		BOT_LOG.info(f'Getting Mastodon token...')
		mastodon = Mastodon(
			client_id=config('MASTODON_SECRET_LOCATION'),
			api_base_url=config('MASTODON_API'),
		)
		mastodon.log_in(
			config('MASTODON_USERNAME'),
			config('MASTODON_PASSWORD'),
			to_file=config('MASTODON_TOKEN_LOCATION'),
		)

	BOT_LOG.info(f'Instantiating mastodon.Mastodon...')
	client = Mastodon(
		client_id=config('MASTODON_SECRET_LOCATION'),
		access_token=config('MASTODON_TOKEN_LOCATION'),
		api_base_url=config('MASTODON_API'),
	)

	return (client)


def get_account(client, username):
	# parts = username.split('@')
	# assert len(parts) == 3, \
	# 	'username must be in the format @account@server.tld'
	# assert len(parts[0]) == 0, \
	# 	'username must begin with @'

	# TODO: Make this prioritize exact matches,
	# raise exception if ambiguous
	BOT_LOG.info(f'Getting account for username {username}...')
	results = client.search(username, result_type='accounts')
	return(results['accounts'][0])


def get_statuses(client, *, account=None, username=None, count=20):
	assert (account is None) != (username is None), \
		f'''
		get_statuses requires precisely one of `account`, `username`
		received `account`={account}, `username`={username}
		'''

	if account is None:
		account = get_account(client, username)
	BOT_LOG.info(f'Getting statuses for account id {account["id"]}...')
	statuses = client.account_statuses(id=account['id'])
	return(statuses[:count])


def instantiate_basilica():
	BOT_LOG.info(f'Instantiating basilica.Connection...')
	client = basilica.Connection(config('BASILICA_KEY'))
	return (client)


def get_embeddings(client, contents):
	BOT_LOG.info(f'Getting embeddings for {len(contents)} statuses...')
	embeddings = client.embed_sentences(contents, model='twitter')
	return (embeddings)


def get_db_account(db, mastodon_client, username):
	BOT_LOG.info(f'Getting database info for username {username}...')
	account = get_account(mastodon_client, username)
	db_account = Account.query.get(account['id'])
	return (
		str(
			[str(status) for status in db_account.statuses],
		)
	)


def add_account(db, basilica_client, mastodon_client, username, count=20):
	BOT_LOG.info(f'Adding account {username}...')
	account = get_account(mastodon_client, username)

	db_account = Account.query.get(account['id'])
	if db_account is None:
		db_account = Account(
			id=account['id'],
			username=account['username'],
			url=account['url'],
			acct=account['acct'],
		)
	db.session.add(db_account)

	statuses = get_statuses(mastodon_client, account=account, count=count)

	contents = [status['content'] for status in statuses]
	embeddings = list(get_embeddings(basilica_client, contents))
	for i in range(len(statuses)):
		statuses[i]['embedding'] = embeddings[i]

	for status in statuses:
		# embedding = list(get_embedding(basilica_client, status))
		db_status = Status(
			id=status['id'],
			uri=status['uri'],
			accountid=status['account']['id'],
			content=status['content'],
			embedding=status['embedding'],
		)
		db.session.add(db_status)

	db.session.commit()
	BOT_LOG.info(f'Done adding account.')

