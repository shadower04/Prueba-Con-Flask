from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("reservar/", views.reservar, name="reservas"),
    path("disponibilidad/", views.disponibilidad, name="disponibilidad"),
    path("contacto/", views.contacto, name="contacto"),
    path("admin-login/", views.admin_login, name="admin_login"),
    path("panel-admin/", views.panel_admin, name="panel_admin"),
]