import cloudinary
import cloudinary.uploader
from config import Config
import os
import uuid
from contextlib import contextmanager

cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

from db.db import SessionLocal
from db.models import Table


UPLOAD_FOLDER = "static/uploads/tables"


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}



def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )



def parse_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on")
    return bool(value)



@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def getAll():
    try:
        with get_db() as db:
            tables = db.query(Table).order_by(Table.id).all()
            return [table.to_dict() for table in tables], None
    except Exception as e:
        return None, str(e)



def getById(id):
    try:
        with get_db() as db:
            table = db.query(Table).filter(Table.id == id).first()
            if not table:
                return None, "Table not found"
            return table.to_dict(), None
    except Exception as e:
        return None, str(e)



def _save_image(image):
    if not allowed_file(image.filename):
        raise ValueError("Solo se permiten imágenes PNG, JPG, JPEG o WEBP.")

    try:
        result = cloudinary.uploader.upload(
            image,
            folder="mesas_centro/tables"
        )
        return result["secure_url"]
    except Exception as e:
        raise ValueError(f"Error subiendo imagen a Cloudinary: {str(e)}")



def create(data, image):
    try:
        image_path = data.get("image_url")

        if image is not None and image.filename != "":
            try:
                image_path = _save_image(image)
            except ValueError as ve:
                return None, str(ve)

        if not image_path:
            return None, "Debe enviar una imagen o un image_url."

        is_active_value = parse_bool(data.get("is_active"), default=True)

        with get_db() as db:
            table = Table(
                name=data.get("name"),
                style=data.get("style"),
                material=data.get("material"),
                color=data.get("color"),
                shape=data.get("shape"),
                width=data.get("width"),
                depth=data.get("depth"),
                height=data.get("height"),
                price=data.get("price"),
                description=data.get("description"),
                image_url=image_path,
                is_active=is_active_value
            )

            db.add(table)
            db.commit()
            db.refresh(table)

            return table, None

    except Exception as e:
        return None, str(e)



def update(id, data, image=None):
    try:
        with get_db() as db:
            table = db.query(Table).filter(Table.id == id).first()

            if not table:
                return None, "Table not found"

            image_path = table.image_url

            if image is not None and image.filename != "":
                try:
                    image_path = _save_image(image)
                except ValueError as ve:
                    return None, str(ve)

            table.name = data.get("name", table.name)
            table.style = data.get("style", table.style)
            table.material = data.get("material", table.material)
            table.color = data.get("color", table.color)
            table.shape = data.get("shape", table.shape)

            shape_value = (data.get("shape", table.shape) or "").strip().lower()
            is_round = shape_value == "redonda"

            if is_round:
                table.width = None
                table.depth = None
                table.diameter = data.get("diameter", table.diameter)
            else:
                table.width = data.get("width", table.width)
                table.depth = data.get("depth", table.depth)
                table.diameter = None

            table.height = data.get("height", table.height)
            table.price = data.get("price", table.price)
            table.description = data.get("description", table.description)
            table.image_url = image_path

            if "is_active" in data:
                table.is_active = parse_bool(data.get("is_active"), default=table.is_active)

            db.commit()
            db.refresh(table)

            return table.to_dict(), None

    except Exception as e:
        return None, str(e)



def delete(id):
    try:
        with get_db() as db:
            table = db.query(Table).filter(Table.id == id).first()

            if not table:
                return False, "Table not found"

            db.delete(table)
            db.commit()

            return True, None

    except Exception as e:
        return False, str(e)



def getActive():
    try:
        with get_db() as db:
            tables = (
                db.query(Table)
                .filter(Table.is_active == True)
                .order_by(Table.id)
                .all()
            )
            return tables, None
    except Exception as e:
        return None, str(e)
