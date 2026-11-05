# Hotel Aurora

Sistema de gestión de hotel en Django: login, CRUD de habitaciones, huéspedes y reservas, API REST con token y base de datos MySQL (XAMPP).

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

## Pruebas
```bat
python manage.py test habitaciones
python demo_errores.py --user USUARIO --password CLAVE
```

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

## Interfaz
- Imágenes de fondo, música ambiente y botón para silenciar (abajo a la izquierda).
- Archivos: `static/habitaciones/css`, `static/habitaciones/js`, `static/habitaciones/img` y `static/habitaciones/audio`.
- Solo afecta la apariencia; no modifica login, validaciones, CRUD ni API.

## Estructura
```
requirements.txt
Proyecto_Hotel/
  manage.py
  demo_errores.py  (pruebas de errores contra el servidor)
  sistema_hotel/   (configuración: settings.py, urls.py)
  habitaciones/    (models, forms, views, api_views, serializers, templates, static, tests)
```

## Flujo de Git
Una rama por integrante, commits descriptivos e integración mediante Merge / Pull Request.
