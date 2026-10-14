# -*- coding: utf-8 -*-
"""Pergunta 6 (com M6), C1 e C4.
P6: companhias com problemas recorrentes em aeroportos específicos? O aeroporto gera recorrência entre companhias
    ou a companhia leva a reclamação de aeroporto em aeroporto?
- Reclamações com aeroporto informado no código classificador (operação doméstica), Azul, LATAM e Gol, período comum.
  Denominador: movimentos da companhia no aeroporto (partidas + chegadas previstas, voos domésticos regulares).
- Modelo aditivo companhia + aeroporto (células ponderadas por movimentos) e divisão de Shapley, como na P1.
- Perfil de temas da companhia num aeroporto comparado com (a) o perfil da mesma companhia nos outros aeroportos e
  (b) o perfil das outras companhias no mesmo aeroporto.
- M6: por mês, companhia x aeroporto acima de 1,2 vez o esperado pelo modelo em 75% dos meses = crônico; de 50% a 75% =
  frequente; menos que isso, mas com algum mês acima de 2 vezes = pico pontual.
C1: reclamações operacionais (temas de alteração pela empresa, comunicação, alternativas, assistência, preterição e
    execução do voo) por 10 mil movimentos x taxa de atraso e de cancelamento das partidas, companhia x aeroporto x mês,
    com efeitos fixos de companhia x aeroporto e de mês (variação dentro do mesmo par ao longo dos meses).
C4: rotas (companhia x origem x destino) com mais minutos de atraso e cancelamentos, com a taxa de reclamação dos
    aeroportos de origem e destino da mesma companhia."""
import numpy as np, pandas as pd
from base import ler, salvar, TEMA, NOME_CURTO, ICAO_IATA, IATA_ICAO, CRUZ_INI, CRUZ_FIM, ESCOPO, GRANDES

nome = lambda e: NOME_CURTO.get(e, e)
per = f"partida_prev >= '{CRUZ_INI}' AND partida_prev < '{CRUZ_FIM}'"
dep = ler(f"""SELECT empresa, origem aer, substr(partida_prev,1,7) mes, COUNT(*) partidas,
              SUM(situacao='CANCELADO') canc, SUM(situacao='REALIZADO' AND atraso_partida > 30) atr,
              SUM(situacao='REALIZADO') real FROM voos WHERE {ESCOPO} AND {per} AND empresa IN ('AZU','TAM','GLO','ACN')
              GROUP BY 1,2,3""")
arr = ler(f"""SELECT empresa, destino aer, substr(partida_prev,1,7) mes, COUNT(*) chegadas FROM voos
              WHERE {ESCOPO} AND {per} AND empresa IN ('AZU','TAM','GLO','ACN') GROUP BY 1,2,3""")
for d in (dep, arr):
    d["empresa"] = d.empresa.replace({"ACN": "AZU"})               # Azul Conecta voa com a marca Azul
dep = dep.groupby(["empresa", "aer", "mes"], as_index=False).sum()
arr = arr.groupby(["empresa", "aer", "mes"], as_index=False).sum()
mv = dep.merge(arr, on=["empresa", "aer", "mes"], how="outer").fillna(0)
mv["mov"] = mv.partidas + mv.chegadas

r = ler(f"SELECT id, empresa, mes, gravidade, avaliacao, nota FROM reclamacoes WHERE data_abertura >= '{CRUZ_INI}' AND data_abertura < '{CRUZ_FIM}' AND empresa IN ('AZU','TAM','GLO')")
c = ler("SELECT id, local, operacao, tema2, gravidade AS grav_cod FROM rec_codigos").merge(r, on="id")
c = c[(c.local.str.len() == 3) & (c.operacao == "D")].copy()
c["aer"] = c.local.map(IATA_ICAO)
cob = c.aer.notna().mean()
c = c.dropna(subset=["aer"])
c["tema"] = c.tema2.map(TEMA).fillna("Outros")
OPER = {21, 22, 23, 29, 31, 32, 33, 34, 35, 39}
c["operacional"] = c.tema2.isin(OPER)
ca = c.drop_duplicates(["id", "aer"])                                   # reclamação conta uma vez por aeroporto

# ---------- P6.1 taxas por companhia x aeroporto
k = ca.groupby(["empresa", "aer"]).agg(recl=("id", "size"), graves=("gravidade", lambda s: (s == "alta").sum()))
m = mv.groupby(["empresa", "aer"])[["mov", "partidas", "canc", "atr", "real"]].sum()
p = m.join(k, how="left").fillna(0)
aer_ok = p.groupby("aer").mov.sum()[lambda s: s >= 6000].index      # aeroportos com movimento relevante
p = p[p.index.get_level_values("aer").isin(aer_ok) & (p.mov >= 1000)].copy()
p["recl_por_10mil_mov"] = 1e4 * p.recl / p.mov
p["graves_por_10mil_mov"] = 1e4 * p.graves / p.mov

