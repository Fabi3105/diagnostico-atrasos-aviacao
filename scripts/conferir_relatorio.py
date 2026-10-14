# -*- coding: utf-8 -*-
"""Confere os números-chave do RELATORIO.md contra os CSVs de resultados/ (rodar depois de toda edição do relatório).
Cada checagem lê o valor no CSV, formata como o texto escreve (vírgula decimal, ponto de milhar) e procura o trecho.
Saída: resultados/conferencia_relatorio.csv e resumo na tela. "NÃO" = relatório desatualizado ou com outra base."""
import pandas as pd
from base import RAIZ, RES, salvar

rel = (RAIZ / "RELATORIO.md").read_text(encoding="utf-8")
ler = lambda n, **k: pd.read_csv(RES / n, encoding="utf-8-sig", **k)
from metodos import br                     # mesmo formato testado em testes.py
r0 = lambda v: str(int(v + 0.5))          # arredondamento comercial para inteiros
L = []
def chk(tema, desc, texto, arq):
    L.append({"tema": tema, "descricao": desc, "texto_procurado": texto, "arquivo": arq, "esta_no_relatorio": "sim" if texto in rel else "NÃO"})

ip = ler("indicadores_padrao.csv").set_index("indicador").valor
chk("geral", "voos no escopo", br(ip["voos previstos (escopo)"]), "indicadores_padrao.csv")
chk("geral", "realizados", br(ip["voos realizados"]), "indicadores_padrao.csv")
chk("geral", "cancelados", br(ip["voos cancelados"]), "indicadores_padrao.csv")
chk("geral", "atraso > 30", br(ip["partidas com atraso > 30 min %"], 1) + "%", "indicadores_padrao.csv")
chk("geral", "cancelamento", br(ip["taxa de cancelamento %"], 1) + "%", "indicadores_padrao.csv")
chk("geral", "mediana dos atrasados", br(ip["atraso mediano dos voos atrasados (min)"]) + " minutos", "indicadores_padrao.csv")
chk("geral", "minutos de atraso", br(ip["minutos de atraso acumulados (milhões)"], 1) + " milhões", "indicadores_padrao.csv")
v = ler("validacao_dados.csv").set_index("checagem").valor
chk("geral", "cobertura ICAO-IATA", v["voos com aeroporto de origem traduzido para IATA"].replace(".", ","), "validacao_dados.csv")

d = ler("q1_decomposicao.csv").set_index("indicador")
chk("P1", "aeroporto explica atraso (3 grandes)", f"aeroporto explica {r0(100 - d.loc['atraso > 30 min (só Azul, LATAM e Gol)', 'companhia_pct_do_explicado_por_ambos'])}%", "q1_decomposicao.csv")
chk("P1", "aeroporto explica cancelamento", f"{r0(100 - d.loc['cancelamento (só Azul, LATAM e Gol)', 'companhia_pct_do_explicado_por_ambos'])}% da de cancelamento", "q1_decomposicao.csv")
dc = ler("qc_p1_decomposicao_sem_clima.csv")
chk("P1", "sem clima: aeroporto", f"aeroporto {r0(100 - dc.iloc[1].companhia_pct_do_explicado_por_ambos)}%", "qc_p1_decomposicao_sem_clima.csv")
e = ler("q1_efeito_companhia.csv").set_index("companhia")
chk("P1", "efeito Gol", f"{br(abs(e.loc['Gol', 'efeito_atraso_pp']), 1)} ponto percentual abaixo", "q1_efeito_companhia.csv")
chk("P1", "efeito Azul", f"Azul fica {br(e.loc['Azul', 'efeito_atraso_pp'], 1)} acima", "q1_efeito_companhia.csv")
chk("P1", "Azul Conecta cancela", br(e.loc["Azul Conecta", "cancelamento_bruto_pct"], 1) + "% dos voos", "q1_efeito_companhia.csv")
a = ler("q1_aeroportos.csv")
chk("P1", "GRU+CGH minutos", f"concentram {r0(a.parte_acumulada_pct.iloc[1])}% de todos os minutos", "q1_aeroportos.csv")
ea = ler("q1_efeito_aeroporto.csv").set_index("iata")
chk("P1", "efeito GRU", f"+{br(ea.loc['GRU', 'efeito_atraso_pp'], 1)} pontos", "q1_efeito_aeroporto.csv")

