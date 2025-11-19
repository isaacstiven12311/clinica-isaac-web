# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clinica-isaac-secret-2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ========================================
# BASE DE DATOS EN MEMORIA CON DATOS REALES 2025
# ========================================

pacientes_db = [
    {'id': 1, 'nombre': 'Carlos Andrés Pérez Gómez', 'edad': 45, 'ciudad': 'Bogotá', 'consultorio': 'Consultorio 101', 'doctor': 'Dr. Juan Ramírez', 'causa': 'Hipertensión arterial', 'fecha_ingreso': '2025-01-15', 'estado': 'Activo'},
    {'id': 2, 'nombre': 'Ana María Rodríguez López', 'edad': 32, 'ciudad': 'Medellín', 'consultorio': 'Consultorio 202', 'doctor': 'Dra. Laura López', 'causa': 'Migrañas crónicas', 'fecha_ingreso': '2025-02-20', 'estado': 'Activo'},
    {'id': 3, 'nombre': 'Luis Fernando Torres Silva', 'edad': 58, 'ciudad': 'Cali', 'consultorio': 'Consultorio 303', 'doctor': 'Dr. Carlos Martínez', 'causa': 'Control cardiológico', 'fecha_ingreso': '2025-03-10', 'estado': 'Activo'},
    {'id': 4, 'nombre': 'María Elena Suárez Castro', 'edad': 67, 'ciudad': 'Bogotá', 'consultorio': 'Consultorio 101', 'doctor': 'Dr. Juan Ramírez', 'causa': 'Diabetes tipo 2', 'fecha_ingreso': '2025-01-25', 'estado': 'En consulta'},
    {'id': 5, 'nombre': 'Pedro José Ramírez Ortiz', 'edad': 28, 'ciudad': 'Barranquilla', 'consultorio': 'Consultorio 404', 'doctor': 'Dra. Ana Castro', 'causa': 'Faringitis aguda', 'fecha_ingreso': '2025-04-05', 'estado': 'Activo'},
    {'id': 6, 'nombre': 'Laura Cristina Mendoza Vargas', 'edad': 41, 'ciudad': 'Cali', 'consultorio': 'Consultorio 303', 'doctor': 'Dr. Carlos Martínez', 'causa': 'Arritmia cardíaca', 'fecha_ingreso': '2025-02-14', 'estado': 'Activo'},
    {'id': 7, 'nombre': 'Jorge Iván Vargas Ruiz', 'edad': 35, 'ciudad': 'Medellín', 'consultorio': 'Consultorio 202', 'doctor': 'Dra. Laura López', 'causa': 'Vértigo posicional', 'fecha_ingreso': '2025-03-22', 'estado': 'Activo'},
    {'id': 8, 'nombre': 'Sandra Patricia Moreno Gil', 'edad': 52, 'ciudad': 'Bogotá', 'consultorio': 'Consultorio 101', 'doctor': 'Dr. Juan Ramírez', 'causa': 'Osteoporosis', 'fecha_ingreso': '2025-04-11', 'estado': 'Activo'},
    {'id': 9, 'nombre': 'Roberto Carlos Díaz Sánchez', 'edad': 43, 'ciudad': 'Cartagena', 'consultorio': 'Consultorio 404', 'doctor': 'Dra. Ana Castro', 'causa': 'Gastritis crónica', 'fecha_ingreso': '2025-03-30', 'estado': 'Activo'},
    {'id': 10, 'nombre': 'Diana Marcela Ríos Herrera', 'edad': 29, 'ciudad': 'Medellín', 'consultorio': 'Consultorio 202', 'doctor': 'Dra. Laura López', 'causa': 'Ansiedad generalizada', 'fecha_ingreso': '2025-04-18', 'estado': 'Activo'},
]

