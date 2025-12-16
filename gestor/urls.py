from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from cancha_reservas import views

urlpatterns = [
    path('', lambda request: redirect('disponibilidad')),
    path('admin/', admin.site.urls),

    path('disponibilidad/', views.disponibilidad, name='disponibilidad'),
    path('api/disponibilidad/', views.api_disponibilidad, name='api_disponibilidad'),

    path('reservas/', views.reservas, name='reservas'),
    path('reservar/', views.reservar, name='reservar'),
    
    # MercadoPago
    path('webhook-mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
    path('pago-exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pago-fallido/', views.pago_fallido, name='pago_fallido'),
    path('pago-pendiente/', views.pago_pendiente, name='pago_pendiente'),
    
    path('index/', views.index, name='index'),
    path('contacto/', views.contacto, name='contacto'),
    path("admin-login/", views.admin_login, name="admin_login"),
    path('test-email/<int:reserva_id>/', views.test_enviar_email, name='test_email'),
]