from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, url_for
from app.tasks.task import long_task, reverse_messages
from app.models.message import Message
from app import db

api_blueprint = Blueprint('api', __name__)


@api_blueprint.before_app_first_request
def init_db():
    db.create_all()


@api_blueprint.route('/status', methods=['GET'])
def ping_pong():
    return jsonify({
        'status': 'success',
        'message': 'pong!'
    })


@api_blueprint.route("/ip", methods=["GET"])
def get_my_ip():
    return jsonify({'ip': request.environ.get('HTTP_X_REAL_IP', request.remote_addr)}), 200


@api_blueprint.route('/')
def longtask():
    """add a new task and start running it after 10 seconds"""
    eta = datetime.utcnow() + timedelta(seconds=10)
    task = long_task.apply_async(eta=eta)
    return jsonify({
        '_links': {
            'task': url_for('api.taskstatus', task_id=task.id, _external=True)
        }
    }), 202


@api_blueprint.route('/status/<task_id>/', methods=['GET', 'POST'])
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
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
    return jsonify(response)


@api_blueprint.route('/messages/')
def messages():
    task = reverse_messages.apply_async()
    messages = Message.query.all()
    return jsonify([message.text for message in messages])
