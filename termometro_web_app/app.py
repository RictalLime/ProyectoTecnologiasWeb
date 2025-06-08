# app.py
from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime, timedelta
import threading
import time
import random
import os
from flask_cors import CORS
from clientemqtt import start_mqtt, mqtt_queue


app = Flask(__name__)
CORS(app)
DATABASE = 'sensor_data.db'
SIMULATION_INTERVAL_SECONDS = 1 # Intervalo de simulación de lecturas (cada segundo)

thermometer_states = {}
simulation_thread = None
simulation_running = False

# Definición de umbrales de temperatura
TEMP_THRESHOLD_HIGH = 45.0
TEMP_THRESHOLD_LOW = 15.0
TEMP_LEVEL_VALUE = 28.0 # Temperatura a la que se nivela

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS thermometers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thermometer_id INTEGER NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (thermometer_id) REFERENCES thermometers (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

    load_thermometers_into_simulation_state()

def load_thermometers_into_simulation_state():
    """Carga los termómetros existentes de la base de datos al estado de simulación."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM thermometers")
    existing_thermometers = cursor.fetchall()
    conn.close()

    current_ids = {t['id'] for t in existing_thermometers}
    
    # Eliminar termómetros del estado de simulación que ya no están en la base de datos
    ids_to_remove = [tid for tid in thermometer_states if tid not in current_ids]
    for tid in ids_to_remove:
        print(f"Eliminando termómetro ID {tid} del estado de simulación.")
        del thermometer_states[tid]

    # Añadir o actualizar termómetros existentes
    for thermo in existing_thermometers:
        if thermo['id'] not in thermometer_states:
            # Si es un termómetro nuevo, inicializar sus valores de simulación
            thermometer_states[thermo['id']] = {
                'name': thermo['name'],
                'current_temp': random.uniform(20.0, 30.0), # Temperatura inicial aleatoria
                'current_hum': random.uniform(50.0, 70.0),  # Humedad inicial aleatoria
                'last_update': datetime.now()
            }
        else:
            # Si ya existe, solo actualizar el nombre por si cambió
            thermometer_states[thermo['id']]['name'] = thermo['name']

def simulate_readings():
    """Función que simula lecturas y las guarda en la base de datos."""
    global simulation_running
    while simulation_running:
        conn = get_db_connection()
        cursor = conn.cursor()
        for thermo_id, state in list(thermometer_states.items()):
            # Simular pequeña variación en temperatura y humedad
            state['current_temp'] += random.uniform(-2.0, 2.0) # Variación más amplia
            state['current_hum'] += random.uniform(-1.0, 1.0)

            # Mantener los valores dentro de rangos razonables (0 a 65 grados para temperatura)
            state['current_temp'] = max(0.0, min(65.0, state['current_temp']))
            state['current_hum'] = max(0.0, min(100.0, state['current_hum'])) # Humedad de 0 a 100%

            state['last_update'] = datetime.now()
            timestamp = state['last_update'].strftime('%Y-%m-%d %H:%M:%S')

            try:
                cursor.execute("INSERT INTO readings (thermometer_id, temperature, humidity, timestamp) VALUES (?, ?, ?, ?)",
                               (thermo_id, state['current_temp'], state['current_hum'], timestamp))
                conn.commit()
                # print(f"Simulado y guardado para {state['name']} (ID: {thermo_id}): Temp={state['current_temp']:.2f}, Hum={state['current_hum']:.2f}")
            except Exception as e:
                print(f"Error al simular y guardar datos para ID {thermo_id}: {e}")
                conn.rollback()
        conn.close()
        time.sleep(SIMULATION_INTERVAL_SECONDS)

# Rutas de la aplicación web

@app.route('/')
def home():
    """Redirige a la página de cliente por defecto."""
    return render_template('client.html')

@app.route('/admin')
def admin_page():
    """Página de administración para gestionar termómetros."""
    return render_template('admin.html')

@app.route('/client')
def client_page():
    """Página de cliente para ver gráficos en tiempo real."""
    return render_template('client.html')

@app.route('/history')
def history_page():
    """Página para ver el historial completo de lecturas."""
    return render_template('history.html')

# --- API Endpoints para la gestión de termómetros ---

@app.route('/api/thermometers', methods=['GET'])
def get_thermometers():
    """Obtiene la lista de todos los termómetros."""
    conn = get_db_connection()
    thermometers = conn.execute("SELECT id, name FROM thermometers").fetchall()
    conn.close()
    return jsonify([dict(row) for row in thermometers])

@app.route('/api/thermometers', methods=['POST'])
def add_thermometer():
    """Añade un nuevo termómetro."""
    name = request.json.get('name')
    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO thermometers (name) VALUES (?)", (name,))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        # Añadir al estado de simulación
        thermometer_states[new_id] = {
            'name': name,
            'current_temp': random.uniform(20.0, 30.0),
            'current_hum': random.uniform(50.0, 70.0),
            'last_update': datetime.now()
        }
        return jsonify({"message": "Thermometer added", "id": new_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Thermometer name already exists"}), 409
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/thermometers/<int:thermometer_id>', methods=['DELETE'])
def delete_thermometer(thermometer_id):
    """Elimina un termómetro por su ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM thermometers WHERE id = ?", (thermometer_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    if rows_affected > 0:
        # Eliminar del estado de simulación
        if thermometer_id in thermometer_states:
            del thermometer_states[thermometer_id]
        return jsonify({"message": "Thermometer deleted"}), 200
    return jsonify({"error": "Thermometer not found"}), 404

@app.route('/api/thermometers/<int:thermometer_id>/level', methods=['POST'])
def level_thermometer_temperature(thermometer_id):
    """Endpoint para nivelar la temperatura de un termómetro específico a 28 grados."""
    if thermometer_id not in thermometer_states:
        return jsonify({"error": "Thermometer not found"}), 404
    
    thermometer_states[thermometer_id]['current_temp'] = TEMP_LEVEL_VALUE
    thermometer_states[thermometer_id]['last_update'] = datetime.now() # Actualizar timestamp
    print(f"Temperatura del termómetro ID {thermometer_id} nivelada a {TEMP_LEVEL_VALUE}°C")
    return jsonify({"message": f"Temperature for thermometer {thermometer_id} leveled to {TEMP_LEVEL_VALUE}°C"}), 200


# --- API Endpoints para lecturas de datos ---

@app.route('/api/readings/latest', methods=['GET'])
def get_latest_readings():
    """Obtiene la última lectura simulada para cada termómetro activo."""
    latest_data = []
    for thermo_id, state in thermometer_states.items():
        latest_data.append({
            'thermometer_id': thermo_id,
            'name': state['name'],
            'temperature': state['current_temp'],
            'humidity': state['current_hum'],
            'timestamp': state['last_update'].strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(latest_data)

@app.route('/api/readings/history/<int:thermometer_id>', methods=['GET'])
def get_thermometer_history(thermometer_id):
    """Obtiene el historial de lecturas para un termómetro específico."""
    conn = get_db_connection()
    readings = conn.execute(
        "SELECT timestamp, temperature, humidity FROM readings WHERE thermometer_id = ? ORDER BY timestamp ASC",
        (thermometer_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in readings])

@app.route('/api/readings/all', methods=['GET'])
def get_all_readings():
    """Obtiene todas las lecturas de todos los termómetros para la tabla de historial."""
    conn = get_db_connection()
    readings = conn.execute(
        "SELECT r.timestamp, t.name, r.temperature, r.humidity FROM readings r JOIN thermometers t ON r.thermometer_id = t.id ORDER BY r.timestamp DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in readings])

# --- Manejo del hilo de simulación ---

def start_simulation():
    """Inicia el hilo de simulación."""
    global simulation_thread, simulation_running
    if not simulation_running:
        simulation_running = True
        simulation_thread = threading.Thread(target=simulate_readings)
        simulation_thread.daemon = True
        simulation_thread.start()
        print("Simulación de lecturas iniciada.")

def stop_simulation():
    """Detiene el hilo de simulación."""
    global simulation_running
    if simulation_running:
        simulation_running = False
        if simulation_thread and simulation_thread.is_alive():
            simulation_thread.join(timeout=2)
        print("Simulación de lecturas detenida.")

import threading

def process_mqtt_messages():
    while True:
        if not mqtt_queue.empty():
            mensaje = mqtt_queue.get()
            print(f"[Flask] Procesando mensaje MQTT: {mensaje}")
            # Aquí puedes guardar el mensaje en la base de datos
            # guardar_en_db(float(mensaje))
        time.sleep(1)

# Iniciar MQTT y el procesador de mensajes
start_mqtt()
threading.Thread(target=process_mqtt_messages, daemon=True).start()


# Inicializar la base de datos y comenzar la simulación al iniciar la aplicación
if __name__ == '__main__':
    init_db()
    start_simulation()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    stop_simulation()
