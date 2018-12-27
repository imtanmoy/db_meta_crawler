import os
import random
import time
import pprint
from flask import current_app
from celery.signals import task_postrun
from celery.utils.log import get_task_logger

from app import celery, db
from app.models.database import Database
from app.models.message import Message

logger = get_task_logger(__name__)


@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}


@celery.task
def log(message):
    """Print some log messages"""
    logger.debug(message)
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)


@celery.task
def reverse_messages():
    """Reverse all messages in DB"""
    print('calling')
    for message in Message.query.all():
        print(message.text)
        words = message.text.split()
        message.text = " ".join(reversed(words))
        db.session.commit()


@celery.task
def save_metadata(db_id):
    """Reverse all messages in DB"""
    print('calling save meta data')
    pprint.pprint(db_id)
    database = Database.query.get(db_id)
    tables = database.save_remote_tables
    for table in tables:
        columns = table.save_remote_columns


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    db.session.remove()
