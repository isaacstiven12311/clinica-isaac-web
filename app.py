# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import os
import pymysql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clinica-isaac-secret-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Variables de entorno para MySQL
MYSQL_HOST = os.environ.get('MYSQLHOST', 'mysql.railway.internal')
MYSQL_PORT = int(os.environ.get('MYSQLPORT', 3306))
MYSQL_USER = os.environ.get('MYSQLUSER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQLPASSWORD', 'siqZiYNigHVZxuqVSxDTCQQxGhAPFdqd')
MYSQL_DATABASE = os.environ.get('MYSQLDATABASE', 'railway')

usuarios_conectados = 0

# ========================================
# FUNCIONES DE BASE DE DATOS
# ========================================

def get_db_connection():
    """Crea conexión a MySQL"""
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        return None

def init_database():
    """Crea las tablas si no existen"""
    conn = get_db_connection()
    if not conn:
        print("❌ No se pudo conectar para inicializar BD")
        return
    
    try:
        cursor = conn.cursor()
        
        # Tabla Pacientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Paciente (
                id_paciente INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                edad INT NOT NULL,
                ciudad VARCHAR(50) NOT NULL,
                consultorio VARCHAR(50) NOT NULL,
                causa TEXT NOT NULL,
                fecha_ingreso DATE NOT NULL
            )
        """)
        
        # Tabla Citas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Cita (
                id_cita INT AUTO_INCREMENT PRIMARY KEY,
                id_paciente INT NOT NULL,
                motivo TEXT NOT NULL,
                fecha DATETIME NOT NULL,
                FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        
        # Insertar datos de prueba si no hay pacientes
        cursor.execute("SELECT COUNT(*) as total FROM Paciente")
        result = cursor.fetchone()
        
        if result['total'] == 0:
            pacientes_iniciales = [
                ('Carlos Pérez', 45, 'Bogotá', 'Consultorio 101', 'Chequeo general', '2024-01-15'),
                ('Ana Gómez', 29, 'Medellín', 'Consultorio 202', 'Dolor de cabeza', '2024-01-16'),
                ('Luis Torres', 38, 'Cali', 'Consultorio 303', 'Control de presión', '2024-01-17')
            ]
            
            cursor.executemany(
                "INSERT INTO Paciente (nombre, edad, ciudad, consultorio, causa, fecha_ingreso) VALUES (%s, %s, %s, %s, %s, %s)",
                pacientes_iniciales
            )
            conn.commit()
            print("✅ Datos iniciales insertados")
        
        cursor.close()
        conn.close()
        print("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"❌ Error inicializando BD: {e}")
        if conn:
            conn.close()

# Inicializar BD al arrancar
init_database()

# ========================================
# RUTAS DE LA API
# ========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pacientes', methods=['GET'])
def listar_pacientes():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a BD'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Paciente ORDER BY id_paciente DESC")
        pacientes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(pacientes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pacientes', methods=['POST'])
def agregar_paciente():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a BD'}), 500
    
    try:
        data = request.json
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO Paciente (nombre, edad, ciudad, consultorio, causa, fecha_ingreso) VALUES (%s, %s, %s, %s, %s, %s)",
            (data['nombre'], int(data['edad']), data['ciudad'], data['consultorio'], data['causa'], datetime.now().date())
        )
        
        conn.commit()
        paciente_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM Paciente WHERE id_paciente = %s", (paciente_id,))
        nuevo_paciente = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        socketio.emit('paciente_agregado', nuevo_paciente, broadcast=True)
        return jsonify({'mensaje': 'Paciente agregado exitosamente', 'paciente': nuevo_paciente}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pacientes/<int:id>', methods=['DELETE'])
def eliminar_paciente(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a BD'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Paciente WHERE id_paciente = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        socketio.emit('paciente_eliminado', {'id': id}, broadcast=True)
        return jsonify({'mensaje': f'Paciente {id} eliminado'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/citas', methods=['POST'])
def registrar_cita():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a BD'}), 500
    
    try:
        data = request.json
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO Cita (id_paciente, motivo, fecha) VALUES (%s, %s, %s)",
            (int(data['id_paciente']), data['motivo'], datetime.now())
        )
        
        conn.commit()
        cita_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM Cita WHERE id_cita = %s", (cita_id,))
        nueva_cita = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({'mensaje': 'Cita registrada', 'cita': nueva_cita}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a BD'}), 500
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM Paciente")
        total_pacientes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM Cita")
        total_citas = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_pacientes': total_pacientes,
            'total_citas': total_citas,
            'usuarios_conectados': usuarios_conectados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    # ========================================
# WEBSOCKETS - CHATBOT MEJORADO
# ========================================

@socketio.on('connect')
def handle_connect():
    global usuarios_conectados
    usuarios_conectados += 1
    print(f'✅ Cliente conectado. Total: {usuarios_conectados}')
    emit('mensaje_servidor', {'texto': '¡Bienvenido a Clínica Isaac! 👋 Escribe "ayuda" para ver los comandos disponibles.', 'tipo': 'bienvenida'})
    emit('usuarios_conectados', {'total': usuarios_conectados}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global usuarios_conectados
    usuarios_conectados = max(0, usuarios_conectados - 1)
    emit('usuarios_conectados', {'total': usuarios_conectados}, broadcast=True)

@socketio.on('mensaje_cliente')
def handle_mensaje(data):
    mensaje = data['mensaje'].strip()
    mensaje_lower = mensaje.lower()
    
    conn = get_db_connection()
    if not conn:
        emit('mensaje_servidor', {'texto': '❌ Error de conexión a la base de datos', 'tipo': 'error'})
        return
    
    cursor = conn.cursor()
    respuesta = ""
    
    try:
        # ===== COMANDOS DE SALUDO =====
        if any(saludo in mensaje_lower for saludo in ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'hi', 'hello']):
            respuesta = '¡Hola! 👋 Soy el asistente de Clínica Isaac. ¿En qué puedo ayudarte?\n\n💡 Escribe "ayuda" para ver todos los comandos.'
        
        # ===== COMANDO: AYUDA =====
        elif 'ayuda' in mensaje_lower or mensaje_lower == '?' or mensaje_lower == 'help':
            respuesta = """📋 COMANDOS DISPONIBLES:

