# -*- coding: utf-8 -*-
"""Revisão crítica (Etapa 7), melhorias aprovadas pelo Fabian em 14/10/2026.
A. Critério de 15 minutos (padrão de mercado, Cirium): chegada e partida até 15 min por companhia, comparação com o ranking
   Cirium 2025 e o modelo companhia x aeroporto refeito com atraso > 15 min.
C. Cancelamento planejado x no dia: o mesmo voo (companhia, número, origem, destino e hora) cancelado em 3 ou mais dias
   seguidos = ajuste de malha (planejado); cancelamento isolado (1 ou 2 dias) = provável cancelamento operacional.
D. Dimensionamento dos pilotos: menor efeito detectável em 90 dias (poder de 80%, significância de 5%), usando a
   variação diária observada da diferença entre o grupo do piloto e o de comparação.
E. Sensibilidade do critério de recorrência das reclamações (limite de 1,2 ou 1,5 vez o mercado; 60%, 75% ou 90% dos meses)."""
import numpy as np
import pandas as pd
from metodos import mde_diferenca, casos_por_grupo
from base import ler, salvar, voos_escopo, NOME_CURTO, GRANDES, ESCOPO, RES, CRUZ_INI, CRUZ_FIM, TEMA
from q1_modelo import celulas, ajusta, decompor

# ---------- A
q = ler(f"""SELECT empresa, tipo_linha, substr(partida_prev,1,4) ano, COUNT(*) n, AVG(atraso_chegada <= 15) a15,
           AVG(atraso_partida <= 15) d15, AVG(atraso_partida > 30) d30 FROM voos WHERE situacao='REALIZADO'
           AND partida_prev IS NOT NULL AND tipo_linha IN ('N','I') AND empresa IN ('AZU','TAM','GLO') GROUP BY 1,2,3""")
def agrega(d):
    w = d.n
    return pd.Series({"voos": w.sum(), "chegada_ate_15min_pct": 100 * np.average(d.a15, weights=w),
                      "partida_ate_15min_pct": 100 * np.average(d.d15, weights=w), "partida_atraso_30_pct": 100 * np.average(d.d30, weights=w)})
a25 = q[q.ano == "2025"].groupby("empresa").apply(agrega, include_groups=False)
a25.index = a25.index.map(NOME_CURTO)
a25["cirium_2025_pct"] = pd.Series({"Azul": 85.18, "Gol": 87.75, "LATAM": np.nan})
a25["diferenca_pp"] = a25.chegada_ate_15min_pct - a25.cirium_2025_pct
salvar(a25.round(2), "q10a_criterio15_2025_cirium.csv", index=True)
v = voos_escopo()
for c in ["empresa", "origem", "mes"]:
    v[c] = v[c].astype(str)
r = v[~v.cancelado].copy()
r["atr15"] = (r.atraso_partida > 15).astype(float)
r["cheg15"] = (r.atraso_chegada > 15).astype(float)
emp_ok = r.empresa.value_counts()[lambda s: s >= 5000].index
aer_ok = r.origem.value_counts()[lambda s: s >= 3000].index
lin = []
for alvo, rot in [("atrasado", "partida > 30 min (relatório)"), ("atr15", "partida > 15 min"), ("cheg15", "chegada > 15 min")]:
    c = celulas(r.assign(y=r[alvo]), emp_ok, aer_ok, alvo="y")
    coef, _, _ = ajusta(c, ["hora_local", "mes", "emp", "aer"])
    d = decompor(c[c.emp.isin(GRANDES)].reset_index(drop=True), rot)
    lin.append({"criterio": rot, "taxa_mercado_pct": 100 * r[alvo].mean(), "companhia_pct_do_explicado": d["companhia_pct_do_explicado_por_ambos"],
                **{f"efeito_{NOME_CURTO[e]}_pp": 100 * coef["emp"][e] for e in GRANDES},
                **{f"taxa_{NOME_CURTO[e]}_pct": 100 * r[r.empresa == e][alvo].mean() for e in GRANDES}})
a15 = pd.DataFrame(lin)
salvar(a15.round(2), "q10a_criterio15_modelo.csv")

