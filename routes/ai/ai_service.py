import os
import time
import uuid
import json
import base64
import traceback

from google import genai
from google.genai import types
from google.genai.errors import ServerError
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from config import Config
from db.db import SessionLocal
from db.models import Table

from routes.rooms import rooms_service
from routes.recommendations import recommendations_service

UPLOAD_FOLDER_ROOMS = "static/uploads/rooms"
UPLOAD_FOLDER_GENERATED = "static/uploads/generated"

client = genai.Client(api_key=Config.GEMINI_API_KEY)
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# Modelo de OpenAI usado para componer la mesa dentro de la foto de la sala.
OPENAI_IMAGE_MODEL = "gpt-image-1"

# Reintentos para la llamada de generación de imagen con OpenAI
OPENAI_MAX_RETRIES = 3


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def _get_active_tables():
    db = SessionLocal()
    try:
        return db.query(Table).filter(Table.is_active == True).all()
    finally:
        db.close()


def _get_table_by_id(table_id):
    db = SessionLocal()
    try:
        return db.query(Table).filter(Table.id == table_id).first()
    finally:
        db.close()


# Orden de modelos de Gemini a intentar (se usa solo para elegir la mejor
# mesa del catálogo y para el chat, NO para generar imágenes).
MODELS_TO_TRY = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]


def _generate_content_with_retry(contents, max_retries_per_model=3):
    """
    Llama a Gemini con reintentos y espera progresiva (backoff) cuando el
    modelo responde 503 (alta demanda temporal). Recorre MODELS_TO_TRY en
    orden: si un modelo se satura tras varios intentos, pasa al siguiente
    modelo de la lista antes de rendirse por completo.
    """
    last_error = None

    for model_index, model_name in enumerate(MODELS_TO_TRY):
        for attempt in range(max_retries_per_model):
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
            except ServerError as e:
                last_error = e
                if "UNAVAILABLE" in str(e) or "503" in str(e):
                    wait = min(2 ** attempt, 15)  # 1s, 2s, 4s (tope 15s)
                    print(f"⏳ {model_name} saturado (503), reintentando en {wait}s... (intento {attempt + 1}/{max_retries_per_model})")
                    time.sleep(wait)
                    continue
                raise

        is_last_model = model_index == len(MODELS_TO_TRY) - 1
        if not is_last_model:
            print(f"⚠️ {max_retries_per_model} intentos fallidos con {model_name}, probando con {MODELS_TO_TRY[model_index + 1]}...")

    # Se agotaron todos los modelos de la lista
    raise last_error


def _choose_best_table(room_image_path, tables):
    parts = [
        types.Part.from_bytes(
            data=open(room_image_path, "rb").read(),
            mime_type="image/jpeg"
        ),
        "Esta es la foto de la sala del cliente."
    ]

    catalog_desc = []
    for t in tables:
        parts.append(
            types.Part.from_bytes(
                data=open(t.image_url, "rb").read(),
                mime_type="image/jpeg"
            )
        )
        catalog_desc.append(
            f"ID {t.id}: {t.name}, estilo {t.style}, color {t.color}, "
            f"material {t.material}, medidas {t.width}x{t.depth}x{t.height}cm"
        )

    prompt = f"""
Eres un experto en diseño de interiores. Analiza la sala y compárala con estas mesas de centro:

{chr(10).join(catalog_desc)}

Responde SOLO con un JSON así, sin texto adicional:
{{"table_id": <id de la mejor mesa>, "score": <0-100>, "reason": "<explicación breve>"}}
"""
    parts.append(prompt)

    response = _generate_content_with_retry(parts)

    text = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(text)


