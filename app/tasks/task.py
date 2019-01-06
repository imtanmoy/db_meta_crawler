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
    total = 100
    current = 0
    message = 'pending'
    db_session = self.session
    self.update_state(state='PROGRESS',
                      meta={'current': current, 'total': total,
                            'status': message})
    try:
        # database = Database.query.get(db_id)
        database = db_session.query(Database).get(db_id)
        total = prepare_metadata(database)
        new_tables = []
        self.update_state(state='PROGRESS',
                          meta={'current': current, 'total': total,
                                'status': message})
        for table_name in database.get_remote_tables():
            table_db = save_table(table_name, database, db_session)
            new_tables.append(table_db)
            current += 1
            self.update_state(state='PROGRESS',
                              meta={'current': current, 'total': total,
                                    'status': message})
        for table in new_tables:
            columns = []
            for column in database.get_remote_columns(table_name=table.table_name):
                new_column = save_column(column, table, db_session)
                columns.append(new_column)
                current += 1
                self.update_state(state='PROGRESS',
                                  meta={'current': current, 'total': total,
                                        'status': message})
            for pk in database.get_remote_primary_keys(table_name=table.table_name):
                pk_column = db_session.query(Column).filter(Column.column_name == pk,
                                                            Column.table_id == table.id).first()
                pk_column.is_pk = True
                db_session.add(pk_column)
                db_session.commit()
                current += 1
                self.update_state(state='PROGRESS',
                                  meta={'current': current, 'total': total,
                                        'status': message})

            for fk in database.get_remote_foreign_keys(table_name=table.table_name):
                fk_column = db_session.query(Column).filter(Column.column_name == fk['constrained_columns'][0],
                                                            Column.table_id == table.id).first()
                fk_column.is_fk = True
                db_session.add(fk_column)
                db_session.commit()
                current += 1
                self.update_state(state='PROGRESS',
                                  meta={'current': current, 'total': total,
                                        'status': message})

        for table in new_tables:
            for column in table.columns:
                if column.is_fk is True:
                    for fk in database.get_remote_foreign_keys(table_name=table.table_name):
                        if column.column_name == fk['constrained_columns'][0]:
                            referred_table = db_session.query(Table).filter(Table.table_name == fk['referred_table'],
                                                                            Table.database_id == database.id) \
                                .first()
                            referred_column = db_session.query(Column) \
                                .filter(Column.column_name == fk['referred_columns'][0],
                                        Column.table_id == referred_table.id).first()
                            fk_key = ForeignKey(column_id=column.id, table_id=column.table_id,
                                                referred_column_id=referred_column.id,
                                                referred_table_id=referred_table.id)
                            db_session.add(fk_key)
                            db_session.commit()
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


def save_table(table_name, database, session):
    table_db = Table(table_name=table_name)
    database.tables.append(table_db)
    session.add(table_db)
    session.commit()
    return table_db


def save_column(column, table, session):
    ncol = Column(column_name=str(column.get('name', 'default_column_name')),
                  column_type=str(getattr(column.get('type'), '__visit_name__')),
                  column_default=column.get('default', None),
                  is_nullable=bool(column.get('nullable', True)),
                  is_autoincrement=bool(column.get('autoincrement', False)))
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


def prepare_metadata(database):
    print('calculation')
    total = 0
    total = total + len(database.get_remote_tables())
    for table_name in database.get_remote_tables():
        total = total + len(database.get_remote_columns(table_name=table_name))
        total = total + len(database.get_remote_primary_keys(table_name=table_name))
        total = total + len(database.get_remote_foreign_keys(table_name=table_name)) * 2
    print('calculation done')
    return total
