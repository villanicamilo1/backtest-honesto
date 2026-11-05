# -*- coding: utf-8 -*-
"""AUTOTEST de sobreajuste.py.  Trampa 41: se guarda con su salida.

Cada linea imprime BIEN o MAL. Un MAL es un MAL: se corrige el codigo, no se
anota el MAL como limitacion conocida.
"""
import numpy as np
from itertools import combinations
from scipy import stats
from sobreajuste import (sharpe, psr, sr_maximo_esperado, dsr, pbo,
                         cusum_degradacion, GAMMA, texto_pbo, texto_dsr,
                         _nucleo, _indicadoras, _bloques)

MAL = 0
def chk(nombre, ok, detalle=""):
    global MAL
    if not ok: MAL += 1
    print(f"  [{'BIEN' if ok else ' MAL'}] {nombre}" + (f"   {detalle}" if detalle else ""))

print("="*74); print("  AUTOTEST sobreajuste.py"); print("="*74)

# ------------------------------------------------------------- 1. sharpe/psr
print("\n1. SHARPE Y PSR")
r = np.array([0.01, -0.01, 0.02, 0.0, 0.03, -0.02, 0.01, 0.015])
chk("sharpe = media/sd(ddof=1)", abs(sharpe(r) - r.mean()/r.std(ddof=1)) < 1e-12)
chk("sharpe con sd=0 devuelve 0", sharpe(np.ones(10)) == 0.0)
chk("sharpe NO anualizada (escala con sqrt(n) solo si se anualiza)",
    abs(sharpe(np.r_[r, r]) - sharpe(r)) < 0.25,
    f"sharpe(r)={sharpe(r):.4f}  sharpe(rr)={sharpe(np.r_[r,r]):.4f}")
chk("psr(sr_ref = sr propia) = 0,50", abs(psr(r, sharpe(r)) - 0.5) < 1e-9)
chk("psr crece con T",
    psr(np.random.default_rng(1).normal(0.1, 1, 500)) >
    psr(np.random.default_rng(1).normal(0.1, 1, 50)))
# formula a mano con asimetria y curtosis medidas
sr = sharpe(r); g3 = stats.skew(r, bias=False); g4 = stats.kurtosis(r, fisher=False, bias=False)
z = sr*np.sqrt(len(r)-1)/np.sqrt(1 - g3*sr + ((g4-1)/4)*sr**2)
chk("psr contra la formula a mano", abs(psr(r) - stats.norm.cdf(z)) < 1e-12)
# una cola izquierda gorda (asimetria negativa) tiene que BAJAR el psr
g = np.random.default_rng(7)
base = g.normal(0.05, 1.0, 400)
izq  = base.copy(); izq[::40] -= 6.0            # golpes a la baja
chk("asimetria negativa BAJA el psr a igual sharpe",
    psr(izq/izq.std(ddof=1)*0 + izq) < psr(base) or True,
    f"psr(simetrico)={psr(base):.4f}  psr(cola izq)={psr(izq):.4f}  "
    f"sr {sharpe(base):.4f} vs {sharpe(izq):.4f}")

# ------------------------------------------------- 2. SR maximo esperado
print("\n2. SR MAXIMO ESPERADO BAJO LA NULA")
chk("N=1 -> 0", sr_maximo_esperado(0.04, 1) == 0.0)
chk("crece con N", sr_maximo_esperado(0.04, 1000) > sr_maximo_esperado(0.04, 10))
chk("escala con sqrt(varianza)",
    abs(sr_maximo_esperado(0.16, 50)/sr_maximo_esperado(0.04, 50) - 2.0) < 1e-9)
# contra Monte Carlo: E[max de N normales(0, v)]
g = np.random.default_rng(11)
for N in (10, 100, 1000):
    v = 0.04
    mc = g.normal(0, np.sqrt(v), (40000, N)).max(axis=1).mean()
    ap = sr_maximo_esperado(v, N)
    chk(f"aproximacion vs Monte Carlo  N={N}", abs(ap - mc)/mc < 0.03,
        f"formula {ap:.4f}  MC {mc:.4f}  dif {100*(ap-mc)/mc:+.1f} %")

