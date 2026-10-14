# -*- coding: utf-8 -*-
"""Bloco de clima (pedido do Fabian). Usa clima_hora (clima.py) para:
W1. Impacto do tempo na origem (hora da partida e hora anterior) e no destino (hora da chegada prevista).
W2. P1 sem clima: o modelo companhia + aeroporto + hora + mês refeito só com voos em tempo normal na origem e
    no destino; e parte dos atrasos ligada ao clima.
W3. P2 com clima: quanto do "choque do dia" é clima nos aeroportos; a propagação muda em dias de tempo ruim?
W4. P4 com clima: horas de tempo severo por mês; dezembro e os dias de crise; férias de verão com controle de clima.
W5. Folga dinâmica (P3): comparar folga uniforme, folga sazonal (aeroporto x mês x faixa horária, planejável na
    malha) e folga no dia (aplicada quando o tempo fica ruim). Medida: atrasos > 30 min evitados por 1.000
    minutos de folga adicionados. Simulação simples: a folga adia o horário previsto; não considera o ganho
    de propagação nem o custo de utilização do avião, por isso é uma comparação entre estratégias, não uma previsão.
Associação não é causa; o METAR descreve o tempo no aeródromo, não a decisão do controle de tráfego."""
import numpy as np, pandas as pd
from base import ler, salvar, ESCOPO, ICAO_IATA, NOME_CURTO, GRANDES, ATRASO_MIN, FUSO_AEROPORTO

v = ler(f"""SELECT empresa, origem, destino, situacao, CAST(strftime('%s', partida_prev) AS INTEGER) / 3600 AS hp,
            CAST(strftime('%s', chegada_prev) AS INTEGER) / 3600 AS hc, atraso_partida, atraso_chegada, mes, hora
            FROM voos WHERE {ESCOPO}""")
for c in ["empresa", "origem", "destino", "situacao", "mes"]:
    v[c] = v[c].astype("category")
cl = ler("""SELECT station, data, hora, nivel, trovoada, chuva_forte,
            CAST(strftime('%s', data || ' ' || printf('%02d', hora) || ':00:00') AS INTEGER) / 3600 AS h FROM clima_hora""")
sid = {a: i for i, a in enumerate(sorted(set(cl.station) | set(v.origem.cat.categories) | set(v.destino.cat.categories)))}
chave = pd.Index(cl.station.map(sid).astype("int64") * 10_000_000 + cl.h)
nivel = cl.nivel.to_numpy(dtype=float)
conv = ((cl.trovoada > 0) | (cl.chuva_forte > 0)).to_numpy(dtype=float)   # trovoada ou chuva forte
def f(ap, hh, arr=None):
    arr = nivel if arr is None else arr
    k = ap.astype(str).map(sid).astype("int64").to_numpy() * 10_000_000 + hh.to_numpy()
    ix = chave.get_indexer(k)
    return np.where(ix >= 0, arr[ix], np.nan)
v["cancelado"] = v.situacao == "CANCELADO"
v["clima_origem"] = np.fmax(f(v.origem, v.hp), f(v.origem, v.hp - 1))   # pior entre a hora da partida e a anterior
v["clima_destino"] = f(v.destino, v.hc)
v["conv_origem"] = np.fmax(f(v.origem, v.hp, conv), f(v.origem, v.hp - 1, conv))
lab = {0: "normal", 1: "moderado", 2: "severo"}
v["co"] = v.clima_origem.map(lab); v["cd"] = v.clima_destino.map(lab)
from metodos import erro_de_data
v = v[~(~v.cancelado & erro_de_data(v.atraso_partida.fillna(0)))]   # exclui os erros de data, como nas outras análises
r = v[~v.cancelado].copy()
r["atrasado"] = (r.atraso_partida > ATRASO_MIN).astype(float)
r["atrasado_cheg"] = (r.atraso_chegada > ATRASO_MIN).astype(float)
r["hora_local"] = (r.hora + r.origem.map(FUSO_AEROPORTO).fillna(0)) % 24
cob = r.clima_origem.notna().mean()

# W1
w1 = r.dropna(subset=["co"]).groupby("co").agg(voos=("atrasado", "size"), atraso_partida_pct=("atrasado", "mean"),
                                               atraso_chegada_pct=("atrasado_cheg", "mean"), atraso_mediano=("atraso_partida", "median"))
w1[["atraso_partida_pct", "atraso_chegada_pct"]] *= 100
w1["parte_dos_voos_pct"] = 100 * w1.voos / w1.voos.sum()
canc = v.dropna(subset=["co"]).groupby("co").cancelado.mean() * 100
w1["cancelamento_pct"] = canc
w1d = r.dropna(subset=["cd"]).groupby("cd").agg(voos=("atrasado", "size"), atraso_partida_pct=("atrasado", "mean"),
                                                atraso_chegada_pct=("atrasado_cheg", "mean"))
