from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def reservar(request):
    return render(request, 'reservas.html')

def disponibilidad(request):
    return render(request, 'disponibilidad.html')

def contacto(request):
    return render(request, 'contacto.html')

def admin_login(request):
    return render(request, 'admin_login.html')

def panel_admin(request):
    return render(request, 'admin.html')