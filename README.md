# Backtest Honesto

**¿Tu backtest miente?** Un método, y el código que lo respalda, para saberlo antes de arriesgar dinero.

Esto **no es una estrategia de trading ni promete ganancias**. Es lo contrario: una forma
ordenada de encontrar los errores que hacen que una estrategia se vea mejor de lo que es.

Nace de [Titanio v2](#origen), un proyecto personal de investigación de mercados en Python
en el que cada hipótesis se escribió con su criterio SÍ/NO **antes** de mirar los datos.
La mayoría de esas hipótesis dio NO, y este repositorio conserva el método y las pruebas.

## Qué hay aquí

| Carpeta o archivo | Qué es |
|---|---|
| [`TRAMPAS.md`](TRAMPAS.md) | 29 trampas de backtesting: qué pasa, cómo se ve y cómo se evita |
| [`PLANTILLA_PREINSCRIPCION.md`](PLANTILLA_PREINSCRIPCION.md) | Plantilla para escribir el SÍ y el NO antes de mirar los datos |
| [`skill/sobreajuste.py`](skill/sobreajuste.py) | Código: Deflated Sharpe Ratio (DSR), Probabilidad de Sobreajuste (PBO por CSCV) y alarma CUSUM |
| [`skill/autotest_sobreajuste.py`](skill/autotest_sobreajuste.py) | Autotest de ese código, con su salida guardada en [`skill/salida_autotest.txt`](skill/salida_autotest.txt) |
| [`skill/revisor-backtests/SKILL.md`](skill/revisor-backtests/SKILL.md) | El método empaquetado como *skill* para Claude |
| [`111b/`](111b) | Un caso completo: la prueba 111b (tendencia multimercado), con scripts, salidas y cierre sellado |
| [`papel/`](papel) | Registro diario en papel (pronósticos sellados con hash) |

## El semáforo

Cada revisión termina en uno de tres colores:

- 🔴 **Rojo:** hay un error concreto (beta disfrazada, datos del futuro, costos ignorados, muestras solapadas).
- 🟡 **Amarillo:** no hay errores, pero los datos no alcanzan para concluir.
- 🟢 **Verde:** pasa los controles escritos de antemano. **No garantiza resultados futuros.**

Un NO es fuerte: encontrar un error es un hecho. Un SÍ es débil: no encontrar errores no dice que la estrategia vaya a ganar.

## Tecnologías

Python 3 con `numpy` y `scipy`.
Probado con Python 3.13, numpy 2.5 y scipy 1.18.

## Instalación

```bash
git clone https://github.com/villanicamilo1/backtest-honesto
cd backtest-honesto
pip install -r requirements.txt
```

## Ejemplo de uso

Un mundo **sin ninguna ventaja**: 100 configuraciones de ruido, y nos quedamos con la mejor.
La Sharpe ingenua la hace ver bien; el DSR corrige por haber probado 100.

```python
import sys
sys.path.insert(0, "skill")
import numpy as np
from sobreajuste import dsr

rng = np.random.default_rng(1)
M = rng.normal(0, 0.01, (1000, 100))            # 1000 observaciones x 100 configuraciones
mejor = M[:, np.argmax(M.mean(0) / M.std(0))]   # la "ganadora" por Sharpe

r = dsr(mejor, n_ensayos=100)
print(r["psr0"], r["dsr"])
```

Salida obtenida al preparar este README: `psr0 = 0.986` (la ingenua dice "casi seguro que hay ventaja")
y `dsr = 0.382` (corregida por 100 ensayos, no pasa el corte de 0,95).
Con otra semilla el número cambia; lo que debe repetirse es que el DSR queda por debajo de 0,95.

Para correr el autotest completo (tarda cerca de 1 minuto):

```bash
cd skill
python autotest_sobreajuste.py
```

Para usar la skill con Claude, sube la carpeta `skill/revisor-backtests` en la configuración de skills
de tu cuenta y pide: *"Revisa este backtest con el revisor de backtests"*, adjuntando tus reglas y tu
lista de operaciones o curva de capital (CSV).

## Estado: qué está probado y qué no

**Probado** (corrido de nuevo el 19-nov-2026 en una revisión de este repositorio):

- `skill/autotest_sobreajuste.py`: 50 controles `BIEN`, 0 `MAL`, igual que la salida guardada.
- Ejemplo de uso de arriba.
- `111b/costo_celda.py`: reproduce el resultado oficial de la 111b, potencia **50,0 % ± 1,1** a 10 bps
  contra un portón de 60 % (NO PASA); a 0 bps da 61,4 % (PASA).
- `111b/unidad_111b.py` y `111b/rango_rho.py`: corren hasta el final y producen salida.

**Experimental:**

- **Registro en papel** (`papel/`): con registros desde el 29-oct-2026, un script diario escribe un pronóstico del rango
  del día para 12 monedas y lo sella con un hash antes de ver el resultado. Evalúa **solo el pronóstico
  de riesgo (cuánto se mueve el mercado), no si una estrategia gana dinero.** Los días sin pronóstico
  quedan registrados con su causa en [`papel/huecos.csv`](papel/huecos.csv). El script que lo genera
  (`papel_diario.py`) vive en el repositorio de Titanio, no aquí.
- **La skill para Claude:** el método está escrito y se usó en el proyecto; este repositorio no incluye
  una prueba automática de la skill.

**Pendiente:**

- `111b/celda_peor.py` y `111b/rejilla_111b.py` tardan más de 4 minutos; no se esperó a que terminaran en esta revisión.
- Control de 30 días del registro en papel: 1 de diciembre de 2026.
- Documentar la fuente y la licencia de los datos de `111b/panel_111b.csv`.
- Elegir una licencia para el código.

## Limitaciones

- **No hay ninguna estrategia direccional validada.** El proyecto de origen demostró que sabe medir
  cuánto se mueve el mercado y cuánto riesgo tomar, no hacia dónde va. Las hipótesis de dirección
  probadas dieron NO.
- Un DSR o un PBO por sí solos no deciden: el PBO de **una** matriz tiene un error de muestreo grande
  (el autotest lo mide). Los números hay que reportarlos con el número de ensayos.
- El corte DSR > 0,95 es conservador: con pocos datos puede no detectar una ventaja que sí existe.
- Algunos scripts de `111b/` y el registro en papel están escritos para el entorno de su autor
  (Windows, rutas propias) y pueden pedir ajustes en otra máquina.
- Es una revisión técnica de datos pasados, no una predicción.

## Origen

Titanio v2 es el proyecto de investigación de mercados de Camilo Villani: un sistema en Python
(datos de Binance, pruebas de estrategias, registro en papel) construido de forma autodidacta.
Su código completo está en un repositorio aparte (`titanium_v2`).

## Revisión hecha por una persona

[Pedir una revisión](https://docs.google.com/forms/d/e/1FAIpQLSd7EJB-5X7tGj8Kt_zmHnQfcAK6baNQj0zmCLptHY3NF7km1A/viewform?usp=header)

## Aviso

Revisión técnica de datos pasados. No es asesoría de inversión ni garantía de
resultados. Operar con apalancamiento puede hacerte perder más de lo que pusiste.


## Licencia y datos
El código fuente y la documentación original de este proyecto se ofrecen bajo la licencia MIT (ver `LICENSE`). La licencia no cubre datos de terceros. La fuente y los términos de reutilización de `111b/panel_111b.csv` aún no están verificados; no se afirma que ese archivo pueda redistribuirse o relicenciarse.
