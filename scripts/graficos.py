# -*- coding: utf-8 -*-
"""Gráficos do relatório (resultados/graficos/*.png), feitos só a partir dos CSVs de resultados/."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from base import RES

OUT = RES / "graficos"; OUT.mkdir(exist_ok=True)
# mesma identidade do painel (painel de partidas): azul-marinho, âmbar e as cores fixas de cada companhia
AZUL, LARANJA, AQUA, AMARELO, CINZA = "#1c5cab", "#d0453f", "#1c5cab", "#e0a100", "#b4bcc8"
CIA = {"Azul": "#2a78d6", "LATAM": "#8e3fa6", "Gol": "#eb6834"}
TXT, TXT2, GRADE, NAVY = "#0f1a2a", "#465265", "#e8ecf1", "#0a1628"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11.5, "axes.edgecolor": GRADE, "axes.labelcolor": TXT2,
                     "xtick.color": TXT2, "ytick.color": TXT2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "figure.dpi": 150, "savefig.bbox": "tight", "axes.titlesize": 12.5, "axes.titleweight": "bold",
                     "axes.titlecolor": NAVY, "axes.titlelocation": "left", "axes.titlepad": 10})
ler = lambda n, **k: pd.read_csv(RES / n, encoding="utf-8-sig", **k)
vir = lambda v, c=1: f"{v:.{c}f}".replace(".", ",")
def salvar(fig, nome):
    fig.savefig(OUT / nome); plt.close(fig)

# g1. Quem explica o atraso e o cancelamento entre as três grandes (P1) e as reclamações (P6)
d1 = ler("q1_decomposicao.csv").set_index("indicador"); dc = ler("qc_p1_decomposicao_sem_clima.csv")
d6 = ler("q6_decomposicao_companhia_aeroporto.csv").set_index("indicador")
lin = [("Atraso (todos os voos)", d1.loc["atraso > 30 min (só Azul, LATAM e Gol)", "companhia_pct_do_explicado_por_ambos"]),
       ("Atraso (só tempo normal)", dc.iloc[1]["companhia_pct_do_explicado_por_ambos"]),
       ("Cancelamento", d1.loc["cancelamento (só Azul, LATAM e Gol)", "companhia_pct_do_explicado_por_ambos"]),
       ("Reclamações (volume)", d6.loc["todas as reclamações com aeroporto", "companhia_pct_do_explicado"]),
       ("Reclamações graves", d6.loc["reclamações graves", "companhia_pct_do_explicado"]),
       ("Assistência no atraso", d6.loc["tema: Assistência material no atraso", "companhia_pct_do_explicado"]),
       ("Preterição (overbooking)", d6.loc["tema: Preterição (overbooking)", "companhia_pct_do_explicado"]),
       ("Bagagem avariada", d6.loc["tema: Bagagem avariada", "companhia_pct_do_explicado"])][::-1]
fig, ax = plt.subplots(figsize=(6.4, 3.6))
y = [a for a, _ in lin]; c = np.array([b for _, b in lin])
ax.barh(y, c, color=AZUL, height=0.6, label="companhia"); ax.barh(y, 100 - c, left=c, color=CINZA, height=0.6, label="aeroporto")
for yi, v in zip(y, c):
    ax.text(v - 1.5, yi, f"{vir(v, 0)}%", va="center", ha="right", color="white", fontsize=10, fontweight="bold")
    ax.text(v + 1.5, yi, f"{vir(100 - v, 0)}%", va="center", ha="left", color=TXT, fontsize=10)
ax.set_xlim(0, 100); ax.set_xlabel("% da diferença explicada pelos dois fatores"); ax.grid(axis="y", visible=False)
ax.axhline(4.5, color=TXT2, lw=0.6, ls="--")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=10.5)
ax.set_title("Operação: pesa o aeroporto. Problema grave: pesa a companhia")
salvar(fig, "g1_companhia_x_aeroporto.png")

# g2. Concentração dos minutos de atraso por aeroporto (M1)
a = ler("q1_aeroportos.csv").head(12)
fig, ax = plt.subplots(figsize=(6.4, 3.2))
b = ax.bar(a.iata, a.parte_dos_minutos_pct, color=[LARANJA if i < 2 else AZUL for i in range(len(a))], width=0.65)
ax.bar_label(b, labels=[vir(v) for v in a.parte_dos_minutos_pct], padding=2, fontsize=10)
ax.set_ylabel("% dos minutos de atraso do país"); ax.set_ylim(0, 19); ax.grid(axis="x", visible=False)
ax.set_title("GRU e Congonhas somam 27% de todo o atraso; seis aeroportos, metade")
for t in ax.get_xticklabels(): t.set_fontfamily("DejaVu Sans Mono"); t.set_fontweight("bold")
salvar(fig, "g2_minutos_por_aeroporto.png")

# g3. Curva do atraso ao longo do dia (P2)
h = ler("q2_curva_hora.csv")
fig, ax = plt.subplots(figsize=(6.4, 3.2))
ax.bar(h.hora_local, h.mercado_parte_dos_voos_pct, color=GRADE, width=0.8, label="% dos voos na hora")
for cia, cor in CIA.items():
    ax.plot(h.hora_local, h[f"{cia}_atraso30_pct"], color=cor, lw=1.6, label=cia)
ax.plot(h.hora_local, h.mercado_atraso30_pct, color=TXT, lw=2.4, label="mercado")
ax.set_xticks(range(0, 24, 2)); ax.set_xlabel("hora local da partida prevista"); ax.set_ylabel("% de partidas com atraso > 30 min")
ax.legend(frameon=False, ncol=5, fontsize=10, loc="upper left"); ax.set_ylim(0, 19); ax.grid(axis="x", visible=False)
ax.set_title("O atraso se acumula ao longo do dia")
salvar(fig, "g3_curva_hora.png")

# g4. Probabilidade de atraso conforme as chegadas anteriores (P2b)
p = ler("q2b_probabilidade_por_situacao.csv").set_index("situacao_cheg")
ordem = ["chegadas no horário", "sem chegada na janela", "parcial", "giro comprometido (>=50%)"]
rot = ["chegadas\nno horário", "sem chegada antes\n(avião de pernoite)", "parte das chegadas\natrasadas", "maioria das chegadas\natrasadas"]
fig, ax = plt.subplots(figsize=(6.4, 3.0))
v = p.loc[ordem, "atraso30_pct"]
b = ax.bar(rot, v, color=[AQUA, AQUA, AMARELO, LARANJA], width=0.6)
ax.bar_label(b, labels=[f"{vir(x)}%" for x in v], padding=2); ax.tick_params(axis="x", labelsize=8.5)
ax.set_ylabel("% de partidas com atraso > 30 min"); ax.set_ylim(0, 34); ax.grid(axis="x", visible=False)
ax.set_title("A partida atrasa 11 vezes mais quando a maioria das chegadas anteriores atrasa")
salvar(fig, "g4_atraso_herdado.png")

# g5. Recuperação no ar x folga no tempo de voo (P3/C2)
r = ler("q3_recuperacao_no_ar_companhia.csv").set_index("companhia").loc[["Gol", "LATAM", "Azul"]]
fig, ax = plt.subplots(figsize=(6.4, 2.8))
b = ax.barh(r.index[::-1], r.chegaram_ate_15min_pct[::-1], color=[CIA[i] for i in r.index[::-1]], height=0.55)
for yi, (pct, f) in enumerate(zip(r.chegaram_ate_15min_pct[::-1], r.folga_media_ponderada_min[::-1])):
    ax.text(pct + 0.5, yi, f"{vir(pct)}%   (folga média de {vir(f)} min no tempo de bloco)", va="center", fontsize=10.5)
ax.set_xlim(0, 45); ax.set_xlabel("% que chega até 15 min do previsto, entre os que saem com +15 min de atraso"); ax.grid(axis="y", visible=False)
ax.set_title("Quem tem mais folga no horário recupera mais no trecho")
salvar(fig, "g5_recuperacao_no_ar.png")

# g6. Eficiência das estratégias de folga (teste no 2º ano)
f = ler("qc_folga_dinamica.csv").iloc[1:]
nomes = {"folga uniforme de 2 min": "uniforme 2 min", "folga uniforme de 3 min": "uniforme 3 min", "folga uniforme de 5 min": "uniforme 5 min",
         "folga sazonal planejada (aeroporto x mês x faixa) x1": "sazonal planejada", "folga sazonal planejada (aeroporto x mês x faixa) x2": "sazonal planejada (x2)",
         "folga no dia, só com tempo ruim x1": "no dia, tempo ruim*", "folga no dia, só com tempo ruim x2": "no dia, tempo ruim (x2)*",
         "sazonal x1 + no dia x1": "sazonal + no dia*"}
f["n"] = f.estrategia.map(nomes)
f = f.sort_values("evitados_por_mil_minutos")
fig, ax = plt.subplots(figsize=(6.4, 3.2))
cores = [CINZA if "uniforme" in n else AQUA for n in f.n]
b = ax.barh(f.n, f.evitados_por_mil_minutos, color=cores, height=0.6)
for yi, (e, m, at) in enumerate(zip(f.evitados_por_mil_minutos, f.minutos_de_folga_por_voo, f.atraso30_pct)):
    ax.text(e + 0.05, yi, f"{vir(e, 1)}  ({vir(m, 1)} min/voo)", va="center", fontsize=10)
ax.set_xlim(0, 6.4); ax.set_xlabel("atrasos evitados por 1.000 min de folga\n(regra do 1º ano testada no 2º; * supõe previsão perfeita do tempo)"); ax.grid(axis="y", visible=False)
ax.set_title("Folga direcionada evita mais atrasos por minuto")
salvar(fig, "g6_folga_dinamica.png")

# g7. Atraso por mês: todos os voos x só tempo normal (P4 + clima)
m = ler("qc_p4_clima_por_mes.csv", dtype={"mes": str})
mes = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
fig, ax = plt.subplots(figsize=(6.4, 3.0))
ax.plot(mes, m.atraso30_pct, color=LARANJA, lw=2.2, marker="o", ms=4, label="todos os voos")
ax.plot(mes, m.atraso30_tempo_normal_pct, color=AZUL, lw=2.2, marker="o", ms=4, label="só com tempo bom na origem e no destino")
ax.bar(mes, m.horas_severas_pct, color=GRADE, width=0.6, label="% de horas com tempo severo (10 maiores aeroportos)")
ax.annotate(vir(m.atraso30_pct.iloc[-1]), (11, m.atraso30_pct.iloc[-1]), xytext=(6, -2), textcoords="offset points", fontsize=10.5, color=LARANJA)
ax.annotate(vir(m.atraso30_tempo_normal_pct.iloc[-1]), (11, m.atraso30_tempo_normal_pct.iloc[-1]), xytext=(6, -4), textcoords="offset points", fontsize=10.5, color=AZUL)
ax.set_ylabel("%"); ax.set_ylim(0, 16); ax.grid(axis="x", visible=False); ax.legend(frameon=False, fontsize=10, loc="upper left")
ax.set_title("O fim de ano é o pior período, mesmo com tempo bom")
salvar(fig, "g7_mes_clima.png")

# g8. Dias de pico x dias comuns por hora (P4)
t = ler("q4_hora_por_tipo_de_dia.csv")
fig, ax = plt.subplots(figsize=(6.4, 2.9))
ax.plot(t.hora_local, t["dia comum"], color=AZUL, lw=2, label="dia comum")
ax.plot(t.hora_local, t["pico (10% mais cheios e feriados)"], color=LARANJA, lw=2, label="dia de pico (10% mais cheios e feriados)")
ax.fill_between(t.hora_local, t["dia comum"], t["pico (10% mais cheios e feriados)"], where=t["pico (10% mais cheios e feriados)"] > t["dia comum"], color=LARANJA, alpha=0.15)
ax.set_xticks(range(0, 24, 2)); ax.set_xlabel("hora local"); ax.set_ylabel("% de atraso > 30 min"); ax.set_ylim(0, 15)
ax.legend(frameon=False, fontsize=10, loc="upper left"); ax.grid(axis="x", visible=False)
ax.set_title("No pico do ano, piora o fim de tarde, não a manhã")
salvar(fig, "g8_pico_hora.png")

# g9. Sensibilidade ao tempo severo por aeroporto
w = ler("qc_impacto_clima_aeroporto.csv").head(10).sort_values("acrescimo_severo_pp")
fig, ax = plt.subplots(figsize=(6.4, 3.2))
yy = np.arange(len(w))
ax.barh(yy - 0.18, w.atraso_normal_pct, height=0.36, color=CINZA, label="tempo normal")
ax.barh(yy + 0.18, w.atraso_severo_pct, height=0.36, color=LARANJA, label="tempo severo")
for yi, s in zip(yy, w.atraso_severo_pct):
    ax.text(s + 0.4, yi + 0.18, vir(s), va="center", fontsize=10)
ax.set_yticks(yy, w.iata, fontfamily="DejaVu Sans Mono", fontweight="bold"); ax.set_xlabel("% de atraso > 30 min"); ax.set_xlim(0, 30); ax.grid(axis="y", visible=False)
ax.legend(frameon=False, fontsize=10, loc="lower right"); ax.set_title("Tempo severo: SDU, CGH e GRU sofrem; Curitiba quase não")
salvar(fig, "g9_clima_aeroporto.png")

# g10. Reclamações das brasileiras por 10 mil voos (P5)
k = ler("q5_ranking_companhias.csv")
k = k[k.empresa.isin(["AZU", "TAM", "GLO"])].set_index("companhia").loc[["Azul", "Gol", "LATAM"]]
fig, ax = plt.subplots(figsize=(6.4, 2.8))
yy = np.arange(3)[::-1]
ax.barh(yy, k.graves_por_10mil_voos, color=LARANJA, height=0.55, label="graves")
ax.barh(yy, k.por_10mil_voos - k.graves_por_10mil_voos, left=k.graves_por_10mil_voos, color=CINZA, height=0.55, label="média e baixa gravidade")
for yi, (g, t_, res) in zip(yy, zip(k.graves_por_10mil_voos, k.por_10mil_voos, k.resolucao_pct)):
    ax.text(t_ + 15, yi, f"{t_:,.0f} no total; {g:,.0f} graves; resolução {vir(res, 0)}%".replace(",", "."), va="center", fontsize=10)
ax.set_yticks(yy, k.index); ax.set_xlim(0, 2100); ax.set_xlabel("reclamações por 10 mil voos (set/2024 a dez/2025)"); ax.grid(axis="y", visible=False)
ax.legend(frameon=False, fontsize=10, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=2); ax.set_title("A Azul tem 3,2 vezes mais reclamações graves por voo que a LATAM")
salvar(fig, "g10_reclamacoes_companhias.png")

# g11. Resolução por tema: referência da melhor companhia (S1)
rt = ler("q7_resolucao_por_tema.csv").set_index("tema")
temas = ["Bagagem extraviada", "Bagagem avariada", "Assistência material no atraso", "Alternativas em atraso/cancelamento/preterição", "Comunicação sobre atraso/cancelamento"]
rot = ["Bagagem extraviada", "Bagagem avariada", "Assistência no atraso", "Alternativas no atraso\nou cancelamento", "Comunicação sobre atraso"]
fig, ax = plt.subplots(figsize=(6.4, 3.3))
yy = np.arange(len(temas))[::-1]
for i, cia in enumerate(["Azul", "Gol", "LATAM"]):
    ax.barh(yy + (1 - i) * 0.26, rt.loc[temas, cia], height=0.26, color=CIA[cia], label=cia)
ax.set_yticks(yy, rot); ax.set_xlim(0, 100); ax.set_xlabel("% das reclamações avaliadas que foram resolvidas"); ax.grid(axis="y", visible=False)
ax.legend(frameon=False, ncol=3, fontsize=10, loc="upper center", bbox_to_anchor=(0.5, -0.2))
ax.set_title("A LATAM resolve mais nos temas graves: é a referência")
salvar(fig, "g11_resolucao_tema.png")

# g12. Motivos estimados dos cancelamentos da ponte aérea (q8 + q9)
e = ler("q9_estimativa_motivos_ponte_2024_26.csv").set_index("grupo")
ordem = ["clima", "técnico-operacional (companhia)", "aeroporto fechado", "programado/autorizado"]
rot = ["Clima", "Técnico-\noperacional\n(companhia)", "Aeroporto\nfechado", "Programado /\ncomercial"]
lo = e.loc[ordem, ["estimativa_ponte_2024_26_pct", "estimativa_com_tabela_so_da_ponte_pct"]].min(axis=1)
hi = e.loc[ordem, ["estimativa_ponte_2024_26_pct", "estimativa_com_tabela_so_da_ponte_pct"]].max(axis=1)
dec = e.loc[ordem, "declarado_na_ponte_em_2019_pct"]
fig, ax = plt.subplots(figsize=(6.4, 3.0))
xx = np.arange(4)
ax.bar(xx - 0.2, dec, width=0.38, color=CINZA, label="declarado pelas companhias em 2019")
ax.bar(xx + 0.2, (lo + hi) / 2, width=0.38, color=AZUL, yerr=[(hi - lo) / 2, (hi - lo) / 2], capsize=4, label="estimado para 2024-26 (faixa)")
for xi, l, h_ in zip(xx, lo, hi):
    ax.text(xi + 0.2, h_ + 2.5, f"{int(l + 0.5)}-{int(h_ + 0.5)}%", ha="center", fontsize=10)
ax.set_xticks(xx, rot); ax.set_ylim(0, 80); ax.set_ylabel("% dos cancelamentos da ponte"); ax.grid(axis="x", visible=False)
ax.legend(frameon=False, fontsize=10); ax.set_title("Ponte aérea: cerca de metade dos cancelamentos não é clima")
salvar(fig, "g12_motivos_ponte.png")
print(sorted(x.name for x in OUT.glob("*.png")))
