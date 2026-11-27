"""Le dice a Swagger que la API usa Authorization: Bearer <JWT> (boton Authorize)."""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTSesionExtension(OpenApiAuthenticationExtension):
    target_class = "habitaciones.autenticacion.JWTSesionAutenticacion"
    name = "bearerAuth"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT",
                "description": "Pega el access_token obtenido en POST /api/login/"}


def ocultar_alias(endpoints):
    """Swagger muestra /api/login/ y /api/refresh/; /api/token/... son rutas equivalentes."""
    return [e for e in endpoints if e[0] not in ("/api/token/", "/api/token/refresh/")]
