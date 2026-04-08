from django.urls import path
from . import views

urlpatterns = [
    path('panel/cancelar-reserva/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('disponibilidad/json/', views.api_disponibilidad, name='api_disponibilidad'),
    # Páginas principales
    path('', views.index, name='index'),
     # Autenticación
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Recuperación de contraseña
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    
    # Perfil de usuario
    path('perfil/', views.perfil_view, name='perfil'),
    path('disponibilidad/', views.disponibilidad, name='disponibilidad'),
    path('contacto/', views.contacto, name='contacto'),
    path('reservas/', views.reservas, name='reservas'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),  # ← AGREGAR ESTA
    path('admin-logout/', views.admin_logout, name='admin_logout'),  # ← AGREGAR ESTA
    
    # API
    path('api/disponibilidad/', views.api_disponibilidad, name='api_disponibilidad'),
    path('reservar/', views.reservar, name='reservar'),
    path('reservar-emergencia/', views.reservar_emergencia, name='reservar_emergencia'),
    
    # MercadoPago
    path('webhook-mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
    path('pago-exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pago-fallido/', views.pago_fallido, name='pago_fallido'),
    path('pago-pendiente/', views.pago_pendiente, name='pago_pendiente'),
    
    # Pruebas
    path('test-pdf/<int:reserva_id>/', views.test_pdf, name='test_pdf'),
    path('test-email/<int:reserva_id>/', views.test_enviar_email, name='test_email'),
]