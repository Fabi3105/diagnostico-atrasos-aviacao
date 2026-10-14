# -*- coding: utf-8 -*-
"""Pergunta 2 (com M2). Como o atraso se distribui ao longo do dia; quais horários geram mais atraso; se são
horários específicos e recorrentes ou acúmulo de voos anteriores (efeito bola de neve).

Método:
1. Curva por hora local de partida: voos, taxa de atraso, minutos acumulados (mercado e por companhia).
2. Ordem no dia: taxa de atraso pela posição da partida dentro do dia da companhia no aeroporto (1º voo do dia,
   2º-3º, 4º-10º...). O 1º voo do dia não herda atraso de voo anterior daquela companhia ali.
3. Bola de neve (companhia x aeroporto x dia): a taxa de atraso da tarde/noite (15h-23h) é comparada com
   (a) a manhã (6h-11h) da própria companhia no mesmo aeroporto, (b) a manhã das outras companhias no mesmo
   aeroporto (choque comum: clima, controle de tráfego, pista) e (c) a manhã da própria companhia nos outros
   aeroportos (atraso que chega com o avião e a tripulação). Regressão ponderada com efeitos de companhia,
   aeroporto e mês. Se (a) e (c) pesam mais que (b), o atraso viaja com a operação da companhia.
4. Horários recorrentes: aeroporto x hora com taxa de atraso acima do mercado naquela hora em pelo menos
   75% dos meses (recorrente) e quanto do atraso total eles concentram.
Sem número de cauda (avião) na base: a propagação é medida pela companhia, não por aeronave."""
import numpy as np, pandas as pd
from base import voos_escopo, salvar, NOME_CURTO, ICAO_IATA, GRANDES

v = voos_escopo()
for c in ["empresa", "origem", "mes", "data"]:
    v[c] = v[c].astype(str)
r = v[~v.cancelado].copy()

# ---------- 1. curva por hora
def curva(d):
    g = d.groupby("hora_local")
    t = pd.DataFrame({"voos": g.size(), "atraso30_pct": 100 * g.atrasado.mean(),
                      "minutos_atraso_mil": g.minutos_atraso.sum() / 1e3,
                      "atraso_mediano_min": g.atraso_partida.median()})
    t["parte_dos_voos_pct"] = 100 * t.voos / t.voos.sum()
    t["parte_dos_minutos_pct"] = 100 * t.minutos_atraso_mil / t.minutos_atraso_mil.sum()
    return t
h = curva(r).add_prefix("mercado_")
for e in GRANDES:
    h = h.join(curva(r[r.empresa == e])[["atraso30_pct"]].rename(columns={"atraso30_pct": f"{NOME_CURTO[e]}_atraso30_pct"}))
h.index = h.index.astype(int); h.index.name = "hora_local"
salvar(h.round(2), "q2_curva_hora.csv", index=True)

# ---------- 2. posição da partida no dia da companhia no aeroporto (horário previsto)
r = r.sort_values(["empresa", "origem", "data", "hora_local", "minuto_prev", "voo"])   # ordem pelo minuto previsto
r["posicao"] = r.groupby(["empresa", "origem", "data"]).cumcount() + 1
r["faixa_posicao"] = pd.cut(r.posicao, [0, 1, 3, 10, 30, 1e9], labels=["1º voo do dia", "2º-3º", "4º-10º", "11º-30º", "31º ou mais"])
m = r[r.empresa.isin(GRANDES)]
pos = m.groupby("faixa_posicao", observed=True).agg(voos=("atrasado", "count"), atraso30_pct=("atrasado", "mean"))
pos["atraso30_pct"] *= 100
# 1º voo do dia antes das 9h: ainda não pegou o movimento do aeroporto
pv = m[m.posicao == 1]
pos.loc["1º voo do dia, antes das 9h", ["voos", "atraso30_pct"]] = [(pv.hora_local < 9).sum(), 100 * pv[pv.hora_local < 9].atrasado.mean()]
pos.loc["demais voos antes das 9h", ["voos", "atraso30_pct"]] = [((m.posicao > 1) & (m.hora_local < 9)).sum(),
                                                                 100 * m[(m.posicao > 1) & (m.hora_local < 9)].atrasado.mean()]
