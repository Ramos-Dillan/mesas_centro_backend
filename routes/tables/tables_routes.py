from flask import Blueprint, request
from routes.tables import tables_controller


table_bp = Blueprint("table_bp", __name__)


@table_bp.route("", methods=["GET"], strict_slashes=False)
@table_bp.route("/", methods=["GET"], strict_slashes=False)
@table_bp.route("/getAll", methods=["GET"], strict_slashes=False)
def getAll():
    return tables_controller.getAll()


@table_bp.route("/get/<int:id>", methods=["GET"], strict_slashes=False)
def getById(id):
    return tables_controller.getById(id)


@table_bp.route("", methods=["POST"], strict_slashes=False)
@table_bp.route("/", methods=["POST"], strict_slashes=False)
@table_bp.route("/create", methods=["POST"], strict_slashes=False)
def create():
    if request.is_json:
        data = request.get_json()
        image = None
    else:
        data = request.form.to_dict()
        image = request.files.get("image")

    return tables_controller.create(data, image)


@table_bp.route("/update/<int:id>", methods=["PUT"], strict_slashes=False)
def update(id):
    if request.is_json:
        data = request.get_json()
        image = None
    else:
        data = request.form.to_dict()
        image = request.files.get("image")

    return tables_controller.update(id, data, image)


@table_bp.route("/delete/<int:id>", methods=["DELETE"], strict_slashes=False)
def delete(id):
    return tables_controller.delete(id)