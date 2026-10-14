# -*- coding: utf-8 -*-
"""Pergunta 1 (com M1). Quais companhias e aeroportos mais atrasam e cancelam, por voo operado; quanto de cada
problema é da companhia e quanto é do aeroporto; onde a ação é mais eficiente.

Método (definições A a E):
- Taxas brutas por companhia e por aeroporto de origem; minutos de atraso acumulados (M1) e concentração (Pareto).
- Modelo aditivo (mínimos quadrados ponderados) sobre células companhia x aeroporto x hora local x mês:
  taxa = companhia + aeroporto + hora + mês. O efeito de cada companhia é medido dentro dos mesmos aeroportos,
  horários e meses (e vice-versa). Efeitos em pontos percentuais em relação à média do mercado.
- Quanto da diferença entre células cada fator explica (R² e divisão de Shapley entre companhia e aeroporto).
- Estabilidade: o modelo é refeito no 1º ano (set/24-ago/25) e no 2º ano (set/25-ago/26); efeitos comparados.
- Interação: pares companhia x aeroporto muito piores que o esperado pela soma dos dois efeitos.
Associação não é causa: a base não traz o motivo do atraso."""
import numpy as np, pandas as pd
from base import voos_escopo, salvar, NOME_CURTO, ICAO_IATA, GRANDES

v = voos_escopo()
v["empresa"] = v.empresa.astype(str); v["origem"] = v.origem.astype(str); v["mes"] = v.mes.astype(str)
r = v[~v.cancelado]
MIN_EMP, MIN_AER = 5000, 3000
emp_ok = v.empresa.value_counts()[lambda s: s >= MIN_EMP].index
aer_ok = v.origem.value_counts()[lambda s: s >= MIN_AER].index
nome = lambda e: NOME_CURTO.get(e, e)

def resumo(g, chave):
    t = g.groupby(chave, observed=True).agg(previstos=("cancelado", "size"), cancelados=("cancelado", "sum"))
    rr = g[~g.cancelado].groupby(chave, observed=True)
    t["realizados"] = rr.size()
    t["cancelamento_pct"] = 100 * t.cancelados / t.previstos
    t["atraso30_pct"] = 100 * rr.atrasado.mean()
    for a, b, rot in [(30, 60, "30_60"), (60, 120, "60_120"), (120, 240, "120_240"), (240, 1e9, "mais240")]:
        t[f"faixa_{rot}_pct"] = 100 * rr.atraso_partida.apply(lambda s: ((s > a) & (s <= b)).mean())
    t["atraso_chegada30_pct"] = 100 * rr.atrasado_chegada.mean()
    t["mediana_atraso_dos_atrasados"] = g[g.atrasado == 1].groupby(chave, observed=True).atraso_partida.median()
    t["minutos_atraso_mil"] = rr.minutos_atraso.sum() / 1e3
    t["minutos_por_voo"] = rr.minutos_atraso.mean()
    t["parte_dos_minutos_pct"] = 100 * t.minutos_atraso_mil / t.minutos_atraso_mil.sum()
    return t

# ---------- 1. taxas brutas
te = resumo(v[v.empresa.isin(emp_ok)], "empresa")
te.insert(0, "companhia", te.index.map(nome))
salvar(te.round(2).sort_values("previstos", ascending=False), "q1_companhias.csv", index=True)

ta = resumo(v, "origem")
ta = ta[ta.previstos >= MIN_AER].sort_values("minutos_atraso_mil", ascending=False)
ta["parte_acumulada_pct"] = ta.parte_dos_minutos_pct.cumsum()
ta.insert(0, "iata", ta.index.map(ICAO_IATA))
# parte dos minutos medida sobre o total do mercado (todos os aeroportos)
tot = r.minutos_atraso.sum() / 1e3
ta["parte_dos_minutos_pct"] = 100 * ta.minutos_atraso_mil / tot
ta["parte_acumulada_pct"] = ta.parte_dos_minutos_pct.cumsum()
salvar(ta.round(2), "q1_aeroportos.csv", index=True)

# ---------- 2. modelo aditivo
def celulas(d, alvo, chaves):
    d = d.assign(emp=np.where(d.empresa.isin(emp_ok), d.empresa, "outras"),
                 aer=np.where(d.origem.isin(aer_ok), d.origem, "outros"))
    return d.groupby(chaves, observed=True).agg(n=(alvo, "count"), y=(alvo, "mean")).reset_index().query("n > 0")

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

ca = celulas(r.assign(y=r.atrasado), "y", ["emp", "aer", "hora_local", "mes"])
cc = celulas(v.assign(y=v.cancelado.astype(float)), "y", ["emp", "aer", "mes"])
coef_a, r2a, pred_a = ajusta(ca, ["hora_local", "mes", "emp", "aer"])
coef_c, r2c, _ = ajusta(cc, ["mes", "emp", "aer"])
g3a, g3c = ca[ca.emp.isin(GRANDES)].reset_index(drop=True), cc[cc.emp.isin(GRANDES)].reset_index(drop=True)
dec = pd.DataFrame([decompor(ca, "atraso > 30 min"), decompor(cc, "cancelamento"),
                    decompor(g3a, "atraso > 30 min (só Azul, LATAM e Gol)"), decompor(g3c, "cancelamento (só Azul, LATAM e Gol)")])
salvar(dec.round(4), "q1_decomposicao.csv")

