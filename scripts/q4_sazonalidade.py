# -*- coding: utf-8 -*-
"""Pergunta 4 (com M4 e C3). Dias, quinzenas e meses de pico; como esses períodos agravam os picos de horário;
efeito do volume x efeito de cada voo atrasar mais; concentração dos cancelamentos em dias de crise.

- Feriados nacionais e Carnaval (calendário oficial) com a véspera e o dia seguinte; férias escolares de verão
  (15/dez a 10/fev) e de julho. Datas listadas abaixo.
- Volume: voos previstos no dia em relação à média do mesmo dia da semana no mês (índice de carga).
- Regressão diária (ponderada pelos voos): taxa de atraso ~ carga do dia + feriado + férias + dia da semana + mês.
- Decomposição dos atrasos a mais nos meses de pico: parte por mais voos e parte por taxa maior.
- Curva por hora nos dias de pico (10% de dias com mais voos e feriados) x dias comuns.
- C3: parte dos cancelamentos do período nos 10 e 20 piores dias; lista dos dias de crise e aeroportos mais afetados."""
import numpy as np, pandas as pd
from base import voos_escopo, salvar, ICAO_IATA, NOME_CURTO, GRANDES

FERIADOS = {  # nacionais + Carnaval (ponto facultativo com grande efeito no movimento)
    "2024-09-07": "Independência", "2024-10-12": "N. Sra. Aparecida", "2024-11-02": "Finados",
    "2024-11-15": "Proclamação da República", "2024-11-20": "Consciência Negra", "2024-12-25": "Natal",
    "2025-01-01": "Ano Novo", "2025-03-03": "Carnaval", "2025-03-04": "Carnaval", "2025-04-18": "Sexta-feira Santa",
    "2025-04-21": "Tiradentes", "2025-05-01": "Dia do Trabalho", "2025-06-19": "Corpus Christi",
    "2025-09-07": "Independência", "2025-10-12": "N. Sra. Aparecida", "2025-11-02": "Finados",
    "2025-11-15": "Proclamação da República", "2025-11-20": "Consciência Negra", "2025-12-25": "Natal",
    "2026-01-01": "Ano Novo", "2026-02-16": "Carnaval", "2026-02-17": "Carnaval", "2026-04-03": "Sexta-feira Santa",
    "2026-04-21": "Tiradentes", "2026-05-01": "Dia do Trabalho", "2026-06-04": "Corpus Christi",
}
v = voos_escopo()
for c in ["empresa", "origem", "data", "mes"]:
    v[c] = v[c].astype(str)
v["dt"] = pd.to_datetime(v.data)
r = v[~v.cancelado].copy()

dia = v.groupby("dt").agg(previstos=("cancelado", "size"), cancelados=("cancelado", "sum"))
dr = r.groupby("dt")
dia["atraso30_pct"] = 100 * dr.atrasado.mean()
dia["minutos_atraso_mil"] = dr.minutos_atraso.sum() / 1e3
dia["cancelamento_pct"] = 100 * dia.cancelados / dia.previstos
dia["dia_semana"] = dia.index.dayofweek
dia["mes"] = dia.index.strftime("%Y-%m")
dia["mes_do_ano"] = dia.index.month
dia["quinzena"] = np.where(dia.index.day <= 15, "1ª", "2ª")
fer = pd.to_datetime(list(FERIADOS))
dia["feriado"] = dia.index.isin(fer)
dia["vespera_ou_dia_seguinte"] = dia.index.isin(fer - pd.Timedelta(days=1)) | dia.index.isin(fer + pd.Timedelta(days=1))
dia["vespera_ou_dia_seguinte"] &= ~dia.feriado
md = dia.index.month * 100 + dia.index.day
dia["ferias"] = np.select([(md >= 1215) | (md <= 210), dia.index.month == 7], ["verão", "julho"], "fora das férias")
dia["carga"] = dia.previstos / dia.groupby(["mes", "dia_semana"]).previstos.transform("mean")
salvar(dia.round(3).reset_index().rename(columns={"dt": "data"}), "q4_serie_diaria.csv")

