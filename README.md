# Hotel Aurora (EVA04)

Sistema de gestión de hotel en Django: login con **JWT (Access + Refresh)**, sesión persistente registrada en MySQL,
CRUD de habitaciones, huéspedes y reservas, API REST documentada con **Swagger** y colección de **Postman**.

## Requisitos
- Python 3.12 y Git
- XAMPP con **Apache** y **MySQL** iniciados
- Una base de datos vacía llamada `hotel_db` (http://localhost/phpmyadmin → Nueva → `hotel_db`)

## Instalación (Windows, CMD)
Desde la carpeta raíz del repositorio (donde está `requirements.txt`):

```bat
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd Proyecto_Hotel
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ → entra al login (`/ingreso/`) con el usuario creado.
Las migraciones ya están en el repositorio: **no hace falta** `makemigrations`.
Si MySQL tiene otra clave/puerto: variables de entorno `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

## Cómo funciona la sesión (resumen)
1. El formulario de login envía `POST /api/login/` (JSON). La API valida usuario y clave.
2. Si es correcto crea una fila en la tabla **`habitaciones_sesion`** (usuario, `jti` de cada token, tokens completos, vencimientos, activa) y responde **200** con `access_token` y `refresh_token`.
3. Los tokens quedan en **cookies** (F12 → Application → Cookies), no en localStorage ni sessionStorage:
   - `access_token` (la lee JavaScript y la manda como `Authorization: Bearer ...`)
   - `refresh_token` (HttpOnly: JavaScript no puede leerla)
   - `aurora_sessionid` (sesión persistente de Django, 1 día)
4. Cada acción del sitio llama a la API con el verbo real: **POST** (crear), **PUT** (modificar), **DELETE** (eliminar).
5. Si el Access vence (**401**), el navegador llama a `POST /api/refresh/` y repite la acción. La BD guarda el Access nuevo.
6. **Salir** llama a `POST /api/logout/`: la sesión queda `activa = 0` y los dos tokens dejan de servir aunque no hayan vencido.
7. Las páginas HTML están protegidas por el decorador propio `@sesion_requerida` (`habitaciones/decoradores.py`, usa `functools.wraps`): sin sesión válida redirige al login.

Duración por defecto: Access **5 minutos**, Refresh **1 día**. Para una demo rápida (CMD, antes de `runserver`):
```bat
set JWT_ACCESS_MINUTOS=1
```

Los tokens se ven en F12 → Application → Cookies y en la tabla `habitaciones_sesion` (phpMyAdmin → `hotel_db` → `habitaciones_sesion` → Examinar): son los mismos.

## Códigos HTTP que usa la API
Solo los vistos en clase: **200, 201, 400, 401, 404**.

| Método y ruta | Función | Respuestas |
|---|---|---|
| `POST /api/login/` | Login: genera Access y Refresh | 200 / 400 (faltan datos) / 401 (credenciales) |
| `POST /api/refresh/` | Renueva el Access con el Refresh | 200 / 400 (no se envió) / 401 (inválido, expirado o revocado) |
| `GET /api/perfil/` | Perfil del usuario (endpoint protegido de ejemplo) | 200 / 401 |
| `POST /api/logout/` | Cierra y revoca la sesión | 200 / 401 |
| `GET /api/sesiones/` · `DELETE /api/sesiones/<id>/` | Administrar sesiones | 200 / 401 / 404 |
| `GET /api/habitaciones/` | Listar | 200 / 401 |
| `POST /api/habitaciones/` | Crear | 201 / 400 / 401 |
| `GET /api/habitaciones/<id>/` | Consultar | 200 / 401 / 404 |
| `PUT /api/habitaciones/<id>/` | Modificar | 200 / 400 / 401 / 404 |
| `DELETE /api/habitaciones/<id>/` | Eliminar | 200 / 401 / 404 |

Lo mismo para `/api/huespedes/` y `/api/reservas/`.
También funcionan las rutas equivalentes de la clase: `POST /api/token/` (login) y `POST /api/token/refresh/` (el cuerpo puede llevar `refresh_token` o `refresh`). Todas las rutas protegidas exigen `Authorization: Bearer <access_token>`;
sin token, con token inválido, expirado o revocado responden **401** con `{"error": "..."}`.

Las páginas web solo usan **GET** (mostrar páginas). Un `302` aparece únicamente cuando se entra a una página protegida sin sesión (redirige al login).

## Swagger / OpenAPI
- http://127.0.0.1:8000/api/docs/ (Swagger UI) y http://127.0.0.1:8000/api/schema/ (OpenAPI).
- Hacer `POST /api/login/` desde Swagger → copiar `access_token` → botón **Authorize** → pegar solo el token.

## Postman
Importar `postman/Hotel_Aurora_JWT.postman_collection.json` y ejecutar con *Run collection* (el servidor debe estar corriendo; usuario/clave en las variables de la colección).
Incluye login, refresh, uso del Access, CRUD completo, errores 400/404 y casos de token ausente/inválido/expirado/revocado (401).

## Pruebas
```bat
cd Proyecto_Hotel
python manage.py test habitaciones
```

## Validaciones
- Usuario y contraseña: obligatorios, máximo 30 caracteres.
- Habitación: número entero 1–9999 y único; tipo 3–30 caracteres; precio entero 1–9.999.999.
- Huésped: nombre/apellido solo letras, RUT válido y único, correo válido, teléfono de 9 dígitos.
- Reserva: máximo 30 noches, sin choque de fechas, 1–6 personas, estados con transiciones permitidas.
- Los datos inválidos nunca se guardan: la API responde 400 y la web muestra la lista de errores.

## Detalles de la interfaz

- **Contador de sesión** en la barra: tiempo restante del Access token; al llegar a 0 se renueva solo con el Refresh.
- **Avisos deslizantes** (con campanita) al crear, modificar, eliminar o renovar la sesión.
- **Puertas** al entrar y al salir (el login/logout se hace en paralelo con la animación).
- **Habitaciones como puertas** (botón Puertas / Tabla).
- **Tarjeta de check-in** al crear una reserva.

Ninguno guarda datos: son efectos de CSS/JS sobre la misma API.

## Estructura
```
requirements.txt
postman/                      (colección de Postman)
GUIA_DEMO_API.md · PREGUNTAS_ORALES.md
Proyecto_Hotel/
  manage.py
  demo_errores.py             (recorre la API y muestra los códigos)
  sistema_hotel/              (settings.py, urls.py)
  habitaciones/
    models.py                 (Habitacion, Huesped, Reserva, Sesion)
    tokens.py                 (JWT con PyJWT: crear, validar, renovar, revocar)
    autenticacion.py          (autenticación Bearer de la API, errores en JSON, cookies)
    decoradores.py            (@sesion_requerida)
    api_views.py · serializers.py · views.py · urls.py
    templates/ · static/ · tests.py
```

## Flujo de Git
Una rama por integrante, commits descriptivos e integración mediante Merge a la rama principal.
