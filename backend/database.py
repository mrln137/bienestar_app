"""
Inicialización de SQLAlchemy.
Se importa `db` en modelos y controladores para evitar importaciones circulares.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
