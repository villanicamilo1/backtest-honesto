# -*- coding: utf-8 -*-
"""REJILLA COMPLETA DEL PORTON 111b · unidad corregida.

Decidido el 2026-11-04: la 111b se reabre. El error era del INSUMO del porton
(la ventaja se calibro sobre comprado/fuera cuando la fuente externa mide +-1),
presente en el momento de medir, destapado por una revision que esperaba la
direccion contraria. Regla simetrica (trampa 27): se corrige en cualquier
direccion.

  ventaja  +-1 (comprado/vendido) = 0,24 de Sharpe por mercado, NETA despues
           de los 10 bps. Es la unidad que mide Hurst/Ooi/Pedersen (AQR).
  regla    la que se EVALUA sigue siendo COMPRADO/FUERA (preinscrita).
  costo    10 bps por unidad de rotacion, estrategia Y referencia.
  umbral   t >= 2,51
  oficial  esquina PEOR de la rejilla completa phi x rho, 2000 mundos.

  TOLERANCIA DE CALIBRACION (escrita antes de correr):
      rho de la senal  +-0,005     Sharpe +-1 por mercado  +-0,005
  Si el punto fijo no la cumple en 12 rondas -> la celda es NO CALIBRABLE y
  no entra en la decision.
"""
import sys, numpy as np
sys.path.insert(0,"/tmp/claude-0/-home-claude/ed80f7a1-0a09-5942-8460-efa74b38a33a/scratchpad/p111b")
import tendencia_111b as M

TOL_RHO = 0.005
TOL_SH  = 0.005
SH_PM1  = 0.24            # +-1, NETA de los 10 bps
N_CAL   = 600
N_EVAL  = 2000
N_NULO  = 600
RONDAS  = 12

def correr_pm1(r, L=12, bps=M.BPS):
    """misma mecanica, posicion +-1: la unidad de la fuente externa."""
    w,k,T=r.shape
    lp=np.cumsum(r,axis=2); s36=M.sigma_movil(r); ini=max(M.VENT,L+1)
    tam=M.OBJ/s36[:,:,ini:T]
    sg=np.sign(lp[:,:,ini-1:T-1]-lp[:,:,ini-1-L:T-1-L]); sg[sg==0]=1.0
    rr=r[:,:,ini:T]
    return M.neto(sg*tam,rr,bps), None, None

def sh_pm1(r): return M.sh_mercado(correr_pm1(r,12)[0])

def calibrar(sig,C,sh_ref,phi,rho_obj,rng):
    d_ref=M.busca(lambda d: M.sh_cart(M.correr(M.mundo(sig,C,1e-6,0.0,200,d,phi,N,rng),12)[2]),
                  sh_ref,0.0,1.5,22)
    s_m=0.05; lam=0.2
    for ronda in range(RONDAS):
        lam=M.busca(lambda L: M.rho_senal(M.mundo(sig,C,s_m,L,N_CAL,d_ref,phi,N,rng),10),
                    rho_obj,0.0,0.999,18)
        s_m=M.busca(lambda s: sh_pm1(M.mundo(sig,C,s,lam,N_CAL,d_ref,phi,N,rng)),
                    SH_PM1,1e-4,1.0,22)
        rl=M.rho_senal(M.mundo(sig,C,s_m,lam,N_CAL,d_ref,phi,N,rng),10)
        sh=sh_pm1(M.mundo(sig,C,s_m,lam,N_CAL,d_ref,phi,N,rng))
        if abs(rl-rho_obj)<=TOL_RHO and abs(sh-SH_PM1)<=TOL_SH:
            return d_ref,lam,s_m,rl,sh,ronda+1,True
    return d_ref,lam,s_m,rl,sh,RONDAS,False

def evaluar(sig,C,s_m,lam,d_ref,phi,n_tot,semilla,lote=400):
    si=[];no=[];t=[];al=[];be=[];dd=[];hecho=0
    while hecho<n_tot:
        nb=min(lote,n_tot-hecho)
        V=M.veredicto(M.mundo(sig,C,s_m,lam,nb,d_ref,phi,N,np.random.default_rng(semilla+hecho)))
        si.append(V["si"]);no.append(V["no"]);t.append(V["t"])
        al.append(V["alfa_sh"]);be.append(V["beta"]);dd.append(V["d"]);hecho+=nb
    si=np.concatenate(si);no=np.concatenate(no)
    return dict(si=si.mean(),gris=(~si&~no).mean(),no=no.mean(),
                t=np.concatenate(t).mean(),alfa=np.concatenate(al).mean(),
                beta=np.concatenate(be).mean(),
                d={k:float(np.mean([x[k] for x in dd])) for k in dd[0]})

