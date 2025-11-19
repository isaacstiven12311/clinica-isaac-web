# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clinica-isaac-secret-2025')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ========================================
# BASE DE DATOS EN MEMORIA
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
    {'id': 1, 'id_paciente': 1, 'paciente': 'Carlos Andrés Pérez Gómez', 'doctor': 'Dr. Juan Ramírez', 'fecha': '2025-11-25', 'hora': '09:00', 'motivo': 'Control mensual de presión arterial', 'estado': 'Programada'},
    {'id': 2, 'id_paciente': 2, 'paciente': 'Ana María Rodríguez López', 'doctor': 'Dra. Laura López', 'fecha': '2025-11-26', 'hora': '10:30', 'motivo': 'Valoración neurológica', 'estado': 'Programada'},
    {'id': 3, 'id_paciente': 3, 'paciente': 'Luis Fernando Torres Silva', 'doctor': 'Dr. Carlos Martínez', 'fecha': '2025-11-27', 'hora': '14:00', 'motivo': 'Electrocardiograma de control', 'estado': 'Programada'},
    {'id': 4, 'id_paciente': 4, 'paciente': 'María Elena Suárez Castro', 'doctor': 'Dr. Juan Ramírez', 'fecha': '2025-10-15', 'hora': '11:00', 'motivo': 'Resultados de glucosa en sangre', 'estado': 'Completada'},
    {'id': 5, 'id_paciente': 5, 'paciente': 'Pedro José Ramírez Ortiz', 'doctor': 'Dra. Ana Castro', 'fecha': '2025-11-22', 'hora': '15:30', 'motivo': 'Seguimiento post-tratamiento', 'estado': 'Programada'},
    {'id': 6, 'id_paciente': 6, 'paciente': 'Laura Cristina Mendoza Vargas', 'doctor': 'Dr. Carlos Martínez', 'fecha': '2025-11-28', 'hora': '09:30', 'motivo': 'Holter de 24 horas', 'estado': 'Programada'},
]

doctores_db = [
    {'id': 1, 'nombre': 'Dr. Juan Ramírez', 'especialidad': 'Medicina General', 'consultorio': 'Consultorio 101', 'pacientes_atendidos': 245, 'disponible': True},
    {'id': 2, 'nombre': 'Dra. Laura López', 'especialidad': 'Neurología', 'consultorio': 'Consultorio 202', 'pacientes_atendidos': 198, 'disponible': True},
    {'id': 3, 'nombre': 'Dr. Carlos Martínez', 'especialidad': 'Cardiología', 'consultorio': 'Consultorio 303', 'pacientes_atendidos': 176, 'disponible': False},
    {'id': 4, 'nombre': 'Dra. Ana Castro', 'especialidad': 'Medicina Interna', 'consultorio': 'Consultorio 404', 'pacientes_atendidos': 134, 'disponible': True},
]

meses_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
atendimientos_mensuales_2025 = [52, 58, 64, 71, 85, 92, 0, 0, 0, 0, 0, 0]
consultas_mensuales_2025 = [32, 35, 40, 45, 52, 58, 0, 0, 0, 0, 0, 0]
examenes_mensuales_2025 = [15, 18, 19, 21, 25, 28, 0, 0, 0, 0, 0, 0]

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
        
        # Emitir actualización después de responder
        socketio.start_background_task(socketio.emit, 'actualizar_datos', {}, broadcast=True)
        
        return jsonify({
            'success': True,
            'mensaje': 'Paciente agregado exitosamente',
            'paciente': nuevo_paciente
        }), 201
    except Exception as e:
        print(f"Error al agregar paciente: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/pacientes/<int:id>', methods=['DELETE'])
def eliminar_paciente(id):
    global pacientes_db
    paciente = next((p for p in pacientes_db if p['id'] == id), None)
    if paciente:
        pacientes_db = [p for p in pacientes_db if p['id'] != id]
        socketio.start_background_task(socketio.emit, 'actualizar_datos', {}, broadcast=True)
        return jsonify({
            'success': True,
            'mensaje': 'Paciente eliminado exitosamente'
        })
    return jsonify({
        'success': False,
        'error': 'Paciente no encontrado'
    }), 404

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
            return jsonify({
                'success': False,
                'error': 'Paciente no encontrado'
            }), 404
        
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
        
        # Emitir actualización después de responder
        socketio.start_background_task(socketio.emit, 'actualizar_datos', {}, broadcast=True)
        
        return jsonify({
            'success': True,
            'mensaje': 'Cita registrada exitosamente',
            'cita': nueva_cita
        }), 201
    except Exception as e:
        print(f"Error al registrar cita: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
        'atendimientos_mensuales': atendimientos_mensuales_2025,
        'consultas_mensuales': consultas_mensuales_2025,
        'examenes_mensuales': examenes_mensuales_2025,
    })