def aditivo(df, y, w):
    e = df.index.get_level_values("empresa").astype(str); a = df.index.get_level_values("aer").astype(str)
    E = pd.get_dummies(e).astype(float); A = pd.get_dummies(a).astype(float)
    def fit(blocos):
        X = np.column_stack([np.ones(len(df))] + [b.values[:, 1:] for b in blocos]) if blocos else np.ones((len(df), 1))
        sw = np.sqrt(df[w].values)
        b = np.linalg.lstsq(X * sw[:, None], df[y].values * sw, rcond=None)[0]
        pr = X @ b; yb = np.average(df[y], weights=df[w])
        return 1 - np.sum(df[w] * (df[y] - pr) ** 2) / np.sum(df[w] * (df[y] - yb) ** 2), pr
    r_e, _ = fit([E]); r_a, _ = fit([A]); r_ea, pr = fit([E, A])
    sh_e = 0.5 * (r_e + (r_ea - r_a)); sh_a = 0.5 * (r_a + (r_ea - r_e))
    return {"R2_companhia_e_aeroporto": r_ea, "parte_companhia": sh_e, "parte_aeroporto": sh_a,
            "companhia_pct_do_explicado": 100 * sh_e / (sh_e + sh_a)}, pr
dec = []
for y, rot in [("recl_por_10mil_mov", "todas as reclamações com aeroporto"), ("graves_por_10mil_mov", "reclamações graves")]:
    d_, pr = aditivo(p, y, "mov"); dec.append(dict(d_, indicador=rot))
    if y == "recl_por_10mil_mov":
        p["esperado"] = pr
dec_t = pd.DataFrame(dec)
# por tema principal: quem explica mais?
temas_chave = ["Bagagem extraviada", "Bagagem avariada", "Alteração pela empresa: alternativas",
               "Alternativas em atraso/cancelamento/preterição", "Assistência material no atraso", "Check-in e embarque",
               "Execução do voo: outros (atraso, conexão, desembarque)", "Preterição (overbooking)"]
for t in temas_chave:
    kt = c[c.tema == t].drop_duplicates(["id", "aer"]).groupby(["empresa", "aer"]).size()
    pt = p[["mov"]].join(kt.rename("n")).fillna(0); pt["taxa"] = 1e4 * pt.n / pt.mov
    d_, _ = aditivo(pt, "taxa", "mov"); dec.append(dict(d_, indicador=f"tema: {t}"))
dec_t = pd.DataFrame(dec)
salvar(dec_t.round(4), "q6_decomposicao_companhia_aeroporto.csv")

p["excesso_por_10mil_mov"] = p.recl_por_10mil_mov - p.esperado
p["reclamacoes_a_mais"] = (p.excesso_por_10mil_mov * p.mov / 1e4).round()

# ---------- P6.2 perfil de temas: companhia ou aeroporto?
pf = c.drop_duplicates(["id", "aer", "tema"]).groupby(["empresa", "aer", "tema"]).size().unstack(fill_value=0)
pf = pf[pf.sum(axis=1) >= 100]
prof = []
for (e, a), row in pf.iterrows():
    v0 = row / row.sum()
    mesma = pf.xs(e, level="empresa").drop(index=a, errors="ignore").sum(); mesma = mesma / mesma.sum()
    outras = pf[(pf.index.get_level_values("aer") == a) & (pf.index.get_level_values("empresa") != e)].sum()
    if outras.sum() < 100:
        continue
    outras = outras / outras.sum()
    prof.append({"empresa": e, "aer": a, "reclamacoes": row.sum(), "corr_mesma_companhia_outros_aeroportos": np.corrcoef(v0, mesma)[0, 1],
                 "corr_outras_companhias_mesmo_aeroporto": np.corrcoef(v0, outras)[0, 1]})
prof = pd.DataFrame(prof)
prof["mais_parecido_com"] = np.where(prof.corr_mesma_companhia_outros_aeroportos > prof.corr_outras_companhias_mesmo_aeroporto,
                                     "a própria companhia", "o aeroporto")
prof.insert(1, "companhia", prof.empresa.map(nome)); prof.insert(3, "iata", prof.aer.map(ICAO_IATA))
salvar(prof.round(3), "q6_perfil_companhia_x_aeroporto.csv")
prof_res = pd.DataFrame({"medida": ["pares companhia x aeroporto comparados", "perfil mais parecido com a própria companhia %",
                                    "correlação média com a própria companhia (outros aeroportos)", "correlação média com as outras companhias (mesmo aeroporto)"],
                         "valor": [len(prof), 100 * (prof.mais_parecido_com == "a própria companhia").mean(),
                                   prof.corr_mesma_companhia_outros_aeroportos.mean(), prof.corr_outras_companhias_mesmo_aeroporto.mean()]})
