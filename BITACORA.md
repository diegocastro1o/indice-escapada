# Bitácora del proyecto — Índice de Escapada

## Objetivo

El proyecto busca responder:

> **¿Cuál es el mejor fin de semana largo del año para escaparse en Uruguay y a qué destino conviene viajar?**

El índice combina clima histórico, feriados y tiempo de viaje por carretera desde Montevideo. No es un pronóstico: compara el comportamiento histórico de las mismas fechas entre 2015 y 2024.

## Fuentes de datos

| Fuente | Uso |
|---|---|
| Nominatim | Coordenadas de Montevideo y los destinos |
| Open-Meteo | Clima histórico diario |
| Nager.Date | Feriados de Uruguay |
| OpenRouteService | Distancia y duración de las rutas; el puntaje actual usa la duración |

Inicialmente consideramos Foursquare para obtener lugares de interés, pero la descartamos porque el registro requería asociar un método de pago y no era indispensable para responder la pregunta principal.

## Organización por hitos

El desarrollo se dividió en tres hitos: primero obtener datos confiables, luego comparar la ejecución secuencial y asíncrona, y finalmente escalar el pipeline completo con caché y reanudación.

---

## Hito 1 — Datos, geocoding y caché

### Objetivo

Construir la base del proyecto y descargar una primera muestra de datos.

Creamos el repositorio Git, usamos PyCharm y organizamos el proyecto así:

```text
indice-escapada/
├── config/        # configuración de ubicaciones
├── data/raw/      # datos obtenidos de las APIs
├── data/processed/# resultados derivados
├── src/           # módulos del programa
├── tests/
├── pyproject.toml
└── uv.lock
```

El origen es Montevideo y se definieron 15 destinos: Colonia del Sacramento, Carmelo, Piriápolis, Punta del Este, José Ignacio, La Paloma, Cabo Polonio, Punta del Diablo, Aguas Dulces, Minas, Villa Serrana, Termas del Daymán, Salto, Mercedes y Tacuarembó.

### Geocoding

Usamos Nominatim para convertir consultas como:

```text
Minas, Lavalleja, Uruguay
```

en coordenadas. Las consultas incluyen departamento y país para evitar ambigüedades. Se respetan las restricciones del servicio: solicitudes secuenciales, intervalo mínimo de un segundo, `User-Agent` identificable, validación de Uruguay y guardado incremental.

Las coordenadas se guardan en `data/raw/geocoding.json`, de modo que no sea necesario consultar nuevamente una localidad ya resuelta.

### Primera muestra

Comenzamos con Colonia del Sacramento, Carmelo y Piriápolis para 2015, 2016 y 2017: nueve tareas en total. Las variables climáticas fueron temperatura aparente máxima, temperatura aparente mínima, suma de precipitación y horas de precipitación.

La validación detecta correctamente los años bisiestos: 2016 tiene 366 registros y los demás años de la muestra tienen 365.

### Resultado

Quedaron funcionando la configuración de destinos, el geocoding, la caché y la descarga básica de clima.

---

## Hito 2 — Paralelización y comparación de tiempos

### Objetivo

Comparar una implementación síncrona con una asíncrona y determinar qué partes se podían paralelizar.

Las consultas independientes a Open-Meteo se ejecutan con una sesión compartida de `aiohttp`, tareas separadas, semáforo, caché y progreso con `asyncio.as_completed()`.

Nominatim no se paraleliza: su política pública exige limitar estrictamente la frecuencia de consultas.

### Tiempos de la muestra

| Modo | Alcance | Tiempo |
|---|---|---:|
| Síncrono | 3 destinos × 3 años | 9,22 s |
| Asíncrono | 3 destinos × 3 años | 1,30 s |

La asincronía reduce el tiempo de espera cuando el cuello de botella es la comunicación con una API externa.

Durante las pruebas aparecieron respuestas `429 Too Many Requests`. El semáforo inicial limitaba la concurrencia, pero no la velocidad total de inicio de solicitudes.

---

## Hito 3 — Escalamiento, pipeline y reanudación

### Objetivo

