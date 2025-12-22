from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
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
import traceback
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count

# ==========================
# CONFIGURACIÓN INICIAL
# ==========================

# Inicializar SDK de MercadoPago
sdk = mercadopago.SDK(settings.MERCADOPAGO['ACCESS_TOKEN'])

HORARIOS = [
    "14:00-15:00",
    "15:00-16:00",
    "16:00-17:00",
    "17:00-18:00",
    "18:00-19:00",
]

# ==========================
# VISTAS DE ADMINISTRACIÓN
# ==========================

def admin_login(request):
    """Login para administradores"""
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        password = request.POST.get('password')
        
        print(f"🔐 Intento de login - Usuario: {usuario}")
        
        user = authenticate(request, username=usuario, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            print(f"✅ Login exitoso para {usuario}")
            return redirect('admin_panel')
        else:
            print(f"❌ Login fallido para {usuario}")
            messages.error(request, '❌ Usuario o contraseña incorrectos')
    
    return render(request, 'admin_login.html')
@login_required
def admin_panel(request):
    """Panel de administración"""
    # Obtener todas las reservas
    reservas = Reserva.objects.all().order_by('-created_at')
    
    # Calcular estadísticas
    total_reservas = reservas.count()
    
    # Ingresos (suma de señas de reservas confirmadas)
    ingresos = reservas.filter(estado='confirmada').aggregate(
        total=Sum('seña')
    )['total'] or 0
    
    # Tasa de confirmación
    confirmadas = reservas.filter(estado='confirmada').count()
    tasa_confirm = round((confirmadas / total_reservas * 100) if total_reservas > 0 else 0, 1)
    
    context = {
        'reservas': reservas,
        'total_reservas': total_reservas,
        'ingresos': f'{int(ingresos):,}',
        'tasa_confirm': tasa_confirm
    }
    
    return render(request, 'admin.html', context)

def admin_logout(request):
    """Cerrar sesión"""
    logout(request)
    return redirect('index')

# ==========================
# FUNCIÓN PARA GENERAR PDF
# ==========================
def generar_pdf_reserva(reserva):
    """Genera un PDF profesional con los detalles de la reserva"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # ===== HEADER CON FONDO =====
    p.setFillColorRGB(0.16, 0.32, 0.59)
    p.rect(0, height - 2*inch, width, 2*inch, fill=True, stroke=False)
    
    # Título principal
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 32)
    p.drawCentredString(width/2, height - 1*inch, 'Cancha 5 "El Golazo"')
    
    # Subtítulo
    p.setFont("Helvetica", 16)
    p.drawCentredString(width/2, height - 1.4*inch, '⚽ Comprobante de Reserva ⚽')
    
    # ===== SECCIÓN DE DATOS DEL CLIENTE =====
    y_pos = height - 2.8*inch
    
    # Caja de datos del cliente
    p.setFillColorRGB(0.96, 0.96, 0.96)
    p.setStrokeColorRGB(0.16, 0.32, 0.59)
    p.roundRect(1*inch, y_pos - 1.2*inch, width - 2*inch, 1.4*inch, 10, fill=True, stroke=True)
    
    # Título de sección
    p.setFillColorRGB(0.16, 0.32, 0.59)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1.2*inch, y_pos - 0.3*inch, '👤 DATOS DEL CLIENTE')
    
    # Datos del cliente
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 11)
    y_pos -= 0.7*inch
    p.drawString(1.2*inch, y_pos, f'Nombre: {reserva.nombre}')
    y_pos -= 0.25*inch
    p.drawString(1.2*inch, y_pos, f'Email: {reserva.email}')
    y_pos -= 0.25*inch
    p.drawString(1.2*inch, y_pos, f'Teléfono: {reserva.telefono}')
    
    # ===== SECCIÓN DE RESERVA =====
    y_pos -= 0.8*inch
    
    # Caja de datos de reserva
    p.setFillColorRGB(0.91, 0.96, 0.97)
    p.setStrokeColorRGB(0.16, 0.32, 0.59)
    p.roundRect(1*inch, y_pos - 1.2*inch, width - 2*inch, 1.4*inch, 10, fill=True, stroke=True)
    
    # Título de sección
    p.setFillColorRGB(0.16, 0.32, 0.59)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1.2*inch, y_pos - 0.3*inch, '📅 DETALLES DE LA RESERVA')
    
    # Datos de la reserva
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 12)
    y_pos -= 0.7*inch
    p.drawString(1.2*inch, y_pos, f'Cancha {reserva.cancha}')
    p.setFont("Helvetica", 11)
    p.drawString(2.5*inch, y_pos, f'|  Fecha: {reserva.fecha}')
    p.drawString(4.5*inch, y_pos, f'|  Horario: {reserva.hora}')
    
    # ===== SECCIÓN DE PAGO =====
    y_pos -= 0.8*inch
    
    # Caja de pago
    p.setFillColorRGB(1, 0.95, 0.9)
    p.setStrokeColorRGB(1, 0.42, 0.21)
    p.roundRect(1*inch, y_pos - 1.4*inch, width - 2*inch, 1.6*inch, 10, fill=True, stroke=True)
    
    # Título de sección
    p.setFillColorRGB(1, 0.42, 0.21)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1.2*inch, y_pos - 0.3*inch, '💰 INFORMACIÓN DE PAGO')
    
    # Detalles de pago
    y_pos -= 0.65*inch
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 11)
    p.drawString(1.2*inch, y_pos, 'Precio Total:')
    p.setFont("Helvetica-Bold", 11)
    p.drawString(5*inch, y_pos, f'${int(reserva.precio_total):,}')
    
    y_pos -= 0.3*inch
    p.setFont("Helvetica", 11)
    p.setFillColorRGB(0, 0.5, 0)
    p.drawString(1.2*inch, y_pos, 'Seña Pagada:')
    p.setFont("Helvetica-Bold", 11)
    p.drawString(5*inch, y_pos, f'${int(reserva.seña):,}')
    
    y_pos -= 0.3*inch
    saldo = float(reserva.precio_total) - float(reserva.seña)
    p.setFont("Helvetica-Bold", 12)
    p.setFillColorRGB(1, 0.42, 0.21)
    p.drawString(1.2*inch, y_pos, 'Saldo Pendiente:')
    p.setFont("Helvetica-Bold", 12)
    p.drawString(5*inch, y_pos, f'${int(saldo):,}')
    
    # ===== NOTA IMPORTANTE =====
    y_pos -= 0.8*inch
    p.setFillColorRGB(1, 0.95, 0.8)
    p.setStrokeColorRGB(1, 0.75, 0)
    p.roundRect(1*inch, y_pos - 0.8*inch, width - 2*inch, 1*inch, 10, fill=True, stroke=True)
    
    p.setFillColorRGB(0.6, 0.4, 0)
    p.setFont("Helvetica-Bold", 11)
    y_pos -= 0.35*inch
    p.drawString(1.2*inch, y_pos, '⚠️ IMPORTANTE: Recordá abonar el saldo restante el día de la reserva.')
    
    # ===== PIE DE PÁGINA =====
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.setFont("Helvetica", 9)
    p.drawCentredString(width/2, 1.2*inch, '📍 Av. del Fútbol 1234')
    p.drawCentredString(width/2, 1*inch, '📞 (011) 1234-5678  |  ✉️ info@elgolazo.com')
    
    # Línea decorativa
    p.setStrokeColorRGB(0.16, 0.32, 0.59)
    p.line(1.5*inch, 0.8*inch, width - 1.5*inch, 0.8*inch)
    
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width/2, 0.5*inch, f'Reserva ID: #{reserva.id} | Generado el {date.today().strftime("%d/%m/%Y")}')
    
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
        print(f"❌ ERROR en enviar_email_confirmacion: {str(e)}")
        return False

# ==========================
# VISTAS DE PÁGINAS (HTML)
# ==========================
def admin_login(request):
    return render(request, "admin_login.html")

def index(request):
    CANCHAS_DISPONIBLES = [
        {'id': 1, 'nombre': 'Cancha 1'},
        {'id': 2, 'nombre': 'Cancha 2'}, 
        {'id': 3, 'nombre': 'Cancha 3'}
    ]
    return render(request, 'index.html', {
        'canchas': CANCHAS_DISPONIBLES 
    })

def contacto(request):
    return render(request, "contacto.html")

def disponibilidad(request):
    return render(request, "disponibilidad.html", {
        "fecha_hoy": date.today().isoformat()
    })

def reservas(request):
    """Muestra todas las reservas"""
    reservas_lista = Reserva.objects.all().order_by('-created_at')
    return render(request, "reservas.html", {"reservas": reservas_lista})

# ==========================
# API DISPONIBILIDAD
# ==========================
def api_disponibilidad(request):
    """API para consultar disponibilidad"""
    try:
        fecha = request.GET.get("fecha")
        if not fecha:
            return JsonResponse({"success": False, "error": "Fecha no especificada"})
        
        # Solo mostrar reservas confirmadas como ocupadas
        reservas_ocupadas = Reserva.objects.filter(fecha=fecha, estado='confirmada')
        
        ocupadas = {}
        for r in reservas_ocupadas:
            if r.hora not in ocupadas:
                ocupadas[r.hora] = []
            ocupadas[r.hora].append(str(r.cancha))
        
        return JsonResponse({
            "success": True,
            "ocupadas": ocupadas,
            "fecha": fecha
        })
        
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

# ==========================
# RESERVA CON MERCADOPAGO (VERSIÓN ÚNICA Y CORREGIDA)
# ==========================
@csrf_exempt
def reservar(request):
    """Crea una nueva reserva con MercadoPago - VERSIÓN DEBUG"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método no permitido"})

    try:
        print("\n" + "="*80)
        print("🚀 INICIANDO PROCESO DE RESERVA - DEBUG MODE")
        print("="*80)
        
        # Leer datos JSON
        data = json.loads(request.body)
        print(f"📦 1. Datos recibidos del frontend:")
        print(f"   {data}")
        
        # Extraer datos
        hora = str(data.get("hora", "")).strip()
        cancha_raw = data.get("cancha")
        fecha = str(data.get("fecha", "")).strip()
        nombre = str(data.get("nombre", "")).strip()
        email = str(data.get("email", "")).strip()
        telefono = str(data.get("telefono", "")).strip()
        
        # Convertir cancha
        try:
            cancha = int(cancha_raw)
        except (ValueError, TypeError):
            print(f"❌ Cancha inválida: {cancha_raw}")
            return JsonResponse({
                "success": False, 
                "message": "Cancha debe ser un número (1, 2 o 3)"
            })
        
        print(f"✅ 2. Datos procesados:")
        print(f"   Hora: {hora}")
        print(f"   Cancha: {cancha} (tipo: {type(cancha)})")
        print(f"   Fecha: {fecha}")
        print(f"   Nombre: {nombre}")
        print(f"   Email: {email}")
        print(f"   Teléfono: {telefono}")
        
        # Validación
        if not all([hora, fecha, nombre, email, telefono]):
            print("❌ Campos faltantes")
            return JsonResponse({
                "success": False, 
                "message": "Todos los campos son obligatorios"
            })
        
        # Verificar disponibilidad
        existe = Reserva.objects.filter(
            fecha=fecha, hora=hora, cancha=cancha, estado='confirmada'
        ).exists()
        
        if existe:
            print(f"❌ Cancha {cancha} ya ocupada en {fecha} {hora}")
            return JsonResponse({
                "success": False, 
                "message": "Este horario ya está ocupado"
            })
        
        print("✅ 3. Disponibilidad verificada")
        
        # ===== CALCULAR PRECIOS =====
        precios_cancha = {1: 20000.00, 2: 60000.00, 3: 80000.00}
        precio_total = precios_cancha.get(cancha, 20000.00)
        seña = round(precio_total * 0.15, 2)
        
        print(f"💰 4. Precios calculados:")
        print(f"   Precio total: ${precio_total:,.2f}")
        print(f"   Seña (15%): ${seña:,.2f}")
        
        # ===== CREAR RESERVA =====
        try:
            reserva = Reserva.objects.create(
                fecha=fecha, hora=hora, cancha=cancha,
                nombre=nombre, email=email, telefono=telefono,
                precio_total=precio_total, seña=seña, estado='pendiente'
            )
            print(f"✅ 5. Reserva creada en BD - ID: {reserva.id}")
            
        except Exception as db_error:
            print(f"❌ Error al crear reserva: {str(db_error)}")
            return JsonResponse({
                "success": False, 
                "message": f"Error al crear reserva: {str(db_error)}"
            })
        
        # ===== CONECTAR CON MERCADOPAGO =====
        print("🔄 6. Conectando con MercadoPago...")
        
        # Verificar token
        mp_token = settings.MERCADOPAGO.get('ACCESS_TOKEN', '')
        print(f"   Token MP: {mp_token[:30]}...")
        
        if not mp_token:
            print("❌ ERROR: No hay token de MercadoPago configurado")
            return JsonResponse({
                "success": False, 
                "message": "Error de configuración del sistema de pagos"
            })
        
        # Crear datos de la preferencia
        preference_data = {
            "items": [
                {
                    "id": str(reserva.id),
                    "title": f"Seña Cancha {cancha} - {hora}",
                    "description": f"Reserva para {fecha} - Cancha {cancha}",
                    "quantity": 1,
                    "currency_id": "ARS",
                    "unit_price": float(seña)
                }
            ],
            "payer": {
                "name": nombre,
                "surname": "",
                "email": email,
                "phone": {
                    "area_code": "11",  # Buenos Aires
                    "number": telefono[-8:] if len(telefono) > 8 else telefono
                },
                "identification": {
                    "type": "DNI",
                    "number": "12345678"  # Puedes pedir esto o usar un valor por defecto
                }
            },
            "back_urls": {
                "success": "http://127.0.0.1:8000/pago-exitoso/",
                "failure": "http://127.0.0.1:8000/pago-fallido/",
                "pending": "http://127.0.0.1:8000/pago-pendiente/"
            },
            "external_reference": str(reserva.id),
        }
        
        print(f"📤 7. Enviando a MercadoPago:")
        print(f"   Datos: {json.dumps(preference_data, indent=2, ensure_ascii=False)}")
        
        try:
            # Intentar crear la preferencia
            preference_response = sdk.preference().create(preference_data)
            print(f"📥 8. Respuesta de MercadoPago recibida")
            
            # DEBUG: Mostrar respuesta completa
            print(f"   Respuesta completa: {json.dumps(preference_response, indent=2, ensure_ascii=False)}")
            
            if "response" not in preference_response:
                print("❌ ERROR: MercadoPago no devolvió 'response'")
                print(f"   Respuesta: {preference_response}")
                
                # Intentar obtener más detalles del error
                if "error" in preference_response:
                    print(f"   Error MP: {preference_response['error']}")
                    error_msg = preference_response['error'].get('message', 'Error desconocido')
                else:
                    error_msg = "MercadoPago no respondió correctamente"
                
                return JsonResponse({
                    "success": False, 
                    "message": f"❌ Error MercadoPago: {error_msg}"
                })
            
            preference = preference_response["response"]
            print(f"✅ 9. Preferencia creada - ID: {preference.get('id')}")
            
            if "init_point" not in preference:
                print("❌ ERROR: No hay 'init_point' en la respuesta")
                print(f"   Campos disponibles: {list(preference.keys())}")
                
                # Buscar link de pago en otros campos
                if "sandbox_init_point" in preference:
                    print(f"   ✅ Encontrado sandbox_init_point")
                    init_point = preference["sandbox_init_point"]
                else:
                    print(f"   Respuesta completa: {preference}")
                    return JsonResponse({
                        "success": False, 
                        "message": "MercadoPago no generó link de pago"
                    })
            else:
                init_point = preference["init_point"]
            
            print(f"🔗 10. Link de pago generado:")
            print(f"   {init_point}")
            
            # Guardar ID de preferencia
            reserva.preference_id = preference.get("id")
            reserva.save()
            
            print("="*80)
            print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
            print("="*80)
            
            return JsonResponse({
                "success": True,
                "message": "Redirigiendo a MercadoPago...",
                "init_point": init_point,
                "reserva_id": reserva.id,
                "preference_id": preference.get("id"),
                "seña": seña
            })
            
        except Exception as mp_error:
            print(f"❌ ERROR con MercadoPago: {str(mp_error)}")
            import traceback
            traceback.print_exc()
            
            # Marcar reserva como fallida
            reserva.estado = 'error_mp'
            reserva.save()
            
            return JsonResponse({
                "success": False, 
                "message": f"Error al conectar con MercadoPago: {str(mp_error)}"
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False, 
            "message": "❌ Datos en formato incorrecto"
        })
        
    except Exception as e:
        print(f"❌ ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False, 
            "message": f"Error del sistema: {str(e)}"
        })
