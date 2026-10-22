# Guía de caché, APIs y asincronía

Esta guía resume cómo el proyecto **Índice de Escapada** usa la caché, maneja las APIs y aplica asincronía.

## Qué pasa si se corta la red durante la corrida

## La idea principal

El programa guarda cada respuesta correcta inmediatamente. Por eso, si la conexión se corta, no se pierde todo el trabajo: se conserva lo que ya fue descargado y solamente queda pendiente lo que no llegó a completarse.

La caché no sirve solamente para recuperarse de errores de red. También evita repetir llamadas a las APIs en futuras corridas. Una vez que los datos están guardados, el programa puede reutilizarlos directamente desde los archivos locales, reduciendo mucho el tiempo de ejecución y la cantidad de solicitudes externas.

> **Cada archivo representa una unidad independiente y recuperable.**

Esto permite que el proyecto sea más rápido, reproducible y resistente a interrupciones.

## Qué ocurre con el clima

Cada combinación de destino y año se guarda en un archivo independiente:

```text
data/raw/weather/<destino>/<año>.json
```

Por ejemplo:

```text
data/raw/weather/carmelo/2019.json
```

Si la red se corta después de completar 80 de las 150 tareas:

- esas 80 respuestas quedan guardadas;
- las tareas que estaban esperando pueden reintentarse;
- las tareas que no logren completarse quedan pendientes;
- el programa termina mostrando un error si todavía hay tareas fallidas.

El programa no borra los archivos que ya estaban correctos.

## Qué ocurre con los reintentos

Cuando Open-Meteo devuelve un error de red o un límite temporal, el programa espera y vuelve a intentar la solicitud. Actualmente utiliza:

- varios intentos por tarea;
- espera progresiva;
- una pequeña variación aleatoria para evitar que todas las tareas reintenten al mismo tiempo;
- una pausa global cuando el servicio responde `429 Too Many Requests`.

Si la conexión no vuelve antes de terminar los reintentos, esa tarea se informa como fallida, pero las demás tareas pueden seguir guardándose.

## Qué tenés que hacer cuando vuelva internet

Volvé a ejecutar el mismo comando, sin `--force`:

```bash
uv run python src/main.py pipeline --year 2026 --top 10
```

El programa revisa la caché y:

- salta los archivos válidos que ya existen;
- vuelve a descargar solamente los datos faltantes;
- continúa también con las rutas que todavía no estén guardadas;
- genera el ranking cuando todas las entradas necesarias están disponibles.

## Por qué no hay que usar `--force`

`--force` le indica al programa que ignore la caché y vuelva a descargar los datos, incluso si ya existen.

Por eso, después de un corte de red, no conviene usarlo. El comando correcto para reanudar es:

```bash
uv run python src/main.py pipeline --year 2026 --top 10
```

## ¿Puede quedar un archivo roto?

No debería. Los JSON se escriben primero en un archivo temporal y luego se reemplaza el archivo definitivo. De esa forma, si el programa se interrumpe justo durante el guardado, no se conserva una respuesta incompleta como si fuera válida.

## Qué pasa en cada etapa

| Etapa | Qué se guarda | Qué ocurre si falla la red |
|---|---|---|
| Geocoding | Cada ubicación en `geocoding.json` | Se conservan las ubicaciones ya resueltas |
| Clima | Un JSON por destino y año | Se reanudan solamente las tareas faltantes |
| Feriados | Un JSON por año | Se vuelve a consultar ese año |
| Rutas | Cada ruta dentro de `routes.json` | Se conservan las rutas ya calculadas |
| Ranking | Un JSON procesado al final | Se ejecuta cuando están todos los datos necesarios |

## Ejemplo sencillo

Supongamos que empezás una corrida completa y se corta la red cuando ya se guardaron 120 archivos climáticos.

Al volver internet, repetís:

```bash
uv run python src/main.py pipeline --year 2026 --top 10
```

El programa no repite esas 120 descargas. Busca solamente los 30 archivos que faltan, completa las rutas o feriados pendientes y luego construye el ranking.

## Resumen

> **Cada archivo representa una unidad independiente y recuperable: la caché permite continuar después de un corte de red y también hace que las corridas posteriores sean mucho más rápidas, porque reutilizan los datos guardados en lugar de volver a consultar las APIs.**

## Verificación de las respuestas de las APIs

Antes de usar una respuesta, cada módulo comprueba que la API haya respondido correctamente mediante el código HTTP (`raise_for_status()`). Si ocurre un error transitorio, como `429 Too Many Requests` o un error del servidor, la solicitud se reintenta; si el problema persiste, se informa como fallida.

También se valida el contenido recibido:

- **Nominatim:** que exista un resultado de Uruguay con coordenadas razonables.
- **Open-Meteo:** que estén todos los datos diarios esperados del año.
- **Feriados:** que la respuesta contenga una lista válida de fechas.
- **OpenRouteService:** que exista una ruta con distancia y duración válidas.

Así se evita guardar respuestas incompletas o tratar un error de la API como si fueran datos correctos.

## Decisión sobre asincronía y límites

No todas las APIs deben ejecutarse de forma asíncrona. El clima sí se paraleliza porque reúne muchas consultas independientes y es la etapa más lenta. Geocoding se mantiene secuencial porque Nominatim limita el uso a una solicitud por segundo. Feriados y rutas también se mantienen secuenciales porque implican pocas consultas, usan caché y no son el cuello de botella del programa. Esta decisión cumple la consigna: paralelizar la parte costosa y justificar qué partes conviene no paralelizar.

## Mejora medida con asincronía

En la muestra de 3 destinos × 3 años, la recolección climática tardó **9,22 segundos en modo síncrono** y **1,30 segundos en modo asíncrono**. Esto representa una reducción de **7,92 segundos**, aproximadamente un **86 % menos de tiempo**.
