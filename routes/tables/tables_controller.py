from common.http import ok, bad_request
from routes.tables import tables_service


def getAll():
    data, err = tables_service.getAll()

    if err:
        return bad_request(
            message="Error obteniendo mesas",
            errors=err
        )

    return ok(
        data=data,
        message="Mesas obtenidas correctamente."
    )


def getById(id):
    data, err = tables_service.getById(id)

    if err:
        return bad_request(
            message="Mesa no encontrada",
            errors=err
        )

    return ok(
        data=data,
        message="Mesa obtenida correctamente."
    )


def create(data, image):
    result, err = tables_service.create(data, image)

    if err:
        return bad_request(
            message="Error creando mesa",
            errors=err
        )

    return ok(
        data=result.to_dict(),
        message="Mesa creada correctamente."
    )


def update(id, data, image=None):
    result, err = tables_service.update(id, data, image)

    if err:
        return bad_request(
            message="Error actualizando mesa",
            errors=err
        )

    return ok(
        data=result,
        message="Mesa actualizada correctamente."
    )


def delete(id):
    result, err = tables_service.delete(id)

    if err:
        return bad_request(
            message="Error eliminando mesa",
            errors=err
        )

    return ok(
        data={"deleted": result},
        message="Mesa eliminada correctamente."
    )
