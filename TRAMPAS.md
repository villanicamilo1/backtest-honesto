# Trampas de backtesting

Lista de errores que hacen que un backtest se vea mejor de lo que es.
Nace de 97 experimentos sobre datos de cripto (futuros de Binance, 2020-2024),
más un análisis de costos en ETF y futuros. Ninguna estrategia pasó todos los
controles, y casi todas las que "pasaban" al principio cayeron en alguna de estas.

Cada trampa trae **qué pasa**, **cómo se ve** y **cómo se evita**.

---

## A. Antes de correr

**1. No escribir el SÍ y el NO antes de mirar.**
Si el criterio se decide después de ver el resultado, siempre se encuentra uno que pase.
→ Escribir qué se mide, qué cuenta como SÍ, qué cuenta como NO y qué cuenta como zona gris. Fecharlo.

**2. Correr sin autotest.**
Un programa puede decir "funciona" porque tiene un error, no porque haya efecto.
→ Fabricar dos mundos: uno donde el efecto existe y otro donde no. La prueba tiene que distinguirlos. Si el autotest falla, no se corre con datos reales.

**3. Revisar el código solo cuando el resultado decepciona.**
Si los errores se buscan solo cuando sale NO, el registro se sesga hacia el SÍ.
→ Revisar ventanas, parámetros y alineación ANTES de ver el resultado, o con el mismo rigor sea SÍ o NO.

**4. Reusar un parámetro para dos cosas.**
Ejemplo real: la misma variable servía como paso de recalibración y como ventana de promedio; la prueba terminó midiendo una variable que nadie pidió.
→ Un nombre, un propósito.

**5. Tocar el tramo reservado.**
El último tramo de datos se guarda sin mirar para una sola prueba final. Un cargador que no lo corta lo quema sin que nadie se entere.
→ Todo cargador imprime su fecha máxima y se detiene si cruza la fecha reservada.

**6. Creer que el tramo reservado confirma algo.**
Dos años de datos casi nunca tienen potencia para confirmar un efecto pequeño.
→ Calcular el efecto mínimo detectable del tramo reservado antes de usarlo. Si es enorme, sirve solo para detectar desastres.

---

## B. Datos del futuro (fugas)

**7. Precio compartido.**
La señal usa el cierre de hoy y el retorno se calcula desde ese mismo cierre. Aparece un "efecto" que es puro artefacto.
→ Entrar en el periodo siguiente al de la señal.

**8. Percentiles o umbrales calculados con toda la muestra.**
Si el corte del "10 % más alto" usa todo el año, cada día conoce la distribución del futuro.
→ Umbrales con ventana hacia atrás (por ejemplo, 30 días anteriores).

**9. Beta estimada con toda la muestra.**
Restar el mercado con una beta calculada sobre todo el periodo usa información futura.
→ Beta con ventana hacia atrás.

**10. Cortes fijos en dólares.**
"Orden grande = más de 10.000 USD" significa otra cosa cuando el precio se multiplica por 8.
→ Cortes en unidades del activo o en percentil con ventana hacia atrás.

---

## C. Contar mal

**11. Contar operaciones en vez de episodios.**
Diez posiciones abiertas al mismo tiempo en activos que se mueven juntos son UNA apuesta, no diez. En un caso real la muestra estaba inflada 69 veces.
→ Agrupar en episodios.

**12. Muestras solapadas.**
Un retorno a 5 horas medido cada hora comparte el 80 % del camino con el siguiente. El estadístico t sale inflado.
→ Muestreo no solapado, o errores con bootstrap por bloques.

**13. Muchas pruebas, un solo listón.**
Con 100 combinaciones, un t > 2 aparece por azar unas 5 veces.
→ Contar las pruebas y subir el listón (t ≥ 3 o corrección de Holm), y exigir el mismo signo en las dos mitades de los datos.

**14. Llamar NO a lo que no se podía ver.**
Si la muestra es chica, un NO no significa "no hay efecto"; significa "no lo pude ver".
→ Calcular y publicar el efecto mínimo detectable de cada prueba. Si supera el doble del costo, la celda es "sin potencia" y no cuenta como SÍ ni como NO.

**15. Hallazgo encontrado después de mirar.**
Elegir la mejor celda después de ver 25 es una hipótesis nueva, no un resultado.
→ Se prueba en datos que no se usaron para encontrarla.

**16. Réplica con otra receta.**
Si la variable se construye distinto, no es réplica.
→ Misma construcción, otros datos.

---

## D. Beta disfrazada

**17. La estrategia es el mercado.**
Si la señal se activa en todos los activos a la vez, no son muchas apuestas: es estar comprado cuando todo sube. En un caso real, el 70 % del "efecto" era beta.
→ Medir el exceso contra una canasta. La canasta excluye el activo que se opera (si no, se diluye).

**18. Canasta con beta = 1.**
Restar el promedio supone que cada activo se mueve igual que el mercado. No es así.
→ Beta estimada hacia atrás para cada activo.

**19. Comparar contra cero en vez de contra comprar y mantener.**
Una estrategia que gana 46 % al año con 46 % de caída empata con comprar y mantener.
→ Comparar retorno ÷ caída máxima contra la referencia pasiva. El listón debe superar su propia caída.

**20. Escalar no arregla nada.**
Operar más pequeño baja el retorno y la caída en la misma proporción. La razón retorno/caída no cambia.

---

## E. Matemática

**21. Retornos simples con volatilidad alta.**
Más volatilidad sube la media aritmética aunque la deriva sea cero.
→ Medir en logaritmos.

**22. Dividir por una desviación casi cero.**
La desviación de una serie constante sale 1e-18 y el Sharpe 1e17.
→ Poner un piso a la volatilidad.

**23. Sensores con escalas que cambian.**
Un modelo entrenado en una época y evaluado en otra extrapola cuando las escalas cambian. En un caso real, el 75 % del castigo era escala.
→ Convertir sensores a rango dentro de una ventana hacia atrás.

---

## F. Costos

**24. Comisión cero no es costo cero.**
El costo se muda: conversión de moneda, horquilla, enrutamiento interno.
→ Buscar dónde está el costo antes de creerle a la tarifa.

**25. Costo medido en calma.**
Las señales suelen dispararse cuando la liquidez se va.
→ Medir la horquilla en los momentos en que la señal se activa.

**26. Costo de mantener la posición.**
Swap o financiamiento crece lineal con el tiempo; el movimiento típico crece como la raíz del tiempo. Pasado cierto plazo, mantener cuesta más de lo que el plazo da.
→ Sumar el costo por noche a cada horizonte.

**27. Margen no es apalancamiento obligatorio.**
El margen es el mínimo. El límite real es tu capital frente al tamaño mínimo del contrato.
→ Calcular cuánto capital hace falta para operar 1 contrato a 1:1.

---

## G. La regla de las reglas

**28. Un SÍ es débil y un NO es fuerte.**
Encontrar un error es un hecho. No encontrar errores no garantiza que la estrategia gane en el futuro.
