
"""
Controlador del chat conversacional con Ollama + Flask.

Capacidades:
- Chat médico conversacional.
- Agendamiento de citas.
- Análisis de síntomas con IA.
- Análisis de PDFs médicos.
- Prioridad automática usando Ollama.
"""

import json
import os
import re
import tempfile

import requests
from flask import Blueprint, current_app, jsonify, request

from backend.database import db
from backend.models.models import Cita, HistorialChat, Usuario

from langchain_community.document_loaders import PyPDFLoader

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# ============================================================================
# ESTADO CONVERSACIONAL
# ============================================================================

_estado_cita = {}

# ============================================================================
# HELPERS DB
# ============================================================================

def _obtener_o_crear_usuario(usuario_id=None, nombre=None):
    if usuario_id:
        usuario = db.session.get(Usuario, usuario_id)
        if usuario:
            return usuario

    usuario = Usuario(
        nombre=nombre or "Usuario Invitado",
        rol="estudiante"
    )

    db.session.add(usuario)
    db.session.commit()

    return usuario


def _guardar_mensaje(usuario_id, rol, contenido):
    registro = HistorialChat(
        usuario_id=usuario_id,
        rol=rol,
        contenido=contenido
    )

    db.session.add(registro)
    db.session.commit()

    return registro


def _cargar_historial(usuario_id, limite=20):
    mensajes = (
        HistorialChat.query
        .filter_by(usuario_id=usuario_id)
        .order_by(HistorialChat.timestamp.desc())
        .limit(limite)
        .all()
    )

    return [m.to_dict() for m in reversed(mensajes)]


# ============================================================================
# ANALISIS IA
# ============================================================================

def analizar_sintomas_con_ollama(
    sintomas,
    ollama_url,
    model_name
):
    prompt = f"""
Eres un asistente médico de triaje universitario.

Analiza los síntomas del usuario y responde SOLO un JSON válido.

Formato:
{{
  "prioridad": 1,
  "riesgo": "alto",
  "motivo": "explicación breve"
}}

Prioridades:
1 = urgente
2 = media
3 = baja

Síntomas:
{sintomas}
"""

    try:
        resp = requests.post(
            ollama_url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        resp.raise_for_status()

        texto = resp.json().get("response", "")

        match = re.search(r"\{.*\}", texto, re.DOTALL)

        if match:
            return json.loads(match.group())

    except Exception as e:
        print("ERROR OLLAMA:", e)

    return {
        "prioridad": 2,
        "riesgo": "medio",
        "motivo": "No se pudo analizar correctamente"
    }


# ============================================================================
# ANALISIS PDF
# ============================================================================

def analizar_pdf_medico(
    ruta_pdf,
    ollama_url,
    model_name
):
    if not os.path.exists(ruta_pdf):
        return "No se encontró el PDF."

    try:
        loader = PyPDFLoader(ruta_pdf)
        pages = loader.load()

        texto = "\n".join(
            p.page_content for p in pages
        )[:4000]

    except Exception as e:
        return f"Error leyendo PDF: {e}"

    prompt = f"""
Eres un médico de triaje.

Analiza este examen médico y responde SOLO un JSON válido.

Formato:
{{
  "hallazgos": "resumen",
  "prioridad": 1,
  "riesgo": "alto",
  "motivo": "explicación"
}}

Prioridades:
1 = urgente
2 = media
3 = baja

EXAMEN:
{texto}
"""

    try:
        resp = requests.post(
            ollama_url,
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False
            },
            timeout=90
        )

        resp.raise_for_status()

        raw = resp.json().get("response", "")

        match = re.search(r"\{.*\}", raw, re.DOTALL)

        if match:
            data = json.loads(match.group())

            prioridad = int(data.get("prioridad", 2))

            etiquetas = {
                1: "Alta",
                2: "Media",
                3: "Baja"
            }

            return (
                f"Resultado del análisis:\n\n"
                f"• Hallazgos: {data.get('hallazgos')}\n"
                f"• Prioridad: {etiquetas[prioridad]}\n"
                f"• Motivo: {data.get('motivo')}\n\n"
                f"¿Deseas agendar una cita?"
            )

    except Exception as e:
        return f"Error analizando PDF: {e}"

    return "No se pudo analizar el PDF."


