# Contexto del proyecto para agentes

Este archivo es el punto de entrada para cualquier IA o agente que continúe trabajando en el repositorio. Antes de modificar código, leer también `README.md`, `INDICE.md`, `BITACORA.md`, `pyproject.toml` y los módulos involucrados.

## Qué es Índice de Escapada

Es un proyecto académico de Programación para Ciencia y Tecnología. Busca responder:

> ¿Qué combinación de destino uruguayo y fin de semana largo ofrece la mejor escapada desde Montevideo?

La idea del equipo es cruzar clima histórico, feriados y accesibilidad por carretera. El programa arma un ranking general y por fin de semana largo, y además intenta producir una conclusión no obvia: por ejemplo, cuánto cambia una recomendación cuando se incorpora el tiempo de viaje y no se observa solamente el clima.

## Requisitos centrales de la consigna

- Integrar varias fuentes de datos; el diseño actual usa Nominatim, Open-Meteo, Nager.Date y OpenRouteService.
- Usar al menos una API con autenticación. La elegida es OpenRouteService mediante `ORS_API_KEY`.
- Procesar más de 5.000 registros. El alcance final definido es 15 destinos × 10 años de datos diarios.
- Implementar caché y reanudación para que una segunda ejecución no repita solicitudes y tarde menos de 5 segundos.
- Comparar una implementación síncrona con una asíncrona.
- Identificar qué se puede paralelizar: Open-Meteo sí; Nominatim no, por su límite público de una solicitud por segundo.
- Generar un índice justificable y una conclusión basada en los datos.

No cambiar estas decisiones sin verificar primero la consigna original y acordarlo con el equipo.

## Alcance y decisiones actuales

- Origen fijo de las rutas: Montevideo.
- Destinos: 15, definidos en `config/ubicaciones.json`.
- Histórico climático: 2015–2024 inclusive.
- Año objetivo habitual: 2026, aunque los comandos aceptan otro año.
- Una tarea climática equivale a un par `destino + año`.
- Open-Meteo se ejecuta con un máximo de 3 solicitudes concurrentes y un inicio cada 0,5 segundos. Ante un `429`, todas las tareas comparten la pausa indicada por el servidor.
- Nominatim se ejecuta secuencialmente, con un `User-Agent` identificable y una espera mínima de un segundo.
- Los fines de semana largos son bloques de al menos 3 días no laborables consecutivos que incluyen algún feriado.
- Los promedios históricos se calculan usando el mismo mes y día del fin de semana objetivo a lo largo de los diez años.
- Los archivos JSON se escriben de forma atómica mediante un temporal y reemplazo.
- Cabo Polonio conserva sus coordenadas para clima, pero su acceso vial se mide hasta Barra de Valizas; ese punto está declarado como `punto_ruta` en la configuración porque el destino no es enrutable en auto por OpenRouteService.

### Fórmula vigente

Variables del componente climático:

- temperatura aparente máxima: 30%;
- temperatura aparente mínima: 20%;
- suma de precipitación: 35%;
- horas de precipitación: 15%.

Composición final:

```text
puntaje final = clima × 0.80 + acceso × 0.15 + duración × 0.05
```

El código fuente de verdad para los pesos y funciones de puntuación está en `src/index.py`. Si se modifica la fórmula, actualizar en el mismo cambio `INDICE.md`, `README.md` y este archivo.

## Flujo de datos

```text
config/ubicaciones.json
          │
          ├── Nominatim ───────────────> data/raw/geocoding.json
          │                                  │
          │                                  ├── Open-Meteo
          │                                  │      └── data/raw/weather/<destino>/<año>.json
          │                                  │
          │                                  └── OpenRouteService + ORS_API_KEY
          │                                         └── data/raw/routes.json
          │
          └── Nager.Date ───────────────> data/raw/holidays/<año>.json

weather + routes + holidays ────────────> src/index.py
                                             └── data/processed/ranking_<año>.json
```

## Responsabilidad de cada módulo

- `src/cache.py`: utilidades genéricas para cargar JSON opcional y guardarlo atómicamente.
- `src/geocoding.py`: resuelve coordenadas con Nominatim, valida que pertenezcan a Uruguay y conserva resultados parciales.
- `src/weather.py`: descarga y valida datos diarios de Open-Meteo. Contiene las versiones síncrona y asíncrona.
- `src/holidays.py`: descarga feriados de Nager.Date y detecta fines de semana largos.
- `src/routes.py`: consulta OpenRouteService y convierte metros/segundos a kilómetros/minutos.
- `src/index.py`: calcula promedios históricos, componentes del puntaje, rankings y conclusiones.
- `src/main.py`: CLI unificada y orden del pipeline.

## Estado verificado al 13 de septiembre de 2026

### Implementado

