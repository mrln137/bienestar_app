"""
Punto de entrada de la aplicación Flask — Bienestar Universitario.
Ejecutar desde la raíz del proyecto: python -m backend.app
"""
import sys
from pathlib import Path

# Asegurar que bienestar_app/ esté en sys.path para imports absolutos
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, render_template
from flask_cors import CORS

from backend.config import get_config
from backend.controllers.chat_controller import chat_bp
from backend.controllers.citas_controller import citas_bp
from backend.database import db


def create_app() -> Flask:
    """Factory de la aplicación Flask."""
    app = Flask(
        __name__,
        template_folder=str(ROOT_DIR / "frontend" / "templates"),
        static_folder=str(ROOT_DIR / "frontend" / "static"),
        static_url_path="/static",
    )

    # Cargar configuración desde variables de entorno
    config_class = get_config()
    app.config.from_object(config_class)

    # Ajustar URI de SQLite para que el archivo quede en backend/
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        db_name = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        if not db_name.startswith("/") and ":" not in db_name[:3]:
            db_path = Path(__file__).resolve().parent / db_name
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    # Extensiones
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Registrar blueprints (rutas de la API)
    app.register_blueprint(chat_bp)
    app.register_blueprint(citas_bp)

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
        _seed_usuario_demo()

    @app.route("/")
    def index():
        """Sirve la interfaz principal del frontend."""
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        """Endpoint de verificación de estado del servicio."""
        return {"status": "ok", "servicio": "Bienestar Universitario API"}, 200

    return app


def _seed_usuario_demo() -> None:
    """Crea un usuario de demostración si la base está vacía."""
    from backend.models.models import Usuario

    if Usuario.query.count() == 0:
        demo = Usuario(nombre="Estudiante Demo", rol="estudiante")
        db.session.add(demo)
        db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
