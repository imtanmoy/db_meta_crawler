import logging
import os

from flask import Flask, make_response, request
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

from config import config

celery = Celery()
db = SQLAlchemy()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('CONFIG', 'development')
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    celery.config_from_object(app.config)

    print(app.config['SQLALCHEMY_DATABASE_URI'])
    print(os.environ.get('DATABASE_URL'))

    # set config
    configure_app(app)
    # set up extensions
    setup_extensions(app)
    # register blueprints
    register_endpoints(app)

    return app


def register_endpoints(app):
    @app.route('/status', methods=['GET'])
    @app.route('/health', methods=['GET'])
    def status():
        return 'OK'

    from .api.routes import api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    @app.errorhandler(404)
    def page_not_found(error):
        app.logger.error('Page not found: %s', request.path)
        return make_response(jsonify({
            'message': f'{str(error)}'
        })), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error('Server Error: %s', error)
        return make_response(jsonify({
            'message': f'{str(error)}'
        })), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        return make_response(jsonify({
            'message': f'{str(e)}'
        })), 500


def setup_extensions(app):
    db.init_app(app)


def configure_app(app):
    app.url_map.strict_slashes = False
    # Configure logging
    handler = logging.FileHandler(app.config['LOGGING_LOCATION'])
    handler.setLevel(app.config['LOGGING_LEVEL'])
    formatter = logging.Formatter(app.config['LOGGING_FORMAT'])
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
