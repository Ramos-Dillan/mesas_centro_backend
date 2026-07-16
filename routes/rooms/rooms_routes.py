from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.rooms import rooms_controller

room_bp = Blueprint("room_bp", __name__)


@room_bp.route("/getAll", methods=["GET"])
@jwt_required()
def getAll():
    return rooms_controller.getAll()


@room_bp.route("/get/<int:id>", methods=["GET"])
@jwt_required()
def getById(id):
    return rooms_controller.getById(id)


@room_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload():
    image = request.files.get("image")
    user_id = get_jwt_identity()
    return rooms_controller.upload(image, user_id)


@room_bp.route("/delete/<int:id>", methods=["DELETE"])
@jwt_required()
def delete(id):
    return rooms_controller.delete(id)