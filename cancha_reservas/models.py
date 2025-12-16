from django.db import models

class Reserva(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente de Pago'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Datos de la reserva
    fecha = models.DateField()
    hora = models.CharField(max_length=20)   # Ej: "14:00-15:00"
    cancha = models.IntegerField()           # 1, 2 o 3
    
    # Datos del cliente
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    
    # Datos de pago
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, default=20000.00)
    seña = models.DecimalField(max_digits=10, decimal_places=2, default=3000.00)  # 15%
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    # MercadoPago
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    preference_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cancha {self.cancha} - {self.fecha} - {self.hora} - {self.nombre}"
    
    class Meta:
        ordering = ['-created_at']