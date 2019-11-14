
class MastodoffError(Exception):
	"""
	Base class for exceptions in the app.
	"""

	pass


class MastodonAPIError(MastodoffError):
	"""
	Base class for errors related to Mastodon API calls.
	"""

	pass


class NoSearchResultsError(MastodonAPIError):
	"""
	Raised when a search with the Mastodon API returns no values.
	"""

	pass


class DatabaseError(MastodoffError):
	"""
	Base class for errors related to the database.
	"""

	pass


class NotInDatabaseError(DatabaseError):
	"""
	Raised when an item is not found in the database.
	"""

	pass



