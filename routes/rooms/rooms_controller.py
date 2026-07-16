from common.http import ok, bad_request
from routes.rooms import rooms_service


def getAll():

    data, err = rooms_service.getAll()

    if err:
        return bad_request(
            message="Error obteniendo salas",
            errors=err
        )

    return ok(
        data=data,
        message="Salas obtenidas correctamente."
    )


def getById(id):

    data, err = rooms_service.getById(id)

    if err:
        return bad_request(
            message="Sala no encontrada",
            errors=err
        )

    return ok(
        data=data,
        message="Sala obtenida correctamente."
    )


def upload(image, user_id):

    if image is None:

        return bad_request(
            message="Debe enviar una imagen."
        )

    data, err = rooms_service.upload(image, user_id)

    if err:

        return bad_request(
            message="Error subiendo imagen.",
            errors=err
        )

    return ok(
        data=data,
        message="Imagen subida correctamente."
    )


def delete(id):

    result, err = rooms_service.delete(id)

    if err:

        return bad_request(
            message="Error eliminando sala",
            errors=err
        )

    return ok(
        data={"deleted": result},
        message="Sala eliminada correctamente."
    )