🔍 BUSCAR:
- "buscar [nombre]" - Busca pacientes por nombre
- Ejemplo: buscar Carlos

👤 VER PACIENTE:
- "ver [id]" - Ver detalles completos de un paciente
- Ejemplo: ver 1

📊 LISTAR:
- "listar" o "pacientes" - Ver todos los pacientes
- "listar [ciudad]" - Pacientes de una ciudad específica
- Ejemplo: listar Bogotá

➕ AGREGAR:
- "agregar [nombre]|[edad]|[ciudad]|[consultorio]|[causa]"
- Ejemplo: agregar Juan Pérez|30|Cali|101|Gripe

🗑️ ELIMINAR:
- "eliminar [id]" - Eliminar paciente por ID
- Ejemplo: eliminar 5

📅 CITA:
- "cita [id]|[motivo]" - Registrar cita
- Ejemplo: cita 1|Consulta de seguimiento

📈 ESTADÍSTICAS:
- "estadísticas" - Ver estadísticas generales
- "edad promedio" - Edad promedio de pacientes
- "ciudad más común" - Ciudad con más pacientes

💬 También puedo entender lenguaje natural!"""
        
        # ===== BUSCAR PACIENTE =====
        elif 'buscar' in mensaje_lower:
            nombre_buscar = mensaje_lower.replace('buscar', '').strip()
            if nombre_buscar:
                cursor.execute("SELECT * FROM Paciente WHERE nombre LIKE %s", (f'%{nombre_buscar}%',))
                pacientes = cursor.fetchall()
                
                if pacientes:
                    respuesta = f"🔍 Encontré {len(pacientes)} paciente(s):\n\n"
                    for p in pacientes:
                        respuesta += f"🆔 ID: {p['id_paciente']}\n"
                        respuesta += f"👤 Nombre: {p['nombre']}\n"
                        respuesta += f"🎂 Edad: {p['edad']} años\n"
                        respuesta += f"🌆 Ciudad: {p['ciudad']}\n"
                        respuesta += f"🏥 Consultorio: {p['consultorio']}\n"
                        respuesta += f"📋 Causa: {p['causa']}\n"
                        respuesta += f"📅 Fecha ingreso: {p['fecha_ingreso']}\n\n"
                else:
                    respuesta = f"❌ No encontré pacientes con el nombre '{nombre_buscar}'"
            else:
                respuesta = "❌ Por favor especifica un nombre. Ejemplo: buscar Carlos"
        
        # ===== VER PACIENTE POR ID =====
        elif 'ver' in mensaje_lower or (mensaje_lower.startswith('paciente') and mensaje_lower.split()[0] == 'paciente'):
            try:
                id_buscar = ''.join(filter(str.isdigit, mensaje))
                if id_buscar:
                    cursor.execute("SELECT * FROM Paciente WHERE id_paciente = %s", (int(id_buscar),))
                    paciente = cursor.fetchone()
                    
                    if paciente:
                        respuesta = f"👤 DETALLES DEL PACIENTE:\n\n"
                        respuesta += f"🆔 ID: {paciente['id_paciente']}\n"
                        respuesta += f"👤 Nombre: {paciente['nombre']}\n"
                        respuesta += f"🎂 Edad: {paciente['edad']} años\n"
                        respuesta += f"🌆 Ciudad: {paciente['ciudad']}\n"
                        respuesta += f"🏥 Consultorio: {paciente['consultorio']}\n"
                        respuesta += f"📋 Causa: {paciente['causa']}\n"
                        respuesta += f"📅 Fecha ingreso: {paciente['fecha_ingreso']}"
                    else:
                        respuesta = f"❌ No encontré paciente con ID {id_buscar}"
                else:
                    respuesta = "❌ Por favor especifica un ID. Ejemplo: ver 1"
            except:
                respuesta = "❌ Error al buscar paciente. Usa: ver [id]"
        
        # ===== LISTAR PACIENTES =====
        elif 'listar' in mensaje_lower or 'pacientes' in mensaje_lower:
            # Verificar si busca por ciudad
            ciudad_buscar = None
            for ciudad in ['bogotá', 'bogota', 'medellín', 'medellin', 'cali', 'barranquilla', 'cartagena']:
                if ciudad in mensaje_lower:
                    ciudad_buscar = ciudad.capitalize()
                    if ciudad_buscar == 'Medellin':
                        ciudad_buscar = 'Medellín'
                    if ciudad_buscar == 'Bogota':
                        ciudad_buscar = 'Bogotá'
                    break
            
            if ciudad_buscar:
                cursor.execute("SELECT * FROM Paciente WHERE ciudad LIKE %s", (f'%{ciudad_buscar}%',))
            else:
                cursor.execute("SELECT * FROM Paciente ORDER BY id_paciente DESC")
            
            pacientes = cursor.fetchall()
            
            if pacientes:
                if ciudad_buscar:
                    respuesta = f"👥 Pacientes en {ciudad_buscar}: {len(pacientes)}\n\n"
                else:
                    respuesta = f"👥 Total de pacientes: {len(pacientes)}\n\n"
                
                for p in pacientes:
                    respuesta += f"🆔 {p['id_paciente']} - {p['nombre']} ({p['edad']} años) - {p['ciudad']}\n"
            else:
                respuesta = "📭 No hay pacientes registrados"
        
        # ===== AGREGAR PACIENTE =====
        elif 'agregar' in mensaje_lower:
            partes = mensaje.split('|')
            if len(partes) == 5:
                try:
                    nombre = partes[0].replace('agregar', '').strip()
                    edad = int(partes[1].strip())
                    ciudad = partes[2].strip()
                    consultorio = partes[3].strip()
                    causa = partes[4].strip()
                    
                    cursor.execute(
                        "INSERT INTO Paciente (nombre, edad, ciudad, consultorio, causa, fecha_ingreso) VALUES (%s, %s, %s, %s, %s, %s)",
                        (nombre, edad, ciudad, consultorio, causa, datetime.now().date())
                    )
                    conn.commit()
                    
                    respuesta = f"✅ Paciente agregado exitosamente:\n👤 {nombre}\n🎂 {edad} años\n🌆 {ciudad}"
                    socketio.emit('paciente_agregado', {}, broadcast=True)
                except Exception as e:
                    respuesta = f"❌ Error al agregar paciente: {str(e)}"
            else:
                respuesta = "❌ Formato incorrecto. Usa:\nagregar [nombre]|[edad]|[ciudad]|[consultorio]|[causa]"
        
        # ===== ELIMINAR PACIENTE =====
        elif 'eliminar' in mensaje_lower:
            try:
                id_eliminar = ''.join(filter(str.isdigit, mensaje))
                if id_eliminar:
                    cursor.execute("SELECT nombre FROM Paciente WHERE id_paciente = %s", (int(id_eliminar),))
                    paciente = cursor.fetchone()
                    
                    if paciente:
                        cursor.execute("DELETE FROM Paciente WHERE id_paciente = %s", (int(id_eliminar),))
                        conn.commit()
                        respuesta = f"✅ Paciente eliminado: {paciente['nombre']} (ID: {id_eliminar})"
                        socketio.emit('paciente_eliminado', {'id': int(id_eliminar)}, broadcast=True)
                    else:
                        respuesta = f"❌ No encontré paciente con ID {id_eliminar}"
                else:
                    respuesta = "❌ Por favor especifica un ID. Ejemplo: eliminar 5"
            except Exception as e:
                respuesta = f"❌ Error al eliminar: {str(e)}"
        
        # ===== REGISTRAR CITA =====
        elif 'cita' in mensaje_lower:
            partes = mensaje.split('|')
            if len(partes) == 2:
                try:
                    id_paciente = ''.join(filter(str.isdigit, partes[0]))
                    motivo = partes[1].strip()
                    
                    cursor.execute("SELECT nombre FROM Paciente WHERE id_paciente = %s", (int(id_paciente),))
                    paciente = cursor.fetchone()
                    
                    if paciente:
                        cursor.execute(
                            "INSERT INTO Cita (id_paciente, motivo, fecha) VALUES (%s, %s, %s)",
                            (int(id_paciente), motivo, datetime.now())
                        )
                        conn.commit()
                        respuesta = f"✅ Cita registrada para: {paciente['nombre']}\n📋 Motivo: {motivo}"
                    else:
                        respuesta = f"❌ No encontré paciente con ID {id_paciente}"
                except Exception as e:
                    respuesta = f"❌ Error al registrar cita: {str(e)}"
            else:
                respuesta = "❌ Formato incorrecto. Usa:\ncita [id]|[motivo]"
        
        # ===== ESTADÍSTICAS =====
        elif 'estadísticas' in mensaje_lower or 'estadisticas' in mensaje_lower:
            cursor.execute("SELECT COUNT(*) as total FROM Paciente")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM Cita")
            total_citas = cursor.fetchone()['total']
            
            cursor.execute("SELECT AVG(edad) as promedio FROM Paciente")
            edad_prom = cursor.fetchone()['promedio']
            
            cursor.execute("SELECT ciudad, COUNT(*) as cant FROM Paciente GROUP BY ciudad ORDER BY cant DESC LIMIT 1")
            ciudad_comun = cursor.fetchone()
            
            respuesta = f"""📊 ESTADÍSTICAS DE LA CLÍNICA:

