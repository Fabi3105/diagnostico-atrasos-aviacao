# Soluções e metas (Etapa 4) — rascunho aprovado em 10/10/2026

> **Rascunho histórico. A versão final está nas seções 2 a 4 do RELATORIO.md.** Depois deste rascunho, as revisões de 14/10/2026 mudaram: a solução 2 (deixou de ser "preferir atrasar a cancelar"; virou reduzir os cancelamentos técnico-operacionais da ponte e decidir pesando os voos protegidos); a meta de recuperação da Azul (21% a 24%, ajustada ao mix de etapas, em vez de 22,8% a 25,7%); o desenho dos pilotos (sorteio de números de voo nos mesmos aeroportos e dias e sorteio de casos no atendimento, com registros internos, prazos de 90 a 180 dias, em vez de aeroportos de comparação e consumidor.gov.br); a base passou a ter passageiros e bagagem (Dados Estatísticos da ANAC); a meta de dezembro segue em aberto; e a meta dos temas recorrentes passou a usar só os sete temas da tabela do relatório. Vários números deste rascunho foram refinados depois (ex.: LATAM resolve 64% em bagagem extraviada); vale sempre o relatório.

Perspectiva: gestão de operações e de atendimento de uma companhia aérea. As soluções são melhorias de serviço ao passageiro e de processo, não punições. Não há estimativa de custo em reais. O custo financeiro e o humano estão numa escala qualitativa (baixo, médio, alto), e a lista vai do mais barato ao mais caro. Toda meta indica o apoio nos dados; sem apoio, fica "em aberto", com a razão.

## 1. Soluções, da mais barata para a mais cara

| # | Solução | Base nos dados | Quem controla | Custo financeiro | Custo humano |
|---|---|---|---|---|---|
| S1 | **Fechar a lacuna de resolução por tema, copiando o processo da melhor companhia.** Bagagem, assistência e alternativas no atraso: roteiro de atendimento e alçada de solução no primeiro contato | P5/C5: a nota é quase só o desfecho (resolvida 4,6; não resolvida 1,3). Resolução de bagagem extraviada: Gol 37%, Azul 56%, LATAM 65%. Assistência no atraso: Gol 56%, LATAM 88%. Bagagem avariada: Gol 50%, LATAM 87% | Companhia (atendimento) | Baixo | Médio (treino, alçada) |
| S2 | **Preferir atraso a cancelamento quando houver escolha**, sobretudo na ponte aérea CGH-SDU | C1: por ponto, cancelar gera de 1,3 a 1,7 vez mais reclamações que atrasar. Na ponte aérea, o cancelamento é de 3,7% contra 1,5% no resto da rede, e o atraso é menor (6,7% contra 7,8%) | Companhia (centro de controle) | Baixo | Baixo |
| S3 | **Atacar as recorrências graves de cada companhia na origem do processo**: Azul (overbooking, alternativas na alteração de voo, bagagem extraviada), Gol (assistência no atraso, check-in), LATAM (aviso de alteração, oferta e compra) | P5: temas acima de 1,2 vez o mercado em 75% ou mais dos 16 meses; perfil estável e próprio de cada companhia (não é acaso). P6: a companhia leva o padrão de aeroporto em aeroporto | Companhia (comercial, aeroportos, atendimento) | Baixo a médio | Médio |
| S4 | **Folga sazonal planejada na malha**: mais tempo de solo e de voo por aeroporto × mês × faixa horária onde o histórico mostra atraso | P3 + clima: rende 4,5 atrasos evitados por 1.000 minutos de folga, contra cerca de 3,0 da folga uniforme (aprendida no 1º ano, testada no 2º) | Companhia (planejamento de malha) | Médio (menos uso do avião) | Baixo |
| S5 | **Folga e reserva no dia com previsão de tempo ruim**: alongar os giros da tarde, segurar avião e tripulação reserva nos aeroportos sensíveis (SDU, CGH, GRU, VCP, GIG) | Clima: tempo severo leva o atraso de 7,0% para 17,4%; a folga no dia rende 4,6 por 1.000 minutos. 13,6% dos atrasos são ligados ao clima | Companhia (centro de controle) | Médio | Médio |
| S6 | **Proteger o giro nos aeroportos que mais geram atraso em solo** (GRU, CGH, CNF, VCP): giro mínimo garantido, prioridade de equipe de solo para a aeronave que chega atrasada | P2b: com a maioria das chegadas atrasadas, a partida atrasa 29%; com as chegadas no horário, 2,6%. GRU e CGH somam 27% dos atrasos que nascem em solo | Companhia (aeroportos e solo) + operador do aeroporto | Médio | Alto |
| S7 | **Plano de dezembro**: reforço de equipe de solo, check-in e bagagem no pico de fim de ano | P4: dezembro atrasa 13,9% e, só com tempo normal, ainda 11,6%; o volume de voos quase não muda; os fins de tarde pioram mais nos dias de pico | Companhia | Médio | Alto |
| S8 | **Agenda com o aeroporto e o controle de tráfego** para GRU (pior efeito próprio mesmo com tempo bom) e para a resiliência a tempo ruim em SP e RJ, usando CWB como referência | P1 + clima: GRU +3,2 pontos com tempo normal. CWB sobe só 2 pontos com tempo severo, contra 15 em CGH | Operador do aeroporto, DECEA, governo (a companhia só influencia) | Alto (fora da companhia) | — |

