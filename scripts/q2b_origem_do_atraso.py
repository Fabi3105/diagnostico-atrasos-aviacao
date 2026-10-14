# -*- coding: utf-8 -*-
"""Pergunta 2, aprofundamento pedido pelo Fabian: o atraso nasce no aeroporto ou chega com o avião?
Quanto se ganharia agindo no aeroporto (solo) contra agindo na malha (folga entre voos, recuperação)?

Sem número de cauda, usamos uma aproximação por companhia e aeroporto. Para cada partida da companhia E no
aeroporto X com horário previsto t, olhamos as chegadas da mesma companhia em X previstas entre t-180 e t-35 min
(os aviões que poderiam fazer esse voo, com giro mínimo de 35 min):
- "chegada que comprometeu o giro": chegou de fato depois de t-35 (não sobrou o giro mínimo para sair no horário);
- a partida atrasada é "provavelmente herdada" se a maior parte (>= 50%) dessas chegadas comprometeu o giro;
  "provavelmente originada em solo" se nenhuma comprometeu; "mista" no meio.
Partidas sem chegada da companhia na janela (1º voo do dia, pernoite) contam como originadas em solo.
Sensibilidade: giro mínimo de 25 e 45 min (limite 50%) e limite de 25% e 75% (giro 35 min).
É uma aproximação: num hub com muitas chegadas, o avião certo pode não ser o atrasado."""
import numpy as np, pandas as pd
from base import ler, salvar, ESCOPO, ICAO_IATA, NOME_CURTO, GRANDES, DB

import time
T0 = time.time()
cache = DB.parent / "q2b.pkl"
if cache.exists() and cache.stat().st_mtime > max(DB.stat().st_mtime, __import__("pathlib").Path(__file__).stat().st_mtime):
    q = pd.read_pickle(cache)
else:
    q = ler(f"""SELECT empresa, origem, destino, partida_prev, chegada_prev, chegada_real, atraso_partida
                FROM voos WHERE {ESCOPO} AND situacao = 'REALIZADO' AND empresa IN ('AZU','TAM','GLO')""")
    for c in ["partida_prev", "chegada_prev", "chegada_real"]:
        q[c] = pd.to_datetime(q[c], format="%Y-%m-%d %H:%M:%S").astype("int64") // 60_000_000_000
    q.to_pickle(cache)
q["atrasado"] = q.atraso_partida > 30

def classifica(giro=35, limite=0.5):
    saida = []
    for (e, x), dep in q.groupby(["empresa", "origem"]):
        arr = q[(q.empresa == e) & (q.destino == x)] if False else ARR.get((e, x))
        t = dep.partida_prev.values
        if arr is None or len(arr) == 0:
            saida.append(pd.DataFrame({"idx": dep.index, "n_cheg": 0, "n_comp": 0})); continue
        ap = arr.chegada_prev.values; ar = arr.chegada_real.values
        o = np.argsort(ap); ap, ar = ap[o], ar[o]
        lo = np.searchsorted(ap, t - 180, "left"); hi = np.searchsorted(ap, t - giro, "right")
        n = hi - lo
        comp = np.zeros(len(t), dtype=int)
        for i in np.nonzero(n)[0]:
            comp[i] = (ar[lo[i]:hi[i]] > t[i] - giro).sum()
        saida.append(pd.DataFrame({"idx": dep.index, "n_cheg": n, "n_comp": comp}))
    s = pd.concat(saida).set_index("idx").reindex(q.index)
    frac = np.where(s.n_cheg > 0, s.n_comp / s.n_cheg.clip(lower=1), 0)
    return np.select([frac >= limite, frac == 0], ["herdada", "solo"], "mista"), s

ARR = {k: g[["chegada_prev", "chegada_real"]] for k, g in q.groupby(["empresa", "destino"])}
print("prep", time.time() - T0, flush=True)
q["classe"], s = classifica()
print("classifica", time.time() - T0, flush=True)
q["n_cheg"] = s.n_cheg.values
a = q[q.atrasado]

# 1. composição dos atrasos
comp = a.groupby("empresa").classe.value_counts(normalize=True).unstack().mul(100)
comp.loc["mercado (3 grandes)"] = a.classe.value_counts(normalize=True).mul(100)
comp.index = [NOME_CURTO.get(i, i) for i in comp.index]
# probabilidade de atrasar conforme a situação das chegadas
q["situacao_cheg"] = np.select([q.n_cheg == 0, q.classe == "herdada", q.classe == "mista"], ["sem chegada na janela", "giro comprometido (>=50%)", "parcial"], "chegadas no horário")
prob = q.groupby("situacao_cheg").agg(partidas=("atrasado", "size"), atraso30_pct=("atrasado", "mean"))
prob["atraso30_pct"] *= 100
salvar(comp.round(1), "q2b_composicao_atrasos.csv", index=True)
salvar(prob.round(2), "q2b_probabilidade_por_situacao.csv", index=True)

