# Authentication and Authorization API

API modular de registro, autenticación con JWT y autorización por roles/permisos, construida con FastAPI, SQLAlchemy 2 y PostgreSQL.

Para conocer en detalle la arquitectura, el flujo de autenticación y las decisiones técnicas, consulta la [guía explicativa](docs/guia-explicativa.md).

## Requisitos

- Python 3.10 o superior
- Docker con Docker Compose

## Inicio local (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Genera un secreto JWT y agrégalo a `JWT_SECRET` en `.env`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Arranca PostgreSQL, aplica la migración y ejecuta la API:

```powershell
docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
```

Documentación interactiva: http://127.0.0.1:8000/docs

## Primer administrador

La migración crea los roles `user` y `admin`, además de los permisos iniciales. El registro público siempre asigna el rol `user`. Para crear o promover un administrador, ejecuta el comando y define una contraseña en la consola:

```powershell
python -m app.cli create-admin admin@example.com
```

El rol `admin` puede listar usuarios y asignarles un único rol con `PUT /users/{user_id}/role`. La API no guarda contraseñas en texto plano; usa Argon2 y JWT de corta duración (30 minutos por defecto).

## Endpoints principales

- `POST /auth/register`: registro con contraseña de al menos 12 caracteres.
- `POST /auth/token`: login OAuth2 Password form, responde con un access token JWT.
- `GET /users/me`: perfil del usuario autenticado.
- `GET /users`: requiere el permiso `users:read`.
- `PUT /users/{user_id}/role`: requiere `users:roles:assign`.
- `GET /health`: comprobación básica de disponibilidad.

El endpoint de tokens sigue el flujo OAuth2 de contraseña para una API propia de aprendizaje; no es un servidor OAuth para delegar acceso a proveedores externos. En producción, prefiere OpenID Connect o Authorization Code con PKCE para inicio de sesión de usuarios y añade migraciones/gestión de secretos apropiadas al despliegue.

## Pruebas y lint

Las pruebas usan SQLite en memoria y no necesitan PostgreSQL:

```powershell
pytest
ruff check .
```
