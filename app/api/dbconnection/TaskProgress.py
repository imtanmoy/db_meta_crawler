from flask import request, make_response, jsonify, current_app
from flask.views import MethodView
from app.models.database import Database
from app import db
from app.tasks.task import save_metadata


class TaskProgress(MethodView):
    """
    DBConnection Registration Resource
    """

    def get(self, task_id):
        try:
            task = save_metadata.AsyncResult(task_id)
            if task.state == 'PENDING':
                # job did not start yet
                response = {
                    'state': task.state,
                    'status': 'Pending...'
                }
            elif task.state != 'FAILURE':
                response = {
                    'state': task.state,
                    'current': task.info.get('current', 0),
                    'total': task.info.get('total', 1),
                    'status': task.info.get('status', '')
                }
                if 'result' in task.info:
                    response['result'] = task.info['result']
            else:
                # something went wrong in the background job
                response = {
                    'state': task.state,
                    'current': 1,
                    'total': 1,
                    'status': str(task.info),  # this is the exception raised
                }
            return make_response(jsonify(response)), 200
        except Exception as e:
            current_app.logger.error(str(e))
            response_object = {
                'status': 'fail',
                'message': 'Some error occurred. Please try again.',
                'reason': f'{e}'
            }
            return make_response(jsonify(response_object)), 401


# define the API resources
task_progress_view = TaskProgress.as_view('task_progress_api')
