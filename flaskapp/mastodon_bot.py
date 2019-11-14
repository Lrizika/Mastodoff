#!/usr/bin/env python

import basilica
import logging
import os

from decouple import config
from mastodon import Mastodon
from flaskapp.model import Account, Status
from flaskapp.exceptions import (
	NoSearchResultsError,
	NotInDatabaseError
)


BOT_LOG = logging.getLogger('root')


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
		ratelimit_method='throw',
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
	if len(results['accounts']) < 1:
		raise NoSearchResultsError(f'No results for account search with username {username}')
	return (results['accounts'][0])


def get_statuses(*, client=None, account=None, username=None, count=None, limit=40):
	"""
	Get the statuses for an account, by account dict or username

	Args:
		client (mastodon.Mastodon, optional): Mastodon.py client to use.
			If not provided, will initialize a new, non-authenticated client.
			Strongly recommended *against* passing, as non-authed clients have higher rate limits.
		account (dict, optional): Account dict. Precisely one of this or `username` is required.
		username (str, optional): Username. Precisely one of this or `account` is required.
		count (int, optional): Number of statuses to fetch. If omitted, retrieves all.
		limit (int, optional): Number of statuses to fetch per request. Defaults to 40.
			This is usually limited to 40 serverside.

	Returns:
		list: Statuses retrieved
	"""

	assert (account is None) != (username is None), \
		f'''
		get_statuses requires precisely one of `account`, `username`
		received `account`={account}, `username`={username}
		'''

	if client is None:
		client = Mastodon(
			api_base_url=config('MASTODON_API'),
			ratelimit_method='throw',
		)

	if account is None:
		account = get_account(client, username)
	BOT_LOG.info(f'Getting statuses for account id {account["id"]}...')
	full_statuses = []
	max_id = None
	while True:
		BOT_LOG.info(f'Getting statuses for account id {account["id"]} with max_id={max_id}. Current count: {len(full_statuses)}')
		statuses = client.account_statuses(id=account['id'], max_id=max_id, limit=limit)
		if len(statuses) > 0:
			full_statuses += statuses
			max_id = statuses[-1]['id']
		else:
			break
		if count is not None and count <= len(full_statuses):
			break
	BOT_LOG.info(f'Got {len(full_statuses)} statuses.')
	if count is None:
		return (full_statuses)
	return (full_statuses[:count])


def instantiate_basilica():
	BOT_LOG.info(f'Instantiating basilica.Connection...')
	client = basilica.Connection(config('BASILICA_KEY'))
	return (client)


def get_embeddings(client, contents):
	BOT_LOG.info(f'Getting embeddings for {len(contents)} statuses...')
	embeddings = client.embed_sentences(contents, model='twitter')
	return (embeddings)


def get_db_account(mastodon_client, username):
	BOT_LOG.info(f'Getting database info for username {username}...')
	account = get_account(mastodon_client, username)
	db_account = Account.query.get(str(account['id']))
	if db_account is None:
		raise NotInDatabaseError(
			f'No information in database for account with username {username}'
		)
	return (db_account)


def get_db_statuses(mastodon_client, username):
	BOT_LOG.info(f'Getting database statuses for username {username}...')
	db_account = get_db_account(mastodon_client, username)
	return ([status.content for status in db_account.statuses])


def get_db_embeddings(mastodon_client, username):
	BOT_LOG.info(f'Getting database embeddings for username {username}...')
	account = get_account(mastodon_client, username)
	db_account = Account.query.get(str(account['id']))
	return ([status.embedding for status in db_account.statuses])


def add_account(db, basilica_client, mastodon_client, username, count=None):
	BOT_LOG.info(f'Adding account {username}...')
	account = get_account(mastodon_client, username)

	db_account = Account.query.get(str(account['id']))
	if db_account is None:
		db_account = Account(
			id=str(account['id']),
			username=account['username'],
			url=account['url'],
			acct=account['acct'],
		)
	db.session.add(db_account)

	statuses = get_statuses(account=account, count=count)

	contents = [status['content'] for status in statuses]
	embeddings = list(get_embeddings(basilica_client, contents))
	for i in range(len(statuses)):
		statuses[i]['embedding'] = embeddings[i]

	for status in statuses:
		if db.session.query(Status.id).filter_by(id=str(status['id'])).scalar() is None:
			db_status = Status(
				id=str(status['id']),
				uri=status['uri'],
				accountid=str(status['account']['id']),
				content=status['content'],
				embedding=status['embedding'],
			)
			db.session.add(db_status)

	db.session.commit()
	BOT_LOG.info(f'Done adding account.')

	return (db_account)