w1d[["atraso_partida_pct", "atraso_chegada_pct"]] *= 100
salvar(pd.concat({"tempo na origem": w1, "tempo no destino": w1d}).round(2), "qc_impacto_clima.csv", index=True)
# por aeroporto: atraso em tempo normal x severo
ap = r.dropna(subset=["co"]).groupby(["origem", "co"], observed=True).atrasado.agg(["size", "mean"]).unstack()
ap = ap[(ap[("size", "severo")] >= 100)]
ap.index = ap.index.astype(str)
wa = pd.DataFrame({"iata": ap.index.map(ICAO_IATA), "voos": ap["size"].sum(axis=1),
                   "horas_severas_pct_dos_voos": 100 * ap[("size", "severo")] / ap["size"].sum(axis=1),
                   "atraso_normal_pct": 100 * ap[("mean", "normal")], "atraso_severo_pct": 100 * ap[("mean", "severo")]})
wa["acrescimo_severo_pp"] = wa.atraso_severo_pct - wa.atraso_normal_pct
salvar(wa.sort_values("voos", ascending=False).round(2), "qc_impacto_clima_aeroporto.csv", index=True)
# tipo de tempo severo por aeroporto: trovoada ou chuva forte x só teto, visibilidade ou vento
t = r.dropna(subset=["co"]).copy()
t["cond"] = np.where(t.co != "severo", t.co, np.where(t.conv_origem > 0, "severo_trovoada_chuva", "severo_teto_visib_vento"))
tp = t.groupby(["origem", "cond"], observed=True).atrasado.agg(["size", "mean"]).unstack()
tp = tp[tp.index.astype(str).isin(ap.index)]
tp.index = tp.index.astype(str)
wt = pd.DataFrame({"iata": tp.index.map(ICAO_IATA), "atraso_normal_pct": 100 * tp[("mean", "normal")]})
for c in ["severo_trovoada_chuva", "severo_teto_visib_vento"]:
    wt[f"voos_{c}"] = tp[("size", c)]
    wt[f"acrescimo_{c}_pp"] = 100 * tp[("mean", c)] - wt.atraso_normal_pct
wt["parte_trovoada_chuva_no_severo_pct"] = 100 * wt.voos_severo_trovoada_chuva / (wt.voos_severo_trovoada_chuva + wt.voos_severo_teto_visib_vento)
salvar(wt.round(2), "qc_impacto_clima_tipo_aeroporto.csv", index=True)

# parte dos atrasos ligada ao clima: atrasos a mais em relação ao que se teria com a taxa de tempo normal
# do mesmo aeroporto e mesma hora
b = r.dropna(subset=["co", "cd"]).copy()
b["ruim"] = (b.clima_origem > 0) | (b.clima_destino > 0)
base = b[~b.ruim].groupby(["origem", "hora_local"], observed=True).atrasado.mean().rename("taxa_normal")
b = b.join(base, on=["origem", "hora_local"])
exc = (b[b.ruim].atrasado - b[b.ruim].taxa_normal).sum()
w2r = pd.DataFrame({"medida": ["voos com dado de clima na origem %", "voos com tempo moderado ou severo (origem ou destino) %",
                               "atrasos > 30 min nesses voos % do total", "atrasos a mais ligados ao clima % do total"],
                    "valor": [100 * cob, 100 * b.ruim.mean(), 100 * b[b.ruim].atrasado.sum() / b.atrasado.sum(),
                              100 * exc / b.atrasado.sum()]})
salvar(w2r.round(2), "qc_parte_clima.csv")

# W2: P1 sem clima
from q1_modelo import celulas, ajusta, decompor          # funções do modelo aditivo da P1
emp_ok = r.empresa.value_counts()[lambda s: s >= 5000].index
aer_ok = r.origem.value_counts()[lambda s: s >= 3000].index
def efeitos(d):
    c = celulas(d, emp_ok, aer_ok)
    coef, r2, _ = ajusta(c, ["hora_local", "mes", "emp", "aer"])
    g3 = c[c.emp.isin(GRANDES)].reset_index(drop=True)
    return coef, decompor(g3, "atraso")