👥 Total de pacientes: {total}
📅 Total de citas: {total_citas}
🎂 Edad promedio: {round(edad_prom, 1) if edad_prom else 0} años
🌆 Ciudad más común: {ciudad_comun['ciudad'] if ciudad_comun else 'N/A'} ({ciudad_comun['cant'] if ciudad_comun else 0} pacientes)
🌐 Usuarios conectados: {usuarios_conectados}"""
        
        # ===== EDAD PROMEDIO =====
        elif 'edad promedio' in mensaje_lower:
            cursor.execute("SELECT AVG(edad) as promedio FROM Paciente")
            edad_prom = cursor.fetchone()['promedio']
            respuesta = f"🎂 Edad promedio de pacientes: {round(edad_prom, 1) if edad_prom else 0} años"
        
        # ===== CIUDAD MÁS COMÚN =====
        elif 'ciudad' in mensaje_lower and ('común' in mensaje_lower or 'comun' in mensaje_lower or 'más' in mensaje_lower or 'mas' in mensaje_lower):
            cursor.execute("SELECT ciudad, COUNT(*) as cant FROM Paciente GROUP BY ciudad ORDER BY cant DESC")
            ciudades = cursor.fetchall()
            
            if ciudades:
                respuesta = "🌆 PACIENTES POR CIUDAD:\n\n"
                for c in ciudades:
                    respuesta += f"{c['ciudad']}: {c['cant']} paciente(s)\n"
            else:
                respuesta = "📭 No hay datos de ciudades"
        
        # ===== GRACIAS =====
        elif 'gracias' in mensaje_lower or 'thanks' in mensaje_lower:
            respuesta = '¡De nada! 😊 Estoy aquí para ayudarte con lo que necesites.'
        
        # ===== MENSAJE NO RECONOCIDO =====
        else:
            respuesta = f'Recibí tu mensaje: "{mensaje}"\n\n💡 Escribe "ayuda" para ver todos los comandos disponibles.'
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        respuesta = f"❌ Error procesando comando: {str(e)}"
        print(f"Error en chatbot: {e}")
    
    emit('mensaje_servidor', {'texto': respuesta, 'tipo': 'respuesta'})
   # ========================================
# INICIAR APLICACIÓN
# ========================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True) 