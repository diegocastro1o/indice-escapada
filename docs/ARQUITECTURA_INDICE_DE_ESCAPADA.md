# Arquitectura del proyecto Índice de Escapada

Este documento explica cómo está organizado el programa, cómo circulan los datos y qué responsabilidad tiene cada archivo importante.

## 1. Idea general

El proyecto está diseñado como un pipeline de datos. Primero obtiene información de distintas APIs, luego la guarda en caché, después la transforma y finalmente construye un ranking de destinos para cada fin de semana largo.

La separación principal es:

```text
configuración → recolección → caché → procesamiento → ranking
```

Cada etapa puede ejecutarse por separado y también puede ejecutarse todo el flujo mediante `src/main.py`.

## 2. Configuración de destinos

El flujo comienza en `config/ubicaciones.json`. Allí se definen Montevideo y los destinos uruguayos, con sus identificadores, nombres y consultas de geocoding.

Para algunos destinos también se define un `punto_ruta`. Esto permite separar el lugar cuyo clima se analiza del punto hasta el que se puede calcular una ruta vehicular realista.

## 3. Recolección de datos

Los módulos de `src/` consultan las APIs externas:

- Nominatim aporta las coordenadas.
- Open-Meteo aporta el clima histórico diario.
- Nager.Date aporta los feriados.
- OpenRouteService aporta distancia y duración del viaje desde Montevideo.

Cada cliente verifica el estado HTTP, valida el contenido de la respuesta y aplica reintentos ante errores temporales.

La recolección climática tiene una versión síncrona y otra asíncrona. La asíncrona paraleliza tareas independientes destino-año, pero mantiene un semáforo, un ritmo máximo de solicitudes y una pausa global ante respuestas `429`.

Nominatim se ejecuta secuencialmente por su límite público de una solicitud por segundo. Feriados y rutas también permanecen secuenciales porque son pocas consultas y no representan el cuello de botella medido.

## 4. Caché de datos crudos

Las respuestas correctas se guardan inmediatamente en `data/raw/`. La estructura representa unidades independientes:

```text
data/raw/
├── geocoding.json
├── holidays/<año>.json
├── routes.json
└── weather/<destino>/<año>.json
```

Si una corrida se interrumpe, los archivos ya guardados permanecen disponibles. Al volver a ejecutar el programa sin `--force`, se reutilizan los datos válidos y solo se descargan los faltantes.

## 5. Procesamiento y construcción del índice

`src/index.py` trabaja sobre los datos cacheados, no sobre respuestas nuevas de las APIs. Calcula promedios climáticos históricos para las fechas de cada fin de semana largo, transforma las variables a puntajes comparables, incorpora el tiempo de viaje y la duración del fin de semana, y aplica la fórmula documentada en `INDICE.md`.

El resultado se guarda en `data/processed/` como un JSON procesado y también se muestra en la terminal en forma de ranking.

## 6. Orquestación del pipeline

`src/main.py` funciona como interfaz de línea de comandos y coordinador. Permite ejecutar etapas individuales o el flujo completo:

```text
geocoding → clima → feriados → rutas → ranking
```

El orden importa porque cada etapa produce datos que necesita la siguiente. La caché hace que una etapa ya completada no tenga que repetirse.

## 7. Responsabilidad de cada archivo importante

| Archivo | Responsabilidad |
|---|---|
| `config/ubicaciones.json` | Configura Montevideo, los destinos, las consultas de geocoding y los puntos alternativos de ruta. |
| `src/main.py` | Expone la CLI, interpreta comandos y coordina el pipeline completo. |
| `src/cache.py` | Proporciona utilidades para leer JSON opcionalmente y escribir archivos de forma atómica. |
| `src/geocoding.py` | Consulta Nominatim, respeta su límite de frecuencia, valida coordenadas y conserva resultados parciales. |
| `src/weather.py` | Descarga y valida el clima histórico de Open-Meteo; contiene recolectores síncrono y asíncrono, caché, reintentos y limitación de solicitudes. |
| `src/holidays.py` | Descarga feriados de Nager.Date, valida las fechas y detecta fines de semana largos. |
| `src/routes.py` | Consulta OpenRouteService, valida las rutas y convierte distancia y duración a unidades útiles para el índice. |
| `src/index.py` | Calcula promedios históricos, puntajes, rankings y conclusiones comparativas. |
| `data/raw/` | Almacena las respuestas crudas cacheadas de las APIs. |
| `data/processed/` | Almacena resultados derivados, como el ranking final. |
| `INDICE.md` | Explica la fórmula, los pesos y las decisiones del criterio de puntuación. |
| `BITACORA.md` | Registra la evolución del proyecto por hitos, mediciones y decisiones técnicas. |
| `README.md` | Contiene instrucciones de instalación, configuración, ejecución y verificación. |
| `pyproject.toml` | Declara el proyecto, sus dependencias y la configuración de herramientas. |
| `uv.lock` | Fija las versiones exactas de las dependencias para reproducir el entorno. |

## 8. Principios de diseño

- Cada módulo tiene una responsabilidad específica.
- Las APIs se consultan durante la recolección, no durante el cálculo del ranking.
- La caché permite reanudar, reproducir y acelerar futuras ejecuciones.
- La asincronía se usa donde aporta una mejora real y se limita según la API correspondiente.
- Las validaciones impiden que datos incompletos lleguen al cálculo final.
- Los resultados derivados pueden regenerarse a partir de los datos crudos cacheados.

## 9. Recorrido completo de una ejecución

1. Se leen los destinos configurados.
2. Se completan las coordenadas faltantes.
3. Se descarga el clima histórico de cada combinación destino-año.
4. Se descargan los feriados del año objetivo.
5. Se calculan y cachean las rutas.
6. Se combinan clima, feriados y accesibilidad.
7. Se calcula el puntaje final y se genera el ranking.

El sistema queda así dividido en una parte de obtención de datos y otra de análisis. Esa separación permite cambiar una fuente, repetir el cálculo o actualizar el ranking sin volver a descargar todo.
