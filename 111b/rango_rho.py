# -*- coding: utf-8 -*-
"""DE DONDE SALE EL RANGO DE rho DE LA REJILLA (0,222 a 0,264).
Lo que use fue un error estandar de Fisher con n = 539 meses. Pero la senal
12-1 se SOLAPA 11 de 12 meses, asi que 539 meses NO son 539 observaciones
independientes. Se mide con bloques anuales sobre el dato real (solo precios)."""
import sys, numpy as np
sys.path.insert(0,"/tmp/claude-0/-home-claude/ed80f7a1-0a09-5942-8460-efa74b38a33a/scratchpad/p111b")
import tendencia_111b as M
ym,X,TB = M.solo_desarrollo(*M.leer_panel("panel_111b.csv"))
r,sig,C = M.momentos(ym,X,TB)
lp = np.cumsum(r,axis=1)
S = np.stack([lp[:,t-1]-lp[:,t-13] for t in range(13,r.shape[1])],axis=1)  # senal 12-1
k,n = S.shape
rho0 = np.corrcoef(S)[np.triu_indices(k,1)].mean()
print(f"  senal 12-1: {k} mercados x {n} meses")
print(f"  rho media medida = {rho0:.4f}")

print(f"\n1 · LO QUE USE (y por que esta mal)")
se_f=(1-rho0**2)/np.sqrt(n-3)
print(f"   Fisher con n={n} meses:           se por pareja {se_f:.4f}")
print(f"   dividido por sqrt(45/3)=sqrt(15): se de la media {se_f/np.sqrt(15):.4f}")
print(f"   rango usado = {rho0:.3f} +- 2x{se_f/np.sqrt(15):.4f} -> "
      f"{rho0-2*se_f/np.sqrt(15):.3f} a {rho0+2*se_f/np.sqrt(15):.3f}")
print(f"   PROBLEMA 1: la senal 12-1 comparte 11 de 12 meses. Su AR(1) es ~0,93.")
print(f"               539 meses no son 539 observaciones independientes.")
print(f"   PROBLEMA 2: el sqrt(15) fue un ajuste a ojo (45 parejas / 3), no una")
print(f"               derivacion. No esta justificado en ninguna parte.")

print(f"\n2 · MEDIDO CON BLOQUES SOBRE EL DATO REAL")
rg=np.random.default_rng(4)
for B,et in ((12,"bloques de 12 meses"),(24,"bloques de 24 meses"),(60,"bloques de 60 meses")):
    out=[]
    nb=n//B
    for _ in range(3000):
        pick=rg.integers(0,nb,nb)
        idx=np.concatenate([np.arange(p*B,(p+1)*B) for p in pick])
        Cb=np.corrcoef(S[:,idx])
        out.append(Cb[np.triu_indices(k,1)].mean())
    out=np.array(out)
    print(f"   {et:<22}se de la media {out.std(ddof=1):.4f}   "
          f"rango +-2se -> {rho0-2*out.std(ddof=1):.3f} a {rho0+2*out.std(ddof=1):.3f}")
print(f"\n3 · CONCLUSION")
o=[]
nb=n//24
for _ in range(3000):
    pick=rg.integers(0,nb,nb)
    idx=np.concatenate([np.arange(p*24,(p+1)*24) for p in pick])
    o.append(np.corrcoef(S[:,idx])[np.triu_indices(k,1)].mean())
se_real=np.std(o,ddof=1)
print(f"   se honesta (bloques de 24 meses) {se_real:.4f} contra {se_f/np.sqrt(15):.4f} que use")
print(f"   es {se_real/(se_f/np.sqrt(15)):.1f} veces mas grande")
print(f"   rango que DEBERIA cubrir la rejilla: {rho0-2*se_real:.3f} a {rho0+2*se_real:.3f}")
print(f"   rango que cubrio:                    0.222 a 0.264")
