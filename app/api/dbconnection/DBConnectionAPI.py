from flask import request, make_response, jsonify, current_app, url_for
from flask.views import MethodView
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
            database = Database(dbtype=post_data['dbtype'], username=post_data['username'],
                                password=post_data['password'], hostname=post_data['hostname'],
                                dbname=post_data['dbname'])
            db.session.add(database)
            db.session.commit()
            task = save_metadata.delay(database.id)
            return make_response(jsonify({'data': database.to_json, 'task': {'task_id': task.task_id}, '_links': {
                'task': url_for('api.task_progress_api', task_id=task.id, _external=True)
            }})), 201
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