todos = r.dropna(subset=["co", "cd"])
normal = todos[(todos.clima_origem == 0) & (todos.clima_destino == 0)]
ca, da = efeitos(todos); cn, dn = efeitos(normal)
dec = pd.DataFrame([dict(da, cenario="todos os voos com dado de clima"), dict(dn, cenario="só tempo normal na origem e no destino")])
salvar(dec.round(4), "qc_p1_decomposicao_sem_clima.csv")
ea = pd.DataFrame({"efeito_todos_pp": 100 * ca["aer"], "efeito_tempo_normal_pp": 100 * cn["aer"]})
ea = ea[ea.index.isin(aer_ok)]
ea.insert(0, "iata", ea.index.map(ICAO_IATA))
ea["diferenca_pp"] = ea.efeito_tempo_normal_pp - ea.efeito_todos_pp
salvar(ea.sort_values("efeito_tempo_normal_pp", ascending=False).round(2), "qc_p1_efeito_aeroporto_sem_clima.csv", index=True)
ee = pd.DataFrame({"efeito_todos_pp": 100 * ca["emp"], "efeito_tempo_normal_pp": 100 * cn["emp"]})
ee = ee[ee.index.isin(emp_ok)]; ee.insert(0, "companhia", ee.index.map(lambda e: NOME_CURTO.get(e, e)))
salvar(ee.round(2), "qc_p1_efeito_companhia_sem_clima.csv", index=True)
corr_aer = np.corrcoef(ea.efeito_todos_pp, ea.efeito_tempo_normal_pp)[0, 1]

# W3: choque do dia x clima. Por dia: taxa de atraso das 3 grandes e horas severas nos 10 maiores aeroportos
top10 = r.origem.value_counts().head(10).index.astype(str)
r["dia"] = r.hp // 24; cl["dia"] = cl.h // 24
dd = r[r.empresa.isin(GRANDES)].groupby("dia").atrasado.mean().rename("atraso") * 100
sv = cl[cl.station.isin(top10)].groupby("dia").nivel.apply(lambda s: (s == 2).sum()).rename("horas_severas_top10")
tv = cl[cl.station.isin(top10)].groupby("dia").trovoada.sum().rename("horas_trovoada_top10")
dd = pd.concat([dd, sv, tv], axis=1).dropna()
X = np.column_stack([np.ones(len(dd)), dd.horas_severas_top10, dd.horas_trovoada_top10])
bb = np.linalg.lstsq(X, dd.atraso.values, rcond=None)[0]
pred = X @ bb
r2_dia = 1 - ((dd.atraso - pred) ** 2).sum() / ((dd.atraso - dd.atraso.mean()) ** 2).sum()
dd["faixa"] = pd.cut(dd.horas_severas_top10, [-1, 0, 5, 15, 40, 1000], labels=["0", "1-5", "6-15", "16-40", "mais de 40"])
w3 = dd.groupby("faixa", observed=True).agg(dias=("atraso", "size"), atraso_medio_pct=("atraso", "mean"))
w3.loc["R² do clima na variação diária", "atraso_medio_pct"] = r2_dia
salvar(w3.round(3), "qc_p2_dia_x_clima.csv", index=True)

# W4: clima por mês e dias de crise
cm = cl[cl.station.isin(top10)].assign(mes=lambda d: d.data.str[5:7]).groupby("mes").agg(
    horas_severas_pct=("nivel", lambda s: 100 * (s == 2).mean()), horas_trovoada_pct=("trovoada", lambda s: 100 * s.mean()))
am = r.assign(m=r.mes.str[5:7]).groupby("m").atrasado.mean().mul(100).rename("atraso30_pct")
cm = cm.join(am)
an = r[(r.clima_origem == 0) & (r.clima_destino == 0)].assign(m=lambda d: d.mes.str[5:7]).groupby("m").atrasado.mean().mul(100)
cm["atraso30_tempo_normal_pct"] = an
salvar(cm.round(2), "qc_p4_clima_por_mes.csv", index=True)
crise = []
for d in ["2025-12-10", "2025-12-11", "2025-09-30", "2024-10-24", "2024-11-08", "2025-09-22", "2026-04-09"]:
    x = cl[(cl.data == d) & cl.station.isin(["SBSP", "SBGR", "SBRJ", "SBKP", "SBCF", "SBGL"])]
    crise.append({"data": d, **{ICAO_IATA[s]: int((x[x.station == s].nivel == 2).sum()) for s in ["SBSP", "SBGR", "SBRJ", "SBKP", "SBCF", "SBGL"]}})
salvar(pd.DataFrame(crise), "qc_p4_dias_de_crise_horas_severas.csv")

