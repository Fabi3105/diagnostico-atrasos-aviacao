# -*- coding: utf-8 -*-
"""Validação da base carregada (rodar depois de carga.py). Saída: resultados/validacao_dados.csv,
uma linha por checagem, com o valor encontrado, se passou e a decisão tomada."""
import pandas as pd
from base import ler, salvar, ESCOPO, ICAO_IATA, IATA_ICAO, GRANDES

L = []
def chk(grupo, nome, valor, ok=True, nota=""):
    L.append({"grupo": grupo, "checagem": nome, "valor": valor, "passou": "sim" if ok else "NÃO", "observacao": nota})
um = lambda sql: ler(sql).iloc[0, 0]

# ---------------- VOOS
chk("voos", "linhas no VRA", f"{um('SELECT COUNT(*) FROM voos'):,}", True, "24 arquivos mensais, set/2024 a ago/2026")
m = ler("SELECT arquivo, COUNT(*) n FROM voos GROUP BY 1")
chk("voos", "arquivos mensais", len(m), len(m) == 24, f"menor mês {m.n.min():,} linhas, maior {m.n.max():,}")
t = ler("SELECT tipo_linha, COUNT(*) n FROM voos GROUP BY 1").fillna("vazio")
chk("voos", "tipo de linha", "; ".join(f"{a}={b:,}" for a, b in zip(t.tipo_linha, t.n)), True,
    "N doméstico regular, I internacional, G cargueiro, C charter. Escopo: N (definição B)")
sp = ler("SELECT situacao, COUNT(*) n FROM voos WHERE partida_prev IS NULL GROUP BY 1")
chk("voos", "registros sem horário previsto", "; ".join(f"{a}={b:,}" for a, b in zip(sp.situacao, sp.n)), True,
    "voos não programados (extras, traslados, retornos ao pátio, testes; muitos com prefixo Z e origem = destino). "
    "Não são promessa ao passageiro: fora do escopo")
chk("voos", "realizados sem horário real", um("SELECT COUNT(*) FROM voos WHERE situacao='REALIZADO' AND partida_real IS NULL"),
    um("SELECT COUNT(*) FROM voos WHERE situacao='REALIZADO' AND partida_real IS NULL") == 0)
chk("voos", "cancelados com horário real", um("SELECT COUNT(*) FROM voos WHERE situacao='CANCELADO' AND partida_real IS NOT NULL"),
    um("SELECT COUNT(*) FROM voos WHERE situacao='CANCELADO' AND partida_real IS NOT NULL") == 0)
dup = um("""SELECT COUNT(*) - COUNT(DISTINCT empresa||'|'||voo||'|'||partida_prev||'|'||origem) FROM voos
            WHERE partida_prev IS NOT NULL""")
chk("voos", "voos repetidos (empresa, número, origem, partida prevista)", dup, dup < 1000,
    "menos de 0,01% da base; mantidos, sem efeito nas taxas")
chk("voos", "justificativa de atraso preenchida", um("SELECT COUNT(*) FROM voos WHERE justificativa IS NOT NULL"), True,
    "campo vazio desde 2020 (revogação da IAC 1504): a causa do atraso não é observável")

e = ler(f"SELECT situacao, atraso_partida, atraso_chegada, empresa, origem, destino, mes FROM voos WHERE {ESCOPO}")
re = e[e.situacao == "REALIZADO"]
chk("escopo", "voos no escopo (domésticos regulares com horário previsto)", f"{len(e):,}", True,
    f"realizados {len(re):,}; cancelados {(e.situacao == 'CANCELADO').sum():,}")
mm = e.groupby("mes").size()
chk("escopo", "voos por mês no escopo", f"{mm.min():,} a {mm.max():,}", mm.min() > 0.7 * mm.max(),
    "variação sazonal normal, sem mês faltando ou incompleto")