salvar(prof_res.round(3), "q6_perfil_resumo.csv")

# ---------- P6.3 M6: crônico x pico pontual (mensal)
km = ca.groupby(["empresa", "aer", "mes"]).size().rename("recl")
mm = mv.set_index(["empresa", "aer", "mes"])[["mov"]].join(km).fillna(0).reset_index()
mm = mm[mm.set_index(["empresa", "aer"]).index.isin(p.index)]
# esperado mensal = taxa esperada do par (modelo) x fator do mês do mercado
fm = mm.groupby("mes").apply(lambda d: d.recl.sum() / d.mov.sum(), include_groups=False)
fm = fm / (mm.recl.sum() / mm.mov.sum())
mm = mm.join(p.esperado, on=["empresa", "aer"])
mm["esp_n"] = mm.esperado * mm.mes.map(fm) * mm.mov / 1e4
mm["razao"] = mm.recl / mm.esp_n.clip(lower=0.5)
cr = mm.groupby(["empresa", "aer"]).agg(meses=("mes", "size"), meses_acima_1_2=("razao", lambda s: (s > 1.2).sum()),
                                        meses_acima_2=("razao", lambda s: (s > 2).sum()), pior_mes=("razao", "max"))
fr = cr.meses_acima_1_2 / cr.meses
cr["classe"] = np.select([fr >= 0.75, fr >= 0.5, cr.meses_acima_2 >= 1], ["crônico", "frequente", "pico pontual"], "dentro do esperado")
p = p.join(cr)
out = p.reset_index(); out.insert(1, "companhia", out.empresa.map(nome)); out.insert(3, "iata", out.aer.map(ICAO_IATA))
salvar(out.sort_values("reclamacoes_a_mais", ascending=False).round(2), "q6_pares_companhia_aeroporto.csv")
# efeito de cada aeroporto (média ponderada do excesso sobre o efeito da companhia, nas três companhias)
ea = out.groupby(["aer", "iata"]).apply(lambda d: pd.Series({"movimentos": d.mov.sum(), "reclamacoes": d.recl.sum(),
        "taxa_por_10mil_mov": 1e4 * d.recl.sum() / d.mov.sum(), "companhias_acima_do_esperado": (d.excesso_por_10mil_mov > 0).sum(),
        "companhias": len(d)}), include_groups=False).reset_index()
mercado = 1e4 * out.recl.sum() / out.mov.sum()
ea["vezes_a_media"] = ea.taxa_por_10mil_mov / mercado
salvar(ea.sort_values("taxa_por_10mil_mov", ascending=False).round(2), "q6_aeroportos.csv")

# ---------- C1: atraso/cancelamento -> reclamações operacionais (mesmo par companhia x aeroporto ao longo dos meses)
ko = ca[ca.operacional].groupby(["empresa", "aer", "mes"]).size().rename("op")
kt = ca.groupby(["empresa", "aer", "mes"]).size().rename("tot")
z = mv.set_index(["empresa", "aer", "mes"]).join([ko, kt]).fillna(0).reset_index()
z = z[z.set_index(["empresa", "aer"]).index.isin(p.index) & (z.real > 0)]
z["atraso_pp"] = 100 * z.atr / z.real; z["canc_pp"] = 100 * z.canc / z.partidas
z["op_10mil"] = 1e4 * z.op / z.mov; z["tot_10mil"] = 1e4 * z.tot / z.mov
z["par"] = z.empresa + "|" + z.aer
def fe(y):
    d = z.copy()
    for col in [y, "atraso_pp", "canc_pp"]:                    # remove média do par e do mês (dois sentidos, iterado)
        d[col + "_r"] = d[col]
        for _ in range(10):
            d[col + "_r"] -= d.groupby("par")[col + "_r"].transform(lambda s: np.average(s, weights=d.loc[s.index, "mov"]))
            d[col + "_r"] -= d.groupby("mes")[col + "_r"].transform(lambda s: np.average(s, weights=d.loc[s.index, "mov"]))
    X = d[["atraso_pp_r", "canc_pp_r"]].values; w = np.sqrt(d.mov.values)
    b = np.linalg.lstsq(X * w[:, None], d[y + "_r"].values * w, rcond=None)[0]
    rng = np.random.default_rng(5); pares = d.par.unique(); gi = d.groupby("par").indices; bs = []
    for _ in range(300):
        ix = np.concatenate([gi[q] for q in rng.choice(pares, len(pares))])
        bs.append(np.linalg.lstsq(X[ix] * w[ix, None], d[y + "_r"].values[ix] * w[ix], rcond=None)[0])
    lo, hi = np.percentile(bs, [5, 95], axis=0)
    return b, lo, hi
