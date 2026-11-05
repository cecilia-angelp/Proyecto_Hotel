from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from habitaciones.forms import LoginForm

urlpatterns = [
    path("admin/", admin.site.urls),
    # Login
    path("ingreso/", auth_views.LoginView.as_view(
        template_name="habitaciones/login.html",
        authentication_form=LoginForm,
        redirect_authenticated_user=True,
    ), name="login"),
    # Logout
    path("salir/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("", include("habitaciones.urls")),
]