p = ler("q2b_probabilidade_por_situacao.csv").set_index("situacao_cheg").atraso30_pct
chk("P2", "chegadas no horário", br(p["chegadas no horário"], 1) + "%", "q2b_probabilidade_por_situacao.csv")
chk("P2", "maioria atrasada", br(p["giro comprometido (>=50%)"], 1) + "%", "q2b_probabilidade_por_situacao.csv")
pos = ler("q2_posicao_no_dia.csv").set_index("faixa_posicao").atraso30_pct
chk("P2", "1º voo do dia", br(pos["1º voo do dia"], 1) + "%", "q2_posicao_no_dia.csv")
chk("P2", "31º em diante", br(pos["31º ou mais"], 1) + "%", "q2_posicao_no_dia.csv")
b = ler("q2_bola_de_neve.csv").efeito_padronizado_pp
chk("P2", "bola de neve outros aeroportos", f"+{br(b[2], 1)} pontos", "q2_bola_de_neve.csv")
chk("P2", "bola de neve mesmo aeroporto", f"+{br(b[0], 1)} pontos", "q2_bola_de_neve.csv")
chk("P2", "bola de neve outras companhias", f"+{br(b[1], 1)} ponto", "q2_bola_de_neve.csv")
o = ler("q2b_primeira_onda_efeito.csv").valor
chk("P2", "1ª onda % dos voos", br(o[0], 1) + "% dos voos", "q2b_primeira_onda_efeito.csv")
chk("P2", "1ª onda atraso", f"atrasam {br(o[1], 1)}%", "q2b_primeira_onda_efeito.csv")
chk("P2", "1ª onda efeito", f"cairia cerca de {r0(o[8])}%", "q2b_primeira_onda_efeito.csv")

cl = ler("qc_impacto_clima.csv")
cl = cl[cl.iloc[:, 0] == "tempo na origem"].set_index(cl.columns[1])
chk("clima", "atraso normal x severo", f"de {br(cl.loc['normal', 'atraso_partida_pct'], 1)}% para {br(cl.loc['severo', 'atraso_partida_pct'], 1)}%", "qc_impacto_clima.csv")
chk("clima", "cancelamento normal x severo", f"de {br(cl.loc['normal', 'cancelamento_pct'], 1)}% para {br(cl.loc['severo', 'cancelamento_pct'], 1)}%", "qc_impacto_clima.csv")
pc = ler("qc_parte_clima.csv").valor
chk("clima", "parte ligada ao clima", br(pc[3], 1) + "% dos atrasos", "qc_parte_clima.csv")

rc = ler("q3_recuperacao_no_ar_companhia.csv").set_index("companhia")
for c in ["Gol", "LATAM", "Azul"]:
    chk("P3", f"recuperação {c}", br(rc.loc[c, "chegaram_ate_15min_pct"], 1) + "%", "q3_recuperacao_no_ar_companhia.csv")
    chk("P3", f"folga {c}", br(rc.loc[c, "folga_media_ponderada_min"], 1) + {"Gol": " na Gol", "LATAM": " na LATAM", "Azul": " minutos de folga na Azul"}[c], "q3_recuperacao_no_ar_companhia.csv")
