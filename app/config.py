# app/config.py
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "SGOAP")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "False") == "True"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))

    # Base de Datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost:5432/sgoap_db")

    # Seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Email SMTP
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@sgoap.com")

    # URL Base
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    # CORS
    CORS_ORIGINS: List[str] = eval(os.getenv("CORS_ORIGINS", '["*"]'))

    # Sesión
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "dev_session_key")
    SESSION_EXPIRE_DAYS: int = int(os.getenv("SESSION_EXPIRE_DAYS", 7))

settings = Settings()

# Verificar configuración de email
if settings.SMTP_USER and settings.SMTP_PASSWORD:
    print("✅ Configuración de email cargada correctamente")
else:
    print("⚠️ Configuración de email incompleta. Los emails no se enviarán.")