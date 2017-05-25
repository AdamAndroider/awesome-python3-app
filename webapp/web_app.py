from aiohttp import web
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

__author__ = 'Adam Lee'

'''
async web application
'''


def index(request):
	return web.Response(body=b'<h1>Welcome Awesome</h1>', content_type='text/html')  # 此处要加content_type

async def init(loop):
	app = web.Application(loop=loop)
	app.router.add_route('GET', '/index', index)
	srv = await loop.create_server(app.make_handler(), '127.0.0.1', 8000)
	logging.info('Server started at http://127.0.0.1:8000/index...')
	return srv

async_loop = asyncio.get_event_loop()
async_loop.run_until_complete(init(async_loop))
async_loop.run_forever()

