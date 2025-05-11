import environ
from dotenv import load_dotenv


load_dotenv()

env = environ.Env(DEBUG=(bool, False), TEST=(bool, False))


from ._base import *  # noqa


TEST = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '[::1]',
    'testserver',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
