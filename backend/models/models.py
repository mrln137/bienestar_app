"""
Modelos SQLAlchemy del dominio de Bienestar Universitario.
"""
from datetime import datetime, timezone

from backend.database import db


def _utcnow() -> datetime:
    """Timestamp UTC consciente de zona horaria."""
    return datetime.now(timezone.utc)


class Usuario(db.Model):
    """Usuario del sistema (estudiante, personal, administrador)."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    rol = db.Column(db.String(50), nullable=False, default="estudiante")

    citas = db.relationship("Cita", back_populates="usuario", lazy="dynamic")
    historial_chat = db.relationship(
        "HistorialChat", back_populates="usuario", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "rol": self.rol}


class Cita(db.Model):
    """
    Cita de atención en servicios de bienestar.
    prioridad: 1 = alta/grave, 2 = media, 3 = baja.
    """

    __tablename__ = "citas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    prioridad = db.Column(db.Integer, nullable=False, default=2)  # 1-3
    estado = db.Column(db.String(30), nullable=False, default="pendiente")
    fecha_creacion = db.Column(db.DateTime, default=_utcnow, nullable=False)

    usuario = db.relationship("Usuario", back_populates="citas")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "motivo": self.motivo,
            "prioridad": self.prioridad,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion.isoformat()
            if self.fecha_creacion
            else None,
        }


class HistorialChat(db.Model):
    """Mensaje del historial conversacional con el agente de IA."""

    __tablename__ = "historial_chat"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # 'user' | 'assistant'
    contenido = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=_utcnow, nullable=False)

    usuario = db.relationship("Usuario", back_populates="historial_chat")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "rol": self.rol,
            "contenido": self.contenido,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
