from flask import request, make_response, jsonify, current_app
from flask.views import MethodView
from app.models.database import Database
from app import db
from app.tasks.task import save_metadata


class DBConnectionAPI(MethodView):
    """
    DBConnection Registration Resource
    """

    def post(self):
        post_data = request.get_json()
        try:
            database = Database(dbtype=post_data['dbtype'], username=post_data['username'],
                                password=post_data['password'], hostname=post_data['hostname'],
                                dbname=post_data['dbname'])
            db.session.add(database)
            db.session.commit()
            task = save_metadata.delay(database.id)
            return make_response(jsonify({'data': database.to_json, 'task_id': task.task_id})), 201
        except Exception as e:
            current_app.logger.error(str(e))
            response_object = {
                'status': 'fail',
                'message': 'Some error occurred. Please try again.',
                'reason': f'{e}'
            }
            return make_response(jsonify(response_object)), 401

    def get(self, db_id):
        database = Database.query.get(db_id)
        return make_response(jsonify(database.to_json)), 200


# define the API resources
dbconnection_view = DBConnectionAPI.as_view('dbconnection_api')
