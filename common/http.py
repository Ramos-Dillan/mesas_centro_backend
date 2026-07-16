from flask import jsonify

def ok(data=None, message="ok"):
    response = {
        "status": "success",
        "message": message,
        "data": data
    }
    return jsonify(response), 200


def created(data=None, message="created"):
    response = {
        "status": "success",
        "message": message,
        "data": data
    }
    return jsonify(response), 201


def bad_request(message="Bad Request", errors=None):
    response = {
        "status": "error",
        "message": message,
        "errors": errors
    }
    return jsonify(response), 400


def not_found(message="Not Found"):
    response = {
        "status": "error",
        "message": message
    }
    return jsonify(response), 404


def internal_server_error(message="Internal Server Error"):
    response = {
        "status": "error",
        "message": message
    }
    return jsonify(response), 500


def forbidden(message="Forbidden"):
    response = {
        "status": "error",
        "message": message
    }
    return jsonify(response), 403


def unauthorized(message="Unauthorized"):
    response = {
        "status": "error",
        "message": message
    }
    return jsonify(response), 401