chk("P3", "Gol evita no ar", br(rc.loc["Gol", "atrasos_evitados_no_ar_liquido"]) + " atrasos", "q3_recuperacao_no_ar_companhia.csv")
chk("P3", "Azul a mais", br(abs(rc.loc["Azul", "atrasos_evitados_no_ar_liquido"])) + " atrasos a mais", "q3_recuperacao_no_ar_companhia.csv")
cs = ler("q3_voos_cronicos_sensibilidade.csv")
chk("P3", "voos crônicos", br(cs.parte_dos_atrasos_pct.max(), 1) + "% dos atrasos", "q3_voos_cronicos_sensibilidade.csv")
f = ler("qc_folga_dinamica.csv").set_index("estrategia")
chk("folga", "sazonal", br(f.loc["folga sazonal planejada (aeroporto x mês x faixa) x1", "evitados_por_mil_minutos"], 1) + " quando é planejada", "qc_folga_dinamica.csv")
chk("folga", "no dia", br(f.loc["folga no dia, só com tempo ruim x1", "evitados_por_mil_minutos"], 1) + " quando é aplicada", "qc_folga_dinamica.csv")
chk("folga", "combinada min/voo", br(f.loc["sazonal x1 + no dia x1", "minutos_de_folga_por_voo"], 2) + " minutos", "qc_folga_dinamica.csv")
chk("folga", "combinada atraso", f"de {br(f.loc['hoje (2º ano)', 'atraso30_pct'], 1)}% para {br(f.loc['sazonal x1 + no dia x1', 'atraso30_pct'], 1)}%", "qc_folga_dinamica.csv")

m = ler("qc_p4_clima_por_mes.csv", dtype={"mes": str}).set_index("mes")
chk("P4", "dezembro atraso", br(m.loc["12", "atraso30_pct"], 1) + "%", "qc_p4_clima_por_mes.csv")
chk("P4", "dezembro tempo normal (origem e destino, gráfico)", "mostra " + br(m.loc["12", "atraso30_tempo_normal_pct"], 1) + "%", "qc_p4_clima_por_mes.csv")
q4 = ler("q4_por_mes_do_ano.csv").set_index("mes_do_ano")
chk("P4", "dezembro cancelamento", "cancela " + br(q4.loc[12, "cancelamento_pct"], 1) + "%", "q4_por_mes_do_ano.csv")
rg = ler("q4_regressao_diaria.csv")
chk("P4", "carga do dia", br(rg.iloc[0].coef_pp, 1) + " pontos", "q4_regressao_diaria.csv")

k = ler("q5_ranking_companhias.csv").set_index("companhia")
for c in ["Azul", "LATAM", "Gol"]:
    chk("P5", f"{c} reclamações/10 mil voos", br(k.loc[c, "por_10mil_voos"]), "q5_ranking_companhias.csv")
    chk("P5", f"{c} graves/10 mil voos", br(k.loc[c, "graves_por_10mil_voos"]), "q5_ranking_companhias.csv")
chk("P5", "razão graves Azul/LATAM", br(k.loc["Azul", "graves_por_10mil_voos"] / k.loc["LATAM", "graves_por_10mil_voos"], 1) + " vezes", "q5_ranking_companhias.csv")
cu = ler("q5_cultura_teste.csv").valor
chk("P5", "classificador", f"{r0(cu[2])}% das vezes", "q5_cultura_teste.csv")
chk("P5", "acaso", f"acertaria {r0(cu[3])}%", "q5_cultura_teste.csv")
c5 = ler("q5_c5_resolucao_volume_nota.csv").set_index("medida").correlacao
chk("P5", "nota resolvida", "nota 4,6", "q5_c5_resolucao_volume_nota.csv") if round(c5["nota média quando resolvida"], 1) == 4.6 else chk("P5", "nota resolvida", "nota " + br(c5["nota média quando resolvida"], 1), "q5")

