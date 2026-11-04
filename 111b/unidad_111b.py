# -*- coding: utf-8 -*-
"""Sobre QUE unidad se fijo la ventaja 0,24, y que pasa si se fija en la unidad
que mide la fuente externa (AQR: regla +-1, comprado/vendido).

No toca dato real. Solo mundos. Se guarda con su salida (trampa 41).
"""
import sys, numpy as np
sys.path.insert(0,"/tmp/claude-0/-home-claude/ed80f7a1-0a09-5942-8460-efa74b38a33a/scratchpad/p111b")
import tendencia_111b as M

def correr_pm1(r, L=12, bps=M.BPS):
    """la MISMA mecanica, pero posicion +-1 (comprado/vendido): la unidad de AQR."""
    w,k,T = r.shape
    lp=np.cumsum(r,axis=2); s36=M.sigma_movil(r); ini=max(M.VENT,L+1)
    tam=M.OBJ/s36[:,:,ini:T]
    sg=np.sign(lp[:,:,ini-1:T-1]-lp[:,:,ini-1-L:T-1-L]); sg[sg==0]=1.0   # SIN el max(.,0)
    rr=r[:,:,ini:T]
    pe=M.neto(sg*tam,rr,bps); pr=M.neto(tam,rr,bps)
    return pe, pe.mean(axis=1), pr.mean(axis=1)

def veredicto_pm1(r, bps=M.BPS, umbral=M.UMBRAL):
    P,e12,rf = correr_pm1(r,12,bps)
    a,t,res,b = M.alfa_t(e12,rf); h=e12.shape[1]//2
    a1,_,_,_=M.alfa_t(e12[:,:h],rf[:,:h]); a2,_,_,_=M.alfa_t(e12[:,h:],rf[:,h:])
    _,e6,r6=correr_pm1(r,6,bps); _,e9,r9=correr_pm1(r,9,bps)
    a6,_,_,_=M.alfa_t(e6,r6); a9,_,_,_=M.alfa_t(e9,r9)
    mes=(a6>0)&(a9>0)&(a>0); rcok=M.rc(e12)>=M.rc(rf)
    si=(a>0)&(t>=umbral)&(a1>0)&(a2>0)&mes&rcok; no=(a<=0)|(t<=0)
    return dict(si=si,no=no&~si,t=t,beta=b,
                alfa_sh=a*12/(res.std(axis=1,ddof=2)*np.sqrt(12)),
                d={"t":(t>=umbral).mean(),"mit":((a1>0)&(a2>0)).mean(),
                   "mes":mes.mean(),"rc":rcok.mean()})

ym,X,TB = M.solo_desarrollo(*M.leer_panel("panel_111b.csv"))
r,sig,C = M.momentos(ym,X,TB); n=r.shape[1]
s36=np.full_like(r,np.nan)
for t in range(M.VENT,r.shape[1]): s36[:,t]=r[:,t-M.VENT:t].std(axis=1,ddof=1)
pr=M.neto((M.OBJ/s36[:,M.VENT:])[None], r[:,M.VENT:][None])[0]; rfr=pr.mean(axis=0)
SHR=rfr.mean()/rfr.std(ddof=1)*np.sqrt(12)
PHI,RHO = M.PHI_PEOR, M.RHO_PEOR
rng=np.random.default_rng(1975)
d_ref=M.busca(lambda d: M.sh_cart(M.correr(M.mundo(sig,C,1e-6,0.0,150,d,PHI,n,rng),12)[2]),
              SHR,0.0,1.5,20)

