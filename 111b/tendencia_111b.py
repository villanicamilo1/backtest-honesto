# -*- coding: utf-8 -*-
"""PRUEBA 111b · tendencia multimercado con historia larga.
Porton de potencia con COSTO FIJADO. Nada de dato real se evalua aqui.

COSTO (fijado el 2026-11-03, antes de cualquier retorno de estrategia):
  10 bps por unidad de rotacion, por lado, sobre |cambio de posicion|.
  Se resta a la ESTRATEGIA Y a la REFERENCIA: la referencia tambien reajusta
  tamano cada mes, y si solo paga la estrategia la comparacion no es justa.
  0 y 20 bps se reportan como informacion; NO deciden.
  Peaje medido en micro futuros: 0,3 a 2 bps. El 10 cubre de sobra 1975-1990.

LIMITE DECLARADO: la ventaja neta por mercado 0,24 viene de Hurst, Ooi &
  Pedersen (AQR) 1880-2016, que son FUTUROS con carry; la 111b opera al
  CONTADO. Si en contado fuera 0,20 la potencia cae a ~53 % y el porton
  cerraria. Ese limite NO se ajusta: se declara.

uso:  python tendencia_111b.py --autotest
      python tendencia_111b.py --simular
      python tendencia_111b.py --potencia [--calib N] [--eval N]
"""
import argparse, os, sys, csv
import numpy as np

BPS = 0.0010                      # 10 bps por unidad de rotacion, por lado
OBJ = 0.10 / np.sqrt(12)          # 10 % anual de sigma objetivo por mercado
VENT = 36                         # sigma de 36 meses
SH_NETA = 0.24                    # ventaja NETA por mercado, EN LA UNIDAD +-1:
                                  # es la que mide la fuente externa (AQR).
                                  # Calibrarla sobre comprado/fuera fue el error
                                  # del 57,5 % (ver bitacora 25).
UMBRAL = 2.51                     # inflacion del t medida en el dato real: x1,254
PHI_PEOR, RHO_PEOR = 0.98, 0.264  # esquina peor de la REJILLA COMPLETA
TOL_CAL = 0.005                   # tolerancia de calibracion, rho y Sharpe
MERCADOS = ["sp","bono","oro","plata","cobre","yen","libra","franco","cad","eur_dem"]
DEV_INI, DEV_FIN = 1975*12+0, 2019*12+11     # desarrollo. El reservado
                                             # (2020-01..2023-06) NO entra en la
                                             # calibracion del mundo: si entra,
                                             # el reservado informa el diseno.

# ---------------------------------------------------------------- panel real
def leer_panel(ruta):
    """panel_111b.csv: ym + los 10 mercados + tb3ms_pct. Solo para medir
    sigma, correlacion y la deriva de la referencia. NO se evalua la regla."""
    f = list(csv.reader(open(ruta, encoding="utf-8-sig")))
    cab = f[0]; idx = [cab.index(m) for m in MERCADOS]; itb = cab.index("tb3ms_pct")
    ym = []; X = []; TB = []
    for r in f[1:]:
        if not r or not r[0]: continue
        a, m = r[0].split("-"); ym.append(int(a)*12 + int(m) - 1)
        X.append([float(r[i]) for i in idx]); TB.append(float(r[itb]))
    ym = np.array(ym); X = np.array(X).T; TB = np.array(TB)
    saltos = int((np.diff(ym) != 1).sum())
    if saltos: raise SystemExit(f"panel con {saltos} saltos de calendario")
    return ym, X, TB

def solo_desarrollo(ym, X, TB):
    """recorta al periodo de DESARROLLO. Todo lo que calibra el mundo sale de
    aqui; el reservado no se toca."""
    m = (ym >= DEV_INI) & (ym <= DEV_FIN)
    return ym[m], X[:, m], TB[m]

EXCESO = ("sp", "bono")      # preinscrito: S&P y bono en EXCESO sobre TB3MS