d6 = ler("q6_decomposicao_companhia_aeroporto.csv").set_index("indicador")
chk("P6", "aeroporto explica volume", f"{r0(100 - d6.loc['todas as reclamações com aeroporto', 'companhia_pct_do_explicado'])}% da diferença no volume", "q6_decomposicao_companhia_aeroporto.csv")
chk("P6", "companhia explica graves", f"companhia explica {r0(d6.loc['reclamações graves', 'companhia_pct_do_explicado'])}%", "q6_decomposicao_companhia_aeroporto.csv")
c1 = ler("q6_c1_atraso_para_reclamacao.csv")
chk("C1", "atraso -> reclamação", br(c1.aumento_pct[0], 1) + "% a mais", "q6_c1_atraso_para_reclamacao.csv")
chk("C1", "cancelamento -> reclamação", br(c1.aumento_pct[1], 1) + "% a mais", "q6_c1_atraso_para_reclamacao.csv")

q8 = ler("q8_ponte_aerea_motivos.csv", index_col=0)
ct = ler("qc_impacto_clima_tipo_aeroporto.csv").set_index("iata")
ca = ler("qc_impacto_clima_aeroporto.csv").set_index("iata")
chk("clima", "Santos Dumont severo", f"{r0(ca.loc['SDU', 'acrescimo_severo_pp'])} pontos no Santos Dumont", "qc_impacto_clima_aeroporto.csv")
chk("clima", "Curitiba severo", f"só {r0(ca.loc['CWB', 'acrescimo_severo_pp'])} em Curitiba", "qc_impacto_clima_aeroporto.csv")
chk("clima", "trovoada GRU/CGH/CWB", f"sobe {r0(ct.loc['GRU', 'acrescimo_severo_trovoada_chuva_pp'])} pontos em GRU, {r0(ct.loc['CGH', 'acrescimo_severo_trovoada_chuva_pp'])} em Congonhas e {r0(ct.loc['CWB', 'acrescimo_severo_trovoada_chuva_pp'])} em Curitiba", "qc_impacto_clima_tipo_aeroporto.csv")
chk("clima", "Curitiba nevoeiro", "quase todo nevoeiro e teto baixo" if ct.loc['CWB', 'parte_trovoada_chuva_no_severo_pct'] < 30 else "(Curitiba mudou)", "qc_impacto_clima_tipo_aeroporto.csv")
fd = ler("qc_folga_dinamica.csv").set_index("estrategia")
saz2, uni3 = fd.loc["folga sazonal planejada (aeroporto x mês x faixa) x2", "evitados_por_mil_minutos"], fd.loc["folga uniforme de 3 min", "evitados_por_mil_minutos"]
chk("folga", "mesma quantidade", f"a sazonal evita {br(saz2, 1)} contra {br(uni3, 1)} da uniforme", "qc_folga_dinamica.csv")
chk("folga", "vantagem com mesma quantidade", "quase 30% a mais" if 0.25 <= saz2 / uni3 - 1 < 0.30 else "(vantagem mudou)", "qc_folga_dinamica.csv")
# valores antigos que não podem sobrar em nenhum trecho
for velho in ["4,4 atrasos", "4,4 quando", "3,7 contra", "0,43 minuto", "cerca de 25% mais", "cerca de 45%", "2,35 minutos"]:
    L.append({"tema": "valor antigo", "descricao": "não pode aparecer", "texto_procurado": velho, "arquivo": "-", "esta_no_relatorio": "NÃO" if velho in rel else "sim"})
