# -*- coding: utf-8 -*-
"""SOBREAJUSTE · tres medidas para el revisor de backtests.

  dsr(retornos, n_ensayos)        Deflated Sharpe Ratio
                                  Bailey & Lopez de Prado (2014), "The Deflated
                                  Sharpe Ratio: Correcting for Selection Bias,
                                  Backtest Overfitting and Non-Normality",
                                  Journal of Portfolio Management 40(5).
                                  Usa la asimetria y la curtosis MEDIDAS, no
                                  supone normalidad.

  pbo(M, S=16)                    Probability of Backtest Overfitting por CSCV
                                  (Combinatorially Symmetric Cross-Validation),
                                  Bailey, Borwein, Lopez de Prado & Zhu (2017),
                                  "The Probability of Backtest Overfitting",
                                  Journal of Computational Finance 20(4).

  cusum_degradacion(...)          alarma de pausa: CUSUM de una cola sobre los
                                  retornos EN VIVO contra la media del backtest.

NO es para Titanio: es herramienta del revisor. No decide nada por si sola;
produce numeros que el revisor interpreta.

LO QUE MIDE EL AUTOTEST (no son citas, son numeros de este codigo):

  * El corte DSR > 0,95 NO es una prueba de tamano 5 %. Con 100 configuraciones
    y T=1000 los falsos SI medidos fueron 0,00 % de 400. Es MUY conservador.
    "DSR 0,60" NO significa "40 % de probabilidad de sobreajuste".
  * La potencia del DSR depende de N. Con 100 configuraciones hace falta una
    Sharpe por observacion de ~0,15 (anual ~2,4) para detectar la ventaja el
    62 % de las veces, y por debajo de 0,10 esta ciego. Con 9 configuraciones
    el corte 0,95 ya alcanza a un efecto del tamano del porton. Reportar el DSR
    sin reportar N no dice nada.
  * El PBO de UNA matriz tiene error de muestreo GRANDE. Las C(16,8)=12.870
    combinaciones comparten el mismo dato. Entre 24 matrices SIN NINGUNA
    ventaja: media 0,503, desviacion 0,146, recorrido de 0,159 a 0,817.
    Un PBO de 0,25 en un solo backtest no es evidencia de nada.
  * El INTERVALO del PBO (remuestreo dentro de bloque, B=200) cubrio el valor
    verdadero 30 de 30 veces en matrices nulas, con ancho medio 0,530 sobre una
    escala de 0 a 1: honesto pero casi no informativo. 30/30 a nominal 95 % es
    compatible con el 95 % (p = 0,21), no prueba sobrecobertura. La pendiente
    centro-del-bootstrap contra punto es 0,36, no 1,00: el intervalo se lee como
    "la banda de PBO compatible con estos datos", no como un intervalo centrado
    en el estimado.
  * El PBO da 0,000 cuando las configuraciones son casi identicas (todas
    empatan fuera de muestra y la elegida queda en el rango alto). Una rejilla
    de variantes que apenas varian produce un PBO halagador. DEGENERACION.
  * CUSUM con delta=1,0 y h=5,0: ARL bajo la nula 927 pasos; con caida de
    0,5 sigma 36,5; con caida de 1,0 sigma 10,5.

uso:  python sobreajuste.py --autotest
"""
import argparse, sys
import numpy as np
from scipy import stats

GAMMA = 0.5772156649015329          # Euler-Mascheroni

# --------------------------------------------------------------------- DSR
def sharpe(r, ddof=1):
    """Sharpe POR OBSERVACION (no anualizada). Toda la maquinaria del DSR
    trabaja en esta unidad; anualizar aqui es un error clasico."""
    r = np.asarray(r, float)
    s = r.std(ddof=ddof)
    return float(r.mean()/s) if s > 0 else 0.0

def psr(r, sr_ref=0.0):
    """Probabilistic Sharpe Ratio: P(SR verdadera > sr_ref) dado el estimado,
    corrigiendo por asimetria y curtosis MEDIDAS."""
    r = np.asarray(r, float); T = len(r)
    if T < 3: return float("nan")
    sr = sharpe(r)
    g3 = stats.skew(r, bias=False)
    g4 = stats.kurtosis(r, fisher=False, bias=False)      # curtosis CRUDA (3 = normal)
    den = 1.0 - g3*sr + ((g4 - 1.0)/4.0)*sr**2
    if den <= 0: return float("nan")
    z = (sr - sr_ref)*np.sqrt(T - 1.0)/np.sqrt(den)
    return float(stats.norm.cdf(z))

