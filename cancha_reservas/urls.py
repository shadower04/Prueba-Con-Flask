from django.urls import path
from . import views

urlpatterns = [
    path('disponibilidad/', views.disponibilidad, name='disponibilidad'),
    path('api/disponibilidad', views.api_disponibilidad, name='api_disponibilidad'),
    path('reservas/', views.reservas, name='reservas'),
    path('reservar/', views.reservar, name='reservar'),
    path('', include('cancha_reservas.urls')),
]