# ========================================
# WEBSOCKETS - CHATBOT
# ========================================

@socketio.on('connect')
def handle_connect():
    global usuarios_conectados
    usuarios_conectados += 1
    print(f'✅ Cliente conectado. Total: {usuarios_conectados}')
    
    mensaje_bienvenida = """¡Bienvenido a Clínica Isaac! 👋

Soy tu asistente virtual inteligente. Puedo ayudarte con:

- 👥 Consultar información de pacientes
- 📅 Ver citas programadas
- 👨‍⚕ Información del equipo médico
- 📊 Estadísticas del sistema
- 🔍 Búsquedas específicas

Escribe "ayuda" para ver todos los comandos disponibles o pregúntame lo que necesites en lenguaje natural."""
    
    emit('mensaje_servidor', {'texto': mensaje_bienvenida, 'tipo': 'bienvenida'})
    emit('usuarios_conectados', {'total': usuarios_conectados}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global usuarios_conectados
    usuarios_conectados = max(0, usuarios_conectados - 1)
    print(f'🔴 Cliente desconectado. Total: {usuarios_conectados}')
    emit('usuarios_conectados', {'total': usuarios_conectados}, broadcast=True)

@socketio.on('mensaje_cliente')
def handle_mensaje(data):
    mensaje = data['mensaje'].strip()
    mensaje_lower = mensaje.lower()
    respuesta = ""
    
    print(f"📩 Mensaje recibido: {mensaje}")
    
    try:
        if any(x in mensaje_lower for x in ['hola', 'hi', 'hello', 'buenos días', 'buenas tardes', 'buenas noches', 'hey']):
            respuesta = """¡Hola! 👋 Soy el asistente virtual de Clínica Isaac.

¿En qué puedo ayudarte hoy?

💡 Puedes preguntarme sobre:
- Pacientes registrados
- Citas programadas
- Equipo médico
- Estadísticas del sistema

O escribe "ayuda" para ver todos los comandos."""
        
        elif 'ayuda' in mensaje_lower or mensaje_lower in ['?', 'help']:
            respuesta = """📋 GUÍA DE COMANDOS:

🔍 BÚSQUEDA Y CONSULTAS:
- "pacientes" - Lista todos los pacientes
- "buscar [nombre]" - Busca pacientes por nombre
- "paciente [ID]" - Ver detalles de un paciente
- "citas" - Lista todas las citas
- "doctores" - Lista el equipo médico

📊 ESTADÍSTICAS:
- "estadísticas" - Resumen completo del sistema
- "cuántos pacientes" - Total de pacientes

💬 LENGUAJE NATURAL:
También entiendo preguntas naturales como:
- "¿Cuántas citas hay programadas?"
- "¿Qué doctores están disponibles?"
- "Dame un resumen del sistema"

¡Pregúntame lo que necesites!"""
        
        elif 'pacientes' in mensaje_lower or 'lista de pacientes' in mensaje_lower:
            total = len(pacientes_db)
            respuesta = f"👥 PACIENTES REGISTRADOS ({total} en total):\n\n"
            
            for p in pacientes_db[:8]:
                estado_emoji = "🟢" if p['estado'] == 'Activo' else "🔵"
                respuesta += f"{estado_emoji} #{p['id']} - {p['nombre']}\n"
                respuesta += f"   🎂 {p['edad']} años | 📍 {p['ciudad']}\n"
                respuesta += f"   👨‍⚕ {p['doctor']}\n"
                respuesta += f"   📋 {p['causa']}\n\n"
            
            if total > 8:
                respuesta += f"... y {total - 8} paciente(s) más\n\n"
            
            respuesta += "💡 Para ver detalles de un paciente específico, escribe: 'paciente [ID]'"
        
        elif 'paciente' in mensaje_lower and any(c.isdigit() for c in mensaje):
            import re
            numeros = re.findall(r'\d+', mensaje)
            if numeros:
                id_buscar = int(numeros[0])
                paciente = next((p for p in pacientes_db if p['id'] == id_buscar), None)
                
                if paciente:
                    respuesta = f"""📋 INFORMACIÓN COMPLETA:

🆔 ID: {paciente['id']}
👤 Nombre: {paciente['nombre']}
🎂 Edad: {paciente['edad']} años
📍 Ciudad: {paciente['ciudad']}
🏥 Consultorio: {paciente['consultorio']}
👨‍⚕ Doctor: {paciente['doctor']}
📋 Motivo: {paciente['causa']}
📅 Ingreso: {paciente['fecha_ingreso']}
🏥 Estado: {paciente['estado']}"""
                else:
                    respuesta = f"❌ No encontré un paciente con ID {id_buscar}.\n\n💡 Escribe 'pacientes' para ver todos los IDs disponibles."
        
        elif 'buscar' in mensaje_lower:
            nombre_buscar = mensaje_lower.replace('buscar', '').strip()
            if nombre_buscar:
                pacientes_encontrados = [p for p in pacientes_db if nombre_buscar in p['nombre'].lower()]
                
                if pacientes_encontrados:
                    respuesta = f"🔍 Encontré {len(pacientes_encontrados)} resultado(s) para '{nombre_buscar}':\n\n"
                    for p in pacientes_encontrados:
                        estado_emoji = "🟢" if p['estado'] == 'Activo' else "🔵"
                        respuesta += f"{estado_emoji} #{p['id']} - {p['nombre']}\n"
                        respuesta += f"   {p['edad']} años | {p['ciudad']} | {p['doctor']}\n\n"
                else:
                    respuesta = f"❌ No encontré pacientes con '{nombre_buscar}'.\n\nIntenta con otro nombre o escribe 'pacientes' para ver la lista completa."
            else:
                respuesta = "❌ Por favor especifica un nombre para buscar.\n\nEjemplo: buscar Carlos"
        
        elif 'citas' in mensaje_lower or 'cita' in mensaje_lower:
            total_citas = len(citas_db)
            programadas = len([c for c in citas_db if c['estado'] == 'Programada'])
            completadas = len([c for c in citas_db if c['estado'] == 'Completada'])
            
            respuesta = f"📅 CITAS DEL SISTEMA:\n\n"
            respuesta += f"📊 Total: {total_citas} citas\n"
            respuesta += f"🟢 Programadas: {programadas}\n"
            respuesta += f"✅ Completadas: {completadas}\n\n"
            
            citas_proximas = [c for c in citas_db if c['estado'] == 'Programada'][:5]
            
            if citas_proximas:
                respuesta += "📆 PRÓXIMAS CITAS:\n\n"
                for c in citas_proximas:
                    respuesta += f"🟢 Cita #{c['id']}\n"
                    respuesta += f"   👤 {c['paciente']}\n"
                    respuesta += f"   📅 {c['fecha']} a las {c['hora']}\n"
                    respuesta += f"   👨‍⚕ {c['doctor']}\n"
                    respuesta += f"   📋 {c['motivo']}\n\n"
        
        elif 'doctores' in mensaje_lower or 'doctor' in mensaje_lower or 'médicos' in mensaje_lower:
            respuesta = f"👨‍⚕ EQUIPO MÉDICO DE CLÍNICA ISAAC:\n\n"
            
            for d in doctores_db:
                disponible_emoji = "🟢" if d['disponible'] else "🔴"
                disponible_texto = "Disponible" if d['disponible'] else "Ocupado"
                
                respuesta += f"{disponible_emoji} {d['nombre']}\n"
                respuesta += f"   🏥 Especialidad: {d['especialidad']}\n"
                respuesta += f"   📍 {d['consultorio']}\n"
                respuesta += f"   📊 Pacientes atendidos: {d['pacientes_atendidos']}\n"
                respuesta += f"   Estado: {disponible_texto}\n\n"
        
        elif 'estadísticas' in mensaje_lower or 'estadisticas' in mensaje_lower or 'resumen' in mensaje_lower:
            edad_prom = sum(p['edad'] for p in pacientes_db) / len(pacientes_db)
            activos = len([p for p in pacientes_db if p['estado'] == 'Activo'])
            en_consulta = len([p for p in pacientes_db if p['estado'] == 'En consulta'])
            
            ciudades = {}
            for p in pacientes_db:
                ciudades[p['ciudad']] = ciudades.get(p['ciudad'], 0) + 1
            ciudad_top = max(ciudades.items(), key=lambda x: x[1]) if ciudades else ('N/A', 0)
            
            respuesta = f"""📊 ESTADÍSTICAS DE CLÍNICA ISAAC:

━━━━━━━━━━━━━━━━━━━━━━━━━
📈 DATOS GENERALES:
━━━━━━━━━━━━━━━━━━━━━━━━━
👥 Total pacientes: {len(pacientes_db)}
📅 Citas programadas: {len(citas_db)}
👨‍⚕ Doctores activos: {len(doctores_db)}
🌐 Usuarios en línea: {usuarios_conectados}

━━━━━━━━━━━━━━━━━━━━━━━━━
👥 PACIENTES:
━━━━━━━━━━━━━━━━━━━━━━━━━
🎂 Edad promedio: {round(edad_prom, 1)} años
✅ Pacientes activos: {activos}
🔵 En consulta: {en_consulta}
📍 Ciudad principal: {ciudad_top[0]} ({ciudad_top[1]} pacientes)

━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Sistema operativo al 100%"""
        
        elif any(x in mensaje_lower for x in ['cuantos', 'cuántos', 'cuantas', 'cuántas']):
            if 'paciente' in mensaje_lower:
                respuesta = f"""👥 PACIENTES REGISTRADOS:

📊 Total: {len(pacientes_db)} pacientes
✅ Activos: {len([p for p in pacientes_db if p['estado'] == 'Activo'])}
🔵 En consulta: {len([p for p in pacientes_db if p['estado'] == 'En consulta'])}"""
            
            elif 'cita' in mensaje_lower:
                programadas = len([c for c in citas_db if c['estado'] == 'Programada'])
                completadas = len([c for c in citas_db if c['estado'] == 'Completada'])
                
                respuesta = f"""📅 CITAS DEL SISTEMA:

📊 Total: {len(citas_db)} citas
🟢 Programadas: {programadas}
✅ Completadas: {completadas}"""
            
            elif 'doctor' in mensaje_lower or 'médico' in mensaje_lower:
                disponibles = len([d for d in doctores_db if d['disponible']])
                
                respuesta = f"""👨‍⚕ EQUIPO MÉDICO:

📊 Total: {len(doctores_db)} doctores
🟢 Disponibles: {disponibles}
🔴 Ocupados: {len(doctores_db) - disponibles}"""
            else:
                respuesta = "❓ No entendí tu pregunta.\n\n💡 Intenta: ¿Cuántos pacientes hay?"
        
        elif 'gracias' in mensaje_lower or 'thank' in mensaje_lower:
            respuesta = "¡De nada! 😊 Es un placer ayudarte.\n\n¿Hay algo más en lo que pueda asistirte?"
        
        elif any(x in mensaje_lower for x in ['adios', 'adiós', 'chao', 'hasta luego', 'bye', 'nos vemos']):
            respuesta = "¡Hasta pronto! 👋 Que tengas un excelente día.\n\nRecuerda que estoy disponible 24/7 cuando me necesites."
        
        else:
            respuesta = f"""Recibí tu mensaje: "{mensaje}"

❓ No estoy seguro de cómo ayudarte con eso.

💡 SUGERENCIAS:
- Escribe "ayuda" para ver todos los comandos
- Pregunta sobre "pacientes", "citas" o "doctores"
- Pide "estadísticas" del sistema
- Hazme preguntas en lenguaje natural

Estoy aquí para ayudarte 😊"""
    
    except Exception as e:
        respuesta = f"""❌ Ocurrió un error al procesar tu solicitud.

💡 Por favor intenta:
- Reformular tu pregunta
- Escribir "ayuda" para ver los comandos
- Verificar que tu mensaje esté completo

Error técnico: {str(e)}"""
        print(f"❌ Error en chatbot: {e}")
    
    print(f"📤 Enviando respuesta")
    emit('mensaje_servidor', {'texto': respuesta, 'tipo': 'respuesta'})

# ========================================
# INICIAR APLICACIÓN
# ========================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n{"="*50}')
    print(f'🏥 CLÍNICA ISAAC - SISTEMA MÉDICO INTEGRAL')
    print(f'{"="*50}')
    print(f'🌐 Servidor iniciado en puerto: {port}')
    print(f'📊 Pacientes registrados: {len(pacientes_db)}')
    print(f'📅 Citas programadas: {len(citas_db)}')
    print(f'👨‍⚕ Doctores disponibles: {len(doctores_db)}')
    print(f'{"="*50}\n')
    
    socketio.run(app, host='0.0.0.0', port=port, debug=True)