import hashlib
import re
import json
import logging
from aiohttp import web

from webapp.api_error import APIValueError, APIError
from webapp.cookie.cookie_manage import COOKIE_NAME, user2cookie
from webapp.core_web import get, post
from webapp.models import User, next_id


logging.basicConfig(level=logging.INFO)

@get('/')
async def index_test():
	users = await User.findAll()
	return {'__template__': 'html_test.html', 'users': users}


# 用户列表API
@post('/api/users')
async def api_get_users():
	users = await User.findAll(orderBy='created_at desc')
	return dict(users=users)

# 邮件地址正则匹配
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
# 密码规则匹配
_RE_PW = re.compile(r'^[a-z0-9]{6,16}$')


# 注册接口
@post('/api/register')
async def api_register_user(*, email, name, password):
	if not name or not name.strip():
		raise APIValueError('name')

	if not email or not _RE_EMAIL.match(email):
		raise APIValueError('email')

	if not password or not _RE_PW.match(password):
		raise APIValueError('password')
	users = await User.findAll('email=?', [email])
	if len(users) > 0:
		raise APIError('register:failed', 'email', 'Email is already in use.')

	uid = next_id()
	sha1_pw = '{}:{}'.format(uid, password)
	user = User(id=uid, name=name.strip(), email=email, password=hashlib.sha1(sha1_pw.encode('utf-8')).hexdigest(), image='')
	await user.save()
	# make session cookie:
	response = web.Response()
	response.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)  # 此处设置cookie
	user.password = '******'  # 密码不显示
	response.content_type = 'application/json'
	response.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
	return response


# 登录验证接口
@post('/api/login')
async def login(*, email, password):
	if not email:
		raise APIValueError('email', 'Invalid email.')

	if not password:
		raise APIValueError('password', 'Invalid password.')

	users = await User.findAll('email=?', [email])

	if len(users) == 0:
		raise APIValueError('email', 'Email not exist.')
	user = users[0]
	# check passwd:
	sha1 = hashlib.sha1()
	sha1.update(user.id.encode('utf-8'))
	sha1.update(b':')
	sha1.update(password.encode('utf-8'))
	if user.password != sha1.hexdigest():
		raise APIValueError('password', 'Invalid password.')
	# authenticate ok, set cookie:
	response = web.Response()
	response.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
	user.password = '******'
	response.content_type = 'application/json'
	response = json.dumps(user, ensure_ascii=False).encode('utf-8')
	return response


# 退出登录
def logout(request):
	referer = request.headers.get('Referer')
	found = web.HTTPFound(referer or '/')
	found.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
	logging.info('user signed out.')
	return found








