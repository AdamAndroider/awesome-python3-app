import time
import uuid
from webapp.async_orm import Model, StringField, BooleanField, FloatField, TextField


def next_id():
	return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


# 用户表
class User(Model):
	__table_name__ = 'users'

	id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
	email = StringField(column_type='varchar(50)')
	password = StringField(column_type='varchar(50)')
	admin = BooleanField()
	name = StringField(column_type='varchar(50)')
	image = StringField(column_type='varchar(500)')
	created_at = FloatField(default=time.time)


# 博客表
class Blog(Model):
	__table_name__ = 'blogs'

	id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
	user_id = StringField(column_type='varchar(50)')
	user_name = StringField(column_type='varchar(50)')
	user_image = StringField(column_type='varchar(500)')
	name = StringField(column_type='varchar(50)')
	summary = StringField(column_type='varchar(200)')
	content = TextField()
	created_at = FloatField(default=time.time)


# 评论表
class Comment(Model):
	__table_name__ = 'comments'

	id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')
	blog_id = StringField(column_type='varchar(50)')
	user_id = StringField(column_type='varchar(50)')
	user_name = StringField(column_type='varchar(50)')
	user_image = StringField(column_type='varchar(500)')
	content = TextField()
	created_at = FloatField(default=time.time)