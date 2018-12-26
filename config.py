import os
import logging
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

BASEDIR = os.path.abspath(os.path.dirname(__file__))
SQLITE_DB = 'sqlite:///' + os.path.join(BASEDIR, 'db.sqlite')


class BaseConfig:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'SECRET_KEY'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOGGING_LOCATION = os.getenv('LOGGING_LOCATION')
    LOGGING_LEVEL = logging.DEBUG
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or SQLITE_DB
    BROKER_URL = os.environ.get('REDIS_URL') or 'redis://redis:6379/0'
    CELERY_SEND_TASK_SENT_EVENT = True
    CELERY_BROKER_URL = BROKER_URL
    CELERY_RESULT_BACKEND = BROKER_URL


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True


class TestingConfig(BaseConfig):
    """Testing configuration"""
    DEBUG = True
    TESTING = True


class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
