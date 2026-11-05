# Hotel Aurora – Sistema de gestión de habitaciones (edición Aurora)

Aplicación Django con login, CRUD de habitaciones, API REST con token y base de datos MySQL (XAMPP).

## Requisitos
- Python 3.12 y Git
- XAMPP con **Apache** y **MySQL** iniciados
- Una base de datos vacía llamada `hotel_db` (se crea desde http://localhost/phpmyadmin → Nueva → `hotel_db`)

## Instalación (Windows, CMD)
Desde la carpeta raíz del repositorio (donde está `requirements.txt`):

```bat
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd Proyecto_Hotel
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py test habitaciones
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ e iniciar sesión en `/ingreso/` con el superusuario creado.

> Las migraciones ya están en el repositorio: **no hace falta** `makemigrations`.
> Si MySQL de XAMPP tiene otra contraseña/puerto, se pueden usar las variables de entorno
> `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

## Rutas web
| Ruta | Función |
|---|---|
| `/ingreso/` | Inicio de sesión |
| `/salir/` | Cerrar sesión (botón "Salir") |
| `/` | Panel de inicio (requiere login) |
| `/habitaciones/` | Listado |
| `/habitaciones/crear/` | Crear |
| `/habitaciones/editar/<id>/` | Editar |
| `/habitaciones/eliminar/<id>/` | Eliminar |

## API REST con token
1. Pedir el token: `POST /api/token/` con JSON `{"username": "...", "password": "..."}`.
2. Enviarlo en cada solicitud protegida con el encabezado `Authorization: Token <TOKEN>`.

| Método y ruta | Función | Respuesta |
|---|---|---|
| `GET /api/habitaciones/` | Listar | 200 |
| `POST /api/habitaciones/` | Crear | 201 (400 si hay datos inválidos) |
| `GET /api/habitaciones/<id>/` | Consultar | 200 (404 si no existe) |
| `PUT /api/habitaciones/<id>/` | Actualizar | 200 (400 / 404) |
| `DELETE /api/habitaciones/<id>/` | Eliminar | 204 (404 si no existe) |
| `POST /api/logout/` | Invalidar el token | 200 |

Sin token o con un token inválido todas las rutas de habitaciones responden **401**.
Ejemplos listos para copiar en CMD: ver [`GUIA_DEMO_API.md`](GUIA_DEMO_API.md).

## Validaciones y límites (web, API y login usan las mismas reglas)
- Usuario y contraseña (login web y `POST /api/token/`): obligatorios, máximo 30 caracteres.
- Número de habitación: obligatorio, entero entre 1 y 9999 y único.
- Tipo: obligatorio, entre 3 y 30 caracteres.
- Precio: obligatorio, entero entre 1 y 9.999.999.
- Los datos inválidos nunca se guardan; la web muestra los errores y la API responde 400.

## Sesión
La sesión se cierra al cerrar el navegador y tras 30 minutos sin actividad. Las páginas privadas no se guardan en la memoria del navegador (el botón "Atrás" tras salir pide login de nuevo).

## Interfaz "Aurora" (ambiente tipo hotel misterioso)
- Login con la imagen del lobby y su música; el resto del hotel (inicio, habitaciones, formularios) con la imagen del pasillo y otra música.
- Botón circular abajo a la izquierda para silenciar o activar el sonido (se recuerda la elección).
- Sonido suave al pasar el mouse por botones y enlaces, y "toc" al hacer clic (generados por código, no son archivos).
- Al ingresar, las puertas se cierran y se abren en el hotel. Luz que parpadea, polvo flotante y viñeta.
- Los navegadores solo permiten reproducir sonido tras el primer clic o tecla en la página.
- Archivos: `static/habitaciones/css/aurora.css`, `static/habitaciones/js/aurora.js`, `static/habitaciones/img/` y `static/habitaciones/audio/`.
- Es solo apariencia: no modifica login, validaciones, CRUD ni API.

## Estructura
```
requirements.txt
Proyecto_Hotel/
  manage.py
  sistema_hotel/   (configuración: settings.py, urls.py)
  habitaciones/    (models, forms, views, api_views, serializers, templates, static, tests)
```

## Flujo de Git
Una rama por integrante (`rama-cecilia`, `rama-diego`), commits descriptivos e integración a `main` mediante Merge / Pull Request.
