# TRAMPAS
Cada una nació de un error real, casi siempre mío. El número es la cicatriz,
no un adorno.

> **AVISO DE PÉRDIDA.** El texto original de las trampas 1 a 20 se perdió con
> el zip. Las que conservan su número (21, 23, 24, 25, 26) están confirmadas
> porque se citan dentro de los programas. Las demás van en la sección
> reconstruida, sin número, para no inventar numeración.

---

## 21 · El tamaño en disco no es el tamaño del dato
Declaré 8 meses de bookTicker «truncados» porque faltaban 30 GB contra el
manifiesto. Los archivos terminaban limpios en fin de mes. La diferencia del
27 % era **formato de número**: `96.90900000` escrito como `96.909`. Los
151 GB estaban completos y le dije que faltaban 30.

**Antes de declarar un dato roto, abre el final del archivo.**

---

## 22 · Los sensores se ordenan con ventana hacia atrás, por omisión
Un percentil calculado sobre toda la muestra usa el futuro para clasificar el
presente. El valor por omisión de cualquier sensor debe ser ventana hacia
atrás; mirar adelante tiene que costar escribirlo a mano.

---

## 23 · El tramo reservado se comprueba en el cargador
Cada cargador fija `SEG_RESERVADO`, imprime su fecha máxima y **falla** si
hay dato más allá. No basta con recordarlo al diseñar la prueba: el recorte
va donde se lee el archivo.

---

## 24 · Una réplica usa la MISMA construcción de la variable
Si la prueba que replica construye el sensor de otra manera, no es una
réplica: es una prueba nueva con el nombre equivocado. Mismo cargador, mismo
muestreo; lo único que cambia es la muestra.

---

## 25 · Si el autotest falla, no se corre
Sin excepciones, sin «es solo una comprobación de formato». Un autotest con
fallos es un programa que no sabes qué está midiendo.

---

## 26 · Un parámetro, un propósito
Reusé `paso` para recalibrar el percentil **y** para la ventana de
agregación. El programa promediaba sobre 24 horas creyendo promediar sobre 1,
y el resultado parecía bueno. Lo encontró el revisor, no yo, y no el
autotest.

**Dos conceptos distintos nunca comparten un parámetro, aunque hoy valgan lo
mismo.**

---

## 27 · El programa busca sus datos junto a sí mismo
Las rutas relativas al directorio actual hacen que «no encuentro nada» y «no
tengo datos» se vean igual. Perdió media hora.

Un programa resuelve sus carpetas desde `__file__`, **nunca** desde el
directorio del terminal, e imprime en la primera línea de dónde las está
leyendo. Si esa línea está mal, lo demás no importa y se ve de inmediato.

---

## 28 · Una comisión de cero no es un peaje de cero
ARQ cobra 0 % de comisión en ETF. Y 0,2 % de conversión de divisa **por
lado**: 40 bps ida y vuelta, tres veces el peaje de Binance. La comisión era
cero de verdad; el coste se había mudado.

**Antes de creerle a una tarifa, busca por dónde se escapó el coste**:
conversión de divisa, horquilla ensanchada, enrutamiento a un creador de
mercado, cuota de custodia o de inactividad.

---

# RECONSTRUIDAS · sin número original

## El autotest tiene que ejecutar `main()`
`rasgos.py` pasó 37 comprobaciones con una constante muerta dentro de
`main()` porque **el autotest nunca llamaba a `main()`**. Reventó en la
máquina de Camilo con un `NameError`.

Un autotest monta la carpeta entera, corre el programa de punta a punta y
comprueba su salida. En `peaje_mercados.py` además se para en un directorio
cualquiera a propósito, para que la trampa 27 no pueda volver.

## El guardia se verifica inyectando una constante mala
Que el autotest pase no prueba que detecte nada. Hay que romper el programa a
propósito y confirmar que sale con código 1.

Así se encontró la constante muerta de la prueba 99: cambié `HORAS["1d"]` de
24 a 12 y el autotest pasó tan campante, porque esas entradas no se leían.
Siete inyecciones ahora, siete detectadas.

## Un minuto malo no tira un mes bueno
`velas1m.py` rechazaba 43 200 minutos buenos por **un** minuto con compra
agresiva mayor que el volumen (EOS 2023-11, XRP 2023-11). Se limpia ese
minuto a NaN y se rechaza el mes solo si falla más del 0,1 %.

