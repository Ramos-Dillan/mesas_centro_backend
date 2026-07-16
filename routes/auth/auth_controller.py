from routes.auth import auth_service
from common.http import ok, bad_request, unauthorized, created
from flask_jwt_extended import create_access_token


def create_user(data):
    user, err = auth_service.create_user(data)

    if err:
        return bad_request(message=err["message"])

    return created(
        data=user,
        message="Usuario creado correctamente"
    )


def login_user(data):
    user, err = auth_service.login_user(data)

    if err:
        return unauthorized(message=err["message"])

    token = create_access_token(identity=str(user["id"]))

    return ok(
        data={
            "access_token": token,
            "user": user
        },
        message="Login exitoso"
    )


def get_users():
    try:
        users, err = auth_service.get_all_users()

        if err:
            return bad_request(message=err["message"])

        return ok(data=users)

    except Exception as e:
        return bad_request(message=str(e))


def update_user(user_id, data):
    user, err = auth_service.update_user(user_id, data)

    if err:
        return bad_request(message=err["message"])

    return ok(data=user, message="Usuario actualizado")


def delete_user(user_id):
    res, err = auth_service.delete_user(user_id)

    if err:
        return bad_request(message=err["message"])

    return ok(data=res, message="Usuario eliminado")


def forgot_password(data):
    res, err = auth_service.forgot_password(data)

    if err:
        return bad_request(message=err["message"])

    return ok(data=res, message=res["message"])


def reset_password(data):
    res, err = auth_service.reset_password(data)

    if err:
        return bad_request(message=err["message"])

    return ok(data=res, message=res["message"])