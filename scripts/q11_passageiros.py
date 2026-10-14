# -*- coding: utf-8 -*-
"""Melhoria B da revisão (14/10/2026): passageiros, ocupação e bagagem (ANAC, Dados Estatísticos do Transporte Aéreo,
filtrado para 2024-2026: dados/externos/dados_estatisticos_2024_2026.csv).
1. Reclamações por 10 mil passageiros (set/2024-dez/2025), brasileiras e estrangeiras na mesma régua.
2. Ocupação (passageiros ÷ assentos) e bagagem por passageiro, por mês, nos voos domésticos regulares das três grandes.
3. Teste da hipótese de dezembro: o atraso mensal com tempo normal anda junto com a ocupação e a bagagem?
   Painel companhia x mês (efeito fixo de companhia); correlação, não causa; poucos meses (24)."""
import numpy as np, pandas as pd
from base import RAIZ, ler, salvar, RES, NOME_CURTO, GRANDES, CRUZ_INI, CRUZ_FIM, ESCOPO

d = pd.read_csv(RAIZ / "dados" / "externos" / "dados_estatisticos_2024_2026.csv", sep=";", dtype=str)
d.columns = [c.strip('"').lower() for c in d.columns]
d = d.apply(lambda s: s.str.strip('"'))
for c in ["ano", "mes", "passageiros_pagos", "passageiros_gratis", "ask", "rpk", "decolagens", "assentos", "bagagem_kg"]:
    d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
d["pax"] = d.passageiros_pagos + d.passageiros_gratis
d["mes7"] = d.ano.astype(int).astype(str) + "-" + d.mes.astype(int).astype(str).str.zfill(2)
d["empresa"] = d.empresa_sigla.replace({"ACN": "AZU"})
reg = d[d.grupo_de_voo == "REGULAR"]
chk = reg[reg.empresa.isin(GRANDES) & (reg.natureza == "DOMÉSTICA") & (reg.mes7 >= "2024-09") & (reg.mes7 < "2026-09")]

# 1. reclamações por 10 mil passageiros
per = reg[(reg.mes7 >= CRUZ_INI[:7]) & (reg.mes7 < CRUZ_FIM[:7])].groupby("empresa").agg(pax=("pax", "sum"), decolagens=("decolagens", "sum"))
rk = pd.read_csv(RES / "q5_ranking_companhias.csv", encoding="utf-8-sig").set_index("empresa")
t1 = rk[["companhia", "grupo", "reclamacoes", "graves", "por_10mil_voos", "graves_por_10mil_voos", "resolucao_pct"]].join(per)
t1["por_10mil_passageiros"] = 1e4 * t1.reclamacoes / t1.pax
t1["graves_por_10mil_passageiros"] = 1e4 * t1.graves / t1.pax
t1["passageiros_por_voo"] = t1.pax / t1.decolagens
t1 = t1.dropna(subset=["pax"]).sort_values(["grupo", "graves_por_10mil_passageiros"], ascending=[True, False])
salvar(t1.round(2), "q11_reclamacoes_por_passageiro.csv", index=True)

# 2. ocupação e bagagem por mês (domésticos regulares)
dom = reg[reg.empresa.isin(GRANDES) & (reg.natureza == "DOMÉSTICA") & (reg.mes7 >= "2024-09") & (reg.mes7 < "2026-09")]
om = dom.groupby(["empresa", "mes7"]).agg(pax=("pax", "sum"), assentos=("assentos", "sum"), rpk=("rpk", "sum"), ask=("ask", "sum"),
                                          bag=("bagagem_kg", "sum"), decol=("decolagens", "sum")).reset_index()
om["ocupacao_pct"] = 100 * om.rpk / om.ask
om["bagagem_kg_por_pax"] = om.bag / om.pax
om["pax_por_voo"] = om.pax / om.decol
# atraso mensal com tempo normal por companhia (q_clima não salva por companhia; recalcula aqui com o clima do banco)
v = ler(f"""SELECT empresa, substr(partida_prev,1,7) mes7, AVG(atraso_partida > 30) atraso FROM voos WHERE {ESCOPO}
            AND situacao='REALIZADO' AND empresa IN ('AZU','TAM','GLO') GROUP BY 1,2""")
om = om.merge(v, on=["empresa", "mes7"])
om["atraso_pct"] = 100 * om.atraso
om["m"] = om.mes7.str[5:]
salvar(om.round(3), "q11_ocupacao_bagagem_mes.csv")
mm = om.groupby("m").apply(lambda x: pd.Series({"ocupacao_pct": np.average(x.ocupacao_pct, weights=x.ask), "bagagem_kg_por_pax": x.bag.sum() / x.pax.sum(),
                                               "pax_por_voo": x.pax.sum() / x.decol.sum(), "atraso_pct": np.average(x.atraso_pct, weights=x.decol)}), include_groups=False)
salvar(mm.round(2), "q11_mes_do_ano.csv", index=True)
# 3. painel com efeito fixo de companhia (desvios da média da companhia)
p = om.copy()
for c in ["ocupacao_pct", "bagagem_kg_por_pax", "pax_por_voo", "atraso_pct"]:
    p[c + "_d"] = p[c] - p.groupby("empresa")[c].transform("mean")
cor = pd.DataFrame({"medida": ["ocupação", "bagagem por passageiro", "passageiros por voo"],
                    "correlacao_com_atraso_mensal": [p.ocupacao_pct_d.corr(p.atraso_pct_d), p.bagagem_kg_por_pax_d.corr(p.atraso_pct_d), p.pax_por_voo_d.corr(p.atraso_pct_d)]})
X = np.column_stack([np.ones(len(p)), p.ocupacao_pct_d, p.bagagem_kg_por_pax_d])
b = np.linalg.lstsq(X, p.atraso_pct_d.values, rcond=None)[0]
rng = np.random.default_rng(4); bs = []
for _ in range(1000):
    ix = rng.integers(0, len(p), len(p)); bs.append(np.linalg.lstsq(X[ix], p.atraso_pct_d.values[ix], rcond=None)[0])
lo, hi = np.percentile(bs, [5, 95], axis=0)
cor.loc[len(cor)] = ["regressão: +1 ponto de ocupação -> pontos de atraso", b[1]]
cor.loc[len(cor)] = ["  margem", f"{lo[1]:.2f} a {hi[1]:.2f}"]
cor.loc[len(cor)] = ["regressão: +1 kg de bagagem por passageiro -> pontos de atraso", b[2]]
cor.loc[len(cor)] = ["  margem", f"{lo[2]:.2f} a {hi[2]:.2f}"]
salvar(cor, "q11_hipotese_dezembro.csv")
pd.set_option("display.width", 220)
print(t1.round(1).to_string()); print(mm.round(2).to_string()); print(cor.to_string())
