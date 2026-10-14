# -*- coding: utf-8 -*-
"""Dados do painel (resultados/painel_dados.json), no mesmo padrão de números do relatório (escopo da definição B).
Tabelas agregadas, pequenas o bastante para o navegador filtrar:
- v: mês x companhia x aeroporto de origem x hora local -> previstos, cancelados, realizados, atrasados (> 30 min), minutos
- cheg: mês x companhia x aeroporto de destino -> chegadas previstas (denominador de reclamações por movimento)
- r: mês x companhia x aeroporto citado (-1 = sem aeroporto) x tema x gravidade x desfecho -> reclamações (três grandes)
Também leva os números fixos do relatório (indicadores, soluções, metas) lidos dos CSVs de resultados."""
import json
import numpy as np, pandas as pd
from base import ler, voos_escopo, ESCOPO, RES, ICAO_IATA, IATA_ICAO, TEMA, NOME_CURTO

v = voos_escopo()
for c in ["empresa", "origem", "destino", "mes"]:
    v[c] = v[c].astype(str)
meses = sorted(v.mes.unique())
CIAS = ["AZU", "TAM", "GLO", "ACN", "OUT"]
v["ci"] = v.empresa.map({c: i for i, c in enumerate(CIAS)}).fillna(4).astype(int)
aers = list(v.origem.value_counts().head(50).index)
amap = {a: i for i, a in enumerate(aers)}
v["ai"] = v.origem.map(amap).fillna(len(aers)).astype(int)
v["mi"] = v.mes.map({m: i for i, m in enumerate(meses)})
v["h"] = v.hora_local.astype(int)
v["atr"] = (v.atrasado == 1).astype(int); v["real"] = (~v.cancelado).astype(int); v["canc"] = v.cancelado.astype(int)
g = v.groupby(["mi", "ci", "ai", "h"]).agg(prev=("canc", "size"), canc=("canc", "sum"), real=("real", "sum"),
                                           atr=("atr", "sum"), mins=("minutos_atraso", "sum")).reset_index()
g["mins"] = g.mins.round().astype(int)
v["di"] = v.destino.map(amap).fillna(len(aers)).astype(int)
ch = v.groupby(["mi", "ci", "di"]).size().reset_index(name="n")
# histograma dos minutos dos voos atrasados (> 30 min), para a mediana responder aos filtros
BORDAS = [30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 105, 120, 150, 180, 240, 360, 1441]
at = v[v.atrasado == 1]
at = at.assign(b=pd.cut(at.minutos_atraso, BORDAS, right=False, labels=False))
hb = at.groupby(["mi", "ci", "ai", "b"]).size().unstack(fill_value=0).reindex(columns=range(len(BORDAS) - 1), fill_value=0).reset_index()

r = ler("SELECT id, empresa, mes, gravidade, avaliacao FROM reclamacoes WHERE empresa IN ('AZU','TAM','GLO')")
k = ler("SELECT id, grupo, local, operacao, tema2 FROM rec_codigos")
k1 = k.sort_values(["id", "grupo"]).drop_duplicates("id")             # primeiro grupo: local e tema principal
r = r.merge(k1, on="id", how="left")
rmeses = sorted(r.mes.unique())
temas = sorted(set(TEMA.values()))
r["tema"] = r.tema2.map(TEMA).fillna("Sem código")
temas = sorted(r.tema.unique())
r["ti"] = r.tema.map({t: i for i, t in enumerate(temas)})
r["ci"] = r.empresa.map({c: i for i, c in enumerate(CIAS)})
r["aer"] = np.where((r.local.str.len() == 3) & (r.operacao == "D"), r.local.map(IATA_ICAO), None)
r["ai"] = r.aer.map(amap).fillna(-1).astype(int)
r.loc[r.aer.notna() & (r.ai == -1), "ai"] = len(aers)                # aeroporto fora da lista = "outros"
r["gi"] = r.gravidade.map({"baixa": 0, "média": 1, "alta": 2}).fillna(0).astype(int)
r["di"] = r.avaliacao.map({"Resolvida": 1, "Não Resolvida": 0}).fillna(2).astype(int)
r["mi"] = r.mes.map({m: i for i, m in enumerate(rmeses)})
rr = r.groupby(["mi", "ci", "ai", "ti", "gi", "di"]).size().reset_index(name="n")

