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
        return super(SQLASessionTask, self).__call__(*args, **kwargs)

    @property
    def session(self):
        app = current_app
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
    total = 0
    current = 0
    message = 'pending'
    try:
        db_session = self.session
        # database = Database.query.get(db_id)
        database = db_session.query(Database).get(db_id)
        new_tables = []
        self.update_state(state='PROGRESS',
                          meta={'current': current, 'total': total,
                                'status': message})
        # pprint.pprint('Total Tables in database--->')
        total = total + len(database.get_remote_tables())
        self.update_state(state='PROGRESS',
                          meta={'current': current, 'total': total,
                                'status': message})
        for tt in database.get_remote_tables():
            table_db = save_table(tt, database, db_session)
            new_tables.append(table_db)
            current += 1
            self.update_state(state='PROGRESS',
                              meta={'current': current, 'total': total,
                                    'status': message})
        for table in new_tables:
            # pprint.pprint('Total Columns in a table---->')
            total = total + len(table.get_remote_columns())
            self.update_state(state='PROGRESS',
                              meta={'current': current, 'total': total,
                                    'status': message})
            for column in table.get_remote_columns():
                new_column = save_column(column, table, db_session)
                save_fk(column, new_column, db_id, db_session)
                current += 1
                self.update_state(state='PROGRESS',
                                  meta={'current': current, 'total': total,
                                        'status': message})
        return {'current': current, 'total': total, 'status': 'completed',
                'result': database.id}
    except Exception as e:
        current_app.logger.error(str(e))
        # return {'current': current, 'total': total, 'status': str(e),
        # 'result': db_id}
        raise e


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


def save_table(tt, database, session):
    table_db = Table(table_name=getattr(tt, 'name'))
    database.tables.append(table_db)
    session.add(table_db)
    session.commit()
    return table_db


def save_column(column, table, session):
    ncol = Column(column_name=getattr(column, 'name'),
                  column_type=getattr((getattr(column, 'type')), '__visit_name__'),
                  # column_default=str(getattr(column, 'default')),
                  column_default=None,
                  is_nullable=getattr(column, 'nullable'),
                  is_autoincrement=False if getattr(column, 'autoincrement') == 'auto' or getattr(column,
                                                                                                  'autoincrement') == True else True,
                  is_pk=getattr(column, 'primary_key'),
                  is_fk=True if len(getattr(column, 'foreign_keys')) > 0 else False)
    table.columns.append(ncol)
    session.add(ncol)
    session.commit()
    return ncol


def save_fk(column, new_column, db_id, session):
    fks = getattr(column, 'foreign_keys')
    if len(fks) > 0:
        parent = str(getattr(next(iter(fks)), '_colspec')).split('.')[0]
        # parent_table = Table.query.filter_by(table_name=parent, database_id=db_id).first()
        parent_table = session.query(Table).filter(Table.table_name == parent,
                                                   Table.database_id == db_id).first()
        # scol = Column.query.filter_by(column_name=ncol.column_name, table_id=parent_table.id).first()
        scol = session.query(Column).filter(Column.column_name == new_column.column_name,
                                            Column.table_id == parent_table.id).first()
        fk_key = ForeignKey(column_id=new_column.id, table_id=new_column.table_id, referred_column_id=scol.id,
                            referred_table_id=scol.table_id)
        session.add(fk_key)
        session.commit()