citas_db = [
    {'id': 1, 'id_paciente': 1, 'paciente': 'Carlos Andrés Pérez Gómez', 'doctor': 'Dr. Juan Ramírez', 'fecha': '2025-05-20', 'hora': '09:00', 'motivo': 'Control mensual de presión arterial', 'estado': 'Programada'},
    {'id': 2, 'id_paciente': 2, 'paciente': 'Ana María Rodríguez López', 'doctor': 'Dra. Laura López', 'fecha': '2025-05-21', 'hora': '10:30', 'motivo': 'Valoración neurológica', 'estado': 'Programada'},
    {'id': 3, 'id_paciente': 3, 'paciente': 'Luis Fernando Torres Silva', 'doctor': 'Dr. Carlos Martínez', 'fecha': '2025-05-22', 'hora': '14:00', 'motivo': 'Electrocardiograma de control', 'estado': 'Programada'},
    {'id': 4, 'id_paciente': 4, 'paciente': 'María Elena Suárez Castro', 'doctor': 'Dr. Juan Ramírez', 'fecha': '2025-04-15', 'hora': '11:00', 'motivo': 'Resultados de glucosa en sangre', 'estado': 'Completada'},
    {'id': 5, 'id_paciente': 5, 'paciente': 'Pedro José Ramírez Ortiz', 'doctor': 'Dra. Ana Castro', 'fecha': '2025-05-19', 'hora': '15:30', 'motivo': 'Seguimiento post-tratamiento', 'estado': 'Programada'},
    {'id': 6, 'id_paciente': 6, 'paciente': 'Laura Cristina Mendoza Vargas', 'doctor': 'Dr. Carlos Martínez', 'fecha': '2025-05-23', 'hora': '09:30', 'motivo': 'Holter de 24 horas', 'estado': 'Programada'},
]

doctores_db = [
    {'id': 1, 'nombre': 'Dr. Juan Ramírez', 'especialidad': 'Medicina General', 'consultorio': 'Consultorio 101', 'pacientes_atendidos': 245, 'disponible': True},
    {'id': 2, 'nombre': 'Dra. Laura López', 'especialidad': 'Neurología', 'consultorio': 'Consultorio 202', 'pacientes_atendidos': 198, 'disponible': True},
    {'id': 3, 'nombre': 'Dr. Carlos Martínez', 'especialidad': 'Cardiología', 'consultorio': 'Consultorio 303', 'pacientes_atendidos': 176, 'disponible': False},
    {'id': 4, 'nombre': 'Dra. Ana Castro', 'especialidad': 'Medicina Interna', 'consultorio': 'Consultorio 404', 'pacientes_atendidos': 134, 'disponible': True},
]

meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
atendimientos_mensuales = [52, 58, 64, 71, 0, 0, 0, 0, 0, 0, 0, 0]  # 2025 hasta abril
consultas_mensuales = [145, 162, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0]

