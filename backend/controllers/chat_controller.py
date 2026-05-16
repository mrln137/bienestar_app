"""
Controlador del chat conversacional con integración a Ollama.
"""
import requests
from flask import Blueprint, current_app, jsonify, request

from backend.database import db
from backend.models.models import HistorialChat, Usuario

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def _obtener_o_crear_usuario(usuario_id: int | None, nombre: str | None) -> Usuario:
    """Obtiene un usuario existente o crea uno de demostración."""
    if usuario_id:
        usuario = db.session.get(Usuario, usuario_id)
        if usuario:
            return usuario

    nombre = nombre or "Usuario invitado"
    usuario = Usuario(nombre=nombre, rol="estudiante")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def _cargar_historial(usuario_id: int, limite: int = 10) -> list[dict]:
    """Últimos mensajes del usuario para contexto conversacional."""
    mensajes = (
        HistorialChat.query.filter_by(usuario_id=usuario_id)
        .order_by(HistorialChat.timestamp.desc())
        .limit(limite)
        .all()
    )
    return [m.to_dict() for m in reversed(mensajes)]


def _guardar_mensaje(usuario_id: int, rol: str, contenido: str) -> HistorialChat:
    """Persiste un turno de la conversación."""
    registro = HistorialChat(
        usuario_id=usuario_id,
        rol=rol,
        contenido=contenido,
    )
    db.session.add(registro)
    db.session.commit()
    return registro


def _consultar_ollama(mensaje: str, historial: list[dict]) -> str:
    """
    Envía el mensaje a la API de Ollama.
    En caso de fallo, devuelve una respuesta simulada de respaldo.
    """
    url = current_app.config.get("OLLAMA_API_URL")
    model = current_app.config.get("OLLAMA_MODEL", "llama3.2")

    # Construir contexto breve a partir del historial
    contexto = ""
    for item in historial[-6:]:
        emisor = "Usuario" if item["rol"] == "user" else "Asistente"
        contexto += f"{emisor}: {item['contenido']}\n"

    prompt = (
        "Eres un asistente virtual de Bienestar Universitario. "
        "Ayudas con salud, deporte, cultura y alimentación. "
        "Responde en español de forma clara y empática.\n\n"
        f"{contexto}Usuario: {mensaje}\nAsistente:"
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip() or "No obtuve una respuesta del modelo."


def _respuesta_simulada(mensaje: str) -> str:
    """Respuesta de respaldo cuando Ollama no está disponible."""
    mensaje_lower = mensaje.lower()
    if any(p in mensaje_lower for p in ("cita", "agendar", "turno")):
        return (
            "Puedo ayudarte a agendar una cita. Indica el motivo de tu consulta "
            "y evaluaré la prioridad. También puedes usar el panel de servicios."
        )
    if "salud" in mensaje_lower:
        return "El área de Salud ofrece atención médica y psicológica. ¿Deseas agendar?"
    if "deporte" in mensaje_lower:
        return "Deporte cuenta con actividades físicas y espacios deportivos universitarios."
    if "cultura" in mensaje_lower:
        return "Cultura organiza eventos artísticos y talleres. ¿Qué te interesa?"
    if "aliment" in mensaje_lower:
        return "Alimentación gestiona comedores y apoyos nutricionales estudiantiles."
    return (
        "Hola, soy el asistente de Bienestar Universitario. "
        "¿En qué servicio puedo ayudarte: Salud, Deporte, Cultura o Alimentación?"
    )


@chat_bp.route("", methods=["POST"])
def enviar_mensaje():
    """
    POST /api/chat
    Body JSON: { "mensaje": "...", "usuario_id": 1 (opcional), "nombre": "..." (opcional) }
    """
    data = request.get_json(silent=True) or {}
    mensaje = (data.get("mensaje") or "").strip()

    if not mensaje:
        return jsonify({"error": "El campo 'mensaje' es obligatorio."}), 400

    usuario = _obtener_o_crear_usuario(
        data.get("usuario_id"),
        data.get("nombre"),
    )

    _guardar_mensaje(usuario.id, "user", mensaje)
    historial = _cargar_historial(usuario.id)

    origen = "ollama"
    try:
        respuesta_texto = _consultar_ollama(mensaje, historial)
    except requests.exceptions.RequestException as exc:
        current_app.logger.warning("Ollama no disponible: %s", exc)
        respuesta_texto = _respuesta_simulada(mensaje)
        origen = "simulado"
    except Exception as exc:
        current_app.logger.exception("Error inesperado al consultar Ollama: %s", exc)
        respuesta_texto = _respuesta_simulada(mensaje)
        origen = "simulado"

    asistente = _guardar_mensaje(usuario.id, "assistant", respuesta_texto)

    return jsonify(
        {
            "usuario_id": usuario.id,
            "mensaje_usuario": mensaje,
            "respuesta": respuesta_texto,
            "origen": origen,
            "historial": _cargar_historial(usuario.id, limite=20),
            "id_respuesta": asistente.id,
        }
    ), 200


@chat_bp.route("/historial/<int:usuario_id>", methods=["GET"])
def obtener_historial(usuario_id: int):
    """GET /api/chat/historial/<usuario_id> — Recupera el historial de un usuario."""
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado."}), 404

    historial = _cargar_historial(usuario_id, limite=50)
    return jsonify({"usuario_id": usuario_id, "historial": historial}), 200