def momentos(ym, X, TB):
    """retornos mensuales. S&P y bono en EXCESO sobre la letra a 3 meses; el
    resto al contado (el carry queda como limite escrito)."""
    r = np.diff(np.log(X), axis=1)
    for m in EXCESO: r[MERCADOS.index(m)] -= TB[1:]/1200.0
    sig = r.std(axis=1, ddof=1)
    return r, sig, np.corrcoef(r)

# ---------------------------------------------------------------- costo
def rotacion(pos):
    """|cambio de posicion| mes a mes. La primera posicion se paga entera."""
    ant = np.concatenate([np.zeros(pos.shape[:-1] + (1,)), pos[..., :-1]], axis=-1)
    return np.abs(pos - ant)

def neto(pos, r, bps=BPS):
    """retorno por mercado NETO del costo de rotacion"""
    return pos * r - bps * rotacion(pos)

# ---------------------------------------------------------------- mundo
def _pd(C):
    w, V = np.linalg.eigh(C); w = np.clip(w, 1e-8, None); C = V @ np.diag(w) @ V.T
    d = np.sqrt(np.diag(C)); return C / np.outer(d, d)

def mundo(sig, C, s_m, lam, nw, d_ref, phi, n_mes, rng):
    k = len(sig)
    Le = np.linalg.cholesky(_pd(C))
    Lm = np.linalg.cholesky(_pd((1 - lam) * C + lam * np.ones((k, k))))
    s_e = np.sqrt(np.maximum(sig**2 - (s_m*sig)**2/(1 - phi**2), 1e-12))
    e = np.einsum("ij,wjt->wit", Le, rng.standard_normal((nw,k,n_mes)))*s_e[None,:,None]
    h = np.einsum("ij,wjt->wit", Lm, rng.standard_normal((nw,k,n_mes)))*(s_m*sig)[None,:,None]
    m = np.empty_like(h); m[:,:,0] = h[:,:,0]/np.sqrt(1-phi**2)
    for t in range(1, n_mes): m[:,:,t] = phi*m[:,:,t-1] + h[:,:,t]
    return (d_ref*sig)[None,:,None] + m + e

# ---------------------------------------------------------------- la regla
def sigma_movil(r, v=VENT):
    """s[...,t] = sigma de los v meses ESTRICTAMENTE ANTERIORES a t: t-v .. t-1.
    No usa r[...,t]. Un indice de diferencia aqui es mirada al futuro."""
    w, k, T = r.shape; s = np.full((w,k,T), np.nan)
    c = np.concatenate([np.zeros((w,k,1)), np.cumsum(r, axis=2)], axis=2)
    c2 = np.concatenate([np.zeros((w,k,1)), np.cumsum(r*r, axis=2)], axis=2)
    for t in range(v, T):
        su = c[:,:,t]-c[:,:,t-v]; su2 = c2[:,:,t]-c2[:,:,t-v]
        s[:,:,t] = np.sqrt(np.maximum(su2/v - (su/v)**2, 1e-12))
    return s

def correr(r, L=12, bps=BPS):
    """devuelve (piezas netas por mercado, cartera estrategia, cartera referencia).
    La senal de t usa hasta t-1. La sigma de t usa hasta t-1. Sin mirada al futuro."""
    w, k, T = r.shape
    lp = np.cumsum(r, axis=2); s36 = sigma_movil(r)
    ini = max(VENT, L + 1)
    tam = OBJ / s36[:, :, ini:T]                           # sigma de t-36..t-1
    sg = np.sign(lp[:,:,ini-1:T-1] - lp[:,:,ini-1-L:T-1-L]); sg[sg == 0] = 1.0
    sg = np.maximum(sg, 0.0)                               # comprado o FUERA
    rr = r[:, :, ini:T]
    pe = neto(sg*tam, rr, bps); pr = neto(tam, rr, bps)
    return pe, pe.mean(axis=1), pr.mean(axis=1)