next_id_paciente = 11
next_id_cita = 7
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
        return jsonify({'mensaje': 'Paciente agregado', 'paciente': nuevo_paciente}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pacientes/<int:id>', methods=['DELETE'])
def eliminar_paciente(id):
    global pacientes_db
    paciente = next((p for p in pacientes_db if p['id'] == id), None)
    if paciente:
        pacientes_db = [p for p in pacientes_db if p['id'] != id]
        socketio.emit('actualizar_datos', {}, broadcast=True)
        return jsonify({'mensaje': f'Paciente eliminado'})
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
    
    edad_promedio = sum(p['edad'] for p in pacientes_db) / len(pacientes_db) if pacientes_db else 0
    
    ciudades = {}
    for p in pacientes_db:
        ciudades[p['ciudad']] = ciudades.get(p['ciudad'], 0) + 1
    
    doctores_stats = {}
    for p in pacientes_db:
        doctores_stats[p['doctor']] = doctores_stats.get(p['doctor'], 0) + 1
    
    top_doctores = sorted(doctores_db, key=lambda x: x['pacientes_atendidos'], reverse=True)[:4]
    
    especialidades = {}
    for d in doctores_db:
        especialidades[d['especialidad']] = doctores_stats.get(d['nombre'], 0)
    
    return jsonify({
        'total_pacientes': total_pacientes,
        'total_citas': total_citas,
        'total_doctores': len(doctores_db),
        'usuarios_conectados': usuarios_conectados,
        'edad_promedio': round(edad_promedio, 1),
        'pacientes_por_ciudad': ciudades,
        'top_doctores': top_doctores,
        'especialidades': especialidades,
        'meses': meses_labels,
        'atendimientos_mensuales': atendimientos_mensuales,
    })

# ========================================
# WEBSOCKETS - CHATBOT FUNCIONAL
# ========================================

@socketio.on('connect')
def handle_connect():
    global usuarios_conectados
    usuarios_conectados += 1
    print(f'✅ Cliente conectado. Total: {usuarios_conectados}')
    emit('mensaje_servidor', {
        'texto': '¡Bienvenido a Clínica Isaac! 👋\n\nSoy tu asistente virtual. Puedo ayudarte con:\n• Ver pacientes y citas\n• Buscar información\n• Estadísticas\n\nEscribe "ayuda" para ver todos los comandos.',
        'tipo': 'bienvenida'
    })
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
        if any(x in mensaje_lower for x in ['hola', 'hi', 'hello', 'buenos dias']):
            respuesta = '¡Hola! 👋 Soy el asistente de Clínica Isaac.\n\n¿En qué puedo ayudarte?\n\n💡 Escribe "ayuda" para ver los comandos.'
        
        elif 'ayuda' in mensaje_lower:
            respuesta = """📋 COMANDOS DISPONIBLES:

🔍 BÚSQUEDA:
- "buscar [nombre]" - Busca pacientes
- "ver paciente [id]" - Ver detalles

📊 LISTADOS:
- "pacientes" - Lista pacientes
- "citas" - Lista citas
- "doctores" - Lista doctores

📈 ESTADÍSTICAS:
- "estadísticas" - Resumen general
- "edad promedio" - Edad promedio
- "ciudad más común" - Ciudad con más pacientes

💬 ¡También entiendo lenguaje natural!"""
        
        elif 'pacientes' in mensaje_lower:
            respuesta = f"👥 Pacientes registrados: {len(pacientes_db)}\n\n"
            for p in pacientes_db[:5]:
                estado_emoji = "🟢" if p['estado'] == 'Activo' else "🔵"
                respuesta += f"{estado_emoji} #{p['id']} - {p['nombre']} ({p['edad']} años)\n   📍 {p['ciudad']} | 👨‍⚕️ {p['doctor']}\n\n"
            if len(pacientes_db) > 5:
                respuesta += f"... y {len(pacientes_db) - 5} más"
        
        elif 'citas' in mensaje_lower:
            respuesta = f"📅 Citas programadas: {len(citas_db)}\n\n"
            for c in citas_db[:5]:
                estado_emoji = "🟢" if c['estado'] == 'Programada' else "✅"
                respuesta += f"{estado_emoji} Cita #{c['id']}\n👤 {c['paciente']}\n📅 {c['fecha']} - {c['hora']}\n👨‍⚕️ {c['doctor']}\n\n"
        
        elif 'doctores' in mensaje_lower:
            respuesta = f"👨‍⚕️ Equipo médico ({len(doctores_db)}):\n\n"
            for d in doctores_db:
                disp = "🟢 Disponible" if d['disponible'] else "🔴 Ocupado"
                respuesta += f"👨‍⚕️ {d['nombre']}\n🏥 {d['especialidad']}\n📊 {d['pacientes_atendidos']} pacientes\n{disp}\n\n"
        
        elif 'estadísticas' in mensaje_lower or 'estadisticas' in mensaje_lower:
            edad_prom = sum(p['edad'] for p in pacientes_db) / len(pacientes_db)
            respuesta = f"""📊 ESTADÍSTICAS:

👥 Pacientes: {len(pacientes_db)}
📅 Citas: {len(citas_db)}
👨‍⚕️ Doctores: {len(doctores_db)}
🎂 Edad promedio: {round(edad_prom, 1)} años
🌐 Usuarios online: {usuarios_conectados}

✅ Activos: {len([p for p in pacientes_db if p['estado'] == 'Activo'])}
🔵 En consulta: {len([p for p in pacientes_db if p['estado'] == 'En consulta'])}"""
        
        elif 'edad promedio' in mensaje_lower:
            edad_prom = sum(p['edad'] for p in pacientes_db) / len(pacientes_db)
            respuesta = f"🎂 Edad promedio: {round(edad_prom, 1)} años\n\nBasado en {len(pacientes_db)} pacientes."
        
        elif 'ciudad' in mensaje_lower and ('común' in mensaje_lower or 'comun' in mensaje_lower):
            ciudades = {}
            for p in pacientes_db:
                ciudades[p['ciudad']] = ciudades.get(p['ciudad'], 0) + 1
            ciudad_top = max(ciudades.items(), key=lambda x: x[1])
            respuesta = f"📍 Ciudad con más pacientes: {ciudad_top[0]}\n\n✅ Total: {ciudad_top[1]} pacientes\n\nDesglose:\n"
            for c, cant in sorted(ciudades.items(), key=lambda x: x[1], reverse=True):
                respuesta += f"• {c}: {cant}\n"
        
        elif 'gracias' in mensaje_lower:
            respuesta = '¡De nada! 😊 Estoy aquí para ayudarte.'
        
        else:
            respuesta = f'Recibí: "{mensaje}"\n\n❓ No entendí. Escribe "ayuda" para ver comandos disponibles.'
    
    except Exception as e:
        respuesta = f"❌ Error: {str(e)}\n\n💡 Intenta de nuevo o escribe 'ayuda'."
        print(f"Error en chatbot: {e}")
    
    emit('mensaje_servidor', {'texto': respuesta, 'tipo': 'respuesta'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n🏥 Clínica Isaac - Iniciado en puerto {port}')
    socketio.run(app, host='0.0.0.0', port=port, debug=True)