g = e.empresa.value_counts(normalize=True)
chk("escopo", "participação de Azul, LATAM e Gol", f"{100 * g[GRANDES].sum():.1f}%", True,
    "; ".join(f"{k} {100 * v:.1f}%" for k, v in g.head(6).items()))
chk("escopo", "atraso de partida acima de 24 horas", int((re.atraso_partida > 1440).sum()), True,
    "mantidos nas taxas (são atrasos reais); médias usam mediana ou limite para não serem distorcidas")
chk("escopo", "partida mais de 2 horas antes do previsto", int((re.atraso_partida < -120).sum()), True,
    "provável troca de horário não atualizada; contam como 'antecipado'")
chk("escopo", "atraso de partida acima de 30 min", f"{100 * (re.atraso_partida > 30).mean():.1f}%", True,
    "definição A (classe oficial ANAC)")
chk("escopo", "atraso de chegada acima de 30 min", f"{100 * (re.atraso_chegada > 30).mean():.1f}%", True)
chk("escopo", "partidas antes do horário previsto", f"{100 * (re.atraso_partida < 0).mean():.1f}%", True,
    "dado de partida = saída do pátio (calço), não decolagem")
chk("escopo", "taxa de cancelamento", f"{100 * (e.situacao == 'CANCELADO').mean():.1f}%", True,
    "cancelados ÷ voos previstos (definição C). A base não diz com que antecedência o voo foi cancelado")
cob = e.origem.isin(ICAO_IATA).mean()
chk("escopo", "voos com aeroporto de origem traduzido para IATA", f"{100 * cob:.2f}%", cob > 0.99,
    "tabela ICAO->IATA montada pelo analista (base.py); necessária para ligar voos às reclamações")

# fuso: blocos de voo de ida e volta entre fusos diferentes e horário de funcionamento de Congonhas
f = ler(f"""SELECT origem, destino, AVG(duracao_prev) d FROM voos WHERE {ESCOPO}
            AND origem IN ('SBGR','SBEG') AND destino IN ('SBGR','SBEG') GROUP BY 1,2""")
h = ler(f"SELECT MIN(hora) a, MAX(hora) b FROM voos WHERE {ESCOPO} AND origem='SBSP'")
chk("fuso", "horário dos registros", "horário de Brasília",
    abs(f.d.iloc[0] - f.d.iloc[1]) < 15 and h.a[0] >= 5,
    f"GRU->MAO e MAO->GRU com duração prevista igual ({f.d.iloc[0]:.0f} e {f.d.iloc[1]:.0f} min) e Congonhas "
    f"com partidas das {h.a[0]:.0f}h às {h.b[0]:.0f}h (o aeroporto fecha à noite). Aeroportos de outro fuso são "
    "ajustados pelo estado quando a análise for por hora local")

# ---------------- RECLAMAÇÕES
r = ler("SELECT * FROM reclamacoes")
chk("reclamacoes", "linhas", f"{len(r):,}", True, "; ".join(f"{a}: {b:,}" for a, b in r.data_abertura.str[:4].value_counts().sort_index().items()))
chk("reclamacoes", "período", f"{r.data_abertura.min()} a {r.data_abertura.max()}", True,
    "cruzamento com voos: set/2024 a dez/2025 (16 meses em comum)")
chk("reclamacoes", "companhia sem código ICAO", int(r.empresa.isna().sum()), r.empresa.isna().sum() == 0)
gr = r.empresa.value_counts(normalize=True)
chk("reclamacoes", "participação de Azul, LATAM e Gol", f"{100 * gr[GRANDES].sum():.1f}%", True)
chk("reclamacoes", "sem código classificador ANAC", int(r.codigo.isna().sum()), True,
    f"{100 * r.codigo.isna().mean():.1f}%; ficam fora das análises por tema e aeroporto")
chk("reclamacoes", "código com formato inválido", int(((r.n_grupos == 0) & r.codigo.notna()).sum()),
    ((r.n_grupos == 0) & r.codigo.notna()).sum() == 0)