## Una posición se toma con su tamaño, o no se toma
`curva.py` abría posiciones de polvo al 0,03 % del tamaño buscado cuando la
caja estaba casi vacía, y las contaba como operaciones. Hace falta tope
explícito de ranuras **y** regla de tamaño mínimo. Lo encontró el autotest.

## Un hallazgo post hoc se prueba en otra muestra
El Δactividad apareció mirando SOL. Se probó en las otras 13 monedas,
excluyendo SOL. Y lo que se preinscribió como «extra, no decide» **sigue sin
decidir** aunque salga bonito: el 24 h de la prueba 97 dio SÍ y se anotó como
hipótesis, no como resultado.

## Comprueba extrapolación antes de decir «inestable»
Un ΔR² muy negativo fuera de muestra parece inestabilidad y suele ser escala.
En la prueba 96, el 75 % del castigo era extrapolación. El signo sobrevivió,
pero la lección era otra.

## La media de |retorno| no es el movimiento típico
La empuja la cola. SOL: media 88,0 contra mediana 56,5, un 56 % de
diferencia. Toda la tabla vieja de peaje-vs-horizonte estaba construida sobre
medias promediadas entre 14 monedas, y por eso la oportunidad parecía mayor
de lo que era.

**Para decidir si algo pasa el peaje, la mediana.** La media contesta otra
pregunta.

## La comisión mínima por orden decide el peaje a tamaño pequeño
Medí el ETF con la fórmula del futuro: una tarifa fija repartida sobre el
nocional. Pero un futuro tiene el nocional que tiene y un ETF se compra con
el dinero que hay. Con 2 000 USD compras 4 acciones de SPY y pagas el mínimo
de 1 USD **dos veces**: 11,9 bps, no 0,24.

La tabla decía 20-150× más barato que Binance. Era 1-3×.

## Mira el MDE antes de leer un NO
Un NO por debajo del efecto mínimo detectable no dice que no haya efecto;
dice que no podías verlo. A 24 h el MDE era 183,8 bps: ese NO no informaba.

## Episodios, no patas
Posiciones solapadas en varias monedas son UNA apuesta. La inflación llegó a
69×. El paso del muestreo es el propio horizonte.

## El umbral de |t| depende de cuántas celdas miraste
Con 132 celdas, |t| > 3 son 0,36 falsos positivos esperados. Se movió a 3,5
**después** de verificar que el veredicto no cambiaba, nunca para salvar un
resultado.

---

## 29 · Diez mercados correlacionados no son diez apuestas
    N_efectivo = n / (1 + (n−1)·ρ)      techo = 1/ρ

Medido: 10 ETF con ρ = 0,249 son **3,08** apuestas efectivas. Pasar a 28
mercados da 3,62 — un 8 % más de Sharpe. Mil darían 4,01.

Nació de un error mío: recomendé ampliar a 28 mercados prometiendo 73 % de
detección, y ese 73 % venía de 30 mercados **independientes** en simulación.
Los ETF reales no lo son.

**Mide las apuestas efectivas antes de prometer potencia.**

---

## 30 · Una optimización que cambia un resultado es un bug
Precalculé las canastas para que la calibración terminara, y las cifras se
movieron de +38,8 a +33,5. Una optimización no puede mover cifras.

Era `cestas[j]` en vez de `cestas[:, j]`: la beta se calculaba contra un
vector de 14 elementos en vez de 33.963, y `beta_atras` devolvía 1,0 por
falta de historia.

**Compara siempre contra el número de antes, y deja una prueba que corra las
dos versiones y exija que coincidan.**

---

## 31 · Calcula el MDE contra un efecto PLAUSIBLE antes de construir
La más cara de todas.

La prueba 102 se diseñó, se programó con 31 comprobaciones, se simuló y se
corrió. MDE: 147 bps. Efecto medido: 38,8. **Estaba muerta antes de escribir
la primera línea**, y se podía saber con una división.

No basta con reportar el MDE al final. Antes de construir:

    1. estima sigma del mercado en la ventana de la prueba
    2. MDE = 3·sigma / raíz(eventos disponibles)
    3. pregunta: ¿existe un efecto de ese tamaño en este mercado?
    4. si MDE > efecto plausible, NO SE CONSTRUYE

Aplicada hacia atrás, esta trampa mata la Prueba E (MDE 986 bps) y deja la
Prueba C en marginal (MDE 296) sin gastar un peso ni una tarde.

---

## 32 · No se corrige un veredicto desde un registro reconstruido
El 27-oct pasé el carry francotirador de CERRADO a GRIS, argumentando que
«cero episodios en 2022» era sin potencia y no un efecto medido.

