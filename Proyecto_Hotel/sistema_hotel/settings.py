from pathlib import Path
import os

# Rutas
BASE_DIR = Path(__file__).resolve().parent.parent


# Seguridad
SECRET_KEY = 'django-insecure-jz2@i7jh#3^h901fr-6$r*xscs^p7u7-s4h1jpwk7@lqdi)rsz'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'habitaciones',
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sistema_hotel.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema_hotel.wsgi.application'


# Base de datos (MySQL XAMPP)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'hotel_db'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}


# Contrasenas
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Idioma y hora
LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Archivos estaticos
STATIC_URL = 'static/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Login
LOGIN_URL = 'login'

# Sesion persistente (cookie de 1 dia; guarda el id de la tabla Sesion)
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_NAME = 'aurora_sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_NAME = 'aurora_csrftoken'
LOGIN_REDIRECT_URL = '/'

# JWT (se pueden cambiar con variables de entorno; ver README)
JWT_ACCESS_MINUTOS = int(os.environ.get('JWT_ACCESS_MINUTOS', 5))
JWT_REFRESH_MINUTOS = int(os.environ.get('JWT_REFRESH_MINUTOS', 60 * 24))
COOKIE_ACCESS = 'access_token'
COOKIE_REFRESH = 'refresh_token'


# API REST
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'habitaciones.autenticacion.JWTSesionAutenticacion',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'habitaciones.autenticacion.manejador_errores',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Swagger / OpenAPI
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Hotel Aurora',
    'DESCRIPTION': (
        'API REST protegida con JWT.\n\n'
        '1. Usa **POST /api/login/** con tu usuario y contraseña.\n'
        '2. Copia el `access_token` y pulsa **Authorize**: pega solo el token (Swagger agrega "Bearer").\n'
        '3. Cuando el Access expire (401) usa **POST /api/refresh/** con el `refresh_token`.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'PREPROCESSING_HOOKS': ['habitaciones.esquema.ocultar_alias'],
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': True},
    'TAGS': [{'name': 'Autenticación'}, {'name': 'Sesiones'}, {'name': 'Habitaciones'},
             {'name': 'Huéspedes'}, {'name': 'Reservas'}],
}

# Parche XAMPP (version de MariaDB)
import django.db.backends.mysql.base as mysql_base
mysql_base.DatabaseWrapper.check_database_version_supported = lambda self: None