# ============================================================================
# AGENDAR CITA
# ============================================================================

def crear_cita(
    usuario_id,
    motivo,
    prioridad
):
    cita = Cita(
        usuario_id=usuario_id,
        motivo=motivo,
        prioridad=prioridad,
        estado="pendiente"
    )

    db.session.add(cita)
    db.session.commit()

    etiquetas = {
        1: "Alta",
        2: "Media",
        3: "Baja"
    }

    return (
        f"Cita agendada correctamente.\n\n"
        f"• Motivo: {motivo}\n"
        f"• Prioridad: {etiquetas[prioridad]}\n"
        f"• Estado: Pendiente\n"
        f"• ID: #{cita.id}"
    )


# ============================================================================
# RESPUESTA SIMPLE
# ============================================================================

def respuesta_basica(mensaje):
    msg = mensaje.lower()

    if "hola" in msg:
        return (
            "Soy el Asistente de IA de Bienestar Universitario 👋\n\n"
            "¿En qué puedo ayudarte?\n"
            "• Salud\n"
            "• Deporte\n"
            "• Cultura\n"
            "• Alimentación"
        )
    
    if "salud" in msg:
        return (
            "🩺 El área de Salud ofrece:\n"
            "• Medicina general\n"
            "• Psicología\n"
            "• Atención prioritaria\n\n"
            "Si deseas agendar una cita escribe:\n"
            "'Quiero una cita'"
        )

    if "deporte" in msg:
        return (
            "⚽ Bienestar Deportivo ofrece:\n"
            "• Gimnasio\n"
            "• Equipos deportivos\n"
            "• Actividades recreativas"
        )

    if "cultura" in msg:
        return (
            "🎭 Bienestar Cultural ofrece:\n"
            "• Talleres\n"
            "• Danza\n"
            "• Arte\n"
            "• Eventos culturales"
        )

    if "alimentación" in msg:
        return (
            "🍽️ Bienestar Alimentario ofrece:\n"
            "• Comedor universitario\n"
            "• Becas alimentarias\n"
            "• Apoyo nutricional"
        )
    if "Transporte" in msg or "Rutas" in msg or "consultar" in msg:
        return (
            "🚗 Bienestar de Transporte ofrece:\n"
            "• Rutas universitarias\n"
            "• Apoyo para movilidad\n"
            "• Información sobre transporte público"
        )
    return (
        "No entendí muy bien tu solicitud.\n"
        "¿Puedes explicarme mejor?"
    )


# ============================================================================
# CHAT PRINCIPAL
# ============================================================================

