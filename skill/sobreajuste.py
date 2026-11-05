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
    return dict(dsr=psr(r, sr0), psr0=psr(r, 0.0), sr=sharpe(r),
                sr_umbral=sr0, var_sr=var_sr_ensayos, fuente_var=fuente,
                n_ensayos=int(n_ensayos), T=T,
                asimetria=float(stats.skew(r, bias=False)),
                curtosis=float(stats.kurtosis(r, fisher=False, bias=False)))

# --------------------------------------------------------------------- PBO
def pbo(M, S=16, metrica=sharpe):
    """CSCV. M es T x N: T observaciones, N configuraciones.
    Parte T en S submatrices disjuntas, toma las C(S,S/2) combinaciones,
    elige la mejor configuracion DENTRO de muestra y mide su rango FUERA.
    PBO = P(logit < 0) = prob. de que la mejor dentro caiga en la mitad
    peor fuera.
    """
    from itertools import combinations
    M = np.asarray(M, float)
    T, N = M.shape
    if S % 2: raise ValueError("S tiene que ser par")
    if T < S*2: raise ValueError(f"T={T} muy chico para S={S}")
    corte = (T//S)*S
    bl = M[:corte].reshape(S, corte//S, N)        # S bloques consecutivos
    # sumas por bloque para componer las combinaciones sin recorrer los datos
    n_b = bl.shape[1]
    s1 = bl.sum(axis=1)                            # S x N
    s2 = (bl**2).sum(axis=1)
    def sr_de(idx):
        n = n_b*len(idx)
        a = s1[list(idx)].sum(axis=0); b = s2[list(idx)].sum(axis=0)
        mu = a/n
        var = np.maximum(b/n - mu**2, 0.0)*n/(n - 1.0)
        sd = np.sqrt(var)
        out = np.zeros(N); m = sd > 0
        out[m] = mu[m]/sd[m]
        return out
    todos = set(range(S))
    logits = []; ranks = []
    for comb in combinations(range(S), S//2):
        ins = sr_de(comb)
        oos = sr_de(tuple(sorted(todos - set(comb))))
        j = int(np.argmax(ins))
        # rango relativo del elegido FUERA de muestra, en (0,1)
        r = float((np.sum(oos <= oos[j]))/(N + 1.0))
        r = min(max(r, 1e-6), 1 - 1e-6)
        ranks.append(r); logits.append(np.log(r/(1 - r)))
    logits = np.array(logits); ranks = np.array(ranks)
    return dict(pbo=float((logits < 0).mean()), logits=logits, rangos=ranks,
                n_combinaciones=len(logits), S=S, T=T, N=N,
                logit_mediano=float(np.median(logits)),
                rango_mediano=float(np.median(ranks)))

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
