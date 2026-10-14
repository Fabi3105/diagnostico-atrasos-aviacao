# -*- coding: utf-8 -*-
"""Motivos de cancelamento a partir do VRA de 2019 (último ano completo, antes da pandemia, com código de justificativa)
e estimativa para 2024-26 por calibração com o clima. Pedido do Fabian (10/10/2026).

Dados: vra2019_justificados.csv (voos de 2019 com código), vra2019_contagem_rotas.csv (totais por rota e situação),
metar_aeroportos_2019.csv; códigos da IAC 1504, Anexo 2 (iac1504_codigos_cancelamento.csv).
Limites declarados: o código é autodeclarado pela companhia (a Folhapress mostrou 35% de justificativas divergentes entre
CGH e SDU em 2023); 2019 é anterior à pandemia e à saída da Avianca Brasil; o dado é defasado e serve para melhorar a
identificação dos motivos, não como medida atual.

1. Checagem: taxa de cancelamento de 2019 x 1,85% publicado pelo Metrópoles (jan-jul/2019, dados ANAC).
2. Motivos declarados em 2019 (Azul, LATAM, Gol; voos domésticos): ponte aérea CGH-SDU x resto da rede.
3. Comparabilidade 2019 x 2024-26 na ponte: taxa de cancelamento e cancelamentos em par ida e volta.
4. Calibração: cada cancelamento de 2019 recebe o mesmo sinal usado hoje (evento no aeroporto, tempo ruim pelo METAR, fim do
   dia, sem sinal). A tabela P(motivo declarado | sinal) de 2019 é aplicada à distribuição de sinais de 2024-26
   (q8_ponte_aerea.py), com margem por reamostragem dos cancelamentos de 2019.
5. Consistência do código: parte dos cancelamentos declarados como clima em que o METAR mostrava tempo normal, e vice-versa."""
import numpy as np, pandas as pd
from base import RAIZ, salvar, RES, GRANDES, FUSO_AEROPORTO

EXT = RAIZ / "dados" / "externos"
cod = pd.read_csv(EXT / "iac1504_codigos_cancelamento.csv").set_index("codigo").grupo
j = pd.read_csv(EXT / "vra2019_justificados.csv", sep=";", dtype=str)
j.columns = ["empresa", "voo", "di", "tipo", "origem", "destino", "pp", "pr", "cp", "cr", "situacao", "cod"]
ag = pd.read_csv(EXT / "vra2019_contagem_rotas.csv", sep=";")

# ---------- 1. checagem
tx_total = 100 * ag[ag.situacao == "CANCELADO"].voos.sum() / ag.voos.sum()
chk = pd.DataFrame({"medida": ["cancelamento 2019, todas as companhias e linhas (arquivo baixado) %", "publicado pelo Metrópoles (jan-jul/2019) %",
                               "cancelamentos com código de justificativa %"],
                    "valor": [tx_total, 1.85, 100 * (j.situacao == "CANCELADO").sum() / ag[ag.situacao == "CANCELADO"].voos.sum()]})

# ---------- 2. motivos declarados em 2019
c = j[(j.situacao == "CANCELADO") & (j.tipo == "N") & j.empresa.isin(GRANDES)].copy()
c["grupo"] = c.cod.map(cod).fillna("outro")
c["ponte"] = ((c.origem == "SBSP") & (c.destino == "SBRJ")) | ((c.origem == "SBRJ") & (c.destino == "SBSP"))
c["t"] = pd.to_datetime(c.pp)
c["tmin"] = c.t.astype("int64") // 60_000_000_000
c["data"] = c.t.dt.strftime("%Y-%m-%d"); c["hora"] = c.t.dt.hour
mot = pd.concat({"ponte aérea CGH-SDU": c[c.ponte].grupo.value_counts(normalize=True),
                 "resto da rede": c[~c.ponte].grupo.value_counts(normalize=True)}, axis=1).mul(100)
mot.loc["cancelamentos (n)"] = [c.ponte.sum(), (~c.ponte).sum()]
codp = pd.concat({"ponte": c[c.ponte].cod.value_counts(normalize=True), "rede": c[~c.ponte].cod.value_counts(normalize=True)}, axis=1).mul(100)