El argumento era bueno. El dato era mío y estaba incompleto: lo saqué de **mi
reconstrucción** del registro perdido, no del original. El original tenía las
cifras — la ganancia neta por episodio cayó de +48,4 a +0,7 bps y ningún
umbral pasó. Eso es un efecto medido. Vuelve a CERRADO.

**Un registro reconstruido sirve para saber QUÉ se probó, no para revisar
veredictos.** Si falta el número, se pide; no se deduce.

---

## 33 · El mundo adversario tiene que atacar lo que la prueba AFIRMA
Para la prueba 103 construí un mundo con un salto de nivel de σ×5, esperando
que la calibración se rompiera. Dio SÍ igual: HAR sobre el logaritmo absorbe
un salto de nivel en pocos días y sobre 365 días la cobertura no se mueve.

Un intervalo del 50 % no afirma nada sobre el NIVEL: afirma algo sobre la
**dispersión alrededor del nivel**. Al atacar eso —dispersión triplicada— la
prueba cayó limpiamente: 0/14 dentro de banda, 14/14 fuera.

**Antes de escribir el mundo adversario, escribe qué afirma exactamente la
prueba, y atacá eso.** Un adversario que ataca otra cosa produce un SÍ que no
significa nada, y encima parece una validación.

---

## 34 · El tamaño de muestra de una CARTERA es el de su miembro más corto
La preinscripción de la 105 decía «los .npz llegan a 2026-09-30, 640 días de
reservado». Era verdad **por moneda** y falso **para la cartera**: EOSUSDT se
acaba el 2025-05-21, y la cartera se construye sobre los días comunes a las
13. Una moneda corta trunca las trece.

    640 dias de reservado  ->  141   (la 105 pedia >= 300)
    213 ventanas de 72 h   ->   46   (la 104 pedia >=  60)

Resultado: el disparo único se gastó y la 105, la 105b y la 105-99 **no
pudieron correr**. No dieron NO: no se hicieron.

MATIC sí se había comprobado y se excluyó por eso (acaba 2024-09-11).
Comprobé una moneda, no las trece, y di la verificación por completa.

**Antes de preinscribir cualquier prueba de cartera: imprimir el primer y el
último día de la INTERSECCIÓN y contar los días que caen en la ventana de
evaluación. Si ese número no está escrito en la preinscripción, la
preinscripción no está hecha.** Es la trampa 31 aplicada al tamaño de
muestra en vez de al efecto: una línea lo habría mostrado.

---

## 35 · Un mundo fabricado no vale hasta compararlo con el dato
Para la prueba 106 fabriqué un mundo de volatilidad agrupada con un AR(1) y
leí su potencia. El mundo no se parecía al dato en lo que importaba:

    log-sigma de la canasta   lag 1   lag 10   lag 30   sd del log
      real 2020-2022          0.890    0.605    0.405        0.328
      mi mundo AR(1)          0.931    0.656    0.161        0.752

Dispersión del **doble** y desplome a 30 días. Más dispersión de σ = más
espacio para que la regla actúe: **el mundo era generoso con la estrategia**.
Dio 11,5 % de SÍ; el mundo realista dio **0,0 %**.

Y antes había comparado la suma `b1+b2+b3` de un HAR (0,86, memoria larga)
con el parámetro de un AR(1) (0,90, vida media de 7 días) **como si fueran
lo mismo**. Dos parametrizaciones distintas, una conclusión sacada de ahí.

**Antes de leer la potencia de un autotest: imprimir la autocorrelación a
varios rezagos y la dispersión del mundo contra las del dato real, en la
serie que la estrategia de verdad usa.** Si no coinciden, la potencia medida
no es la potencia. Y no se comparan parámetros de modelos distintos: se
comparan los estadísticos que los dos producen.

---

## 36 · La potencia se cuenta con los eventos del periodo que se EVALÚA
La preinscripción de la 107 escribió «potencia 52 %». Ese número salió de un
mundo calibrado con la σ de **2020-2022**, que producía ~14 eventos al año.
El periodo evaluado fue **2023-2024**, con la vol un 31 % más baja, y dio
**7 y 10**. Menos eventos = razón más frágil = **menos potencia que la
escrita**.

El veredicto salió SÍ y no se tocó nada, pero el SÍ es FRÁGIL: un solo
evento más en 2023 lo habría dejado en GRIS.

Es la trampa 34 girada: allí el tamaño de muestra eran los **días** de la
cartera; aquí son los **eventos**, y el número de eventos **depende del nivel
de volatilidad del periodo**, que no es el del mundo que calibró la potencia.

