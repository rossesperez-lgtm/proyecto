# Guía explicativa del proyecto

## 1. Qué construimos

Este proyecto es una API web para:

1. Registrar usuarios.
2. Comprobar sus credenciales y entregarles un token de acceso.
3. Identificar al usuario que presenta ese token en una petición posterior.
4. Permitir o denegar operaciones según sus roles y permisos.

La API está pensada como una base educativa y ejecutable en local. Usa PostgreSQL al ejecutarse normalmente y SQLite en memoria para las pruebas automatizadas.

### Autenticación y autorización no son lo mismo

- **Autenticación** responde: «¿quién eres?». En este proyecto se demuestra una contraseña al iniciar sesión y se valida un JWT en peticiones posteriores.
- **Autorización** responde: «¿qué puedes hacer?». La API consulta los permisos asociados a los roles del usuario y los compara con el permiso requerido por el endpoint.

Por ejemplo, un usuario con el rol `user` puede ver su propio perfil, pero no tiene el permiso `users:read` para consultar la lista completa de usuarios. El rol `admin` recibe permisos para consultar usuarios y asignar roles.

## 2. Cómo se organizó el código

Se eligió una estructura modular, con responsabilidades separadas:

| Área | Archivos | Responsabilidad |
|---|---|---|
| Presentación/API | [app/main.py](../app/main.py), [app/api/auth.py](../app/api/auth.py), [app/api/users.py](../app/api/users.py) | Crear la aplicación FastAPI, declarar rutas, recibir datos HTTP y devolver respuestas. |
| Validación y serialización | [app/schemas.py](../app/schemas.py) | Definir los datos aceptados y devueltos mediante modelos Pydantic. |
| Dominio/persistencia | [app/models.py](../app/models.py), [app/db/base.py](../app/db/base.py), [app/db/session.py](../app/db/session.py) | Representar usuarios, roles y permisos en SQLAlchemy, y administrar sesiones de base de datos. |
| Seguridad y configuración | [app/core/security.py](../app/core/security.py), [app/core/config.py](../app/core/config.py), [app/api/deps.py](../app/api/deps.py) | Hash de contraseñas, JWT, carga de configuración y dependencias de autenticación/autorización. |
| Migraciones | [alembic/env.py](../alembic/env.py), [alembic/versions/0001_initial.py](../alembic/versions/0001_initial.py) | Crear y evolucionar el esquema de base de datos de forma versionada. |
| Operación local | [compose.yaml](../compose.yaml), [.env.example](../.env.example), [app/cli.py](../app/cli.py) | Levantar PostgreSQL, configurar secretos y crear/promover un administrador. |
| Calidad | [tests/](../tests/), [pyproject.toml](../pyproject.toml) | Pruebas automatizadas, dependencias y reglas de Ruff. |

Es una separación modular práctica para un proyecto pequeño: no pretende ser una arquitectura de microservicios ni impone una capa de dominio extensa. Por ejemplo, las operaciones de registro y asignación de rol están cerca de sus rutas; si el proyecto crece, podrían moverse a servicios/casos de uso sin cambiar los contratos HTTP.

## 3. Tecnologías y por qué se eligieron

### FastAPI

Define las rutas HTTP y resuelve dependencias como sesiones y usuarios autenticados. También genera documentación OpenAPI automáticamente, visible en `/docs` cuando el servidor está activo.

### SQLAlchemy 2

Es el ORM: permite trabajar con clases y consultas Python en lugar de construir manualmente cada consulta SQL. `User`, `Role` y `Permission` son modelos mapeados a tablas. SQLAlchemy también administra el motor y las sesiones de conexión.

### PostgreSQL y Psycopg

PostgreSQL es la base normal de ejecución. Psycopg es el controlador que permite a SQLAlchemy conectarse a PostgreSQL. [compose.yaml](../compose.yaml) ofrece una instancia local de PostgreSQL 16 con una base y usuario de desarrollo.

### Pydantic y pydantic-settings

Pydantic valida los cuerpos HTTP y convierte los datos en tipos Python. Por ejemplo, `EmailStr` valida el formato del correo y `Field` impone límites de longitud a la contraseña. `pydantic-settings` carga valores desde el entorno o desde `.env`.

### PyJWT

Firma y verifica los JWT. El token contiene el identificador de usuario en `sub` y una fecha de expiración en `exp`. Se firma con HS256 y el secreto configurado en `JWT_SECRET`.

### pwdlib con Argon2

Genera y verifica hashes de contraseñas. La contraseña original no se almacena; la verificación compara una contraseña presentada con el hash guardado.

### Alembic

Gestiona cambios de esquema con migraciones versionadas. La primera migración crea las tablas y carga roles/permisos iniciales. Así no dependemos de crear tablas automáticamente al arrancar la API.

### Pytest, HTTPX y Ruff

