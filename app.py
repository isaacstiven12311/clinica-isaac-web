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
# WEBSOCKETS - CHATBOT MEJORADO
# ========================================

@socketio.on('connect')
def handle_connect():
    global usuarios_conectados
    usuarios_conectados += 1
    print(f'✅ Cliente conectado. Total: {usuarios_conectados}')
    emit('mensaje_servidor', {
        'texto': '¡Bienvenido a Clínica Isaac! 👋 Soy tu asistente virtual.\n\nPuedo ayudarte con:\n• Ver pacientes y citas\n• Buscar información\n• Estadísticas en tiempo real\n• Y mucho más!\n\nEscribe "ayuda" para ver todos los comandos disponibles.',
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
        # SALUDOS
        if any(saludo in mensaje_lower for saludo in ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'hi', 'hello', 'hey']):
            respuesta = '¡Hola! 👋 Soy el asistente virtual de Clínica Isaac.\n\n¿En qué puedo ayudarte hoy?\n\n💡 Escribe "ayuda" para ver todo lo que puedo hacer por ti.'
        
        # AYUDA
        elif 'ayuda' in mensaje_lower or mensaje_lower in ['?', 'help', 'comandos']:
            respuesta = """📋 COMANDOS DISPONIBLES:

🔍 BÚSQUEDA:
• "buscar [nombre]" - Busca pacientes por nombre
• "doctor [nombre]" - Busca información de doctores
• "ver paciente [id]" - Ver detalles de un paciente específico
• "citas de [nombre]" - Ver citas de un paciente

📊 LISTADOS:
• "pacientes" o "listar pacientes" - Lista todos los pacientes
• "citas" o "listar citas" - Lista todas las citas
• "doctores" o "listar doctores" - Lista el equipo médico
• "pacientes de [ciudad]" - Filtra por ciudad

📈 ESTADÍSTICAS:
• "estadísticas" - Resumen general del sistema
• "edad promedio" - Edad promedio de pacientes
• "ciudad más común" - Ciudad con más pacientes
• "doctor más ocupado" - Doctor con más pacientes

💬 También entiendo lenguaje natural, ¡prueba preguntarme cualquier cosa!"""
        
        # BUSCAR PACIENTE
        elif 'buscar' in mensaje_lower and 'paciente' in mensaje_lower or mensaje_lower.startswith('buscar '):
            nombre_buscar = mensaje_lower.replace('buscar', '').replace('paciente', '').strip()
            if nombre_buscar:
                pacientes = [p for p in pacientes_db if nombre_buscar in p['nombre'].lower()]
                if pacientes:
                    respuesta = f"🔍 Encontré {len(pacientes)} paciente(s) con '{nombre_buscar}':\n\n"
                    for p in pacientes:
                        respuesta += f"🆔 ID: {p['id']}\n👤 Nombre: {p['nombre']} ({p['edad']} años)\n📍 Ciudad: {p['ciudad']}\n👨‍⚕️ Doctor: {p['doctor']}\n🏥 Estado: {p['estado']}\n📋 Causa: {p['causa']}\n\n"
                else:
                    respuesta = f"❌ No encontré pacientes con el nombre '{nombre_buscar}'.\n\n💡 Intenta con otro nombre o escribe 'pacientes' para ver la lista completa."
            else:
                respuesta = "❌ Por favor especifica un nombre.\n\nEjemplo: buscar Carlos"
        
        # VER PACIENTE POR ID
        elif 'ver paciente' in mensaje_lower or 'paciente' in mensaje_lower and any(c.isdigit() for c in mensaje):
            import re
            numeros = re.findall(r'\d+', mensaje)
            if numeros:
                id_buscar = int(numeros[0])
                paciente = next((p for p in pacientes_db if p['id'] == id_buscar), None)
                if paciente:
                    respuesta = f"""📋 INFORMACIÓN DEL PACIENTE:

🆔 ID: {paciente['id']}
👤 Nombre: {paciente['nombre']}
🎂 Edad: {paciente['edad']} años
📍 Ciudad: {paciente['ciudad']}
🏥 Consultorio: {paciente['consultorio']}
👨‍⚕️ Doctor asignado: {paciente['doctor']}
📋 Motivo: {paciente['causa']}
📅 Fecha de ingreso: {paciente['fecha_ingreso']}
🏥 Estado: {paciente['estado']}"""
                else:
                    respuesta = f"❌ No encontré un paciente con el ID {id_buscar}.\n\n💡 Escribe 'pacientes' para ver todos los IDs disponibles."
        
        # LISTAR PACIENTES
        elif 'pacientes' in mensaje_lower or 'listar paciente' in mensaje_lower:
            # Filtrar por ciudad si se menciona
            if 'de ' in mensaje_lower:
                ciudad = mensaje_lower.split('de ')[-1].strip().title()
                pacientes = [p for p in pacientes_db if ciudad.lower() in p['ciudad'].lower()]
                if pacientes:
                    respuesta = f"👥 Pacientes de {ciudad} ({len(pacientes)}):\n\n"
                else:
                    respuesta = f"❌ No hay pacientes registrados de {ciudad}"
            else:
                pacientes = pacientes_db
                respuesta = f"👥 Total de pacientes registrados: {len(pacientes_db)}\n\n"
            
            if pacientes:
                for p in pacientes:
                    estado_emoji = "🟢" if p['estado'] == 'Activo' else "🔵"
                    respuesta += f"{estado_emoji} #{p['id']} - {p['nombre']} ({p['edad']} años) - {p['ciudad']}\n   👨‍⚕️ {p['doctor']} | 📋 {p['causa']}\n\n"
        
        # LISTAR CITAS
        elif 'citas' in mensaje_lower or 'listar citas' in mensaje_lower or 'ver citas' in mensaje_lower:
            if 'de ' in mensaje_lower:
                # Buscar citas de un paciente específico
                nombre = mensaje_lower.split('de ')[-1].strip()
                citas = [c for c in citas_db if nombre in c['paciente'].lower()]
                if citas:
                    respuesta = f"📅 Citas de {citas[0]['paciente']}:\n\n"
                else:
                    respuesta = f"❌ No encontré citas para '{nombre}'"
            else:
                citas = citas_db
                respuesta = f"📅 Total de citas: {len(citas_db)}\n\n"
            
            if citas:
                for c in citas:
                    estado_emoji = "🟢" if c['estado'] == 'Programada' else "✅"
                    respuesta += f"{estado_emoji} Cita #{c['id']}\n👤 Paciente: {c['paciente']}\n📅 Fecha: {c['fecha']} a las {c['hora']}\n👨‍⚕️ Doctor: {c['doctor']}\n📋 Motivo: {c['motivo']}\n🏥 Estado: {c['estado']}\n\n"
        
        # LISTAR DOCTORES
        elif 'doctores' in mensaje_lower or 'medicos' in mensaje_lower or 'médicos' in mensaje_lower or 'doctor' in mensaje_lower:
            respuesta = f"👨‍⚕️ Equipo médico de Clínica Isaac ({len(doctores_db)} doctores):\n\n"
            for d in doctores_db:
                disponible = "🟢 Disponible" if d['disponible'] else "🔴 Ocupado"
                respuesta += f"👨‍⚕️ {d['nombre']}\n🏥 Especialidad: {d['especialidad']}\n📍 {d['consultorio']}\n📊 Pacientes atendidos: {d['pacientes_atendidos']}\n{disponible}\n\n"
        
        # ESTADÍSTICAS
        elif 'estadísticas' in mensaje_lower or 'estadisticas' in mensaje_lower or 'estadística' in mensaje_lower:
            total_pacientes = len(pacientes_db)
            total_citas = len(citas_db)
            edad_prom = sum(p['edad'] for p in pacientes_db) / len(pacientes_db) if pacientes_db else 0
            
            # Ciudad más común
            ciudades = {}
            for p in pacientes_db:
                ciudades[p['ciudad']] = ciudades.get(p['ciudad'], 0) + 1
            ciudad_comun = max(ciudades.items(), key=lambda x: x[1]) if ciudades else ('N/A', 0)
            
            # Doctor más ocupado
            doctores_count = {}
            for p in pacientes_db:
                doctores_count[p['doctor']] = doctores_count.get(p['doctor'], 0) + 1
            doctor_ocupado = max(doctores_count.items(), key=lambda x: x[1]) if doctores_count else ('N/A', 0)
            
            respuesta = f"""📊 ESTADÍSTICAS DE CLÍNICA ISAAC:

👥 Total de pacientes: {total_pacientes}
📅 Citas programadas: {total_citas}
👨‍⚕️ Doctores activos: {len(doctores_db)}
🎂 Edad promedio: {round(edad_prom, 1)} años
🌐 Usuarios en línea: {usuarios_conectados}

📍 Ciudad con más pacientes: {ciudad_comun[0]} ({ciudad_comun[1]} pacientes)
⭐ Doctor más solicitado: {doctor_ocupado[0]} ({doctor_ocupado[1]} pacientes)

✅ Pacientes activos: {len([p for p in pacientes_db if p['estado'] == 'Activo'])}
🔵 En consulta: {len([p for p in pacientes_db if p['estado'] == 'En consulta'])}"""
        
        # EDAD PROMEDIO
        elif 'edad promedio' in mensaje_lower or 'edad media' in mensaje_lower:
            edad_prom = sum(p['edad'] for p in pacientes_db) / len(pacientes_db) if pacientes_db else 0
            respuesta = f"🎂 La edad promedio de los pacientes es: {round(edad_prom, 1)} años\n\nBasado en {len(pacientes_db)} pacientes registrados."
        
        # CIUDAD MÁS COMÚN
        elif 'ciudad' in mensaje_lower and ('común' in mensaje_lower or 'comun' in mensaje_lower or 'más' in mensaje_lower or 'mas' in mensaje_lower):
            ciudades = {}
            for p in pacientes_db:
                ciudades[p['ciudad']] = ciudades.get(p['ciudad'], 0) + 1
            if ciudades:
                ciudad_comun = max(ciudades.items(), key=lambda x: x[1])
                respuesta = f"📍 La ciudad con más pacientes es: {ciudad_comun[0]}\n\n✅ Total: {ciudad_comun[1]} pacientes ({round(ciudad_comun[1]/len(pacientes_db)*100, 1)}%)\n\nDesglose por ciudades:\n"
                for ciudad, cant in sorted(ciudades.items(), key=lambda x: x[1], reverse=True):
                    respuesta += f"• {ciudad}: {cant} pacientes\n"
        
        # DOCTOR MÁS OCUPADO
        elif 'doctor' in mensaje_lower and ('ocupado' in mensaje_lower or 'solicitado' in mensaje_lower or 'más' in mensaje_lower or 'mas' in mensaje_lower):
            doctores_count = {}
            for p in pacientes_db:
                doctores_count[p['doctor']] = doctores_count.get(p['doctor'], 0) + 1
            if doctores_count:
                doctor_ocupado = max(doctores_count.items(), key=lambda x: x[1])
                respuesta = f"⭐ El doctor más solicitado es: {doctor_ocupado[0]}\n\n✅ Pacientes asignados: {doctor_ocupado[1]}\n\nRanking de doctores:\n"
                for doctor, cant in sorted(doctores_count.items(), key=lambda x: x[1], reverse=True):
                    respuesta += f"• {doctor}: {cant} pacientes\n"
        
        # CUÁNTOS/CUÁNTAS
        elif mensaje_lower.startswith('cuantos') or mensaje_lower.startswith('cuántos') or mensaje_lower.startswith('cuantas') or mensaje_lower.startswith('cuántas'):
            if 'paciente' in mensaje_lower:
                respuesta = f"👥 Actualmente hay {len(pacientes_db)} pacientes registrados en el sistema."
            elif 'cita' in mensaje_lower:
                respuesta = f"📅 Hay {len(citas_db)} citas programadas en total.\n\n🟢 Programadas: {len([c for c in citas_db if c['estado'] == 'Programada'])}\n✅ Completadas: {len([c for c in citas_db if c['estado'] == 'Completada'])}"
            elif 'doctor' in mensaje_lower or 'médico' in mensaje_lower:
                respuesta = f"👨‍⚕️ Tenemos {len(doctores_db)} doctores en nuestro equipo médico."
            else:
                respuesta = "❌ No entendí tu pregunta.\n\n💡 Intenta preguntar: ¿Cuántos pacientes hay?"
        
        # GRACIAS
        elif 'gracias' in mensaje_lower or 'thank' in mensaje_lower:
            respuesta = '¡De nada! 😊 Estoy aquí para ayudarte en lo que necesites.\n\n¿Hay algo más en lo que pueda asistirte?'
        
        # DESPEDIDA
        elif any(palabra in mensaje_lower for palabra in ['adios', 'adiós', 'chao', 'hasta luego', 'bye']):
            respuesta = '¡Hasta pronto! 👋 Que tengas un excelente día.\n\nRecuerda que estoy disponible 24/7 para ayudarte.'
        
        # MENSAJE NO RECONOCIDO
        else:
            respuesta = f'Recibí tu mensaje: "{mensaje}"\n\n❓ No estoy seguro de cómo ayudarte con eso.\n\n💡 Escribe "ayuda" para ver todos los comandos disponibles o intenta hacer una pregunta más específica.'
        
    except Exception as e:
        respuesta = f"❌ Ocurrió un error al procesar tu solicitud: {str(e)}\n\n💡 Por favor intenta de nuevo o escribe 'ayuda' para ver los comandos disponibles."
        print(f"Error en chatbot: {e}")
    
    emit('mensaje_servidor', {'texto': respuesta, 'tipo': 'respuesta'})

# ========================================
# INICIAR APLICACIÓN
# ========================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n🏥 Clínica Isaac - Sistema iniciado en puerto {port}')
    print(f'🌐 Accede a: http://localhost:{port}\n')
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)