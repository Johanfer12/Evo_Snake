# Evo_Snake
# Simulación de Serpientes Evolutivas

## Descripción
Este proyecto implementa una simulación evolutiva donde las serpientes compiten por comida, sobreviven y se reproducen siguiendo reglas genéticas. Las serpientes desarrollan comportamientos diferentes basados en sus genes, que determinan cómo perciben su entorno y toman decisiones.

## Características
- Simulación de evolución en tiempo real
- Representación visual del entorno con serpientes y comida
- Sistema genético con herencia y mutación
- Estadísticas detalladas por serpiente
- Posibilidad de reiniciar la simulación

## Requisitos
- Python 3.6 o superior
- Flask

## Instalación
1. Clona este repositorio
2. Instala las dependencias:
```
pip install -r requirements.txt
```

## Ejecución
Para iniciar la simulación:
```
python app.py
```
Abre tu navegador en: http://localhost:5000

## Funcionamiento

### Serpientes
Cada serpiente está controlada por un conjunto de genes que determinan su comportamiento:

- **Visión**: Determina el rango de visión de la serpiente. Valores más altos permiten detectar comida y otras serpientes a mayor distancia.
- **Energía Baja**: Define cuándo la serpiente priorizará buscar comida. Si su energía cae por debajo de este umbral, ignorará posibles parejas.
- **Energía Alta**: Establece el umbral para buscar reproducirse. Solo cuando supere este valor, buscará pareja en lugar de comida.

### Reproducción
Las serpientes se reproducen cuando:
1. Están adyacentes entre sí
2. Ambas tienen suficiente energía
3. Al menos una tiene energía superior a su umbral de "Energía Alta"

Los genes de los descendientes son una combinación de los genes de los padres, con posibilidad de mutaciones.

### Ciclo de vida
- Las serpientes pierden energía al moverse
- Ganan energía al comer
- Mueren cuando su energía llega a 0
- La reproducción consume energía de ambos padres

## Interfaz
- **Área de simulación**: Muestra el entorno con serpientes (cuadrados de colores) y comida (círculos rojos)
- **Estadísticas globales**: Muestra el paso actual, número de serpientes y cantidad de comida
- **Estadísticas por serpiente**: Detalla los genes, número de hijos y comida consumida por cada serpiente
- **Botón de reinicio**: Permite reiniciar la simulación desde cero

## Estructura del proyecto
- `app.py`: Servidor Flask y gestión de la simulación
- `simulation.py`: Lógica principal de la simulación y comportamiento evolutivo
- `templates/`: Archivos HTML para la interfaz web
- `static/`: Recursos estáticos (JS, CSS)

## Acerca de
Proyecto realizado con la ayuda de Gemini 2.5 y Claude 3.7