chk("ponte", "cancelamentos", br(q8.loc["cancelamentos", "ponte aérea CGH-SDU"]), "q8_ponte_aerea_motivos.csv")
chk("ponte", "sem sinal", f"{br(q8.loc['taxa_canc_sem sinal observável_pct', 'ponte aérea CGH-SDU'], 1)}% dos voos, contra {br(q8.loc['taxa_canc_sem sinal observável_pct', 'resto da rede (aeroportos com METAR)'], 1)}%", "q8_ponte_aerea_motivos.csv")
chk("ponte", "em par", f"{r0(q8.loc['cancelamentos_em_par_ida_e_volta_pct', 'ponte aérea CGH-SDU'])}% dos cancelamentos vêm em par", "q8_ponte_aerea_motivos.csv")
es = ler("q9_estimativa_motivos_ponte_2024_26.csv").set_index("grupo")
lo = es[["estimativa_ponte_2024_26_pct", "estimativa_com_tabela_so_da_ponte_pct"]].min(axis=1); hi = es[["estimativa_ponte_2024_26_pct", "estimativa_com_tabela_so_da_ponte_pct"]].max(axis=1)
chk("ponte", "clima estimado", f"clima: {r0(lo['clima'])}% a {r0(hi['clima'])}%", "q9_estimativa_motivos_ponte_2024_26.csv")
chk("ponte", "técnico estimado", f"companhia: {r0(lo['técnico-operacional (companhia)'])}% a {r0(hi['técnico-operacional (companhia)'])}%", "q9_estimativa_motivos_ponte_2024_26.csv")
mt = ler("q9_motivos_declarados_2019.csv", index_col=0)
chk("ponte", "2019 clima ponte", f"{r0(mt.loc['clima', 'ponte aérea CGH-SDU'])}% foram declarados como clima", "q9_motivos_declarados_2019.csv")
cons = ler("q9_consistencia_codigo_metar.csv").valor
chk("ponte", "clima com tempo normal", f"{r0(cons[0])}% dos cancelamentos declarados como clima", "q9_consistencia_codigo_metar.csv")

ci = ler("q10a_criterio15_2025_cirium.csv").set_index("empresa")
for c in ["Gol", "Azul", "LATAM"]:
    chk("revisão", f"chegada 15 min {c}", br(ci.loc[c, "chegada_ate_15min_pct"], 1) + "%", "q10a_criterio15_2025_cirium.csv")
pl = ler("q10c_cancelamento_planejado.csv", index_col=0)
chk("revisão", "cancelamento planejado", br(pl.loc["3 grandes", "planejado (3+ dias seguidos)"], 1) + "% dos cancelamentos", "q10c_cancelamento_planejado.csv")
dm = ler("q10d_dimensionamento_pilotos.csv")
chk("revisão", "MDE folga 90d", br(dm.menor_efeito_detectavel_90d_pp[0], 1) + " pontos", "q10d_dimensionamento_pilotos.csv")
chk("revisão", "MDE GRU 90d", br(dm.menor_efeito_detectavel_90d_pp[1], 1) + " pontos", "q10d_dimensionamento_pilotos.csv")
chk("revisão", "MDE folga voos sorteados 90d", br(dm.menor_efeito_detectavel_90d_pp[2], 1) + " ponto", "q10d_dimensionamento_pilotos.csv")
chk("revisão", "MDE tempo em solo sorteado 90d", br(dm.menor_efeito_detectavel_90d_pp[3], 1) + " pontos", "q10d_dimensionamento_pilotos.csv")
chk("revisão", "MDE semanas alternadas 90d", br(dm.menor_efeito_detectavel_90d_pp[4], 1) + " pontos", "q10d_dimensionamento_pilotos.csv")
chk("revisão", "casos para +28 pontos", f"{int(round(dm.reclamacoes_avaliadas_por_grupo_em_90d[6]))} casos por grupo", "q10d_dimensionamento_pilotos.csv")
chk("revisão", "casos para +10 pontos", f"{int(round(dm.reclamacoes_avaliadas_por_grupo_em_90d[7]))} casos por grupo", "q10d_dimensionamento_pilotos.csv")
pp = ler("q11_reclamacoes_por_passageiro.csv").set_index("companhia")
for c in ["Azul", "LATAM", "Gol"]:
    chk("passageiros", f"{c} por passageiro", f"| {c} | {br(k.loc[c, 'por_10mil_voos'])} | {br(k.loc[c, 'graves_por_10mil_voos'])} | {br(pp.loc[c, 'por_10mil_passageiros'], 1)} | {br(pp.loc[c, 'graves_por_10mil_passageiros'], 1)} | {r0(k.loc[c, 'resolucao_pct'])}% |", "q11_reclamacoes_por_passageiro.csv")
    chk("passageiros", f"{c} pax por voo", r0(pp.loc[c, "passageiros_por_voo"]), "q11_reclamacoes_por_passageiro.csv")
