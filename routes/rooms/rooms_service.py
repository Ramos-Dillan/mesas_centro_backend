import os
import uuid

from contextlib import contextmanager

from db.db import SessionLocal
from db.models import Room


UPLOAD_FOLDER = "static/uploads/rooms"

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

            rooms = db.query(Room).order_by(Room.id.desc()).all()

            return [room.to_dict() for room in rooms], None

    except Exception as e:

        return None, str(e)


def getById(id):

    try:

        with get_db() as db:

            room = db.query(Room).filter(Room.id == id).first()

            if not room:

                return None, "Room not found"

            return room.to_dict(), None

    except Exception as e:

        return None, str(e)


def upload(image, user_id):

    try:

        if image is None:
            return None, "Debe seleccionar una imagen."

        if image.filename == "":
            return None, "Debe seleccionar una imagen."

        if not allowed_file(image.filename):
            return None, "Solo se permiten imágenes PNG,JPG,JPEG,WEBP."

        if not user_id:
            return None, "Usuario no identificado."

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        extension = image.filename.rsplit(".", 1)[1].lower()

        filename = f"{uuid.uuid4()}.{extension}"

        filepath = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        image.save(filepath)

        with get_db() as db:

            room = Room(
                image_url=filepath,
                user_id=user_id
            )

            db.add(room)

            db.commit()

            db.refresh(room)

            return room.to_dict(), None

    except Exception as e:

        return None, str(e)


def delete(id):

    try:

        with get_db() as db:

            room = db.query(Room).filter(Room.id == id).first()

            if not room:

                return False, "Room not found"

            if room.image_url and os.path.exists(room.image_url):

                os.remove(room.image_url)

            db.delete(room)

            db.commit()

            return True, None

    except Exception as e:

        return False, str(e)