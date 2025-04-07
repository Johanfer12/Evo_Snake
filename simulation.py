import random
import copy # Necesario si pasas objetos complejos
import logging
import math # Para distancia

# --- Clases Base (Añadir aquí tus clases Serpiente y Entorno) ---
# Ejemplo de placeholder para la clase Serpiente
class Serpiente:
    def __init__(self, id, x, y, color="green", genes=None):
        self.id = id
        self.cuerpo = [(x, y)] # Lista de coordenadas [(x,y), ...]
        self.color = color
        self.energia = 100 # Ejemplo
        self.edad = 0
        self.comida_comida = 0 # <-- NUEVO: Contador de comida
        self.hijos_generados = 0
        # <<< Log de confirmación >>>
        logging.debug(f"Serpiente {self.id} __init__: hijos_generados inicializado a {self.hijos_generados}")
        # Genes: Placeholder como una lista de 10 números aleatorios si no se proporcionan
        if genes is None:
            self.genes = [random.random() for _ in range(10)]
        else:
            self.genes = genes # Permitir heredar genes

    def mover(self, direccion, width, height):
        """Intenta mover la serpiente en la dirección dada.
        Devuelve True si el movimiento es válido (dentro de los límites),
        False si choca contra una pared.
        """
        cabeza_x, cabeza_y = self.cuerpo[0]
        nueva_cabeza_x = cabeza_x + direccion[0]
        nueva_cabeza_y = cabeza_y + direccion[1]

        # Comprobar colisión con paredes
        if not (0 <= nueva_cabeza_x < width and 0 <= nueva_cabeza_y < height):
            return False # Chocó con la pared

        # Movimiento válido: Actualizar cuerpo
        nueva_cabeza = (nueva_cabeza_x, nueva_cabeza_y)
        self.cuerpo.insert(0, nueva_cabeza)
        # La lógica de acortar la cola se manejará en 'step' después de verificar si comió

        self.energia -= 5 # <-- CAMBIO: Coste de energía por movimiento aumentado
        self.edad += 1
        return True # Movimiento válido

    def decidir_movimiento(self, simulation_manager, all_food, all_snakes):
        """Toma decisiones basadas en genes, energía y visión."""
        # 1. Obtener estado y parámetros genéticos
        cabeza = self.cuerpo[0]
        vision_range = self._get_vision_range()
        low_energy_threshold = self._get_low_energy_threshold()
        high_energy_threshold = self._get_high_energy_threshold()

        # 2. Percibir el entorno
        visible_food = self._get_visible_targets(cabeza, all_food, vision_range)
        # Excluirse a sí mismo de las serpientes visibles
        other_snakes = [s for s in all_snakes if s.id != self.id]
        visible_snakes = self._get_visible_targets(cabeza, other_snakes, vision_range, target_is_snake=True)

        # 3. Determinar el objetivo prioritario
        target_pos = None
        target_type = None # 'food' o 'mate'

        if self.energia < low_energy_threshold and visible_food:
            target_pos = self._find_closest_target(cabeza, visible_food)
            target_type = 'food'
            logging.debug(f"Serpiente {self.id} (E:{self.energia:.0f}<{low_energy_threshold:.0f}): Busca comida -> {target_pos}")
        elif self.energia > high_energy_threshold and visible_snakes:
            # Buscar pareja potencial (con suficiente energía también?)
            potential_mates = [s for s in visible_snakes if s.energia >= simulation_manager.reproduction_energy_cost]
            if potential_mates:
                target_pos = self._find_closest_target(cabeza, potential_mates, target_is_snake=True)
                target_type = 'mate'
                logging.debug(f"Serpiente {self.id} (E:{self.energia:.0f}>{high_energy_threshold:.0f}): Busca pareja -> {target_pos}")

        # 4. Elegir dirección hacia el objetivo o moverse aleatoriamente
        direcciones_posibles = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        mejor_direccion = None

        if target_pos:
            mejor_direccion = self._get_direction_towards(cabeza, target_pos)

        # 5. Validar direcciones (evitar cuello y paredes)
        direcciones_validas_final = []
        cuello = self.cuerpo[1] if len(self.cuerpo) > 1 else None

        possible_next_heads = {}
        for dx, dy in direcciones_posibles:
            next_head = (cabeza[0] + dx, cabeza[1] + dy)
            # Validar cuello
            if cuello and next_head == cuello:
                continue
            # Validar paredes (usando dimensiones del entorno)
            if not (0 <= next_head[0] < simulation_manager.width and 0 <= next_head[1] < simulation_manager.height):
                continue
            # Validar si choca con su propio cuerpo (permitido pero no ideal?)
            # Lo dejamos permitido por ahora

            # Guardar dirección y la cabeza resultante
            possible_next_heads[(dx, dy)] = next_head
            direcciones_validas_final.append((dx, dy))

        # 6. Seleccionar la mejor dirección válida
        if not direcciones_validas_final:
            # Atrapado! Moverse a cualquier sitio (incluso cuello/pared, step lo manejará)
            logging.warning(f"Serpiente {self.id} está atrapada! Eligiendo movimiento al azar (podría ser fatal).")
            return random.choice(direcciones_posibles)

        # Si el objetivo calculado es válido, usarlo
        if mejor_direccion and mejor_direccion in direcciones_validas_final:
            logging.debug(f"Serpiente {self.id} moviendo hacia {target_type if target_type else 'objetivo'}: {mejor_direccion}")
            return mejor_direccion
        else:
            # Si el objetivo no es válido (ej. bloqueado por cuello/pared) o no hay objetivo,
            # elegir una dirección válida al azar.
            logging.debug(f"Serpiente {self.id} sin objetivo claro o dirección bloqueada. Moviendo al azar entre válidas.")
            return random.choice(direcciones_validas_final)

    # --- NUEVOS MÉTODOS AUXILIARES ---
    def _get_vision_range(self, max_range=10):
        # Escalar gen[0] (0.0-1.0) a un rango de casillas (ej. 1 a max_range)
        # Usamos una escala no lineal (ej. cuadrática) para que pequeños cambios
        # en el gen tengan más impacto en rangos bajos.
        # Asegurarse que gen[0] existe
        if len(self.genes) > 0:
            base_range = max(1, int(math.sqrt(self.genes[0]) * max_range))
            return base_range
        else:
            return 3 # Rango por defecto si no hay genes

    def _get_low_energy_threshold(self, max_energy=200):
        # Escalar gen[1] (0.0-1.0) a un umbral de energía
        if len(self.genes) > 1:
            return self.genes[1] * max_energy
        else:
            return 50 # Umbral por defecto

    def _get_high_energy_threshold(self, max_energy=200):
        # Escalar gen[2] (0.0-1.0) a un umbral de energía
        # Asegurarse que sea mayor o igual al umbral bajo
        if len(self.genes) > 2:
            high_threshold = self.genes[2] * max_energy
            low_threshold = self._get_low_energy_threshold(max_energy)
            return max(low_threshold, high_threshold) # Garantizar que alto >= bajo
        else:
            return 150 # Umbral por defecto

    # --- MÁS MÉTODOS AUXILIARES ---
    def _get_visible_targets(self, position, targets, vision_range, target_is_snake=False):
        visible = []
        for target in targets:
            target_pos = target if not target_is_snake else target.cuerpo[0] # Posición de la comida o cabeza de la serpiente
            # Calcular distancia (Manhattan o Euclídea? Usemos Manhattan por simplicidad en grid)
            distance = abs(position[0] - target_pos[0]) + abs(position[1] - target_pos[1])
            if distance <= vision_range:
                visible.append(target)
        return visible

    def _find_closest_target(self, position, targets, target_is_snake=False):
        closest_target = None
        min_dist = float('inf')
        for target in targets:
            target_pos = target if not target_is_snake else target.cuerpo[0]
            distance = abs(position[0] - target_pos[0]) + abs(position[1] - target_pos[1])
            if distance < min_dist:
                min_dist = distance
                closest_target = target
        # Devolver la posición del objetivo más cercano
        if closest_target:
            return closest_target if not target_is_snake else closest_target.cuerpo[0]
        return None

    def _get_direction_towards(self, start_pos, end_pos):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]

        # Elegir la dirección principal (mayor diferencia absoluta)
        if abs(dx) > abs(dy):
            # Mover horizontalmente
            return (dx // abs(dx), 0) if dx != 0 else (0, 0) # Evitar división por cero
        elif abs(dy) > abs(dx):
            # Mover verticalmente
            return (0, dy // abs(dy)) if dy != 0 else (0, 0)
        else: # Empate (movimiento diagonal)
            # Elegir al azar entre moverse horizontal o verticalmente hacia el objetivo
            if dx != 0 and dy != 0:
                return random.choice([(dx // abs(dx), 0), (0, dy // abs(dy))])
            elif dx != 0: # Solo movimiento horizontal posible
                return (dx // abs(dx), 0)
            elif dy != 0: # Solo movimiento vertical posible
                return (0, dy // abs(dy))
            else: # start_pos == end_pos
                return (0,0) # O elegir una dirección aleatoria? (0,0) indica que ya está allí

# Ejemplo de placeholder para la clase Entorno
class Entorno:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Podría contener información sobre obstáculos, etc.

# --- Gestor de la Simulación ---
class SimulationManager:
    def __init__(self, width, height, initial_snakes=5, initial_food=10, mutation_rate=0.1, reproduction_energy_cost=25, max_age=10000, food_energy=50, snake_initial_energy=1000):
        self.width = width
        self.height = height
        self.entorno = Entorno(width, height)
        self.serpientes = []
        self.comida = []
        self.paso_actual = 0
        self._next_snake_id = 0
        self.mutation_rate = mutation_rate
        self.reproduction_energy_cost = reproduction_energy_cost
        self.max_age = max_age
        self.food_energy = food_energy
        self.snake_initial_energy = snake_initial_energy
        self._inicializar_simulacion(initial_snakes, initial_food, self.snake_initial_energy)

    def _get_new_snake_id(self):
        self._next_snake_id += 1
        return self._next_snake_id

    def _posicion_aleatoria(self):
        return (random.randint(0, self.width - 1), random.randint(0, self.height - 1))

    def _inicializar_simulacion(self, num_serpientes, num_comida, initial_energy):
        self.serpientes = [] # Asegurar que la lista esté vacía al inicializar
        self.comida = []
        self._next_snake_id = 0
        # Crear serpientes iniciales
        for i in range(num_serpientes):
            x, y = self._posicion_aleatoria()
            # Asegurar que las posiciones iniciales no se solapen (simple check)
            while any( (x,y) in s.cuerpo for s in self.serpientes ):
                 x, y = self._posicion_aleatoria()
            # Color aleatorio y ID único
            color = random.choice(['#0000FF', '#800080', '#FFA500', '#FFC0CB', '#008000'])
            nueva_serpiente = Serpiente(self._get_new_snake_id(), x, y, color=color)
            nueva_serpiente.energia = initial_energy
            self.serpientes.append(nueva_serpiente)
            logging.info(f"Serpiente inicial {nueva_serpiente.id} creada en {(x,y)} con color {color} y energía {initial_energy}")

        # Colocar comida inicial
        for _ in range(num_comida):
            self._añadir_comida(1)
        logging.info(f"Simulación inicializada con {len(self.serpientes)} serpientes y {len(self.comida)} comidas.")


    def _añadir_comida(self, cantidad=1):
        for _ in range(cantidad):
             pos = self._posicion_aleatoria()
             # Evitar poner comida donde ya hay comida o serpientes
             intentos = 0
             max_intentos = self.width * self.height # Evitar bucle infinito si todo está lleno
             while (pos in self.comida or any(pos in s.cuerpo for s in self.serpientes)) and intentos < max_intentos:
                 pos = self._posicion_aleatoria()
                 intentos += 1
             if intentos < max_intentos:
                  self.comida.append(pos)
             else:
                  logging.warning("No se pudo encontrar espacio para añadir comida.")

    def reproducir(self, s1, s2):
        """Intenta reproducir dos serpientes, devolviendo la nueva serpiente o None."""
        # <<< DEBUG LOGGING INICIAL >>>
        logging.info(f"Intentando reproducir S{s1.id} (E:{s1.energia}) con S{s2.id} (E:{s2.energia})")
        # <<< FIN DEBUG LOGGING >>>

        # Requisito de energía para reproducirse
        # <<< DEBUG LOGGING PRE-CHECK >>>
        logging.debug(f"Check Energía: S1={s1.energia}>={self.reproduction_energy_cost}? {s1.energia >= self.reproduction_energy_cost}. S2={s2.energia}>={self.reproduction_energy_cost}? {s2.energia >= self.reproduction_energy_cost}")
        # <<< FIN DEBUG LOGGING >>>
        if s1.energia < self.reproduction_energy_cost or s2.energia < self.reproduction_energy_cost:
            logging.debug(f"Reproducción fallida entre {s1.id} y {s2.id}: Energía insuficiente.")
            return None

        # Coste de energía
        s1.energia -= self.reproduction_energy_cost
        s2.energia -= self.reproduction_energy_cost
        # <<< DEBUG LOGGING >>>
        logging.debug(f"Energía post-reproducción - S1 ({s1.id}): {s1.energia}, S2 ({s2.id}): {s2.energia}")
        # <<< FIN DEBUG LOGGING >>>

        # 1. Crossover de Genes
        punto_cruce = len(s1.genes) // 2
        genes_hijo = s1.genes[:punto_cruce] + s2.genes[punto_cruce:]

        # 2. Mutación
        for i in range(len(genes_hijo)):
            if random.random() < self.mutation_rate:
                genes_hijo[i] = random.random()

        # 3. Color del hijo
        try:
             c1 = tuple(int(s1.color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
             c2 = tuple(int(s2.color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
             cr = (c1[0] + c2[0]) // 2
             cg = (c1[1] + c2[1]) // 2
             cb = (c1[2] + c2[2]) // 2
             # Mutación ligera de color
             cr = max(0, min(255, cr + random.randint(-10, 10)))
             cg = max(0, min(255, cg + random.randint(-10, 10)))
             cb = max(0, min(255, cb + random.randint(-10, 10)))
             color_hijo = f'#{cr:02x}{cg:02x}{cb:02x}'
        except ValueError: # Si los colores no son hex válidos
             color_hijo = random.choice([s1.color, s2.color]) # Elegir uno al azar

        # <<< 4. NUEVA LÓGICA: Buscar Posición del hijo (ALEATORIA y vacía) >>>
        pos_hijo = None
        empty_spots = []

        # Crear conjuntos de todas las coordenadas y las ocupadas
        all_coords = set((x, y) for x in range(self.width) for y in range(self.height))
        occupied_food = set(self.comida)
        occupied_snakes = set()
        for s in self.serpientes:
            for segment in s.cuerpo:
                occupied_snakes.add(segment)

        # Calcular coordenadas vacías
        available_coords = all_coords - occupied_food - occupied_snakes

        if not available_coords:
             logging.warning(f"Reproducción entre {s1.id} y {s2.id}: No hay espacio vacío en el tablero para nacer. No nace hijo.")
             return None # Falló el nacimiento por falta de espacio
        else:
             pos_hijo = random.choice(list(available_coords))
             logging.debug(f"Posición de nacimiento aleatoria elegida para hijo de {s1.id} y {s2.id}: {pos_hijo}")

        # Incrementar contador de hijos de los padres
        s1.hijos_generados += 1
        s2.hijos_generados += 1
        
        # 5. Crear la nueva serpiente
        hijo = Serpiente(self._get_new_snake_id(), pos_hijo[0], pos_hijo[1], color=color_hijo, genes=genes_hijo)
        hijo.energia = self.reproduction_energy_cost * 2
        logging.info(f"¡Reproducción! Serpientes {s1.id} y {s2.id} crean hijo {hijo.id} en {pos_hijo}. Energía hijo: {hijo.energia}")
        return hijo

    def step(self):
        """Avanza un paso en la simulación."""
        serpientes_a_eliminar = set() # Usar un set para evitar duplicados
        nuevas_serpientes = []
        serpientes_procesadas_ids = set()

        # Iterar sobre una copia de la lista para poder modificarla durante la iteración (al añadir hijos)
        # Aunque añadimos hijos a 'nuevas_serpientes', es más seguro iterar sobre índices o copia
        # for serpiente in list(self.serpientes): # Iterar sobre copia
        # O mejor, iterar con índice para manejar la lista original
        for i in range(len(self.serpientes) -1, -1, -1): # Iterar hacia atrás por si eliminamos
            serpiente = self.serpientes[i]

            # Si la serpiente ya fue marcada para eliminar en este paso (ej. por colisión mutua)
            # O si ya se procesó (esto no debería pasar con el bucle for actual, pero como seguro)
            if serpiente.id in serpientes_a_eliminar or serpiente.id in serpientes_procesadas_ids:
                continue

            # 0. Verificar si debe morir antes de moverse (por si acaso)
            if serpiente.energia <= 0:
                logging.warning(f"Serpiente {serpiente.id} eliminada (pre-movimiento): Sin energía ({serpiente.energia}).")
                serpientes_a_eliminar.add(serpiente.id)
                continue
            if serpiente.edad > self.max_age:
                logging.warning(f"Serpiente {serpiente.id} eliminada (pre-movimiento): Edad límite ({serpiente.edad}/{self.max_age}).")
                serpientes_a_eliminar.add(serpiente.id)
                continue

            # 1. Decidir y intentar mover
            direccion = serpiente.decidir_movimiento(self, self.comida, self.serpientes)
            movimiento_valido = serpiente.mover(direccion, self.width, self.height)

            # 2. Comprobar muerte por pared
            if not movimiento_valido:
                logging.warning(f"Serpiente {serpiente.id} marcada para eliminar: Colisión con pared.")
                serpientes_a_eliminar.add(serpiente.id)
                continue # Pasar a la siguiente serpiente

            # Si el movimiento fue válido, obtener la nueva cabeza
            cabeza_actual = serpiente.cuerpo[0]

            # 3. Comprobar colisión con comida
            comio_comida = False
            comida_comida_idx = -1
            for food_idx, pos_comida in enumerate(self.comida):
                if cabeza_actual == pos_comida:
                    serpiente.energia += self.food_energy
                    serpiente.comida_comida += 1 # <-- Incrementar contador
                    # La serpiente crece: no quitamos la cola
                    comida_comida_idx = food_idx
                    self._añadir_comida(1)
                    comio_comida = True
                    logging.debug(f"Serpiente {serpiente.id} comió comida #{serpiente.comida_comida} en {pos_comida}. Energía: {serpiente.energia}")
                    break

            if comida_comida_idx != -1:
                del self.comida[comida_comida_idx]

            # 4. Acortar cola SI NO COMIÓ
            if not comio_comida:
                if len(serpiente.cuerpo) > 1:
                     serpiente.cuerpo.pop()
                else:
                     # Si solo tiene cabeza y no comió, muere por inanición implícita?
                     # O simplemente no se acorta. Por ahora, no hacemos nada.
                     pass
                if cabeza_actual in serpiente.cuerpo[1:]:
                      logging.warning(f"Serpiente {serpiente.id} detectó colisión consigo misma (tras acortar) en {cabeza_actual} (no fatal).")
                      # No hacer nada, ya que la auto-colisión no es fatal

            # 5. Comprobar auto-colisión (ya no fatal)
            elif cabeza_actual in serpiente.cuerpo[1:]: # Se comprueba aquí si comió (cola no se acortó)
                logging.warning(f"Serpiente {serpiente.id} detectó colisión consigo misma (tras comer) en {cabeza_actual} (no fatal).")
                # No hacer nada

            # 7. Chequear muerte por energía o edad (final del turno de la serpiente)
            # Si ya está marcada por colisión de pared, no volver a marcar
            if serpiente.id not in serpientes_a_eliminar:
                 if serpiente.energia <= 0:
                     logging.warning(f"Serpiente {serpiente.id} marcada para eliminar: Sin energía ({serpiente.energia}) al final del turno.")
                     serpientes_a_eliminar.add(serpiente.id)
                 elif serpiente.edad > self.max_age:
                     logging.warning(f"Serpiente {serpiente.id} marcada para eliminar: Edad límite ({serpiente.edad}/{self.max_age}) al final del turno.")
                     serpientes_a_eliminar.add(serpiente.id)

            serpientes_procesadas_ids.add(serpiente.id)

        # --- Fin del bucle principal de serpientes --- 

        # <<< NUEVA SECCIÓN 8: Comprobar Reproducción por Adyacencia >>>
        reproduced_ids = set() # Para evitar que una serpiente se reproduzca varias veces
        potential_parents = [s for s in self.serpientes if s.id not in serpientes_a_eliminar]
        logging.debug(f"Paso {self.paso_actual}: Comprobando adyacencia para reproducción entre {len(potential_parents)} padres potenciales.")

        for idx1 in range(len(potential_parents)):
            s1 = potential_parents[idx1]
            # Si ya se reprodujo en este paso, saltar
            if s1.id in reproduced_ids:
                continue

            for idx2 in range(idx1 + 1, len(potential_parents)):
                s2 = potential_parents[idx2]
                # Si la segunda ya se reprodujo, saltar
                if s2.id in reproduced_ids:
                    continue

                # Comprobar adyacencia de cabezas (Manhattan distance == 1)
                head1 = s1.cuerpo[0]
                head2 = s2.cuerpo[0]
                distance = abs(head1[0] - head2[0]) + abs(head1[1] - head2[1])

                if distance == 1:
                    logging.debug(f"Adyacencia detectada entre S{s1.id} en {head1} y S{s2.id} en {head2}. Intentando reproducción.")
                    # <<< Pasar serpientes_a_eliminar a reproducir para la comprobación de espacio >>>
                    # Esto es complicado. Modifiquemos reproducir para que reciba la lista de vivos.
                    # O simplifiquemos la comprobación de espacio en reproducir (riesgo menor)
                    # Vamos a simplificar en reproducir por ahora.
                    hijo = self.reproducir(s1, s2)
                    if hijo:
                        nuevas_serpientes.append(hijo)
                        # Marcar ambos padres como reproducidos en este paso
                        reproduced_ids.add(s1.id)
                        reproduced_ids.add(s2.id)
                        # Salir del bucle interno (s1 ya se reprodujo)
                        break

        # 9. Eliminar serpientes marcadas
        num_eliminadas = 0
        supervivientes = []
        for serpiente in self.serpientes:
            if serpiente.id not in serpientes_a_eliminar:
                supervivientes.append(serpiente)
            else:
                 num_eliminadas += 1
        if num_eliminadas > 0:
             logging.info(f"Paso {self.paso_actual}: Eliminando {num_eliminadas} serpientes (IDs: {[sid for sid in serpientes_a_eliminar]}). Quedan {len(supervivientes)}.")
        self.serpientes = supervivientes

        # 10. Añadir nuevas serpientes (hijos)
        if nuevas_serpientes:
             logging.info(f"Paso {self.paso_actual}: Añadiendo {len(nuevas_serpientes)} nuevos hijos.")
             self.serpientes.extend(nuevas_serpientes)

        # 11. Incrementar paso
        self.paso_actual += 1

        # 12. Asegurar que haya algo de comida siempre (ejemplo)
        if not self.comida and self.serpientes: # Solo añadir si quedan serpientes
            num_nueva_comida = min(5, len(self.serpientes)) # Añadir proporcionalmente? O fijo?
            logging.debug(f"No queda comida. Añadiendo {num_nueva_comida} items.")
            self._añadir_comida(num_nueva_comida)
        elif len(self.comida) < 5 and self.serpientes: # Mantener un mínimo de comida
             self._añadir_comida(1)

    def get_state(self):
        """Devuelve el estado actual para serializar a JSON."""
        # Se asume que se llama dentro de un lock
        state = {
            'paso': self.paso_actual,
            'serpientes': [
                {
                    'id': s.id,
                    'cuerpo': s.cuerpo,
                    'color': s.color,
                    'energia': s.energia,
                    'edad': s.edad,
                    'comida_comida': s.comida_comida,
                    'hijos': s.hijos_generados,
                    # <<< AÑADIR GENES (formateados/reducidos) >>>
                    # Enviar todos puede ser mucho, enviemos los primeros 3 redondeados
                    'genes_display': [round(g, 2) for g in s.genes[:3]] if s.genes else []
                } for s in self.serpientes
            ],
            'comida': self.comida,
            'dimensiones': {
                 'width': self.width,
                 'height': self.height
            }
            # Podríamos añadir estadísticas aquí
            # 'stats': {
            #     'num_serpientes': len(self.serpientes),
            #     'num_comida': len(self.comida),
            #     'avg_energia': sum(s.energia for s in self.serpientes) / len(self.serpientes) if self.serpientes else 0,
            #     'avg_edad': sum(s.edad for s in self.serpientes) / len(self.serpientes) if self.serpientes else 0
            # }
        }
        return state

    # <<< NUEVO MÉTODO RESET >>>
    def reset(self):
        logging.info("Llamando a SimulationManager.reset()...")
        # Guardar los parámetros iniciales si no se guardaron antes
        # (Aunque ya están como atributos gracias al __init__ mejorado)
        initial_snakes = len([s for s in self.serpientes if s.edad == 0 and s.energia == self.snake_initial_energy]) # Una forma de estimar, o mejor guardarlos
        # Mejor opción: Guardar en __init__
        if not hasattr(self, '_initial_snakes'): self._initial_snakes = 5 # Valor por defecto si no se guardó
        if not hasattr(self, '_initial_food'): self._initial_food = 10 # Valor por defecto si no se guardó

        # Llamar al método de inicialización
        try:
            # Usar los atributos de la instancia actual si están disponibles
            snakes_to_create = getattr(self, '_initial_snakes', 5)
            food_to_create = getattr(self, '_initial_food', 10)
            self._inicializar_simulacion(snakes_to_create, food_to_create, self.snake_initial_energy)
            self.paso_actual = 0 # Resetear contador de pasos
            logging.info("Simulación reseteada por SimulationManager.reset().")
            return True
        except Exception as e:
            logging.error(f"Error durante SimulationManager.reset(): {e}", exc_info=True)
            return False

    # --- Métodos potenciales a implementar --- (Ya no son necesarios aquí)