linhas = []
for y, rot in [("op_10mil", "reclamações operacionais"), ("tot_10mil", "todas as reclamações com aeroporto")]:
    b, lo, hi = fe(y)
    media = np.average(z[y], weights=z.mov)
    for i, x in enumerate(["+1 ponto de atraso > 30 min", "+1 ponto de cancelamento"]):
        linhas.append({"reclamacao": rot, "variacao": x, "reclamacoes_a_mais_por_10mil_mov": b[i], "margem_baixa": lo[i],
                       "margem_alta": hi[i], "media_por_10mil_mov": media, "aumento_pct": 100 * b[i] / media})
c1 = pd.DataFrame(linhas)
salvar(c1.round(3), "q6_c1_atraso_para_reclamacao.csv")

# ---------- C4: rotas críticas
rt = ler(f"""SELECT empresa, origem, destino, COUNT(*) previstos, SUM(situacao='CANCELADO') canc,
             SUM(situacao='REALIZADO' AND atraso_partida > 30) atr, SUM(situacao='REALIZADO') real,
             SUM(CASE WHEN situacao='REALIZADO' AND atraso_partida > 30 THEN MIN(atraso_partida, 1440) ELSE 0 END) minutos
             FROM voos WHERE {ESCOPO} AND empresa IN ('AZU','TAM','GLO') GROUP BY 1,2,3""")
rt = rt[rt.previstos >= 500].copy()
rt["atraso30_pct"] = 100 * rt.atr / rt.real; rt["cancelamento_pct"] = 100 * rt.canc / rt.previstos
tot_min = rt.minutos.sum()
rt["parte_dos_minutos_pct"] = 100 * rt.minutos / tot_min
# índice: minutos de atraso + cancelamentos convertidos (cada cancelamento ~ 180 min de atraso equivalente, premissa)
rt["impacto_min_equiv"] = rt.minutos + 180 * rt.canc
rt = rt.sort_values("impacto_min_equiv", ascending=False)
rt["parte_acumulada_impacto_pct"] = 100 * rt.impacto_min_equiv.cumsum() / rt.impacto_min_equiv.sum()
taxa_par = p.recl_por_10mil_mov
rt["recl_origem_por_10mil"] = [taxa_par.get((e, o), np.nan) for e, o in zip(rt.empresa, rt.origem)]
rt["recl_destino_por_10mil"] = [taxa_par.get((e, d), np.nan) for e, d in zip(rt.empresa, rt.destino)]
rt.insert(0, "companhia", rt.empresa.map(nome))
rt.insert(1, "rota", rt.origem.map(ICAO_IATA).fillna(rt.origem) + "-" + rt.destino.map(ICAO_IATA).fillna(rt.destino))
top20 = rt.head(20)
salvar(rt.round(2).head(100), "q6_c4_rotas_criticas.csv")
c4r = pd.DataFrame({"medida": ["rotas companhia x origem x destino com 500+ voos", "parte do impacto nas 20 piores rotas %",
                               "parte do impacto nas 100 piores rotas %"],
                    "valor": [len(rt), top20.impacto_min_equiv.sum() / rt.impacto_min_equiv.sum() * 100,
                              rt.head(100).impacto_min_equiv.sum() / rt.impacto_min_equiv.sum() * 100]})
salvar(c4r.round(2), "q6_c4_resumo.csv")

pd.set_option("display.width", 260, "display.max_columns", 30)
print("cobertura IATA->ICAO das citações domésticas", round(cob, 3))
print(dec_t.round(3).to_string()); print(prof_res.round(3).to_string())
print(prof.groupby("companhia").mais_parecido_com.value_counts().unstack().to_string())
print(out.sort_values("reclamacoes_a_mais", ascending=False).round(1)[["companhia", "iata", "mov", "recl", "recl_por_10mil_mov", "esperado", "excesso_por_10mil_mov", "reclamacoes_a_mais", "classe", "meses_acima_1_2", "meses"]].head(15).to_string())
print(out.classe.value_counts().to_string())
print(ea.sort_values("taxa_por_10mil_mov", ascending=False).round(2).head(12).to_string())
print(c1.round(3).to_string()); print(c4r.round(1).to_string())
print(top20.round(1)[["companhia", "rota", "previstos", "atraso30_pct", "cancelamento_pct", "minutos", "parte_acumulada_impacto_pct", "recl_origem_por_10mil", "recl_destino_por_10mil"]].to_string())