# ---------- C
cv = ler(f"""SELECT empresa, voo, origem, destino, substr(partida_prev,12,5) hhmm, data, situacao FROM voos
             WHERE {ESCOPO} AND empresa IN ('AZU','TAM','GLO')""")
cv["dia"] = pd.to_datetime(cv.data).astype("int64") // 86_400_000_000_000
cc = cv[cv.situacao == "CANCELADO"].sort_values(["empresa", "voo", "origem", "destino", "hhmm", "dia"]).copy()
k = ["empresa", "voo", "origem", "destino", "hhmm"]
nova = (cc.groupby(k).dia.diff() != 1)
cc["seq"] = nova.cumsum()
cc["dias_seguidos"] = cc.groupby("seq").dia.transform("size")
cc["tipo"] = np.where(cc.dias_seguidos >= 3, "planejado (3+ dias seguidos)", "isolado (1-2 dias)")
cc["ponte"] = ((cc.origem == "SBSP") & (cc.destino == "SBRJ")) | ((cc.origem == "SBRJ") & (cc.destino == "SBSP"))
tc = pd.crosstab(cc.empresa.map(NOME_CURTO), cc.tipo, normalize="index").mul(100)
tc.loc["3 grandes"] = cc.tipo.value_counts(normalize=True).mul(100)
tc.loc["ponte aérea"] = cc[cc.ponte].tipo.value_counts(normalize=True).mul(100)
tot = cv.groupby("empresa").size()
tc["cancelamentos"] = list(cc.groupby(cc.empresa.map(NOME_CURTO)).size().reindex(tc.index[:3])) + [len(cc), cc.ponte.sum()]
iso = cc[cc.tipo.str.startswith("isolado")]
tc["taxa_cancelamento_isolado_pct"] = list((100 * iso.groupby("empresa").size() / tot).rename(NOME_CURTO).reindex(tc.index[:3])) + \
    [100 * len(iso) / len(cv), 100 * iso.ponte.sum() / (((cv.origem == "SBSP") & (cv.destino == "SBRJ")) | ((cv.origem == "SBRJ") & (cv.destino == "SBSP"))).sum()]
sens_c = []
for lim in (2, 3, 5, 7):
    sens_c.append({"dias_seguidos_para_planejado": lim, "planejado_pct": 100 * (cc.dias_seguidos >= lim).mean(),
                   "planejado_pct_ponte": 100 * (cc[cc.ponte].dias_seguidos >= lim).mean()})
salvar(tc.round(2), "q10c_cancelamento_planejado.csv", index=True)
salvar(pd.DataFrame(sens_c).round(2), "q10c_sensibilidade.csv")

# ---------- D
dd = r.assign(dia=r.data.astype(str))
def mde(piloto, controle, alvo="atrasado", dias=90):
    p = dd[dd.origem.isin(piloto)].groupby("dia")[alvo].mean(); c_ = dd[dd.origem.isin(controle)].groupby("dia")[alvo].mean()
    dif = (p - c_).dropna()
    sd, rho, ef, m90, m180 = mde_diferenca(dif, dias)        # metodos.py (testado em testes.py)
    return {"grupo_piloto": "+".join(piloto), "grupo_comparacao": "+".join(controle), "taxa_piloto_pct": 100 * p.mean(),
            "dp_diario_da_diferenca_pp": 100 * sd, "autocorrelacao": rho, "dias_efetivos_em_90": ef,
            # a série já é a diferença diária entre os dois grupos: erro da média = dp / raiz(dias efetivos)
            "menor_efeito_detectavel_90d_pp": 100 * m90, "menor_efeito_detectavel_180d_pp": 100 * m180}