# ==========================
# WEBHOOK MERCADOPAGO
# ==========================
@csrf_exempt
def webhook_mercadopago(request):
    """Webhook para recibir notificaciones de MercadoPago"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(f"🔔 Webhook recibido: {data}")
            
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
                        print(f"✅ Reserva {reserva_id} confirmada vía webhook")
                
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"❌ Error en webhook: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Método no permitido"})

# ==========================
# VISTAS DE PAGO
# ==========================
def pago_exitoso(request):
    """Página de confirmación de pago exitoso"""
    try:
        payment_id = request.GET.get('payment_id')
        external_reference = request.GET.get('external_reference')
        
        print(f"🔍 pago_exitoso - external_reference: {external_reference}")
        
        if external_reference:
            try:
                reserva = Reserva.objects.get(id=external_reference)
                
                # Solo actualizar si está pendiente
                if reserva.estado == 'pendiente':
                    reserva.estado = 'confirmada'
                    if payment_id:
                        reserva.payment_id = payment_id
                    reserva.save()
                    
                    # Enviar email
                    enviar_email_confirmacion(reserva)
                    print(f"✅ Reserva {reserva.id} confirmada desde pago_exitoso")
                
                return render(request, 'pago_exitoso.html', {
                    'reserva': reserva,
                    'payment_id': payment_id
                })
                
            except Reserva.DoesNotExist:
                print(f"❌ Reserva no encontrada: {external_reference}")
                return render(request, 'pago_exitoso.html', {
                    'reserva': None,
                    'error': 'Reserva no encontrada'
                })
        
        return render(request, 'pago_exitoso.html', {'reserva': None})
        
    except Exception as e:
        print(f"❌ Error en pago_exitoso: {str(e)}")
        return render(request, 'pago_exitoso.html', {
            'reserva': None,
            'error': str(e)
        })

def pago_fallido(request):
    """Página de pago fallido"""
    external_reference = request.GET.get('external_reference')
    
    if external_reference:
        try:
            reserva = Reserva.objects.get(id=external_reference)
            return render(request, 'pago_fallido.html', {'reserva': reserva})
        except:
            pass
    
    return render(request, 'pago_fallido.html')

def pago_pendiente(request):
    """Página de pago pendiente"""
    external_reference = request.GET.get('external_reference')
    
    if external_reference:
        try:
            reserva = Reserva.objects.get(id=external_reference)
            return render(request, 'pago_pendiente.html', {'reserva': reserva})
        except:
            pass
    
    return render(request, 'pago_pendiente.html')

# ==========================
# VISTAS DE PRUEBA
# ==========================
def test_pdf(request, reserva_id):
    """Descargar PDF de prueba"""
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        pdf_buffer = generar_pdf_reserva(reserva)
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reserva_{reserva_id}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

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
            return JsonResponse({
                "success": False, 
                "message": "La función enviar_email_confirmacion() devolvió False"
            })
            
    except Reserva.DoesNotExist:
        return JsonResponse({"success": False, "message": "Reserva no encontrada"})
    
    except Exception as e:
        return JsonResponse({
            "success": False, 
            "message": f"Error: {str(e)}",
            "error_type": type(e).__name__
        })

# ==========================
# VISTA DE EMERGENCIA
# ==========================
@csrf_exempt
def reservar_emergencia(request):
    """Versión simplificada para debug"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("🆘 RESERVA EMERGENCIA - Datos:", data)
            
            # Crear reserva mínima
            reserva = Reserva()
            reserva.fecha = data.get("fecha", "2024-01-01")
            reserva.hora = data.get("hora", "14:00-15:00")
            reserva.cancha = 1
            reserva.nombre = data.get("nombre", "Test")
            reserva.email = data.get("email", "test@test.com")
            reserva.telefono = data.get("telefono", "1234567890")
            reserva.precio_total = 20000.00
            reserva.seña = 3000.00
            reserva.estado = 'pendiente'
            reserva.save()
            
            print(f"✅ RESERVA EMERGENCIA CREADA - ID: {reserva.id}")
            
            # Pago simple en MP
            preference_data = {
                "items": [{
                    "title": "Seña Cancha 1",
                    "quantity": 1,
                    "unit_price": 3000.00,
                    "currency_id": "ARS"
                }],
                "back_urls": {
                    "success": f"http://127.0.0.1:8000/pago-exitoso/?external_reference={reserva.id}",
                },
                "external_reference": str(reserva.id),
            }
            
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]
            
            return JsonResponse({
                "success": True,
                "init_point": preference["init_point"],
                "reserva_id": reserva.id
            })
            
        except Exception as e:
            print(f"❌ ERROR EMERGENCIA: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    return JsonResponse({"success": False, "message": "Método no permitido"})