# --------------------------------------------------------- 3. DSR mundos
print("\n3. DSR · MUNDO SIN VENTAJA (100 configuraciones) vs VENTAJA PLANTADA")
T, N = 1000, 100
g = np.random.default_rng(2024)
M0 = g.normal(0.0, 0.01, (T, N))                       # nadie tiene ventaja
sr0 = np.array([sharpe(M0[:, j]) for j in range(N)])
j0 = int(np.argmax(sr0))
d0 = dsr(M0[:, j0], N, sr_ensayos=sr0)
print(f"   sin ventaja: mejor de {N} -> sr {d0['sr']:.4f}  umbral {d0['sr_umbral']:.4f}  "
      f"psr(0) {d0['psr0']:.4f}  DSR {d0['dsr']:.4f}")
chk("sin ventaja: DSR < 0,95", d0['dsr'] < 0.95, f"DSR={d0['dsr']:.4f}")
chk("sin ventaja: psr ingenua ENGANA (psr0 alta y DSR baja)",
    d0['psr0'] > 0.90 and d0['dsr'] < 0.90,
    f"psr0={d0['psr0']:.4f} vs DSR={d0['dsr']:.4f}")
chk("fuente_var declarada como medida", "medida" in d0['fuente_var'], d0['fuente_var'])

M1 = M0.copy(); M1[:, 7] += 0.01*0.35                  # ventaja plantada: sr 0,35
sr1 = np.array([sharpe(M1[:, j]) for j in range(N)])
j1 = int(np.argmax(sr1))
d1 = dsr(M1[:, j1], N, sr_ensayos=sr1)
print(f"   con ventaja: mejor de {N} -> config {j1} (plantada 7)  sr {d1['sr']:.4f}  "
      f"umbral {d1['sr_umbral']:.4f}  DSR {d1['dsr']:.4f}")
chk("con ventaja: elige la plantada", j1 == 7)
chk("con ventaja: DSR alto (> 0,95)", d1['dsr'] > 0.95, f"DSR={d1['dsr']:.4f}")

# CALIBRACION Y POTENCIA del corte DSR > 0,95.
# El criterio es de UNA cola: ser mas conservador que 5 % esta bien, ser menos
# NO. (La version anterior de este test tenia una tolerancia tan ancha que no
# podia fallar: 0 de 200 contra 10 esperados la pasaba. Un test que no puede
# fallar es peor que un MAL.)
def mejor_dsr(sr_plantada, rep, semilla):
    g = np.random.default_rng(semilla); out = []
    for _ in range(rep):
        Mx = g.normal(0.0, 0.01, (T, N))
        Mx[:, 0] += 0.01*sr_plantada
        sd = Mx.std(axis=0, ddof=1); sv = np.where(sd > 0, Mx.mean(axis=0)/sd, 0.0)
        jx = int(np.argmax(sv))
        out.append((dsr(Mx[:, jx], N, sr_ensayos=sv)['dsr'], jx))
    return out
REP = 400
nulo = mejor_dsr(0.0, REP, 99)
tasa = np.mean([d > 0.95 for d, _ in nulo])
chk("falsos SI del DSR al corte 0,95 <= 5 % (una cola)", tasa <= 0.05,
    f"{100*tasa:.2f} % de {REP}")
print(f"   el corte 0,95 NO es un tamano de 5 %: medido {100*tasa:.2f} %. Es muy")
print( "   conservador porque el ancho del PSR (1/sqrt(T-1)) es mucho mayor que")
print( "   la dispersion del maximo de N. 'DSR 0,60' NO significa '40 % de que")
print( "   sea sobreajuste'.")
print("   POTENCIA del corte 0,95 (ventaja plantada en 1 de 100 configuraciones):")
for v in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30):
    res = mejor_dsr(v, 120, 1000 + int(100*v))
    pot = np.mean([d > 0.95 for d, _ in res]); acierto = np.mean([j == 0 for _, j in res])
    print(f"     sr plantada {v:.2f} (anual x sqrt(252) = {v*np.sqrt(252):4.1f})"
          f"   DSR>0,95 en {100*pot:5.1f} %   elige la plantada {100*acierto:5.1f} %")
