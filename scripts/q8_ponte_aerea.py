# -*- coding: utf-8 -*-
"""Cancelamentos da ponte aérea CGH-SDU (pedido do Fabian): o que dá para estimar sobre os motivos sem o campo de
justificativa. Classificação aproximada, em ordem de prioridade, para cada voo cancelado (três grandes):
1. Evento no aeroporto: dia em que o aeroporto de origem ou destino cancelou 25% ou mais de todos os seus voos
   (todas as companhias): fechamento de pista, vendaval etc.
2. Tempo ruim: tempo moderado ou severo (METAR) na origem (hora prevista ou anterior) ou no destino (hora de chegada).
3. Fim do dia: partida prevista a partir das 21h (perto do fechamento de CGH e SDU às 23h; atraso acumulado tende a
   virar cancelamento).
4. Demais: sem sinal observável (decisão de malha, manutenção, tripulação, comercial).
Sinal adicional: "cancelamento em par" = a mesma companhia cancela a ida e a volta no mesmo dia em até 3 horas
(ajuste típico de rotação do avião). Comparação com o resto da rede das mesmas companhias."""
import numpy as np, pandas as pd
from base import ler, salvar, ESCOPO, GRANDES, FUSO_AEROPORTO

v = ler(f"""SELECT empresa, voo, origem, destino, situacao, CAST(strftime('%s', partida_prev) AS INTEGER) / 60 tmin,
            CAST(strftime('%s', chegada_prev) AS INTEGER) / 3600 hc, data, hora FROM voos WHERE {ESCOPO}""")
v["canc"] = v.situacao == "CANCELADO"
v["hp"] = v.tmin // 60
cl = ler("""SELECT station, nivel, CAST(strftime('%s', data || ' ' || printf('%02d', hora) || ':00:00') AS INTEGER) / 3600 h FROM clima_hora""")
nv = dict(zip(zip(cl.station, cl.h), cl.nivel))
g = lambda a, h: np.array([nv.get(k, np.nan) for k in zip(a, h)])
# taxa de cancelamento diária de cada aeroporto (todas as companhias, partidas + chegadas)
mov = pd.concat([v[["origem", "data", "canc"]].rename(columns={"origem": "aer"}), v[["destino", "data", "canc"]].rename(columns={"destino": "aer"})])
evento = mov.groupby(["aer", "data"]).canc.mean()
evento = set(evento[evento >= 0.25].index)

def classifica(d):
    d = d.copy()
    d["ev"] = [(o, dt) in evento or (de, dt) in evento for o, de, dt in zip(d.origem, d.destino, d.data)]
    co = np.fmax(g(d.origem, d.hp), g(d.origem, d.hp - 1)); cd = g(d.destino, d.hc)
    d["tempo_ruim"] = (np.nan_to_num(co) > 0) | (np.nan_to_num(cd) > 0)
    d["sem_dado_clima"] = np.isnan(co) & np.isnan(cd)
    d["hora_local"] = (d.hora + d.origem.map(FUSO_AEROPORTO).fillna(0)) % 24
    d["fim_do_dia"] = d.hora_local >= 21
    d["classe"] = np.select([d.ev, d.tempo_ruim, d.fim_do_dia], ["evento no aeroporto", "tempo ruim", "fim do dia (após 21h)"],
                            "sem sinal observável")
    return d

pa_mask = v.empresa.isin(GRANDES) & (((v.origem == "SBSP") & (v.destino == "SBRJ")) | ((v.origem == "SBRJ") & (v.destino == "SBSP")))
rede_mask = v.empresa.isin(GRANDES) & ~pa_mask & v.origem.isin(cl.station.unique()) & v.destino.isin(cl.station.unique())
res = {}
for nome, m in [("ponte aérea CGH-SDU", pa_mask), ("resto da rede (aeroportos com METAR)", rede_mask)]:
    d = classifica(v[m & v.canc])
    t = d.classe.value_counts(normalize=True).mul(100)
    t["cancelamentos"] = len(d); t["taxa_de_cancelamento_pct"] = 100 * v[m].canc.mean()
    # base: parte dos voos (não só cancelados) em cada condição, para comparar
    base = classifica(v[m])
    for k in ["evento no aeroporto", "tempo ruim", "fim do dia (após 21h)", "sem sinal observável"]:
        t[f"taxa_canc_{k}_pct"] = 100 * v[m].canc[base.classe == k].mean() if (base.classe == k).any() else np.nan
        t[f"parte_dos_voos_{k}_pct"] = 100 * (base.classe == k).mean()
    # pares ida e volta cancelados: existe cancelamento no sentido oposto, mesma companhia, até 3 h antes ou depois
    d = d.reset_index(drop=True); emp_par = np.zeros(len(d), bool)
    for (e, dt), ix in d.groupby(["empresa", "data"]).groups.items():
        x = d.loc[ix]
        for i_, row in x.iterrows():
            emp_par[i_] = ((x.origem == row.destino) & (x.destino == row.origem) & ((x.tmin - row.tmin).abs() <= 180)).any()
    t["cancelamentos_em_par_ida_e_volta_pct"] = 100 * emp_par.mean()
    res[nome] = t
out = pd.DataFrame(res)
salvar(out.round(2), "q8_ponte_aerea_motivos.csv", index=True)
# por companhia na ponte
d = classifica(v[pa_mask & v.canc])
pc = pd.crosstab(d.empresa, d.classe, normalize="index").mul(100)
pc["taxa_canc_pct"] = 100 * v[pa_mask].groupby("empresa").canc.mean()
salvar(pc.round(1), "q8_ponte_por_companhia.csv", index=True)
# por hora prevista (local) na ponte
h = v[pa_mask].assign(h=lambda x: x.hora).groupby("h").canc.agg(["size", "mean"])
h["mean"] *= 100
salvar(h.round(2), "q8_ponte_por_hora.csv", index=True)
pd.set_option("display.width", 220)
print(out.round(1).to_string()); print(pc.round(1).to_string()); print(h.round(1).T.to_string())
