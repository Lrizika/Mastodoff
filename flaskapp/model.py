#!/usr/bin/env python

from flask_sqlalchemy import SQLAlchemy

DB = SQLAlchemy()


class Account(DB.Model):
	__tablename__ = 'account'
	id = DB.Column(DB.String(255), primary_key=True)
	username = DB.Column(DB.String(255), nullable=False)

	statuses = DB.relationship('Status', back_populates='accountname', lazy='select')

	def __repr__(self):
		return(f'<Account {self.id} ({self.username})>')


class Status(DB.Model):
	__tablename__ = 'status'
	id = DB.Column(DB.String(255), primary_key=True)
	uri = DB.Column(DB.String(255), nullable=False)
	account = DB.Column(DB.String(255), DB.ForeignKey('account.id'), nullable=False)
	content = DB.Column(DB.String(255), nullable=False)

	accountname = DB.relationship('Account', back_populates='statuses', lazy='select')

	def __repr__(self):
		return(f'<Status {self.id} by {self.account}>')

