"""
Configuración centralizada de la aplicación.
Lee variables de entorno desde .env mediante python-dotenv.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto (bienestar_app/)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Configuración base compartida por todos los entornos."""

    # Clave secreta para sesiones y firmas (cambiar en producción)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-cambiar-en-produccion")

    # SQLite (desarrollo) o PostgreSQL (producción) vía DATABASE_URL en .env
    # Ejemplo Postgres: postgresql://usuario:clave@localhost:5432/bienestar
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///bienestar.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Endpoint de Ollama para el agente conversacional
    OLLAMA_API_URL = os.getenv(
        "OLLAMA_API_URL",
        "http://localhost:11434/api/generate",
    )
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Entorno Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"


class DevelopmentConfig(Config):
    """Configuración para desarrollo local."""
    DEBUG = True


class ProductionConfig(Config):
    """Configuración para despliegue en producción."""
    DEBUG = False


# Mapa de configuraciones por nombre de entorno
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> type[Config]:
    """Devuelve la clase de configuración según FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
