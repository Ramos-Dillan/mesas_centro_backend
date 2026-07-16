from common.http import ok, bad_request
from routes.recommendations import recommendations_service


def getAll():

    data, err = recommendations_service.getAll()

    if err:
        return bad_request(
            message="Error obteniendo recomendaciones",
            errors=err
        )

    return ok(
        data=data,
        message="Recomendaciones obtenidas correctamente."
    )


def getById(id):

    data, err = recommendations_service.getById(id)

    if err:
        return bad_request(
            message="Error obteniendo recomendación",
            errors=err
        )

    return ok(
        data=data,
        message="Recomendación obtenida correctamente."
    )


def delete(id):

    result, err = recommendations_service.delete(id)

    if err:
        return bad_request(
            message="Error eliminando recomendación",
            errors=err
        )

    return ok(
        data={"deleted": result},
        message="Recomendación eliminada correctamente."
    )