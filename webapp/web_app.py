from datetime import datetime
from aiohttp import web
import logging, os, json, time, asyncio
from jinja2 import Environment, FileSystemLoader
from webapp import core_web, async_orm
from webapp.config.config import configs
from webapp.cookie.cookie_manage import COOKIE_NAME, cookie2user

logging.basicConfig(level=logging.INFO)

__author__ = 'Adam Lee'

'''
async web application
'''


# def index(request):
# 	return web.Response(body=b'<h1>Welcome Awesome</h1>', content_type='text/html')  # 此处要加content_type
#
# async def init(loop):
# 	app = web.Application(loop=loop)
# 	app.router.add_route('GET', '/index', index)
# 	srv = await loop.create_server(app.make_handler(), '127.0.0.1', 8000)
# 	logging.info('Server started at http://127.0.0.1:8000/index...')
# 	return srv
#
# async_loop = asyncio.get_event_loop()
# async_loop.run_until_complete(init(async_loop))
# async_loop.run_forever()


def init_jinja2(app, **kw):
	logging.info('init jinja2...')
	options = dict(
		autoescape=kw.get('autoescape', True),
		block_start_string=kw.get('block_start_string', '{%'),
		block_end_string=kw.get('block_end_string', '%}'),
		variable_start_string=kw.get('variable_start_string', '{{'),
		variable_end_string=kw.get('variable_end_string', '}}'),
		auto_reload=kw.get('auto_reload', True)
	)
	path = kw.get('path', None)
	if path is None:
		path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
	logging.info('set jinja2 template path: {}'.format(path))
	env = Environment(loader=FileSystemLoader(path), **options)
	filters = kw.get('filters', None)
	if filters is not None:
		for name, f in filters.items():
			env.filters[name] = f
	app['__templating__'] = env


async def logger_factory(app, handler):
	async def logger(request):
		logging.info('Request: {} {}'.format(request.method, request.path))
		# await asyncio.sleep(0.3)
		return (await handler(request))
	return logger


async def data_factory(app, handler):
	async def parse_data(request):
		if request.method == 'POST':
			if request.content_type.startswith('application/json'):
				request.__data__ = await request.json()
				logging.info('request json: {}'.format(str(request.__data__)))
			elif request.content_type.startswith('application/x-www-form-urlencoded'):
				request.__data__ = await request.post()
				logging.info('request form: {}'.format(str(request.__data__)))
		return (await handler(request))
	return parse_data


# 自动登录验证
async def auth_factory(app, hander):
	async def auth(request):
		logging.info('check user: {} {}'.format(request.method, request.path))
		request.__user__ = None
		cookie_str = request.cookies.get(COOKIE_NAME)
		if cookie_str:
			user = await cookie2user(cookie_str)
			if user:
				logging.info('set current user: {}'.format(user.email))
				request.__user__ = user
		if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
			return web.HTTPFound('/login')
		return (await hander(request))
	return auth


# 返回数据
async def response_factory(app, handler):
	async def response(request):
		logging.info('Response handler...')
		hr = await handler(request)
		if isinstance(hr, web.StreamResponse):
			return hr
		if isinstance(hr, bytes):
			resp = web.Response(body=hr)
			resp.content_type = 'application/octet-stream'
			return resp
		if isinstance(hr, str):
			if hr.startswith('redirect:'):
				return web.HTTPFound(hr[9:])
			resp = web.Response(body=hr.encode('utf-8'))
			resp.content_type = 'text/html;charset=utf-8'
			return resp
		if isinstance(hr, dict):
			template = hr.get('__template__')
			if template is None:
				resp = web.Response(body=json.dumps(hr, ensure_ascii=False, default=lambda ob: ob.__dict__).encode('utf-8'))
				resp.content_type = 'application/json;charset=utf-8'
				return resp
			else:
				hr['__user__'] = request.__user__
				resp = web.Response(body=app['__templating__'].get_template(template).render(**hr).encode('utf-8'))
				resp.content_type = 'text/html;charset=utf-8'
				return resp

		if isinstance(hr, int) and hr >= 100 and hr <= 600:
			return web.Response(hr)
		if isinstance(hr, tuple) and len(hr) == 2:
			code, msg = hr
			if isinstance(code, int) and code >=100 and code <= 600:
				return web.Response(code, str(msg))
		# default:
		resp = web.Response(body=str(hr).encode('utf-8'))
		resp.content_type = 'text/plain;charset=utf-8'
		return resp
	return response


def datetime_filter(tm):
	delta = int(time.time() - tm)
	if delta < 60:
		return u'1分钟前'
	if delta < 3600:
		return u'%s分钟前' % (delta // 60)
	if delta < 86400:
		return u'%s小时前' % (delta // 3600)
	if delta < 604800:
		return u'%s天前' % (delta // 86400)
	dt = datetime.fromtimestamp(tm)
	return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


async def init(loop):
	await async_orm.create_pool(loop=loop, **configs.db)
	app = web.Application(loop=loop, middlewares=[logger_factory, auth_factory, response_factory])
	init_jinja2(app, filters=dict(datetime=datetime_filter))
	core_web.add_routes(app, 'handlers')
	core_web.add_static(app)
	srv = await loop.create_server(app.make_handler(), 'localhost', 9000)
	logging.info('server started at http://localhost:9000...')
	return srv

async_loop = asyncio.get_event_loop()
async_loop.run_until_complete(init(async_loop))
async_loop.run_forever()


