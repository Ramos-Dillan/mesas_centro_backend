from flask import Blueprint
from routes.recommendations import recommendations_controller

recommendation_bp = Blueprint(
    "recommendation_bp",
    __name__
)


@recommendation_bp.route("/getAll", methods=["GET"])
def getAll():
    return recommendations_controller.getAll()


@recommendation_bp.route("/get/<int:id>", methods=["GET"])
def getById(id):
    return recommendations_controller.getById(id)


@recommendation_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete(id):
    return recommendations_controller.delete(id)