dims = [mde(["SBSP", "SBKP"], ["SBGR", "SBCF", "SBGL"])]
gru = dd[(dd.origem == "SBGR") & dd.hora_local.between(14, 19)]; cgh = dd[(dd.origem == "SBSP") & dd.hora_local.between(14, 19)]
dd2 = pd.concat([gru.assign(origem="GRU_tarde"), cgh.assign(origem="CGH_tarde")])
dd_bak = dd; dd = dd2
dims.append(mde(["GRU_tarde"], ["CGH_tarde"]))
dd = dd_bak
# desenho alternativo 1: sortear metade dos números de voo de CGH e VCP para receber a folga (mesmos aeroportos e dias)
import zlib
sel = dd[dd.origem.isin(["SBSP", "SBKP"])].copy()
sel["grupo"] = [zlib.crc32(f"{e}-{n}".encode()) % 2 for e, n in zip(sel.empresa, sel.voo)]
dd_bak = dd; dd = pd.concat([sel[sel.grupo == 1].assign(origem="voos_sorteados"), sel[sel.grupo == 0].assign(origem="demais_voos")])
dims.append(mde(["voos_sorteados"], ["demais_voos"]))
dd = dd_bak
# tempo em solo: sortear metade dos números de voo da tarde de GRU (mesmo banco, mesmos dias)
gs = gru.copy(); gs["grupo"] = [zlib.crc32(f"{e}-{n}".encode()) % 2 for e, n in zip(gs.empresa, gs.voo)]
dd_bak = dd; dd = pd.concat([gs[gs.grupo == 1].assign(origem="GRU_tarde_sorteados"), gs[gs.grupo == 0].assign(origem="GRU_tarde_demais")])
dims.append(mde(["GRU_tarde_sorteados"], ["GRU_tarde_demais"]))
dd = dd_bak
# desenho alternativo 2: semanas alternadas com e sem folga em CGH e VCP (cada aeroporto como comparação de si mesmo)
wk = dd[dd.origem.isin(["SBSP", "SBKP"])].assign(sem=lambda x: pd.to_datetime(x.dia).dt.to_period("W")).groupby("sem").atrasado.mean()
dw = wk.values[1::2][:len(wk.values[0::2])] - wk.values[0::2][:len(wk.values[1::2])]
sdw = np.std(dw, ddof=1)
dims.append({"grupo_piloto": "semanas com folga (CGH+VCP)", "grupo_comparacao": "semanas sem folga (mesmos aeroportos)", "taxa_piloto_pct": 100 * wk.mean(),
             "dp_diario_da_diferenca_pp": np.nan, "autocorrelacao": np.nan, "dias_efetivos_em_90": np.nan,
             "menor_efeito_detectavel_90d_pp": 100 * 2.8 * sdw / np.sqrt(6), "menor_efeito_detectavel_180d_pp": 100 * 2.8 * sdw / np.sqrt(13)})
# resolução de bagagem extraviada: proporções, metade das filas (Gol), 90 dias
rc = ler(f"""SELECT r.id, r.empresa, r.avaliacao FROM reclamacoes r JOIN rec_codigos k USING (id)
             WHERE k.tema2 = 41 AND r.empresa = 'GLO' AND r.avaliacao IN ('Resolvida','Não Resolvida')""").drop_duplicates("id")
n90 = len(rc) / 24 * 3 / 2                                     # por grupo, em 90 dias (24 meses de base)
p0 = (rc.avaliacao == "Resolvida").mean()
mde_prop = 2.8 * np.sqrt(2 * p0 * (1 - p0) / n90)
dims.append({"grupo_piloto": "Gol, bagagem extraviada (metade das filas)", "grupo_comparacao": "outra metade", "taxa_piloto_pct": 100 * p0,
             "dp_diario_da_diferenca_pp": np.nan, "autocorrelacao": np.nan, "dias_efetivos_em_90": np.nan,
             "menor_efeito_detectavel_90d_pp": 100 * mde_prop, "menor_efeito_detectavel_180d_pp": 100 * mde_prop / np.sqrt(2),
             "reclamacoes_avaliadas_por_grupo_em_90d": n90})
# casos necessários por grupo para detectar uma melhora da resolução (de p0 para p0 + efeito)
for ef_ in (0.28, 0.10):
    p1 = p0 + ef_
    dims.append({"grupo_piloto": f"casos necessários por grupo para +{int(ef_ * 100)} pontos de resolução", "grupo_comparacao": "",
                 "taxa_piloto_pct": 100 * p0, "reclamacoes_avaliadas_por_grupo_em_90d": casos_por_grupo(p0, ef_)})