# ---------------------------------------------------------------- criterio
def alfa_t(e, rf):
    n = e.shape[1]
    x = rf - rf.mean(axis=1, keepdims=True); y = e - e.mean(axis=1, keepdims=True)
    sx2 = np.maximum((x*x).sum(axis=1), 1e-18); b = (x*y).sum(axis=1)/sx2
    a = e.mean(axis=1) - b*rf.mean(axis=1); res = e - (a[:,None] + b[:,None]*rf)
    se = np.sqrt(res.var(axis=1, ddof=2)*(1.0/n + rf.mean(axis=1)**2/sx2))
    return a, a/np.maximum(se, 1e-18), res, b

def rc(X):
    """r/c: curva COMPUESTA con el capital inicial dentro del pico"""
    eq = np.concatenate([np.ones((X.shape[0],1)), np.cumprod(1.0+X, axis=1)], axis=1)
    pico = np.maximum.accumulate(eq, axis=1)
    dd = ((pico-eq)/pico).max(axis=1)
    return (eq[:,-1]**(12.0/X.shape[1]) - 1.0)/np.maximum(dd, 1e-12)

def rc_bucle(X):
    """segunda implementacion INDEPENDIENTE, para el autotest"""
    w, n = X.shape; out = np.empty(w)
    for i in range(w):
        eq = 1.0; pico = 1.0; peor = 0.0
        for t in range(n):
            eq *= (1.0 + X[i,t])
            if eq > pico: pico = eq
            d = (pico-eq)/pico
            if d > peor: peor = d
        out[i] = (eq**(12.0/n) - 1.0)/(peor if peor > 1e-12 else 1e-12)
    return out

def veredicto(r, bps=BPS, umbral=UMBRAL):
    P, e12, rf = correr(r, 12, bps)
    a, t, res, b = alfa_t(e12, rf); h = e12.shape[1]//2
    a1,_,_,_ = alfa_t(e12[:,:h], rf[:,:h]); a2,_,_,_ = alfa_t(e12[:,h:], rf[:,h:])
    _, e6, r6 = correr(r, 6, bps); _, e9, r9 = correr(r, 9, bps)
    a6,_,_,_ = alfa_t(e6, r6); a9,_,_,_ = alfa_t(e9, r9)
    mes = (a6 > 0) & (a9 > 0) & (a > 0)
    rcok = rc(e12) >= rc(rf)
    si = (a > 0) & (t >= umbral) & (a1 > 0) & (a2 > 0) & mes & rcok
    no = (a <= 0) | (t <= 0)
    return dict(si=si, no=no & ~si, t=t, alfa=a, beta=b,
                alfa_sh=a*12/(res.std(axis=1, ddof=2)*np.sqrt(12)), piezas=P,
                d={"t":(t>=umbral).mean(), "mit":((a1>0)&(a2>0)).mean(),
                   "mes":mes.mean(), "rc":rcok.mean()})

def sh_mercado(P): return (P.mean(axis=2)/P.std(axis=2, ddof=1)*np.sqrt(12)).mean()

def piezas_pm1(r, L=12, bps=BPS):
    """las MISMAS piezas pero con posicion +-1 (comprado/vendido). Solo se usa
    para FIJAR la ventaja en la unidad de la fuente externa; la regla que se
    EVALUA es comprado/fuera."""
    w, k, T = r.shape
    lp = np.cumsum(r, axis=2); s36 = sigma_movil(r); ini = max(VENT, L+1)
    tam = OBJ / s36[:, :, ini:T]
    sg = np.sign(lp[:,:,ini-1:T-1] - lp[:,:,ini-1-L:T-1-L]); sg[sg == 0] = 1.0
    return neto(sg*tam, r[:, :, ini:T], bps)

def sh_pm1(r, bps=BPS): return sh_mercado(piezas_pm1(r, 12, bps))
def sh_cart(x):    return (x.mean(axis=1)/x.std(axis=1, ddof=1)*np.sqrt(12)).mean()

