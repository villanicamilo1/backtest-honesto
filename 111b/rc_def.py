# -*- coding: utf-8 -*-
"""DEFINICION B · retorno/caida de la 111b, fijada antes de recalcular potencia.

  curva     eq_t = prod_{s<=t}(1 + r_s), eq_0 = 1      COMPUESTA
  retorno   CAGR = eq_n^(12/n) - 1
  caida     max_t (pico_t - eq_t)/pico_t                RELATIVA al pico
  razon     r/c = CAGR / caida_max
  referencia  mismos mercados, mismo tamano por sigma de 36 meses, SIEMPRE
              LARGA, misma ventana; en el mundo gana su Sharpe MEDIDA (0,345
              con 10 mercados sobre el panel 1975-2019)

Compuesta y no suma porque asi se comporta el dinero: una caida sumada
subestima las caidas profundas. Relativa y no absoluta porque la caida que
importa es la fraccion del pico. Se fija por principio, NO por cual da mas
potencia: las dos versiones se reportan abajo para que se vea la diferencia.
"""
import numpy as np

def rc_vectorizada(X):
    """implementacion 1: numpy, acumuladores vectorizados"""
    # el capital inicial 1.0 ENTRA en la curva: si no, se pierde la caida
    # desde el principio y el r/c sale inflado (error encontrado por rc_bucle)
    eq=np.concatenate([np.ones((X.shape[0],1)), np.cumprod(1.0+X,axis=1)],axis=1)
    pico=np.maximum.accumulate(eq,axis=1)
    dd=((pico-eq)/pico).max(axis=1)
    n=X.shape[1]
    cagr=eq[:,-1]**(12.0/n)-1.0
    return cagr/np.maximum(dd,1e-12)

def rc_bucle(X):
    """implementacion 2, INDEPENDIENTE: bucle explicito, sin acumuladores numpy,
    sin cumprod. Escrita a proposito de otra forma para que un error de una no
    aparezca en la otra."""
    w,n=X.shape
    out=np.empty(w)
    for i in range(w):
        eq=1.0; pico=1.0; peor=0.0
        for t in range(n):
            eq=eq*(1.0+X[i,t])
            if eq>pico: pico=eq
            d=(pico-eq)/pico
            if d>peor: peor=d
        cagr=eq**(12.0/n)-1.0
        out[i]=cagr/(peor if peor>1e-12 else 1e-12)
    return out

def rc_suma(X):
    """la version de SUMA, solo para reportar cuanto se habria desviado"""
    c=np.concatenate([np.zeros((X.shape[0],1)), np.cumsum(X,axis=1)],axis=1)
    dd=(np.maximum.accumulate(c,axis=1)-c).max(axis=1)
    return X.mean(axis=1)*12/np.maximum(dd,1e-12)
