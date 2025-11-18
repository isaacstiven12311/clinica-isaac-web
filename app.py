# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clinica-isaac-secret-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ========================================
# BASE DE DATOS EN MEMORIA (MEJORADA)
# ========================================

pacientes_db = [
    {'id': 1, 'nombre': 'Carlos Pérez', 'edad': 45, 'ciudad': 'Bogotá', 'consultorio': 'Consultorio 101', 'doctor': 'Dr. Ramírez', 'causa': 'Chequeo general', 'fecha_ingreso': '2024-01-15', 'estado': 'Activo'},
    {'id': 2, 'nombre': 'Ana Gómez', 'edad': 29, 'ciudad': 'Medellín', 'consultorio': 'Consultorio 202', 'doctor': 'Dra. López', 'causa': 'Dolor de cabeza', 'fecha_ingreso': '2024-01-16', 'estado': 'Activo'},
    {'id': 3, 'nombre': 'Luis Torres', 'edad': 38, 'ciudad': 'Cali', 'consultorio': 'Consultorio 303', 'doctor': 'Dr. Martínez', 'causa': 'Control de presión', 'fecha_ingreso': '2024-01-17', 'estado': 'Activo'},
    {'id': 4, 'nombre': 'María Silva', 'edad': 52, 'ciudad': 'Bogotá', 'consultorio': 'Consultorio 101', 'doctor': 'Dr. Ramírez', 'causa': 'Diabetes', 'fecha_ingreso': '2024-01-18', 'estado': 'En consulta'},
    {'id': 5, 'nombre': 'Pedro Ruiz', 'edad': 33, 'ciudad': 'Medellín', 'consultorio': 'Consultorio 404', 'doctor': 'Dra. Castro', 'causa': 'Gripe', 'fecha_ingreso': '2024-01-19', 'estado': 'Activo'},
    {'id': 6, 'nombre': 'Laura Mendoza', 'edad': 41, 'ciudad': 'Cali', 'consultorio': 'Consultorio 303', 'doctor': 'Dr. Martínez', 'causa': 'Cardiología', 'fecha_ingreso': '2024-01-20', 'estado': 'Activo'},
    {'id': 7, 'nombre': 'Jorge Vargas', 'edad': 27, 'ciudad': 'Barranquilla', 'consultorio': 'Consultorio 202', 'doctor': 'Dra. López', 'causa': 'Migraña', 'fecha_ingreso': '2024-01-21', 'estado': 'Activo'},
]

citas_db = [
    {'id': 1, 'id_paciente': 1, 'paciente': 'Carlos Pérez', 'doctor': 'Dr. Ramírez', 'fecha': '2024-01-20', 'hora': '09:00', 'motivo': 'Consulta de seguimiento', 'estado': 'Programada'},
    {'id': 2, 'id_paciente': 2, 'paciente': 'Ana Gómez', 'doctor': 'Dra. López', 'fecha': '2024-01-20', 'hora': '10:30', 'motivo': 'Neurología', 'estado': 'Programada'},
    {'id': 3, 'id_paciente': 3, 'paciente': 'Luis Torres', 'doctor': 'Dr. Martínez', 'fecha': '2024-01-21', 'hora': '14:00', 'motivo': 'Control mensual', 'estado': 'Programada'},
    {'id': 4, 'id_paciente': 4, 'paciente': 'María Silva', 'doctor': 'Dr. Ramírez', 'fecha': '2024-01-19', 'hora': '11:00', 'motivo': 'Control de diabetes', 'estado': 'Completada'},
]

doctores_db = [
    {'id': 1, 'nombre': 'Dr. Juan Ramírez', 'especialidad': 'Medicina General', 'consultorio': 'Consultorio 101', 'pacientes_atendidos': 145, 'disponible': True},
    {'id': 2, 'nombre': 'Dra. Laura López', 'especialidad': 'Neurología', 'consultorio': 'Consultorio 202', 'pacientes_atendidos': 132, 'disponible': True},
    {'id': 3, 'nombre': 'Dr. Carlos Martínez', 'especialidad': 'Cardiología', 'consultorio': 'Consultorio 303', 'pacientes_atendidos': 98, 'disponible': False},
    {'id': 4, 'nombre': 'Dra. Ana Castro', 'especialidad': 'Pediatría', 'consultorio': 'Consultorio 404', 'pacientes_atendidos': 87, 'disponible': True},
]

# Datos históricos para gráficas (últimos 12 meses)
meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
atendimientos_mensuales = [45, 52, 48, 61, 55, 67, 72, 68, 74, 81, 77, 85]
consultas_mensuales = [120, 135, 128, 145, 152, 168, 175, 171, 182, 190, 185, 195]

next_id_paciente = 8
next_id_cita = 5
usuarios_conectados = 0

# ========================================
# RUTAS DE LA API
# ========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pacientes', methods=['GET'])
def listar_pacientes():
    return jsonify(pacientes_db)

