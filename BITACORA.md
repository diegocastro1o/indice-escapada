# Bitácora del proyecto

## Objetivo

Este primer proyecto busca responder la siguiente pregunta:

> ¿Cuál es el mejor fin de semana largo del año para escaparse en Uruguay y adónde?

El proyecto se dividirá en distintos hitos. Cada uno representará una etapa del trabajo, en la que se documentarán:

- Decisiones
- Inconvenientes
- Procedimientos
- Aprendizajes

---

## Elección de la API

El primer aspecto fundamental de nuestro trabajo fue la elección de la API. Luego de una búsqueda exhaustiva, necesitábamos una que cumpliera con nuestras necesidades. En ese momento encontramos la API de **Foursquare**.

Foursquare permitía solicitar ubicaciones de interés cerca de un lugar. Detectaba y devolvía ubicaciones de restaurantes, boliches, zonas de entretenimiento, atracciones, entre otros.

Esta posibilidad sería crucial y de gran ayuda para responder la pregunta del proyecto. Finalmente, decidimos descartar esta API porque, para utilizarla, debíamos ingresar un método de pago como parte del registro.

---

# Hito 1 — Inicio del proyecto

Comenzamos creando un repositorio en **Git** para poder trabajar de forma sincronizada. Utilizamos **PyCharm** como entorno de desarrollo.

Creamos la carpeta `indice-escapada`, que sería el lugar principal de nuestros archivos.

También creamos la carpeta solicitada en los requisitos, llamada `config`. Dentro de ella se encuentra el archivo `ubicaciones.json`.

## Lugar de partida

- Montevideo

## Destinos elegidos

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

    
Agregamos al achivo ubicaciones.json el lugar de partida y los destinos, cada uno con una id respectiva y su forma de llamarlos en la API.
Creamos la carpeta SRC, dentro tiene dos archivos: 
-geocoding.py
Este archivo se compone de 4 funciones principales.
cargar_ubicaciones: extrae un punto de origen y una lista de destinos, devolviendo una lista unificada.
cargar_cache: verifica si existe el archivo de cache, sino devuelve un diccionario vacio. Si existe, lee la informacion y devuelve el diccionario con la informacion previa.
guardar_cache: toma los resultados obtenidos y los guarda para el futuro.
buscar_coordenadas: se comunica directamente con la API para obtener las coordenadas
geocodificar_todo: esta funcion es el motor de todo, ordena y orquesta todas las funciones anteriores. Maneja errores y va guardando datos

-weather.py



