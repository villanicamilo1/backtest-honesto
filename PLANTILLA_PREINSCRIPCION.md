# Plantilla de preinscripción

Se llena y se fecha ANTES de correr nada con datos reales.
Lo que no esté escrito aquí no se puede usar después para decidir.

```
PRUEBA N.º ____        FECHA ________        PROGRAMA ____________

PREGUNTA
  (una sola, concreta y medible)

DATOS
  activos:
  periodo de desarrollo:            → hasta ____-__-__
  tramo reservado (no se toca):     ____-__-__ en adelante
  potencia del tramo reservado:     efecto mínimo detectable = ____

QUÉ SE MIDE
  señal:
  entrada: periodo siguiente a la señal (t+1)
  horizonte(s):
  muestreo: no solapado / episodios
  referencia: comprar y mantener / canasta sin el activo / beta hacia atrás
  costo por vuelta (fuente):

SÍ si
  t ≥ ____ (bootstrap por bloques)
  mismo signo en las dos mitades
  efecto ≥ ____ (piso económico)
  retorno/caída ≥ referencia

NO si
  ...

ZONA GRIS
  ...

SIN POTENCIA
  si el efecto mínimo detectable > 2 × piso → no cuenta como SÍ ni como NO

AUTOTEST (--simular)
  mundo con efecto → debe dar SÍ en ≥ __ % de semillas
  mundo sin efecto → falsos SÍ ≤ 5 %

NÚMERO DE PRUEBAS EN ESTA FAMILIA: ____
```

## Después de correr

Una línea en la bitácora, con el número que decidió:

```
N.º · VEREDICTO · dato decisivo · qué queda cerrado · qué queda sin probar
```

Si el veredicto es NO, se escribe igual. Un registro que solo guarda los SÍ miente.