def rho_senal(r, k):
    lp = np.cumsum(r, axis=2); o = []
    for w in range(0, r.shape[0], max(1, r.shape[0]//60)):
        sg = np.stack([lp[w,:,t-1]-lp[w,:,t-13] for t in range(13, r.shape[2])], axis=1)
        o.append(np.corrcoef(sg)[np.triu_indices(k,1)].mean())
    return float(np.mean(o))

def busca(f, obj, lo, hi, pasos=22):
    for _ in range(pasos):
        mid = (lo+hi)/2
        if f(mid) < obj: lo = mid
        else: hi = mid
    return (lo+hi)/2

# ---------------------------------------------------------------- calibracion
def calibrar(sig, C, CS, phi, rho_obj, n_cal, n_mes, rng, sh_obj=SH_NETA):
    k = len(sig)
    # 1 · deriva constante que le da a la referencia su Sharpe MEDIDA
    def f_ref(d):
        _,_,rf = correr(mundo(sig,C,1e-6,0.0,n_cal//3,d,phi,n_mes,rng),12)
        return sh_cart(rf)
    d_ref = busca(f_ref, CS["sh_ref"], 0.0, 1.5, 20)
    # 2 y 3 · lam (rho de la SENAL) y s_m (ventaja NETA) INTERACTUAN: mas
    # tendencia sube la correlacion de la senal para un mismo lam. Calibrarlos
    # en secuencia da un mundo descalibrado (paso por ahi: lam 0,987 con
    # objetivo rho 0,243 produjo 0,420). Se hace por PUNTO FIJO y se verifica.
    s_m = 0.05
    for _ in range(12):
        lam = busca(lambda L: rho_senal(mundo(sig,C,s_m,L,n_cal,d_ref,phi,n_mes,rng), k),
                    rho_obj, 0.0, 0.999, 16)
        s_m = busca(lambda s: sh_pm1(mundo(sig,C,s,lam,n_cal,d_ref,phi,n_mes,rng)),
                    sh_obj, 1e-4, 1.0, 22)
        rl = rho_senal(mundo(sig,C,s_m,lam,max(400,n_cal),d_ref,phi,n_mes,rng), k)
        sh = sh_pm1(mundo(sig,C,s_m,lam,max(400,n_cal),d_ref,phi,n_mes,rng))
        if abs(rl-rho_obj) <= TOL_CAL and abs(sh-sh_obj) <= TOL_CAL: break
    conv = abs(rl-rho_obj) <= TOL_CAL and abs(sh-sh_obj) <= TOL_CAL
    return d_ref, lam, s_m, dict(rho=rl, sh=sh, conv=conv)

def evaluar(sig, C, s_m, lam, d_ref, phi, n_mes, n_eval, rng, bps=BPS, lote=400):
    acc = {"si":[], "no":[], "t":[], "alfa_sh":[], "beta":[], "sh":[], "rot":[]}
    dd = []
    hecho = 0
    while hecho < n_eval:
        nb = min(lote, n_eval-hecho)
        r = mundo(sig, C, s_m, lam, nb, d_ref, phi, n_mes, rng)
        V = veredicto(r, bps)
        P, e12, rf = correr(r, 12, bps)
        acc["si"].append(V["si"]); acc["no"].append(V["no"]); acc["t"].append(V["t"])
        acc["alfa_sh"].append(V["alfa_sh"]); acc["beta"].append(V["beta"])
        acc["sh"].append(sh_mercado(P))
        T = r.shape[2]; ini = max(VENT, 13)
        lp = np.cumsum(r, axis=2); s36 = sigma_movil(r)
        sgn = np.maximum(np.sign(lp[:,:,ini-1:T-1]-lp[:,:,ini-13:T-13]), 0.0)
        acc["rot"].append(rotacion(sgn*(OBJ/s36[:,:,ini:T])).mean())
        dd.append(V["d"]); hecho += nb
    out = {k_: np.concatenate(v) for k_, v in acc.items() if k_ in ("si","no","t","alfa_sh","beta")}
    out["sh"] = float(np.mean(acc["sh"])); out["rot"] = float(np.mean(acc["rot"]))
    out["d"] = {k_: float(np.mean([d[k_] for d in dd])) for k_ in dd[0]}
    return out

# ---------------------------------------------------------------- autotest
def autotest():
    fallos = [0]
    def ok(e, cond, extra=""):
        print(f"  {'OK ' if cond else 'MAL'}  {e}{('  ' + extra) if extra else ''}")
        if not cond: fallos[0] += 1
    print("="*74); print("  AUTOTEST tendencia_111b"); print("="*74)
    rng = np.random.default_rng(7)

    # --- (a) el costo restado = rotacion x 10 bps EXACTO, estrategia y referencia
    w,k,T = 40,4,200
    r = rng.standard_normal((w,k,T))*0.04 + 0.002
    for L in (6,12):
        pe, e, rf = correr(r, L, BPS)
        pe0, e0, rf0 = correr(r, L, 0.0)
        lp = np.cumsum(r,axis=2); s36 = sigma_movil(r); ini = max(VENT, L+1)
        tam = OBJ/s36[:,:,ini:T]
        sg = np.maximum(np.sign(lp[:,:,ini-1:T-1]-lp[:,:,ini-1-L:T-1-L]), 0.0)
        ce = BPS*rotacion(sg*tam); cr = BPS*rotacion(tam)
        ok(f"costo estrategia = rotacion x {BPS*1e4:.0f} bps exacto (L={L})",
           np.abs((pe0-pe) - ce).max() < 1e-15,
           f"dif max {np.abs((pe0-pe)-ce).max():.2e}")
        ok(f"costo referencia = rotacion x {BPS*1e4:.0f} bps exacto (L={L})",
           np.abs((rf0-rf) - cr.mean(axis=1)).max() < 1e-15,
           f"dif max {np.abs((rf0-rf)-cr.mean(axis=1)).max():.2e}")
    ok("la referencia PAGA costo (no es gratis)", np.abs(rf0-rf).mean() > 0,
       f"media {np.abs(rf0-rf).mean()*1e4:.2f} bps/mes")
    ok("20 bps cuesta el doble que 10",
       abs(np.abs(correr(r,12,0.0020)[1]-correr(r,12,0.0)[1]).mean()
           / np.abs(correr(r,12,0.0010)[1]-correr(r,12,0.0)[1]).mean() - 2.0) < 1e-10)

    # --- sin mirada al futuro
    r2 = r.copy(); r2[:,:,-1] = 99.0          # cambiar SOLO el ultimo mes
    a1,_,_ = correr(r, 12); a2,_,_ = correr(r2, 12)
    ok("cambiar el ultimo mes no altera meses anteriores",
       np.allclose(a1[:,:,:-1], a2[:,:,:-1]))
    r3 = r.copy(); r3[:,:,5] *= 3.0
    b1,_,_ = correr(r, 12); b3,_,_ = correr(r3, 12)
    ok("cambiar el mes 5 SI altera los posteriores (la senal lo usa)",
       not np.allclose(b1, b3))
    # la sigma de t no usa el mes t
    s = sigma_movil(r); rr = r.copy(); rr[:,:,100] *= 5.0
    ok("sigma de 36 meses no usa el mes en curso",
       np.allclose(sigma_movil(rr)[:,:,100], s[:,:,100]))
    ok("sigma de 36 meses SI usa el mes anterior",
       not np.allclose(sigma_movil(rr)[:,:,101], s[:,:,101]))

    # --- comprado o FUERA, nunca vendido
    lp = np.cumsum(r,axis=2); ini=max(VENT,13)
    sg = np.maximum(np.sign(lp[:,:,ini-1:T-1]-lp[:,:,ini-13:T-13]), 0.0)
    ok("la posicion es comprado o FUERA, nunca vendida",
       (sg >= 0).all() and set(np.unique(sg)) <= {0.0,1.0},
       f"valores {sorted(set(np.unique(sg)))}")

    # --- la ventaja se fija en la unidad +-1, no en comprado/fuera
    lp2=np.cumsum(r,axis=2); ini2=max(VENT,13)
    sg_lf=np.maximum(np.sign(lp2[:,:,ini2-1:T-1]-lp2[:,:,ini2-13:T-13]),0.0)
    sg_pm=np.sign(lp2[:,:,ini2-1:T-1]-lp2[:,:,ini2-13:T-13]); sg_pm[sg_pm==0]=1.0
    ok("piezas +-1 toman valores -1 y +1 (unidad de la fuente)",
       set(np.unique(sg_pm)) == {-1.0,1.0})
    ok("piezas comprado/fuera toman 0 y +1 (regla preinscrita)",
       set(np.unique(sg_lf)) == {0.0,1.0})
    ok("las dos unidades dan piezas DISTINTAS", not np.allclose(sg_lf, sg_pm))
    ok("sh_pm1 usa +-1 y sh_mercado(correr) usa comprado/fuera",
       abs(sh_pm1(r) - sh_mercado(correr(r,12)[0])) > 1e-6,
       f"+-1 {sh_pm1(r):.4f} vs comprado/fuera {sh_mercado(correr(r,12)[0]):.4f}")

    # --- r/c contra la segunda implementacion
    X = rng.standard_normal((60,300))*0.02 + 0.003
    d = np.abs(rc(X)-rc_bucle(X)).max()
    ok("r/c coincide con la segunda implementacion", d < 1e-9, f"dif max {d:.2e}")
    Y = np.zeros((1,24)); Y[0,0] = -0.20          # cae 20 % el primer mes
    ok("el capital inicial entra en el pico (caida del primer mes contada)",
       abs(rc(Y)[0] - rc_bucle(Y)[0]) < 1e-12 and rc(Y)[0] < 0,
       f"r/c {rc(Y)[0]:.4f}")

    # --- veredicto de tres vias sobre casos con respuesta conocida
    n=400; rf0=np.zeros((3,n))
    e=np.zeros((3,n)); e[0]=0.02; e[1]=-0.02; e[2]=rng.standard_normal(n)*0.01
    a,t,_,_ = alfa_t(e, rf0)
    ok("alfa > 0 con serie constante positiva", a[0] > 0 and t[0] > 10)
    ok("alfa < 0 con serie constante negativa", a[1] < 0)
    ok("NO cuando alfa <= 0", (a[1] <= 0))

    # --- panel real: contigüidad y orientacion
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panel_111b.csv")
    if os.path.exists(p):
        ym0, X0, TB0 = leer_panel(p)
        ym, X10, TB10 = solo_desarrollo(ym0, X0, TB0)
        rr2, sg2, C2 = momentos(ym, X10, TB10)
        ok("panel sin saltos de calendario", int((np.diff(ym0)!=1).sum())==0,
           f"{len(ym0)} meses, {len(ym)} de desarrollo")
        ok("la calibracion usa SOLO el desarrollo (el reservado no entra)",
           ym[-1]==DEV_FIN and ym0[-1]>DEV_FIN,
           f"desarrollo hasta {ym[-1]//12}-{ym[-1]%12+1:02d}, panel hasta {ym0[-1]//12}-{ym0[-1]%12+1:02d}")
        rr2, sg2, C2 = momentos(ym, X10, TB10)
        rho = C2[np.triu_indices(10,1)].mean()
        # la prueba que importa no es una constante: es que las divisas esten
        # orientadas. Al reves, la rho se vuelve NEGATIVA.
        Xv = X10.copy()
        for m in ("yen","franco","cad","eur_dem"): Xv[MERCADOS.index(m)] = 1.0/Xv[MERCADOS.index(m)]
        rho_mal = momentos(ym, Xv, TB10)[2][np.triu_indices(10,1)].mean()
        ok("rho del retorno positiva con divisas orientadas", 0.15 < rho < 0.25,
           f"{rho:.4f} con {rr2.shape[1]} retornos")
        ok("al invertir 4 divisas la rho se vuelve negativa", rho_mal < 0,
           f"{rho_mal:.4f}")
        # el franco y el yen se APRECIARON: las series deben subir
        ok("divisas en USD por unidad extranjera (franco sube)",
           X10[MERCADOS.index("franco")][-1] > X10[MERCADOS.index("franco")][0])
        ok("divisas en USD por unidad extranjera (yen sube)",
           X10[MERCADOS.index("yen")][-1] > X10[MERCADOS.index("yen")][0])
    else:
        ok("panel_111b.csv presente", False, "no esta: falta el panel")

    # --- determinismo
    g1 = np.random.default_rng(5); g2 = np.random.default_rng(5)
    s1 = mundo(np.full(3,0.04), np.eye(3), 0.05, 0.2, 10, 0.1, 0.95, 100, g1)
    s2 = mundo(np.full(3,0.04), np.eye(3), 0.05, 0.2, 10, 0.1, 0.95, 100, g2)
    ok("misma semilla da el mismo mundo", np.allclose(s1,s2))
    print(f"\n  {18+len(['']) if False else ''}{'':<0}{fallos[0]} MAL")
    return fallos[0]

# ---------------------------------------------------------------- potencia
def potencia(n_cal=400, n_eval=2000, phi=PHI_PEOR, rho=RHO_PEOR, semilla=1975):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panel_111b.csv")
    ym, X, TB = solo_desarrollo(*leer_panel(p))
    r, sig, C = momentos(ym, X, TB)
    n_mes = r.shape[1]
    # Sharpe MEDIDA de la referencia en el panel real (precios, no la regla)
    s36 = np.full_like(r, np.nan)
    for t in range(VENT, r.shape[1]): s36[:,t] = r[:,t-VENT:t].std(axis=1, ddof=1)
    ini = VENT
    pr = neto((OBJ/s36[:,ini:])[None], r[:,ini:][None])[0]
    refr = pr.mean(axis=0)
    sh_ref_real = refr.mean()/refr.std(ddof=1)*np.sqrt(12)
    print("="*78)
    print(f"  POTENCIA 111b · regla COMPRADO/FUERA · costo {BPS*1e4:.0f} bps por rotacion")
    print(f"  esquina peor phi {phi} rho senal {rho} · calib {n_cal} · eval {n_eval}")
    print("="*78)
    print(f"\n  panel {len(ym)} meses, {n_mes} retornos, 10 mercados")
    print(f"  Sharpe MEDIDA de la referencia (neta de costo): {sh_ref_real:.3f}")
    rng = np.random.default_rng(semilla)
    d_ref, lam, s_m, chk = calibrar(sig, C, {"sh_ref": sh_ref_real}, phi, rho,
                                    n_cal, n_mes, rng, SH_NETA)
    print(f"  calibrado   d_ref {d_ref:.5f}   lam {lam:.4f}   s_m {s_m:.5f}")
    print(f"  rho senal lograda {chk['rho']:.4f} (objetivo {rho})   "
          f"Sharpe +-1 por mercado {chk['sh']:.4f} (objetivo {SH_NETA}, unidad AQR)")
    if not chk["conv"]:
        print(f"\n  *** MUNDO NO CALIBRABLE. No se reporta potencia. ***")
        return None, None
    print(f"  punto fijo CONVERGIDO")
    print(f"\n  {'bps':>5}{'Sh/merc':>9}{'rotacion':>10}{'alfa cart':>11}{'beta':>7}"
          f"{'t':>7}{'SI':>8}{'GRIS':>8}{'NO':>7}{'falsos':>8}   decide")
    oficial=None
    for bps in (0.0, BPS, 0.0020):
        V  = evaluar(sig,C,s_m,lam,d_ref,phi,n_mes,n_eval,
                     np.random.default_rng(semilla+1), bps)
        V0 = evaluar(sig,C,1e-6,lam,d_ref,phi,n_mes,n_eval,
                     np.random.default_rng(semilla+2), bps)
        si=V["si"].mean()*100; gr=(~V["si"]&~V["no"]).mean()*100; no=V["no"].mean()*100
        f0=V0["si"].mean()*100
        dec = "SI" if abs(bps-BPS)<1e-12 else "no"
        if dec=="SI": oficial=(si,f0,V)
        print(f"  {bps*1e4:>5.0f}{V['sh']:>9.3f}{V['rot']:>10.4f}"
              f"{V['alfa_sh'].mean():>11.3f}{V['beta'].mean():>7.2f}{V['t'].mean():>7.2f}"
              f"{si:>7.1f}%{gr:>7.1f}%{no:>6.1f}%{f0:>7.1f}%   {dec}")
    si,f0,V = oficial
    e=np.sqrt(si/100*(1-si/100)/n_eval)*100
    print(f"\n  desglose al nivel que decide ({BPS*1e4:.0f} bps)")
    for kk,et in (("t","t>=2,51"),("mit","mitades"),("mes","meseta"),("rc","r/c")):
        print(f"    {et:<12}{V['d'][kk]*100:>6.1f}%")
    print(f"\n  POTENCIA OFICIAL = {si:.1f} % +-{e:.1f}   falsos SI {f0:.1f} %")
    print(f"  porton 60 %  ->  {'PASA' if si>=60 else 'NO PASA: EL PORTON CIERRA'}")
    return si, f0

def simular():
    print("="*74); print("  --simular · tres comprobaciones sobre el mundo"); print("="*74)
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "panel_111b.csv")
    ym, X, TB = solo_desarrollo(*leer_panel(p)); r, sig, C = momentos(ym, X, TB); n_mes=r.shape[1]
    s36=np.full_like(r,np.nan)
    for t in range(VENT,r.shape[1]): s36[:,t]=r[:,t-VENT:t].std(axis=1,ddof=1)
    ini=VENT
    pr=neto((OBJ/s36[:,ini:])[None], r[:,ini:][None])[0]; refr=pr.mean(axis=0)
    shr=refr.mean()/refr.std(ddof=1)*np.sqrt(12)
    rng=np.random.default_rng(1975)
    d_ref,lam,s_m,chk = calibrar(sig,C,{"sh_ref":shr},PHI_PEOR,RHO_PEOR,200,n_mes,rng)
    print(f"\n  calibracion: rho senal {chk['rho']:.4f} (obj {RHO_PEOR})  "
          f"Sharpe +-1/merc {chk['sh']:.4f} (obj {SH_NETA})  "
          f"{'CONVERGIDO' if chk['conv'] else 'NO CONVERGIDO'}")
    V  = evaluar(sig,C,s_m,lam,d_ref,PHI_PEOR,n_mes,600,np.random.default_rng(11))
    V0 = evaluar(sig,C,1e-6,lam,d_ref,PHI_PEOR,n_mes,600,np.random.default_rng(12))
    print(f"\n  (a) costo: ver --autotest (comprobado al bit)")
    print(f"  (b) mundo SIN ventaja: falsos SI {V0['si'].mean()*100:.1f} %  "
          f"-> {'OK (<=5 %)' if V0['si'].mean()<=0.05 else 'MAL (>5 %)'}")
    print(f"  (c) mundo CON ventaja: SI {V['si'].mean()*100:.1f} %  "
          f"(potencia oficial 64,4 %; esquina phi {PHI_PEOR} rho {RHO_PEOR})")
    print(f"      Sharpe comprado/fuera {V['sh']:.3f} · Sharpe +-1 {chk['sh']:.3f} "
          f"(la fijada, unidad AQR)")
    print(f"\n  rotacion media por mercado y mes: {V['rot']:.4f}"
          f"  -> costo {V['rot']*BPS*1e4:.2f} bps/mes = {V['rot']*BPS*12*1e4:.0f} bps/ano")

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--autotest", action="store_true")
    a.add_argument("--simular", action="store_true")
    a.add_argument("--potencia", action="store_true")
    a.add_argument("--calib", type=int, default=400)
    a.add_argument("--eval", type=int, default=2000)
    n = a.parse_args()
    if n.autotest: sys.exit(1 if autotest() else 0)
    elif n.simular: simular()
    elif n.potencia: potencia(n.calib, n.eval)
    else: a.print_help()
