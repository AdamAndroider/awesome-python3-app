import logging

logging.basicConfig(level=logging.INFO)
__author__ = 'Adam Lee'


'''
JSON API Error definition.
'''


class APIError(Exception):
	'''The base APIError which contains error(required), data(optional) and message(optional).
	'''

	def __init__(self, error, data='', message=''):
		super(APIError, self).__init__(message)
		self.error = error
		self.data = data
		self.message = message
