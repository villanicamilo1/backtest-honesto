---
name: revisor-backtests
description: Usar al diseñar, revisar o auditar un backtest o una prueba de estrategia de trading. Aplica preinscripción SÍ/NO, catálogo de trampas, autotest y entrega un informe con semáforo rojo/amarillo/verde.
---

# Revisor de backtests

Método para decidir si un resultado de backtest es real o un artefacto.
No promete ganancias: detecta errores y mide cuánta evidencia hay.

## Principio
Un NO es fuerte (encontrar un error es un hecho). Un SÍ es débil (no encontrar
errores no garantiza el futuro). Nunca escribir ni insinuar que una estrategia
"va a ganar" o que "no se va a perder dinero".

## Flujo

### 1. Preinscribir antes de mirar
Antes de correr con datos reales, escribir: pregunta, datos, tramo reservado,
qué se mide, criterio SÍ, criterio NO, zona gris, regla de "sin potencia",
autotest y número de pruebas de la familia. Si falta algo, pedirlo antes de seguir.

### 2. Revisar contra el catálogo de trampas
Recorrer cada grupo y anotar las que aplican:

- **Antes de correr:** criterio escrito antes · autotest con mundo con y sin efecto
  (si falla, no se corre) · revisión de construcción antes de ver el resultado ·
  un parámetro, un propósito · cargador que se detiene en el tramo reservado ·
  potencia del tramo reservado.
- **Fugas:** precio compartido (entrar en t+1) · umbrales y percentiles con ventana
  hacia atrás · beta hacia atrás · cortes en unidades del activo, no en dólares fijos.
- **Contar mal:** episodios, no operaciones · muestreo no solapado o bootstrap por
  bloques · listón según el número de pruebas (t ≥ 3 o Holm) y mismo signo en las
  dos mitades · efecto mínimo detectable ("sin potencia" ≠ NO) · hallazgo post hoc =
  hipótesis · réplica = misma construcción.
- **Beta disfrazada:** si dispara en todos los activos a la vez es beta · exceso
  contra canasta que excluye el activo · beta ≠ 1 · comparar retorno/caída contra
  comprar y mantener · escalar no cambia la razón retorno/caída.
- **Matemática:** logaritmos · piso de volatilidad · sensores en rango con ventana
  hacia atrás.
- **Costos:** comisión cero ≠ costo cero · horquilla en los momentos de la señal ·
  swap o financiamiento por noche · margen ≠ apalancamiento obligatorio.

### 3. Medir
- Retornos en logaritmos, entrada en t+1, neto de costos.
- t con bootstrap por bloques; reportar las dos mitades por separado.
- Efecto contra la referencia (no contra cero).
- Efecto mínimo detectable de cada celda.

### 4. Semáforo
- **ROJO:** se encontró al menos un error concreto. Nombrarlo y cuantificarlo.
- **AMARILLO:** sin errores, pero sin potencia o con mitades en desacuerdo.
- **VERDE:** pasa todos los controles preinscritos. Incluir siempre:
  "Esto no garantiza resultados futuros."

### 5. Informe (una página)
```
ESTRATEGIA:            REVISADA EL:
SEMÁFORO:
QUÉ SE ENCONTRÓ:       (máximo 3 puntos, con el número que lo demuestra)
QUÉ NO SE PUEDE SABER: (potencia, épocas no cubiertas, ejecución real)
SIGUIENTE PASO:        (una acción concreta)
AVISO: revisión técnica de datos pasados; no es asesoría de inversión
       ni garantía de resultados.
```

### 6. Registrar
Una línea por prueba, con el número decisivo, sea SÍ o NO:
`N.º · VEREDICTO · dato decisivo · qué queda cerrado · qué queda sin probar`
