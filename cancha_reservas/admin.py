from django.contrib import admin
from .models import Reserva
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cancha', 'fecha', 'hora', 'nombre', 'email', 'estado', 'created_at']
    list_filter = ['estado', 'fecha', 'cancha']
    search_fields = ['nombre', 'email', 'telefono']
    ordering = ['-created_at']
    
@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """
    Configuración del modelo Usuario en el admin de Django
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'telefono', 'is_staff', 'fecha_registro')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verificado', 'fecha_registro')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telefono')
    ordering = ('-fecha_registro',)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email', 'telefono')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Información Adicional', {
            'fields': ('email_verificado', 'fecha_registro', 'ultima_actualizacion', 'last_login')
        }),
    )
    
    readonly_fields = ('fecha_registro', 'ultima_actualizacion', 'last_login')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'telefono', 'password1', 'password2'),
        }),
    )
