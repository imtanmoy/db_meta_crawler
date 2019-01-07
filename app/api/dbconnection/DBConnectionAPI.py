from flask import request, make_response, jsonify, current_app, url_for
from flask.views import MethodView
from sqlalchemy import create_engine, select, exc
from app.models.database import Database
from app import db
from app.tasks.task import save_metadata


class DBConnectionAPI(MethodView):
    """
    DBConnection Registration Resource
    """

    def post(self):
        try:
            post_data = request.get_json()
            ping = ping_database_connection(dbtype=post_data['dbtype'], username=post_data['username'],
                                            password=post_data['password'], hostname=post_data['hostname'],
                                            db_name=post_data['dbname'])
            if ping is 1:
                database = Database(dbtype=post_data['dbtype'], username=post_data['username'],
                                    password=post_data['password'], hostname=post_data['hostname'],
                                    dbname=post_data['dbname'])
                db.session.add(database)
                db.session.commit()
                task = save_metadata.delay(database.id)
                return make_response(jsonify({'data': database.to_json, 'task': {'task_id': task.task_id}, '_links': {
                    'task': url_for('api.task_progress_api', task_id=task.id, _external=True)
                }})), 201
        except exc.DBAPIError as e:
            current_app.logger.error(str(e))
            msg = str(e.orig.args[1]).split('(')[0].rstrip(' ')
            response_object = {
                'status': 'fail',
                'message': 'Some error occurred. Please try again.',
                'reason': f'{msg}'
            }
            return make_response(jsonify(response_object)), 401
        # except exc.IntegrityError as e:
        #     # current_app.logger.error(str(e.orig.args))
        #     msg = str(e.orig.args[1]).split('(')[0].rstrip(' ')
        #     response_object = {
        #         'status': 'fail',
        #         'message': 'Some error occurred. Please try again.',
        #         'reason': f'{msg}'
        #     }
        #     return make_response(jsonify(response_object)), 401
        except Exception as e:
            current_app.logger.error(str(e))
            response_object = {
                'status': 'fail',
                'message': 'Some error occurred. Please try again.',
                'reason': f'{e}'
            }
            return make_response(jsonify(response_object)), 401

    def get(self, db_id):
        try:
            database = Database.query.get(db_id)
            return make_response(jsonify(database.to_json)), 200
        except Exception as e:
            current_app.logger.error(str(e))
            response_object = {
                'status': 'fail',
                'message': 'Some error occurred. Please try again.',
                'reason': f'{e}'
            }
            return make_response(jsonify(response_object)), 401


# define the API resources
dbconnection_view = DBConnectionAPI.as_view('dbconnection_api')


def create_sqlalchemy_uri(sqlalchemy_driver, username, password, hostname, db_name):
    return sqlalchemy_driver + "://" + username + ":" + password + "@" + hostname + "/" \
           + db_name


def create_sqla_engine(url):
    return create_engine(url, isolation_level='READ UNCOMMITTED', pool_pre_ping=True)


def create_sqlalchemy_driver(dbtype):
    if dbtype == 'mysql':
        return 'mysql'
    elif dbtype == 'mssql':
        return 'mssql+pymssql'
    elif dbtype == 'postgresql':
        return 'postgresql+psycopg2'
    else:
        return None


def ping_database_connection(dbtype, username, password, hostname, db_name):
    driver = create_sqlalchemy_driver(dbtype)
    url = create_sqlalchemy_uri(driver, username, password, hostname, db_name)
    engine = create_sqla_engine(url)
    connection = engine.connect()
    save_should_close_with_result = connection.should_close_with_result
    connection.should_close_with_result = False

    try:
        return connection.scalar(select([1]))
    except exc.DBAPIError as err:
        if err.connection_invalidated:
            connection.scalar(select([1]))
        else:
            raise
    finally:
        # restore "close with result"
        connection.should_close_with_result = save_should_close_with_result
        connection.close()
