from flask import Blueprint, request
from routes.auth import auth_controller
from flask_jwt_extended import jwt_required  

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/create", methods=["POST"])
def create_user_route():
    data = request.get_json() or {}
    return auth_controller.create_user(data)

@auth_bp.route("/login", methods=["POST"])
def login_user_route():
    data = request.get_json() or {}
    return auth_controller.login_user(data)

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password_route():
    data = request.get_json() or {}
    return auth_controller.forgot_password(data)

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password_route():
    data = request.get_json() or {}
    return auth_controller.reset_password(data)

@auth_bp.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    print("🔥 GET USERS HIT")
    return auth_controller.get_users()

@auth_bp.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    data = request.get_json() or {}
    return auth_controller.update_user(user_id, data)

@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    return auth_controller.delete_user(user_id)