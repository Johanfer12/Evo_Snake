from flask import Flask, render_template, jsonify
import threading
import time
import logging # Para depuración
from simulation import SimulationManager # Importa tu clase

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Configuración de la Simulación ---
SIM_WIDTH = 30
SIM_HEIGHT = 20
INITIAL_SNAKES = 5
INITIAL_FOOD = 10
SIM_SPEED_MS = 500 # Milisegundos entre pasos

# ¡Importante! Crear un Lock para proteger el acceso al estado de la simulación
simulation_lock = threading.Lock()
try:
    simulation = SimulationManager(SIM_WIDTH, SIM_HEIGHT, INITIAL_SNAKES, INITIAL_FOOD)
    logging.info("SimulationManager inicializado correctamente.")
except Exception as e:
    logging.error(f"Error al inicializar SimulationManager: {e}", exc_info=True)
    # Decide cómo manejar este error crítico. Podrías salir o intentar de nuevo.
    # Por ahora, saldremos si la simulación no se puede crear.
    exit()


# --- Hilo para correr la simulación en background ---
_simulation_running = True # Variable para controlar el bucle del hilo

def run_simulation():
    global _simulation_running
    logging.info("Iniciando hilo de simulación...")
    while _simulation_running:
        with simulation_lock: # Adquirir el lock antes de modificar el estado
            try:
                simulation.step()
                # logging.debug(f"Simulación avanzó al paso {simulation.paso_actual}") # Puede ser muy verboso
            except Exception as e:
                logging.error(f"Error en simulation.step(): {e}", exc_info=True)
                # Considera si detener el hilo o solo loggear
                # _simulation_running = False # Descomentar para detener en error

        # Controla la velocidad de la simulación
        # time.sleep(SIM_SPEED_MS / 1000.0)
        # Corrección: time.sleep espera segundos, no milisegundos
        sleep_duration = SIM_SPEED_MS / 1000.0
        if sleep_duration > 0:
             time.sleep(sleep_duration)
        else:
             # Evitar espera negativa o nula si SIM_SPEED_MS es 0 o negativo
             pass # Opcionalmente, yield para ceder control si es muy rápido

    logging.info("Hilo de simulación detenido.")

simulation_thread = threading.Thread(target=run_simulation, daemon=True)
# Se inicia más abajo, después de definir las rutas, o dentro del if __name__ == '__main__':

# --- Rutas de Flask ---
@app.route('/')
def index():
    """Sirve la página HTML principal."""
    logging.info("Sirviendo index.html")
    # Pasa las dimensiones al template si el JS las necesita al inicio
    return render_template('index.html', width=SIM_WIDTH, height=SIM_HEIGHT)

@app.route('/game_state')
def game_state():
    """Devuelve el estado actual del juego en formato JSON."""
    logging.debug("Petición a /game_state recibida.")
    state = None # Inicializar state fuera del try
    with simulation_lock: # Adquirir lock para leer el estado de forma segura
        try:
            state = simulation.get_state()
            # <<< DEBUG LOGGING >>>
            logging.info(f"Enviando estado desde /game_state: Pasos={state.get('paso')}, Serpientes={len(state.get('serpientes', []))}, Comida={len(state.get('comida', []))}")
            # Log detallado de las primeras serpientes (si existen)
            if state.get('serpientes'):
                 logging.debug(f"  Detalle primeras serpientes: {state['serpientes'][:2]}") # Loguea las 2 primeras
            # <<< FIN DEBUG LOGGING >>>
            return jsonify(state)
        except Exception as e:
            logging.error(f"Error en get_state() o jsonify: {e}", exc_info=True)
            # Loguear el estado si se obtuvo antes del error
            if state:
                logging.error(f"  Estado parcial antes del error: {state}")
            return jsonify({"error": "Error al obtener el estado"}), 500

# Nueva ruta para reiniciar la simulación
@app.route('/reset_simulation', methods=['POST'])
def reset_simulation():
    """Reinicia la simulación y devuelve el estado inicial."""
    logging.info("Petición a /reset_simulation recibida.")
    with simulation_lock:
        try:
            success = simulation.reset()
            if success:
                return jsonify({"status": "success", "message": "Simulación reiniciada correctamente"})
            else:
                return jsonify({"status": "error", "message": "Error al reiniciar la simulación"}), 500
        except Exception as e:
            logging.error(f"Error en reset_simulation: {e}", exc_info=True)
            return jsonify({"status": "error", "message": str(e)}), 500

# --- Manejo de cierre limpio (opcional pero recomendado) ---
def shutdown_hook():
    global _simulation_running
    logging.info("Señal de apagado recibida. Deteniendo hilo de simulación...")
    _simulation_running = False
    if simulation_thread.is_alive():
        simulation_thread.join(timeout=2) # Esperar un poco a que el hilo termine
    logging.info("Aplicación Flask terminando.")

# Registrar el hook de apagado (requiere `pip install Werkzeug>=2.0` si no está ya)
try:
    from werkzeug.serving import is_running_from_reloader
    if not is_running_from_reloader(): # Evitar registrar dos veces en modo debug
        import atexit
        atexit.register(shutdown_hook)
except ImportError:
    logging.warning("werkzeug.serving no encontrado, el cierre limpio del hilo no estará activo.")
    pass # Continuar sin el hook si werkzeug no está o es una versión antigua


# --- Punto de entrada ---
if __name__ == '__main__':
    # Iniciar el hilo de simulación ANTES de iniciar el servidor Flask
    simulation_thread.start()
    logging.info("Hilo de simulación iniciado.")

    # Nota: El servidor de desarrollo de Flask no es ideal para producción con hilos.
    # Para algo más robusto, considera Gunicorn/uWSGI.
    # Werkzeug (servidor dev) puede tener problemas con hilos en modo reload.
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000) # use_reloader=False es importante con hilos
    # host='0.0.0.0' permite acceso desde otros dispositivos en la red local 