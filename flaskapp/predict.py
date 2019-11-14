#!/usr/bin/env python

import logging
import numpy

from sklearn.linear_model import LogisticRegression
from decouple import config
from flaskapp.model import Account, Status
from flaskapp.mastodon_bot import get_db_account


PREDICT_LOG = logging.getLogger('root')


def predict_account(basilica_client, mastodon_client, username1, username2, content):
	account1 = get_db_account(mastodon_client, username1)
	account2 = get_db_account(mastodon_client, username2)
	account1_embeddings = numpy.array([status.embedding for status in account1.statuses])
	account2_embeddings = numpy.array([status.embedding for status in account2.statuses])
	embeddings = numpy.vstack([account1_embeddings, account2_embeddings])
	labels = numpy.concatenate([numpy.ones(len(account1.statuses)),
								numpy.zeros(len(account2.statuses))])
	log_reg = LogisticRegression().fit(embeddings, labels)
	status_embedding = basilica_client.embed_sentence(content, model='twitter')
	if log_reg.predict(numpy.array(status_embedding).reshape(1, -1)):
		return (str(account1))
	else:
		return (str(account2))

