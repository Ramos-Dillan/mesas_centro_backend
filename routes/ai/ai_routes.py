from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.ai import ai_controller

ai_bp = Blueprint("ai_bp", __name__)


@ai_bp.route("/recommend", methods=["POST"])
@jwt_required()
def recommend_route():
    image = request.files.get("image")
    preferences = request.form.get("preferences")  
    user_id = get_jwt_identity()
    return ai_controller.recommend(image, user_id, preferences=preferences)


@ai_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():

    body = request.get_json(silent=True) or {}

    room_id = body.get("room_id")
    message = body.get("message")
    conversation_id = body.get("conversation_id")
    user_id = get_jwt_identity()

    if not message:
        return {
            "message": "El mensaje no puede estar vacío."
        }, 400

    return ai_controller.chat(room_id, message, conversation_id, user_id)