@app.route('/api/pacientes', methods=['POST'])
def agregar_paciente():
    global next_id_paciente
    try:
        data = request.json
        nuevo_paciente = {
            'id': next_id_paciente,
            'nombre': data['nombre'],
            'edad': int(data['edad']),
            'ciudad': data['ciudad'],
            'consultorio': data['consultorio'],
            'doctor': data.get('doctor', 'Por asignar'),
            'causa': data['causa'],
            'fecha_ingreso': datetime.now().strftime('%Y-%m-%d'),
            'estado': 'Activo'
        }
        pacientes_db.append(nuevo_paciente)
        next_id_paciente += 1
        socketio.emit('actualizar_datos', {}, broadcast=True)
        return jsonify({'mensaje': 'Paciente agregado exitosamente', 'paciente': nuevo_paciente}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pacientes/<int:id>', methods=['DELETE'])
def eliminar_paciente(id):
    global pacientes_db
    paciente = next((p for p in pacientes_db if p['id'] == id), None)
    if paciente:
        pacientes_db = [p for p in pacientes_db if p['id'] != id]
        socketio.emit('actualizar_datos', {}, broadcast=True)
        return jsonify({'mensaje': f'Paciente {id} eliminado'})
    return jsonify({'error': 'Paciente no encontrado'}), 404

@app.route('/api/citas', methods=['GET'])
def listar_citas():
    return jsonify(citas_db)

@app.route('/api/citas', methods=['POST'])
def registrar_cita():
    global next_id_cita
    try:
        data = request.json
        paciente = next((p for p in pacientes_db if p['id'] == int(data['id_paciente'])), None)
        
        if not paciente:
            return jsonify({'error': 'Paciente no encontrado'}), 404
        
        nueva_cita = {
            'id': next_id_cita,
            'id_paciente': int(data['id_paciente']),
            'paciente': paciente['nombre'],
            'doctor': data.get('doctor', paciente['doctor']),
            'fecha': data['fecha'],
            'hora': data['hora'],
            'motivo': data['motivo'],
            'estado': 'Programada'
        }
        citas_db.append(nueva_cita)
        next_id_cita += 1
        socketio.emit('actualizar_datos', {}, broadcast=True)
        return jsonify({'mensaje': 'Cita registrada', 'cita': nueva_cita}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/doctores', methods=['GET'])
def listar_doctores():
    return jsonify(doctores_db)

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    total_pacientes = len(pacientes_db)
    total_citas = len(citas_db)
    total_doctores = len(doctores_db)
    
    citas_programadas = len([c for c in citas_db if c['estado'] == 'Programada'])
    citas_completadas = len([c for c in citas_db if c['estado'] == 'Completada'])
    
    pacientes_activos = len([p for p in pacientes_db if p['estado'] == 'Activo'])
    pacientes_en_consulta = len([p for p in pacientes_db if p['estado'] == 'En consulta'])
    
    if pacientes_db:
        edad_promedio = sum(p['edad'] for p in pacientes_db) / len(pacientes_db)
    else:
        edad_promedio = 0
    
    # Pacientes por ciudad
    ciudades = {}
    for p in pacientes_db:
        ciudades[p['ciudad']] = ciudades.get(p['ciudad'], 0) + 1
    
    # Pacientes por doctor
    doctores_stats = {}
    for p in pacientes_db:
        if p['doctor'] not in doctores_stats:
            doctores_stats[p['doctor']] = 0
        doctores_stats[p['doctor']] += 1
    
    # Top doctores
    top_doctores = sorted(doctores_db, key=lambda x: x['pacientes_atendidos'], reverse=True)[:3]
    
    # Pacientes por especialidad
    especialidades = {}
    for d in doctores_db:
        especialidades[d['especialidad']] = doctores_stats.get(d['nombre'], 0)
    
    return jsonify({
        'total_pacientes': total_pacientes,
        'total_citas': total_citas,
        'total_doctores': total_doctores,
        'usuarios_conectados': usuarios_conectados,
        'citas_programadas': citas_programadas,
        'citas_completadas': citas_completadas,
        'pacientes_activos': pacientes_activos,
        'pacientes_en_consulta': pacientes_en_consulta,
        'edad_promedio': round(edad_promedio, 1),
        'pacientes_por_ciudad': ciudades,
        'pacientes_por_doctor': doctores_stats,
        'top_doctores': top_doctores,
        'especialidades': especialidades,
        'meses': meses_labels,
        'atendimientos_mensuales': atendimientos_mensuales,
        'consultas_mensuales': consultas_mensuales
    })

# ========================================
# WEBSOCKETS
# ========================================

@socketio.on('connect')
def handle_connect():
    global usuarios_conectados
    usuarios_conectados += 1
    print(f'✅ Cliente conectado. Total: {usuarios_conectados}')
    emit('mensaje_servidor', {'texto': '¡Bienvenido a Clínica Isaac! 👋 Soy tu asistente virtual.\n\nPuedo ayudarte con:\n• Ver pacientes y citas\n• Buscar información\n• Estadísticas\n• Y mucho más!\n\nEscribe "ayuda" para ver todos los comandos.', 'tipo': 'bienvenida'})
    socketio.emit('usuarios_conectados', {'total': usuarios_conectados}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global usuarios_conectados
    usuarios_conectados = max(0, usuarios_conectados - 1)
    socketio.emit('usuarios_conectados', {'total': usuarios_conectados}, broadcast=True)

@socketio.on('mensaje_cliente')
def handle_mensaje(data):
    mensaje = data['mensaje'].strip()
    mensaje_lower = mensaje.lower()
    respuesta = ""
    
    try:
        # SALUDOS
        if any(saludo in mensaje_lower for saludo in ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'hi', 'hello']):
            respuesta = '¡Hola! 👋 Soy el asistente virtual de Clínica Isaac.\n\n¿En qué puedo ayudarte hoy?\n\n💡 Escribe "ayuda" para ver todo lo que puedo hacer.'
        
        # AYUDA
        elif 'ayuda' in mensaje_lower or mensaje_lower in ['?', 'help']:
            respuesta = """📋 COMANDOS DISPONIBLES:

🔍 BÚSQUEDA:
- "buscar [nombre]" - Busca pacientes
- "doctor [nombre]" - Busca doctores
- "ver paciente [id]" - Detalles de paciente

📊 LISTADOS:
- "pacientes" o "listar pacientes"
- "citas" o "listar citas"
- "doctores" o "listar doctores"
- "pacientes de [ciudad]"

📈 ESTADÍSTICAS:
- "estadísticas" - Resumen general
- "edad promedio"
- "ciudad más común"
- "doctor más ocupado"

💬 ¡También entiendo lenguaje natural!"""
        
        # BUSCAR PACIENTE
        elif 'buscar' in mensaje_lower:
            nombre_buscar = mensaje_lower.replace('buscar', '').strip()
            if nombre_buscar:
                pacientes = [p for p in pacientes_db if nombre_buscar in p['nombre'].lower()]
                if pacientes:
                    respuesta = f"🔍 Encontré {len(pacientes)} paciente(s):\n\n"
                    for p in pacientes:
                        respuesta += f"🆔 ID: {p['id']}\n👤 {p['nombre']} ({p['edad']} años)\n👨‍⚕️ {p['doctor']}\n📍 {p['estado']}\n\n"
                else:
                    respuesta = f"❌ No encontré pacientes con '{nombre_buscar}'"
            else:
                respuesta = "❌ Especifica un nombre. Ejemplo: buscar Carlos"
        
        # LISTAR PACIENTES
        elif 'pacientes' in mensaje_lower or 'listar paciente' in mensaje_lower:
            respuesta = f"👥 Total de pacientes: {len(pacientes_db)}\n\n"
            for p in pacientes_db:
                estado_emoji = "🟢" if p['estado'] == 'Activo' else "🔵"
                respuesta += f"{estado_emoji} {p['id']}. {p['nombre']} ({p['edad']} años) - {p['ciudad']}\n"
        
        # LISTAR CITAS
        elif 'citas' in mensaje_lower:
            if citas_db:
                respuesta = f"📅 Total de citas: {len(citas_db)}\n\n"
                for c in citas_db:
                    estado_emoji = "🟢" if c['estado'] == 'Programada' else "✅"
                    respuesta += f"{estado_emoji} Cita #{c['id']}: {c['paciente']}\n📅 {c['fecha']} - {c['hora']}\n👨‍⚕️ {c['doctor']}\n\n"
            else:
                respuesta = "📭 No hay citas registradas"
        
        # LISTAR DOCTORES
        elif 'doctores' in mensaje_lower or 'medicos' in mensaje_lower:
            respuesta = f"👨‍⚕️ Equipo médico ({len(doctores_db)} doctores):\n\n"
            for d in doctores_db:
                disponible = "🟢 Disponible" if d['disponible'] else "🔴 Ocupado"
                respuesta += f"👨‍⚕️ {d['nombre']}\n🏥 {d['especialidad']}\n📊 {d['pacientes_atendidos']} pacientes\n{disponible}\n\n"
        
        # ESTADÍSTICAS
        elif 'estadísticas' in mensaje_lower or 'estadisticas' in mensaje_lower:
            total_pacientes = len(pacientes_db)
            total_citas = len(citas_db)
            edad_prom = sum(p['edad'] for p in pacientes_db) / len(pacientes_db) if pacientes_db else 0
            
            respuesta = f"""📊 ESTADÍSTICAS:

👥 Pacientes: {total_pacientes}
📅 Citas: {total_citas}
👨‍⚕️ Doctores: {len(doctores_db)}
🎂 Edad promedio: {round(edad_prom, 1)} años
🌐 Usuarios online: {usuarios_conectados}"""
        
        # GRACIAS
        elif 'gracias' in mensaje_lower:
            respuesta = '¡De nada! 😊 Estoy aquí para ayudarte.'
        
        # MENSAJE NO RECONOCIDO
        else:
            respuesta = f'Recibí: "{mensaje}"\n\n💡 Escribe "ayuda" para ver comandos.'
        
    except Exception as e:
        respuesta = f"❌ Error: {str(e)}"
        print(f"Error en chatbot: {e}")
    
    emit('mensaje_servidor', {'texto': respuesta, 'tipo': 'respuesta'})

# ========================================
# INICIAR APLICACIÓN
# ========================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)