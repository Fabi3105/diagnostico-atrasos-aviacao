# -*- coding: utf-8 -*-
"""Pergunta 5 (com M5 e C5). Principais reclamações por gravidade e recorrência; ranking das companhias; é
"cultura da empresa" (padrão próprio e estável) ou não há relação estatística?

- Temas: grupos do Anexo II da Portaria 9.128/SAS (código classificador preenchido pela companhia; parte estimada
  pela ANAC). Uma reclamação conta uma vez em cada tema que cita. Gravidade: definição F.
- Taxas por 10 mil voos no período comum (set/2024-dez/2025): voos regulares domésticos e internacionais da
  companhia no VRA (previstos). Companhias com pelo menos 300 reclamações e 2.000 voos no período.
- Desfecho (M5): taxa de resolução (resolvidas ÷ avaliadas), nota média, tempo de resposta mediano (dias; valores
  negativos descartados), resposta em até 10 dias, procedência admitida pela companhia (P ou M ÷ informadas).
- Recorrência (definição G): companhia x tema com taxa por 10 mil voos acima de 1,2 vez a do mercado em 75% ou
  mais dos 16 meses.
- "Cultura": perfil de temas (participação de cada tema) por companhia e mês. Se cada companhia tem um perfil
  próprio e estável, os meses de uma companhia se parecem mais entre si do que com os de outras, e um
  classificador acerta a companhia pelo perfil do mês. Teste de permutação (embaralhando os rótulos).
- C5: resolução x nota x volume entre companhias e entre meses.
Cuidados: (1) companhias estrangeiras fazem voos longos e com aviões maiores, então "por voo" não é comparável com
as brasileiras: os rankings são separados por grupo. (2) O código de tema e a procedência são preenchidos pela própria
companhia; parte do "perfil" pode refletir o jeito de cada uma classificar."""
import numpy as np, pandas as pd
from base import ler, salvar, TEMA, NOME_CURTO, CRUZ_INI, CRUZ_FIM

r = ler("SELECT * FROM reclamacoes")
c = ler("SELECT id, grupo, local, operacao, assunto, tema2, gravidade FROM rec_codigos")
r["tempo_resposta"] = r.tempo_resposta.where(r.tempo_resposta >= 0)
c["tema"] = c.tema2.map(TEMA).fillna("Outros")
c = c.merge(r[["id", "empresa", "mes", "avaliacao", "nota", "avaliacao_empresa"]], on="id")
ct = c.drop_duplicates(["id", "tema"])                          # uma vez por tema na reclamação
nomes = r.drop_duplicates("empresa").set_index("empresa").empresa_nome.to_dict()
nome = lambda e: NOME_CURTO.get(e, nomes.get(e, e))

# ---------- 1. principais temas
GRAV_TEMA = ct.groupby("tema").gravidade.agg(lambda s: s.mode().iloc[0])
t1 = ct.groupby("tema").agg(reclamacoes=("id", "nunique"), nota_media=("nota", "mean"),
                            resolvidas_pct=("avaliacao", lambda s: 100 * (s == "Resolvida").sum() / s.isin(["Resolvida", "Não Resolvida"]).sum()),
                            procedente_admitida_pct=("avaliacao_empresa", lambda s: 100 * s.isin(["P", "M"]).sum() / s.isin(["P", "M", "I"]).sum()))
t1["gravidade"] = GRAV_TEMA
t1["parte_das_reclamacoes_pct"] = 100 * t1.reclamacoes / r.codigo.notna().sum()
t1 = t1.sort_values("reclamacoes", ascending=False)
salvar(t1.round(2), "q5_temas.csv", index=True)
g1 = r.groupby("gravidade").agg(reclamacoes=("id", "size"), nota_media=("nota", "mean"),
                                resolvidas_pct=("avaliacao", lambda s: 100 * (s == "Resolvida").sum() / s.isin(["Resolvida", "Não Resolvida"]).sum()))
salvar(g1.round(2), "q5_gravidade.csv", index=True)

# ---------- 2. ranking das companhias (período comum)
# Azul Conecta (ACN) voa com a marca Azul e suas reclamações aparecem como Azul: os voos entram no denominador da Azul
voos = ler(f"""SELECT CASE empresa WHEN 'ACN' THEN 'AZU' ELSE empresa END empresa, COUNT(*) voos FROM voos WHERE tipo_linha IN ('N','I') AND partida_prev IS NOT NULL
               AND partida_prev >= '{CRUZ_INI}' AND partida_prev < '{CRUZ_FIM}' GROUP BY 1""").set_index("empresa").voos
