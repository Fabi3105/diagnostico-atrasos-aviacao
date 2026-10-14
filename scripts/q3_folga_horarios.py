# -*- coding: utf-8 -*-
"""Pergunta 3 (com M3 e C2). Horário prometido x partida e chegada reais: as diferenças são mínimas ou há folga?
Ajustar o horário previsto reduziria o atraso?

1. Partida: distribuição da diferença real - previsto (antecipado, no horário, atrasado) por companhia.
2. Folga no tempo de voo (M3): por rota e companhia, duração prevista - duração real mediana. Folga positiva =
   o horário de chegada prometido já embute minutos a mais que o voo costuma levar.
3. Recuperação no ar (C2): voos que saíram com mais de 15 min de atraso; minutos recuperados (atraso de partida
   - atraso de chegada) e parte que chega dentro de 15 min do previsto, por companhia e rota.
4. Voos cronicamente atrasados: mesmo número de voo, mesma origem e hora prevista, com pelo menos 30 operações e
   atraso > 30 min em 50% ou mais delas. Simulação: se o horário previsto desses voos fosse movido para a mediana
   do que realizam, quantos atrasos deixariam de existir (no papel: o passageiro passa a ser avisado do horário real).
5. Simulação de tempo de voo: se a chegada prevista fosse fixada no percentil 50/75/85 da duração real da rota,
   qual seria a taxa de chegada com atraso > 30 min (mantida a partida real)."""
import numpy as np, pandas as pd
from base import voos_escopo, salvar, NOME_CURTO, ICAO_IATA, GRANDES

v = voos_escopo()
for c in ["empresa", "origem", "destino", "voo", "mes"]:
    v[c] = v[c].astype(str)
r = v[~v.cancelado & v.empresa.isin(GRANDES)].copy()
r["companhia"] = r.empresa.map(NOME_CURTO)

# 1. partida
def faixas(s):
    return pd.Series({"antes_5min_ou_mais_pct": 100 * (s <= -5).mean(), "entre_-5_e_+15_pct": 100 * s.between(-4.99, 15).mean(),
                      "15_a_30_pct": 100 * s.between(15.01, 30).mean(), "mais_de_30_pct": 100 * (s > 30).mean(),
                      "mediana_min": s.median(), "p90_min": s.quantile(0.9)})
p1 = r.groupby("companhia").atraso_partida.apply(faixas).unstack()
p1.loc["3 grandes"] = faixas(r.atraso_partida)
c1 = r.groupby("companhia").atraso_chegada.apply(faixas).unstack()
c1.loc["3 grandes"] = faixas(r.atraso_chegada)
salvar(pd.concat({"partida": p1, "chegada": c1}).round(2), "q3_partida_chegada.csv", index=True)

# 2. folga no tempo de voo por rota x companhia
r["rota"] = r.origem + "-" + r.destino
rt = r.groupby(["companhia", "rota"]).agg(voos=("duracao_prev", "size"), prevista=("duracao_prev", "median"),
                                          real_mediana=("duracao_real", "median"), real_p85=("duracao_real", lambda s: s.quantile(0.85)))
rt = rt[rt.voos >= 300]
rt["folga_min"] = rt.prevista - rt.real_mediana
rt["folga_pct_do_voo"] = 100 * rt.folga_min / rt.real_mediana
fe = rt.groupby("companhia").apply(lambda d: pd.Series({
    "rotas": len(d), "folga_media_ponderada_min": np.average(d.folga_min, weights=d.voos),
    "folga_pct_do_voo": np.average(d.folga_pct_do_voo, weights=d.voos),
    "rotas_com_folga_de_10min_ou_mais_pct": 100 * np.average(d.folga_min >= 10, weights=d.voos),
    "rotas_sem_folga_pct": 100 * np.average(d.folga_min <= 0, weights=d.voos)}), include_groups=False)
salvar(fe.round(2), "q3_folga_tempo_de_voo_companhia.csv", index=True)
rt2 = rt.reset_index()
rt2["rota_iata"] = rt2.rota.map(lambda s: "-".join(ICAO_IATA.get(x, x) for x in s.split("-")))
salvar(rt2.sort_values("folga_min", ascending=False).round(1), "q3_folga_por_rota.csv")

# 3. recuperação no ar (C2)
d = r[r.atraso_partida > 15].copy()
d["recuperado_min"] = d.atraso_partida - d.atraso_chegada
d["chegou_ate_15"] = d.atraso_chegada <= 15
d["saiu_atrasado_30_chegou_ate_30"] = (d.atraso_partida > 30) & (d.atraso_chegada <= 30)
rec = d.groupby("companhia").agg(voos_que_sairam_15_atrasados=("recuperado_min", "size"),
                                 minutos_recuperados_mediana=("recuperado_min", "median"),
                                 minutos_recuperados_media=("recuperado_min", "mean"),
                                 chegaram_ate_15min_pct=("chegou_ate_15", "mean"))
rec["chegaram_ate_15min_pct"] *= 100
s30 = r[r.atraso_partida > 30]
rec["sairam_30_e_chegaram_ate_30_pct"] = 100 * s30.groupby("companhia").apply(lambda x: (x.atraso_chegada <= 30).mean(), include_groups=False)
rec["atrasos_de_partida_30"] = s30.groupby("companhia").size()
rec["atrasos_de_chegada_30"] = r[r.atraso_chegada > 30].groupby("companhia").size()
rec["atrasos_evitados_no_ar_liquido"] = rec.atrasos_de_partida_30 - rec.atrasos_de_chegada_30
rec = rec.join(fe[["folga_media_ponderada_min"]])
salvar(rec.round(2), "q3_recuperacao_no_ar_companhia.csv", index=True)
rr = d.groupby(["companhia", "rota"]).agg(voos=("recuperado_min", "size"), recuperado_mediana=("recuperado_min", "median"),
                                         chegaram_ate_15_pct=("chegou_ate_15", "mean")).reset_index()
