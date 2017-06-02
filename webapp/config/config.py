from webapp.config import config_default


'''Default configurations.
'''

__author__ = 'Adam Lee'


class Dict(dict):

	'''Simple dict but support access as x.y style.
	'''

	def __init__(self, names=(), values=(), **kw):
		super(Dict, self).__init__(**kw)
		for key, value in zip(names, values):
			self[key] = value

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no attribute '{}'".format(key))

	def __setattr__(self, key, value):
		self[key] = value


def merge(default, override):
	d = {}
	for key, value in default.items():
		if key in override:
			if isinstance(value, dict):
				d[key] = merge(value, override[key])
			else:
				d[key] = override[key]
		else:
			d[key] = value
	return d


def toDict(dic):
	di = Dict()
	for key, value in dic.items():
		di[key] = toDict(value) if isinstance(value, dict) else value
	return di

configs = config_default.configs

try:
	from webapp.config import config_override
	configs = merge(configs, config_override.configs)
except ImportError:
	pass

configs = toDict(configs)