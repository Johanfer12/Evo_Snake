const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const statsDiv = document.getElementById('stats');

// --- Configuración Inicial --- 
// Leer dimensiones desde los atributos de datos del canvas
let boardWidth = parseInt(canvas.getAttribute('data-width')) || 30; // Ancho lógico
let boardHeight = parseInt(canvas.getAttribute('data-height')) || 20; // Alto lógico
let TILE_SIZE = 20; // Tamaño en píxeles de cada celda

// Ajustar tamaño inicial del canvas
canvas.width = boardWidth * TILE_SIZE;
canvas.height = boardHeight * TILE_SIZE;

console.log(`Canvas inicializado: ${boardWidth}x${boardHeight} tiles, ${canvas.width}x${canvas.height} pixels`);

function drawBoard() {
    // Dibuja el fondo (ya hecho con background-color en HTML/CSS, pero podemos añadir cuadrícula)
    ctx.strokeStyle = '#ddd'; // Color de la cuadrícula
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= canvas.width; x += TILE_SIZE) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }
    for (let y = 0; y <= canvas.height; y += TILE_SIZE) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }
}

function drawSnake(snakeData) {
    // Usar el color de la serpiente si existe, sino uno por defecto
    const mainColor = snakeData.color || 'green';
    ctx.fillStyle = mainColor;

    snakeData.cuerpo.forEach((segment, index) => {
        // Dibujar cuerpo
        ctx.fillRect(segment[0] * TILE_SIZE, segment[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        // Dibujar un borde para distinguir segmentos (opcional)
        // ctx.strokeStyle = 'black';
        // ctx.strokeRect(segment[0] * TILE_SIZE, segment[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE);

        // Dibujar la cabeza diferente
        if (index === 0) {
            // Podríamos hacerla un poco más oscura o con un borde más grueso
            ctx.fillStyle = darkenColor(mainColor, 30); // Función para oscurecer (ver abajo)
            ctx.fillRect(segment[0] * TILE_SIZE, segment[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            ctx.strokeStyle = 'black'; // Borde negro para la cabeza
            ctx.lineWidth = 1;
            ctx.strokeRect(segment[0] * TILE_SIZE + 1, segment[1] * TILE_SIZE + 1, TILE_SIZE - 2, TILE_SIZE - 2);
            ctx.fillStyle = mainColor; // Restaurar color para el resto del cuerpo
        }
    });
}

function drawFood(foodItems) {
    ctx.fillStyle = 'red';
    foodItems.forEach(foodPos => {
        // Comprobar que las coordenadas son válidas
        if (typeof foodPos[0] === 'number' && typeof foodPos[1] === 'number') {
            ctx.beginPath();
            ctx.arc(
                foodPos[0] * TILE_SIZE + TILE_SIZE / 2, // Centro X
                foodPos[1] * TILE_SIZE + TILE_SIZE / 2, // Centro Y
                TILE_SIZE / 3, // Radio (un poco más pequeño que la celda)
                0, 2 * Math.PI // Círculo completo
            );
            ctx.fill();
        } else {
             console.warn("Posición de comida inválida:", foodPos);
        }
    });
}

function updateStats(paso, numSerpientes, numComida) {
    statsDiv.textContent = `Paso: ${paso} | Serpientes: ${numSerpientes} | Comida: ${numComida}`;
}

// Función para formatear los genes con sus descripciones
function formatGenes(genes) {
    if (!genes || genes.length === 0) return 'N/A';
    
    const descriptions = [
        "Visión",    // Gen 0: Rango de visión
        "E.Baja",    // Gen 1: Umbral energía baja
        "E.Alta"     // Gen 2: Umbral energía alta
    ];
    
    return genes.map((gen, index) => 
        `${descriptions[index] || `Gen${index}`}: ${gen}`
    ).join(', ');
}

// Función para mostrar información detallada sobre los genes
function getGeneDescription(index) {
    const descriptions = [
        "Rango de visión: Determina qué tan lejos puede ver la serpiente. Valores más altos permiten detectar comida y otras serpientes a mayor distancia.",
        "Energía baja: Define cuándo la serpiente buscará comida de forma prioritaria. Si su energía cae por debajo de este umbral, ignorará posibles parejas y se enfocará en comer.",
        "Energía alta: Establece el umbral a partir del cual la serpiente buscará reproducirse. Solo cuando su energía supere este valor, intentará encontrar una pareja en lugar de buscar comida."
    ];

    return descriptions[index] || `Gen ${index}: Función desconocida`;
}

// Añadir función para mostrar las estadísticas detalladas de las serpientes
function updateSnakeStats(snakes) {
    const snakeList = document.getElementById('snakeList');
    snakeList.innerHTML = ''; // Limpiar estadísticas anteriores
    
    // Para cada serpiente, mostrar sus estadísticas
    snakes.forEach(snake => {
        const listItem = document.createElement('li');
        
        // Mostrar ID, genes y cantidad de hijos
        listItem.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 15px; height: 15px; background-color: ${snake.color}; margin-right: 5px;"></div>
                <strong>Serpiente ${snake.id}</strong>
            </div>
            <div class="gene-info">
                ${formatGenes(snake.genes_display)}
                <div class="gene-tooltip">
                    <span>ℹ️</span>
                    <div class="tooltip-content">
                        <p>${getGeneDescription(0)}</p>
                        <p>${getGeneDescription(1)}</p>
                        <p>${getGeneDescription(2)}</p>
                    </div>
                </div>
            </div>
            <div>Hijos: ${snake.hijos || 0}</div>
            <div>Comida: ${snake.comida_comida}</div>
        `;
        snakeList.appendChild(listItem);
    });
}

async function fetchAndUpdate() {
    try {
        const response = await fetch('/game_state');
        if (!response.ok) {
            console.error("Error al obtener estado:", response.status, response.statusText);
            try {
                const errorData = await response.json();
                console.error("Detalles del error del servidor:", errorData);
                statsDiv.textContent = `Error ${response.status}: ${errorData.error || response.statusText}`;
            } catch (jsonError) {
                statsDiv.textContent = `Error ${response.status}: ${response.statusText}`;
            }
            return; // No continuar si hay error
        }
        const gameState = await response.json();

        // <<< DEBUG LOGGING >>>
        console.log("Estado recibido del servidor:", gameState);
        // <<< FIN DEBUG LOGGING >>>

        // Verificar si las dimensiones han cambiado (aunque en este ejemplo son fijas)
        let dimensionsChanged = false;
        if (gameState.dimensiones) {
            if (gameState.dimensiones.width !== boardWidth || gameState.dimensiones.height !== boardHeight) {
                 boardWidth = gameState.dimensiones.width;
                 boardHeight = gameState.dimensiones.height;
                 canvas.width = boardWidth * TILE_SIZE;
                 canvas.height = boardHeight * TILE_SIZE;
                 dimensionsChanged = true;
                 console.log(`Dimensiones actualizadas a ${boardWidth}x${boardHeight}`);
            }
        }

        // Limpiar y Redibujar
        // ctx.clearRect(0, 0, canvas.width, canvas.height); // Limpiar canvas
        // Es mejor redibujar el fondo en lugar de limpiar para evitar parpadeo
        ctx.fillStyle = '#8FBC8F'; // Color de fondo VERDE HIERBA
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        drawBoard(); // Dibujar cuadrícula

        // Dibujar elementos del juego
        if (gameState.comida && Array.isArray(gameState.comida)) {
             drawFood(gameState.comida);
        } else {
             console.warn("Datos de comida inválidos o ausentes", gameState.comida);
        }

        if (gameState.serpientes && Array.isArray(gameState.serpientes)){
             // <<< DEBUG LOGGING >>>
             console.log(`Dibujando ${gameState.serpientes.length} serpientes...`);
             // <<< FIN DEBUG LOGGING >>>
             gameState.serpientes.forEach(snake => {
                 // <<< DEBUG LOGGING >>>
                 console.log("  Dibujando serpiente:", snake.id, snake.color, snake.cuerpo);
                 // <<< FIN DEBUG LOGGING >>>
                 drawSnake(snake)
             });
             
             // Actualizar estadísticas detalladas de serpientes
             updateSnakeStats(gameState.serpientes);
        } else {
             console.warn("Datos de serpientes inválidos o ausentes", gameState.serpientes);
        }

        // Actualizar Estadísticas
        updateStats(gameState.paso, gameState.serpientes?.length || 0, gameState.comida?.length || 0);

    } catch (error) {
        console.error("Error en fetchAndUpdate:", error);
        statsDiv.textContent = "Error de conexión o procesando datos.";
        // Podrías querer detener el intervalo si hay errores repetidos
        // clearInterval(intervalId);
    }
}

// --- Funciones auxiliares ---
function darkenColor(color, amount) {
    // Función simple para oscurecer un color (aproximado)
    // Asume color en formato 'colorname' o '#rrggbb'. Simplificado.
    // Para una solución robusta, se necesitaría parsear el color.
    if (color.startsWith('#')) {
         // Lógica básica para hex (sin validación completa)
         try {
             let r = parseInt(color.slice(1, 3), 16);
             let g = parseInt(color.slice(3, 5), 16);
             let b = parseInt(color.slice(5, 7), 16);
             r = Math.max(0, r - amount);
             g = Math.max(0, g - amount);
             b = Math.max(0, b - amount);
             return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
         } catch (e) { return color; } // Devolver original si falla
    } else {
        // Para nombres de color, es más complejo. Devolver un gris oscuro genérico.
        return '#555555'; // Gris oscuro
    }
}


// --- Iniciar el Bucle de Actualización ---
const updateInterval = 150; // Milisegundos (más lento que simulación para dar tiempo a renderizar)
console.log(`Iniciando actualización del juego cada ${updateInterval} ms`);
let intervalId = setInterval(fetchAndUpdate, updateInterval);

// Llamada inicial para no esperar el primer intervalo
console.log("Realizando primera llamada a fetchAndUpdate...");
fetchAndUpdate();

// Agregar el manejador de eventos para el botón de reinicio
document.getElementById('resetButton').addEventListener('click', async function() {
    console.log("Botón de reinicio clickeado");
    try {
        const response = await fetch('/reset_simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        console.log("Respuesta de reset:", data);
        
        if (response.ok) {
            console.log("Simulación reiniciada exitosamente.");
            // Actualizar inmediatamente para mostrar el estado inicial
            fetchAndUpdate();
        } else {
            console.error("Error al reiniciar:", data.message);
            alert("Error al reiniciar la simulación: " + data.message);
        }
    } catch (error) {
        console.error("Error de conexión al reiniciar:", error);
        alert("Error de conexión al intentar reiniciar la simulación");
    }
}); 