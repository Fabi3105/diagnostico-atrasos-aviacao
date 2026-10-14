# -*- coding: utf-8 -*-
"""Modelo aditivo ponderado da P1 (companhia + aeroporto + hora + mês), reutilizado no bloco de clima."""
import numpy as np, pandas as pd

def celulas(d, emp_ok, aer_ok, alvo="atrasado", chaves=("emp", "aer", "hora_local", "mes")):
    d = d.assign(emp=np.where(d.empresa.astype(str).isin(emp_ok), d.empresa.astype(str), "outras"),
                 aer=np.where(d.origem.astype(str).isin(aer_ok), d.origem.astype(str), "outros"), mes=d.mes.astype(str))
    return d.groupby(list(chaves), observed=True).agg(n=(alvo, "count"), y=(alvo, "mean")).reset_index().query("n > 0")

def ajusta(c, fatores):
    cols, nomes = [np.ones(len(c))], [("const", "")]
    for f in fatores:
        niv = c[f].astype(str).value_counts().index           # o nível mais frequente é a referência
        for k in niv[1:]:
            cols.append((c[f].astype(str) == k).values.astype(float)); nomes.append((f, k))
    X = np.column_stack(cols); w = np.sqrt(c.n.values)
    b, *_ = np.linalg.lstsq(X * w[:, None], c.y.values * w, rcond=None)
    pred = X @ b
    ybar = np.average(c.y, weights=c.n)
    r2 = 1 - np.sum(c.n * (c.y - pred) ** 2) / np.sum(c.n * (c.y - ybar) ** 2)
    coef = {f: {} for f in fatores}
    for (f, k), bb in zip(nomes[1:], b[1:]):
        coef[f][k] = bb
    for f in fatores:                                      # efeito centrado na média ponderada pelos voos
        niv = c[f].astype(str).value_counts().index
        coef[f][niv[0]] = 0.0
        peso = c.groupby(c[f].astype(str)).n.sum()
        s = pd.Series(coef[f]); m = np.average(s[peso.index], weights=peso)
        coef[f] = (s - m)
    return coef, r2, pred

def decompor(c, alvo_nome):
    base = ["hora_local", "mes"] if "hora_local" in c else ["mes"]
    R = {}
    for nome_m, fat in [("controles", base), ("+companhia", base + ["emp"]), ("+aeroporto", base + ["aer"]),
                        ("completo", base + ["emp", "aer"])]:
        R[nome_m] = ajusta(c, fat)[1]
    sh_emp = 0.5 * ((R["+companhia"] - R["controles"]) + (R["completo"] - R["+aeroporto"]))
    sh_aer = 0.5 * ((R["+aeroporto"] - R["controles"]) + (R["completo"] - R["+companhia"]))
    return {"indicador": alvo_nome, "R2_so_hora_mes": R["controles"], "R2_completo": R["completo"],
            "parte_companhia": sh_emp, "parte_aeroporto": sh_aer,
            "companhia_pct_do_explicado_por_ambos": 100 * sh_emp / (sh_emp + sh_aer)}