# ---------- 3. comparabilidade
g3 = ag[(ag.tipo_linha == "N") & ag.empresa.isin(GRANDES)]
pm = ((g3.origem == "SBSP") & (g3.destino == "SBRJ")) | ((g3.origem == "SBRJ") & (g3.destino == "SBSP"))
taxa_ponte19 = 100 * g3[pm & (g3.situacao == "CANCELADO")].voos.sum() / g3[pm].voos.sum()
taxa_rede19 = 100 * g3[~pm & (g3.situacao == "CANCELADO")].voos.sum() / g3[~pm].voos.sum()
def pares(d):
    d = d.reset_index(drop=True); ok = np.zeros(len(d), bool)
    for _, ix in d.groupby(["empresa", "data"]).groups.items():
        x = d.loc[ix]
        for i_, row in x.iterrows():
            ok[i_] = ((x.origem == row.destino) & (x.destino == row.origem) & ((x.tmin - row.tmin).abs() <= 180)).any()
    return 100 * ok.mean()
q8 = pd.read_csv(RES / "q8_ponte_aerea_motivos.csv", index_col=0)
comp = pd.DataFrame({"2019": [taxa_ponte19, taxa_rede19, pares(c[c.ponte])],
                     "2024-26": [q8.loc["taxa_de_cancelamento_pct", "ponte aérea CGH-SDU"], 1.54, q8.loc["cancelamentos_em_par_ida_e_volta_pct", "ponte aérea CGH-SDU"]]},
                    index=["cancelamento na ponte %", "cancelamento no resto da rede %", "cancelamentos da ponte em par ida e volta %"])

# ---------- 4. calibração com o clima de 2019 (mesmos critérios de clima.py)
m = pd.read_csv(EXT / "metar_aeroportos_2019.csv", dtype=str)
for k in ["vsby", "skyl1", "skyl2", "skyl3", "gust"]:
    m[k] = pd.to_numeric(m[k], errors="coerce")
wx = m.wxcodes.fillna("")
teto = pd.Series(np.inf, index=m.index)
for i in (1, 2, 3):
    camada = m[f"skyc{i}"].isin(["BKN", "OVC", "VV"])
    teto = np.where(camada & (m[f"skyl{i}"] < teto), m[f"skyl{i}"], teto)
sev = wx.str.contains(r"(?<!VC)TS", regex=True) | wx.str.contains(r"\+(?:TS)?(?:SH)?RA", regex=True) | (m.vsby < 1) | (teto < 500) | (m.gust >= 35)
mod = wx.str.contains("VCTS") | wx.str.contains(r"(?:^|\s)-?(?:SH)?RA") | wx.str.contains(r"(?:^|\s)FG") | m.vsby.between(1, 3, inclusive="left") | \
      ((teto >= 500) & (teto < 1000)) | m.gust.between(25, 34.9)
m["nivel"] = np.select([sev, mod], [2, 1], 0)
t = pd.to_datetime(m.valid)
m["h"] = t.astype("int64") // 3_600_000_000_000
nv = m.groupby(["station", "h"]).nivel.max().to_dict()
c["hp"] = c.tmin // 60
c["hc"] = pd.to_datetime(c.cp).astype("int64") // 3_600_000_000_000
co = np.array([max(nv.get((a, h), -1), nv.get((a, h - 1), -1)) for a, h in zip(c.origem, c.hp)], float)
cd = np.array([nv.get((a, h), -1) for a, h in zip(c.destino, c.hc)], float)
co[co < 0] = np.nan; cd[cd < 0] = np.nan
c["tempo_ruim"] = (np.nan_to_num(co) > 0) | (np.nan_to_num(cd) > 0)
c["com_metar"] = ~(np.isnan(co) & np.isnan(cd))
# evento no aeroporto: cancelamentos do aeroporto no dia (todas as companhias) >= 25% do movimento diário médio de 2019
todos = j[j.situacao == "CANCELADO"].copy(); todos["data"] = todos.pp.str[:10]
canc_dia = pd.concat([todos[["origem", "data"]].rename(columns={"origem": "a"}), todos[["destino", "data"]].rename(columns={"destino": "a"})]).groupby(["a", "data"]).size()
mov_dia = (ag.groupby("origem").voos.sum().add(ag.groupby("destino").voos.sum(), fill_value=0) / 365)
ev = canc_dia[canc_dia >= 0.25 * mov_dia.reindex(canc_dia.index.get_level_values("a")).values]
evs = set(ev.index)
c["evento"] = [(o, d) in evs or (de, d) in evs for o, de, d in zip(c.origem, c.destino, c.data)]
c["hora_local"] = (c.hora + c.origem.map(FUSO_AEROPORTO).fillna(0)) % 24
c["sinal"] = np.select([c.evento, c.tempo_ruim, c.hora_local >= 21], ["evento no aeroporto", "tempo ruim", "fim do dia (após 21h)"], "sem sinal observável")
cal = pd.crosstab(c[c.com_metar].sinal, c[c.com_metar].grupo, normalize="index").mul(100)
cal_p = pd.crosstab(c[c.com_metar & c.ponte].sinal, c[c.com_metar & c.ponte].grupo, normalize="index").mul(100)
nsin = c[c.com_metar].sinal.value_counts(); nsin_p = c[c.com_metar & c.ponte].sinal.value_counts()