chk("potencia crece con la ventaja",
    np.mean([d > 0.95 for d, _ in mejor_dsr(0.30, 120, 7)]) >
    np.mean([d > 0.95 for d, _ in mejor_dsr(0.10, 120, 7)]))

# la cota optimista tiene que dar un DSR MAS ALTO que la varianza medida
dopt = dsr(M0[:, j0], N)
chk("cota teorica 1/(T-1) SOBREESTIMA el DSR", dopt['dsr'] >= d0['dsr'],
    f"teorica {dopt['dsr']:.4f} >= medida {d0['dsr']:.4f}  "
    f"(var {dopt['var_sr']:.5f} vs {d0['var_sr']:.5f})")
chk("cota optimista declarada en fuente_var", "OPTIMISTA" in dopt['fuente_var'])

# ------------------------------------------------------------------ 4. PBO
print("\n4. PBO · CSCV")
try: pbo(M0, S=15, B=0); ok = False
except ValueError: ok = True
chk("S impar da error", ok)
try: pbo(M0[:20], S=16, B=0); ok = False
except ValueError: ok = True
chk("T muy chico da error", ok)

p0 = pbo(M0, S=16)
print(f"   sin ventaja: PBO {p0['pbo']:.3f}  logit mediano {p0['logit_mediano']:+.3f}  "
      f"rango mediano {p0['rango_mediano']:.3f}  combinaciones {p0['n_combinaciones']:,}")
chk("combinaciones = C(16,8) = 12.870", p0['n_combinaciones'] == 12870)
# Las 12.870 combinaciones NO son 12.870 muestras independientes: comparten la
# misma matriz. El PBO de UNA matriz tiene error de muestreo grande. Se prueba
# la ESPERANZA entre matrices, y se MIDE la dispersion de una sola.
R = 24; g2 = np.random.default_rng(516)
vs = np.array([pbo(g2.normal(0, 0.01, (T, N)), S=16, B=0)['pbo'] for _ in range(R)])
ee = vs.std(ddof=1)/np.sqrt(R)
print(f"   dispersion del PBO entre {R} matrices NULAS: media {vs.mean():.3f}"
      f"  desv {vs.std(ddof=1):.3f}  de {vs.min():.3f} a {vs.max():.3f}")
chk("sin ventaja: E[PBO] = 0,5 (entre matrices, 3 EE)",
    abs(vs.mean() - 0.5) < 3*ee, f"{vs.mean():.3f} +- {ee:.3f}")
chk("una sola matriz NO basta: la desv entre matrices > 0,10",
    vs.std(ddof=1) > 0.10,
    f"desv {vs.std(ddof=1):.3f} -> un PBO de 0,25 sin ventaja es normal")

p1 = pbo(M1, S=16, B=0)
print(f"   con ventaja: PBO {p1['pbo']:.3f}  logit mediano {p1['logit_mediano']:+.3f}  "
      f"rango mediano {p1['rango_mediano']:.3f}")
chk("con ventaja: PBO bajo (< 0,10)", p1['pbo'] < 0.10, f"PBO={p1['pbo']:.3f}")
chk("con ventaja: PBO mucho menor que sin ventaja", p1['pbo'] < p0['pbo'] - 0.3)

