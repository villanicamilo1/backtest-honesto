# 27 — 111b · EL PORTON CIERRA. Quinto y ultimo numero.

Fecha 2026-11-04. Anula el 64,4 % de la entrada 25/26. **111b CERRADA SIN
CONSTRUIR. Ningun dato real evaluado, ni el desarrollo ni el reservado.**

```
  POTENCIA OFICIAL = 50,0 % ± 1,1     falsos SI 0,2 %
  esquina peor de la rejilla: phi 0,98, rho senal 0,341
  porton preinscrito 60 %         ->  NO PASA
  banda 48,9-51,1: entera por debajo de 60
```

## POR QUE SE VOLVIO A CORREGIR

La revision pidio **declarar de donde salia el rango de rho de la rejilla
(0,222-0,264)**. Al escribirlo aparecieron dos errores, los dos en el insumo
del porton y los dos contra la estrategia.

### Error A · el rango era 3,8 veces demasiado estrecho

Use el error estandar de Fisher, `(1-rho^2)/sqrt(n-3)` con n = 526 meses,
dividido por `sqrt(45/3)`. Las dos partes estan mal:

- **n = 526 meses no son 526 observaciones independientes.** La senal 12-1
  comparte 11 de 12 meses con la del mes anterior; su AR(1) es ~0,93.
- **El `sqrt(15)` fue un ajuste a ojo** (45 parejas / 3). No se deriva de nada.

Medido con bootstrap por bloques sobre el dato real (solo precios):

```
  se con Fisher y n=526 (lo que use)   0,0105
  se con bloques de 12 meses           0,0409
  se con bloques de 24 meses           0,0404
  se con bloques de 60 meses           0,0636
  rango honesto  0,180 a 0,341      rango que use  0,222 a 0,264
```

### Error B · el objetivo de rho tambien estaba mal: 0,260, no 0,243

El 0,243 se midio cuando la senal podia mirar a 1974 para formar el retorno de
12 meses de 1975-01. Con la ventana cortada en 1975-01 —correcto, el oro solo
es libre desde ahi— la primera senal computable es de 1976-02 y la rho sube a
**0,2604**.

### Error C · la tolerancia estaba excluyendo justo la esquina peor

La rejilla v2 dejo fuera tres celdas. **Dos exclusiones son genuinas y una no:**

```
  phi 0,85 · rho 0,180   lam 0,0000   rho lograda 0,1934   <- lam EN EL SUELO
  phi 0,98 · rho 0,180   lam 0,0000   rho lograda 0,1930   <- lam EN EL SUELO
  phi 0,98 · rho 0,341   lam 0,7656   rho lograda 0,3337   <- fuera por 0,0073
```

Las dos de rho 0,180 son imposibles: con `lam` en cero el mundo no baja de
~0,19 cuando la rho del retorno es 0,196. Y ademas serian las celdas MEJORES,
asi que excluirlas no favorece a nadie.

La de (0,98 · 0,341) tiene `lam` 0,766, lejos de cualquier tope: **fallo por
precision de la busqueda, no por imposibilidad. Y es la esquina que seria la
peor.** Dejarla fuera habria sido la tolerancia haciendole un favor a la
estrategia.

Reintentada con 1500 mundos de calibracion, **convergio en 2 rondas**:
`lam` 0,7326, rho lograda **0,3401** (objetivo 0,341), Sharpe ±1 0,2353.
Dentro de tolerancia en las dos cantidades.

**Y da 50,0 %**, catorce puntos y medio por debajo de la siguiente peor.

## LA REJILLA COMPLETA

