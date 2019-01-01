import os
import random
import time
import pprint
from flask import current_app
from celery.signals import task_postrun, worker_process_init, task_prerun
from celery.utils.log import get_task_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from app import celery, db, create_app
from app.models.column import Column
from app.models.database import Database
from app.models.foreignkey import ForeignKey
from app.models.message import Message
from app.models.table import Table

logger = get_task_logger(__name__)

Session = scoped_session(sessionmaker(autocommit=False, autoflush=False))


class SQLASessionTask(celery.Task):
    _session = None

    def __call__(self, *args, **kwargs):
        print("CALLED!")
        return super(SQLASessionTask, self).__call__(*args, **kwargs)

    @property
    def session(self):
        app = current_app
        print(app.config['SQLALCHEMY_DATABASE_URI'])
        if self._session is None:
            engine = create_engine(
                app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True, echo_pool=True)
            self._session = Session(bind=engine)
        return self._session

    def on_success(self, retval, task_id, args, kwargs):
        print('success')
        Session.remove()
        # pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('failure')
        Session.remove()
        # pass


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


@celery.task(base=SQLASessionTask, bind=True)
def save_metadata(self, db_id):
    """saving all meta data from database conn"""
    db_session = self.session
    # database = Database.query.get(db_id)
    database = db_session.query(Database).get(db_id)
    # tables = database.save_remote_tables
    new_tables = []
    time.sleep(1)
    total = 0
    current = 0
    message = 'pending'
    self.update_state(state='PROGRESS',
                      meta={'current': current, 'total': total,
                            'status': message})
    # pprint.pprint('Total Tables in database--->')
    # pprint.pprint(len(database.get_remote_tables))
    total = total + len(database.get_remote_tables)
    self.update_state(state='PROGRESS',
                      meta={'current': current, 'total': total,
                            'status': message})
    for tt in database.get_remote_tables:
        table_db = Table(table_name=getattr(tt, 'name'))
        database.tables.append(table_db)
        db_session.add(table_db)
        db_session.commit()
        new_tables.append(table_db)
        time.sleep(1)
        current += 1
        self.update_state(state='PROGRESS',
                          meta={'current': current, 'total': total,
                                'status': message})
    for table in new_tables:
        # pprint.pprint('Total Columns in a table---->')
        # pprint.pprint(len(table.get_remote_columns))
        total = total + len(table.get_remote_columns)
        self.update_state(state='PROGRESS',
                          meta={'current': current, 'total': total,
                                'status': message})
        for column in table.get_remote_columns:
            ncol = Column(column_name=getattr(column, 'name'),
                          column_type=getattr((getattr(column, 'type')), '__visit_name__'),
                          column_default=getattr(column, 'default'),
                          is_nullable=getattr(column, 'nullable'),
                          is_autoincrement=False if getattr(column, 'autoincrement') == 'auto' else True,
                          is_pk=getattr(column, 'primary_key'))
            table.columns.append(ncol)
            db_session.add(ncol)
            db_session.commit()
            time.sleep(1)
            fks = getattr(column, 'foreign_keys')
            if len(fks) > 0:
                parent = str(getattr(next(iter(fks)), '_colspec')).split('.')[0]
                # parent_table = Table.query.filter_by(table_name=parent, database_id=db_id).first()
                parent_table = db_session.query(Table).filter(Table.table_name == parent,
                                                              Table.database_id == db_id).first()
                # scol = Column.query.filter_by(column_name=ncol.column_name, table_id=parent_table.id).first()
                scol = db_session.query(Column).filter(Column.column_name == ncol.column_name,
                                                       Column.table_id == parent_table.id).first()
                fk_key = ForeignKey(column_id=ncol.id, table_id=ncol.table_id, referred_column_id=scol.id,
                                    referred_table_id=scol.table_id)
                db_session.add(fk_key)
                db_session.commit()
            current += 1
            self.update_state(state='PROGRESS',
                              meta={'current': current, 'total': total,
                                    'status': message})
    return {'current': current, 'total': total, 'status': 'completed',
            'result': database.id}


@task_postrun.connect
def close_session(*args, **kwargs):
    # Flask SQLAlchemy will automatically create new sessions for you from
    # a scoped session factory, given that we are maintaining the same app
    # context, this ensures tasks have a fresh session (e.g. session errors
    # won't propagate across tasks)
    print('removing session')
    # db.session.remove()


@task_prerun.connect
def pre_run(*args, **kwargs):
    print('before run')


@worker_process_init.connect
def init_celery_flask_app(**kwargs):
    print('worker init')
    # app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    # app.app_context().push()
