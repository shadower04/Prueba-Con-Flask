from django.contrib import admin
from django.urls import path, include
from cancha_reservas import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('cancha_reservas.urls')),
    path("admin-login/", views.admin_login, name="admin_login"),
    path("admin-panel/", views.admin_panel, name="admin_panel"),
    path("admin-logout/", views.admin_logout, name="admin_logout"),
]