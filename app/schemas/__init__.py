from functools import wraps

from flask import request
from flask.json import jsonify
from jsonschema import Draft4Validator


def validate_schema(schema):
    """Decorator that performs schema validation on the JSON post data in
    the request and returns an error response if validation fails.  It
    calls the decorated function if validation succeeds.
    :param schema: Schema that represents the expected input.
    """
    validator = Draft4Validator(schema)

    def wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            post_data = request.get_json(force=True)
            errors = {}
            for error in validator.iter_errors(post_data):
                errors[error.path[0]] = error.message
            if errors:
                response = jsonify(dict(success=False,
                                        message="invalid input",
                                        errors=errors))
                response.status_code = 406
                return response
            else:
                return fn(*args, **kwargs)

        return wrapped

    return wrapper
