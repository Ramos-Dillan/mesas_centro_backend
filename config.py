import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:

    DATABASE_URL = os.getenv("DATABASE_URL")

    HOST = os.getenv("HOST", "0.0.0.0")

    PORT = int(os.getenv("PORT", 5000))

    DEBUG = os.getenv("DEBUG", "True") == "True"

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "super_secret_key_mesas_2026_segura_123456"
    )

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "super_secret_key_mesas_2026_segura_123456"
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Hugging Face
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")