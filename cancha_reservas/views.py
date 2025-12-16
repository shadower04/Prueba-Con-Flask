from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import EmailMessage
from datetime import date
from .models import Reserva
import json
import mercadopago
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO

# Inicializar SDK de MercadoPago
sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

HORARIOS = [
    "14:00-15:00",
    "15:00-16:00",
    "16:00-17:00",
    "17:00-18:00",
    "18:00-19:00",
]

# ==========================
# FUNCIÓN PARA GENERAR PDF
# ==========================
def generar_pdf_reserva(reserva):
    """Genera un PDF con los detalles de la reserva"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Título
    p.setFont("Helvetica-Bold", 24)
    p.drawString(1*inch, height - 1*inch, 'Cancha 5 "El Golazo"')
    
    # Subtítulo
    p.setFont("Helvetica-Bold", 18)
    p.drawString(1*inch, height - 1.5*inch, 'Comprobante de Reserva')
    
    # Línea separadora
    p.line(1*inch, height - 1.7*inch, width - 1*inch, height - 1.7*inch)
    
    # Datos de la reserva
    y_position = height - 2.2*inch
    p.setFont("Helvetica-Bold", 12)
    
    datos = [
        ('Cliente:', reserva.nombre),
        ('Email:', reserva.email),
        ('Teléfono:', reserva.telefono),
        ('', ''),  # Espacio
        ('Cancha:', f'Cancha {reserva.cancha}'),
        ('Fecha:', str(reserva.fecha)),
        ('Horario:', reserva.hora),
        ('', ''),  # Espacio
        ('Precio Total:', f'${reserva.precio_total}'),
        ('Seña Pagada:', f'${reserva.seña}'),
        ('Saldo Pendiente:', f'${float(reserva.precio_total) - float(reserva.seña)}'),
    ]
    
    for label, value in datos:
        if label:  # Solo si no es línea vacía
            p.setFont("Helvetica-Bold", 12)
            p.drawString(1*inch, y_position, label)
            p.setFont("Helvetica", 12)
            p.drawString(2.5*inch, y_position, value)
        y_position -= 0.3*inch
    
    # Nota al pie
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(1*inch, 1.5*inch, 'Recordá abonar el saldo restante el día de la reserva.')
    p.drawString(1*inch, 1.2*inch, 'Dirección: Av. del Fútbol 1234')
    p.drawString(1*inch, 0.9*inch, 'Teléfono: (011) 1234-5678')
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

# ==========================
# FUNCIÓN PARA ENVIAR EMAIL
# ==========================
def enviar_email_confirmacion(reserva):
    """Envía email con PDF de confirmación"""
    try:
        # Generar PDF
        pdf_buffer = generar_pdf_reserva(reserva)
        
        # Crear email
        subject = f'Confirmación de Reserva - Cancha {reserva.cancha}'
        message = f"""
Hola {reserva.nombre}!

Tu reserva ha sido confirmada exitosamente.

Detalles de la reserva:
- Cancha: {reserva.cancha}
- Fecha: {reserva.fecha}
- Horario: {reserva.hora}
- Seña pagada: ${reserva.seña}
- Saldo pendiente: ${float(reserva.precio_total) - float(reserva.seña)}

Recordá abonar el saldo restante el día de tu reserva.

Adjuntamos el comprobante en PDF.

¡Nos vemos en la cancha!

