from django.urls import path
from . import views
from . import api_views

urlpatterns = [

   
    path("", views.inicio, name="inicio"),
    path("habitaciones/", views.lista_habitaciones, name="lista_habitaciones"),
    path("habitaciones/crear/", views.crear_habitacion, name="crear_habitacion"),
    path("habitaciones/editar/<int:pk>/", views.editar_habitacion, name="editar_habitacion"),
    path("habitaciones/eliminar/<int:pk>/", views.eliminar_habitacion, name="eliminar_habitacion"),
    
    # Rutas API REST
    path("api/habitaciones/", api_views.api_habitaciones, name="api_habitaciones"),
    path("api/habitaciones/<int:pk>/", api_views.api_habitacion_detalle, name="api_habitacion_detalle"),
]