def _generate_composite_image(room_image_path, best_table, output_path, extra_instructions=None):
    """
    Genera la imagen final usando la API de imágenes de OpenAI (gpt-image-1).

    Se le pasan dos imágenes de referencia (la sala y la mesa del catálogo)
    y un prompt pidiendo que componga la mesa dentro de la sala de forma
    realista (perspectiva, escala, iluminación y sombra coherentes con la
    foto original). A diferencia del enfoque anterior con Pillow+rembg,
    aquí toda la composición (recorte, iluminación, sombra, perspectiva)
    la resuelve el modelo.
    """
    prompt = f"""
Coloca la mesa de centro que aparece en la segunda imagen dentro de la sala
que aparece en la primera imagen, de forma fotorrealista.

Instrucciones:
- Ubica la mesa sobre el piso, en una posición natural dentro de la sala
  (por ejemplo, frente al sofá o en el centro del área de estar visible).
- Respeta la perspectiva, la escala y el punto de fuga de la foto original
  de la sala.
- Ajusta la iluminación, el color y las sombras de la mesa para que
  combinen con la luz de la sala.
- No modifiques el resto de la sala (paredes, muebles, piso, ventanas):
  debe seguir siendo reconociblemente la misma foto, solo con la mesa
  añadida.
- El resultado debe verse como una foto real, no como un render 3D ni un
  colage.
"""
    if extra_instructions:
        prompt += f"\nInstrucciones adicionales del cliente: {extra_instructions}\n"

    last_error = None

    for attempt in range(OPENAI_MAX_RETRIES):
        try:
            with open(room_image_path, "rb") as room_file, \
                 open(best_table.image_url, "rb") as table_file:

                room_file.name = os.path.basename(room_image_path)
                table_file.name = os.path.basename(best_table.image_url)

                result = openai_client.images.edit(
                    model=OPENAI_IMAGE_MODEL,
                    image=[room_file, table_file],
                    prompt=prompt,
                    size="auto",
                )

            image_base64 = result.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)

            with open(output_path, "wb") as f:
                f.write(image_bytes)

            return True

        except RateLimitError as e:
            last_error = e
            wait = min(2 ** attempt, 15)
            print(f"⏳ OpenAI saturado/rate-limited, reintentando en {wait}s... (intento {attempt + 1}/{OPENAI_MAX_RETRIES})")
            time.sleep(wait)
        except (APIConnectionError, APIError) as e:
            last_error = e
            print(f"⚠️ Error de OpenAI (intento {attempt + 1}/{OPENAI_MAX_RETRIES}): {repr(e)}")
            time.sleep(min(2 ** attempt, 15))
        except Exception as e:
            print("⚠️ No se pudo generar la imagen compuesta con OpenAI")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Detalle: {repr(e)}")
            traceback.print_exc()
            return False

    print(f"⚠️ Se agotaron los reintentos con OpenAI. Último error: {repr(last_error)}")
    return False


def recommend(image, user_id):
    try:
        if image is None or image.filename == "":
            return None, "Debe enviar una imagen."

        if not allowed_file(image.filename):
            return None, "Solo se permiten imágenes PNG, JPG, JPEG o WEBP."

        if not os.path.exists(UPLOAD_FOLDER_ROOMS):
            os.makedirs(UPLOAD_FOLDER_ROOMS)
        if not os.path.exists(UPLOAD_FOLDER_GENERATED):
            os.makedirs(UPLOAD_FOLDER_GENERATED)

        # 1. Guardar la sala (crea el registro Room con user_id)
        room_data, err = rooms_service.upload(image, user_id)
        if err:
            return None, err

        room_path = room_data["image_url"]

        # 2. Buscar mesas activas
        tables = _get_active_tables()
        if not tables:
            return None, "No hay mesas activas en el catálogo."

        # 3. Elegir la mejor con Gemini
        choice = _choose_best_table(room_path, tables)
        best_table = next((t for t in tables if t.id == choice["table_id"]), None)

        if not best_table:
            return None, "La IA no pudo identificar una mesa válida."

        # 4. Generar la imagen compuesta con OpenAI (gpt-image-1)
        generated_filename = f"{uuid.uuid4()}.png"
        generated_path = os.path.join(UPLOAD_FOLDER_GENERATED, generated_filename)

        generated_ok = _generate_composite_image(
            room_path, best_table, generated_path
        )

        # 5. Guardar la recomendación
        result, err = recommendations_service.create(
            room_id=room_data["id"],
            table_id=best_table.id,
            user_id=user_id,
            score=choice["score"],
            explanation=choice["reason"],
            generated_image=generated_path if generated_ok else None
        )

        if err:
            return None, err

        return result, None

    except json.JSONDecodeError:
        return None, "La IA no devolvió un formato válido, intenta de nuevo."
    except ServerError:
        traceback.print_exc()
        return None, "El servicio de IA está saturado en este momento. Intenta de nuevo en unos segundos."
    except Exception as e:
        traceback.print_exc()
        return None, str(e)