salvar(pos.round(2), "q2_posicao_no_dia.csv", index=True)

# ---------- 3. bola de neve
r["periodo"] = np.select([r.hora_local.between(6, 11), r.hora_local.between(15, 23)], ["manha", "tarde"], "outro")
k = r[r.periodo != "outro"].groupby(["empresa", "origem", "data", "periodo"]).agg(n=("atrasado", "size"), a=("atrasado", "sum")).unstack("periodo")
k.columns = [f"{x}_{y}" for x, y in k.columns]
k = k.dropna().reset_index()
k = k[(k.n_manha >= 2) & (k.n_tarde >= 2) & k.empresa.isin(GRANDES)]
# manhã das outras companhias no mesmo aeroporto/dia
tot = k.groupby(["origem", "data"])[["n_manha", "a_manha"]].transform("sum")
allm = r[r.periodo == "manha"].groupby(["origem", "data"]).agg(N=("atrasado", "size"), A=("atrasado", "sum"))
k = k.join(allm, on=["origem", "data"])
k["outras_n"] = k.N - k.n_manha; k["outras_a"] = k.A - k.a_manha
# manhã da própria companhia em outros aeroportos
net = r[r.periodo == "manha"].groupby(["empresa", "data"]).agg(NN=("atrasado", "size"), AA=("atrasado", "sum"))
k = k.join(net, on=["empresa", "data"])
k["rede_n"] = k.NN - k.n_manha; k["rede_a"] = k.AA - k.a_manha
k = k[(k.outras_n >= 2) & (k.rede_n >= 10)].copy()
k["y"] = k.a_tarde / k.n_tarde
k["x_propria"] = k.a_manha / k.n_manha
k["x_outras"] = k.outras_a / k.outras_n
k["x_rede"] = k.rede_a / k.rede_n
k["mes"] = k.data.str[:7]

def wls(d, xs, fe):
    cols = [np.ones(len(d))] + [d[x].values for x in xs]
    for f in fe:
        niv = d[f].value_counts().index
        cols += [(d[f] == n).values.astype(float) for n in niv[1:]]
    X = np.column_stack(cols); w = np.sqrt(d.n_tarde.values)
    b, *_ = np.linalg.lstsq(X * w[:, None], d.y.values * w, rcond=None)
    return b[1:1 + len(xs)]

xs = ["x_propria", "x_outras", "x_rede"]
b = wls(k, xs, ["empresa", "origem", "mes"])
# margem por reamostragem de dias (200 reamostragens)
rng = np.random.default_rng(42); dias = k.data.unique(); bs = []
gi = {d: ix for d, ix in k.groupby("data").indices.items()}
for _ in range(200):
    sel = np.concatenate([gi[d] for d in rng.choice(dias, len(dias))])
    bs.append(wls(k.iloc[sel], xs, ["empresa", "origem", "mes"]))
lo, hi = np.percentile(np.array(bs), [5, 95], axis=0)
sd = k[xs].std()
bn = pd.DataFrame({"fonte": ["manhã da própria companhia no mesmo aeroporto", "manhã das outras companhias no mesmo aeroporto",
                             "manhã da própria companhia nos outros aeroportos"],
                   "coeficiente": b, "margem_baixa": lo, "margem_alta": hi,
                   "efeito_de_10pp_na_manha_sobre_a_tarde_pp": 10 * b,
                   "efeito_padronizado_pp": 100 * b * sd.values})
salvar(bn.round(3), "q2_bola_de_neve.csv")
# leitura simples: tarde conforme a manhã da própria companhia
k["faixa_manha"] = pd.cut(k.x_propria, [-0.01, 0, 0.1, 0.25, 0.5, 1], labels=["0%", "até 10%", "10-25%", "25-50%", "mais de 50%"])
sim = k.groupby("faixa_manha", observed=True)[["a_tarde", "n_tarde", "outras_a", "outras_n"]].apply(lambda d: pd.Series({"dias_companhia_aeroporto": len(d),
        "atraso_tarde_pct": 100 * d.a_tarde.sum() / d.n_tarde.sum(), "atraso_manha_outras_pct": 100 * d.outras_a.sum() / d.outras_n.sum()}))