rr = rr[rr.voos >= 50]; rr["chegaram_ate_15_pct"] *= 100
rr["rota_iata"] = rr.rota.map(lambda s: "-".join(ICAO_IATA.get(x, x) for x in s.split("-")))
rr = rr.merge(rt2[["companhia", "rota", "folga_min"]], on=["companhia", "rota"], how="left")
salvar(rr.sort_values("recuperado_mediana", ascending=False).round(1), "q3_recuperacao_por_rota.csv")
cor = np.corrcoef(rr.dropna().folga_min, rr.dropna().recuperado_mediana)[0, 1]

# 4. voos cronicamente atrasados
r["hora_prev"] = r.hora.astype(int)
k = r.groupby(["companhia", "voo", "origem", "hora_prev"]).agg(ops=("atrasado", "size"), taxa=("atrasado", "mean"),
                                                               mediana=("atraso_partida", "median"))
k = k[k.ops >= 30]
cron = k[k.taxa >= 0.5]
# simulação: horário previsto movido para a mediana realizada do próprio voo
sim = r.merge(cron.reset_index()[["companhia", "voo", "origem", "hora_prev", "mediana"]], on=["companhia", "voo", "origem", "hora_prev"])
sim["atraso_ajustado"] = sim.atraso_partida - sim.mediana
t4 = pd.DataFrame({"medida": ["combinações voo x origem x hora com 30+ operações", "cronicamente atrasadas (>=50% das operações > 30 min)",
                              "operações desses voos", "atraso > 30 min nelas hoje %", "atraso > 30 min com horário na mediana %",
                              "atrasos que deixariam de existir", "parte de todos os atrasos > 30 min das 3 grandes %"],
                   "valor": [len(k), len(cron), len(sim), 100 * (sim.atraso_partida > 30).mean(),
                             100 * (sim.atraso_ajustado > 30).mean(),
                             int((sim.atraso_partida > 30).sum() - (sim.atraso_ajustado > 30).sum()),
                             100 * ((sim.atraso_partida > 30).sum() - (sim.atraso_ajustado > 30).sum()) / (r.atraso_partida > 30).sum()]})
for e in ["Azul", "LATAM", "Gol"]:
    t4.loc[len(t4)] = [f"cronicamente atrasadas: {e}", int((cron.reset_index().companhia == e).sum())]
salvar(t4.round(2), "q3_voos_cronicos.csv")
sens = []
for lim in (0.2, 0.3, 0.4, 0.5):
    cr = k[k.taxa >= lim].reset_index()
    sm = r.merge(cr[["companhia", "voo", "origem", "hora_prev", "mediana"]], on=["companhia", "voo", "origem", "hora_prev"])
    evit = (sm.atraso_partida > 30).sum() - ((sm.atraso_partida - sm.mediana.clip(lower=0)) > 30).sum()
    sens.append({"limite_de_operacoes_atrasadas": lim, "voos_cronicos": len(cr), "operacoes": len(sm),
                 "atrasos_evitados": int(evit), "parte_dos_atrasos_pct": 100 * evit / (r.atraso_partida > 30).sum()})
salvar(pd.DataFrame(sens).round(2), "q3_voos_cronicos_sensibilidade.csv")
print(pd.DataFrame(sens).round(2).to_string())
cl = cron.reset_index(); cl["iata"] = cl.origem.map(ICAO_IATA)
salvar(cl.sort_values("taxa", ascending=False).round(2), "q3_voos_cronicos_lista.csv")

# 5. simulação do tempo de voo previsto no percentil da duração real
q = r.dropna(subset=["duracao_real"]).copy()
pc = q.groupby(["companhia", "rota"]).duracao_real.quantile([0.5, 0.75, 0.85]).unstack()
q = q.join(pc, on=["companhia", "rota"])
linhas = [("hoje", 100 * (q.atraso_chegada > 30).mean(), np.average(q.duracao_prev))]
for pcl in (0.5, 0.75, 0.85):
    cheg_prev_nova = q.atraso_partida * 0 + q[pcl]            # duração prevista nova
    atraso_cheg_novo = q.atraso_chegada + q.duracao_prev - cheg_prev_nova
    linhas.append((f"duração prevista = percentil {int(pcl*100)} da real", 100 * (atraso_cheg_novo > 30).mean(), cheg_prev_nova.mean()))
t5 = pd.DataFrame(linhas, columns=["cenario", "chegada_atraso30_pct", "duracao_prevista_media_min"])
salvar(t5.round(2), "q3_simulacao_tempo_de_voo.csv")

pd.set_option("display.width", 250)
print(pd.concat({"partida": p1, "chegada": c1}).round(1).to_string()); print(fe.round(1).to_string()); print(rec.round(1).to_string())
print("corr folga x recuperação por rota:", round(cor, 2))
print(rr.sort_values("recuperado_mediana", ascending=False).round(1).head(8).to_string())
print(t4.round(1).to_string()); print(t5.round(1).to_string())