# --- 1. meses, quinzenas, dias da semana
def tab(chave):
    g = r.assign(**{chave: r.dt.map(dia[chave]) if chave in dia else r[chave]}).groupby(chave)
    t = pd.DataFrame({"voos_realizados": g.size(), "atraso30_pct": 100 * g.atrasado.mean(),
                      "minutos_atraso_mil": g.minutos_atraso.sum() / 1e3})
    gv = v.assign(**{chave: v.dt.map(dia[chave]) if chave in dia else v[chave]}).groupby(chave)
    t["cancelamento_pct"] = 100 * gv.cancelado.mean()
    t["voos_por_dia"] = gv.size() / gv.dt.nunique()
    return t
tm = tab("mes"); salvar(tm.round(2), "q4_por_mes.csv", index=True)
r["mes_do_ano"] = r.dt.dt.month; v["mes_do_ano"] = v.dt.dt.month
tma = tab("mes_do_ano"); salvar(tma.round(2), "q4_por_mes_do_ano.csv", index=True)
r["mes_quinzena"] = r.mes + " " + np.where(r.dt.dt.day <= 15, "1ª", "2ª"); v["mes_quinzena"] = v.mes + " " + np.where(v.dt.dt.day <= 15, "1ª", "2ª")
tq = tab("mes_quinzena"); salvar(tq.round(2), "q4_por_quinzena.csv", index=True)
r["dia_semana"] = r.dt.dt.dayofweek; v["dia_semana"] = v.dt.dt.dayofweek
tw = tab("dia_semana"); tw.index = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
salvar(tw.round(2), "q4_por_dia_semana.csv", index=True)

# --- 2. eventos: feriados e férias
ev = dia.assign(evento=np.select([dia.feriado, dia.vespera_ou_dia_seguinte], ["feriado", "véspera/dia seguinte"], "dia comum"))
te = ev.groupby(["evento"]).apply(lambda d: pd.Series({"dias": len(d), "voos_por_dia": d.previstos.mean(),
        "atraso30_pct": np.average(d.atraso30_pct, weights=d.previstos), "cancelamento_pct": np.average(d.cancelamento_pct, weights=d.previstos)}), include_groups=False)
tf = ev.groupby(["ferias"]).apply(lambda d: pd.Series({"dias": len(d), "voos_por_dia": d.previstos.mean(),
        "atraso30_pct": np.average(d.atraso30_pct, weights=d.previstos), "cancelamento_pct": np.average(d.cancelamento_pct, weights=d.previstos)}), include_groups=False)
salvar(pd.concat({"feriados": te, "férias": tf}).round(2), "q4_eventos.csv", index=True)

# --- 3. regressão diária: volume x eventos
X = pd.DataFrame({"carga_10pct": (dia.carga - 1) * 10, "feriado": dia.feriado.astype(float),
                  "vespera_dia_seguinte": dia.vespera_ou_dia_seguinte.astype(float),
                  "ferias_verao": (dia.ferias == "verão").astype(float), "ferias_julho": (dia.ferias == "julho").astype(float)})
# sem dummies de mês (as férias são meses inteiros); dia da semana como controle
for k in range(1, 7):
    X[f"dow{k}"] = (dia.dia_semana == k).astype(float)
def reg(y):
    A = np.column_stack([np.ones(len(X)), X.values]); w = np.sqrt(dia.previstos.values)
    b = np.linalg.lstsq(A * w[:, None], y * w, rcond=None)[0]
    rng = np.random.default_rng(3); bs = []
    for _ in range(500):
        ix = rng.integers(0, len(y), len(y)); bs.append(np.linalg.lstsq(A[ix] * w[ix, None], y[ix] * w[ix], rcond=None)[0])
    lo, hi = np.percentile(bs, [5, 95], axis=0)
    return pd.DataFrame({"coef_pp": b[1:6], "margem_baixa": lo[1:6], "margem_alta": hi[1:6]}, index=X.columns[:5])
rg = pd.concat({"atraso30": reg(dia.atraso30_pct.values), "cancelamento": reg(dia.cancelamento_pct.values)})
salvar(rg.round(3), "q4_regressao_diaria.csv", index=True)

# --- 4. decomposição volume x taxa por mês do ano (em relação à média do período)
base_voos = tma.voos_por_dia.mean(); base_taxa = np.average(tma.atraso30_pct, weights=tma.voos_realizados)
dec = pd.DataFrame({"voos_por_dia": tma.voos_por_dia, "atraso30_pct": tma.atraso30_pct})
dec["atrasos_por_dia"] = dec.voos_por_dia * dec.atraso30_pct / 100
dec["a_mais_por_volume"] = (dec.voos_por_dia - base_voos) * base_taxa / 100
dec["a_mais_por_taxa"] = base_voos * (dec.atraso30_pct - base_taxa) / 100
dec["a_mais_interacao"] = (dec.voos_por_dia - base_voos) * (dec.atraso30_pct - base_taxa) / 100
salvar(dec.round(2), "q4_decomposicao_volume_taxa.csv", index=True)