**Cuando la prueba cuenta eventos raros (excesos, roturas de un límite,
reuniones), la potencia se calcula con el conteo del periodo que se va a
evaluar, no del de ajuste.** Y en cuanto se lee el dato, antes del veredicto:
contar los eventos reales y recalcular la potencia con ese conteo. Si salen
la mitad de los esperados, el veredicto se escribe con la fragilidad al lado,
no solo.

---

## 37 · La potencia se calcula BAJO LA NULA, no con el dato
En la 109 calculé el error de la tasa con un **bootstrap por bloques de la
serie realizada**, y al hacerlo vi el resultado. Escribí entonces que «hay
pruebas cuyo cálculo de potencia es la prueba». **Camilo lo corrigió, y
tenía razón: no hacía falta mirar la tasa.**

    error bajo la nula = raiz( p0 (1 - p0) / n )
      p0 = 0,25, que es el valor NULO, no el medido
      n  = los dias del quintil, que salen del CALENDARIO y del
           pronostico, no del resultado

    n = 473  ->  raiz(0,25 x 0,75 / 473)  =  1,99 pts

**El mismo 2,0 que me costó la ceguera.** La fórmula no toca el resultado.

### Y por qué mi corrección por agrupamiento sobraba
Usé bloques porque en este proyecto el agrupamiento de volatilidad casi
siempre infla el error. Aquí no: **bajo la nula, superar el percentil 75 de
los residuos son Bernoulli independientes por CONSTRUCCIÓN del cuantil.** El
agrupamiento es un problema de la **alternativa**, no de la nula. Resolví un
problema que bajo la nula no existe, y pagué con la única cosa que no se
puede recomprar.

**La regla: la potencia se calcula con los parámetros de la NULA y con un n
que salga del calendario o del diseño. Si para estimar el error hace falta el
resultado, es que se está usando la nula equivocada.**

---

## 38 · No se selecciona la muestra por algo que solo se sabe después
Para la 110 propuse medir **solo los días de ida y vuelta** (el 6,8 % en que
se tocan los dos límites), porque son los que miden reversión de verdad.

**Camilo lo cerró: eso condiciona en el resultado.** Qué días son de ida y
vuelta solo se sabe *después* de ver si el precio tocó los dos límites, y
tocarlos es parte de lo que la estrategia gana. Seleccionar esos días y medir
su P&L es medir los días que salieron bien y llamar muestra al conjunto.

Es la selección sobre la variable dependiente, con otro disfraz. La muestra
tiene que quedar definida por algo conocido **antes** del día: el calendario,
el pronóstico, un umbral fijado de antemano. Nunca por lo que hizo el precio.

**Y la segunda salida que propuse tampoco valía:** medir el esquema entero es
una apuesta direccional, y eso **reabre la familia 1 sin una razón nueva**.
Nueve familias cerradas no se reabren porque se les ponga otro nombre.

---

## 39 · Más mundos reducen el error de muestreo, no el de calibración
En la 111 pedí 1.000 mundos para la potencia y salió **58,6 % ± 1,6**. Un
número precioso de la cosa equivocada: era la potencia a una alfa de **0,459**
cuando el objetivo era **0,400**, porque calibré el mundo con 40 mundos y la
alfa tiene **sd 0,208** entre mundos. La bisección perseguía ruido.

    error de la potencia por muestreo (1.000 mundos)   ±1,6 puntos
    error por calibracion del mundo                    ±3,7 puntos

**El segundo era más del doble del primero, y añadir mundos no lo toca.** Con
la calibración hecha en serio (400 mundos por paso) la potencia es 46,7 %: la
diferencia entre pasar el umbral y no pasarlo.

**Antes de subir el número de mundos, preguntar qué error ata.** Si la
potencia es empinada en el parámetro del mundo —aquí ~180 puntos por cada
0,10 de alfa—, el error que manda es el de **calibrar el mundo**, no el de
contar mundos. Y se mide igual de fácil: produce N mundos con el parámetro
elegido y mira qué efecto dan de verdad.

---

## 40 · RETIRADA · era un artefacto de mi calibración
Escribí que «el N efectivo no predice la potencia», con tres casos de la 111
donde apuntaban al revés. **Camilo encontró el error: había calibrado la alfa
de CARTERA a un valor fijo en todos los universos**, así que un universo que
diversificaba más recibía una ventaja **por mercado más débil**. «Más N
efectivo» venía atado a «señal más floja», y eso fue lo que medí.