chk("passageiros", "Azul/LATAM graves por passageiro", br(pp.loc["Azul", "graves_por_10mil_passageiros"] / pp.loc["LATAM", "graves_por_10mil_passageiros"], 1) + " vezes por passageiro", "q11_reclamacoes_por_passageiro.csv")

# revisão camada 1, 2ª rodada (q12) e economia da folga
fd = ler("qc_folga_dinamica.csv").set_index("estrategia")
mf = fd.loc["sazonal x1 + no dia x1", "minutos_de_atraso_evitados_por_minuto_de_folga"]
chk("revisão 2", "minuto evitado por minuto de folga", br(mf, 2) + " minuto", "qc_folga_dinamica.csv")
ma = ler("q12a_mes_ano_tempo_bom.csv").set_index("mes")
chk("revisão 2", "dez/24 tempo bom", br(ma.loc["2024-12", "atraso_tempo_bom_pct"], 1) + "% em dez/2024", "q12a_mes_ano_tempo_bom.csv")
chk("revisão 2", "dez/25 sem vendaval tempo bom", br(ma.loc["2025-12 sem 10-12/12", "atraso_tempo_bom_pct"], 1) + "% em dez/2025", "q12a_mes_ano_tempo_bom.csv")
chk("revisão 2", "outros meses tempo bom", br(ma.loc["média dos outros meses (tempo bom, sem nov e dez)", "atraso_tempo_bom_pct"], 1) + "% nos meses fora do fim de ano", "q12a_mes_ano_tempo_bom.csv")
chk("revisão 2", "dez/24 atraso", br(ma.loc["2024-12", "atraso_pct"], 1) + "% (2024)", "q12a_mes_ano_tempo_bom.csv")
chk("revisão 2", "dez/25 atraso", br(ma.loc["2025-12", "atraso_pct"], 1) + "% (2025)", "q12a_mes_ano_tempo_bom.csv")
rc = ler("q12c_recuperacao_por_etapa.csv").set_index("faixa")
chk("revisão 2", "Azul mix LATAM", br(rc.loc["Azul com a taxa da LATAM em cada faixa", "rec_azul_pct"], 1) + "%", "q12c_recuperacao_por_etapa.csv")
chk("revisão 2", "Azul mix Gol", br(rc.loc["Azul com a taxa da Gol em cada faixa", "rec_azul_pct"], 1) + "%", "q12c_recuperacao_por_etapa.csv")
pt = ler("q12d_piloto_tempo_em_solo.csv").iloc[-1]
chk("revisão 2", "teto tempo em solo", "a tarde de GRU atrasaria " + br(pt.teto_do_efeito_pp, 1) + " pontos", "q12d_piloto_tempo_em_solo.csv")
chk("revisão 2", "metade do teto", br(pt.metade_do_teto_pp, 1) + " pontos", "q12d_piloto_tempo_em_solo.csv")
chk("revisão 2", "MDE sorteio por dia", "sortear dias inteiros, " + br(pt.mde_sorteio_por_dia_90d_pp, 1), "q12d_piloto_tempo_em_solo.csv")
import base as _b
_v = _b.voos_escopo(); _r = _v[~_v.cancelado]
chk("revisão 2", "minutos por voo realizado", br(_r.minutos_atraso.sum() / len(_r), 1) + " minutos por voo realizado", "voos (base)")

ma2 = ler("q12a_mes_ano_tempo_bom.csv").set_index("mes")
chk("revisão 2", "taxa tarde GRU", "taxa de " + br(ler("q12d_piloto_tempo_em_solo.csv").iloc[-1].taxa_tarde_gru_pct, 1) + "% na tarde de GRU", "q12d_piloto_tempo_em_solo.csv")
ex = ler("q7_recorrencias_excesso.csv")
sete = {"Azul": ["Preterição (overbooking)", "Alteração pela empresa: alternativas", "Bagagem extraviada"], "LATAM": ["Alteração pela empresa: aviso", "Oferta e compra"],
        "Gol": ["Assistência material no atraso", "Check-in e embarque"]}