- Pytest ejecuta las pruebas.
- HTTPX permite a `TestClient` enviar peticiones a la aplicación durante las pruebas sin arrancar un servidor real.
- Ruff revisa estilo, errores comunes, orden de imports y algunas modernizaciones de sintaxis.

Las versiones y grupos de dependencias están declarados en [pyproject.toml](../pyproject.toml).

## 4. Modelo de datos: usuarios, roles y permisos

La migración inicial crea cinco tablas:

- `users`: correo único, hash de contraseña, estado activo y fecha de creación.
- `roles`: nombres únicos de roles, inicialmente `user` y `admin`.
- `permissions`: nombres únicos de permisos, inicialmente `users:read` y `users:roles:assign`.
- `user_roles`: relación muchos-a-muchos entre usuarios y roles.
- `role_permissions`: relación muchos-a-muchos entre roles y permisos.

Las relaciones muchos-a-muchos permiten que un usuario tenga varios roles y que un permiso pueda pertenecer a varios roles. En esta versión, el registro público asigna solamente `user`, y la ruta de asignación reemplaza los roles existentes por el rol elegido. El comando administrativo puede añadir `admin` a una cuenta existente.

La migración está en [0001_initial.py](../alembic/versions/0001_initial.py). Crea también índices/restricciones para evitar correos y nombres duplicados. Un usuario normal no recibe permisos iniciales; el rol `admin` recibe ambos permisos.

## 5. Recorrido de las peticiones

### 5.1 Registro: `POST /auth/register`

El cliente envía JSON, por ejemplo:

```json
{
  "email": "persona@example.com",
  "password": "una-clave-larga"
}
```

El flujo es:

1. FastAPI valida el JSON con `UserCreate`: correo válido y contraseña de 12 a 128 caracteres.
2. Se normaliza el correo a minúsculas.
3. Se comprueba que no exista ya.
4. Se busca el rol `user`. Si la migración no se aplicó, se devuelve un error explicativo.
5. Se calcula un hash Argon2 y se crea el usuario con el rol `user`.
6. Se confirma la transacción y se devuelve una representación pública, sin el hash.

Una cuenta duplicada recibe `409 Conflict`; un registro exitoso, `201 Created`. La restricción única de la base complementa la comprobación previa para proteger también frente a dos registros simultáneos.

### 5.2 Inicio de sesión: `POST /auth/token`

Este endpoint recibe un formulario OAuth2, no JSON. El campo estándar `username` contiene aquí el correo:

```text
username=persona@example.com
password=una-clave-larga
```

Si el usuario existe, la contraseña coincide y la cuenta está activa, la API emite un JWT. Si las credenciales no coinciden o la cuenta no está activa, responde con `401 Unauthorized`.

El JWT es un **token firmado**, no cifrado: su contenido puede ser leído por quien lo tenga, pero una firma válida permite detectar alteraciones. Por eso no se ponen contraseñas ni datos sensibles dentro. Su `exp` limita su vigencia; el valor predeterminado es 30 minutos.

### 5.3 Autenticación de una petición con bearer token

El cliente envía el token en la cabecera:

```text
Authorization: Bearer <access_token>
```

`OAuth2PasswordBearer` extrae el bearer token. La dependencia `get_current_user` lo verifica con PyJWT, comprueba expiración/firma, interpreta `sub` como ID, busca al usuario en la base y rechaza cuentas inexistentes o inactivas. Si el token no es válido, responde `401` y la cabecera `WWW-Authenticate: Bearer`.

El usuario se carga desde la base en cada petición protegida. Así, el rol y estado actuales se consultan desde la base, en lugar de confiar en roles que pudieran haber quedado obsoletos dentro de un token emitido antes de un cambio.

### 5.4 Autorización mediante permisos

`require_permission("nombre:permiso")` construye una dependencia de FastAPI. Esta:

1. Obtiene el usuario autenticado.
2. Reúne los permisos de sus roles.
3. Comprueba que exista el permiso pedido.
4. Devuelve el usuario o responde `403 Forbidden`.

La diferencia de códigos es intencional: `401` significa que falta una identidad aceptable; `403` significa que se identificó al usuario, pero no está autorizado.

### 5.5 Perfil: `GET /users/me`

Requiere un token válido. Devuelve el perfil de quien hizo la petición, sin contraseña ni hash.

### 5.6 Listado de usuarios: `GET /users`

Requiere `users:read`. Un usuario normal recibe `403`; el administrador puede obtener la lista.

### 5.7 Asignar rol: `PUT /users/{user_id}/role`

Requiere `users:roles:assign`. El cuerpo tiene esta forma:

```json
{
  "role": "user"
}
```

La ruta comprueba que existan tanto el usuario como el rol; de lo contrario, responde `404`. Si ambos existen, asigna ese rol y devuelve el perfil actualizado.