ym,X,TB=M.solo_desarrollo(*M.leer_panel("panel_111b.csv"))
r,sig,C=M.momentos(ym,X,TB); N=r.shape[1]
s36=np.full_like(r,np.nan)
for t in range(M.VENT,r.shape[1]): s36[:,t]=r[:,t-M.VENT:t].std(axis=1,ddof=1)
pr=M.neto((M.OBJ/s36[:,M.VENT:])[None], r[:,M.VENT:][None])[0]; rfr=pr.mean(axis=0)
SHR=rfr.mean()/rfr.std(ddof=1)*np.sqrt(12)
# rho de la senal y su error estandar, MEDIDOS estrictamente dentro del
# desarrollo. El error sale de un bootstrap por BLOQUES de 24 meses sobre el
# dato real, porque la senal 12-1 solapa 11 de 12 meses (AR1 ~0,93) y los 526
# meses no son 526 observaciones independientes. El error de Fisher con n=526
# daba 0,0105, que es 3,8 veces demasiado chico (ver bitacora 27).
lp_=np.cumsum(r,axis=1)
S_=np.stack([lp_[:,t-1]-lp_[:,t-13] for t in range(13,r.shape[1])],axis=1)
RHO_MED=float(np.corrcoef(S_)[np.triu_indices(10,1)].mean())
_g=np.random.default_rng(4); _nb=S_.shape[1]//24; _o=[]
for _ in range(3000):
    _p=_g.integers(0,_nb,_nb)
    _i=np.concatenate([np.arange(q*24,(q+1)*24) for q in _p])
    _o.append(np.corrcoef(S_[:,_i])[np.triu_indices(10,1)].mean())
SE_RHO=float(np.std(_o,ddof=1))
RHOS=[round(RHO_MED-2*SE_RHO,3), round(RHO_MED,3), round(RHO_MED+2*SE_RHO,3)]
PHIS=[0.85,0.90,0.95,0.98]

print("="*96)
print("  REJILLA COMPLETA DEL PORTON 111b · ventaja +-1 = 0,24 NETA (unidad AQR)")
print(f"  regla evaluada COMPRADO/FUERA · 10 bps · t>=2,51 · {N_EVAL} mundos por celda")
print(f"  tolerancia rho +-{TOL_RHO}  Sharpe +-{TOL_SH}  ·  Sharpe ref medida {SHR:.3f}")
print(f"  rho senal medida {RHO_MED:.4f}  se por bloques de 24 meses {SE_RHO:.4f}")
print(f"  rejilla de rho = medida +-2se = {RHOS}")
print("="*96)
print(f"\n  {'phi':>5}{'rho obj':>9}{'lam':>8}{'rho logr':>10}{'Sh+-1':>8}{'rond':>6}"
      f"{'alfa':>8}{'beta':>6}{'t':>6}{'SI':>8}{'GRIS':>8}{'NO':>6}{'falsos':>8}  estado")
peor=(1e9,None); cells={}
for phi in PHIS:
    for rho in RHOS:
        rng=np.random.default_rng(int(phi*1000)+int(rho*1000))
        d_ref,lam,s_m,rl,sh,rd,ok = calibrar(sig,C,SHR,phi,rho,rng)
        if not ok:
            print(f"  {phi:>5.2f}{rho:>9.3f}{lam:>8.4f}{rl:>10.4f}{sh:>8.4f}{rd:>6}"
                  f"{'':>36}  NO CALIBRABLE, excluida")
            cells[(phi,rho)]=None; continue
        E=evaluar(sig,C,s_m,lam,d_ref,phi,N_EVAL,7000)
        E0=evaluar(sig,C,1e-6,lam,d_ref,phi,N_NULO,9000)
        print(f"  {phi:>5.2f}{rho:>9.3f}{lam:>8.4f}{rl:>10.4f}{sh:>8.4f}{rd:>6}"
              f"{E['alfa']:>8.3f}{E['beta']:>6.2f}{E['t']:>6.2f}{E['si']*100:>7.1f}%"
              f"{E['gris']*100:>7.1f}%{E['no']*100:>5.1f}%{E0['si']*100:>7.1f}%  OK")
        cells[(phi,rho)]=(E,E0)
        if E['si']<peor[0]: peor=(E['si'],(phi,rho,E,E0))
print(f"\n  celdas validas: {sum(1 for v in cells.values() if v)}/{len(cells)}")
p,(phi,rho,E,E0)=peor
err=np.sqrt(p*(1-p)/N_EVAL)*100
print(f"\n  ESQUINA PEOR DE LA REJILLA: phi {phi:.2f}, rho senal {rho:.3f}")
print(f"  desglose  t {E['d']['t']*100:.1f}% · mitades {E['d']['mit']*100:.1f}%"
      f" · meseta {E['d']['mes']*100:.1f}% · r/c {E['d']['rc']*100:.1f}%")
print(f"\n  POTENCIA OFICIAL = {p*100:.1f} % +-{err:.1f}    falsos SI {E0['si']*100:.1f} %")
print(f"  porton 60 %  ->  {'PASA' if p*100>=60 else 'NO PASA: EL PORTON CIERRA'}")
print(f"\n  ESTE NUMERO ES EL ULTIMO DEL PORTON. Si aparece otro error se corrige")
print(f"  con la misma regla simetrica (trampa 27) y queda escrito.")
