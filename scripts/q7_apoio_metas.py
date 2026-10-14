# -*- coding: utf-8 -*-
"""Etapa 4. Números de apoio às metas (referências observadas na própria base).
1. Dezembro por companhia (atraso e cancelamento) e diferença para novembro.
2. Reclamações a mais nas recorrências (quanto cairia se o tema voltasse à taxa do mercado).
3. Resolução por tema e companhia (melhor referência observada entre as três grandes).
4. Ponte aérea CGH-SDU: cancelamento, parte com tempo severo na origem e comparação com a rede."""
import numpy as np, pandas as pd
from base import ler, salvar, voos_escopo, NOME_CURTO, TEMA, GRANDES, RES

v = voos_escopo()
for c in ["empresa", "origem", "destino", "mes"]:
    v[c] = v[c].astype(str)
v = v[v.empresa.isin(GRANDES)]
v["m"] = v.mes.str[5:7]
r = v[~v.cancelado]
d = pd.DataFrame({"atraso30_pct": 100 * r.groupby(["empresa", "m"]).atrasado.mean(),
                  "cancelamento_pct": 100 * v.groupby(["empresa", "m"]).cancelado.mean()}).reset_index()
d = d[d.m.isin(["10", "11", "12", "01"])].pivot(index="empresa", columns="m")
d.index = d.index.map(NOME_CURTO)
salvar(d.round(2), "q7_dezembro_por_companhia.csv", index=True)

rec = pd.read_csv(RES / "q5_recorrencias.csv")
rec = rec[rec.empresa.isin(GRANDES)].copy()
rec["reclamacoes_a_mais_16_meses"] = (rec.reclamacoes * (1 - 1 / rec.vezes_o_mercado)).round()
rec["por_ano"] = (rec.reclamacoes_a_mais_16_meses * 12 / 16).round()
salvar(rec[["companhia", "tema", "gravidade", "vezes_o_mercado", "reclamacoes", "reclamacoes_a_mais_16_meses", "por_ano"]], "q7_recorrencias_excesso.csv")

c = ler("SELECT DISTINCT r.id, r.empresa, r.avaliacao, k.tema2 FROM reclamacoes r JOIN rec_codigos k USING (id) WHERE r.empresa IN ('AZU','TAM','GLO')")
c["tema"] = c.tema2.map(TEMA)
c = c[c.avaliacao.isin(["Resolvida", "Não Resolvida"])].drop_duplicates(["id", "tema"])
t = c.groupby(["tema", "empresa"]).avaliacao.apply(lambda s: 100 * (s == "Resolvida").mean()).unstack()
t.columns = [NOME_CURTO[x] for x in t.columns]
t["melhor"] = t.max(axis=1)
t["avaliadas"] = c.groupby("tema").size()
salvar(t[t.avaliadas >= 500].round(2).sort_values("melhor"), "q7_resolucao_por_tema.csv", index=True)   # 2 casas: evita arredondar duas vezes

cl = pd.read_csv(RES / "qc_impacto_clima.csv")   # só para registro
pa = v[((v.origem == "SBSP") & (v.destino == "SBRJ")) | ((v.origem == "SBRJ") & (v.destino == "SBSP"))]
outros = v[~v.index.isin(pa.index)]
ponte = pd.DataFrame({"medida": ["voos previstos na ponte aérea (3 grandes)", "cancelamento na ponte %", "cancelamento no resto da rede %",
                                 "atraso > 30 min na ponte %", "atraso > 30 min no resto da rede %"],
                      "valor": [len(pa), 100 * pa.cancelado.mean(), 100 * outros.cancelado.mean(),
                                100 * pa[~pa.cancelado].atrasado.mean(), 100 * outros[~outros.cancelado].atrasado.mean()]})
salvar(ponte.round(2), "q7_ponte_aerea.csv")
pd.set_option("display.width", 220)
print(d.round(1).to_string()); print(rec[["companhia", "tema", "vezes_o_mercado", "reclamacoes_a_mais_16_meses", "por_ano"]].to_string())
print(t[t.avaliadas >= 500].round(1).sort_values("melhor").to_string()); print(ponte.round(2).to_string())
