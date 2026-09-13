# Índice de Escapada

Proyecto académico que recomienda **qué destino de Uruguay conviene visitar en cada fin de semana largo**. La recomendación combina clima histórico, duración del viaje desde Montevideo y cantidad de días disponibles.

El programa obtiene datos de cuatro servicios, los guarda en caché y construye un ranking reproducible para el año elegido.

## Estado actual

La estructura y los módulos del pipeline ya están implementados. Actualmente hay:

- 15 destinos configurados y sus coordenadas cacheadas, además de Montevideo.
- Una muestra climática de 3 destinos × 3 años (2015–2017), con 3.288 registros diarios.
- Recolección climática síncrona y asíncrona, con un máximo de 5 solicitudes simultáneas.
- Feriados de Uruguay de 2026 cacheados y detección de fines de semana largos.
- Recolección de rutas y cálculo del ranking implementados.

Para completar una ejecución final todavía se necesita configurar `ORS_API_KEY`, descargar las rutas y recolectar el histórico completo de clima: 15 destinos × 10 años, 54.795 registros diarios. Después de eso se podrá generar el ranking final.

## Fuentes de datos

| Fuente | Uso | Autenticación | Paralelización |
|---|---|---|---|
| [Nominatim](https://nominatim.org/) | Coordenadas de origen y destinos | No | No; se respeta 1 solicitud por segundo |
| [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) | Clima diario histórico | No | Sí; máximo 5 solicitudes simultáneas |
| [Nager.Date](https://date.nager.at/) | Feriados de Uruguay | No | No es necesaria |
| [OpenRouteService](https://openrouteservice.org/) | Distancia y duración en auto desde Montevideo | `ORS_API_KEY` | Actualmente secuencial |

## Variables y criterio del índice

Para cada destino y fin de semana largo se toman las mismas fechas de calendario en los años 2015–2024 y se calculan promedios históricos de:

- temperatura aparente máxima;
- temperatura aparente mínima;
- suma de precipitación;
- horas de precipitación.

El puntaje climático pondera esas variables así:

| Componente climático | Peso |
|---|---:|
| Temperatura aparente máxima | 30% |
| Temperatura aparente mínima | 20% |
| Suma de precipitación | 35% |
| Horas de precipitación | 15% |

El resultado final combina:

```text
puntaje final = clima × 0.80 + acceso × 0.15 + duración del fin de semana × 0.05
```

El acceso recibe mejor puntuación cuanto menor sea el tiempo de viaje desde Montevideo. La duración premia los fines de semana con más días. Los detalles del criterio climático están en [`INDICE.md`](INDICE.md).

## Requisitos

- Python 3.12 o posterior.
- [`uv`](https://docs.astral.sh/uv/) para instalar y ejecutar el proyecto.
- Una clave de OpenRouteService para descargar las rutas.
- Conexión a internet para la primera ejecución de cada fuente.

## Instalación

```bash
git clone https://github.com/diegocastro1o/indice-escapada.git
cd indice-escapada
uv sync
```

`uv sync` crea el entorno virtual e instala las versiones registradas en `uv.lock`.

## Configuración de OpenRouteService

1. Crear una cuenta y una API key en OpenRouteService.
2. Copiar el archivo de ejemplo:

```bash
cp .env.example .env
```

3. Completar `.env`:

```dotenv
ORS_API_KEY=tu_clave_aqui
```

No se debe subir `.env` al repositorio. `.env.example` sí se versiona porque solamente documenta el nombre de la variable.

## Uso rápido

Con la clave configurada, el pipeline completo se ejecuta con:

```bash
uv run python src/main.py pipeline --year 2026 --top 10
```

La primera ejecución puede tardar porque descarga los datos faltantes. Las ejecuciones posteriores reutilizan la caché; para la entrega se debe comprobar que la segunda ejecución completa tarde menos de 5 segundos.

También se puede ejecutar como módulo:

```bash
uv run python -m src.main pipeline --year 2026 --top 10
```

## Comandos disponibles

Para ver la ayuda general:

```bash
uv run python src/main.py --help
```

### 1. Geocodificar origen y destinos

```bash
uv run python src/main.py geocoding
```

Lee `config/ubicaciones.json`, consulta Nominatim solamente para las ubicaciones que falten y actualiza `data/raw/geocoding.json`. Este paso es deliberadamente secuencial porque la política pública de Nominatim exige limitar las solicitudes.

### 2. Descargar clima histórico

Prueba rápida con 3 destinos × 3 años:

```bash
uv run python src/main.py clima --scope sample --mode async
```

Recolección completa de 15 destinos × 10 años:

```bash
uv run python src/main.py clima --scope full --mode async
```

Comparación de tiempos síncrono/asíncrono sobre la muestra:

```bash
uv run python src/main.py clima --scope sample --mode sync --force
uv run python src/main.py clima --scope sample --mode async --force
```

`--force` ignora la caché y vuelve a descargar. Debe usarse solamente cuando se quiere medir tiempos de red o reemplazar datos existentes; no es necesario en el uso habitual.

### 3. Descargar feriados y detectar fines de semana largos

```bash
uv run python src/main.py feriados --year 2026
```

Se consideran bloques de tres o más días no laborables consecutivos que contienen al menos un feriado.

### 4. Calcular las rutas

```bash
uv run python src/main.py rutas
```

Requiere `ORS_API_KEY`. Calcula distancia y duración en auto desde Montevideo a cada destino y guarda el resultado en `data/raw/routes.json`.

### 5. Construir el ranking

```bash
uv run python src/main.py ranking --year 2026 --top 10
```

Este comando no descarga el histórico que falta. Requiere que ya existan:

- los 150 archivos climáticos válidos;
- los feriados del año elegido;
- las 15 rutas.

Muestra el ranking en la terminal y escribe `data/processed/ranking_2026.json`.

### 6. Ejecutar todo el pipeline

```bash
uv run python src/main.py pipeline --year 2026 --top 10
```

Ejecuta, en orden: geocoding, clima completo asíncrono, feriados, rutas y ranking. Cada etapa reutiliza lo que ya esté cacheado.

## Caché y reanudación

Los datos se guardan inmediatamente después de cada respuesta válida. Si una ejecución se interrumpe, al repetir el comando se procesan solamente los elementos faltantes.

```text
data/
├── raw/
│   ├── geocoding.json
│   ├── holidays/
│   │   └── 2026.json
│   ├── routes.json
│   └── weather/
│       └── <destino>/
│           └── <año>.json
└── processed/
    └── ranking_<año>.json
```

Los archivos de `data/raw/` forman parte de la caché reproducible del proyecto y pueden versionarse. No contienen credenciales. No conviene borrarlos salvo que se quiera forzar una descarga completa.

Si una caché climática o de feriados contiene JSON inválido o datos incompletos, el programa la detecta y vuelve a descargarla.

## Estructura del proyecto

```text
indice-escapada/
├── config/
│   └── ubicaciones.json     # origen y 15 destinos
├── data/
│   ├── raw/                 # respuestas cacheadas de las APIs
│   └── processed/           # ranking y resultados derivados
├── src/
│   ├── cache.py             # lectura y escritura atómica de JSON
│   ├── geocoding.py         # coordenadas mediante Nominatim
│   ├── holidays.py          # feriados y fines de semana largos
│   ├── index.py             # cálculo del índice y conclusiones
│   ├── main.py              # interfaz de línea de comandos y pipeline
│   ├── routes.py            # rutas mediante OpenRouteService
│   └── weather.py           # clima síncrono y asíncrono
├── tests/                   # pruebas automatizadas (pendientes)
├── .env.example
├── AGENTS.md                # contexto técnico para agentes/IA
├── BITACORA.md              # registro académico de decisiones
├── INDICE.md                # criterio de diseño del índice
├── pyproject.toml
└── uv.lock
```

## Agregar o modificar destinos

Los destinos se definen en `config/ubicaciones.json`. Cada entrada necesita:

```json
{
  "id": "nombre_sin_espacios",
  "nombre": "Nombre para mostrar",
  "consulta_nominatim": "Localidad, Departamento, Uruguay"
}
```

Después de editar la configuración, ejecutar nuevamente `geocoding`, `clima --scope full`, `rutas` y `ranking`. Las consultas de Nominatim deben ser específicas para evitar localidades homónimas.

## Verificación del código

Actualmente no hay una suite de pruebas automatizadas completa. Como control básico se puede verificar la sintaxis y la interfaz:

```bash
uv run python -m py_compile src/*.py
uv run python src/main.py --help
```

Antes de entregar también conviene comprobar:

- que existan 150 archivos de clima;
- que el total supere 5.000 registros diarios;
- que `routes.json` contenga 15 rutas;
- que una segunda ejecución use caché y tarde menos de 5 segundos;
- que `ranking_<año>.json` se genere sin errores;
- que `BITACORA.md` e `INDICE.md` reflejen las decisiones finales.

## Problemas frecuentes

### `Falta ORS_API_KEY`

Crear `.env` desde `.env.example`, completar la clave y volver a ejecutar `rutas`.

### Faltan archivos climáticos al construir el ranking

Ejecutar:

```bash
uv run python src/main.py clima --scope full --mode async
```

### Respuestas `429` o errores temporales de red

Los recolectores tienen reintentos y espera progresiva. Si el servicio sigue limitando solicitudes, esperar y repetir sin `--force`; las respuestas ya guardadas se reutilizarán.

### Un año tiene 366 registros

Es correcto para los años bisiestos, por ejemplo 2016. La validación calcula automáticamente si espera 365 o 366 días.

### Se interrumpió una descarga

Ejecutar el mismo comando otra vez, sin borrar archivos y sin `--force`. El programa continúa desde la caché existente.

## Archivos que se versionan

Se deben subir `pyproject.toml` y `uv.lock` para que todo el equipo use las mismas dependencias. También se puede subir la caché de `data/raw/`, ya que permite reproducir resultados y acelerar la segunda ejecución.

No se deben versionar:

- `.env` ni otras credenciales;
- `.venv/`;
- `.idea/`;
- archivos temporales de Python.

## Alcance académico

El índice es una herramienta comparativa basada en promedios históricos, no un pronóstico meteorológico ni una garantía de las condiciones futuras. Los pesos expresan una decisión de diseño del equipo y deben justificarse en la entrega.
