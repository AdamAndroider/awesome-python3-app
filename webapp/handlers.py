from webapp.core_web import get
from webapp.models import User


@get('/')
async def index_test(request):
	users = await User.findAll()
	return {'__template__': 'html_test.html', 'users': users}