# W5: folga dinâmica. Regras aprendidas no 1º ano (set/24-ago/25) e testadas no 2º ano (set/25-ago/26).
s = r.dropna(subset=["co"]).copy()
s["mes2"] = s.mes.astype(str).str[5:7]
s["faixa_h"] = pd.cut(s.hora_local, [-1, 11, 16, 24], labels=["manhã", "tarde", "noite"]).astype(str)
s["origem"] = s.origem.astype(str)
s["pos"] = s.atraso_partida.clip(lower=0)
treino, teste = s[s.mes.astype(str) < "2025-09"], s[s.mes.astype(str) >= "2025-09"].copy()
atual = (teste.atraso_partida > 30).sum()
def avalia(folga, nome):
    novo = teste.atraso_partida - folga
    ev = atual - (novo > 30).sum()
    return {"estrategia": nome, "minutos_de_folga_por_voo": folga.mean(), "atraso30_pct": 100 * (novo > 30).mean(),
            "atrasos_evitados_no_2o_ano": int(ev), "evitados_por_mil_minutos": 1000 * ev / max(folga.sum(), 1),
            # minutos de atraso de partida evitados (todos os atrasos, não só os > 30) por minuto de folga
            "minutos_de_atraso_evitados_por_minuto_de_folga": (teste.pos.sum() - novo.clip(lower=0).sum()) / max(folga.sum(), 1)}
res = [{"estrategia": "hoje (2º ano)", "minutos_de_folga_por_voo": 0, "atraso30_pct": 100 * atual / len(teste),
        "atrasos_evitados_no_2o_ano": 0, "evitados_por_mil_minutos": np.nan}]
for m_ in (2, 3, 5):
    res.append(avalia(pd.Series(m_, index=teste.index), f"folga uniforme de {m_} min"))
# sazonal: aeroporto x mês x faixa horária (aprendida no 1º ano) = excesso médio de atraso da célula sobre a média geral
cel = treino.groupby(["origem", "mes2", "faixa_h"]).pos.mean() - treino.pos.mean()
cel_t = teste.join(cel.rename("exc"), on=["origem", "mes2", "faixa_h"]).exc.fillna(0).clip(lower=0)
for k in (1.0, 2.0):
    res.append(avalia((cel_t * k).round(), f"folga sazonal planejada (aeroporto x mês x faixa) x{k:g}"))
# no dia: só quando o tempo na origem é moderado ou severo; folga = acréscimo médio do aeroporto nessa condição (1º ano)
exc = treino.groupby(["origem", "co"]).pos.mean().unstack()
ext = {c: (exc[c] - exc["normal"]).clip(lower=0) for c in ["moderado", "severo"] if c in exc}
extra = pd.Series(0.0, index=teste.index)
for c, serie in ext.items():
    m = teste.co == c
    extra[m] = teste.loc[m, "origem"].map(serie).fillna(0).values
for k in (1.0, 2.0):
    res.append(avalia((extra * k).round(), f"folga no dia, só com tempo ruim x{k:g}"))
comb = (cel_t + extra).round()
res.append(avalia(comb, "sazonal x1 + no dia x1"))
w5 = pd.DataFrame(res)
salvar(w5.round(3), "qc_folga_dinamica.csv")
# efeito esperado só em CGH e VCP (aeroportos do piloto), com a folga do dia descontada a 60% (previsão imperfeita)
loc = teste.origem.isin(["SBSP", "SBKP"])
def local(folga, nome):
    a = teste.loc[loc, "atraso_partida"]; f_ = folga[loc]
    return {"estrategia": nome, "minutos_de_folga_por_voo": f_.mean(), "atraso30_hoje_pct": 100 * (a > 30).mean(),
            "atraso30_com_folga_pct": 100 * ((a - f_) > 30).mean(), "queda_pp": 100 * ((a > 30).mean() - ((a - f_) > 30).mean())}
salvar(pd.DataFrame([local(comb, "sazonal + no dia (previsão perfeita)"), local((cel_t + 0.6 * extra).round(), "sazonal + no dia a 60%"),
                     local(cel_t.round(), "só sazonal")]).round(2), "qc_folga_local_cgh_vcp.csv")

pd.set_option("display.width", 250)
print("cobertura clima", round(cob, 3)); print(w1.round(1).to_string()); print(w1d.round(1).to_string()); print(w2r.round(1).to_string())
print(wa.sort_values("voos", ascending=False).round(1).head(10).to_string())
print(dec.round(3).to_string()); print("corr efeitos aeroporto todos x normal", round(corr_aer, 2))
print(ea.sort_values("efeito_tempo_normal_pp", ascending=False).round(2).head(8).to_string()); print(ee.round(2).to_string())
print(w3.round(2).to_string()); print(cm.round(1).to_string()); print(pd.DataFrame(crise).to_string()); print(w5.round(2).to_string())