```
    phi  rho obj     lam  rho logr   Sh+-1    alfa  beta     t      SI    GRIS    NO  falsos
   0.85    0.180  0.0000    0.1934                            NO CALIBRABLE (lam en el suelo)
   0.85    0.260  0.2295    0.2599  0.2434   0.539  0.56  3.46   78.1%   21.6%  0.2%   0.0%
   0.85    0.341  0.5210    0.3397  0.2382   0.510  0.56  3.28   72.8%   27.0%  0.3%   0.0%
   0.90    0.180  0.0000    0.1809  0.2406   0.561  0.57  3.61   81.8%   18.1%  0.1%   0.0%
   0.90    0.260  0.2430    0.2584  0.2441   0.540  0.57  3.47   78.0%   21.7%  0.2%   0.0%
   0.90    0.341  0.5727    0.3392  0.2395   0.501  0.57  3.22   69.2%   30.1%  0.7%   0.0%
   0.95    0.180  0.0000    0.1839  0.2384   0.548  0.56  3.52   78.1%   21.7%  0.1%   0.0%
   0.95    0.260  0.2857    0.2579  0.2367   0.523  0.57  3.36   74.4%   25.2%  0.4%   0.0%
   0.95    0.341  0.6498    0.3378  0.2448   0.488  0.57  3.13   65.5%   33.5%  1.0%   0.0%
   0.98    0.180  0.0000    0.1930                            NO CALIBRABLE (lam en el suelo)
   0.98    0.260  0.3589    0.2551  0.2406   0.489  0.57  3.13   64.5%   34.4%  1.0%   0.0%
   0.98    0.341  0.7326    0.3401  0.2353   0.429  0.57  2.74   50.0%   47.6%  2.4%   0.2%  <-- OFICIAL
```

10 celdas validas de 12. Monotona en las dos direcciones. Falsos SI entre 0,0 y
0,2 %: el criterio **no es flojo, es estrecho**.

Desglose de la celda que decide: t 54,9 % · mitades 77,7 % · meseta 91,1 % ·
r/c 93,4 %. **Lo que ata sigue siendo el t**, y el t es bajo por la beta 0,57
contra la referencia siempre larga.

## HISTORIAL COMPLETO DE LOS NUMEROS DEL PORTON

Ninguno se borra.

| # | numero | estado | causa |
|---|---|---|---|
| 1 | 72,8 % | INVALIDO | regla comprado/VENDIDO; r/c con el pico mal; ventaja sobre Sharpe cruda; reservado filtrado a la calibracion |
| 2 | 64,3 % | INVALIDO | los mismos, mas calibracion SECUENCIAL de lam y s_m (mundos con rho senal hasta 0,42) |
| 3 | 57,5 % | UNIDAD MAL | ventaja calibrada sobre comprado/fuera cuando la fuente mide ±1 -> mundo con 18 % MENOS tendencia -> numero conservador |
| 4 | 64,4 % | RANGO MAL | unidad corregida, pero rho objetivo 0,243 en vez de 0,260 y rango ±2se con el se 3,8 veces chico |
| 5 | **50,0 % ± 1,1** | **FINAL · NO PASA** | rango y objetivo de rho medidos con bloques; la esquina peor rescatada de una exclusion por tolerancia |

## LOS OCHO ERRORES, Y QUE LOS ENCONTRO

**Ninguno lo encontro una corrida.** Las corridas produjeron numeros creibles
cada vez.

| # | error | lo encontro |
|---|---|---|
| 1 | regla comprado/VENDIDO en vez de comprado/fuera | escribir la preinscripcion y leerla contra el codigo |
| 2 | sigma de 36 meses incluia el mes en curso | autotest |
| 3 | S&P y bono sin exceso sobre TB3MS | autotest |
| 4 | el reservado filtrandose a la CALIBRACION (al diseno) | autotest |
| 5 | r/c con el pico arrancando en el primer mes (+15 %) | segunda implementacion independiente |
| 6 | unidad de la ventaja (comprado/fuera en vez de ±1) | revision de Camilo |
| 7 | rango de rho 3,8 veces estrecho, y objetivo 0,243 en vez de 0,260 | tener que DECLARAR de donde salia el rango |
| 8 | la tolerancia excluia justo la esquina peor | mirar por que fallo la exclusion en vez de aceptarla |

Cinco de los ocho (1, 5, 6, 7, 8) iban en la direccion de aprobar.

## REGLA NUEVA PARA LAS EXCLUSIONES