ind = pd.read_csv(RES / "indicadores_padrao.csv", encoding="utf-8-sig")
dados = {
    "meses": meses, "rmeses": rmeses, "cias": CIAS,
    "nomes": {"AZU": "Azul", "TAM": "LATAM", "GLO": "Gol", "ACN": "Azul Conecta", "OUT": "Outras"},
    "aers": [ICAO_IATA.get(a, a) for a in aers] + ["Outros"], "temas": temas,
    "v": g[["mi", "ci", "ai", "h", "prev", "canc", "real", "atr", "mins"]].values.tolist(),
    "cheg": ch[["mi", "ci", "di", "n"]].values.tolist(),
    "r": rr[["mi", "ci", "ai", "ti", "gi", "di", "n"]].values.tolist(),
    "hb": hb.values.tolist(), "bordas": BORDAS,
    "ind": dict(zip(ind.indicador, ind.valor)),
}

# números fixos dos gráficos de diagnóstico, lidos dos mesmos CSVs do relatório
L = lambda n: pd.read_csv(RES / n, encoding="utf-8-sig")
ca = L("qc_impacto_clima_aeroporto.csv").sort_values("voos", ascending=False).head(10)
sit = L("q2b_probabilidade_por_situacao.csv").set_index("situacao_cheg").atraso30_pct
pos = L("q2_posicao_no_dia.csv")
rec = L("q3_recuperacao_no_ar_companhia.csv").set_index("companhia")
fol_ = L("qc_folga_dinamica.csv").set_index("estrategia"); fol = fol_.evitados_por_mil_minutos; fmin = fol_.minutos_de_folga_por_voo
dsem = L("q4_por_dia_semana.csv").rename(columns={"Unnamed: 0": "dia"})
pm = L("q8_ponte_aerea_motivos.csv").set_index("classe")
pe = L("q9_estimativa_motivos_ponte_2024_26.csv").set_index("grupo")
rt = L("q7_resolucao_por_tema.csv").set_index("tema")
pares = L("q6_pares_companhia_aeroporto.csv")
dados["F"] = {
    "clima": [[r.iata, r.atraso_normal_pct, r.atraso_severo_pct] for r in ca.itertuples()],
    "situacao": [["Chegadas no horário", sit["chegadas no horário"]], ["Sem chegada antes", sit["sem chegada na janela"]],
                 ["Parte atrasada", sit["parcial"]], ["Maioria atrasada", sit["giro comprometido (>=50%)"]]],
    "posicao": pos[["faixa_posicao", "atraso30_pct"]].values.tolist(),
    "recup": [[c, rec.loc[c, "chegaram_ate_15min_pct"], rec.loc[c, "folga_media_ponderada_min"]] for c in ["Gol", "LATAM", "Azul"]],
    "folga": [[n, fol[k], fmin[k]] for n, k in [("Igual para todos", "folga uniforme de 3 min"), ("Sazonal planejada", "folga sazonal planejada (aeroporto x mês x faixa) x1"),
              ("Sazonal, mesma quantidade", "folga sazonal planejada (aeroporto x mês x faixa) x2"), ("Só nos dias de tempo ruim", "folga no dia, só com tempo ruim x1")]],
    "dsem": dsem[["dia", "atraso30_pct"]].values.tolist(),
    "ponte_sinais": [[c, pm.loc[c, "ponte aérea CGH-SDU"], pm.loc[c, "resto da rede (aeroportos com METAR)"]]
                     for c in ["sem sinal observável", "tempo ruim", "evento no aeroporto", "fim do dia (após 21h)"]],
    "ponte_taxa": [pm.loc["taxa_de_cancelamento_pct", "ponte aérea CGH-SDU"], pm.loc["taxa_de_cancelamento_pct", "resto da rede (aeroportos com METAR)"]],
    "ponte_motivos": [[g, min(pe.loc[g, "estimativa_ponte_2024_26_pct"], pe.loc[g, "estimativa_com_tabela_so_da_ponte_pct"]),
                       max(pe.loc[g, "estimativa_ponte_2024_26_pct"], pe.loc[g, "estimativa_com_tabela_so_da_ponte_pct"])] for g in pe.index],
    "resol": [[t, rt.loc[t, "Azul"], rt.loc[t, "LATAM"], rt.loc[t, "Gol"]] for t in ["Bagagem extraviada", "Assistência material no atraso", "Bagagem avariada"] if t in rt.index],
    "pares": pares[pares.classe == "crônico"][["companhia", "iata", "recl_por_10mil_mov", "esperado"]].values.tolist(),
}
out = RES / "painel_dados.json"
out.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(len(g), len(ch), len(rr), round(out.stat().st_size / 1e6, 2), "MB")
