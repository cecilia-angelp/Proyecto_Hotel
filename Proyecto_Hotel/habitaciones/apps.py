from django.apps import AppConfig


class HabitacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'habitaciones'

    def ready(self):
        from . import esquema  # noqa: F401  (registra el esquema Bearer de Swagger)
