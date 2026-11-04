from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from habitaciones import views as habitaciones_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
  
    path('', habitaciones_views.inicio, name='inicio'), 
    
    
    path('ingreso/', auth_views.LoginView.as_view(template_name='habitaciones/login.html'), name='login'),
    path('salir/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    
    path('habitaciones/', include('habitaciones.urls')),
]