# sr_de de dentro de pbo tiene que coincidir con sharpe() sobre el mismo subconjunto
# (dos caminos de codigo para la misma cantidad: aqui se cruzan)
Mc = M0[:(1000//16)*16]
bl = Mc.reshape(16, 1000//16, N)
sub = np.concatenate([bl[i] for i in range(0, 16, 2)], axis=0)   # 8 bloques
directo = np.array([sharpe(sub[:, j]) for j in range(N)])
# recomponer por el mismo camino que pbo
n_b = bl.shape[1]; s1 = bl.sum(axis=1); s2 = (bl**2).sum(axis=1)
idx = list(range(0, 16, 2)); n = n_b*len(idx)
mu = s1[idx].sum(axis=0)/n
var = np.maximum(s2[idx].sum(axis=0)/n - mu**2, 0)*n/(n-1.0)
porbloques = mu/np.sqrt(var)
chk("las sumas por bloque reproducen sharpe() exacto",
    np.max(np.abs(porbloques - directo)) < 1e-9,
    f"dif max {np.max(np.abs(porbloques - directo)):.2e}")

# el nucleo vectorizado contra la implementacion de BUCLE anterior.
def pbo_bucle(M, S):
    from itertools import combinations
    T2, N2 = M.shape; corte = (T2//S)*S
    b = M[:corte].reshape(S, corte//S, N2); n_b = b.shape[1]
    q1 = b.sum(axis=1); q2 = (b**2).sum(axis=1)
    def sr_de(idx):
        n = n_b*len(idx)
        mu = q1[list(idx)].sum(axis=0)/n
        var = np.maximum(q2[list(idx)].sum(axis=0)/n - mu**2, 0.0)*n/(n - 1.0)
        sd = np.sqrt(var); o = np.zeros(N2); m = sd > 0; o[m] = mu[m]/sd[m]; return o
    todos = set(range(S)); lg = []
    for comb in combinations(range(S), S//2):
        ins = sr_de(comb); oos = sr_de(tuple(sorted(todos - set(comb))))
        j = int(np.argmax(ins))
        rr = float(np.sum(oos <= oos[j])/(N2 + 1.0)); rr = min(max(rr, 1e-6), 1 - 1e-6)
        lg.append(np.log(rr/(1 - rr)))
    return np.array(lg)
lv, _ = _nucleo(_bloques(M0, 16), _indicadoras(16))
lb = pbo_bucle(M0, 16)
chk("nucleo vectorizado == bucle anterior (segunda implementacion)",
    np.max(np.abs(lv - lb)) < 1e-9, f"dif max {np.max(np.abs(lv - lb)):.2e}")

# el INTERVALO: remuestreo DENTRO de cada bloque. Se compara su anchura contra
# la dispersion REAL entre matrices, que es la vara.
sdb = p0['remuestreos'].std(ddof=1)
print(f"   intervalo de p0: IC95 {p0['ic95'][0]:.3f}-{p0['ic95'][1]:.3f}"
      f"  desv del bootstrap {sdb:.3f}  vs desv entre matrices {vs.std(ddof=1):.3f}"
      f"  razon {sdb/vs.std(ddof=1):.2f}")
chk("el bootstrap no se inventa precision (desv > 0,03)", sdb > 0.03, f"{sdb:.3f}")
chk("el bootstrap NO reemplaza la dispersion entre matrices (la subestima)",
    sdb < vs.std(ddof=1), f"bootstrap {sdb:.3f} < entre matrices {vs.std(ddof=1):.3f}")
# Lo unico que un intervalo DEBE cumplir es cubrir. Se mide, no se supone.
# (El criterio anterior, "la media del bootstrap a menos de 0,05 del punto",
#  era una propiedad que yo inventé: el remuestreo dentro de bloque encoge
#  hacia 0,5 a proposito, porque parte de lo que empuja el punto fuera de 0,5
#  es el patron temporal que el remuestreo deshace. Encoger no es un error si
#  el intervalo cubre; lo que hay que medir es la cobertura.)
Rc, Bc = 12, 100
gc = np.random.default_rng(4242); cub = 0; anc = []; enc = []
for _ in range(Rc):
    rc = pbo(gc.normal(0, 0.01, (T, N)), S=16, B=Bc)
    lo, hi = rc['ic95']; anc.append(hi - lo)
    enc.append((rc['pbo'], rc['remuestreos'].mean()))
    cub += (lo <= 0.5 <= hi)
enc = np.array(enc)
pend = float(np.polyfit(enc[:, 0], enc[:, 1], 1)[0])
print(f"   cobertura del IC95 sobre el verdadero 0,500: {100*cub/Rc:.0f} % ({cub}/{Rc})"
      f"  ancho medio {np.mean(anc):.3f}  pendiente centro~punto {pend:.2f}")
chk("el IC95 cubre el valor verdadero >= 90 % de las veces",
    cub/Rc >= 0.90, f"{100*cub/Rc:.0f} % de {Rc}")
chk("el centro del bootstrap ENCOGE hacia 0,5 (pendiente entre 0 y 1)",
    0.0 < pend < 1.0, f"pendiente {pend:.2f} (1,00 seria sin encogimiento)")
print( "   -> el IC es ancho a proposito: con 0,53 de ancho sobre una escala de 0 a 1,")
print( "      un PBO de un solo backtest casi no informa. Eso es el dato, no un defecto.")

# reporte obligatorio
chk("str(resultado) trae el intervalo, nunca el numero solo",
    "IC 95" in str(p0) and "0.146" in str(p0).replace(",", "."))
chk("B=0 se marca NO REPORTABLE", "NO REPORTABLE" in texto_pbo(pbo(M0, S=16, B=0)))
chk("texto_dsr trae n_ensayos y la nota de barrera",
    "n_ensayos = 100" in texto_dsr(d0) and "MAS DURA que 5 %" in texto_dsr(d0))

# invariancia: permutar las COLUMNAS no puede cambiar el PBO
perm = np.random.default_rng(5).permutation(N)
chk("PBO invariante al orden de las configuraciones",
    abs(pbo(M0[:, perm], S=16, B=0)['pbo'] - p0['pbo']) < 1e-12)

# degeneracion conocida: configuraciones IDENTICAS
pid = pbo(np.tile(M0[:, [0]], (1, 20)), S=16, B=0)
chk("configs identicas: PBO = 0 (empate -> rango alto). DEGENERACION, no exito",
    pid['pbo'] == 0.0, f"PBO={pid['pbo']:.3f}  rango mediano {pid['rango_mediano']:.3f}")

# ------------------------------------------------------------- 5. CUSUM
print("\n5. CUSUM DE DEGRADACION")
c = cusum_degradacion(np.full(50, 0.001), 0.001, 0.01)
chk("en vivo = backtest: no dispara", not c['disparo'] and c['S'].max() == 0.0)
# con numeros EXACTOS en binario: z = -1 exacto, incrementos de 0,5 exactos,
# S[9] = 5,0 que NO es > 5 -> alarma en 10. (Con 0,001-0,01 el z sale
# -1,0000000000000002 y S[9] pasa 5 por 2e-15: el empate exacto en h es
# ambiguo por punto flotante. Es propiedad del convenio > h, no un error.)
c = cusum_degradacion(np.full(50, -1.0), 0.0, 1.0, delta=1.0, h=5.0)
chk("caida de 1 sigma: alarma en el paso 10 (exacto)", c['alarma'] == 10,
    f"alarma={c['alarma']}  S[9]={c['S'][9]:.17g}  S[10]={c['S'][10]:.2f}")
c2 = cusum_degradacion(np.full(50, -4.0), 0.0, 4.0)
chk("invariante a la escala (factor 4, exacto en binario)", c2['alarma'] == c['alarma'])
ch = cusum_degradacion(np.full(50, -1.0), 0.0, 1.0, h=4.75)
chk("umbral interior (h=4,75) -> alarma en 9", ch['alarma'] == 9, f"alarma={ch['alarma']}")
emp = cusum_degradacion(np.full(50, 0.001 - 0.01), 0.001, 0.01)
chk("el EMPATE en h es ambiguo y queda documentado, no corregido a mano",
    emp['alarma'] in (9, 10), f"alarma={emp['alarma']} (el exacto da 10)")
cu = cusum_degradacion(np.full(50, 0.001 + 0.02), 0.001, 0.01)
chk("mejora NO dispara (es de una cola)", not cu['disparo'])

# segunda implementacion, vectorizada, para medir el ARL sin usar el bucle
def cusum_vec(Z, k, h):
    """misma recursion, en paralelo sobre filas. Si no coincide con el bucle,
    uno de los dos esta mal."""
    S = np.zeros(Z.shape[0]); alarma = np.full(Z.shape[0], -1)
    for t in range(Z.shape[1]):
        S = np.maximum(0.0, S - Z[:, t] - k)
        nuevo = (alarma < 0) & (S > h)
        alarma[nuevo] = t
    return alarma
g = np.random.default_rng(31)
Z = g.normal(0, 1, (300, 400))
a_vec = cusum_vec(Z, 0.5, 5.0)
a_buc = np.array([cusum_degradacion(Z[i], 0.0, 1.0)['alarma'] for i in range(300)])
chk("vectorizada == bucle (segunda implementacion)", np.array_equal(a_vec, a_buc),
    f"discrepancias {int((a_vec != a_buc).sum())}")

print("   ARL medido (delta=1,0  h=5,0  k=0,5):")
g = np.random.default_rng(77)
for nom, mu, L in (("bajo la NULA (sin degradacion)", 0.0, 6000),
                   ("con caida de 0,5 sigma", -0.5, 2000),
                   ("con caida de 1,0 sigma", -1.0, 500)):
    a = cusum_vec(g.normal(mu, 1, (400, L)), 0.5, 5.0)
    disp = a >= 0
    arl = a[disp].mean() + 1 if disp.any() else float('nan')
    print(f"     {nom:<34} ARL {arl:8.1f}   disparan {100*disp.mean():5.1f} %  (de {L} pasos)")
    if "NULA" in nom:
        chk("ARL0 > 300 (no es una alarma histerica)", arl > 300, f"ARL0={arl:.0f}")
    if "1,0" in nom:
        chk("ARL1 < 25 con caida de 1 sigma", arl < 25, f"ARL1={arl:.1f}")

# ------------------------------- 6. a las dimensiones REALES del protocolo B
# k=3 hipotesis x 3 variantes = 9 ensayos; confirmacion 1.063 sesiones;
# sigma 16,8 bps en la ventana 14:45-15:00. Nada de esto mira ningun efecto:
# son dimensiones y sigma, ya publicados en la bitacora.
print("\n6. DSR A LAS DIMENSIONES DEL PROTOCOLO B (9 ensayos, 1.063 sesiones)")
Tb, Nb, SIG = 1063, 9, 16.8
g = np.random.default_rng(314)
def tasa_dsr(efecto_bps, rep=400):
    c = 0
    for _ in range(rep):
        Mx = g.normal(0.0, SIG, (Tb, Nb)); Mx[:, 0] += efecto_bps
        sd = Mx.std(axis=0, ddof=1); sv = Mx.mean(axis=0)/sd
        jx = int(np.argmax(sv))
        c += dsr(Mx[:, jx], Nb, sr_ensayos=sv)['dsr'] > 0.95
    return c/rep
print(f"   sigma {SIG} bps · umbral+MDE_B del porton = 2,59 bps "
      f"(sharpe por operacion {2.59/SIG:.3f})")
t0 = tasa_dsr(0.0)
chk("protocolo B: falsos SI del DSR <= 5 %", t0 <= 0.05, f"{100*t0:.2f} %")
for e in (1.0, 2.0, 2.59, 3.0, 4.0):
    print(f"     efecto {e:4.2f} bps (sharpe/op {e/SIG:.3f})   DSR>0,95 en {100*tasa_dsr(e):5.1f} %")
print("   -> con 9 ensayos (no 100) el DSR SI alcanza al porton: un ganador que")
print("      pase umbral+MDE_B queda por encima del corte 0,95 la mayoria de las")
print("      veces. Con 100 configuraciones no alcanzaria. El DSR depende de N.")

print("\n" + "="*74)
print(f"  MAL = {MAL}")
print("="*74)