print("="*78)
print("  UNIDAD DE LA VENTAJA · esquina peor phi 0,85, rho senal 0,243")
print("="*78)
print(f"\n1 · EL MUNDO DEL 57,5 %: calibrado con la regla COMPRADO/FUERA = 0,24")
S_M_111b, LAM_111b = 0.13062, 0.2038          # del oficial sellado
rr=M.mundo(sig,C,S_M_111b,LAM_111b,400,d_ref,PHI,n,rng)
sh_lf=M.sh_mercado(M.correr(rr,12)[0]); sh_pm=M.sh_mercado(correr_pm1(rr,12)[0])
print(f"    Sharpe por mercado comprado/FUERA   {sh_lf:.4f}   <- a esto se calibro")
print(f"    Sharpe por mercado +-1 (unidad AQR) {sh_pm:.4f}   <- lo que AQR dice que es 0,24")
print(f"    el mundo tiene {(sh_pm/0.24-1)*100:+.0f} % mas tendencia de la que dice la fuente")

print(f"\n2 · MUNDO CORREGIDO: se fija +-1 = 0,24 (la unidad de la fuente)")
s_m2=0.05
for _ in range(5):
    lam2=M.busca(lambda L: M.rho_senal(M.mundo(sig,C,s_m2,L,400,d_ref,PHI,n,rng),10),
                 RHO,0.0,0.999,16)
    s_m2=M.busca(lambda s: M.sh_mercado(correr_pm1(M.mundo(sig,C,s,lam2,400,d_ref,PHI,n,rng),12)[0]),
                 0.24,1e-4,1.0,20)
rl=M.rho_senal(M.mundo(sig,C,s_m2,lam2,400,d_ref,PHI,n,rng),10)
rr2=M.mundo(sig,C,s_m2,lam2,400,d_ref,PHI,n,rng)
print(f"    lam {lam2:.4f}  s_m {s_m2:.5f}  rho senal lograda {rl:.4f} (obj {RHO})"
      f"  {'CONVERGIDO' if abs(rl-RHO)<=0.012 else 'NO CONVERGIDO'}")
print(f"    Sharpe +-1              {M.sh_mercado(correr_pm1(rr2,12)[0]):.4f}  (fijada)")
print(f"    Sharpe comprado/fuera   {M.sh_mercado(M.correr(rr2,12)[0]):.4f}  (resultado)")

print(f"\n3 · POTENCIA EN EL MUNDO CORREGIDO, 2000 mundos, 10 bps")
print(f"    {'regla':<22}{'alfa cart':>11}{'beta':>7}{'t':>7}{'SI':>8}{'GRIS':>8}"
      f"{'NO':>7}{'falsos':>8}")
for et,vf in (("comprado/FUERA (111b)",M.veredicto),("+-1 comprado/vendido",veredicto_pm1)):
    acc=[];acc0=[];ds=[];bs=[];ts=[];al=[];nos=[]
    for seed in range(5):
        g=np.random.default_rng(500+seed)
        rb=M.mundo(sig,C,s_m2,lam2,400,d_ref,PHI,n,g); V=vf(rb)
        g0=np.random.default_rng(900+seed)
        r0=M.mundo(sig,C,1e-6,lam2,400,d_ref,PHI,n,g0); V0=vf(r0)
        acc.append(V["si"]);acc0.append(V0["si"]);nos.append(V["no"])
        bs.append(V["beta"]);ts.append(V["t"]);al.append(V["alfa_sh"]);ds.append(V["d"])
    si=np.concatenate(acc); si0=np.concatenate(acc0); no=np.concatenate(nos)
    print(f"    {et:<22}{np.concatenate(al).mean():>11.3f}{np.concatenate(bs).mean():>7.2f}"
          f"{np.concatenate(ts).mean():>7.2f}{si.mean()*100:>7.1f}%"
          f"{(~si&~no).mean()*100:>7.1f}%{no.mean()*100:>6.1f}%{si0.mean()*100:>7.1f}%")
    print(f"      {'':<20}desglose  t {np.mean([d['t'] for d in ds])*100:.1f}%"
          f" · mitades {np.mean([d['mit'] for d in ds])*100:.1f}%"
          f" · meseta {np.mean([d['mes'] for d in ds])*100:.1f}%"
          f" · r/c {np.mean([d['rc'] for d in ds])*100:.1f}%"
          f"   (error +-{np.sqrt(si.mean()*(1-si.mean())/len(si))*100:.1f})")