- CLI con comandos `geocoding`, `clima`, `feriados`, `rutas`, `ranking` y `pipeline`.
- Coordenadas de Montevideo y de los 15 destinos: 16 ubicaciones cacheadas.
- Recolector climático síncrono.
- Recolector climático asíncrono con sesión compartida de `aiohttp`, semáforo de 3, limitador de 2 inicios por segundo, pausa global ante `429`, reintentos y progreso por tarea completada.
- Validación de 365/366 días y de las cuatro variables requeridas.
- Recuperación automática ante cachés climáticas o de feriados inválidas.
- Histórico climático completo: 15 destinos × 10 años (2015–2024), 150 archivos y 54.795 registros diarios.
- Feriados de Uruguay de 2026 cacheados: 15 entradas; el código detecta 8 bloques largos con los datos actuales de Nager.Date.
- Cliente de OpenRouteService y 15 rutas cacheadas. Cabo Polonio usa Barra de Valizas como acceso vehicular alternativo, y la caché lo registra explícitamente.
- Ranking de 2026 generado: 120 combinaciones. La primera es Piriápolis, 2026-04-02 a 2026-04-05, con 87,35 puntos.
- La conclusión comparativa detectada es que Termas del Daymán baja 13 puestos en el finde del 2026-05-16 al incorporar el tiempo de viaje.
- Pipeline completo con caché verificado en 0,17 segundos en este equipo.
- Dependencias declaradas y bloqueadas con `uv`.

### Pendiente de documentación y calidad

1. Contrastar manualmente resultados extremos o inesperados del ranking.
2. Actualizar `INDICE.md` para explicar también los pesos finales 80/15/5 y las funciones que convierten cada variable a 0–100.
3. Completar `BITACORA.md` con tiempos síncrono/asíncrono, decisiones, problemas y evidencia de la segunda ejecución con caché.
4. Ampliar las pruebas automatizadas: `tests/test_weather.py` cubre el limitador, pero faltan los demás módulos.

El pipeline de datos está completo. No dar por cerrada la entrega académica hasta terminar la documentación y las pruebas pendientes.

## Comandos canónicos

```bash
uv sync
uv run python src/main.py geocoding
uv run python src/main.py clima --scope sample --mode sync
uv run python src/main.py clima --scope sample --mode async
uv run python src/main.py clima --scope full --mode async
uv run python src/main.py feriados --year 2026
uv run python src/main.py rutas
uv run python src/main.py ranking --year 2026 --top 10
uv run python src/main.py pipeline --year 2026 --top 10
uv run python -m py_compile src/*.py
```

Preferir `src/main.py` como interfaz pública. Los módulos individuales también tienen CLI, pero `main.py` mantiene rutas absolutas basadas en la raíz y centraliza el flujo.

## Invariantes que se deben preservar

- Nunca paralelizar Nominatim ni superar una solicitud por segundo.
- No crear una sesión `aiohttp` por tarea; compartir una sola sesión dentro del recolector.
- No eliminar el limitador global de Open-Meteo: el semáforo limita concurrencia, pero el limitador evita ráfagas y reintentos simultáneos que provocan `429`.
- No eliminar cachés válidas ni usar `--force` como comportamiento predeterminado.
- Guardar cada resultado exitoso inmediatamente para permitir reanudar.
- Validar las respuestas antes de guardarlas o consumirlas.
- Mantener `latitud` y `longitud` en geocoding, pero enviar a OpenRouteService el orden `[longitud, latitud]`.
- No incluir claves, tokens ni contenido de `.env` en código, logs, documentación o commits.
- Mantener `uv.lock` versionado junto con cambios de dependencias.
- Conservar nombres de usuario, mensajes y documentación en español, de acuerdo con el estilo actual.
- Preservar cambios no relacionados que ya existan en el árbol de trabajo.

## Caché y datos versionados

La caché es parte del diseño, no un residuo temporal. Permite demostrar reanudación, reproducibilidad y la ejecución rápida posterior.

- `data/raw/geocoding.json`: una entrada por origen/destino.
- `data/raw/weather/<destino>/<año>.json`: un archivo independiente por tarea climática.
- `data/raw/holidays/<año>.json`: feriados por año objetivo.
- `data/raw/routes.json`: una entrada por destino; se actualiza después de cada ruta exitosa.
- `data/processed/ranking_<año>.json`: resultado derivado y regenerable.

Antes de regenerar o borrar datos, entender por qué se hace y preferir una reanudación normal. Un archivo de clima válido debe incluir todos los días del año y todas las variables de `DAILY_VARIABLES`.

## Criterios de finalización

El proyecto puede considerarse listo para entregar cuando:

- `uv sync` funciona desde un clon limpio;
- el pipeline completo termina con la configuración documentada;
- hay 15 destinos × 10 años de clima y más de 5.000 registros;
- existen las 15 rutas reales obtenidas con la API autenticada;
- existe un ranking final legible y su JSON procesado;
- repetir el pipeline reutiliza la caché y tarda menos de 5 segundos;
- la comparación síncrona/asíncrona y sus tiempos están documentados;
- la bitácora y la explicación del índice coinciden con el código;
- las credenciales no aparecen en Git;
- se ejecutaron verificaciones automáticas y una inspección razonable de los resultados.

## Notas para futuros cambios

- No interpretar los promedios históricos como un pronóstico. El resultado es una estimación comparativa.
- Si cambia la ventana histórica, actualizar tanto la recolección como `ANIOS_HISTORICOS` en `src/index.py`.
- Si se agregan destinos, geocodificar, descargar clima y obtener rutas antes de recalcular.
- Si una fuente cambia su formato, adaptar primero la validación y conservar compatibilidad con las cachés existentes cuando sea razonable.
- `TODO_CACHE.md`, si todavía existe, puede estar desactualizado: el código actual ya recupera cachés inválidas. Verificar contra la implementación antes de usarlo como lista de pendientes.