Cancha 5 "El Golazo"
        """
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[reserva.email],
        )
        
        # Adjuntar PDF
        email.attach(
            f'Reserva_Cancha_{reserva.cancha}_{reserva.fecha}.pdf',
            pdf_buffer.getvalue(),
            'application/pdf'
        )
        
        email.send()
        print(f"✅ Email enviado a {reserva.email}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar email: {str(e)}")
        return False

# ==========================
# VISTAS DE PÁGINAS (HTML)
# ==========================
def admin_login(request):
    return render(request, "admin_login.html")

def index(request):
    return render(request, 'index.html')

def contacto(request):
    return render(request, "contacto.html")

def disponibilidad(request):
    return render(request, "disponibilidad.html", {
        "fecha_hoy": date.today().isoformat()
    })

def reservas(request):
    reservas = Reserva.objects.all()
    return render(request, "reservas.html", {"reservas": reservas})

# ==========================
# API JSON (Disponibilidad)
# ==========================

def api_disponibilidad(request):
    fecha = request.GET.get("fecha")
    
    # Solo mostrar reservas confirmadas como ocupadas
    reservas = Reserva.objects.filter(fecha=fecha, estado='confirmada')

    ocupadas = {}

    for r in reservas:
        if r.hora not in ocupadas:
            ocupadas[r.hora] = []
        ocupadas[r.hora].append(str(r.cancha))

    return JsonResponse({
        "success": True,
        "ocupadas": ocupadas
    })


# ==========================
# RESERVA CON MERCADOPAGO
# ==========================

@csrf_exempt
def reservar(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método no permitido"})

    try:
        data = json.loads(request.body)

        hora = data.get("hora")
        cancha = data.get("cancha")
        fecha = data.get("fecha")
        nombre = data.get("nombre")
        email = data.get("email")
        telefono = data.get("telefono")

        # Validar datos
        if not all([hora, cancha, fecha, nombre, email, telefono]):
            return JsonResponse({"success": False, "message": "❌ Faltan datos obligatorios"})

        # Verificar disponibilidad
        existe = Reserva.objects.filter(
            fecha=fecha, hora=hora, cancha=cancha, estado='confirmada'
        ).exists()

        if existe:
            return JsonResponse({"success": False, "message": "❌ Ya está ocupada"})

        # Crear reserva pendiente
        reserva = Reserva.objects.create(
            fecha=fecha,
            hora=hora,
            cancha=cancha,
            nombre=nombre,
            email=email,
            telefono=telefono,
            estado='pendiente'
        )

        # Crear preferencia de MercadoPago
        preference_data = {
            "items": [
                {
                    "title": f"Seña Cancha {cancha} - {hora}",
                    "description": f"Reserva para el {fecha}",
                    "quantity": 1,
                    "unit_price": float(reserva.seña),
                    "currency_id": "ARS"
                }
            ],
            "payer": {
                "name": nombre,
                "email": email,
                "phone": {
                    "number": telefono
                }
            },
            "back_urls": {
                "success": f"{settings.SITE_URL}/pago-exitoso/?external_reference={reserva.id}",
                "failure": f"{settings.SITE_URL}/pago-fallido/?external_reference={reserva.id}",
                "pending": f"{settings.SITE_URL}/pago-pendiente/?external_reference={reserva.id}"
            },
            "external_reference": str(reserva.id)
        }

        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        # Guardar preference_id
        reserva.preference_id = preference["id"]
        reserva.save()

        return JsonResponse({
            "success": True,
            "message": "Redirigiendo a MercadoPago...",
            "init_point": preference["init_point"],
            "reserva_id": reserva.id
        })
    
    except Exception as e:
        print("ERROR:", str(e))
        return JsonResponse({"success": False, "message": f"❌ Error: {str(e)}"})


# ==========================
# WEBHOOKS Y CONFIRMACIONES
# ==========================

@csrf_exempt
def webhook_mercadopago(request):
    """Webhook para recibir notificaciones de MercadoPago"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            if data.get("type") == "payment":
                payment_id = data["data"]["id"]
                
                # Obtener info del pago
                payment_info = sdk.payment().get(payment_id)
                payment = payment_info["response"]
                
                # Buscar reserva por external_reference
                reserva_id = payment.get("external_reference")
                if reserva_id:
                    reserva = Reserva.objects.get(id=reserva_id)
                    
                    if payment["status"] == "approved":
                        reserva.estado = 'confirmada'
                        reserva.payment_id = str(payment_id)
                        reserva.save()
                        
                        # Enviar email con PDF
                        enviar_email_confirmacion(reserva)
                
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False})


def pago_exitoso(request):
    """Página de confirmación de pago exitoso"""
    payment_id = request.GET.get('payment_id')
    external_reference = request.GET.get('external_reference')
    
    if external_reference:
        try:
            reserva = Reserva.objects.get(id=external_reference)
            reserva.estado = 'confirmada'
            reserva.payment_id = payment_id
            reserva.save()
            
            # Enviar email con PDF
            enviar_email_confirmacion(reserva)
            
            return render(request, 'pago_exitoso.html', {'reserva': reserva})
        except Reserva.DoesNotExist:
            pass
    
    return render(request, 'pago_exitoso.html')


def pago_fallido(request):
    """Página de pago fallido"""
    return render(request, 'pago_fallido.html')


def pago_pendiente(request):
    """Página de pago pendiente"""
    return render(request, 'pago_pendiente.html')

# SOLO PARA TESTING - ELIMINAR EN PRODUCCIÓN
def test_enviar_email(request, reserva_id):
    """Vista temporal para probar el envío de email"""
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        reserva.estado = 'confirmada'
        reserva.save()
        
        resultado = enviar_email_confirmacion(reserva)
        
        if resultado:
            return JsonResponse({"success": True, "message": "Email enviado correctamente"})
        else:
            return JsonResponse({"success": False, "message": "Error al enviar email"})
    except Reserva.DoesNotExist:
        return JsonResponse({"success": False, "message": "Reserva no encontrada"})