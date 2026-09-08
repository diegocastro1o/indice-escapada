# Criterio de diseño

## Objetivo

El objetivo del proyecto es comparar distintos fines de semana y elegir cuál es el más conveniente para hacer una escapada.

La decisión se toma según las condiciones climáticas de cada destino. La idea es que el fin de semana elegido tenga un clima más cómodo para viajar y hacer actividades al aire libre.

## Destinos a comparar

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

Cada destino puede tener características diferentes. Por ejemplo, en un destino de playa importa más que haga calor y no llueva, mientras que en una escapada a una ciudad la lluvia puede afectar menos.

## Variables utilizadas

Para comparar los fines de semana decidí usar estas variables meteorológicas:

| Variable | Qué representa | Cuándo es mejor |
|:--|:--|:--|
| Temperatura aparente máxima | Cómo se siente el calor durante el día. | Cuando la temperatura es agradable, sin calor extremo. |
| Temperatura aparente mínima | Cómo se siente el frío durante la noche o temprano. | Cuando no hace demasiado frío. |
| Suma de precipitación | Cantidad total de lluvia esperada. | Cuanto menor sea, mejor. |
| Horas de precipitación | Cantidad de horas en las que puede llover. | Cuantas menos horas llueva, mejor. |

## Pesos de las variables

A cada variable le asigné un peso. Todos los pesos suman 100%.

| Variable | Peso |
|:--|--:|
| Temperatura aparente máxima | 30% |
| Temperatura aparente mínima | 20% |
| Suma de precipitación | 35% |
| Horas de precipitación | 15% |
| **Total** | **100%** |

## Por qué elegí estos pesos

Le dimos más importancia a la suma de precipitación porque mucha lluvia puede complicar el viaje y las actividades al aire libre.

También le dimos bastante importancia a la temperatura aparente máxima y mínima, porque no es agradable viajar si hace demasiado calor o demasiado frío.

Las horas de precipitación tienen un peso menor, pero sirven para diferenciar entre una lluvia corta y un día entero con lluvia.

No usé el código meteorológico porque resume datos que ya estoy teniendo en cuenta con la temperatura y las precipitaciones. Tampoco agregué la suma de lluvia por separado, porque es muy parecida a la suma de precipitación y estaría repitiendo el mismo dato.

## Cálculo del puntaje

Primero, cada dato del clima se transforma en un puntaje entre 0 y 100.

Después, el puntaje final de cada fin de semana se calcula usando los pesos definidos:

```text
puntaje final =
    (temperatura máxima × 0.30) +
    (temperatura mínima × 0.20) +
    (suma de precipitación × 0.35) +
    (horas de precipitación × 0.15)
```

El fin de semana con el puntaje más alto será el recomendado.

## Ejemplo

Si un destino tiene temperaturas agradables y poca lluvia, va a obtener un puntaje alto.

En cambio, si se espera mucha lluvia durante varias horas, su puntaje va a bajar, aunque la temperatura sea buena.

## Posibles cambios

Los pesos pueden cambiar según el tipo de destino.

Por ejemplo:

- Para una escapada de playa, la temperatura máxima y la lluvia pueden tener más peso.
- Para una escapada a una ciudad, la temperatura puede importar menos que la lluvia.
- Para una escapada de invierno, la temperatura mínima puede ser más importante.

Por eso, el resultado no es una verdad absoluta: depende de los destinos elegidos y de las preferencias de la persona que viaja.