def sr_maximo_esperado(var_sr_ensayos, n_ensayos):
    """E[max SR] bajo la nula con n_ensayos independientes.
    SR*0 = sqrt(V[SR]) x [ (1-g)Z^-1(1-1/N) + g Z^-1(1-1/(N e)) ]"""
    N = max(int(n_ensayos), 1)
    if N == 1: return 0.0
    a = stats.norm.ppf(1.0 - 1.0/N)
    b = stats.norm.ppf(1.0 - 1.0/(N*np.e))
    return float(np.sqrt(max(var_sr_ensayos, 0.0))*((1.0 - GAMMA)*a + GAMMA*b))

def dsr(retornos, n_ensayos, var_sr_ensayos=None, sr_ensayos=None):
    """Deflated Sharpe. Devuelve dict con todo lo que hace falta para auditarlo.

    var_sr_ensayos : varianza de las Sharpe de los n_ensayos probados. Si no se
        pasa y se dan sr_ensayos, se mide de ahi. Si no se pasa ninguna, se usa
        la varianza TEORICA de la Sharpe bajo la nula, 1/(T-1), que es la cota
        OPTIMISTA (subestima la dispersion real entre configuraciones y por
        tanto SOBREESTIMA el DSR). Queda declarado en el resultado.
    """
    r = np.asarray(retornos, float); T = len(r)
    fuente = "pasada"
    if var_sr_ensayos is None:
        if sr_ensayos is not None and len(np.asarray(sr_ensayos)) > 1:
            var_sr_ensayos = float(np.var(np.asarray(sr_ensayos, float), ddof=1))
            fuente = "medida de los ensayos"
        else:
            var_sr_ensayos = 1.0/max(T - 1, 1)
            fuente = "teorica 1/(T-1) · COTA OPTIMISTA"
    sr0 = sr_maximo_esperado(var_sr_ensayos, n_ensayos)
    nota = (f"barrera MAS DURA que 5 %: falsos SI medidos 0,00 % de 400 "
            f"(N=100, T=1000). Reportar siempre con n_ensayos={int(n_ensayos)}.")
    return dict(nota=nota, dsr=psr(r, sr0), psr0=psr(r, 0.0), sr=sharpe(r),
                sr_umbral=sr0, var_sr=var_sr_ensayos, fuente_var=fuente,
                n_ensayos=int(n_ensayos), T=T,
                asimetria=float(stats.skew(r, bias=False)),
                curtosis=float(stats.kurtosis(r, fisher=False, bias=False)))

