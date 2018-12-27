import os
from dotenv import load_dotenv
from celery import Celery
# from celery.schedules import crontab
from app import create_app

# from app.tasks.task import log, reverse_messages


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')


def create_celery(app):
    celery = Celery(app.import_name,
                    backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = create_celery(app)

# @celery.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     # Calls reverse_messages every 10 seconds.
#     sender.add_periodic_task(10.0, reverse_messages, name='reverse every 10')
#
#     # Calls log('Logging Stuff') every 30 seconds
#     sender.add_periodic_task(30.0, log.s(('Logging Stuff')), name='Log every 30')
#
#     # Executes every Monday morning at 7:30 a.m.
#     sender.add_periodic_task(
#         crontab(hour=7, minute=30, day_of_week=1),
#         log.s('Monday morning log!'),
#     )