# 2. por aeroporto: onde o atraso nasce em solo
g = q.groupby("origem").agg(partidas=("atrasado", "size"), atrasos=("atrasado", "sum"))
g["atrasos_solo"] = a[a.classe == "solo"].groupby("origem").size()
g["atrasos_herdados"] = a[a.classe == "herdada"].groupby("origem").size()
g = g.fillna(0)
g["taxa_atraso_solo_pct"] = 100 * g.atrasos_solo / g.partidas       # atraso nascido ali, por partida
g["parte_solo_dos_atrasos_pct"] = 100 * g.atrasos_solo / g.atrasos
g["parte_do_total_solo_mercado_pct"] = 100 * g.atrasos_solo / g.atrasos_solo.sum()
g = g[g.partidas >= 3000].sort_values("atrasos_solo", ascending=False)
g["parte_acumulada_pct"] = g.parte_do_total_solo_mercado_pct.cumsum()
g.insert(0, "iata", g.index.map(ICAO_IATA))
salvar(g.round(2), "q2b_atraso_solo_por_aeroporto.csv", index=True)

# 3. sensibilidade
sens = []

import os
for giro, lim in ([] if os.environ.get("SEM_SENS") else [(25, 0.5), (35, 0.5), (45, 0.5), (35, 0.25), (35, 0.75)]):
        c, _ = classifica(giro, lim) if (giro, lim) != (35, 0.5) else (q.classe.values, None)
        cc = pd.Series(c[q.atrasado.values]).value_counts(normalize=True)
        sens.append({"giro_min": giro, "limite": lim, **{f"{k}_pct": 100 * cc.get(k, 0) for k in ["solo", "mista", "herdada"]}})
if sens:
    salvar(pd.DataFrame(sens).round(1), "q2b_sensibilidade.csv")

pd.set_option("display.width", 250)
print(comp.round(1).to_string()); print(prob.round(1).to_string()); print(g.round(1).head(15).to_string()); print(pd.DataFrame(sens).round(1).to_string())

# 4. primeira onda (voos sem chegada da companhia antes: avião que pernoitou) x resto do dia, por companhia-dia
from base import FUSO_AEROPORTO
q["hora_local"] = ((q.partida_prev % 1440) // 60 + q.origem.map(FUSO_AEROPORTO).fillna(0)) % 24
q["dia"] = q.partida_prev // 1440
q["primeira_onda"] = (q.n_cheg == 0) & (q.hora_local < 10)
d = q.groupby(["empresa", "dia", "primeira_onda"]).agg(n=("atrasado", "size"), a=("atrasado", "sum")).unstack("primeira_onda")
d.columns = [f"{x}_{'onda' if y else 'resto'}" for x, y in d.columns]
d = d.dropna().reset_index()
tot = d.groupby("dia")[["n_onda", "a_onda", "n_resto", "a_resto"]].transform("sum")
d["onda"] = d.a_onda / d.n_onda; d["resto"] = d.a_resto / d.n_resto
d["onda_outras"] = (tot.a_onda - d.a_onda) / (tot.n_onda - d.n_onda)
d["resto_outras"] = (tot.a_resto - d.a_resto) / (tot.n_resto - d.n_resto)
d["faixa_onda"] = pd.cut(d.onda, [-0.01, 0, 0.05, 0.10, 0.20, 1], labels=["0%", "até 5%", "5-10%", "10-20%", "mais de 20%"])
t4 = d.groupby("faixa_onda", observed=True).apply(lambda x: pd.Series({
    "dias_companhia": len(x), "atraso_resto_do_dia_pct": 100 * x.a_resto.sum() / x.n_resto.sum(),
    "atraso_resto_outras_companhias_pct": 100 * (x.resto_outras * x.n_resto).sum() / x.n_resto.sum()}), include_groups=False)
salvar(t4.round(2), "q2b_primeira_onda.csv", index=True)
# regressão: resto do dia ~ 1ª onda própria + 1ª onda das outras + resto das outras (choque do dia) + companhia
X = np.column_stack([np.ones(len(d)), d.onda, d.onda_outras, d.resto_outras,
                     (d.empresa == "TAM").astype(float), (d.empresa == "GLO").astype(float)])
w = np.sqrt(d.n_resto.values)
b, *_ = np.linalg.lstsq(X * w[:, None], d.resto.values * w, rcond=None)
rng = np.random.default_rng(1); bs = []
for _ in range(300):
    ix = rng.integers(0, len(d), len(d))
    bs.append(np.linalg.lstsq(X[ix] * w[ix, None], d.resto.values[ix] * w[ix], rcond=None)[0][1])
lo, hi = np.percentile(bs, [5, 95])
media_onda = np.average(d.onda, weights=d.n_onda); media_resto = np.average(d.resto, weights=d.n_resto)
t5 = pd.DataFrame({"medida": ["voos da 1ª onda (pernoite, antes das 10h) % dos voos", "atraso da 1ª onda %", "atraso do resto do dia %",
                              "coeficiente 1ª onda própria -> resto do dia", "margem baixa", "margem alta",
                              "coeficiente choque do dia (resto das outras companhias)",
                              "queda estimada no atraso do resto do dia se a 1ª onda fosse 100% pontual (pp)",
                              "idem, em % do atraso do resto do dia"],
                   "valor": [100 * d.n_onda.sum() / (d.n_onda.sum() + d.n_resto.sum()), 100 * media_onda, 100 * media_resto,
                             b[1], lo, hi, b[3], 100 * b[1] * media_onda, 100 * b[1] * media_onda / media_resto]})
salvar(t5.round(3), "q2b_primeira_onda_efeito.csv")
print(t4.round(1).to_string()); print(t5.round(3).to_string())