# --------------------------------------------------------------------- PBO
def _indicadoras(S):
    """matriz C x S con 1 en los bloques DENTRO de muestra. C = C(S, S/2)."""
    from itertools import combinations
    co = list(combinations(range(S), S//2))
    A = np.zeros((len(co), S))
    for i, c in enumerate(co): A[i, list(c)] = 1.0
    return A

def _nucleo(bl, A):
    """bl: S x n_b x N (bloques de tiempo contiguos). Devuelve logits y rangos.
    Vectorizado: las C(S,S/2) combinaciones se componen con un producto de
    matrices sobre las sumas por bloque, sin recorrer los datos C veces."""
    S, n_b, N = bl.shape
    s1 = bl.sum(axis=1); s2 = (bl**2).sum(axis=1)       # S x N
    n = n_b*(S//2)
    def srs(W):
        mu = (W @ s1)/n
        var = np.maximum((W @ s2)/n - mu**2, 0.0)*n/(n - 1.0)
        sd = np.sqrt(var)
        return np.where(sd > 0, mu/np.where(sd > 0, sd, 1.0), 0.0)
    ins = srs(A); oos = srs(1.0 - A)                     # C x N
    j = ins.argmax(axis=1)
    eleg = oos[np.arange(len(A)), j]
    r = (oos <= eleg[:, None]).sum(axis=1)/(N + 1.0)
    r = np.clip(r, 1e-6, 1 - 1e-6)
    return np.log(r/(1 - r)), r

def _bloques(M, S):
    corte = (M.shape[0]//S)*S
    return M[:corte].reshape(S, corte//S, M.shape[1])

class ResultadoPBO(dict):
    """dict que al imprimirse NUNCA da el PBO solo: siempre con su intervalo.
    Trampa 43: un PBO sin intervalo no es reportable."""
    def __str__(self): return texto_pbo(self)
    __repr__ = __str__

def pbo(M, S=16, B=200, semilla=0):
    """CSCV. M es T x N: T observaciones, N configuraciones.
    Parte T en S submatrices de tiempo CONTIGUO, toma las C(S,S/2)
    combinaciones, elige la mejor configuracion DENTRO de muestra y mide su
    rango FUERA. PBO = P(logit < 0).

    La metrica es la Sharpe por observacion. Para otra metrica hay que
    escribir otro nucleo: _nucleo esta vectorizado sobre la Sharpe.

    B remuestreos para el intervalo. El remuestreo es DENTRO de cada bloque:
    se remuestrean con reemplazo las filas de cada bloque por separado. Asi
    una fila duplicada nunca puede caer a la vez dentro y fuera de muestra,
    porque cada bloque entero es dentro o fuera en cada combinacion. Un
    bootstrap de filas sobre toda la matriz SI mezclaria las dos mitades y
    sesgaria el PBO a la baja. B=0 apaga el intervalo (no reportable).
    """
    M = np.asarray(M, float)
    T, N = M.shape
    if S % 2: raise ValueError("S tiene que ser par")
    if T < S*2: raise ValueError(f"T={T} muy chico para S={S}")
    A = _indicadoras(S)
    bl = _bloques(M, S)
    logits, ranks = _nucleo(bl, A)
    punto = float((logits < 0).mean())
    ic = None; rem = None
    if B:
        g = np.random.default_rng(semilla)
        rem = np.empty(B)
        for b in range(B):
            idx = g.integers(0, bl.shape[1], (bl.shape[0], bl.shape[1]))
            lb, _ = _nucleo(np.take_along_axis(bl, idx[:, :, None], axis=1), A)
            rem[b] = (lb < 0).mean()
        ic = (float(np.percentile(rem, 2.5)), float(np.percentile(rem, 97.5)))
    return ResultadoPBO(pbo=punto, ic95=ic, remuestreos=rem,
                        logits=logits, rangos=ranks, n_combinaciones=len(logits),
                        S=S, T=T, N=N, n_bloque=bl.shape[1], B=B,
                        logit_mediano=float(np.median(logits)),
                        rango_mediano=float(np.median(ranks)))

# ------------------------------------------------------------------ informe
def texto_pbo(res):
    """La UNICA forma sancionada de reportar un PBO. Trampa 43."""
    ic = res.get("ic95")
    t = (f"PBO {res['pbo']:.3f}" +
         (f" (IC 95 % {ic[0]:.3f}-{ic[1]:.3f}, {res['B']} remuestreos por bloque)"
          if ic else "  SIN INTERVALO: NO REPORTABLE (B=0)"))
    return (t + f" · S={res['S']} bloques de {res['n_bloque']} obs"
            f" · N={res['N']} configuraciones · {res['n_combinaciones']:,} combinaciones\n"
            "  Un PBO solo no es evidencia: sin ninguna ventaja, 24 matrices dieron"
            " de 0,159 a 0,817 (desv 0,146).\n"
            "  Si las configuraciones son casi identicas el PBO sale 0,000 sin"
            " ventaja alguna (trampa 43).")

def texto_dsr(res):
    """La UNICA forma sancionada de reportar un DSR: con N y con la nota."""
    return (f"DSR {res['dsr']:.4f}  (SR {res['sr']:.4f} por observacion, umbral de"
            f" seleccion {res['sr_umbral']:.4f}, PSR ingenua {res['psr0']:.4f})\n"
            f"  n_ensayos = {res['n_ensayos']} · T = {res['T']} ·"
            f" varianza entre ensayos: {res['fuente_var']}\n"
            f"  {res['nota']}")

# ------------------------------------------------------- CUSUM de degradacion
def cusum_degradacion(retornos_vivos, media_backtest, sigma, delta=1.0, h=5.0):
    """Alarma de PAUSA. CUSUM de una cola para detectar una caida de la media.

      z_t = (r_t - media_backtest)/sigma
      S_t = max(0, S_{t-1} - z_t - k)      con k = delta/2
      alarma cuando S_t > h

    delta es la caida a detectar en unidades de sigma; h el umbral. El ARL bajo
    la nula NO se cita: lo mide el autotest con estos mismos parametros.
    """
    r = np.asarray(retornos_vivos, float)
    k = delta/2.0
    z = (r - media_backtest)/sigma
    S = np.empty(len(r)); acc = 0.0; alarma = -1
    for i, zi in enumerate(z):
        acc = max(0.0, acc - zi - k)
        S[i] = acc
        if alarma < 0 and acc > h: alarma = i
    return dict(S=S, alarma=int(alarma), disparo=(alarma >= 0),
                k=k, h=h, delta=delta, n=len(r),
                S_final=float(S[-1]) if len(S) else 0.0)

# ----------------------------------------------------------------- entrada
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="medidas de sobreajuste")
    ap.add_argument("--autotest", action="store_true",
                    help="corre autotest_sobreajuste.py (trampa 41)")
    a = ap.parse_args()
    if a.autotest:
        import runpy, os
        runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "autotest_sobreajuste.py"), run_name="__main__")
    else:
        ap.print_help(); sys.exit(0)
