from common.http import ok, bad_request
from routes.ai import ai_service


def recommend(image, user_id, preferences=None):

    data, err = ai_service.recommend(image, user_id, preferences=preferences)

    if err:
        return bad_request(
            message="Error analizando la sala",
            errors=err
        )

    return ok(
        data=data,
        message="Recomendación generada correctamente."
    )


def chat(room_id, message, conversation_id, user_id):

    data, err = ai_service.chat(room_id, message, conversation_id, user_id)

    if err:
        return bad_request(
            message="Error respondiendo tu mensaje",
            errors=err
        )

    return ok(
        data=data,
        message="Respuesta generada correctamente."
    )