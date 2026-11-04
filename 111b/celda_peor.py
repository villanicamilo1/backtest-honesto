# -*- coding: utf-8 -*-
"""La celda (phi 0,98 · rho 0,341) quedo NO CALIBRABLE por 0,0073, no por ser
imposible. Es la esquina que seria la PEOR, asi que excluirla por una
tolerancia seria la tolerancia favoreciendo a la estrategia.
Se reintenta con mas mundos de calibracion y mas rondas."""
import sys, numpy as np
sys.path.insert(0,"/tmp/claude-0/-home-claude/ed80f7a1-0a09-5942-8460-efa74b38a33a/scratchpad/p111b")
import tendencia_111b as M
import rejilla_111b as R
PHI, RHO = 0.98, 0.341
ym,X,TB=M.solo_desarrollo(*M.leer_panel("panel_111b.csv"))
r,sig,C=M.momentos(ym,X,TB); N=r.shape[1]
s36=np.full_like(r,np.nan)
for t in range(M.VENT,r.shape[1]): s36[:,t]=r[:,t-M.VENT:t].std(axis=1,ddof=1)
pr=M.neto((M.OBJ/s36[:,M.VENT:])[None], r[:,M.VENT:][None])[0]; rfr=pr.mean(axis=0)
SHR=rfr.mean()/rfr.std(ddof=1)*np.sqrt(12)
print(f"  REINTENTO de la celda phi {PHI} rho {RHO}")
print(f"  Sharpe ref objetivo {SHR:.4f}")
rng=np.random.default_rng(980341)
d_ref=M.busca(lambda d: M.sh_cart(M.correr(M.mundo(sig,C,1e-6,0.0,300,d,PHI,N,rng),12)[2]),
              SHR,0.0,1.5,24)
print(f"\n  {'ronda':>6}{'lam':>9}{'s_m':>9}{'rho logr':>10}{'Sh+-1':>8}  estado")
s_m=0.10
for ronda in range(25):
    lam=M.busca(lambda L: M.rho_senal(M.mundo(sig,C,s_m,L,1500,d_ref,PHI,N,rng),10),
                RHO,0.0,0.999,22)
    s_m=M.busca(lambda s: R.sh_pm1(M.mundo(sig,C,s,lam,1500,d_ref,PHI,N,rng)),
                0.24,1e-4,1.0,24)
    rl=M.rho_senal(M.mundo(sig,C,s_m,lam,1500,d_ref,PHI,N,rng),10)
    sh=R.sh_pm1(M.mundo(sig,C,s_m,lam,1500,d_ref,PHI,N,rng))
    ok=abs(rl-RHO)<=0.005 and abs(sh-0.24)<=0.005
    if ronda<6 or ok:
        print(f"  {ronda+1:>6}{lam:>9.4f}{s_m:>9.5f}{rl:>10.4f}{sh:>8.4f}  "
              f"{'CONVERGIDO' if ok else ''}")
    if ok: break
if not ok:
    print(f"  ... 25 rondas sin converger: lam {lam:.4f} rho {rl:.4f} Sh {sh:.4f}")
    print(f"  dif rho {abs(rl-RHO):.4f}  dif Sh {abs(sh-0.24):.4f}  (tolerancia 0,005)")
print(f"\n  EVALUACION, 2000 mundos")
E=R.evaluar(sig,C,s_m,lam,d_ref,PHI,2000,4242)
E0=R.evaluar(sig,C,1e-6,lam,d_ref,PHI,600,8484)
print(f"    alfa {E['alfa']:.3f}  beta {E['beta']:.2f}  t {E['t']:.2f}")
print(f"    SI {E['si']*100:.1f}%  GRIS {E['gris']*100:.1f}%  NO {E['no']*100:.1f}%"
      f"   falsos SI {E0['si']*100:.1f}%")
print(f"    desglose  t {E['d']['t']*100:.1f}% · mitades {E['d']['mit']*100:.1f}%"
      f" · meseta {E['d']['mes']*100:.1f}% · r/c {E['d']['rc']*100:.1f}%")
e=np.sqrt(E['si']*(1-E['si'])/2000)*100
print(f"\n    {E['si']*100:.1f} % +-{e:.1f}   porton 60 %  ->  "
      f"{'PASA' if E['si']*100>=60 else 'NO PASA'}")
print(f"    {'CALIBRADA: entra en la decision' if ok else 'NO CALIBRABLE aun'}")
