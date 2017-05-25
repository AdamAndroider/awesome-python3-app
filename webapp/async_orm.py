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
		password=kw['password'],
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
	global __pool
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


# 数字转为特定字符串
def create_args_string(num):
	nums = []
	for n in range(num):
		nums.append('?')
	return ', '.join(nums)


# 字段
class Field:
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default

	def __str__(self):
		return '<{}, {}:{}>'.format(self.__class__.__name__, self.column_type, self.name)


# 字符串字段
class StringField(Field):
	def __init__(self, name=None, primary_key=False, default=None, column_type='varchar(100)'):
		super().__init__(name, column_type, primary_key, default)


# boolean字段
class BooleanField(Field):
	def __init__(self, name=None, default=False):
		super().__init__(name, 'boolean', False, default)


# int字段
class IntegerField(Field):
	def __init__(self, name=None, primary_key=False, default=0):
		super().__init__(name, 'bigint', primary_key, default)


# float字段
class FloatField(Field):
	def __init__(self, name=None, primary_key=False, default=0.0):
		super().__init__(name, 'real', primary_key, default)


# text字段
class TextField(Field):
	def __init__(self, name=None, default=None):
		super().__init__(name, 'text', False, default)


# model的元类
class ModelMetaclass(type):
	def __new__(cls, name, bases, attrs):
		if name == 'Model':
			return type.__new__(cls, name, bases, attrs)
		table_name = attrs.get('__table_name__', None) or name
		logging.info('found model: {} (table: {})'.format(name, table_name))
		mappings = dict()
		fields = []
		primary_key = None
		for key, value in attrs.items():
			if isinstance(value, Field):
				logging.info(' found mapping: {} ==> {}'.format(key, value))
				mappings[key] = value
				if value.primary_key:
					if primary_key:
						raise Exception('Duplicate primary key for field: {}'.format(key))
					primary_key = key
				else:
					fields.append(key)

		if not primary_key:
			raise Exception('Primary key not found.')

		for k in mappings.keys():
			attrs.pop(k)

		escaped_fields = list(map(lambda f: '`%s`' % f, fields))
		attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
		attrs['__table_name__'] = table_name
		attrs['__primary_key__'] = primary_key  # 主键属性名
		attrs['__fields__'] = fields  # 除主键外的属性名
		attrs['__select__'] = 'select `%s`, %s from `%s`' % (primary_key, ', '.join(escaped_fields), table_name)
		attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (table_name, ', '.join(escaped_fields), primary_key, create_args_string(len(escaped_fields) + 1))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (table_name, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primary_key)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (table_name, primary_key)
		return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" % key)

	def __setattr__(self, key, value):
		self[key] = value

	def getvalue(self, key):
		return getattr(self, key, None)

	def getValueOrDefault(self, key):
		value = getattr(self, key, None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for {}: {}'.format(key, str(value)))
				setattr(self, key, value)

		return value

	@classmethod
	async def findAll(cls, where=None, args=None, **kw):
		'''
		find objects by where clause.	
		:param where: 
		:param args: 
		:param kw: 
		:return: 
		'''
		sql = [cls.__select__]
		if where:
			sql.append('where')
			sql.append(where)
		if args is None:
			args = []
		orderBy = kw.get("orderBy", None)
		if orderBy:
			sql.append('order by')
			sql.append(orderBy)
		limit = kw.get('limit', None)
		if limit is not None:
			sql.append('limit')
			if isinstance(limit, int):
				sql.append('?')
				args.append(limit)
			elif isinstance(limit, tuple) and len(limit) == 2:
				sql.append('?, ?')
				args.extend(limit)
			else:
				raise ValueError('Invalid limit value: {}'.format(str(limit)))
		rs = await select(' '.join(sql), args)
		return [cls(**r) for r in rs]

	@classmethod
	async def findNumber(cls, selectField, where=None, args=None):
		'''
		ffind number by select and where.
		:param selectField: 
		:param where: 
		:param args: 
		:return: 
		'''
		sql = ['select %s _num_ from `%s`' % (selectField, cls.__table_name__)]
		if where:
			sql.append('where')
			sql.append(where)
		rs = await select(' '.join(sql), args, 1)
		if len(rs) == 0:
			return None
		return rs[0]['_num_']

	@classmethod
	async def find(cls, pk):
		'''
		find object by primary key. '
		:param pk: 
		:return: 
		'''
		rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
		if len(rs) == 0:
			return None
		return cls(**rs[0])

	# 保存
	async def save(self):
		args = list(map(self.getValueOrDefault, self.__fields__))
		args.append(self.getValueOrDefault(self.__primary_key__))
		rows = await execute(self.__insert__, args)
		if rows != 1:
			logging.info('failed to insert record: affected rows: {}'.format(str(rows)))

	# 更新
	async def update(self):
		args = list(map(self.getvalue(), self.__fields__))
		args.append(self.getvalue(self.__primary_key__))
		rows = await execute(self.__update__, args)
		if rows != 1:
			logging.info('failed to insert record: affected rows: {}'.format(str(rows)))

	# 删除
	async def remove(self):
		args = [self.getValue(self.__primary_key__)]
		rows = await execute(self.__delete__, args)
		if rows != 1:
			logging.info('failed to insert record: affected rows: {}'.format(str(rows)))