# --- 5. curva por hora: dias de pico x dias comuns
pico = dia.index[(dia.previstos >= dia.previstos.quantile(0.9)) | dia.feriado | dia.vespera_ou_dia_seguinte]
ferias_dias = dia.index[dia.ferias != "fora das férias"]
r["tipo_dia"] = np.select([r.dt.isin(pico), r.dt.isin(ferias_dias)], ["pico (10% mais cheios e feriados)", "férias (demais dias)"], "dia comum")
hc = r.groupby(["hora_local", "tipo_dia"]).atrasado.mean().unstack().mul(100)
hc.index = hc.index.astype(int)
hc["diferenca_pico_menos_comum_pp"] = hc.iloc[:, hc.columns.get_loc("pico (10% mais cheios e feriados)")] - hc["dia comum"]
salvar(hc.round(2), "q4_hora_por_tipo_de_dia.csv", index=True)
vh = r.groupby(["tipo_dia"]).size() / r.groupby("tipo_dia").dt.nunique()

# --- 6. C3: dias de crise (cancelamentos)
cs = dia.sort_values("cancelados", ascending=False)
tot = dia.cancelados.sum()
cri = pd.DataFrame({"medida": ["cancelamentos no período", "parte nos 10 piores dias %", "parte nos 20 piores dias %",
                               "parte nos 5% piores dias (36 dias) %", "dia mediano: cancelamentos", "parte dos atrasos (min) nos 20 piores dias %"],
                    "valor": [tot, 100 * cs.cancelados.head(10).sum() / tot, 100 * cs.cancelados.head(20).sum() / tot,
                              100 * cs.cancelados.head(int(len(dia) * 0.05)).sum() / tot, dia.cancelados.median(),
                              100 * dia.sort_values("minutos_atraso_mil", ascending=False).minutos_atraso_mil.head(20).sum() / dia.minutos_atraso_mil.sum()]})
salvar(cri.round(2), "q4_dias_de_crise_resumo.csv")
top = cs.head(20).copy()
vc = v[v.cancelado & v.dt.isin(top.index)]
top["aeroportos_mais_afetados"] = [", ".join(f"{ICAO_IATA.get(a, a)} {n}" for a, n in vc[vc.dt == d].origem.value_counts().head(3).items()) for d in top.index]
top["companhias"] = [", ".join(f"{NOME_CURTO.get(a, a)} {n}" for a, n in vc[vc.dt == d].empresa.value_counts().head(3).items()) for d in top.index]
top["parte_no_1o_aeroporto_pct"] = [100 * vc[vc.dt == d].origem.value_counts().iloc[0] / len(vc[vc.dt == d]) for d in top.index]
salvar(top[["previstos", "cancelados", "cancelamento_pct", "atraso30_pct", "aeroportos_mais_afetados", "companhias", "parte_no_1o_aeroporto_pct"]].round(1).reset_index().rename(columns={"dt": "data"}), "q4_dias_de_crise.csv")
# sem as regionais (Azul Conecta e Voepass têm cancelamento estrutural)
g3 = v[v.empresa.isin(GRANDES)].groupby("dt").cancelado.sum().sort_values(ascending=False)
cri.loc[len(cri)] = ["só Azul, LATAM e Gol: parte nos 20 piores dias %", 100 * g3.head(20).sum() / g3.sum()]
salvar(cri.round(2), "q4_dias_de_crise_resumo.csv")

pd.set_option("display.width", 250)
print(tma.round(1).to_string()); print(tw.round(1).to_string()); print(pd.concat({"feriados": te, "férias": tf}).round(1).to_string())
print(rg.round(2).to_string()); print(dec.round(0).to_string()); print(hc.round(1).to_string()); print(vh.round(0))
print(cri.round(1).to_string()); print(top[["cancelados", "cancelamento_pct", "atraso30_pct", "aeroportos_mais_afetados", "companhias", "parte_no_1o_aeroporto_pct"]].round(1).to_string())
q = tq.sort_values("atraso30_pct", ascending=False); print(q.head(8).round(1).to_string())