pa = {c: ex[(ex.companhia == c) & ex.tema.isin(t)].por_ano.sum() for c, t in sete.items()}
chk("metas", "temas recorrentes a menos por ano", f"Cerca de {br(pa['Azul'] / 1000, 1)} mil reclamações a menos por ano na Azul, {br(pa['LATAM'] / 1000, 1)} mil na LATAM e {br(pa['Gol'] / 1000, 1)} mil na Gol", "q7_recorrencias_excesso.csv")
pr = ler("q6_pares_companhia_aeroporto.csv").set_index(["companhia", "iata"])
chk("metas", "LATAM CNF", f"{r0(pr.loc[('LATAM', 'CNF'), 'recl_por_10mil_mov'])} reclamações por 10 mil movimentos | 250 | **{r0(pr.loc[('LATAM', 'CNF'), 'esperado'])}**", "q6_pares_companhia_aeroporto.csv")
chk("metas", "Gol VCP", f"{r0(pr.loc[('Gol', 'VCP'), 'recl_por_10mil_mov'])} reclamações por 10 mil movimentos | 90 | **{r0(pr.loc[('Gol', 'VCP'), 'esperado'])}**", "q6_pares_companhia_aeroporto.csv")
chk("metas", "Gol VCP vezes", br(pr.loc[("Gol", "VCP"), "recl_por_10mil_mov"] / pr.loc[("Gol", "VCP"), "esperado"], 1) + " vezes", "q6_pares_companhia_aeroporto.csv")
c1 = ler("q6_c1_atraso_para_reclamacao.csv")
chk("C1", "razão operacionais", br(c1.aumento_pct[1] / c1.aumento_pct[0], 1) + " vez a reclamação de atrasar nas reclamações operacionais", "q6_c1_atraso_para_reclamacao.csv")
chk("C1", "razão todas com aeroporto", br(c1.aumento_pct[3] / c1.aumento_pct[2], 1) + " vez em todas as reclamações que citam aeroporto", "q6_c1_atraso_para_reclamacao.csv")
ea2 = ler("qc_p1_efeito_aeroporto_sem_clima.csv")
chk("P1", "GRU com tempo bom", "+" + br(ea2.set_index("iata").loc["GRU", "efeito_tempo_normal_pp"], 1) + " só com tempo bom", "qc_p1_efeito_aeroporto_sem_clima.csv")
rt = ler("q7_resolucao_por_tema.csv").set_index("tema")
chk("metas", "bagagem extraviada Gol/Azul", f"| {r0(rt.loc['Bagagem extraviada', 'Gol'])}% / {r0(rt.loc['Bagagem extraviada', 'Azul'])}% | 50% / 60% | **{r0(rt.loc['Bagagem extraviada', 'LATAM'])}%** |", "q7_resolucao_por_tema.csv")