rp = r[(r.data_abertura >= CRUZ_INI) & (r.data_abertura < CRUZ_FIM)]
def indicadores(d):
    av = d.avaliacao.isin(["Resolvida", "Não Resolvida"])
    inf = d.avaliacao_empresa.isin(["P", "M", "I"])
    return pd.Series({"reclamacoes": len(d), "graves": (d.gravidade == "alta").sum(),
                      "graves_pct": 100 * (d.gravidade == "alta").mean(),
                      "resolucao_pct": 100 * (d.avaliacao == "Resolvida").sum() / max(av.sum(), 1),
                      "nota_media": d.nota.mean(), "tempo_resposta_mediano_dias": d.tempo_resposta.median(),
                      "resposta_ate_10_dias_pct": 100 * (d.tempo_resposta <= 10).sum() / max(d.tempo_resposta.notna().sum(), 1),
                      "procedencia_admitida_pct": 100 * d.avaliacao_empresa.isin(["P", "M"]).sum() / max(inf.sum(), 1),
                      "reclama_tambem_do_atendimento_pct": 100 * (d.atendimento_cod == "S").mean()})
rk = rp.groupby("empresa").apply(indicadores, include_groups=False)
rk["voos"] = voos
rk = rk[(rk.reclamacoes >= 300) & (rk.voos >= 2000)].copy()
rk["por_10mil_voos"] = 1e4 * rk.reclamacoes / rk.voos
rk["graves_por_10mil_voos"] = 1e4 * rk.graves / rk.voos
rk["graves_nao_resolvidas_por_10mil_voos"] = rk.graves_por_10mil_voos * (1 - rk.resolucao_pct / 100)
rk.insert(0, "companhia", rk.index.map(nome))
rk.insert(1, "grupo", np.where(rk.index.isin(["AZU", "TAM", "GLO", "PTB"]), "brasileira", "estrangeira"))

# ---------- 3. recorrência por tema (mensal, por 10 mil voos)
vm = ler(f"""SELECT CASE empresa WHEN 'ACN' THEN 'AZU' ELSE empresa END empresa, substr(partida_prev,1,7) mes, COUNT(*) voos FROM voos WHERE tipo_linha IN ('N','I')
             AND partida_prev IS NOT NULL AND partida_prev >= '{CRUZ_INI}' AND partida_prev < '{CRUZ_FIM}' GROUP BY 1,2""")
ctp = ct[(ct.mes >= CRUZ_INI[:7]) & (ct.mes < CRUZ_FIM[:7]) & ct.empresa.isin(rk.index)]
x = ctp.groupby(["empresa", "tema", "mes"]).id.nunique().rename("n").reset_index()
grade = pd.MultiIndex.from_product([rk.index, ct.tema.unique(), sorted(vm.mes.unique())], names=["empresa", "tema", "mes"])
x = x.set_index(["empresa", "tema", "mes"]).reindex(grade, fill_value=0).reset_index()
x = x.merge(vm, on=["empresa", "mes"])
x["taxa"] = 1e4 * x.n / x.voos
mk = x.groupby(["tema", "mes"]).apply(lambda d: 1e4 * d.n.sum() / d.voos.sum(), include_groups=False).rename("taxa_mercado")
x = x.join(mk, on=["tema", "mes"])
x["acima"] = x.taxa > 1.2 * x.taxa_mercado
rec = x.groupby(["empresa", "tema"]).agg(meses=("mes", "size"), meses_acima=("acima", "sum"), reclamacoes=("n", "sum"),
                                         taxa_media=("taxa", "mean"), taxa_mercado=("taxa_mercado", "mean"))
rec["recorrente"] = (rec.meses_acima / rec.meses >= 0.75) & (rec.reclamacoes >= 50)
rec["vezes_o_mercado"] = rec.taxa_media / rec.taxa_mercado
rec = rec.reset_index(); rec["companhia"] = rec.empresa.map(nome); rec["gravidade"] = rec.tema.map(GRAV_TEMA)
salvar(rec[rec.recorrente].sort_values(["companhia", "vezes_o_mercado"], ascending=[True, False]).round(2), "q5_recorrencias.csv")
rr = rec[rec.recorrente].groupby("empresa").agg(temas_recorrentes=("tema", "size"),
                                                 temas_recorrentes_graves=("gravidade", lambda s: (s == "alta").sum()))
rk = rk.join(rr).fillna({"temas_recorrentes": 0, "temas_recorrentes_graves": 0})
rk = rk.sort_values(["grupo", "graves_nao_resolvidas_por_10mil_voos"], ascending=[True, False])
salvar(rk.round(2), "q5_ranking_companhias.csv", index=True)

# ---------- 4. "cultura": perfil próprio e estável?
p = ctp.groupby(["empresa", "mes", "tema"]).id.nunique().unstack(fill_value=0)
p = p[p.sum(axis=1) >= 30]
P = p.div(p.sum(axis=1), axis=0)
emp = P.index.get_level_values("empresa").values
M = P.values
def acerto(rot):
    ok = 0
    for i in range(len(M)):
        mask = np.ones(len(M), bool); mask[i] = False
        cent = {e: M[mask & (rot == e)].mean(axis=0) for e in np.unique(rot[mask])}
        pred = min(cent, key=lambda e: ((M[i] - cent[e]) ** 2).sum())
        ok += pred == rot[i]
    return ok / len(M)