### 5.8 Salud: `GET /health`

Devuelve `{"status": "ok"}`. Es una comprobación básica de que la aplicación responde; **no** comprueba que PostgreSQL esté disponible.

## 6. Configuración y ejecución local

1. Crear y activar un entorno virtual.
2. Instalar dependencias de desarrollo con `python -m pip install -e ".[dev]"`.
3. Copiar [.env.example](../.env.example) a `.env`.
4. Generar un secreto con `python -c "import secrets; print(secrets.token_urlsafe(48))"` y guardarlo como `JWT_SECRET` en `.env`.
5. Arrancar PostgreSQL con `docker compose up -d db`.
6. Aplicar el esquema con `alembic upgrade head`.
7. Arrancar la API con `uvicorn app.main:app --reload`.
8. Abrir `http://127.0.0.1:8000/docs`.

`DATABASE_URL` debe apuntar a PostgreSQL y `ACCESS_TOKEN_EXPIRE_MINUTES` permite configurar la duración de los tokens. La clave `JWT_SECRET` se valida con longitud mínima de 32 caracteres y se representa como `SecretStr`, para reducir su exposición accidental en representaciones del objeto.

Después de aplicar la migración, se puede crear el primer administrador con:

```powershell
python -m app.cli create-admin admin@example.com
```

El CLI solicita contraseña y confirmación de forma interactiva para no pasar la contraseña en los argumentos del comando. No existe una contraseña administrativa predeterminada. Se puede usar este comando para crear el administrador o promover una cuenta ya registrada.

Los valores de usuario/contraseña de PostgreSQL declarados en Compose son solo de desarrollo local; hay que reemplazarlos por secretos gestionados adecuadamente antes de desplegar.

## 7. Pruebas

Las pruebas están en [tests/test_auth.py](../tests/test_auth.py) y [tests/conftest.py](../tests/conftest.py). Usan SQLite en memoria y sustituyen la dependencia de base de datos de la API. Esto hace las pruebas rápidas y no requiere Docker ni una instancia PostgreSQL.

Los casos cubiertos son:

- Registro, inicio de sesión y lectura del perfil.
- Rechazo de un usuario normal al listar usuarios.
- Rechazo de correo duplicado.
- Lectura de lista y asignación de rol por un administrador.

Para ejecutarlas:

```powershell
python -m pytest
```

Y para revisar el estilo:

```powershell
python -m ruff check .
```

El chequeo de migración se puede hacer por separado en un SQLite temporal, pero PostgreSQL continúa siendo la base configurada para la ejecución normal.

## 8. OAuth2, JWT y alcance de esta implementación

Es importante distinguir tres conceptos:

- **OAuth 2.0** es un marco de autorización para que un cliente obtenga acceso delegado a recursos.
- **OpenID Connect (OIDC)** agrega identidad/autenticación interoperable sobre OAuth 2.0.
- **JWT** es un formato de token que puede utilizarse dentro de un sistema de autenticación/autorización; no es por sí mismo un protocolo OAuth.

La implementación sirve para aprender sobre bearer tokens y el esquema de formulario que FastAPI documenta como flujo de contraseña. El endpoint `/auth/token` autentica contra la base propia y entrega JWT; no registra clientes OAuth, no mantiene consentimientos ni emite tokens para acceder a Google, GitHub u otro proveedor. Tampoco es un servidor de autorización OAuth completo.

Para una aplicación nueva con inicio de sesión interactivo, el flujo de contraseña de OAuth2 no es la opción recomendada. Para integrarse con un proveedor de identidad, normalmente se usa OpenID Connect con Authorization Code y PKCE. En una aplicación backend propia, se puede evaluar una biblioteca/servicio de identidad adecuado en vez de convertir este ejemplo en un servidor OAuth completo.

## 9. Qué faltaría antes de producción

Esta base es didáctica, no una solución de autenticación lista para producción. Antes de exponerla públicamente habría que decidir e implementar, entre otras cosas:

- HTTPS y gestión segura del secreto JWT por entorno; rotación de claves.
- Limitación de intentos y protección contra fuerza bruta en login/registro.
- Verificación de correo y recuperación/cambio de contraseña.
- Política para revocar sesiones o tokens comprometidos; aquí no hay refresh tokens ni lista de revocación.
- Auditoría de inicios de sesión y cambios de roles.
- CORS, límites de tamaño y políticas de despliegue según los clientes.
- Pruebas de integración contra PostgreSQL, además de las pruebas rápidas en SQLite.
- Revisión de privacidad, registros, copias de seguridad y manejo de errores operativos.
- Proceso controlado para asignar roles privilegiados y posibles permisos más granulares.

El objetivo de esta primera versión es dejar claros los componentes y sus relaciones, manteniendo el ejemplo pequeño y ejecutable localmente.