# aplica à ponte de 2024-26 (usa a tabela da rede inteira, mais estável; a da ponte é mostrada para comparação)
sin_atual = q8.loc[["evento no aeroporto", "tempo ruim", "fim do dia (após 21h)", "sem sinal observável"], "ponte aérea CGH-SDU"] / 100
def estima(d):
    tb = pd.crosstab(d.sinal, d.grupo, normalize="index")
    tb = tb.reindex(sin_atual.index).fillna(0)
    return (tb.mul(sin_atual, axis=0)).sum() * 100
base_cal = c[c.com_metar]
est = estima(base_cal)
rng = np.random.default_rng(11); bs = []
for _ in range(500):
    bs.append(estima(base_cal.sample(len(base_cal), replace=True, random_state=int(rng.integers(1e9)))))
bs = pd.DataFrame(bs).fillna(0)
est_p = estima(base_cal[base_cal.ponte])
estt = pd.DataFrame({"estimativa_ponte_2024_26_pct": est, "estimativa_com_tabela_so_da_ponte_pct": est_p, "margem_baixa": bs.quantile(0.05), "margem_alta": bs.quantile(0.95),
                     "declarado_na_ponte_em_2019_pct": mot["ponte aérea CGH-SDU"].drop("cancelamentos (n)")}).fillna(0)

# ---------- 5. consistência código x METAR
x = c[c.com_metar]
cons = pd.DataFrame({"medida": ["declarados como clima com tempo normal no METAR (origem e destino) %",
                                "declarados como técnico-operacional com tempo ruim no METAR %",
                                "declarados como aeroporto fechado sem evento nem tempo ruim %",
                                "cancelamentos de 2019 com METAR disponível %"],
                     "valor": [100 * (~x[x.grupo == "clima"].tempo_ruim).mean(),
                               100 * x[x.grupo == "técnico-operacional (companhia)"].tempo_ruim.mean(),
                               100 * (~x[x.grupo == "aeroporto fechado"].tempo_ruim & ~x[x.grupo == "aeroporto fechado"].evento).mean(),
                               100 * c.com_metar.mean()]})

salvar(chk.round(2), "q9_checagem_2019.csv")
salvar(mot.round(1), "q9_motivos_declarados_2019.csv", index=True)
salvar(codp.round(1), "q9_codigos_2019.csv", index=True)
salvar(comp.round(2), "q9_comparabilidade_ponte.csv", index=True)
salvar(pd.concat({"rede (usada)": cal.assign(n=nsin), "ponte (comparação)": cal_p.assign(n=nsin_p)}).round(1), "q9_calibracao_sinal_x_motivo_2019.csv", index=True)
salvar(estt.round(1), "q9_estimativa_motivos_ponte_2024_26.csv", index=True)
salvar(cons.round(1), "q9_consistencia_codigo_metar.csv")
pd.set_option("display.width", 220)
for t_ in [chk, mot, codp, comp, pd.concat({"rede": cal.assign(n=nsin), "ponte": cal_p.assign(n=nsin_p)}), estt, cons]:
    print(t_.round(1).to_string()); print()