# o piloto é de uma companhia só: menor efeito detectável com os voos de cada companhia (sorteio por número de voo)
# mediana de 20 sorteios diferentes, porque um sorteio só varia cerca de 0,2 ponto
for emp, nome in [("AZU", "Azul"), ("TAM", "LATAM"), ("GLO", "Gol")]:
    for base_, rot in [(sel, "CGH+VCP"), (gs, "GRU tarde")]:
        b0 = base_[base_.empresa == emp]; xs = []
        for semente in range(20):
            g_ = np.array([zlib.crc32(f"{semente}-{e}-{n}".encode()) % 2 for e, n in zip(b0.empresa, b0.voo)])
            dd_bak = dd; dd = pd.concat([b0[g_ == 1].assign(origem="s"), b0[g_ == 0].assign(origem="d")])
            xs.append(mde(["s"], ["d"])); dd = dd_bak
        x_ = pd.DataFrame(xs).median(numeric_only=True).to_dict()
        x_["grupo_piloto"] = f"{nome}, {rot}, voos sorteados (mediana de 20 sorteios)"; x_["grupo_comparacao"] = "demais voos da mesma companhia"
        dims.append(x_)
salvar(pd.DataFrame(dims).round(3), "q10d_dimensionamento_pilotos.csv")

# ---------- E
rec = None
x = pd.read_csv(RES / "q5_recorrencias.csv", encoding="utf-8-sig")   # só para referência dos temas recorrentes atuais
rr = ler(f"SELECT DISTINCT r.id, r.empresa, r.mes, k.tema2 FROM reclamacoes r JOIN rec_codigos k USING (id) WHERE r.empresa IN ('AZU','TAM','GLO') AND r.data_abertura >= '{CRUZ_INI}' AND r.data_abertura < '{CRUZ_FIM}'")
rr["tema"] = rr.tema2.map(TEMA)
vm = ler(f"""SELECT CASE empresa WHEN 'ACN' THEN 'AZU' ELSE empresa END empresa, substr(partida_prev,1,7) mes, COUNT(*) voos FROM voos
             WHERE tipo_linha IN ('N','I') AND partida_prev IS NOT NULL AND partida_prev >= '{CRUZ_INI}' AND partida_prev < '{CRUZ_FIM}'
             AND empresa IN ('AZU','ACN','TAM','GLO') GROUP BY 1,2""")
m = rr.drop_duplicates(["id", "tema"]).groupby(["empresa", "tema", "mes"]).size().rename("n").reset_index()
grade = pd.MultiIndex.from_product([GRANDES, rr.tema.dropna().unique(), sorted(vm.mes.unique())], names=["empresa", "tema", "mes"])
m = m.set_index(["empresa", "tema", "mes"]).reindex(grade, fill_value=0).reset_index().merge(vm, on=["empresa", "mes"])
m["taxa"] = m.n / m.voos
mk = m.groupby(["tema", "mes"]).apply(lambda d: d.n.sum() / d.voos.sum(), include_groups=False).rename("mk")
m = m.join(mk, on=["tema", "mes"])
sens = []
for vez in (1.2, 1.5):
    for frac in (0.6, 0.75, 0.9):
        g = m.assign(ac=m.taxa > vez * m.mk).groupby(["empresa", "tema"]).agg(f=("ac", "mean"), n=("n", "sum"))
        g = g[(g.f >= frac) & (g.n >= 50)].reset_index()
        for e in GRANDES:
            sens.append({"vezes_o_mercado": vez, "fracao_dos_meses": frac, "companhia": NOME_CURTO[e],
                         "temas_recorrentes": ", ".join(sorted(g[g.empresa == e].tema))})
se = pd.DataFrame(sens)
salvar(se, "q10e_sensibilidade_recorrencia.csv")

pd.set_option("display.width", 250, "display.max_colwidth", 200)
print(a25.round(2).to_string()); print(a15.round(2).to_string()); print(tc.round(1).to_string()); print(pd.DataFrame(sens_c).round(1).to_string())
print(pd.DataFrame(dims).round(2).to_string()); print(se.to_string())