salvar(sim.round(2), "q2_tarde_conforme_manha.csv", index=True)

# ---------- 4. horários recorrentes por aeroporto
mk = r.groupby("hora_local").atrasado.mean()
ah = r.groupby(["origem", "hora_local", "mes"]).agg(n=("atrasado", "size"), a=("atrasado", "mean"))
ah = ah[ah.n >= 30].reset_index()
ah["acima"] = ah.a > ah.hora_local.map(mk) + 0.03          # 3 pontos acima do mercado naquela hora
rec = ah.groupby(["origem", "hora_local"]).agg(meses=("mes", "size"), meses_acima=("acima", "sum"))
rec = rec[rec.meses >= 12]
rec["recorrente"] = rec.meses_acima / rec.meses >= 0.75
g = r.groupby(["origem", "hora_local"]).agg(voos=("atrasado", "size"), atraso30_pct=("atrasado", "mean"),
                                            minutos_atraso_mil=("minutos_atraso", "sum"))
g["atraso30_pct"] *= 100; g["minutos_atraso_mil"] /= 1e3
rec = rec.join(g)
rec["mercado_na_hora_pct"] = 100 * rec.index.get_level_values("hora_local").map(mk)
rec["parte_dos_minutos_do_mercado_pct"] = 100 * rec.minutos_atraso_mil / (r.minutos_atraso.sum() / 1e3)
rec = rec.reset_index(); rec.insert(1, "iata", rec.origem.map(ICAO_IATA)); rec["hora_local"] = rec.hora_local.astype(int)
salvar(rec[rec.recorrente].sort_values("minutos_atraso_mil", ascending=False).round(2), "q2_horarios_recorrentes.csv")
res = pd.DataFrame({"medida": ["combinações aeroporto x hora analisadas", "recorrentes (≥75% dos meses acima do mercado)",
                               "parte dos voos nas recorrentes %", "parte dos minutos de atraso nas recorrentes %"],
                    "valor": [len(rec), rec.recorrente.sum(), 100 * rec[rec.recorrente].voos.sum() / len(r),
                              rec[rec.recorrente].parte_dos_minutos_do_mercado_pct.sum()]})
salvar(res.round(2), "q2_horarios_recorrentes_resumo.csv")
# sensibilidade do critério de recorrência
sens = []
for pp in (0.02, 0.03, 0.05):
    for frac in (0.6, 0.75):
        a2 = ah.assign(acima=ah.a > ah.hora_local.map(mk) + pp).groupby(["origem", "hora_local"]).agg(meses=("mes", "size"), m=("acima", "sum"))
        a2 = a2[(a2.meses >= 12) & (a2.m / a2.meses >= frac)].join(g)
        sens.append({"pontos_acima_do_mercado": 100 * pp, "fracao_dos_meses": frac, "combinacoes": len(a2),
                     "parte_dos_minutos_pct": 100 * a2.minutos_atraso_mil.sum() / (r.minutos_atraso.sum() / 1e3),
                     "quais": ", ".join(f"{ICAO_IATA.get(o, o)} {int(hh)}h" for o, hh in a2.sort_values("minutos_atraso_mil", ascending=False).index[:8])})
salvar(pd.DataFrame(sens).round(2), "q2_horarios_recorrentes_sensibilidade.csv")
print(pd.DataFrame(sens).round(1).to_string())

pd.set_option("display.width", 250)
print(h.round(1).to_string()); print(pos.round(1).to_string()); print(bn.round(3).to_string()); print(sim.round(1).to_string())
print(res.round(1).to_string()); print(rec[rec.recorrente].sort_values("minutos_atraso_mil", ascending=False).round(1).head(15).to_string())
