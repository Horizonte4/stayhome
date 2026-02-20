Proyecto básico en Django conectado a PostgreSQL, con un formulario web para registrar usuarios en la base de datos.

 Requisitos
- Python 3.x
- PostgreSQL (pgAdmin opcional)
- Django
- psycopg2-binary

 Instalación (Windows)

1) Crear y activar entorno virtual
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

2) Instalar dependencias
pip install django psycopg2-binary

Configuración de PostgreSQL
Ejecutar como postgres:
CREATE DATABASE usuarios_db;

CREATE USER usuario_django WITH PASSWORD 'password123';
ALTER ROLE usuario_django SET client_encoding TO 'utf8';
ALTER ROLE usuario_django SET default_transaction_isolation TO 'read committed';
ALTER ROLE usuario_django SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE usuarios_db TO usuario_django;

-- Permisos para crear tablas en public
GRANT USAGE, CREATE ON SCHEMA public TO usuario_django;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO usuario_django;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO usuario_django;

Migraciones
python manage.py makemigrations
python manage.py migrate

Ejecutar el servidor
python manage.py runserver

Abrir en el navegador:
http://127.0.0.1:8000/
