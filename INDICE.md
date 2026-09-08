# Cómo elegí el mejor fin de semana para una escapada

## Objetivo

La idea del proyecto es comparar distintos fines de semana y elegir cuál parece mejor para hacer una escapada. Para eso tomé datos del clima, porque pueden cambiar bastante la experiencia del viaje.

## Variables que usé

| Variable | Peso | Por qué la elegí |
|:--|--:|:--|
| Temperatura aparente máxima | 30% | Me dice qué tan caluroso se va a sentir el día. |
| Temperatura aparente mínima | 20% | Sirve para saber cómo va a estar el frío de noche o temprano. |
| Suma de precipitación | 35% | Si se espera mucha lluvia, puede complicar el viaje y los planes al aire libre. |
| Horas de precipitación | 15% | Ayuda a saber si la lluvia sería solo un rato o durante gran parte del día. |
| **Total** | **100%** | |

## Por qué elegí estos pesos

Le di más importancia a la suma de precipitación porque, si llueve bastante, probablemente se complique hacer actividades afuera, pasear o incluso viajar. Por eso tiene un peso de **35%**.

Después le di importancia a la temperatura aparente máxima y mínima. Elegí la temperatura aparente en lugar de la temperatura común porque muestra mejor cómo se siente el clima, teniendo en cuenta cosas como el viento y la humedad.

Las horas de precipitación tienen menos peso, pero también son útiles. No es lo mismo que llueva mucho durante una hora que tener llovizna o lluvia durante casi todo el día.

No usé el código meteorológico porque resume datos que ya estoy teniendo en cuenta con la temperatura y la lluvia. Tampoco agregué la suma de lluvia por separado, porque es muy parecida a la suma de precipitación y estaría repitiendo casi el mismo dato.

## Conclusión

Con estos criterios puedo darle un puntaje a cada fin de semana y comparar cuál conviene más. El que tenga mejor clima, menos lluvia y temperaturas más agradables va a tener un puntaje más alto.