Con la ventaja por mercado fija, la potencia crece de forma **monótona** con
el número de series: 54 → 74 → 85 → 91 → 94 %.

**Se retira**, como se retiró la recomendación de los 28 mercados de la
prueba 100 (trampa 29). No se queda escrita una lección que salió de un
experimento mal montado.

Lo que sí queda, medido con el diseño correcto: **lo que compra potencia es
el NÚMERO de series, no su correlación.** A `n` igual, la ρ casi no importa
(74,0 % contra 76,5 % con ρ 0,10 y 0,25: 2,5 ± 3,0, ruido). El N efectivo
gobierna cuánto Sharpe te llevas; el número de señales gobierna si lo puedes
medir. No se contradicen: son dos preguntas.

### La lección de método, que es la que vale
**Cuando se compara un universo grande con uno pequeño, lo que se mantiene
fijo es la ventaja POR PIEZA, no la del conjunto.** Fijar la del conjunto le
quita al universo grande justo aquello que se estaba evaluando.

## 41 · Toda potencia se guarda con su script y su salida

Una potencia sin código **no es auditable**, y un número no auditable no
puede servir de referencia para validar otro arnés.

Lo aprendimos cuando la 111b intentó validar su arnés reproduciendo el 46,7 %
de la 111 y resultó imposible: el cálculo de la 111 se corrió en un
contenedor y nunca se escribió a disco. `tendencia_mercados.py` es el de la
100/101, sobre dato diario. **La 111 quedó declarada no auditable** — su
veredicto NO no cambió, porque 39,7 % y 46,7 % están los dos bajo su portón
de 50 %, pero ya no se puede usar para comparar nada.

### El corolario, que es el que de verdad vale

**La comprobación independiente no es lujo.** En la 111b hubo **ocho** errores
en los insumos del portón y **ninguno lo encontró una corrida**. Las corridas
produjeron cinco números perfectamente creíbles —72,8 · 64,3 · 57,5 · 64,4 ·
50,0 %— y cuatro estaban mal.

| error | lo encontró |
|---|---|
| regla comprado/VENDIDO en vez de comprado/fuera | escribir la preinscripción y leerla contra el código |
| σ de 36 meses incluía el mes en curso | autotest |
| S&P y bono sin exceso sobre la letra | autotest |
| el reservado filtrándose a la CALIBRACIÓN (al diseño) | autotest |
| r/c con el pico arrancando en el primer mes (+15 %) | **segunda implementación independiente** |
| unidad de la ventaja (comprado/fuera en vez de ±1) | revisión de Camilo |
| rango de ρ 3,8 veces estrecho, y objetivo mal | **tener que DECLARAR de dónde salía el número** |
| la tolerancia excluía justo la esquina peor | mirar por qué falló la exclusión en vez de aceptarla |

**Cinco de los ocho iban en la dirección de aprobar.** Dos se encontraron solo
porque hubo que escribir de dónde salía algo: declarar un número es una
comprobación, no papeleo.

## 42 · Una celda excluida por tolerancia no es una celda imposible

Cuando una rejilla de calibración excluye celdas por no alcanzar la
tolerancia, hay que distinguir dos casos, porque solo uno es legítimo:

```
  IMPOSIBLE   el parámetro queda en un EXTREMO de su rango.
              El mundo no puede reproducir el dato: se excluye.
  IMPRECISA   el parámetro queda en el INTERIOR y falló por precisión de la
              búsqueda. Se REINTENTA con más mundos hasta converger, o hasta
              mostrar que se topa.
```

En la 111b la rejilla dejó fuera tres celdas. Dos tenían `lam` en el suelo
(0,0000): con ρ del retorno 0,196 el mundo no puede dar una señal menos
correlacionada que ~0,19, así que eran genuinamente imposibles — y además
eran las celdas **mejores**, con lo que excluirlas no favorecía a nadie.

La tercera, (φ 0,98 · ρ 0,341), tenía `lam` 0,766, lejos de cualquier tope:
falló por 0,0073 contra una tolerancia de 0,005. **Y era la esquina que sería
la peor.** Reintentada con 1500 mundos de calibración convergió en dos rondas
y dio **50,0 %**, catorce puntos y medio por debajo de la siguiente peor.

Aceptarla como «no calibrable» habría dejado el portón en 64,5 % y lo habría
hecho pasar.

**Sin esta distinción, la tolerancia se convierte en un filtro que descarta
justo las esquinas incómodas**, y lo hace con cara de rigor.