def _detect_image_edit_request(message):
    """
    Le pregunta a Gemini si el mensaje del cliente es un pedido de cambio
    VISUAL sobre la imagen ya generada (color, material, tamaño, posición,
    acabado, etc.) en vez de una pregunta normal de catálogo.

    Devuelve un dict {"is_image_edit": bool, "instruction": str}.
    Si algo falla, devuelve is_image_edit=False para no romper el flujo
    normal del chat.
    """
    prompt = f"""
Un cliente ya recibió una imagen generada de su sala con una mesa de centro
puesta. Analiza su siguiente mensaje y determina si está pidiendo un CAMBIO
VISUAL sobre esa imagen (por ejemplo: cambiar el color de la mesa, el
material, el acabado, el tamaño, moverla de lugar, etc.), o si es una
pregunta/comentario normal que no requiere modificar la imagen.

Mensaje del cliente: "{message}"

Responde SOLO con este JSON, sin texto adicional:
{{"is_image_edit": true/false, "instruction": "<instrucción clara y breve en español para aplicar el cambio; vacío si is_image_edit es false>"}}
"""
    try:
        response = _generate_content_with_retry([prompt])
        text = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(text)
        return {
            "is_image_edit": bool(data.get("is_image_edit")),
            "instruction": data.get("instruction", "") or ""
        }
    except Exception:
        traceback.print_exc()
        return {"is_image_edit": False, "instruction": ""}


