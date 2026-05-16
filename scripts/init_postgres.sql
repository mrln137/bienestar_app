-- Ejecutar en PostgreSQL (pgAdmin → Query Tool o psql) como superusuario (postgres).
-- Ajusta usuario y contraseña si cambias .env

CREATE USER bienestar_user WITH PASSWORD 'bienestar_pass';

CREATE DATABASE bienestar OWNER bienestar_user ENCODING 'UTF8';

GRANT ALL PRIVILEGES ON DATABASE bienestar TO bienestar_user;

-- Conéctate a la base "bienestar" y ejecuta (PostgreSQL 15+):
-- GRANT ALL ON SCHEMA public TO bienestar_user;
