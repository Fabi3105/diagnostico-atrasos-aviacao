# -*- coding: utf-8 -*-
"""Revisão crítica, camada 1 (segunda rodada, 14/10/2026). Cálculos pedidos pela revisão do analista do setor:
a) dezembro é estrutural? atraso por mês e ano, só com tempo bom na origem, e dez/25 sem 10 a 12/12 (vendaval);
b) voos não programados (extras) por mês, como hipótese para o fim de ano (competem por avião e tripulação);
c) recuperação no trecho por faixa de duração prevista do voo: meta da Azul ajustada ao próprio mix de etapas;
d) piloto do tempo em solo: menor efeito detectável sorteando dias inteiros na tarde de GRU, e o teto do efeito
   (se as partidas com chegadas atrasadas tivessem a taxa das partidas com chegadas no horário)."""
import numpy as np, pandas as pd
from base import ler, salvar, ESCOPO, VOO_INI, VOO_FIM, DB, RES, voos_escopo

# a) dezembro
v = ler(f"""SELECT origem, situacao, CAST(strftime('%s', partida_prev) AS INTEGER) / 3600 AS hp, atraso_partida, mes, data
            FROM voos WHERE {ESCOPO}""")
cl = ler("""SELECT station, nivel, CAST(strftime('%s', data || ' ' || printf('%02d', hora) || ':00:00') AS INTEGER) / 3600 AS h FROM clima_hora""")
sid = {a: i for i, a in enumerate(sorted(set(cl.station) | set(v.origem.unique())))}
chave = pd.Index(cl.station.map(sid).astype("int64") * 10_000_000 + cl.h); niv = cl.nivel.to_numpy(float)
def f(hh):
    k = v.origem.map(sid).astype("int64").to_numpy() * 10_000_000 + hh.to_numpy()
    ix = chave.get_indexer(k); return np.where(ix >= 0, niv[ix], np.nan)
v["co"] = np.fmax(f(v.hp), f(v.hp - 1))
r = v[v.situacao != "CANCELADO"].copy()
from metodos import erro_de_data                             # tira os erros de data, como em base.voos_escopo
r = r[~erro_de_data(r.atraso_partida.fillna(0))].copy(); r["atr"] = r.atraso_partida > 30
m = r.groupby("mes").agg(voos=("atr", "size"), atraso_pct=("atr", "mean"))
m["atraso_tempo_bom_pct"] = r[r.co == 0].groupby("mes").atr.mean()
m[["atraso_pct", "atraso_tempo_bom_pct"]] *= 100
sem = r[(r.mes == "2025-12") & ~r.data.isin(["2025-12-10", "2025-12-11", "2025-12-12"])]
m.loc["2025-12 sem 10-12/12", ["voos", "atraso_pct", "atraso_tempo_bom_pct"]] = [len(sem), 100 * sem.atr.mean(), 100 * sem[sem.co == 0].atr.mean()]
dz = r[r.mes.str.endswith("-12")]
m.loc["dezembros juntos", ["voos", "atraso_pct", "atraso_tempo_bom_pct"]] = [len(dz), 100 * dz.atr.mean(), 100 * dz[dz.co == 0].atr.mean()]
dzs = dz[~dz.data.isin(["2025-12-10", "2025-12-11", "2025-12-12"])]
m.loc["dezembros juntos sem 10-12/12", ["voos", "atraso_pct", "atraso_tempo_bom_pct"]] = [len(dzs), 100 * dzs.atr.mean(), 100 * dzs[dzs.co == 0].atr.mean()]
# comparação de igual para igual: média dos outros meses com tempo bom
outros = r[(r.co == 0) & ~r.mes.str.endswith(("-11", "-12"))]
m.loc["média dos outros meses (tempo bom, sem nov e dez)", "atraso_tempo_bom_pct"] = 100 * outros.atr.mean()
salvar(m.round(2), "q12a_mes_ano_tempo_bom.csv", index=True)
# dezembro por semana (o pico acaba antes do Natal?)
dz = dz.assign(ano=dz.mes.str[:4], dia=dz.data.str[8:10].astype(int))
dz["semana"] = pd.cut(dz.dia, [0, 7, 15, 23, 31], labels=["1 a 7/12", "8 a 15/12", "16 a 23/12", "24 a 31/12"])
sm = dz.groupby(["semana", "ano"], observed=True).atr.mean().unstack().mul(100)
sm["tempo_bom_dois_anos"] = dz[dz.co == 0].groupby("semana", observed=True).atr.mean().mul(100)
salvar(sm.round(2), "q12e_dezembro_por_semana.csv", index=True)
# ponte aérea: tamanho do prêmio em cancelamentos por ano (teto e meta intermediária)
pm = pd.read_csv(RES / "q8_ponte_aerea_motivos.csv", encoding="utf-8-sig", index_col=0)
P, Rr = pm["ponte aérea CGH-SDU"], pm["resto da rede (aeroportos com METAR)"]
voos_ano = P["cancelamentos"] / (P["taxa_de_cancelamento_pct"] / 100) / 2
sem_ano = voos_ano * P["parte_dos_voos_sem sinal observável_pct"] / 100
teto = sem_ano * (P["taxa_canc_sem sinal observável_pct"] - Rr["taxa_canc_sem sinal observável_pct"]) / 100
salvar(pd.DataFrame([{"voos_ponte_por_ano": voos_ano, "voos_sem_causa_externa_por_ano": sem_ano,
                      "cancelamentos_evitaveis_por_ano_teto": teto, "meta_intermediaria_12_meses": teto / 2,
                      "taxa_intermediaria_pct": (P["taxa_canc_sem sinal observável_pct"] + Rr["taxa_canc_sem sinal observável_pct"]) / 2}]).round(1),
       "q12f_ponte_premio.csv")
