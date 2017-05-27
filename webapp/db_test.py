import asyncio
from webapp import async_orm
from webapp.models import User


async def db_test(loop):
	await async_orm.create_pool(loop=loop, user='root', password='root123', db='awesome')
	user = User(name='Test', email='test10@example.com', password='1234567890', image='about:blank')
	await user.save()
	# await destroy_pool()

event_loop = asyncio.get_event_loop()
event_loop.run_until_complete(db_test(event_loop))
event_loop.close()




