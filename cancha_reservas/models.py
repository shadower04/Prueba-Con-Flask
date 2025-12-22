# models.py COMPLETO
from django.db import models

class Reserva(models.Model):
    fecha = models.DateField()
    hora = models.CharField(max_length=20)
    cancha = models.IntegerField()
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    seña = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=20, default='pendiente')
    preference_id = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cancha_reservas_reserva'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reserva #{self.id} - Cancha {self.cancha} ({self.fecha} {self.hora})"