# erros de data no VRA: atraso a menos de 90 min de um múltiplo de 24 h (fora o zero)
ad = v.loc[v.situacao != "CANCELADO", "atraso_partida"]   # antes de tirar os erros
erro = erro_de_data(ad.fillna(0))
mins = ad.clip(lower=0).where(ad > 30, 0).clip(upper=1440)
salvar(pd.DataFrame([{"voos_com_erro_de_data": int(erro.sum()), "parte_dos_voos_pct": 100 * erro.mean(),
                      "minutos_totais_mi": mins.sum() / 1e6, "minutos_sem_erros_mi": mins[~erro].sum() / 1e6,
                      "atraso30_pct": 100 * (ad > 30).mean(), "atraso30_sem_erros_pct": 100 * (ad[~erro] > 30).mean()}]).round(3),
       "q12g_erros_de_data.csv")

# b) extras: voos regulares sem horário previsto (não programados) por mês
x = ler(f"""SELECT substr(COALESCE(partida_real, chegada_real), 1, 7) AS mes, COUNT(*) AS nao_programados FROM voos
            WHERE tipo_linha = 'N' AND partida_prev IS NULL AND COALESCE(partida_real, chegada_real) >= '{VOO_INI}'
            AND COALESCE(partida_real, chegada_real) < '{VOO_FIM}' GROUP BY 1""").set_index("mes")
x["programados"] = v.groupby("mes").size()
x["extras_pct_dos_programados"] = 100 * x.nao_programados / x.programados
x["atraso_pct"] = m.atraso_pct
salvar(x.round(2), "q12b_extras_por_mes.csv", index=True)

# c) recuperação no trecho por faixa de duração prevista
e = voos_escopo(); e = e[(~e.cancelado) & (e.atraso_partida > 15) & e.empresa.isin(["AZU", "TAM", "GLO"])].copy()
e["faixa"] = pd.cut(e.duracao_prev, [0, 60, 90, 120, 180, 10_000], labels=["até 60 min", "61-90", "91-120", "121-180", "mais de 180"])
e["rec"] = e.atraso_chegada <= 15
t = e.groupby(["faixa", "empresa"], observed=True).rec.agg(["size", "mean"]).unstack()
mix_azul = t[("size", "AZU")] / t[("size", "AZU")].sum()
out = pd.DataFrame({"voos_azul": t[("size", "AZU")], "parte_dos_voos_azul_pct": 100 * mix_azul,
                    "rec_azul_pct": 100 * t[("mean", "AZU")], "rec_latam_pct": 100 * t[("mean", "TAM")], "rec_gol_pct": 100 * t[("mean", "GLO")]})