Escalar a 15 destinos × 10 años y permitir que una ejecución interrumpida continúe desde la caché.

```text
15 destinos × 10 años (2015–2024) = 150 tareas
Total: 54.795 registros diarios
```

Guardamos cada tarea en `data/raw/weather/<destino>/<año>.json`. El comando principal es:

```bash
uv run python src/main.py pipeline --year 2026 --top 10
```

El pipeline ejecuta geocoding, clima, feriados, fines de semana largos, rutas y ranking. Cada respuesta válida se guarda inmediatamente; por eso, repetir el comando sin `--force` reanuda solamente las tareas faltantes.

### Estado de los datos

| Recurso | Cantidad |
|---|---:|
| Archivos climáticos | 150 |
| Registros climáticos diarios | 54.795 |
| Rutas desde Montevideo | 15 |
| Feriados de 2026 | 15 |
| Fines de semana largos | 8 |
| Combinaciones del ranking | 120 |

El resultado queda en `data/processed/ranking_2026.json`.

### OpenRouteService y Cabo Polonio

OpenRouteService fue la fuente autenticada y la clave se guarda localmente en `.env`, que está excluido de Git.

Cabo Polonio no tiene una conexión apta para automóviles en la red de OpenRouteService. Sus coordenadas se mantienen para el clima, pero la ruta se calcula hasta Barra de Valizas, definida como acceso vehicular alternativo en `config/ubicaciones.json`. La caché registra esta excepción.

---

## Corrección del problema `Too Many Requests`

En la corrida completa Open-Meteo respondió `429` porque varias tareas iniciaban solicitudes prácticamente al mismo tiempo. La solución combinó concurrencia y ritmo:

- máximo de 3 solicitudes simultáneas;
- máximo de 2 inicios por segundo;
- pausa global cuando aparece un `429`;
- respeto de `Retry-After`;
- espera progresiva con variación aleatoria;
- hasta cinco intentos por tarea.

Así se mantiene la asincronía sin saturar la API. Las tareas cacheadas no generan solicitudes.

Se agregaron pruebas del espaciado y de la pausa global:

```bash
uv run python -m unittest discover -s tests
```

---

## Resultado final del índice

Para 2026 se evaluaron 120 combinaciones. La mejor fue:

| Puesto | Destino | Fecha | Puntaje |
|---:|---|---|---:|
| 1 | Piriápolis | 2 al 5 de abril de 2026 | 87,35 |

La conclusión más relevante fue:

> Termas del Daymán baja 13 puestos en el fin de semana del 16 de mayo cuando se incorpora el tiempo de viaje: pasa del puesto 2 por clima al puesto 15 final.

Esto muestra que el destino con mejor clima histórico no necesariamente es la mejor escapada cuando también se considera el tiempo de viaje desde Montevideo.

## Estado del proyecto

### Completado

- configuración de 15 destinos y Montevideo;
- geocoding y caché;
- recolectores síncrono y asíncrono;
- limitador contra `429` y reanudación;
- feriados y fines de semana largos;
- rutas autenticadas;
- ranking final de 2026;
- documentación técnica y pruebas básicas.

### Pendiente

- ampliar la cobertura de pruebas;
- revisar manualmente resultados extremos;
- mantener sincronizados esta bitácora e `INDICE.md` si cambian pesos o fórmulas;
- preparar la presentación o informe final.

## Comandos principales

```bash
uv sync
uv run python src/main.py pipeline --year 2026 --top 10
uv run python src/main.py clima --scope full --mode async
uv run python -m unittest discover -s tests
uv run python -m py_compile src/*.py
```

## Aprendizajes
1. El caché nos permitió reanudar y evitar repetir llamadas costosas.
2. Paralelizar requiere controlar tanto la concurrencia como la frecuencia.
3. Las restricciones de una API forman parte del diseño técnico.
4. Una API autenticada puede aportar una dimensión adicional al análisis.
5. Un índice debe documentar sus pesos, transformaciones y excepciones.
6. Incorporar el tiempo de viaje puede cambiar sustancialmente la recomendación climática.
