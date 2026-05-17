# Bienestar Universitario

Plataforma web para la **optimización de la gestión de servicios de bienestar universitario** mediante agentes conversacionales (IA). Desarrollada para la **Universidad de Pamplona**, integra un portal de servicios (Salud, Deporte, Cultura, Transporte, Alimentación) con un asistente virtual y gestión de citas.

## Características

- Portal de servicios con interfaz institucional (Universidad de Pamplona).
- Chatbot de IA con integración a **Ollama** y modo simulado de respaldo.
- Agendamiento y listado de citas con priorización (1 = alta, 3 = baja).
- Historial conversacional persistido en base de datos.
- API REST modular (Flask Blueprints).
- Soporte para **SQLite** (desarrollo) y **PostgreSQL** (producción).

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.10+, Flask, Flask-SQLAlchemy |
| Base de datos | SQLite / PostgreSQL (`psycopg2-binary`) |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| IA | Ollama (API local) |
| Configuración | python-dotenv |

## Estructura del proyecto

```
bienestar_app/
├── .env                    # Variables de entorno (no versionar)
├── .env.example            # Plantilla de configuración
├── requirements.txt
├── scripts/
│   └── init_postgres.sql   # Creación de BD y usuario en PostgreSQL
├── backend/
│   ├── app.py              # Punto de entrada Flask
│   ├── config.py           # Configuración por entorno
│   ├── database.py         # Instancia SQLAlchemy
│   ├── controllers/        # Blueprints (rutas / lógica HTTP)
│   │   ├── chat_controller.py
│   │   └── citas_controller.py
│   └── models/
│       └── models.py       # Usuario, Cita, HistorialChat
└── frontend/
    ├── templates/
    │   └── index.html
    └── static/
        ├── css/style.css
        ├── js/script.js
        └── img/
```

## Requisitos previos

- Python 3.10 o superior
- `pip` y entorno virtual recomendado
- **PostgreSQL** (opcional, si no usas SQLite)
- **Ollama** (opcional, para respuestas reales del chatbot)

## Instalación

### 1. Clonar y entrar al proyecto

```bash
cd bienestar_app
```

### 2. Crear entorno virtual

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/macOS
```

Edita `.env` según tu entorno. Variables principales:

| Variable | Descripción |
|----------|-------------|
| `FLASK_ENV` | `development` o `production` |
| `SECRET_KEY` | Clave secreta de Flask (cambiar en producción) |
| `DATABASE_URL` | URI de SQLite o PostgreSQL |
| `OLLAMA_API_URL` | Endpoint de Ollama |
| `OLLAMA_MODEL` | Modelo instalado en Ollama (ej. `llama3.2:3b`) |

## Base de datos

### Opción A: SQLite (rápido para desarrollo)

En `.env`:

```env
DATABASE_URL=sqlite:///bienestar.db
```

El archivo se crea en `backend/bienestar.db` al iniciar la aplicación.

### Opción B: PostgreSQL (recomendado en producción)

**1. Crear base de datos** (pgAdmin o `psql`):

```bash
psql -U postgres -f scripts/init_postgres.sql
```

**2. Configurar `.env`:**

```env
DATABASE_URL=postgresql://bienestar_user:bienestar_pass@localhost:5432/bienestar
```

**3. Iniciar la app** — las tablas se crean automáticamente con `db.create_all()`.

#### Ver datos en PostgreSQL

- **pgAdmin:** Databases → `bienestar` → Schemas → public → Tables
- **psql:**

```bash
psql -U bienestar_user -d bienestar
\dt
SELECT * FROM usuarios;
```

## Ejecutar la aplicación

Desde la carpeta `bienestar_app/` con el entorno virtual activado:

```bash
python -m backend.app
```

Abre en el navegador: **http://localhost:5000**

> Usa siempre la URL del servidor Flask. No abras `index.html` directamente como archivo.

### Verificar que la API responde

```bash
curl http://localhost:5000/api/health
```

## API REST

### Salud del servicio

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/health` | Estado del servicio |

### Chat (IA)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/chat` | Enviar mensaje al asistente |
| `GET` | `/api/chat/historial/<usuario_id>` | Obtener historial de un usuario |

**Ejemplo — enviar mensaje:**

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"mensaje\": \"Tengo fiebre\", \"nombre\": \"Juan Pérez\"}"
```

### Citas

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/citas/agendar` | Agendar cita |
| `GET` | `/api/citas/listar` | Listar citas (prioridad + fecha) |
| `PATCH` | `/api/citas/<id>/estado` | Actualizar estado de cita |

**Ejemplo — agendar cita:**

```bash
curl -X POST http://localhost:5000/api/citas/agendar \
  -H "Content-Type: application/json" \
  -d "{\"motivo\": \"Consulta psicológica\", \"prioridad\": 2}"
```

**Estados válidos de cita:** `pendiente`, `confirmada`, `atendida`, `cancelada`

## Ollama (chatbot con IA real)

1. Instala [Ollama](https://ollama.com).
2. Descarga un modelo:

```bash
ollama pull llama3.2
```

3. Asegúrate de que `.env` tenga la URL correcta:

```env
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2
```

Si Ollama no está disponible, el chat responde en **modo simulado** sin interrumpir la aplicación.

## Modelos de datos

| Modelo | Campos principales |
|--------|-------------------|
| `Usuario` | `id`, `nombre`, `rol` |
| `Cita` | `id`, `usuario_id`, `motivo`, `prioridad` (1-3), `estado`, `fecha_creacion` |
| `HistorialChat` | `id`, `usuario_id`, `rol` (`user`/`assistant`), `contenido`, `timestamp` |

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: backend` | Ejecutar desde `bienestar_app/`, no desde una subcarpeta |
| `No module named 'psycopg2'` | `pip install psycopg2-binary` |
| Error de conexión a PostgreSQL | Verificar que el servicio Postgres esté activo y que `.env` coincida con `init_postgres.sql` |
| CSS/JS no cargan | Acceder vía `http://localhost:5000` |
| Chat en modo simulado | Iniciar Ollama y verificar `OLLAMA_MODEL` |
| Puerto 5000 ocupado | Cerrar el proceso o cambiar el puerto en `backend/app.py` |

## Próximos pasos sugeridos

- [ ] Autenticación de usuarios (JWT o sesiones)
- [ ] Migraciones con Flask-Migrate (Alembic)
- [ ] Despliegue con Gunicorn + Nginx
- [ ] Tests automatizados (pytest)

