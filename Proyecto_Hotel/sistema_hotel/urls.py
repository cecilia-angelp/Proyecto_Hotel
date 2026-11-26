from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from habitaciones import views


def devtools(request):
    # Chrome lo pide al abrir F12; se responde 200 para que no ensucie la consola
    return JsonResponse({})


urlpatterns = [
    path("admin/", admin.site.urls),
    # Login (pagina)
    path("ingreso/", views.ingreso, name="login"),
    # Documentacion Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path(".well-known/appspecific/com.chrome.devtools.json", devtools),
    path("", include("habitaciones.urls")),
]
