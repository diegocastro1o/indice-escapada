# Criterio de diseño

## Objetivo

El objetivo del proyecto es comparar distintos fines de semana largos y elegir cuál es la mejor opción para hacer una escapada desde Montevideo.

Para tomar la decisión usamos datos climáticos históricos, los feriados de 2026 y la facilidad para llegar a cada destino por carretera.

No estamos tratando de adivinar cómo va a estar el clima en 2026. Para cada fin de semana largo, miramos cómo estuvo el clima en esas mismas fechas entre 2015 y 2024. Esto sirve como referencia para comparar los destinos.

Cada opción que analiza el programa está formada por un destino y un fin de semana largo. El sistema compara todas las combinaciones y recomienda la que obtiene el puntaje más alto.

---

## Destinos a comparar

El punto de partida para todas las rutas es **Montevideo**.

Los destinos que se van a comparar son:

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

Todos los destinos se comparan usando los mismos criterios y los mismos pesos. De esta forma, la comparación es más justa.

---

## Fuentes de datos

Para armar el índice se usan cuatro fuentes:

| Fuente | Para qué se usa |
| --- | --- |
| Nominatim | Obtener las coordenadas de Montevideo y de cada destino. |
| Open-Meteo | Obtener datos climáticos históricos entre 2015 y 2024. |
| Nager.Date | Obtener los feriados de Uruguay y detectar los fines de semana largos de 2026. |
| OpenRouteService | Obtener la distancia y el tiempo de viaje por carretera desde Montevideo hasta cada destino. |

---

## Variables climáticas utilizadas

Para comparar el clima se utilizan las siguientes variables:

| Variable | Qué representa | Cuándo es mejor |
| --- | --- | --- |
| Temperatura aparente máxima | Cómo se siente el calor durante el día. | Cuando la temperatura es agradable y no hay calor extremo. |
| Temperatura aparente mínima | Cómo se siente el frío durante la noche o temprano. | Cuando no hace demasiado frío. |
| Suma de precipitación | Cantidad total de precipitación registrada en los datos históricos. | Cuanto menor sea, mejor. |
| Horas de precipitación | Cantidad de horas en las que hubo precipitación. | Cuantas menos horas haya, mejor. |

Estas variables se obtienen de Open-Meteo. Para cada fin de semana largo se calcula un promedio usando los datos de las mismas fechas entre 2015 y 2024.

---

## Pesos del componente climático

Dentro del puntaje climático, cada variable tiene un peso diferente:

| Variable | Peso |
| --- | ---: |
| Temperatura aparente máxima | 30 % |
| Temperatura aparente mínima | 20 % |
| Suma de precipitación | 35 % |
| Horas de precipitación | 15 % |
| **Total** | **100 %** |

Le damos más importancia a la precipitación porque mucha lluvia puede complicar el viaje y las actividades al aire libre.

La temperatura también es importante, porque no es cómodo viajar si hace demasiado calor o demasiado frío.

Las horas de precipitación sirven para diferenciar entre una lluvia corta y un día con lluvia durante muchas horas.

---

## Rutas, accesibilidad y duración del viaje

El clima no es lo único que importa para una escapada. También tenemos en cuenta qué tan fácil y rápido es llegar desde Montevideo.

La información de rutas se obtiene con OpenRouteService.

| Parte del índice | Peso |
| --- | ---: |
| Clima | 80 % |
| Accesibilidad por carretera | 15 % |
| Duración del viaje | 5 % |
| **Total** | **100 %** |

La accesibilidad se basa en la distancia por carretera. La duración se basa en el tiempo estimado del viaje.

En los dos casos, cuanto menor sea la distancia o el tiempo necesario para llegar, mejor será el puntaje.

---

## Reglas para asignar puntajes climáticos

Cada variable climática recibe un puntaje entre 0 y 100.

Cuanto más cerca esté un valor de lo que consideramos cómodo para una escapada, mayor será su puntaje.

Los pesos no cambian. Lo que cambia es el puntaje de cada variable según los datos históricos de cada destino y cada fin de semana largo.

Por ejemplo, si la temperatura aparente máxima obtiene 80 puntos y su peso dentro del clima es 30 %, aporta:

```text
80 × 0.30 = 24 puntos
```

### Temperatura aparente máxima — peso: 30 %

Se considera que una temperatura máxima agradable para realizar actividades al aire libre es de aproximadamente **25 °C**.

| Temperatura aparente máxima | Puntaje |
| --- | ---: |
| 25 °C | 100 |
| Entre 23 °C y 27 °C | Entre 80 y 100 |
| Entre 20 °C y 30 °C | Entre 50 y 80 |
| Menor a 15 °C o mayor a 35 °C | 0 |

El puntaje baja a medida que la temperatura se aleja de los 25 °C, ya sea por frío o por calor excesivo.

### Temperatura aparente mínima — peso: 20 %

Se considera cómoda una temperatura mínima de entre **15 °C y 20 °C**.

| Temperatura aparente mínima | Puntaje |
| --- | ---: |
| Entre 15 °C y 20 °C | 100 |
| Entre 10 °C y 14 °C | Entre 50 y 80 |
| Menor a 5 °C | 0 |

El puntaje baja principalmente cuando la temperatura mínima es muy baja.

### Suma de precipitación — peso: 35 %

Para una escapada, lo ideal es que no haya lluvia.

| Precipitación total durante el fin de semana | Puntaje |
| --- | ---: |
| 0 mm | 100 |
| Entre 1 mm y 3 mm | Entre 70 y 90 |
| Entre 4 mm y 10 mm | Entre 20 y 60 |
| Más de 10 mm | 0 |

Cuanta más precipitación haya en el promedio histórico, menor será el puntaje.

### Horas de precipitación — peso: 15 %

También se considera la duración de la lluvia.

| Horas de precipitación | Puntaje |
| --- | ---: |
| 0 horas | 100 |
| Entre 1 y 2 horas | Entre 70 y 90 |
| Entre 3 y 5 horas | Entre 30 y 60 |
| Más de 6 horas | 0 |

Cuantas menos horas de precipitación haya, mayor será el puntaje.

---

## Cálculo del puntaje final

Primero se calcula el puntaje del clima:

```text
puntaje del clima =
    (puntaje de temperatura aparente máxima × 0.30) +
    (puntaje de temperatura aparente mínima × 0.20) +
    (puntaje de suma de precipitación × 0.35) +
    (puntaje de horas de precipitación × 0.15)
```

Después se calcula el puntaje final:

```text
puntaje final =
    (puntaje del clima × 0.80) +
    (puntaje de accesibilidad × 0.15) +
    (puntaje de duración × 0.05)
```

El destino y el fin de semana largo con el puntaje más alto serán los recomendados por el programa.

---

## Ejemplo

Un destino puede tener muy buen clima histórico, pero quedar por debajo de otro si está mucho más lejos de Montevideo o lleva muchas horas de viaje.

Por eso, el resultado final no depende solamente del clima. También depende de qué tan fácil y rápido sea llegar al destino.

---

## Posibles cambios

Los pesos elegidos representan una escapada general, donde importa mucho tener buen clima, pero también llegar sin que el viaje sea demasiado largo.

Si se cambian los pesos, el resultado puede cambiar. Por ejemplo, un destino lejano puede mejorar mucho si se le da más importancia al clima y menos importancia al tiempo de viaje.

Por eso, el resultado no es una verdad absoluta. Es una recomendación basada en los criterios y los pesos definidos para este proyecto.