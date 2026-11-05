from django.urls import path
from . import views, api_views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("habitaciones/", views.lista_habitaciones, name="lista_habitaciones"),
    path("habitaciones/crear/", views.crear_habitacion, name="crear_habitacion"),
    path("habitaciones/editar/<int:pk>/", views.editar_habitacion, name="editar_habitacion"),
    path("habitaciones/eliminar/<int:pk>/", views.eliminar_habitacion, name="eliminar_habitacion"),
    path("huespedes/", views.lista_huespedes, name="lista_huespedes"),
    path("huespedes/crear/", views.crear_huesped, name="crear_huesped"),
    path("huespedes/editar/<int:pk>/", views.editar_huesped, name="editar_huesped"),
    path("huespedes/eliminar/<int:pk>/", views.eliminar_huesped, name="eliminar_huesped"),
    path("reservas/", views.lista_reservas, name="lista_reservas"),
    path("reservas/crear/", views.crear_reserva, name="crear_reserva"),
    path("reservas/editar/<int:pk>/", views.editar_reserva, name="editar_reserva"),
    path("reservas/eliminar/<int:pk>/", views.eliminar_reserva, name="eliminar_reserva"),
    path("api/token/", api_views.api_login, name="api_login"),
    path("api/logout/", api_views.api_logout, name="api_logout"),
    path("api/habitaciones/", api_views.api_habitaciones, name="api_habitaciones"),
    path("api/habitaciones/<int:pk>/", api_views.api_habitacion_detalle, name="api_habitacion_detalle"),
    path("api/huespedes/", api_views.api_huespedes, name="api_huespedes"),
    path("api/huespedes/<int:pk>/", api_views.api_huesped_detalle, name="api_huesped_detalle"),
    path("api/reservas/", api_views.api_reservas, name="api_reservas"),
    path("api/reservas/<int:pk>/", api_views.api_reserva_detalle, name="api_reserva_detalle"),
]
