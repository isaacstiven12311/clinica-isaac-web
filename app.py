# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clinica-isaac-secret-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Base de datos en memoria (para Railway)
pacientes_db = [
    {'id': 1, 'nombre': 'Carlos Pérez', 'edad': 45, 'ciudad': 'Bogotá', 'consultorio': 'Consultorio 101', 'causa': 'Chequeo general', 'fecha_ingreso': '2024-01-15'},
    {'id': 2, 'nombre': 'Ana Gómez', 'edad': 29, 'ciudad': 'Medellín', 'consultorio': 'Consultorio 202', 'causa': 'Dolor de cabeza', 'fecha_ingreso': '2024-01-16'},
    {'id': 3, 'nombre': 'Luis Torres', 'edad': 38, 'ciudad': 'Cali', 'consultorio': 'Consultorio 303', 'causa': 'Control de presión', 'fecha_ingreso': '2024-01-17'}
]

citas_db = []
next_id = 4
usuarios_conectados = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pacientes', methods=['GET'])
def listar_pacientes():
    return jsonify(pacientes_db)

@app.route('/api/pacientes', methods=['POST'])
def agregar_paciente():
    global next_id
    try:
        data = request.json
        nuevo_paciente = {
            'id': next_id,
            'nombre': data['nombre'],
            'edad': int(data['edad']),
            'ciudad': data['ciudad'],
            'consultorio': data['consultorio'],
            'causa': data['causa'],
            'fecha_ingreso': datetime.now().strftime('%Y-%m-%d')
        }
        pacientes_db.append(nuevo_paciente)
        next_id += 1
        socketio.emit('paciente_agregado', nuevo_paciente, broadcast=True)
        return jsonify({'mensaje': 'Paciente agregado exitosamente', 'paciente': nuevo_paciente}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pacientes/<int:id>', methods=['DELETE'])
def eliminar_paciente(id):
    global pacientes_db
    paciente = next((p for p in pacientes_db if p['id'] == id), None)
    if paciente:
        pacientes_db = [p for p in pacientes_db if p['id'] != id]
        socketio.emit('paciente_eliminado', {'id': id}, broadcast=True)
        return jsonify({'mensaje': f'Paciente {id} eliminado'})
    return jsonify({'error': 'Paciente no encontrado'}), 404

@app.route('/api/citas', methods=['POST'])
def registrar_cita():
    try:
        data = request.json
        nueva_cita = {
            'id': len(citas_db) + 1,
            'id_paciente': int(data['id_paciente']),
            'motivo': data['motivo'],
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        citas_db.append(nueva_cita)
        return jsonify({'mensaje': 'Cita registrada', 'cita': nueva_cita}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/estadisticas', methods=['GET'])
def estadisticas():
    return jsonify({
        'total_pacientes': len(pacientes_db),
        'total_citas': len(citas_db),
        'usuarios_conectados': usuarios_conectados
    })

@socketio.on('connect')
def handle_connect():
    global usuarios_conectados
    usuarios_conectados += 1
    print(f'✅ Cliente conectado. Total: {usuarios_conectados}')
    emit('mensaje_servidor', {'texto': '¡Bienvenido a Clínica Isaac! 👋', 'tipo': 'bienvenida'})
    emit('usuarios_conectados', {'total': usuarios_conectados}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global usuarios_conectados
    usuarios_conectados = max(0, usuarios_conectados - 1)
    emit('usuarios_conectados', {'total': usuarios_conectados}, broadcast=True)

@socketio.on('mensaje_cliente')
def handle_mensaje(data):
    mensaje = data['mensaje'].lower()
    
    if any(saludo in mensaje for saludo in ['hola', 'buenos dias', 'hi']):
        respuesta = '¡Hola! 👋 ¿En qué puedo ayudarte?'
    elif 'listar' in mensaje or 'pacientes' in mensaje:
        respuesta = f'📊 Hay {len(pacientes_db)} pacientes registrados'
    elif 'ayuda' in mensaje:
        respuesta = '📋 Puedes: ver pacientes, agregar paciente, registrar cita'
    elif 'gracias' in mensaje:
        respuesta = '¡De nada! 😊 Estoy aquí para ayudarte'
    else:
        respuesta = f'Recibí: "{data["mensaje"]}". Escribe "ayuda" para ver comandos.'
    
    emit('mensaje_servidor', {'texto': respuesta, 'tipo': 'respuesta'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)