chk("reclamacoes", "reclamações com mais de um local/grupo", int((r.n_grupos > 1).sum()), True,
    "todos os grupos entram na contagem por aeroporto e tema")
c = ler("SELECT * FROM rec_codigos")
chk("reclamacoes", "códigos de assunto sem tema reconhecido", int(c.gravidade.isna().sum()), c.gravidade.isna().mean() < 0.01)
gv = r.gravidade.value_counts(normalize=True)
chk("reclamacoes", "gravidade (definição F)", "; ".join(f"{k} {100 * v:.1f}%" for k, v in gv.items()), True,
    "pior tema da reclamação")
c1 = c[c.grupo == 1]
aer = c1.local.str.len() == 3
chk("reclamacoes", "reclamações com aeroporto informado", f"{100 * aer.mean():.1f}%", True,
    "as demais ocorreram em site, aplicativo, telefone, loja ou agência (letra no campo Local)")
dom = c[(c.local.str.len() == 3) & (c.operacao == "D")]
sem = dom[~dom.local.isin(IATA_ICAO)].local.value_counts()
chk("reclamacoes", "aeroportos de voo doméstico sem tradução para ICAO", f"{sem.sum():,} citações",
    sem.sum() < 0.02 * len(dom), f"{100 * sem.sum() / len(dom):.1f}% das citações domésticas; principais: "
    + ", ".join(f"{a} {b}" for a, b in sem.head(8).items()))
chk("reclamacoes", "nota fora de 1 a 5", int(((r.nota < 1) | (r.nota > 5)).sum()), ((r.nota < 1) | (r.nota > 5)).sum() == 0,
    f"sem nota: {100 * r.nota.isna().mean():.1f}% (consumidor não avaliou)")
ab = r.situacao.isin(["Respondida", "Em análise pelo gestor", "Em análise pelo fornecedor", "Aberta", "Não respondida"])
chk("reclamacoes", "reclamações ainda não finalizadas", f"{ab.sum():,}", True,
    "sem avaliação final do consumidor; contam no volume, não na taxa de resolução")
ae = r.avaliacao_empresa.value_counts(normalize=True)
chk("reclamacoes", "classificação da própria empresa", "; ".join(f"{k} {100 * v:.1f}%" for k, v in ae.items()), True,
    "P procedente, M parcialmente, I improcedente, N não informou. É a visão da empresa, não do consumidor")

n_erro = um(f"""SELECT COUNT(*) FROM voos WHERE {ESCOPO} AND situacao <> 'CANCELADO' AND ABS(atraso_partida) >= 1350
                AND (ABS(atraso_partida) % 1440 < 90 OR ABS(atraso_partida) % 1440 > 1350)""")
chk("voos", "erros de data (atraso perto de múltiplo de 24 h)", n_erro, True,
    "Partida prevista registrada em outro dia (ex.: AZU 2612 em nov/2024). Ficam fora das taxas e dos minutos (base.voos_escopo)")
dup = um(f"SELECT COUNT(*) - COUNT(DISTINCT empresa || voo || partida_prev) FROM voos WHERE {ESCOPO}")
chk("voos", "voos duplicados (empresa, número, partida prevista)", dup, dup < 100, "Desprezível (de 1,57 milhão)")
_cols = [c for c in ler("PRAGMA table_info(reclamacoes)").name if c != "id"]
rd = um("SELECT COUNT(*) FROM reclamacoes") - um(f"SELECT COUNT(*) FROM (SELECT DISTINCT {', '.join(_cols)} FROM reclamacoes)")
chk("reclamações", "linhas iguais em todos os campos menos o protocolo", rd, True,
    "Mantidas: têm protocolos diferentes e podem ser reclamações repetidas; 0,6% do total, nenhuma conclusão muda")

out = salvar(pd.DataFrame(L), "validacao_dados.csv")
pd.set_option("display.width", 250, "display.max_colwidth", 140)
print(out.to_string())