# 3ª rodada
ma3 = ler("q12a_mes_ano_tempo_bom.csv").set_index("mes")
chk("revisão 3", "dezembros sem vendaval tempo bom", br(ma3.loc["dezembros juntos sem 10-12/12", "atraso_tempo_bom_pct"], 1) + "%, contra 6,3%", "q12a_mes_ano_tempo_bom.csv")
pp3 = ler("q12f_ponte_premio.csv").iloc[0]
chk("revisão 3", "ponte melhor caso por ano", f"cerca de {int(round(pp3.cancelamentos_evitaveis_por_ano_teto, -1))} cancelamentos a menos por ano", "q12f_ponte_premio.csv")
chk("revisão 3", "ponte meta 12 meses", f"{br(pp3.taxa_intermediaria_pct, 1)}% 12 meses após a decisão da 2b (cerca de {int(round(pp3.meta_intermediaria_12_meses, -1))} cancelamentos", "q12f_ponte_premio.csv")
fl = ler("qc_folga_local_cgh_vcp.csv").set_index("estrategia")
chk("revisão 3", "efeito esperado folga CGH VCP (só sazonal)", "queda de " + br(fl.loc["só sazonal", "queda_pp"], 1) + " ponto", "qc_folga_local_cgh_vcp.csv")
chk("revisão 3", "com a reserva junto", "a queda seria de " + br(fl.loc["sazonal + no dia a 60%", "queda_pp"], 1) + " ponto", "qc_folga_local_cgh_vcp.csv")
dm3 = ler("q10d_dimensionamento_pilotos.csv")
f90 = dm3.menor_efeito_detectavel_90d_pp[[8, 10, 12]]; f180 = dm3.menor_efeito_detectavel_180d_pp[[8, 10, 12]]
chk("revisão 3", "folga por companhia 90 e 180", f"quedas de {br(f90.min(), 1)} a {br(f90.max(), 1)} ponto em 90 dias e de {br(f180.min(), 1)} a {br(f180.max(), 1)} ponto em 180", "q10d_dimensionamento_pilotos.csv")
g90 = dm3.menor_efeito_detectavel_90d_pp[[11, 13]]; g180 = dm3.menor_efeito_detectavel_180d_pp[[11, 13]]
chk("revisão 3", "GRU tarde por companhia", f"de {br(g90.min(), 1)} a {br(g90.max(), 1)} pontos em 90 dias e de {br(g180.min(), 1)} a {br(g180.max(), 1)} em 180", "q10d_dimensionamento_pilotos.csv")
ge = ler("q12g_erros_de_data.csv").iloc[0]
chk("revisão 3", "voos com erro de data", f"Há {int(ge.voos_com_erro_de_data)} voos com a data", "q12g_erros_de_data.csv")
se = ler("q12e_dezembro_por_semana.csv").set_index("semana")
chk("revisão 3", "última semana de dezembro", f"{br(se.loc['24 a 31/12', '2024'], 1)}% nos dois anos de 24 a 31/12", "q12e_dezembro_por_semana.csv")
chk("revisão 3", "1ª semana dez 2024", f"{br(se.loc['1 a 7/12', '2024'], 1)}% e {br(se.loc['1 a 7/12', '2025'], 1)}% de 1 a 7/12", "q12e_dezembro_por_semana.csv")

# ponte: razão contra o resto da rede das três grandes (taxa total da ponte e da rede das três grandes, sem filtro de METAR)
import sqlite3 as _sq
from base import DB as _DB, ESCOPO as _ESC
_c = _sq.connect(_DB)
_p = _c.execute(f"""SELECT AVG(situacao='CANCELADO') FROM voos WHERE {_ESC} AND empresa IN ('AZU','TAM','GLO')
                    AND ((origem='SBSP' AND destino='SBRJ') OR (origem='SBRJ' AND destino='SBSP'))""").fetchone()[0]
_r = _c.execute(f"""SELECT AVG(situacao='CANCELADO') FROM voos WHERE {_ESC} AND empresa IN ('AZU','TAM','GLO')
                    AND NOT ((origem='SBSP' AND destino='SBRJ') OR (origem='SBRJ' AND destino='SBSP'))""").fetchone()[0]
chk("ponte", "razão ponte x resto das três grandes", f"cancela {br(_p / _r, 1)} vezes mais que o resto da rede das três grandes", "voos (base)")
chk("ponte", "taxas ponte x resto", f"({br(100 * _p, 1)}% contra {br(100 * _r, 1)}%)", "voos (base)")

out = salvar(pd.DataFrame(L), "conferencia_relatorio.csv")
print(f"{(out.esta_no_relatorio == 'sim').sum()} de {len(out)} números conferem")
print(out[out.esta_no_relatorio == "NÃO"][["tema", "descricao", "texto_procurado"]].to_string())
import sys
if (out.esta_no_relatorio == "NÃO").any():
    sys.exit(1)