@chat_bp.route("", methods=["POST"])
def enviar_mensaje():

    data = request.get_json(silent=True) or {}

    mensaje = (data.get("mensaje") or "").strip()

    if not mensaje:
        return jsonify({
            "error": "Mensaje vacío"
        }), 400

    usuario = _obtener_o_crear_usuario(
        data.get("usuario_id"),
        data.get("nombre")
    )

    _guardar_mensaje(usuario.id, "user", mensaje)

    ollama_url = current_app.config.get(
        "OLLAMA_API_URL",
        "http://localhost:11434/api/generate"
    )

    model_name = current_app.config.get(
        "OLLAMA_MODEL",
        "llama3.2:latest"
    )

    estado = _estado_cita.get(usuario.id)

    msg = mensaje.lower()

   # =======================================================================
    # CONTROL DE CANCELACIÓN (AGREGAR ESTO AQUÍ)
    # =======================================================================
    # Si el usuario dice "no", "cancelar" o "salir" mientras se está gestionando la cita, abortamos.
    if estado and msg in ["no", "cancelar", "salir", "ninguno", "parar"]:
        _estado_cita.pop(usuario.id, None)  # Borramos el estado actual
        respuesta = "Entendido, he cancelado el proceso de la cita. ¿Hay algo más en lo que te pueda ayudar?"

    # =======================================================================
    # INICIAR FLUJO
    # =======================================================================
    elif any(x in msg for x in ["cita", "agendar", "quiero una cita"]):
        _estado_cita[usuario.id] = {
            "paso": "esperando_sintomas"
        }
        respuesta = "🩺 Claro. Cuéntame cuáles son tus síntomas o el motivo de la consulta."

    # =======================================================================
    # ESPERANDO SINTOMAS
    # =======================================================================
    elif estado and estado.get("paso") == "esperando_sintomas":
        # Al poner el IF de cancelación arriba, si el usuario escribe "no", 
        # entrará allá primero y NUNCA llegará a este análisis de Ollama.
        analisis = analizar_sintomas_con_ollama(mensaje, ollama_url, model_name)
        prioridad = int(analisis.get("prioridad", 2))
        
        etiquetas = {1: "Alta ", 2: "Media", 3: "Baja"}

        _estado_cita[usuario.id] = {
            "paso": "confirmar_cita",
            "motivo": mensaje,
            "prioridad": prioridad
        }

        respuesta = (
            f"🩺 He analizado tus síntomas.\n\n"
            f"• Prioridad detectada: {etiquetas[prioridad]}\n"
            f"• Motivo: {analisis.get('motivo')}\n\n"
            f"¿Deseas que agende la cita?"
        )

    # =======================================================================
    # CONFIRMAR CITA
    # =======================================================================
    elif estado and estado.get("paso") == "confirmar_cita":
        if msg in ["si", "sí", "confirmo", "ok"]:
            respuesta = crear_cita(usuario.id, estado["motivo"], estado["prioridad"])
        else:
            respuesta = "Entendido. La cita no fue agendada."
        
        _estado_cita.pop(usuario.id, None)

        

 # =======================================================================
    # RESPUESTA NORMAL
    # =======================================================================
    else:
        # Evaluamos si el mensaje es una negativa o despedida común fuera de flujo
        if msg in ["no", "no gracias", "nada", "ninguno", "gracias", "gracias de nada", "chao", "adios"]:
            respuesta = "¡Entendido! Quedo a tu disposición si necesitas algo más de Bienestar Universitario. ¡Que tengas un excelente día! 😊"
        else:
            respuesta = respuesta_basica(mensaje)

    asistente = _guardar_mensaje(
        usuario.id,
        "assistant",
        respuesta
    )

    return jsonify({
        "usuario_id": usuario.id,
        "respuesta": respuesta,
        "historial": _cargar_historial(usuario.id),
        "id_respuesta": asistente.id
    })



# ============================================================================
# HISTORIAL
# ============================================================================

@chat_bp.route("/historial/<int:usuario_id>", methods=["GET"])
def obtener_historial(usuario_id):

    historial = _cargar_historial(usuario_id, 50)

    return jsonify({
        "usuario_id": usuario_id,
        "historial": historial
    })


# ============================================================================
# SUBIR PDF
# ============================================================================

@chat_bp.route("/subir-pdf", methods=["POST"])
def subir_pdf():

    if "pdf" not in request.files:
        return jsonify({
            "error": "No se envió PDF"
        }), 400

    archivo = request.files["pdf"]

    usuario = _obtener_o_crear_usuario(
        request.form.get("usuario_id", type=int),
        request.form.get("nombre")
    )

    ollama_url = current_app.config.get(
        "OLLAMA_API_URL",
        "http://localhost:11434/api/generate"
    )

    model_name = current_app.config.get(
        "OLLAMA_MODEL",
        "llama3.2:latest"
    )

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    ) as tmp:

        archivo.save(tmp.name)

        ruta = tmp.name

    try:

        resultado = analizar_pdf_medico(
            ruta,
            ollama_url,
            model_name
        )
    # Guardar estado para confirmar cita
        _estado_cita[usuario.id] = {
        "paso": "confirmar_cita",
        "motivo": "Examen médico analizado desde PDF",
        "prioridad": 1
}

    finally:

        os.unlink(ruta)

    _guardar_mensaje(
        usuario.id,
        "user",
        f"[PDF]: {archivo.filename}"
    )

    _guardar_mensaje(
        usuario.id,
        "assistant",
        resultado
    )

    return jsonify({
        "usuario_id": usuario.id,
        "analisis": resultado,
        "historial": _cargar_historial(usuario.id)
    })
