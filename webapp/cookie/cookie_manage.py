import hashlib
import time
import logging

from webapp.config.config import configs
from webapp.models import User


logging.basicConfig(level=logging.INFO)


''''Manage cookie.
'''
__author__ = 'Adam Lee'

_COOKIE_KEY = configs.session.secret
COOKIE_NAME = 'awesession'


# 根据用户信息设置cookie
def user2cookie(user, max_age):
	'''Generate cookie str by user.
	'''
	# build cookie string by: id-expires-sha1
	expires = str(int(time.time() + max_age))
	key = '{}-{}-{}-{}'.format(user.id, user.password, expires, _COOKIE_KEY)
	cookies = [user.id, expires, hashlib.sha1(key.encode('utf-8')).hexdigest()]
	return '-'.join(cookies)


# 解析cookie
async def cookie2user(cookie_str):
	'''Parse cookie and load user if cookie is valid.
	'''

	if not cookie_str:
		return None
	try:
		cookies = cookie_str.split('-')
		if len(cookies) != 3:
			return None
		(uid, expires, sha1) = cookies
		if int(expires) < time.time():
			return None
		user = await User.find(uid)
		if user is None:
			return None
		key = '{}-{}-{}-{}'.format(user.id, user.password, expires, _COOKIE_KEY)
		if sha1 != hashlib.sha1(key.encode('utf-8')).hexdigest():
			logging.info('invalid sha1')
			return None
		user.password = '******'
		return user
	except Exception as e:
		logging.info(e)
		return None
