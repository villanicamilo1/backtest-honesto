# Backtest Honesto

**¿Tu backtest miente?** Un método para saberlo antes de arriesgar dinero.

Esto no es una estrategia de trading ni promete ganancias. Es lo contrario:
una forma ordenada de encontrar los errores que hacen que una estrategia se vea
mejor de lo que es.
Nace de 97 experimentos sobre datos de cripto (futuros de Binance, 2020-2024),
más un análisis de costos en ETF y futuros.

## Qué hay aquí

| archivo | para qué |
|---|---|
| [`TRAMPAS.md`](TRAMPAS.md) | 28 trampas de backtesting: qué pasa, cómo se ve, cómo se evita |
| [`PLANTILLA_PREINSCRIPCION.md`](PLANTILLA_PREINSCRIPCION.md) | escribir el SÍ y el NO antes de mirar los datos |
| [`skill/revisor-backtests/SKILL.md`](skill/revisor-backtests/SKILL.md) | el mismo método empaquetado como skill para Claude |

## El semáforo

Cada revisión termina en uno de tres colores:

- 🔴 **Rojo:** hay un error concreto (beta disfrazada, datos del futuro, costos ignorados, muestras solapadas).
- 🟡 **Amarillo:** no hay errores, pero los datos no alcanzan para concluir.
- 🟢 **Verde:** pasa los controles escritos de antemano. **No garantiza resultados futuros.**

Un NO es fuerte: encontrar un error es un hecho.
Un SÍ es débil: no encontrar errores no dice que la estrategia vaya a ganar.

## Cómo usar la skill

1. Descarga la carpeta `skill/revisor-backtests`.
2. Súbela como skill en Claude (en la configuración de skills de tu cuenta).
3. Pide: *"Revisa este backtest con el revisor de backtests"* y adjunta tus reglas
   y tu lista de operaciones o curva de capital (CSV).

## Revisión hecha por una persona

escribe aquí: **[Pedir una revisión](https://docs.google.com/forms/d/e/1FAIpQLSd7EJB-5X7tGj8Kt_zmHnQfcAK6baNQj0zmCLptHY3NF7km1A/viewform?usp=header)**
## Aviso

Revisión técnica de datos pasados. No es asesoría de inversión ni garantía de
resultados. Operar con apalancamiento puede hacerte perder más de lo que pusiste.
