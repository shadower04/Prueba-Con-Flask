from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta_muy_segura_2025'

# Credenciales de administrador
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Eliminar la tabla existente y crear una nueva con todas las columnas
    cursor.execute('DROP TABLE IF EXISTS reservas')
    
    cursor.execute('''
        CREATE TABLE reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL,
            telefono TEXT NOT NULL,
            cancha INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            duracion INTEGER DEFAULT 1,
            estado TEXT DEFAULT 'confirmada',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos recreada exitosamente")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Por favor inicia sesión para acceder al panel de administración', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Tus rutas normales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reservas')
def reservas():
    return render_template('reservas.html')

@app.route('/disponibilidad')
def disponibilidad():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    return render_template('disponibilidad.html', fecha_hoy=fecha_hoy)

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

# Ruta SIMPLIFICADA para procesar reservas
@app.route('/reservar', methods=['POST'])
def reservar():
    try:
        data = request.get_json()
        print("📝 Datos de reserva recibidos:", data)
        
        hora = data.get('hora')
        cancha = data.get('cancha')
        fecha = data.get('fecha')
        
        if not all([hora, cancha, fecha]):
            return jsonify({
                'success': False,
                'message': 'Faltan datos requeridos'
            })
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Verificar si ya existe reserva
        cursor.execute('''
            SELECT id FROM reservas 
            WHERE cancha = ? AND fecha = ? AND hora = ?
        ''', (cancha, fecha, hora))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Cancha ya reservada en este horario'
            })
        
        # Insertar nueva reserva
        cursor.execute('''
            INSERT INTO reservas (nombre, email, telefono, cancha, fecha, hora)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Reserva Rápida', 'quick@reserva.com', '000-0000', cancha, fecha, hora))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Reserva guardada: Cancha {cancha}, {fecha} {hora}")
        return jsonify({
            'success': True,
            'message': '¡Reserva confirmada exitosamente!'
        })
        
    except Exception as e:
        print("❌ Error en reserva:", str(e))
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

# Ruta SIMPLIFICADA para obtener disponibilidad
@app.route('/api/disponibilidad')
def api_disponibilidad():
    fecha = request.args.get('fecha')
    print(f"📅 Consultando disponibilidad para: {fecha}")
    
    if not fecha:
        return jsonify({'success': False, 'error': 'No se proporcionó fecha'})
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cancha, hora FROM reservas WHERE fecha = ?
        ''', (fecha,))
        
        reservas = cursor.fetchall()
        conn.close()
        
        print(f"📊 Reservas encontradas: {reservas}")
        
        # Crear estructura simple de ocupadas
        ocupadas = {}
        for cancha, hora in reservas:
            if hora not in ocupadas:
                ocupadas[hora] = []
            ocupadas[hora].append(str(cancha))
        
        return jsonify({
            'success': True,
            'ocupadas': ocupadas
        })
        
    except Exception as e:
        print("❌ Error en disponibilidad:", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Ruta de login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reservas ORDER BY created_at DESC')
    reservas = cursor.fetchall()
    conn.close()
    
    return render_template('admin.html', reservas=reservas)

if __name__ == '__main__':
    init_db()
    print("=== Cancha 5 El Golazo ===")
    print("Servidor: http://127.0.0.1:5000")
    print("Admin Login: http://127.0.0.1:5000/admin/login")
    print("⚠️  Base de datos recreada desde cero")
    app.run(debug=True)