out.loc["Azul real"] = [np.nan, 100, 100 * e[e.empresa == "AZU"].rec.mean(), np.nan, np.nan]
out.loc["Azul com a taxa da LATAM em cada faixa"] = [np.nan, 100, 100 * (mix_azul * t[("mean", "TAM")]).sum(), np.nan, np.nan]
out.loc["Azul com a taxa da Gol em cada faixa"] = [np.nan, 100, 100 * (mix_azul * t[("mean", "GLO")]).sum(), np.nan, np.nan]
salvar(out.round(2), "q12c_recuperacao_por_etapa.csv", index=True)

# d) piloto do tempo em solo na tarde de GRU
pk = DB.parent / "q2b.pkl"
if not pk.exists():
    raise SystemExit("q12: rode antes q2b_origem_do_atraso.py, que grava o cache q2b.pkl ao lado do banco")
q = pd.read_pickle(pk)
q["atr"] = q.atraso_partida > 30
dep = q[(q.origem == "SBGR")].copy()
dep["hl"] = (dep.partida_prev // 60) % 24
dep = dep[dep.hl.between(14, 19)].copy()
res = []
for emp, d in dep.groupby("empresa"):
    arr = q[(q.empresa == emp) & (q.destino == "SBGR")]
    ap = arr.chegada_prev.values; ar = arr.chegada_real.values; o = np.argsort(ap); ap, ar = ap[o], ar[o]
    tt = d.partida_prev.values
    lo = np.searchsorted(ap, tt - 180, "left"); hi = np.searchsorted(ap, tt - 35, "right")
    comp = np.array([(ar[a:b] > tt_ - 35).sum() for a, b, tt_ in zip(lo, hi, tt)])
    res.append(pd.DataFrame({"idx": d.index, "n": hi - lo, "comp": comp}))
c = pd.concat(res).set_index("idx"); dep = dep.join(c)
dep["sit"] = np.where(dep.n == 0, "sem chegada", np.where(dep.comp == 0, "no horário", np.where(dep.comp / dep.n >= 0.5, "maioria atrasada", "parte atrasada")))
s = dep.groupby("sit").atr.agg(["size", "mean"]); s["parte_pct"] = 100 * s["size"] / s["size"].sum(); s["atraso_pct"] = 100 * s["mean"]
base_ok = s.loc["no horário", "mean"]
teto = sum(s.loc[k, "size"] * (s.loc[k, "mean"] - base_ok) for k in ["parte atrasada", "maioria atrasada"] if k in s.index) / s["size"].sum()
dia = dep.assign(dia=pd.to_datetime(dep.partida_prev * 60_000_000_000).dt.date).groupby("dia").atr.mean()
sd = dia.std()
d_ = {"taxa_tarde_gru_pct": 100 * dep.atr.mean(), "teto_do_efeito_pp": 100 * teto, "metade_do_teto_pp": 50 * teto,
      "dp_diario_pp": 100 * sd,
      "mde_sorteio_por_dia_90d_pp": 100 * 2.8 * sd * np.sqrt(1 / 45 + 1 / 45),
      "mde_sorteio_por_dia_180d_pp": 100 * 2.8 * sd * np.sqrt(1 / 90 + 1 / 90)}
salvar(pd.concat([s[["size", "parte_pct", "atraso_pct"]].round(2).reset_index(),
                  pd.DataFrame([d_]).round(2)], axis=0), "q12d_piloto_tempo_em_solo.csv")
print(m.round(1).to_string()); print(x.round(1).to_string()); print(out.round(1).to_string()); print(s.round(2).to_string()); print(d_)