real = acerto(emp)
rng = np.random.default_rng(7)
perm = [acerto(rng.permutation(emp)) for _ in range(200)]
C = np.corrcoef(M)
same = emp[:, None] == emp[None, :]
iu = np.triu_indices(len(M), 1)
sim_mesma, sim_outras = C[iu][same[iu]].mean(), C[iu][~same[iu]].mean()
cult = pd.DataFrame({"medida": ["meses-companhia analisados", "companhias", "acerto do classificador (companhia pelo perfil do mês) %",
                                "acerto esperado ao acaso (permutação, média) %", "acerto máximo nas permutações %",
                                "valor-p da permutação", "correlação média entre meses da mesma companhia",
                                "correlação média entre meses de companhias diferentes"],
                     "valor": [len(M), len(np.unique(emp)), 100 * real, 100 * np.mean(perm), 100 * np.max(perm),
                               (1 + sum(q >= real for q in perm)) / (1 + len(perm)), sim_mesma, sim_outras]})
salvar(cult.round(3), "q5_cultura_teste.csv")
# só as três grandes: perfil por companhia (participação dos temas) e estabilidade 2024 x 2025
g3 = ct[ct.empresa.isin(["AZU", "TAM", "GLO"])]
perf = g3.groupby(["empresa", "tema"]).id.nunique().unstack(fill_value=0)
perf = 100 * perf.div(perf.sum(axis=1), axis=0)
perf.index = perf.index.map(nome)
salvar(perf.T.round(2).sort_values("Azul", ascending=False), "q5_perfil_temas_3grandes.csv", index=True)
est = []
for e in ["AZU", "TAM", "GLO"]:
    a = g3[(g3.empresa == e) & (g3.mes < "2025-01")].tema.value_counts(normalize=True)
    b = g3[(g3.empresa == e) & (g3.mes >= "2025-01")].tema.value_counts(normalize=True)
    a, b = a.align(b, fill_value=0)
    est.append({"companhia": nome(e), "correlacao_perfil_2024_x_2025": np.corrcoef(a, b)[0, 1]})
salvar(pd.DataFrame(est).round(3), "q5_estabilidade_perfil.csv")

# ---------- 5. C5: resolução compensa volume?
c5 = rk[["companhia", "por_10mil_voos", "resolucao_pct", "nota_media", "graves_pct"]]
cc = pd.DataFrame({"medida": ["entre companhias: resolução x nota", "entre companhias: reclamações por voo x nota",
                              "entre companhias: reclamações por voo x resolução"],
                   "correlacao": [c5.resolucao_pct.corr(c5.nota_media), c5.por_10mil_voos.corr(c5.nota_media),
                                  c5.por_10mil_voos.corr(c5.resolucao_pct)]})
em = rp[rp.empresa.isin(["AZU", "TAM", "GLO"])].groupby(["empresa", "mes"]).apply(lambda d: pd.Series({
    "res": (d.avaliacao == "Resolvida").sum() / max(d.avaliacao.isin(["Resolvida", "Não Resolvida"]).sum(), 1), "nota": d.nota.mean(), "n": len(d)}), include_groups=False)
em = em.join(vm.set_index(["empresa", "mes"]).voos)
em["por_voo"] = em.n / em.voos
cc.loc[len(cc)] = ["meses das 3 grandes: resolução x nota", em.res.corr(em.nota)]
cc.loc[len(cc)] = ["meses das 3 grandes: reclamações por voo x nota", em.por_voo.corr(em.nota)]
# nota por desfecho
nd = r.groupby("avaliacao").nota.mean()
cc.loc[len(cc)] = ["nota média quando resolvida", nd.get("Resolvida")]
cc.loc[len(cc)] = ["nota média quando não resolvida", nd.get("Não Resolvida")]
salvar(cc.round(3), "q5_c5_resolucao_volume_nota.csv")

pd.set_option("display.width", 260, "display.max_columns", 30)
print(t1.round(1).head(16).to_string()); print(g1.round(1).to_string())
print(rk.round(1)[["companhia", "voos", "reclamacoes", "por_10mil_voos", "graves_pct", "graves_por_10mil_voos", "resolucao_pct", "nota_media",
                   "tempo_resposta_mediano_dias", "procedencia_admitida_pct", "graves_nao_resolvidas_por_10mil_voos", "temas_recorrentes", "temas_recorrentes_graves"]].to_string())
print(rec[rec.recorrente & rec.empresa.isin(["AZU", "TAM", "GLO"])].round(2)[["companhia", "tema", "gravidade", "meses_acima", "vezes_o_mercado", "reclamacoes"]].to_string())
print(cult.round(3).to_string()); print(perf.T.round(1).sort_values("Azul", ascending=False).head(14).to_string()); print(pd.DataFrame(est).round(3)); print(cc.round(3).to_string())