## 2. Indicadores e metas

| Indicador | Hoje | Meta proposta | Apoio nos dados |
|---|---|---|---|
| Partidas com atraso > 30 min (rede) | 8,0% (2º ano) | **7,0%** com S4 + S5 (+2,31 min de folga média por voo) | Simulação aprendida no 1º ano e testada no 2º (`qc_folga_dinamica.csv`). Não inclui o ganho de propagação |
| Recuperação no ar: voos que saem com +15 min e chegam dentro de 15 min (Azul) | 14,2% | **22,8% a 25,7%** (nível LATAM e Gol) | Referência observada entre as três grandes (`q3_recuperacao_no_ar_companhia.csv`) |
| Resolução de bagagem extraviada (Gol / Azul) | 37% / 56% | **65%** (nível LATAM) | Referência observada (`q7_resolucao_por_tema.csv`) |
| Resolução de assistência no atraso (Gol / Azul) | 56% / 62% | **88%** (nível LATAM) | Referência observada |
| Resolução de bagagem avariada (Gol) | 50% | **80% a 87%** (Azul e LATAM) | Referência observada |
| Reclamações nos temas recorrentes | 1,3 a 2,3 vezes o mercado | **taxa do mercado (1,0 vez)** | Referência observada: o próprio mercado. Equivale a cerca de 8 mil reclamações a menos por ano na Azul, 0,6 mil na Gol e 5,4 mil na LATAM (`q7_recorrencias_excesso.csv`) |
| Cancelamento da ponte aérea CGH-SDU sem sinal externo (sem evento, tempo ruim ou fim do dia) | 2,8% dos voos nessas condições | **1,1%** (resto da rede nas mesmas condições); cerca de 860 cancelamentos a menos em 24 meses | Referência observada (`q8_ponte_aerea_motivos.csv`). Pelo VRA de 2019 (dado defasado, autodeclarado), 65% a 68% dos cancelamentos sem sinal eram técnico-operacionais da companhia (`q9_calibracao_sinal_x_motivo_2019.csv`). A meta é proposta, não comprovada: parte pode ser imposição externa não observada |
| Atraso em dezembro | 14,0% (Azul), 14,3% (LATAM), 12,8% (Gol) | **em aberto** | A causa não é clima nem volume, e a base não tem passageiros nem bagagem por voo para dimensionar o reforço. Sugere-se medir no piloto |
| Pares crônicos companhia × aeroporto (ex.: LATAM em CNF) | 317 reclamações por 10 mil movimentos | **180** (o esperado pelo modelo) | Modelo aditivo da P6 (`q6_pares_companhia_aeroporto.csv`) |
| Efeito do aeroporto GRU com tempo normal | +3,2 pontos | **em aberto** | A alavanca não é da companhia (S8) |

**Ligação com as reclamações (C1):** cada ponto a menos de atraso reduz as reclamações operacionais com aeroporto em cerca de 4,7%, e cada ponto a menos de cancelamento, em 6,2%. A meta de 7,0% de atraso equivale a cerca de 5% a menos nessas reclamações. Elas são 31% do total; o efeito sobre o total é menor.

## 3. Como ajustar

- Revisar a folga sazonal a cada temporada (IATA verão e inverno) com os dados do ano anterior. A regra é refeita, não fixa.
- Acompanhar mensalmente, por companhia × aeroporto: atraso, cancelamento, reclamações por 10 mil movimentos e a classe crônico, frequente ou pontual.
- Recalcular as referências de resolução a cada semestre. A melhor companhia em cada tema muda.

## 4. Decisão recomendada: pilotos de 90 dias com grupo de comparação

1. **Folga direcionada (S4 + S5)** em dois aeroportos sensíveis (sugestão: CGH e VCP), comparados com GRU, CNF e GIG sem mudança. Hipótese: −1 ponto de atraso de partida nos aeroportos do piloto, sem piora no resto da rede. Medida: atraso > 30 min, minutos de atraso, reclamações operacionais por 10 mil movimentos.
2. **Resolução no primeiro contato (S1)** para bagagem e assistência no atraso, em metade das filas de atendimento (sorteio), contra a outra metade. Hipótese: resolução de bagagem extraviada acima de 60% e nota média +0,5 no grupo do piloto. Medida: resolução e nota no consumidor.gov.br.
3. **Proteção do giro (S6)** em GRU, no banco da tarde, comparado com o mesmo banco em CGH. Hipótese: menor taxa de atraso nas partidas com chegadas atrasadas (hoje 29%). Medida: taxa por situação das chegadas (método P2b).