**Una celda excluida por tolerancia no es lo mismo que una celda imposible.**

```
  se excluye SOLO si el parametro queda en un EXTREMO de su rango
  (lam en 0 o en 0,999): entonces el mundo no puede reproducir el dato.
  Si falla por tolerancia con el parametro en el interior, se REINTENTA con
  mas mundos hasta converger o hasta mostrar que se topa.
```

Sin esta regla, la tolerancia se vuelve un filtro que descarta justo las
esquinas incomodas.

## QUE CIERRA EL PORTON

**Cierra por la beta 0,57 MAS el costo de 10 bps. Sin cualquiera de los dos
pasaria.** Medido en la celda oficial, mismo mundo y distinto costo cobrado,
2000 mundos:

```
    bps   Sh+-1  Sh c/f   rotac    alfa  beta     t      SI    GRIS    NO   porton
      0   0.257   0.268  0.1116   0.487  0.57  3.12   61.4%   37.5%  1.1%   PASA (61,4±1,1)
     10   0.233   0.251  0.1116   0.429  0.57  2.74   50.0%   47.6%  2.4%   NO PASA  <- DECIDE
     20   0.208   0.234  0.1116   0.371  0.57  2.37   39.0%   56.2%  4.8%   NO PASA
```

A 0 bps pasaria, pero **raspando**: 61,4 ± 1,1, banda 60,3-62,5, apenas encima
del porton. Los 10 bps se llevan 11,4 puntos de potencia y lo hunden a 50,0 %.
Los 10 bps estaban fijados antes de correr, asi que el veredicto es NO PASA.

Las dos piezas, por separado:

- **beta 0,57 contra la referencia.** La regla comprado/fuera comparte mas de
  la mitad del riesgo con la canasta siempre larga, asi que el alfa de
  regresion —la unidad en la que el criterio A mide el SI— se queda en 0,429
  cuando la Sharpe cruda de las piezas es 0,251. Sin esa beta el alfa seria
  casi la Sharpe y el t pasaria de sobra.
- **costo 10 bps por rotacion.** La rotacion medida es 0,1116 por mercado y
  mes, o sea 13 bps al ano, que suena poco: pero se come 0,058 de alfa
  (0,487 -> 0,429) y con ella 11,4 puntos de potencia, porque el t estaba
  justo en el filo.

Lo que **no** cierra el porton: falta de senal (la ventaja esta puesta en
0,24, el valor que respalda la fuente externa), el universo (10 mercados con
45 anos), ni el criterio por flojo (falsos SI entre 0,0 y 0,2 %).

## LO QUE NO SE HACE

- No se afloja el porton del 60 %, ni el umbral 2,51, ni la tolerancia.
- No se vuelve a la rejilla estrecha de rho.
- No se excluye la celda que decide.
- No se abre la 111c: ±1 no gana potencia (77,2 contra 80,5 en la celda donde
  se comparo) y el problema de unidad se arreglo en la calibracion.
- No se reconstruye la 111, que sigue declarada no auditable.
- **No se abre el reservado.** No hay veredicto de desarrollo que proteger.

## LO QUE QUEDA MEDIDO Y SIRVE

- Panel 1975-2019 verificado, 0 saltos, divisas en USD por unidad extranjera.
- Bono a la par validado dos veces: Shiller 0,9974 (1871-2023), IEF 0,9916
  (2006-2024).
- Inflacion del t en el dato real: x1,254 con dependencia anual -> umbral 2,51.
- rho de la senal 0,2604 con error estandar 0,0404 por bloques de 24 meses.
- El arnes, autotest de 27 comprobaciones, costo verificado al bit, segunda
  implementacion de r/c.
- Que lo que ata una regla comprado/fuera es la beta contra la referencia
  siempre larga, no la senal.

## TRAMPA 41, confirmada ocho veces

Todo calculo de potencia se guarda con su script y su salida. Y el corolario:
**la comprobacion independiente no es lujo.** Ocho errores, cero encontrados
por una corrida.
