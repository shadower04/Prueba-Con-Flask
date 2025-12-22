from django.contrib import admin
from .models import Reserva

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cancha', 'fecha', 'hora', 'nombre', 'email', 'estado', 'created_at']
    list_filter = ['estado', 'fecha', 'cancha']
    search_fields = ['nombre', 'email', 'telefono']
    ordering = ['-created_at']