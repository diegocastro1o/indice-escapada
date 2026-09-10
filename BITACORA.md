# Bitácora del proyecto

## Objetivo

Este primer proyecto busca responder la siguiente pregunta:

> *¿Cuál es el mejor fin de semana largo del año para escaparse en Uruguay y adónde?*

El proyecto se dividirá en distintos hitos. Cada uno representará una etapa del trabajo, en la que se documentarán:
- Decisiones
- Inconvenientes
- Procedimientos
- Aprendizajes

---

## Elección de la API

El primer aspecto fundamental de nuestro trabajo fue la elección de la API. Luego de una búsqueda exhaustiva, necesitábamos una que cumpliera con nuestras necesidades. En ese momento encontramos la API de **Foursquare**.

Foursquare permitía solicitar ubicaciones de interés cerca de un lugar. Detectaba y devolvía ubicaciones de restaurantes, boliches, zonas de entretenimiento, atracciones, entre otros.

Esta posibilidad sería crucial y de gran ayuda para responder la pregunta del proyecto. Finalmente, decidimos **descartar esta API** porque, para utilizarla, debíamos ingresar un método de pago como parte del registro.

---

## Hito 1 — Inicio del proyecto

Comenzamos creando un repositorio en **Git** para poder trabajar de forma sincronizada. Utilizamos **PyCharm** como entorno de desarrollo.

Creamos la carpeta `indice-escapada`, que sería el directorio principal de nuestros archivos. También creamos la carpeta solicitada en los requisitos, llamada `config`. Dentro de ella se encuentra el archivo `ubicaciones.json`.

### Ubicaciones definidas

**Lugar de partida:**
- Montevideo

**Destinos elegidos:**
- Colonia del Sacramento
- Carmelo
- Piriápolis
- Punta del Este
- José Ignacio
- La Paloma
- Cabo Polonio
- Punta del Diablo
- Aguas Dulces
- Minas
- Villa Serrana
- Termas del Daymán
- Salto
- Mercedes
- Tacuarembó

Agregamos al archivo `ubicaciones.json` el lugar de partida y los destinos, cada uno con un `id` respectivo y el término de búsqueda exacto para consultarlos en la API.

---

### Estructura del código (`src`)

Creamos la carpeta `src`, que contiene los siguientes archivos principales:

#### 1. `geocoding.py`
Este script se encarga de obtener las coordenadas y se compone de las siguientes funciones principales:

* **`cargar_ubicaciones`**: Extrae el punto de origen y la lista de destinos, devolviendo una lista unificada lista para procesar.
* **`cargar_cache`**: Verifica si existe un archivo de caché. Si no existe, devuelve un diccionario vacío; si existe, lee y carga la información almacenada previamente.
* **`guardar_cache`**: Toma los resultados obtenidos de la API y los guarda en el disco duro para evitar consultas duplicadas en el futuro.
* **`buscar_coordenadas`**: Se comunica directamente con la API (Nominatim) para obtener la latitud y longitud.
* **`geocodificar_todo`**: Es el motor principal. Ordena y orquesta todas las funciones anteriores, maneja errores y guarda los datos de forma incremental.

#### 2. `weather.py`
Este script está diseñado para conectarse a la API de **Open-Meteo** y descargar datos meteorológicos históricos para los distintos destinos en años específicos, tales como:
* Temperatura máxima y mínima.
* Precipitación.
* Velocidad del viento.

> **Nota de desarrollo (Actualización 10/09):**
> La recolección de datos en Open-Meteo **sí se paraleliza** (modo asíncrono) para agilizar la descarga. Sin embargo, las consultas a Nominatim (`geocoding.py`) **no se paralelizan**, ya que los términos de servicio exigen mantener un límite estricto de una consulta por segundo.



