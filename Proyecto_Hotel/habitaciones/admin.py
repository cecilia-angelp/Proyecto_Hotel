from django.contrib import admin

from .models import Habitacion, Huesped, Reserva, Sesion

admin.site.register(Habitacion)
admin.site.register(Huesped)
admin.site.register(Reserva)


@admin.register(Sesion)
class SesionAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "activa", "creada", "access_expira", "refresh_expira", "ip")
    list_filter = ("activa",)
    readonly_fields = ("jti_access", "jti_refresh", "access_token", "refresh_token", "creada", "actualizada")
