import logging
import aiomysql


__author__ = 'Adam Lee'

'''
orm 操作数据库
'''


# 统一调用的log方法
def log(sql):
	logging.info('SQL：{}'.format(sql))


__pool = None

# 异步IO接连mysql
async def create_pool(loop, **kw):
	logging.info('create database connection pool...')
	global __pool
	__pool = await aiomysql.create_pool(
		loop=loop,
		host=kw.get('host', 'localhost'),
		port=kw.get('port', 3306),
		user=kw['user'],
		db=kw['db'],
		charset=kw.get('charset', 'utf8'),
		autocommit=kw.get('autocommit', True),
		maxsize=kw.get('maxsize', 10),
		minsize=kw.get('minsize', 1)
	)

# 执行SELECT语句，完成查找 sql是sql语句
async def select(sql, args, size=None):
	log(sql)
	global __pool
	async with __pool.get() as conn:
		async with conn.cursor(aiomysql.DictCursor) as cursor:
			await cursor.execute(sql.replace('?', '%s'), args or ())
			if size:
				rs = await cursor.fetchmany(size)
			else:
				rs = await cursor.fetchall()
		logging.info('rows returned: %s' % len(rs))
		return rs

# 通用的execute()执行INSERT、UPDATE、DELETE语句
async def execute(sql, args, autocommit=True):
	log(sql)
	async with __pool.get() as conn:
		if not autocommit:
			await conn.begin()
		try:
			async with conn.cursor(aiomysql.DictCursor) as cursor:
				await cursor.execute(sql.replace('?', '%s'), args)
				affected = cursor.rowcount
				if not autocommit:
					await conn.commit()
		except:
			if not autocommit:
				await conn.rollback()
			raise
		return affected

