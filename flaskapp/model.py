#!/usr/bin/env python

from flask_sqlalchemy import SQLAlchemy

DB = SQLAlchemy()


class Account(DB.Model):
	__tablename__ = 'account'
	id = DB.Column(DB.String(255), primary_key=True, nullable=False)
	username = DB.Column(DB.String(255), nullable=False)
	url = DB.Column(DB.String(255), nullable=False)
	acct = DB.Column(DB.String(255), nullable=False)

	statuses = DB.relationship('Status', back_populates='account', lazy='select')

	def __repr__(self):
		return(f'<Account {self.id} ({self.username})>')

	def __str__(self):
		return(f'{self.username} ({self.id}, {self.url})')


class Status(DB.Model):
	__tablename__ = 'status'
	id = DB.Column(DB.String(255), primary_key=True, nullable=False)
	uri = DB.Column(DB.String(255), nullable=False)
	accountid = DB.Column(DB.String(255), DB.ForeignKey('account.id'), nullable=False)
	content = DB.Column(DB.String(255), nullable=False)
	embedding = DB.Column(DB.PickleType, nullable=False)

	account = DB.relationship('Account', back_populates='statuses', lazy='select')

	def __repr__(self):
		return(f'<Status {self.id} by {self.accountid}>')

	def __str__(self):
		return(f'{self.account} ({self.uri}): "{self.content}"')

