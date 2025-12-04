from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('reservar/', views.reservar, name="reservar"),
    path('disponibilidad/', views.disponibilidad, name="disponibilidad"),
    path('contacto/', views.contacto, name="contacto"),
    
    # ADMIN
    path('admin-login/', views.admin_login, name="admin_login"),
    path('admin-logout/', views.admin_logout, name="admin_logout"),
    path('panel-admin/', views.panel_admin, name="panel_admin"),
]