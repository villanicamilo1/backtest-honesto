# -*- coding: utf-8 -*-
"""Punto 1: medir la CELDA OFICIAL (phi 0,98 · rho 0,341) a 0, 10 y 20 bps.
Mismo mundo, distinto costo cobrado. El 10 es el que decide (fijado antes)."""
import sys, numpy as np
sys.path.insert(0,"/tmp/claude-0/-home-claude/ed80f7a1-0a09-5942-8460-efa74b38a33a/scratchpad/p111b")
import tendencia_111b as M   # NO importar rejilla_111b: se ejecuta al importarse
PHI, RHO = 0.98, 0.341
LAM, S_M = 0.7326, 0.03640          # calibrados en celda_peor.py, convergidos
ym,X,TB=M.solo_desarrollo(*M.leer_panel("panel_111b.csv"))
r,sig,C=M.momentos(ym,X,TB); N=r.shape[1]
s36=np.full_like(r,np.nan)
for t in range(M.VENT,r.shape[1]): s36[:,t]=r[:,t-M.VENT:t].std(axis=1,ddof=1)
pr=M.neto((M.OBJ/s36[:,M.VENT:])[None], r[:,M.VENT:][None])[0]; rfr=pr.mean(axis=0)
SHR=rfr.mean()/rfr.std(ddof=1)*np.sqrt(12)
rng=np.random.default_rng(980341)
d_ref=M.busca(lambda d: M.sh_cart(M.correr(M.mundo(sig,C,1e-6,0.0,300,d,PHI,N,rng),12)[2]),
              SHR,0.0,1.5,24)
print(f"  CELDA OFICIAL phi {PHI} rho {RHO}  ·  lam {LAM}  s_m {S_M}")
print(f"  mismo mundo, distinto costo cobrado. 2000 mundos.\n")
print(f"  {'bps':>5}{'Sh+-1':>8}{'Sh c/f':>8}{'rotac':>8}{'alfa':>8}{'beta':>6}"
      f"{'t':>6}{'SI':>8}{'GRIS':>8}{'NO':>6}   porton")
def ev(bps, n=2000, lote=400):
    si=[];no=[];t=[];al=[];be=[];h=0
    while h<n:
        nb=min(lote,n-h)
        rr=M.mundo(sig,C,S_M,LAM,nb,d_ref,PHI,N,np.random.default_rng(4242+h))
        V=M.veredicto(rr,bps)
        si.append(V["si"]);no.append(V["no"]);t.append(V["t"])
        al.append(V["alfa_sh"]);be.append(V["beta"]);h+=nb
    si=np.concatenate(si);no=np.concatenate(no)
    rr=M.mundo(sig,C,S_M,LAM,400,d_ref,PHI,N,np.random.default_rng(777))
    return (si.mean(),(~si&~no).mean(),no.mean(),np.concatenate(t).mean(),
            np.concatenate(al).mean(),np.concatenate(be).mean(),
            M.sh_pm1(rr,bps), M.sh_mercado(M.correr(rr,12,bps)[0]),
            M.rotacion(np.maximum(np.sign(np.cumsum(rr,axis=2)[:,:,35:-1]
              -np.cumsum(rr,axis=2)[:,:,23:-13]),0.0)).mean())
for bps in (0.0, 0.0010, 0.0020):
    s,g,n_,t,a,b,s1,sf,rot = ev(bps)
    e=np.sqrt(s*(1-s)/2000)*100
    print(f"  {bps*1e4:>5.0f}{s1:>8.3f}{sf:>8.3f}{rot:>8.4f}{a:>8.3f}{b:>6.2f}"
          f"{t:>6.2f}{s*100:>7.1f}%{g*100:>7.1f}%{n_*100:>5.1f}%   "
          f"{'PASA' if s*100>=60 else 'NO PASA'} ({s*100:.1f}±{e:.1f})"
          + ("   <- DECIDE" if abs(bps-0.0010)<1e-12 else ""))