# estabilidade entre os dois anos
anos = {"ano1": r.mes < "2025-09", "ano2": r.mes >= "2025-09"}
est = {}
for k, m in anos.items():
    cak = celulas(r[m].assign(y=r[m].atrasado), "y", ["emp", "aer", "hora_local", "mes"])
    est[k] = ajusta(cak, ["hora_local", "mes", "emp", "aer"])[0]

def efeitos(f, coef, coefc, rot, filtro):
    t = pd.DataFrame({"efeito_atraso_pp": 100 * coef[f], "efeito_cancelamento_pp": 100 * coefc[f],
                      "efeito_atraso_ano1_pp": 100 * est["ano1"][f], "efeito_atraso_ano2_pp": 100 * est["ano2"][f]})
    t = t[t.index.isin(filtro)]
    t.index.name = rot
    return t

ee = efeitos("emp", coef_a, coef_c, "empresa", emp_ok)
ee.insert(0, "companhia", ee.index.map(nome))
ee = ee.join(te[["atraso30_pct", "cancelamento_pct"]].rename(columns={"atraso30_pct": "atraso_bruto_pct", "cancelamento_pct": "cancelamento_bruto_pct"}))
salvar(ee.round(2).sort_values("efeito_atraso_pp"), "q1_efeito_companhia.csv", index=True)

ea = efeitos("aer", coef_a, coef_c, "origem", aer_ok)
ea.insert(0, "iata", ea.index.map(ICAO_IATA))
ea = ea.join(ta[["previstos", "atraso30_pct", "cancelamento_pct", "minutos_atraso_mil", "parte_dos_minutos_pct"]])
# "por quê" possível com os dados: tamanho e congestionamento do aeroporto e domínio de uma companhia
pico = (r[r.origem.isin(aer_ok)].groupby(["origem", "data", "hora_local"], observed=True).size()
        .groupby(["origem", "hora_local"], observed=True).mean().groupby("origem", observed=True).max())
ea["partidas_na_hora_de_pico"] = pico
ea["voos_por_dia"] = ea.previstos / v.data.nunique()
dom = v[v.origem.isin(aer_ok)].groupby("origem", observed=True).empresa.agg(lambda s: s.value_counts(normalize=True).iloc[0])
ea["parte_da_maior_companhia_pct"] = 100 * dom
salvar(ea.round(2).sort_values("efeito_atraso_pp", ascending=False), "q1_efeito_aeroporto.csv", index=True)

corr = pd.DataFrame({
    "medida": ["log(voos por dia)", "partidas na hora de pico", "parte da maior companhia"],
    "correlacao_com_efeito_atraso": [np.corrcoef(np.log(ea.voos_por_dia), ea.efeito_atraso_pp)[0, 1],
                                     np.corrcoef(ea.partidas_na_hora_de_pico, ea.efeito_atraso_pp)[0, 1],
                                     np.corrcoef(ea.parte_da_maior_companhia_pct, ea.efeito_atraso_pp)[0, 1]]})
corr["correlacao_ano1_ano2_efeito_aeroporto"] = np.corrcoef(ea.efeito_atraso_ano1_pp, ea.efeito_atraso_ano2_pp)[0, 1]
salvar(corr.round(3), "q1_aeroporto_porque.csv")

# ---------- 3. interação companhia x aeroporto (pares piores que o esperado)
ca["pred"] = pred_a
ca["ano"] = np.where(ca.mes < "2025-09", "ano1", "ano2")
ca["obs_n"] = ca.y * ca.n; ca["pred_n"] = ca.pred * ca.n
p = ca[(ca.emp != "outras") & (ca.aer != "outros")].groupby(["emp", "aer"]).agg(voos=("n", "sum"), obs=("obs_n", "sum"), esp=("pred_n", "sum"))
py = ca[(ca.emp != "outras") & (ca.aer != "outros")].groupby(["emp", "aer", "ano"]).agg(n=("n", "sum"), obs=("obs_n", "sum"), esp=("pred_n", "sum"))
py["exc"] = 100 * (py.obs - py.esp) / py.n
p["atraso_obs_pct"] = 100 * p.obs / p.voos; p["atraso_esperado_pct"] = 100 * p.esp / p.voos
p["excesso_pp"] = p.atraso_obs_pct - p.atraso_esperado_pct
p["excesso_ano1_pp"] = py.exc.xs("ano1", level="ano"); p["excesso_ano2_pp"] = py.exc.xs("ano2", level="ano")
p["voos_atrasados_a_mais"] = (p.obs - p.esp).round()
p = p[p.voos >= 1500].drop(columns=["obs", "esp"]).reset_index()
p.insert(1, "companhia", p.emp.map(nome)); p.insert(3, "iata", p.aer.map(ICAO_IATA))
p["persistente"] = (p.excesso_ano1_pp > 1) & (p.excesso_ano2_pp > 1)
salvar(p.round(2).sort_values("excesso_pp", ascending=False), "q1_pares_companhia_aeroporto.csv")

pd.set_option("display.width", 250, "display.max_columns", 30)
print(te.round(1).to_string()); print(dec.round(4).to_string()); print(ee.round(2).to_string())
print(ea.round(2).head(15).to_string()); print(ea.round(2).tail(8).to_string()); print(corr.round(3).to_string())
print(ta.round(1).head(12)[["iata", "previstos", "atraso30_pct", "cancelamento_pct", "minutos_atraso_mil", "parte_dos_minutos_pct", "parte_acumulada_pct"]].to_string())
print(p.sort_values("excesso_pp", ascending=False).round(2).head(15).to_string())
print("aeroportos no modelo", len(aer_ok), "R2", r2a, r2c)