def chat(room_id, message, conversation_id, user_id):
    """
    Responde una pregunta del usuario sobre el catálogo de mesas.
    - Si hay room_id: responde con contexto de esa sala y su recomendación.
    - Si no hay room_id: responde preguntas generales del catálogo
      (precios, materiales, estilos disponibles, comparaciones, etc.)
    - Si el cliente pide un cambio visual sobre la imagen ya generada
      (ej. "ponla en negro", "que sea más pequeña"), regenera la imagen
      con OpenAI aplicando ese cambio y la devuelve en "generated_image".
    """
    try:
        if not message or not message.strip():
            return None, "El mensaje no puede estar vacío."

        tables = _get_active_tables()
        if not tables:
            return None, "No hay mesas activas en el catálogo."

        catalog_desc = [
            f"- ID {t.id} | {t.name} | estilo: {t.style} | color: {t.color} | "
            f"material: {t.material} | forma: {t.shape} | "
            f"medidas: {t.width}x{t.depth}x{t.height}cm | precio: ${t.price}"
            for t in tables
        ]

        room = None
        recommendation = None

        if room_id:
            room, err = rooms_service.getById(room_id)
            if err:
                return None, err

            recommendation, err = recommendations_service.getByRoomId(room_id)

            context = (
                f"El cliente ya recibió una recomendación para su sala: "
                f"{recommendation['table'] if recommendation else 'sin datos'}. "
                f"Ten esa recomendación en cuenta si la pregunta se relaciona con ella, "
                f"pero también puedes hablar de cualquier otra mesa del catálogo si lo pide."
            )
        else:
            context = (
                "El cliente todavía no ha subido una foto de su sala. "
                "Responde con la información del catálogo. Si la pregunta requiere "
                "ver su sala para dar una recomendación personalizada, sugiérele "
                "amablemente subir una foto, pero igual intenta responder lo que puedas."
            )

        # ============ NUEVO: detectar pedido de cambio visual ============
        # Solo tiene sentido si ya existe una imagen generada previamente
        # para esta sala (si no, no hay nada que editar todavía).
        if room and recommendation and recommendation.get("generated_image"):
            edit_check = _detect_image_edit_request(message)

            if edit_check["is_image_edit"]:
                table_id = recommendation.get("table_id")
                best_table = _get_table_by_id(table_id) if table_id else None

                if not best_table or not room.get("image_url"):
                    return {
                        "reply": (
                            "Quise aplicar ese cambio pero no encontré los datos "
                            "de tu sala o de la mesa recomendada. ¿Puedes subir "
                            "la foto de nuevo?"
                        ),
                        "generated_image": None,
                        "conversation_id": conversation_id
                    }, None

                new_filename = f"{uuid.uuid4()}.png"
                new_path = os.path.join(UPLOAD_FOLDER_GENERATED, new_filename)

                generated_ok = _generate_composite_image(
                    room["image_url"],
                    best_table,
                    new_path,
                    extra_instructions=edit_check["instruction"]
                )

                if not generated_ok:
                    return {
                        "reply": (
                            "Intenté aplicar ese cambio pero el servicio de "
                            "generación de imágenes falló. ¿Probamos de nuevo?"
                        ),
                        "generated_image": None,
                        "conversation_id": conversation_id
                    }, None

                # Actualiza la recomendación en la BD con la nueva imagen.
                # ⚠️ Requiere que recommendations_service tenga un método
                # `update(recommendation_id, generated_image=...)`. Si no
                # existe todavía, hay que agregarlo (ver nota más abajo).
                recommendations_service.update(
                    recommendation["id"],
                    generated_image=new_path
                )

                return {
                    "reply": f"¡Listo! Actualicé la imagen: {edit_check['instruction']}",
                    "generated_image": new_path,
                    "conversation_id": conversation_id
                }, None
        # ==================================================================

        prompt = f"""
Eres Sofía, la asistente virtual de Centro Home, una tienda de mesas de centro.
Tu tono es cálido, cercano y profesional. Respondes siempre en español.

IMPORTANTE sobre cómo interpretar la pregunta del cliente:
- El cliente puede escribir sin tildes, con mayúsculas o minúsculas mezcladas,
  con errores de tipeo, abreviado, o de forma muy coloquial (ej: "q mesas hay",
  "cuanto cuestan", "tienen algo redondo", "mesa d vidrio"). Interpreta la
  intención real de la pregunta sin importar cómo esté escrita.
- Entiende cualquier pregunta relacionada con mesas de centro: precios,
  materiales, colores, estilos, tamaños/medidas, disponibilidad, diferencias
  entre modelos, recomendaciones según gustos o espacio, formas de pago,
  envíos, o cualquier duda general sobre el catálogo.
- Si la pregunta es ambigua, responde con la interpretación más probable y,
  si hace falta, pide amablemente que aclare un detalle puntual.
- Si preguntan por algo que no está en el catálogo (ej: sillas, sofás), acláralo
  con amabilidad y redirige a lo que sí puedes ofrecer: mesas de centro.

{context}

Catálogo disponible:
{chr(10).join(catalog_desc)}

Pregunta del cliente: {message}

Responde de forma clara, breve y natural (máximo 4-5 líneas). Si mencionas
mesas específicas, usa su nombre real del catálogo.
"""

        try:
            response = _generate_content_with_retry([prompt])
        except ServerError:
            return None, "El servicio de IA está saturado en este momento. Intenta de nuevo en unos segundos."
        except Exception as e:
            traceback.print_exc()
            return None, f"Error consultando la IA: {str(e)}"

        if not response or not response.text:
            return None, "La IA no devolvió una respuesta, intenta de nuevo."

        reply_text = response.text.strip()

        return {
            "reply": reply_text,
            "generated_image": None,
            "conversation_id": conversation_id
        }, None

    except Exception as e:
        traceback.print_exc()
        return None, str(e)