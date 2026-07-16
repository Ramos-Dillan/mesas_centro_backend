from typing import Any, Tuple, Dict, Optional
from contextlib import contextmanager
from datetime import datetime, timedelta
import secrets
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from db.db import SessionLocal
from db.models import User
from werkzeug.security import check_password_hash, generate_password_hash


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _send_reset_email(to_email: str, reset_link: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)
    frontend_name = os.getenv("APP_NAME", "Mesas de Centro")

    subject = f"{frontend_name} - Restablecer contraseña"

    html = f"""
    <div style="font-family: Arial, sans-serif; line-height:1.5">
      <h2>Restablecer contraseña</h2>
      <p>Recibimos una solicitud para restablecer tu contraseña.</p>
      <p>
        <a href="{reset_link}" target="_blank"
           style="display:inline-block;padding:12px 18px;background:#2563eb;color:#fff;text-decoration:none;border-radius:8px;">
          Crear nueva contraseña
        </a>
      </p>
      <p>Este enlace expira en 1 hora.</p>
      <p>Si no pediste este cambio, ignora este correo.</p>
    </div>
    """

    if not smtp_host or not smtp_user or not smtp_pass:
        print(f"[DEV] Password reset link for {to_email}: {reset_link}")
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    return True


# =========================
# REGISTER
# =========================
def create_user(data: Dict[str, Any]) -> Tuple[Optional[dict], Any]:
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not username or not email or not password:
        return None, {"message": "Todos los campos son requeridos"}

    with get_db() as db:
        if db.query(User).filter(User.username == username).first():
            return None, {"message": "El username ya existe"}

        if db.query(User).filter(User.email == email).first():
            return None, {"message": "El correo ya existe"}

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user.to_dict(), None


# =========================
# LOGIN
# =========================
def login_user(data: Dict[str, Any]) -> Tuple[Optional[dict], Any]:
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return None, {"message": "Email y password requeridos"}

    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None, {"message": "Usuario no encontrado"}

        if not check_password_hash(user.password, password):
            return None, {"message": "Password incorrecto"}

        return user.to_dict(), None


# =========================
# GET USERS
# =========================
def get_all_users():
    try:
        with get_db() as db:
            users = db.query(User).order_by(User.id.asc()).all()
            return [u.to_dict() for u in users], None

    except Exception as e:
        return None, {"message": str(e)}


# =========================
# UPDATE USER
# =========================
def update_user(user_id: int, data: Dict[str, Any]):
    try:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return None, {"message": "Usuario no encontrado"}

            if "username" in data:
                user.username = data["username"]

            if "email" in data:
                user.email = data["email"]

            db.commit()
            db.refresh(user)

            return user.to_dict(), None

    except Exception as e:
        return None, {"message": str(e)}


# =========================
# DELETE USER
# =========================
def delete_user(user_id: int):
    try:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return None, {"message": "Usuario no encontrado"}

            db.delete(user)
            db.commit()

            return {"message": "Usuario eliminado correctamente"}, None

    except Exception as e:
        return None, {"message": str(e)}


# =========================
# FORGOT PASSWORD
# =========================
def forgot_password(data: Dict[str, Any]) -> Tuple[Optional[dict], Any]:
    email = (data.get("email") or "").strip().lower()

    if not email:
        return None, {"message": "Email requerido"}

    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return {"message": "Si el correo existe, recibirás instrucciones"}, None

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        user.reset_token = token
        user.reset_token_expires = expires_at
        db.commit()

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:4200")
        reset_link = f"{frontend_url}/reset-password?token={token}"

        _send_reset_email(email, reset_link)

        return {"message": "Si el correo existe, recibirás instrucciones"}, None


# =========================
# RESET PASSWORD
# =========================
def reset_password(data: Dict[str, Any]) -> Tuple[Optional[dict], Any]:
    token = (data.get("token") or "").strip()
    new_password = (data.get("password") or "").strip()

    if not token or not new_password:
        return None, {"message": "Token y nueva contraseña son requeridos"}

    with get_db() as db:
        user = db.query(User).filter(User.reset_token == token).first()

        if not user:
            return None, {"message": "Token inválido"}

        if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
            return None, {"message": "Token expirado"}

        user.password = generate_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()

        return {"message": "Contraseña actualizada correctamente"}, None