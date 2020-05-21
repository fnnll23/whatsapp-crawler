# default config
class BaseConfig(object):
    DEBUG = False
    SECRET_KEY = 'o9z1MB2kgXGv2SzLZxco4O3h2RVIfvkuBWHxRVCIKdOVGgT69tOyWrFUdqOuYy4'
    UPLOAD_FOLDER = './uploads'

# testing config
class DevelopmentConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    FLASK_ENV= 'development'


# production config
class ProductionConfig(BaseConfig):
    TESTING = False
    DEBUG = False
    