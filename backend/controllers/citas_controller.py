"""
Controlador de gestión de citas de bienestar universitario.
"""
from flask import Blueprint, jsonify, request

from backend.database import db
from backend.models.models import Cita, Usuario

citas_bp = Blueprint("citas", __name__, url_prefix="/api/citas")


def _obtener_o_crear_usuario(usuario_id: int | None, nombre: str | None) -> Usuario:
    if usuario_id:
        usuario = db.session.get(Usuario, usuario_id)
        if usuario:
            return usuario
    nombre = nombre or "Usuario invitado"
    usuario = Usuario(nombre=nombre, rol="estudiante")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def _validar_prioridad(prioridad: int) -> bool:
    return isinstance(prioridad, int) and 1 <= prioridad <= 3


@citas_bp.route("/agendar", methods=["POST"])
def agendar_cita():
    """
    POST /api/citas/agendar
    Body JSON: {
        "motivo": "...",
        "prioridad": 1|2|3,
        "usuario_id": 1 (opcional),
        "nombre": "..." (opcional)
    }
    """
    data = request.get_json(silent=True) or {}
    motivo = (data.get("motivo") or "").strip()
    prioridad = data.get("prioridad", 2)

    if not motivo:
        return jsonify({"error": "El campo 'motivo' es obligatorio."}), 400

    try:
        prioridad = int(prioridad)
    except (TypeError, ValueError):
        return jsonify({"error": "La prioridad debe ser un entero entre 1 y 3."}), 400

    if not _validar_prioridad(prioridad):
        return jsonify(
            {"error": "La prioridad debe estar entre 1 (alta) y 3 (baja)."}
        ), 400

    usuario = _obtener_o_crear_usuario(
        data.get("usuario_id"),
        data.get("nombre"),
    )

    cita = Cita(
        usuario_id=usuario.id,
        motivo=motivo,
        prioridad=prioridad,
        estado="pendiente",
    )
    db.session.add(cita)
    db.session.commit()

    etiquetas = {1: "Alta", 2: "Media", 3: "Baja"}
    return jsonify(
        {
            "mensaje": "Cita agendada correctamente.",
            "cita": cita.to_dict(),
            "prioridad_etiqueta": etiquetas.get(prioridad, "Desconocida"),
        }
    ), 201


@citas_bp.route("/listar", methods=["GET"])
def listar_citas():
    """
    GET /api/citas/listar
    Devuelve citas ordenadas por prioridad (1 primero) y luego por fecha de creación.
    Query opcional: ?estado=pendiente
    """
    estado = request.args.get("estado")

    query = Cita.query
    if estado:
        query = query.filter_by(estado=estado)

    citas = (
        query.order_by(Cita.prioridad.asc(), Cita.fecha_creacion.asc()).all()
    )

    return jsonify(
        {
            "total": len(citas),
            "citas": [c.to_dict() for c in citas],
        }
    ), 200


@citas_bp.route("/<int:cita_id>/estado", methods=["PATCH"])
def actualizar_estado(cita_id: int):
    """PATCH /api/citas/<id>/estado — Actualiza el estado de una cita."""
    data = request.get_json(silent=True) or {}
    nuevo_estado = (data.get("estado") or "").strip()

    estados_validos = {"pendiente", "confirmada", "atendida", "cancelada"}
    if nuevo_estado not in estados_validos:
        return jsonify(
            {
                "error": f"Estado inválido. Valores permitidos: {', '.join(estados_validos)}"
            }
        ), 400

    cita = db.session.get(Cita, cita_id)
    if not cita:
        return jsonify({"error": "Cita no encontrada."}), 404

    cita.estado = nuevo_estado
    db.session.commit()

    return jsonify({"mensaje": "Estado actualizado.", "cita": cita.to_dict()}), 200
