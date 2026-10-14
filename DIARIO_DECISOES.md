# Diário de decisões — Voos e reclamações no setor aéreo (ANAC)

Registro, etapa a etapa, das perguntas, das decisões de método, dos resultados e da revisão do Fabian. Método: skill `analise-dados-negocio` v1.1.

## Origem do projeto

- **Decisão do Fabian (10/10/2026):** o projeto previsto era o das reclamações do consumidor.gov.br (todos os setores). Os arquivos oficiais estavam fora do ar (o servidor dados.mj.gov.br não responde e a aba de dados abertos do consumidor.gov.br está vazia). O Fabian escolheu seguir com a alternativa da ANAC, que publica no próprio servidor os voos (VRA) e as reclamações do setor aéreo no consumidor.gov.br.
- **Dados baixados:** VRA de set/2024 a ago/2026 (24 arquivos, cerca de 285 MB) e reclamações do setor aéreo de 2024 e 2025 (2 arquivos, cerca de 78 MB), em `dados/brutos/`. Baixados pelo navegador do Fabian, do servidor sistemas.anac.gov.br.

## Etapa 0. Briefing do negócio

- **Rascunho:** `BRIEFING_NEGOCIO.md`.
- **Revisão do Fabian (10/10/2026):** briefing aprovado. Perspectiva: **companhia aérea** ("pensando no portfólio, soluções empresariais são mais interessantes").
- **Perguntas do Fabian (10/10/2026), registradas como enviadas:**
  1. Quais companhias e aeroportos mais atrasam e cancelam, por voo operado? Analisar o fator companhia e o fator aeroporto separadamente e depois a relação entre eles ("quais e por quê?"), para mostrar onde a ação é mais eficiente.
  2. Como é o fluxo de atrasos ao longo do dia? Quais horários geram mais atrasos? São horários específicos e recorrentes ou acúmulo de voos anteriores?
  3. Como se compara o horário prometido com a partida real? As diferenças são mínimas e operacionais ou há uma margem de segurança a trabalhar? Ajustar os horários previstos reduziria atrasos e reclamações?
  4. Quais dias, quinzenas ou meses são picos no ano? Como esses períodos agravam os picos de horário?
  5. Quais as principais reclamações, classificadas por gravidade, e as mais recorrentes? Algumas companhias concentram problemas recorrentes? Ranking das companhias com reclamações mais preocupantes e mais recorrentes. É cultura da empresa ou não há correlação estatística?
  6. Companhias específicas têm problemas recorrentes em aeroportos específicos? O aeroporto gera recorrência entre companhias, ou a companhia leva a reclamação de aeroporto em aeroporto?
- **Achado de método (registro):** a reclamação traz o "Código Classificador ANAC" (Portaria 764/SAS, alterada pela Portaria 9.128/SAS de 12/09/2022). O campo Local traz o aeroporto (código IATA) quando o problema ocorreu nele; quando foi no site, aplicativo, telefone, loja ou agência, traz uma letra. O aeroporto da Pergunta 6 vem desse campo, e não da UF do consumidor (que é onde ele mora). O código de assunto (Anexo II) dá o tema da reclamação; parte dos códigos é estimada pela ANAC ou por modelo de IA dela.
- **Sobreposição de períodos:** voos de set/2024 a ago/2026; reclamações de 2024 e 2025. Cruzamentos entre voos e reclamações usam set/2024 a dez/2025 (16 meses).

### Definições de método (aprovadas pelo Fabian em 10/10/2026, itens A a G)

- **A. Atraso:** partida mais de 30 min após o previsto (classe oficial ANAC); faixas 30-60, 60-120, 120-240 e >240 min para gravidade. Medida principal na partida; chegada como complemento.
- **B. Escopo:** voos domésticos regulares (tipo N) com horário previsto.
- **C. Denominadores:** atraso = atrasados ÷ realizados; cancelamento = cancelados ÷ previstos; reclamações por 10 mil voos.
- **D. Aeroporto do voo:** origem para partida, destino para chegada.
- **E. Companhia × aeroporto:** modelo que separa o efeito de cada um comparando companhias dentro do mesmo aeroporto e o mesmo aeroporto entre companhias.
- **F. Gravidade das reclamações** pelo tema do Anexo II (alta: preterição, falta de alternativa ou assistência, bagagem extraviada ou violada, PNAE; média: atraso, alteração pela empresa, embarque, bagagem avariada, reembolso; baixa: compra, tarifa, alteração pelo passageiro, opcionais, fidelidade, outros), ponderada pelo desfecho (procedência, resolução, nota).
- **G. Recorrência:** tema acima da média do mercado na mesma companhia (ou companhia × aeroporto) mês após mês; "cultura" testada pela estabilidade do perfil de temas no tempo e entre aeroportos.

### Regra nova de processo (Fabian, 10/10/2026)

- Depois de receber as perguntas, sempre sugerir melhorias para aprovação. As aprovadas passam a valer como perguntas principais; em seguida, sugerir perguntas complementares que se relacionem com as principais. Registrada para a próxima versão da skill.

## Etapa 1. Conhecer e validar os dados

- **Carga:** `scripts/carga.py` grava as tabelas voos, reclamacoes e rec_codigos no SQLite (caminho em ANAC_SQLITE). `scripts/validar_dados.py` gera `resultados/validacao_dados.csv`; resumo em `RESUMO_DADOS.md`.
- **Correção registrada:** na mensagem anterior ao Fabian, os 160 mil voos "realizados sem horário real" foram uma leitura errada. Todo voo realizado tem horário real. O que falta em 181.860 registros é o horário *previsto*: são voos não programados (extras, traslados, retornos, testes), fora do escopo por não serem promessa ao passageiro.
- **Achados de método:** horários em horário de Brasília (verificado); partida = saída do pátio; a base não informa a antecedência do cancelamento; tabela ICAO->IATA montada pelo analista (cobre 99,2% dos voos e 99,9% das citações domésticas).
- **Revisão do Fabian (10/10/2026):** Etapa 1 aprovada (implícita na aprovação das perguntas).

### Melhorias e perguntas complementares (aprovadas pelo Fabian em 10/10/2026)

Todas aprovadas; passam a valer como parte das perguntas principais.
- **M1 (P1):** medir também os minutos de atraso acumulados (onde se concentra o atraso total), não só a taxa.
- **M2 (P2):** testar o efeito bola de neve (manhã atrasada piora a tarde na mesma companhia e aeroporto?) e separar o primeiro voo do dia.
- **M3 (P3):** separar a folga no horário de partida da folga no tempo de voo previsto, por rota; simular a pontualidade com horários ajustados ao realizado.
- **M4 (P4):** marcar feriados e férias escolares; separar o efeito de mais voos do efeito de cada voo atrasar mais.
- **M5 (P5):** incluir o desfecho da reclamação: resolução, nota, tempo de resposta e procedência admitida pela companhia.
- **M6 (P6):** separar problema crônico (meses seguidos acima do mercado) de pico pontual.
- **C1:** reclamações a mais por ponto percentual de atraso (companhia × aeroporto × mês); cancelar custa mais que atrasar?
- **C2:** recuperação de atraso no ar, por companhia e rota. **Ênfase do Fabian: analisar as companhias que mais fazem isso.**
- **C3:** concentração dos cancelamentos em poucos dias de crise.
- **C4:** as 20 rotas com mais minutos de atraso e mais reclamações (lista de ação).
- **C5:** resolução compensa volume? Companhia que resolve melhor tem nota melhor mesmo com mais reclamações?

## Etapa 2. Análises

### Indicadores padrão
- `scripts/indicadores_padrao.py` -> `resultados/indicadores_padrao.csv` (fonte única para relatório e painel): 1.570.951 voos previstos; atraso de partida > 30 min 7,87%; cancelamento 1,96%; atraso mediano dos voos atrasados 51 min; 8,8 milhões de minutos de atraso acumulados; 1.099 reclamações de Azul+LATAM+Gol por 10 mil voos no período comum.
- **Minutos de atraso:** soma dos minutos de partida dos voos com atraso > 30 min, cada voo limitado a 24 h.
- **Hora:** hora local do aeroporto de origem (horário de Brasília ajustado pelo fuso; tabela em `base.py`).

### P1 (com M1). Companhias e aeroportos: quem atrasa e cancela, e quanto é de cada um
- **Script:** `q1_companhias_aeroportos.py`. **Método:** modelo aditivo ponderado em células companhia × aeroporto × hora × mês, com divisão de Shapley do que cada fator explica e o modelo refeito em cada ano (set/24-ago/25 e set/25-ago/26) para checar estabilidade. Entram as companhias com pelo menos 5 mil voos e os aeroportos com pelo menos 3 mil partidas (50 aeroportos).
- **Resultados:**
  - Entre Azul, LATAM e Gol, o **aeroporto explica 86% da diferença de atraso** e 80% da de cancelamento que os dois fatores explicam juntos; a companhia explica o resto.
  - Efeito ajustado da companhia, em pontos percentuais de atraso em relação à média do mercado: Gol -1,2 (estável nos dois anos), LATAM -0,1 (passou de -0,8 para +0,5), Azul +0,7.
  - Nas regionais o fator companhia domina: Azul Conecta tem 15,5% de cancelamento e +4,8 pp de atraso; Voepass tem 24% de atraso e só entra no 1º ano.
  - **Concentração (M1):** GRU e CGH somam 27% de todos os minutos de atraso do país, e seis aeroportos somam 50%. GRU tem o maior efeito próprio (+3,7 pp, piorou no 2º ano: de +2,9 para +4,5).
  - O efeito de cada aeroporto é estável entre os anos (correlação 0,76) e pouco ligado ao tamanho ou ao pico de movimento (0,13 a 0,16).
  - Pares companhia × aeroporto persistentemente acima do esperado: LATAM em BEL, Azul em BSB, VIX, GIG e SDU, Gol em FOR (+1,5 a +2,8 pp).
- **Limite:** sem a causa do atraso, o efeito do aeroporto mistura infraestrutura, controle de tráfego, clima e a operação local das companhias.

### P2 (com M2). Fluxo do atraso ao longo do dia
- **Script:** `q2_fluxo_diario.py`.
- **Curva:** a taxa de atraso sobe de 2,5% às 4h para 10,4-11,5% entre 16h e 23h. Do 1º voo do dia da companhia no aeroporto (5,4%) ao 31º em diante (10,3%), a taxa quase dobra. É **acúmulo**.
- **Bola de neve:** regressão da tarde contra a manhã, com margem por 200 reamostragens de dias. Pelo efeito padronizado, o atraso da tarde acompanha mais a manhã da **própria companhia nos outros aeroportos** (+3,5 pp, faixa 0,67-0,93 no coeficiente) e no mesmo aeroporto (+2,2 pp) do que a manhã das outras companhias no mesmo aeroporto (+0,8 pp). O atraso viaja com a operação da companhia (avião e tripulação), mais do que com o aeroporto no dia.
- **Horários recorrentes:** no critério principal (3 pp acima do mercado em 75% dos meses), 2 combinações aeroporto × hora, com 2,3% dos minutos. Com o critério mais frouxo, 14 combinações e 7,2%. A exceção estável é **GRU às 22h-23h** (19% de atraso; LATAM 16-17% depois das 22h em toda a rede).
- **Leitura combinada com a P1:** o aeroporto define o patamar de cada lugar; a variação de cada dia se propaga pela malha da companhia, e essa propagação é alavanca da companhia (folga entre voos, reserva de avião e tripulação, recuperação no meio do dia).
- **Revisão do Fabian (10/10/2026):** P2 aprovada depois do aprofundamento P2b (ver abaixo). P1 aprovada com o pedido de separar o clima, atendido no bloco de clima.

### Revisão do Fabian sobre P1 e P2 (10/10/2026)
- **P1:** pediu para tentar separar o clima, usando uma base de clima por aeroporto e dia. Proposta: METAR (boletim meteorológico do próprio aeroporto, hora a hora) do arquivo público da Iowa State University (IEM), para os 50 aeroportos da P1. Depende do download pelo navegador (os servidores de clima são bloqueados no ambiente de análise). Links em `dados/externos/LINKS_METAR.md`. Download autorizado pelo Fabian em 10/10/2026.
- **P2:** leu que o atraso nasce no aeroporto e acompanha avião e tripulação, e pediu números que comprovem a relação, para saber se agir no aeroporto (no 1º voo) evita a propagação. Feito em `q2b_origem_do_atraso.py`.

### P2b. O atraso nasce em solo ou chega com o avião?
- **Método:** sem número do avião, para cada partida olhamos as chegadas da mesma companhia no mesmo aeroporto previstas entre 180 e 35 min antes. "Giro comprometido" = a chegada real não deixou 35 min para sair no horário. Só Azul, LATAM e Gol.
- **Relação principal:** com as chegadas no horário, a partida atrasa 2,6%; sem chegada antes (avião de pernoite) atrasa 4,8%; com parte das chegadas comprometidas, 14,1%; com a maioria comprometida, **29,1%** (11 vezes mais).
- **Composição dos atrasos:** 24% sem nenhuma chegada comprometida (nascidos em solo), 23% com a maioria comprometida (herdados), 53% mistos. A divisão é sensível ao critério (solo de 24% a 39%; herdado de 12% a 41%); a relação de probabilidade não muda.
- **Onde nasce o atraso em solo:** GRU e CGH concentram 27% dos atrasos nascidos em solo; seis aeroportos, 49%. Em BPS e UDI mais da metade dos atrasos nasce em solo.
- **Hipótese do Fabian (1º voo):** a 1ª onda (aviões de pernoite, antes das 10h) é 7,3% dos voos e atrasa 3,1%. Na regressão por companhia-dia, controlando o choque do dia (as outras companhias), se a 1ª onda fosse 100% pontual o atraso do resto do dia cairia 0,9 ponto (12% do atraso do resto do dia; faixa de 9% a 15%). O choque do dia, comum a todas as companhias (clima e controle de tráfego, provavelmente), pesa mais (coeficiente 0,74).
- **Leitura:** a 1ª onda importa, mas a maior parte do atraso se forma nos giros ao longo do dia. A alavanca maior é proteger o giro (tempo de solo e reserva) nos aeroportos que mais geram atraso.

### P3 (com M3 e C2). Horário prometido x realizado; folga; recuperação no ar
- **Script:** `q3_folga_horarios.py`.
- **Partida:** mediana de -2 min; 38% saem 5 min ou mais antes do previsto (a partida registrada é a saída do pátio). LATAM é a mais "no horário" (mediana 0, 29% antecipadas); Azul e Gol, mediana -3.
- **Folga no tempo de voo (M3):** pequena. Média ponderada de 3,1 min (Azul), 4,1 (LATAM) e 5,6 (Gol), entre 3% e 6% da duração do voo. Rotas sem folga: Azul 11%, Gol 5%, LATAM 2%.
- **Recuperação no ar (C2, ênfase do Fabian):** entre os voos que saem com mais de 15 min de atraso, chegam dentro de 15 min do previsto 25,7% na Gol, 22,8% na LATAM e 14,2% na Azul. Saldo líquido de atrasos > 30 min (partida - chegada): Gol evita 775, LATAM 194, Azul tem 322 a mais na chegada que na partida. A recuperação acompanha a folga da rota (correlação 0,68 entre rotas).
- **Voos cronicamente atrasados:** quase não existem: 3 de 8.068 combinações voo × origem × hora no critério de 50% das operações. Mesmo com o critério de 20%, mover esses horários para a mediana realizada evitaria só 2,9% dos atrasos. O atraso é espalhado, não concentrado em voos específicos.
- **Simulação do tempo de voo previsto:** fixar a duração prevista no percentil 85 da real reduz a chegada com atraso > 30 min de 7,7% para 6,6% (-14%), com +4 min por voo em média; no percentil 50 piora para 9,2%.
- **Efeito em reclamações:** depende de C1 (reclamações por ponto de atraso), feita junto com P5/P6.
- **Revisão do Fabian (10/10/2026):** aprovada ("P2 e P3 aprovados").

### Revisão do Fabian (10/10/2026)
- P2 (com aprofundamento) e P3 aprovadas.
- Download do clima (METAR) autorizado; feito pelo Chrome em 4 arquivos semestrais. O Fabian move os arquivos para `dados/externos/`.
- **Pedido novo:** com o clima, revisitar P2 e P3 medindo o impacto do clima e avaliar uma **folga dinâmica** (tempo previsto ajustado conforme a previsão do tempo), se fizer sentido.

### P4 (com M4 e C3). Sazonalidade
- **Script:** `q4_sazonalidade.py`. Feriados nacionais e Carnaval com a véspera e o dia seguinte; férias de verão (15/dez a 10/fev) e de julho; carga do dia = voos previstos ÷ média do mesmo dia da semana no mês.
- **Meses:** dezembro é o pior (13,9% de atraso e 3,2% de cancelamento), seguido de novembro (9,8%), fevereiro (8,4%) e outubro (8,2%). Os melhores são maio (6,0%) e março (6,1%). Quinzena pior: 1ª de dez/2025 (21,4%), depois 1ª de nov/2024 (15,0%) e 1ª de dez/2024 (12,7%).
- **Volume x taxa (M4):** o número de voos por dia varia pouco entre os meses (cerca de ±4%). Quase todo o atraso a mais dos meses ruins vem de cada voo atrasar mais: em dezembro, +129 atrasos por dia pela taxa contra +3 pelo volume. **Dentro do mês, porém, o dia mais carregado pesa:** +10% de voos no dia sobe o atraso em 2,8 pontos (faixa de 2,0 a 3,7) e o cancelamento em 0,8.
- **Dia da semana:** quinta (9,1%) e sexta (9,7%) são os piores; sábado e domingo, os melhores (6,5% a 6,7%).
- **Feriados e férias:** feriados têm menos voos e menos atraso (5,1%). Férias de julho: -1,4 ponto, já descontada a carga. Férias de verão: +1,1 ponto; coincidem com a estação de temporais no Sudeste, por isso a separação depende do clima.
- **Picos do ano x picos do dia:** nos dias de pico (os 10% mais cheios e feriados), a manhã não muda e o fim da tarde e a noite pioram de 1,2 a 2,2 pontos (17h-21h). O pico do ano amplia o acúmulo do dia.
- **Dias de crise (C3):** os cancelamentos são pouco concentrados. Os 20 piores dias somam 11,6% (12,9% só nas três grandes) e o dia mediano tem 33. Os dois piores dias, 10 e 11/dez/2025 (452 e 332 cancelamentos, atraso de 47% a 51%), concentraram-se em CGH, GRU e SDU: evento regional, provavelmente meteorológico, a confirmar com o METAR.
- **Revisão do Fabian (10/10/2026):** aprovada ("P2 e P3 aprovados").
- **Download do clima (refeito):** os 4 links semestrais não geraram arquivo. Refeito mês a mês pelo navegador (24 pedidos, nenhum erro) e unido em `metar_aeroportos_2024-09_2026-08.csv` (44,6 MB). Detalhe em `dados/externos/LINKS_METAR.md`.

## Bloco de clima (pedido do Fabian; P1, P2, P3 e P4 revisitadas)
- **Dados:** METAR de 48 dos 50 aeroportos da P1 (faltam SBVC e SBSI no arquivo do IEM), 844.604 boletins. `scripts/clima.py` classifica cada aeroporto × hora: severo (trovoada no aeródromo, chuva forte, visibilidade < 1,6 km, teto < 500 pés, rajada ≥ 35 kt), moderado (trovoada nas proximidades, chuva, nevoeiro, visibilidade 1,6-4,8 km, teto 500-999 pés, rajada 25-34 kt) ou normal. Horas: 88,1% normais, 8,2% moderadas, 3,7% severas. 95,7% dos voos têm dado de clima na origem. Análises em `scripts/q_clima.py`; o modelo da P1 virou módulo (`q1_modelo.py`).
- **Impacto:** com tempo severo na origem (na hora da partida ou na anterior), o atraso vai de 7,0% para 17,4% e o cancelamento de 1,6% para 4,5%. Com tempo moderado, o atraso fica em 9,9%. Tempo severo no destino eleva o atraso de chegada para 16,0%. 28% dos voos operam com tempo moderado ou severo na origem ou no destino e concentram 38% dos atrasos. **Atrasos a mais ligados ao clima** (comparados com a taxa de tempo normal do mesmo aeroporto e hora): **13,6% do total**.
- **Sensibilidade dos aeroportos ao tempo severo:** SDU +16,4 pontos, CGH +15,1, GRU +14,7, VCP +12,3, GIG +11,0; CWB só +2,0, apesar de ter tempo severo em 15% das horas.
- **P1 sem clima:** refeita só com voos em tempo normal na origem e no destino. Entre as três grandes, o aeroporto continua explicando a maior parte (79%; a companhia, 21%). Os efeitos de aeroporto quase não mudam (correlação 0,91). GRU continua o pior em tempo normal (+3,2 pontos); CGH cai de +1,5 para +0,9 (parte do problema de CGH é clima). Efeitos das companhias iguais (Gol -1,1; LATAM -0,1; Azul +0,8).
- **P2 com clima:** as horas de tempo severo nos 10 maiores aeroportos explicam 15% da variação diária do atraso das três grandes. Dias sem hora severa: 5,2% de atraso; com 16 a 40 horas severas: 10,4%. O restante do "choque do dia" não é clima de aeródromo (controle de tráfego, sistemas, operação).
- **P4 com clima:** dezembro não é explicado pelo clima. Tem menos horas severas que janeiro (4,9% contra 5,6%) e, só com tempo normal, ainda atrasa 11,6% (contra 5,4%-7,1% nos outros meses). O pico de dezembro é operacional (provavelmente aviões mais cheios e mais bagagem, que a base não mede). Dias de crise: 10/dez/2025 teve 10 horas severas em CGH e GRU (evento meteorológico); 11/dez quase não teve (dia de recuperação); 30/set/2025 (203 cancelamentos, concentrados em SDU e CGH) não teve tempo severo: crise não meteorológica.
- **Folga dinâmica (P3), regras aprendidas no 1º ano e testadas no 2º:**
  - Folga uniforme rende cerca de 3 atrasos evitados por 1.000 minutos de folga.
  - Folga sazonal planejada (por aeroporto × mês × faixa horária) rende 4,4.
  - Folga no dia, aplicada só com tempo ruim, rende 4,6.
  - As duas juntas: 2,35 min por voo levam o atraso do 2º ano de 8,0% para 7,0% (-12,6%), mais do que uma folga uniforme de 3 min (7,1%) com menos minutos.
  - É uma simulação simples: não inclui o ganho de propagação nem o custo de usar menos o avião.
- **Revisão do Fabian (10/10/2026):** aprovada ("Aprovado P4").
- **Revisão do Fabian (10/10/2026):** P4 e bloco de clima aprovados.

### P5 (com M5 e C5). Reclamações: gravidade, recorrência, ranking e "cultura"
- **Script:** `q5_reclamacoes.py`. Taxas por 10 mil voos no período comum (set/24-dez/25), sobre os voos regulares (domésticos e internacionais) de cada companhia. Os voos da Azul Conecta entram no denominador da Azul, porque as reclamações saem com a marca Azul. **Os rankings são separados:** as estrangeiras fazem voos longos com aviões maiores, então "por voo" não é comparável com as brasileiras.
- **Principais temas:** alteração pedida pelo passageiro (20%, gravidade baixa), alternativas quando a empresa altera ou cancela o voo (15%, alta), oferta e compra (12%), reembolso (12%), bagagem avariada (7%). Temas com pior nota e menor resolução: bagagem extraviada (nota 2,6; 46% resolvidas), assistência no atraso (2,7; 46%), bagagem "outros" (2,8), execução do voo/atraso (2,9; 52%).
- **Ranking das brasileiras** (graves não resolvidas por 10 mil voos):
  - Voepass: 295 (43% graves, 8% de resolução).
  - **Azul: 104.** 1.175 reclamações e 443 graves por 10 mil voos; 38% graves.
  - Gol: 59 (782 reclamações e 233 graves por 10 mil voos).
  - LATAM: 33 (1.025 e 137; só 13% graves).
  - A resolução é parecida nas três grandes (75%-76%), e a nota também (3,8-3,9). LATAM responde mais rápido (mediana de 2 dias contra 7).
- **Recorrências** (acima de 1,2 vez o mercado em 75% dos meses ou mais):
  - Azul: preterição/overbooking 2,3×, alternativas na alteração pela empresa 1,7× e bagagem extraviada 1,7× (as três graves), mais alteração pelo passageiro e alteração pela empresa "outros".
  - Gol: assistência material no atraso 1,8× (grave) e check-in/embarque 1,6×.
  - LATAM: aviso de alteração 2,3×, oferta e compra 2,0×, reembolso e alteração "outros"; nenhuma grave.
- **"Cultura" (padrão próprio):** sim, há relação estatística forte. Pelo perfil de temas de um mês, um classificador acerta a companhia em 82% dos casos, contra 7% ao acaso (permutação, p = 0,005). Meses da mesma companhia se parecem bem mais entre si (correlação 0,77) do que com os de outras (0,31). O perfil de 2024 se repete em 2025 (0,89 a 0,97). **Cuidado:** o código de tema é preenchido pela própria companhia, então parte do padrão pode ser o jeito de classificar. A recorrência medida por voo não depende disso.
- **C5:** a nota é quase só o desfecho: resolvida tem nota 4,6, não resolvida 1,3; correlação entre resolução e nota de 0,99 entre companhias e entre meses. O volume por voo quase não pesa na nota (-0,24 entre companhias, -0,07 entre meses). **Resolver compensa o volume na nota**, mas não reduz a quantidade.
- **Cuidado adicional:** a "procedência admitida" é a visão da companhia e varia por política (0% a 100% entre estrangeiras). Não serve para comparar companhias.
- **Revisão do Fabian (10/10/2026):** aprovado junto com a P4.
- **Revisão do Fabian (10/10/2026):** P5 aprovada.

### P6 (com M6), C1 e C4. Companhia × aeroporto nas reclamações; atraso → reclamação; rotas críticas
- **Script:** `q6_companhia_aeroporto.py`. Reclamações das três grandes com aeroporto informado no código classificador (operação doméstica; 99,9% traduzidas para ICAO), período comum. Denominador: movimentos (partidas + chegadas previstas) da companhia no aeroporto; voos da Azul Conecta somados à Azul. Pares com pelo menos 1.000 movimentos em aeroportos com 6.000 ou mais.
- **Quem explica o volume x a gravidade (modelo aditivo, Shapley):**
  - Volume total de reclamações: o aeroporto explica 76% e a companhia 24%.
  - Reclamações graves: a companhia explica 59%.
  - Por tema: assistência no atraso, companhia 83%; overbooking, companhia 75%; bagagem extraviada, companhia 60%; bagagem avariada, aeroporto 62%.
- **Perfil de temas:** em 46 de 47 pares (98%), o perfil da companhia num aeroporto se parece mais com o da própria companhia nos outros aeroportos (correlação média 0,93) do que com o das outras companhias no mesmo aeroporto (0,55). **A companhia leva o tipo de problema de aeroporto em aeroporto; o aeroporto pesa no volume.** Aeroporto com mais reclamações por movimento entre os grandes: CNF (1,7 vez a média; duas das três companhias acima do esperado).
- **M6 (crônico x pontual), pares acima do esperado pelo modelo:**
  - 5 crônicos (75% dos meses ou mais): LATAM em CNF (317 por 10 mil movimentos contra 180 esperados; 244 reclamações a mais), Azul em GIG e FLN, Gol em VCP, e mais um.
  - 23 frequentes (50%-75% dos meses): Gol CNF; Azul SSA, FOR, BSB, VIX, NAT, IGU; LATAM CWB, JOI, BEL; entre outros.
  - 34 picos pontuais; 49 dentro do esperado.
- **C1 (mesmo par ao longo dos meses, efeitos fixos de par e mês, margem por reamostragem de pares):**
  - +1 ponto de atraso > 30 min traz +3,4 reclamações operacionais por 10 mil movimentos (+4,7%; faixa 2,5-4,5).
  - +1 ponto de cancelamento traz +4,5 (+6,2%; faixa 2,9-6,2).
  - Sobre todas as reclamações com aeroporto: +3,4% por ponto de atraso e +5,9% por ponto de cancelamento.
  - **Cancelar custa cerca de 1,3 a 1,7 vez mais reclamações que atrasar, por ponto.** Vale só para as reclamações com aeroporto (31% do total).
- **C4 (rotas críticas):** índice = minutos de atraso + 180 min por cancelamento (premissa). As 20 piores rotas (de 768 com 500 ou mais voos) somam 13,6% do impacto, e as 100 piores, 41%. Topo: a ponte aérea CGH-SDU nas três companhias (cancelamento de 3,7% a 4,5%), rotas do hub da Azul em CNF e VCP, LATAM GRU-POA (14,3% de atraso).
- **Revisão do Fabian (10/10/2026):** aprovada.
- **Revisão do Fabian (10/10/2026):** P6, C1 e C4 aprovadas. Pulamos as sugestões A, B, C da IA, porque as complementares já cobriram o necessário.

## Etapa 4. Soluções e metas
- **Rascunho:** `SOLUCOES_METAS.md`; números de apoio em `scripts/q7_apoio_metas.py`.
- **Oito soluções, da mais barata para a mais cara**, cada uma com quem controla a alavanca. S8 (GRU e resiliência a tempo ruim) não é da companhia.
- **Metas só com apoio:** simulação testada fora da amostra (folga), referências observadas entre as três grandes (recuperação no ar, resolução por tema) e a taxa do mercado (recorrências).
- **Em aberto, com a razão escrita:** cancelamento da ponte aérea, dezembro e GRU.
- **Achados novos usados nas metas:**
  - Resolução por tema: Gol resolve 37% da bagagem extraviada (LATAM 65%), 50% da avariada (LATAM 87%) e 56% da assistência no atraso (LATAM 88%).
  - Na ponte aérea, o cancelamento é 2,4 vezes o do resto da rede, com atraso menor.
  - Dezembro é o pior mês nas três companhias (12,8% a 14,3%).
- **Revisão do Fabian (10/10/2026):** aprovadas.

### Motivos de cancelamento na ponte aérea (pergunta do Fabian, 10/10/2026)
- **Pesquisa de fontes:**
  - **A justificativa não é pública hoje.** A ANAC deixou de publicar a justificativa no VRA quando revogou a IAC 1504 (2020) e trocou a fonte do VRA. Os aeroportos coordenados (CGH, SDU) recebem justificativas para o controle de uso de slots, mas não as publicam. Reportagem da Folha (2023) mostrou que 35% dos cancelamentos da ponte tinham justificativas diferentes em cada ponta, sem rotina de checagem.
  - **Regra nova** (notícia de ago/2026): as companhias passam a informar no SRV a causa certificada de cada atraso e cancelamento, em categorias padronizadas (clima, infraestrutura, controle de tráfego, obstrução de pista, greves de terceiros, embarque e PNAE). Alimenta o INFOVOO (ANAC/CNJ); não está claro se será aberto.
  - **Não há regra fixa** do tipo "atraso acima de X min vira cancelamento". O que empurra o atraso para o cancelamento: o fechamento de CGH e SDU às 23h (exceção após as 23h só em contingência, analisada caso a caso), os limites de jornada da tripulação, o direito do passageiro a reacomodação ou reembolso com atraso acima de 4 horas (Res. 400) e o índice mínimo de uso de slots (cancelamento por clima não conta contra a companhia).
  - **Fonte possível para percentuais:** os arquivos do VRA anteriores a 2020 trazem o código de justificativa. A verificar no download.
- **Estimativa com os nossos dados** (`q8_ponte_aerea.py`; prioridade evento > tempo > fim do dia):
  - Dos 2.784 cancelamentos da ponte (três grandes), 9% caíram em dias de evento no aeroporto (dia com 25% ou mais dos voos cancelados: 30/set/2025, vazamento de óleo na pista do SDU; 10/dez/2025, vendaval em SP), 38% com tempo ruim, 1% depois das 21h e **51% sem sinal observável**.
  - A ponte cancela mais em todas as condições. Com tempo ruim: 4,8% contra 2,1% no resto da rede. **Sem sinal nenhum: 2,8% contra 1,1%** (2,5 vezes).
  - **83% dos cancelamentos da ponte são em par ida e volta** (mesma companhia, sentidos opostos, até 3 horas), contra 52% no resto da rede: sinal de decisão de rotação do avião (recuperar a malha ou consolidar voos), o que é fácil numa rota com saídas a cada 30 a 60 min.
  - Por companhia, parte sem sinal observável: Gol 57%, LATAM 51%, Azul 27% (na Azul, 49% com tempo ruim).
- **Leitura:** clima e eventos explicam cerca de metade. A outra metade tem a assinatura de decisão da companhia, sem como separar manutenção, tripulação e comercial. A C1 mostrou que cancelar custa mais reclamações que atrasar.

### Decisão do Fabian (10/10/2026): baixar o VRA 2019 (com justificativa) e cruzar com a Folhapress
- **Regra combinada:** se os percentuais de 2019 coincidirem estatisticamente com os da Folhapress, usar os dois para estimar os motivos atuais, deixando claro como foi feito. Se não coincidirem, usar só 2019 e declarar que é um dado defasado, usado para melhorar a identificação dos motivos.
- **Downloads** (pelo navegador, 10/10/2026):
  - `vra2019_justificados.csv`: 340.932 voos de 2019 com código de justificativa, entre cancelamentos e atrasos justificados.
  - `vra2019_contagem_rotas.csv`: contagem de voos por companhia × tipo × origem × destino × situação, para as taxas.
  - `metar_aeroportos_2019.csv`: METAR de 2019 dos mesmos 50 aeroportos, para calibrar o sinal de clima.
  - Tabela de códigos: `dados/externos/iac1504_codigos_cancelamento.csv` (IAC 1504, Anexo 2).
- **Achado sobre a Folhapress:** a reportagem (mar/2024, dados de 2023) **não publica a distribuição dos cancelamentos por motivo**. Traz só que 35% dos cancelamentos da ponte tiveram justificativas diferentes em CGH e SDU, que 13% afetavam o índice de regularidade e que a portaria tem 14 categorias e 150 códigos. Um teste estatístico de coincidência de percentuais por motivo não é possível. O 35% entra como medida de confiabilidade das justificativas autodeclaradas. Pela regra combinada, usa-se só 2019, declarado como defasado.
- **Checagem externa possível:** o Metrópoles publicou cancelamento de 1,85% em jan-jul/2019 (dados ANAC), para conferir com o arquivo baixado.

### Motivos de cancelamento: VRA 2019 e calibração (`q9_motivos_cancelamento_2019.py`)
- **Checagem:** o cancelamento de 2019 no arquivo baixado (1,85%, todas as companhias) bate com o publicado pelo Metrópoles (1,85% em jan-jul/2019). 99,9% dos cancelamentos têm código.
- **Folhapress:** não publica percentuais por motivo, então o teste de coincidência não é possível. **Usado só 2019**, declarado como dado defasado e autodeclarado, que serve para melhorar a identificação dos motivos.
- **Motivos declarados em 2019** (Azul, LATAM, Gol; voos domésticos):
  - Ponte aérea (979 cancelamentos): clima 68% (destino abaixo dos mínimos 33%, origem 27%, retorno 7%), técnico-operacional 26%, aeroporto fechado 6%, programado 0,4%.
  - Resto da rede: clima 55%, técnico 39%, aeroporto fechado 5%, programado 2%.
- **Comparabilidade:** a ponte de 2019 já cancelava mais que a rede (2,9% contra 1,3%) e também em pares ida e volta (87%). Hoje: 3,7%, 1,5% e 83%. A estrutura se parece; a taxa da ponte subiu 0,8 ponto.
- **Calibração com o METAR de 2019** (mesmos sinais de hoje), motivo declarado em 2019 conforme o sinal:
  - Cancelamento "sem sinal observável": técnico-operacional em 68% dos casos na rede (65% na ponte) e clima em 27% (32%).
  - Cancelamento "com tempo ruim": clima em 69% (81% na ponte).
- **Estimativa para a ponte de 2024-26** (tabela de 2019 aplicada à distribuição de sinais de hoje): clima 47% a 56%, técnico-operacional da companhia 39% a 47%, aeroporto fechado 4% a 5%, programado/comercial 1% a 2%. A faixa vem das duas tabelas de calibração (rede ou só ponte). A margem por reamostragem é estreita (±1 ponto) e não inclui a incerteza do próprio código.
- **Confiabilidade do código:** 33% dos cancelamentos declarados como clima em 2019 tinham tempo normal no METAR da origem e do destino. Ordem de grandeza parecida com os 35% de justificativas divergentes da Folhapress (2023), embora sejam medidas diferentes: o METAR do aeródromo não capta tudo, como restrição do controle de tráfego ou tempo na rota.
- **Meta da ponte** em `SOLUCOES_METAS.md`: atualizada com esse apoio, mas mantida como proposta.
- **Revisão do Fabian (10/10/2026):** soluções, metas e estimativa dos motivos da ponte aprovadas.

## Etapa 5. Relatório e painel
- **Gráficos:** `scripts/graficos.py` gera g1 a g12 em `resultados/graficos/`, só a partir dos CSVs de resultados.
- **Relatório:** `RELATORIO.md` e `RELATORIO.pdf` (15 páginas). PDF gerado do Markdown via HTML + Chromium (mesmo padrão do estudo Olist).
  - Estrutura: cabeçalho, sumário executivo com cinco conclusões e a decisão recomendada, seções 1 a 5, Método, Anexo A (dicionário de indicadores) e Anexo B (referência de scripts e arquivos).
  - A estimativa dos motivos da ponte está na seção 2.7, com os limites escritos.
- **Painel:** `index.html`, montado por `painel_dados.py` + `painel_montar.py` sobre `scripts/painel_modelo.html`.
  - Filtros: período, companhia e aeroporto de origem. Cartões marcados "Responde aos filtros" ou "Fixo".
  - Gráficos em SVG próprio, sem biblioteca externa. Bloco "Como ler os números".
  - **Diferença declarada:** o painel usa a média do atraso dos atrasados, não a mediana. Nas reclamações por aeroporto, considera só o primeiro local citado. Os dois pontos estão explicados no próprio painel.
  - Testado no navegador sem erros de script (só a fonte externa não carrega no ambiente de teste).
- **Revisão do Fabian (10/10/2026):** soluções e metas aprovadas, com a estimativa dos motivos da ponte aérea.
- **Revisão do Fabian (14/10/2026):** leu o relatório e o painel e pediu a revisão crítica (Etapa 7).

## Etapa 7. Revisão crítica, camada 1: analista sênior do setor aéreo
- **Checagem externa feita durante a revisão:** o ranking Cirium 2025 (chegada até 15 min do horário, voos realizados) dá Azul 85,18% e Gol 87,75%. Pela nossa base, em 2025 (voos domésticos e internacionais regulares), a chegada até 15 min dá Azul 85,7% e Gol 88,5%: diferença de até 0,7 ponto, validação externa da base. **Achado:** pelo critério de 15 min a ordem é Gol 88,5% > Azul 85,7% > LATAM 83,3%. No de 30 min, Azul e LATAM empatam (8,2% e 8,1%). A LATAM tem mais atrasos pequenos (15-30 min: 9,9% das partidas). O relatório só usa o corte de 30 min.
- **Nota proposta: 8,0/10.** Pontos fortes, fracos e melhorias priorizadas apresentados ao Fabian (14/10/2026).
- **Revisão do Fabian (14/10/2026):** leu o relatório e o painel e pediu a revisão crítica (Etapa 7).
- **Revisão do Fabian (14/10/2026):** aprovou as melhorias A a E, com o download dos dados de passageiros e ocupação. Sobre F (custo): não aprofundar, mas mencionar uma estimativa de referência onde o relatório fala dos minutos de atraso e da folga ("se o avião parado tem custo, o atraso também tem").

### Melhorias da revisão (`scripts/q10_revisao_senior.py`)
- **A. Critério de 15 minutos:**
  - Validação externa: chegada até 15 min em 2025 dá Azul 85,7% e Gol 88,5%, contra 85,18% e 87,75% na Cirium (diferença de 0,5 e 0,7 ponto). A LATAM no Brasil fica em 83,3%; a Cirium só publica o grupo LATAM.
  - Modelo refeito com atraso > 15 min: o aeroporto continua explicando a maior parte (87% na partida, 82% na chegada).
  - Efeitos das companhias com corte de 15 min: Gol -1,8 (partida) e -2,2 (chegada); LATAM +1,3; Azul -0,2 e +0,1. **A Gol é a melhor em qualquer critério. Azul e LATAM trocam de lugar conforme o corte:** a LATAM tem mais atrasos pequenos (15 a 30 min), a Azul mais atrasos grandes.
- **C. Cancelamento planejado x no dia:** só 1,5% dos cancelamentos das três grandes aparecem como o mesmo voo cancelado 3 ou mais dias seguidos (9% com o critério de 2 dias; 0% com 5 ou mais). Ajustes de malha feitos com antecedência saem da programação antes, sem aparecer como cancelamento. **Os cancelamentos do VRA são praticamente todos operacionais, de curto prazo.** Ponte aérea: 0,8% planejados.
- **D. Dimensionamento dos pilotos** (poder de 80%, significância de 5%, autocorrelação diária considerada):
  - Folga em CGH+VCP contra GRU+CNF+GIG: em 90 dias detecta efeito de 2,9 pontos ou mais; em 180 dias, 2,1. A meta é cerca de 1 ponto, então **90 dias não bastam com esse desenho.** Sugestão: alternar semanas com e sem folga no mesmo aeroporto (desenho cruzado) e usar mais aeroportos.
  - Proteção do giro na tarde de GRU contra a tarde de CGH: detecta 7,4 pontos em 90 dias.
  - Resolução de bagagem extraviada da Gol medida pelo consumidor.gov.br: só cerca de 17 casos avaliados por grupo em 90 dias (detecta 46 pontos). **Inviável com dado público; o piloto deve ser medido com os registros internos da companhia** (todos os casos de bagagem, não só os que viram reclamação pública).
- **E. Sensibilidade da recorrência:** o núcleo se mantém até no critério de 1,5 vez o mercado em 75% dos meses: Azul (overbooking, alternativas na alteração de voo, bagagem extraviada), LATAM (aviso de alteração, oferta e compra), Gol (assistência no atraso). Os demais temas recorrentes dependem do critério.
- **Monitoramento de slots (ANAC):** verificado como possível fonte de motivos de cancelamento atuais em CGH e SDU. O arquivo traz horários coordenados e realizados, mas **não traz justificativa**; não serve para esse fim.
- **B. Passageiros, ocupação e bagagem** (`scripts/q11_passageiros.py`; ANAC, Dados Estatísticos do Transporte Aéreo, recorte 2024-2026 baixado pelo navegador por faixa de bytes do arquivo de 360 MB, que é ordenado por ano: `dados/externos/dados_estatisticos_2024_2026.csv`):
  - **Reclamações por 10 mil passageiros** (set/24-dez/25): Azul 11,6 (4,4 graves), LATAM 6,6 (0,9), Gol 5,5 (1,6). Por passageiro, a Azul tem 4,9 vezes mais graves que a LATAM, porque voa aviões menores (106 passageiros por voo, contra 158 na LATAM e 144 na Gol). Entre as estrangeiras, agora comparáveis, a pior é a Avianca (25,5).
  - **Hipótese de dezembro:**
    - A ocupação **não** explica o pico. Dezembro tem 84,4%, abaixo de novembro (86,0%) e de julho (85,4%), e julho atrasa só 6,6%. Coeficiente de +0,16 ponto de atraso por ponto de ocupação, com faixa que cruza o zero.
    - A bagagem por passageiro anda junto em parte: +1 kg por passageiro acompanha +1,5 ponto de atraso (faixa de 0,5 a 2,6; painel companhia × mês com efeito fixo de companhia). Dezembro tem 7,8 kg por passageiro, mas janeiro tem 8,1 kg e atrasa menos.
    - Conclusão: a maior parte do pico de dezembro continua sem explicação nos dados. O relatório foi corrigido, porque dizia "provavelmente aviões mais cheios e mais bagagem".
- **F. Custo:** referência da Airlines for America (US$ 98,41 por minuto de operação em 2025: tripulação 37, combustível 29, manutenção 18, aeronave 10) mencionada nas seções 2.1 e 2.3, com a ressalva de que não se transfere para o Brasil.
- **Relatório e painel atualizados** com A a F. PDF regenerado.
- **Nota revisada da camada 1: 9,0/10** (antes 8,0).
- **Revisão do Fabian (14/10/2026):** camada 1 aprovada ("Aprovado pode seguir para a segunda camada").

## Etapa 7. Revisão crítica, camada 2: analista de dados sênior, projeto inteiro (14/10/2026)
- **Reprodução do zero:** banco novo (`ANAC_SQLITE` em outro caminho), sem caches, os 20 passos de `rodar_tudo.py` rodados em trechos (cerca de 15 minutos no total). Nenhum erro. Os 90 CSVs de resultados saíram idênticos aos anteriores, com duas exceções esperadas:
  - `qc_p4_dias_de_crise_horas_severas.csv` perdeu uma coluna vazia removida antes;
  - a cobertura ICAO->IATA foi de 99,22% para 99,47%, porque RRJ entrou na tabela depois da primeira validação. Texto atualizado no relatório e no RESUMO_DADOS.
- **Conferência automática do relatório (`scripts/conferir_relatorio.py`, novo, último passo do `rodar_tudo.py`):** 80 números do texto conferidos contra os CSVs. A primeira rodada achou 10 diferenças, todas corrigidas:
  - 3 arredondamentos digitados à mão (Azul Conecta 15,6% e não 15,5%; LATAM 22,9% e não 22,8%; Azul/LATAM graves por passageiro 5,0 vezes e não 4,9, que vinha da divisão de números já arredondados);
  - a cobertura ICAO->IATA desatualizada;
  - 6 números de reclamações por voo que só apareciam no gráfico (entrou uma tabela na seção 2.5).
  - Resultado final: **80 de 80**.
- **Achado de conteúdo:** RRJ (Jacarepaguá) tinha efeito de aeroporto maior que o de GRU (+4,3), mas só a Azul Conecta opera lá, e o modelo não separa aeroporto de companhia nesse caso. A frase "GRU tem o pior efeito próprio" foi corrigida para "entre os aeroportos com mais de uma companhia".
- **Pasta:**
  - novos `README.md` (conclusões, dados, como reproduzir, autoria) e `requirements.txt` (pandas 2.3.3, numpy 2.2.6, matplotlib 3.10.9; Python 3.10);
  - `.gitignore` passou a excluir os CSVs grandes de `dados/externos` (118 MB); fica só a tabela de códigos IAC 1504;
  - `SOLUCOES_METAS.md` marcado como rascunho aprovado, com remissão à versão final no relatório.
- **Diário:** nenhuma entrada "(pendente)"; todas as revisões registradas com data.
- **Premissas não verificadas (declaradas no relatório ou no diário):**
  - tabela ICAO->IATA e fusos por aeroporto montados pelo analista (cobertura verificada; correção item a item, não);
  - escala de gravidade própria (definição F, aprovada);
  - limites operacionais escolhidos: giro mínimo de 35 min, evento no aeroporto com 25% de cancelamentos, 180 min por cancelamento no índice de rotas;
  - código de tema e procedência preenchidos pelas companhias.
- **Limites remanescentes:** os efeitos de companhia da P1 não têm margem por reamostragem (a estabilidade entre os dois anos faz esse papel); `q1_companhias_aeroportos.py` mantém uma cópia das funções que foram para `q1_modelo.py` (sem efeito nos resultados).
- **Nota do projeto: 9,0/10** (antes dos ajustes, 8,0).

## 14/10/2026 — Dimensionamento dos pilotos reescrito

- **Pedido:** descrever melhor por que e como cada piloto é feito.
- **Erro encontrado:** a fórmula do menor efeito detectável multiplicava por raiz de 2 uma série que já era a diferença entre os grupos. Os valores antigos (2,9 e 7,4 pontos em 90 dias) estavam superestimados; os corretos são 2,1 e 5,2.
- **Erro encontrado:** a recomendação de alternar semanas com e sem folga foi testada com dados reais e é o desenho menos sensível (6,9 pontos em 90 dias), porque o clima varia muito de uma semana para outra.
- **Decisão:** folga e tempo em solo passam a sortear metade dos números de voo nos mesmos aeroportos e dias (0,8 e 2,3 pontos em 90 dias). Atendimento: 46 casos por grupo para +28 pontos e 377 para +10, medidos nos registros internos.
- **Formato:** cada piloto ganhou objetivo, efeito esperado, como, medida e fonte, prazo, regra de decisão e cuidados. Ressalva registrada: avião compartilhado entre grupos dilui o efeito medido (resultado conservador).
- **Conferência:** 85 de 85 números.


## 14/10/2026 — Relatório reescrito para leitura de gestão

- **Pedido:** simplificar o relatório inteiro para gerência e diretoria, deixando claro o que, por que e como, completo mas sucinto.
- **Estrutura nova:** sumário executivo com cada achado ligado a uma ação; diagnóstico com o mesmo formato em cada tema (o que os dados mostram, por que importa, o que fazer); soluções; pilotos; metas e rotina; limites. Os detalhes estatísticos (correlações, testes, calibração da ponte, validação Cirium, RRJ, cálculo do dimensionamento) foram para o Anexo A, sem perder nenhum.
- **Linguagem:** termos técnicos saíram do corpo e foram para o dicionário (ponto percentual, correlação, menor efeito detectável).
- **Conferência:** 85 de 85 números; PDF com 16 páginas (antes 18). Referências de seção ajustadas no README, no SOLUCOES_METAS e no painel.

## 14/10/2026 — Painel reorganizado e revisão crítica, camada 1 (2ª rodada)

- **Painel:** mesma estrutura do relatório (00 resumo a 09 como ler), cada tema com "o que mostra / por que importa / o que fazer". Visual de painel de partidas aprovado pelo Fabian (topo azul-marinho, números em âmbar, situação contra a rede, códigos IATA em etiquetas). Entraram clima por aeroporto, chegadas anteriores, posição no dia, recuperação, folga, dia da semana, ponte aérea, resolução por tema, combinações crônicas, as três grandes lado a lado, decisão pedida, variação contra o ano anterior e limites. Gráficos com fonte em tamanho real (largura do contêiner) e dicas ao passar o mouse; cores validadas para daltonismo.
- **Revisão (analista do setor), principais correções aceitas:**
  - A ponte não se distingue pela proporção sem causa externa visível (parecida com a rede), e sim pela taxa (2,8% contra 1,1%).
  - A solução 2 deixou de ser "preferir atrasar a cancelar": na ponte, cancelar em par é ferramenta legítima; a alavanca é reserva de avião e tripulação e manutenção; na rede, decidir pesando quantos voos o cancelamento protege (Res. 400 a partir de 4 horas).
  - "Sem causa externa visível" é o teto do controlável, não o valor garantido.
  - Propagação descrita como associação (base sem matrícula); alavancas do setor acrescentadas.
  - Dezembro por ano e com tempo bom (q12a): 10,7% (2024) e 11,2% (2025, sem o vendaval), contra 6,3%; voos extras não explicam (q12b).
  - Economia da folga: 0,43 minuto de atraso evitado por minuto de folga; ponto de equilíbrio de 2,3 vezes.
  - Meta da Azul ajustada ao mix de etapas: 21% a 24% (q12c). "Recuperação no ar" virou "recuperação no trecho".
  - Pilotos: folga sorteada na publicação da malha (slots e Res. 400); atendimento sorteado por caso, com FCR e custo por caso; tempo em solo com equipe extra dedicada (sortear dias daria 6,3 pontos de menor efeito); teto do efeito de 6,6 pontos (q12d); decisão por intervalo de confiança e ponto de equilíbrio.
  - Gol em Viracopos (3,2 vezes o esperado) e Azul em Teresina incluídas; termos do setor (preterição, calço, A15/D15, Res. 400, FCR, NPS); contexto de Chapter 11 e motores GTF; limites corrigidos (a resolução e a nota são do consumidor).
- **Conferência:** 98 de 98 números.

## 14/10/2026 — Revisão crítica, camada 2 (analista de dados, projeto inteiro), 2ª rodada

- **Nota da revisão:** 8,0 antes das correções.
- **Corrigido:**
  - Dezembro com uma só definição de tempo bom (tempo normal na origem): 12,1% nos dois dezembros juntos, 10,7% e 11,2% por ano, contra 6,3%. O gráfico do mês usa origem e destino (11,6%), o que está declarado no Anexo A.
  - Meta dos temas recorrentes recalculada só com os sete temas da tabela: cerca de 4,7 mil reclamações a menos por ano na Azul, 4,2 mil na LATAM e 0,6 mil na Gol (antes 8 mil e 5,4 mil, que incluíam temas de 1,2 a 1,5 vez o mercado).
  - Folga: premissas declaradas (a folga do dia supõe previsão perfeita; o atraso é medido contra o horário novo). O ponto de equilíbrio de 2,3 vezes saiu, porque comparava um minuto real com um minuto nominal; a conta de custo fica para o piloto. "45%" virou "de 25% a 45%, conforme a quantidade de folga".
  - Piloto 3: "teto" virou "efeito máximo, se toda a associação for causal"; taxa da tarde de GRU corrigida para 11,7%.
  - Anexo A: o que significa "o aeroporto explica 86%" (parte do que os dois explicam juntos; o modelo vai de 27% para 34%), ressalvas do menor efeito detectável e lista dos scripts do painel no Anexo C.
  - `dados/FONTES.md` com endereço, filtro e destino de cada arquivo; `vra2019_contagem_rotas.csv` passa a ir no repositório.
  - README, RESUMO_DADOS e aviso do SOLUCOES_METAS atualizados.
  - `conferir_relatorio.py`: textos procurados com contexto (folga por companhia, estratégias de folga, taxa da tarde de GRU), novas checagens de metas, pilotos, razão 1,3/1,7 e GRU com tempo bom. Resultado: 107 de 107.
  - `q12_revisao_camada1.py` avisa com mensagem clara se faltar o cache do q2b.
  - PDF regerado a partir do texto atual.
- **Fica registrado, sem mudança:** `q1_companhias_aeroportos.py` tem uma versão própria das funções do modelo (assinatura diferente da de `q1_modelo.py`); unificar exigiria rodar a P1 inteira de novo, sem efeito nos resultados.

## 14/10/2026 — Painel (texto saindo do layout) e terceira rodada das duas camadas

- **Pedido do Fabian:** corrigir os textos que saíam das caixas no painel e rodar de novo as duas camadas para melhorar a qualidade dos dados. A nota da camada 2 tinha caído de 9,0 para 8,0 porque a rodada anterior pegou o PDF desatualizado e misturas de definição criadas pelas mudanças; não era piora dos dados.
- **Painel:** selos de situação com largura flexível; selos vazios escondidos; decisão pedida logo abaixo do topo; mediana do atraso por filtro (histograma de minutos); temas com "% do total" e sem "Sem código"; quadro "Se a sua companhia é..."; gráfico de folga com minutos por voo e a dose igual.
- **Camada 1 (nota 8,0 / 7,5 antes), aplicado:**
  - Dezembro: "pior mês nos dois anos" era falso para 2024 (novembro empatou); agora "o fim de ano é o pior período", com 10,9% sem o vendaval contra 6,3%. Achado novo da camada 2: o pico vai de 1 a 23/12 e cai para 8% na semana do Natal (q12e).
  - Ponte: "resto da rede das três grandes"; a taxa de 2,8% é condicional (voos sem tempo ruim, sem incidente, antes das 21h); prêmio de cerca de 430 cancelamentos por ano no melhor caso e meta de 1,9% em 12 meses (q12f).
  - Título do achado 4 refeito: um cancelamento gera só 1,3 a 1,7 vez as reclamações de um atraso.
  - Solução 2 dividida em 2a (cruzar com o registro do CCO, já) e 2b (reserva, se confirmado).
  - Piloto 1: sorteio por rotação, medida em hora real e partida seguinte; efeito esperado em CGH e VCP de 1,4 ponto (qc_folga_local_cgh_vcp); menor efeito por companhia de 1,2 a 1,6 (90 dias) e 0,8 a 1,1 (180 dias), então 180 dias com leitura aos 90. Piloto 3: sem mudar horário, aditivo de contrato de solo, 180 dias (2,1 a 2,2 pontos por companhia). Piloto 2: número de casos refeito com a taxa interna de FCR.
  - Folga: manchete com a mesma quantidade de minutos (cerca de 25%). "86%" explicado no sumário. Bases das reclamações declaradas.
- **Camada 2 (nota 8,8 antes), aplicado:**
  - 126 erros de data excluídos das taxas e dos minutos em base.py (minutos 8,8 → 8,7 milhões; 1º voo do dia 5,4% → 5,3%; voos crônicos 2,9% → 2,8%); toda a cadeia dependente rodada de novo.
  - q1_modelo e q1_companhias contam só valores válidos nas células (efeito da exclusão).
  - Cache refeito também quando base.py ou q2b mudam; conferir_relatorio para a rodada (saída 1) se algum número não bater.
  - 48 de 50 aeroportos com METAR declarados; denominadores com voos internacionais declarados; erros, duplicidades e reclamações sem código no RESUMO_DADOS.
- **Conferência:** 115 de 115 números.

## 14/10/2026 — Rodada de confirmação das duas camadas (4ª rodada)

- **Notas:** camada 1, relatório 8,5 e painel 8,5 (antes 8,0 e 7,5); camada 2, 9,4 (antes 8,8). A camada 2 recalculou de novo, direto no banco, os números novos (minutos sem erros de data, 1º voo do dia, dezembro, semana do Natal, prêmio da ponte, menor efeito por companhia) e todos bateram; PDF confirmado na versão atual.
- **Aplicado:** piloto 1 com a medida principal definida (partida seguinte do mesmo avião com atraso > 30 min, dimensionada com dados internos) e o 1,4 / 0,8 a 1,1 declarados como medida secundária; meta de 7,0% declarada "contra o horário novo", com meta em hora real após o piloto; "8,0% (2º ano)"; o 25% com a mesma quantidade de folga também no corpo e na solução 4; justificativa do sorteio por número de voo no piloto 3; "quase o dobro" virou "cerca de 70% a mais"; Anexo A com quatro rodadas; painel com aviso de base pequena (menos de 100 reclamações), período efetivo das reclamações e sem "—%".
- **Método:** q12a e q12e sem os erros de data (resultados iguais); menor efeito por companhia pela mediana de 20 sorteios (resultados iguais na primeira casa); posição no dia conta só voos válidos.
- **Aceito sem mudança:** a ordem dentro da mesma hora, na posição do voo no dia, usa o número do voo (a base em cache não guarda o minuto previsto); a taxa do 1º voo não muda (5,33% contra 5,34% na checagem da revisão).
- **Conferência:** 115 de 115.

## 14/10/2026 — Pacote para manter as notas acima de 9 (aprovado pelo Fabian)

- **Relatório:** seção 3 virou um quadro de uma página por piloto (objetivo, como, medida principal, prazo, decisão); o detalhe foi para o novo Anexo D, sem perder nenhum número. Siglas explicadas na primeira vez (FCR, NPS, D15/A15, DECEA). PDF com 18 páginas (corpo de 12; anexos de 6), contra 20 antes.
- **Identidade visual do PDF:** os 12 gráficos refeitos com as cores do painel (azul-marinho, âmbar, vermelho de alerta, cinza da rede e as cores fixas das companhias), títulos em azul-marinho, códigos de aeroporto em fonte mono; o gráfico dos minutos por aeroporto perdeu o segundo eixo; títulos desatualizados corrigidos (folga, dezembro). O PDF abre com um quadro de números no estilo do painel de partidas, lido do próprio sumário.
- **Painel:** celular com quadro compacto (3 números), sem o parágrafo do topo e com a barra de filtros sem ficar presa; "Ver dados" com a tabela de cada gráfico (11 gráficos).
- **Projeto:** `metodos.py` reúne as contas sensíveis (menor efeito detectável, casos por grupo, erros de data, formato dos números), usadas por base.py, q10, q12 e conferir; `testes.py` testa essas contas e abre o `rodar_tudo.py`. Posição do voo no dia ordenada pelo minuto previsto (o cache passou a guardar o minuto). LICENSE (MIT para código e textos; dados pelos termos das fontes). Resumo em inglês no README. Checagem do que vai para o GitHub: 158 arquivos, 5,6 MB, nenhum acima de 20 MB, nenhum e-mail pessoal.
- **Resultados:** sem mudança de número; conferência 115 de 115; testes 8 de 8.

## 14/10/2026 — 5ª rodada das duas camadas e correções

- **Notas da rodada:** camada 1, relatório 8,8 e painel 8,9; camada 2, 9,4.
- **Aplicado (camada 1):**
  - "86%" sempre com a ressalva de que a maior parte da variação vem da hora, do dia e do mês.
  - Frase "a meta de 7,0% equivale a 5% menos reclamações" trocada (a meta é contra o horário novo): cada ponto de atraso real evitado reduz cerca de 4,7% as reclamações operacionais.
  - Pilotos: a leitura aos 90 dias serve só para parar se não houver sinal ou houver dano; "antes de começar" (dimensionar com as rotações internas; se a menor melhora passar de 1,4, incluir GRU ou estender o prazo); slot compatível na origem e no destino; custo comercial da alteração programada nos riscos; linha do Anexo D renomeada para "base do desenho".
  - Nota da legenda do gráfico de dezembro (11,6% no gráfico, 10,9% no texto); saldo de recuperação em percentual no corpo e absolutos no Anexo A; curva do dia descrita sem exagero.
  - Gráficos do PDF com letra maior (figuras de 6,4 polegadas e letra de 10 a 12,5 pt) e imagem a 76% da largura; títulos e eixos encurtados.
  - Painel: remissão às seções do relatório; celular com o quadro em uma linha (3 números) e a decisão na primeira tela; selo "na média" e "rede x%" só com filtro ativo; nota das bases nos temas; "Ver dados" com título de coluna e base de voos nos gráficos de mês e hora.
- **Aplicado (camada 2):** README sem a frase antiga de dezembro e com pilotos "de 90 a 180 dias"; resolução da LATAM em bagagem extraviada 64% (64,48; o CSV passou a guardar 2 casas para não arredondar duas vezes); cache refeito também quando metodos.py muda; RESUMO_DADOS item 5 corrigido; aviso do SOLUCOES com os prazos; conferência com a razão da ponte (2,4 vezes) e as taxas calculadas direto no banco.
- **Conferência:** 117 de 117; testes 8 de 8. PDF com 19 páginas (corpo de 12 a 13; anexos de 6).

## 14/10/2026 — 6ª rodada das duas camadas e correções

- **Notas:** camada 1, relatório 9,0 e painel 8,9; camada 2, 9,6.
- **Aplicado:**
  - Piloto 1 passa a testar só a folga sazonal (solução 4; efeito esperado 1,1 ponto em CGH e VCP). A reserva dos dias de tempo ruim (solução 5) sai do piloto, porque o CCO a usaria também nas rotações de comparação, e é avaliada à parte, sorteando os dias com previsão de tempo ruim em que é acionada. O passo "antes de começar" compara a menor melhora e o efeito esperado da mesma medida (a principal), ambos com as rotações internas.
  - Piloto 3 com "equipe e recursos dedicados, sem tirar a vez dos outros voos" e o grupo de comparação acompanhado contra o próprio histórico.
  - Metas com dono e etapa de 12 meses (metade do caminho, como na ponte), no relatório e no painel.
  - Base da resolução "do mercado" declarada (inclui estrangeiras); "86%" com "da variação que se consegue explicar"; linguagem de associação na ligação atraso → reclamações; "os dois piores episódios" (vendaval de 10 e 11/12).
  - Painel: saldo de recuperação em percentual; etiqueta da seção do relatório em cada seção; "Ver dados" com legenda e fonte; "meses fora do fim de ano".
  - Gráficos: rótulo do g6 em duas linhas, título do g4 ("a maioria das chegadas anteriores"), legenda do g7 com "tempo bom". README alinhado nas duas línguas; aviso do SOLUCOES sobre números refinados.
- **Conferência:** 118 de 118; testes 8 de 8.

## 7ª rodada das duas camadas e correções

- Notas: relatório 9,2, painel 9,0, projeto 9,4 (todas acima de 9 pela primeira vez).
- Poder do piloto 1 escrito como mínimo por voo; por rotação o mínimo é maior e será recalculado com os dados internos. "Antes de começar" usa "menor melhora detectável" e Confins (não GRU) como reforço, para não sobrepor o piloto 3.
- Piloto 3: 2,1 a 2,2 pontos vale para LATAM ou Gol; na Azul, 5,7.
- Linguagem de associação no achado 4, na 1.6 e no Anexo A ("se associa a", "acompanha").
- Solução 7 com data de decisão (início de novembro; sem tempo de contratação, dez/2026 vira linha de base e o plano roda em dez/2027). Meta da ponte amarrada à decisão da 2b.
- Curitiba: o tempo severo lá é quase todo nevoeiro e teto baixo (+0); com trovoada ou chuva forte, +9, contra +21 em GRU e +25 em Congonhas. Nova saída `qc_impacto_clima_tipo_aeroporto.csv`; solução 8 e painel ajustados; 4 checagens novas no conferir.
- `q_clima.py` passa a excluir os 126 erros de data, como as outras análises. Efeitos: folga sazonal 4,4 → 4,5 atrasos evitados por 1.000 min; folga combinada 2,35 → 2,31 min por voo; 0,43 → 0,44 minuto evitado por minuto de folga. Efeito esperado do piloto 1 (1,1) e números do clima sem mudança.
- README: ressalva do 86% e "ligados ao clima" na versão em português. Histórico de revisões atualizado para sete rodadas.
- Conferência 122/122; testes 8/8.

## 8ª rodada das duas camadas e correções

- Notas: relatório 9,3, painel 9,1, projeto 9,3. É a segunda rodada seguida com tudo acima de 9.
- Números da folga propagados em todos os trechos depois da exclusão dos erros de data:
  - 4,5 atrasos evitados por 1.000 min;
  - 3,8 contra 3,0 com a mesma quantidade (quase 30% a mais);
  - 0,44 minuto;
  - vantagem com pouca folga de cerca de 50%.
- O conferir ganhou uma lista de valores antigos que não podem sobrar (131 checagens).
- Achado 1 reescrito: "da parte que se consegue explicar, hora e mês pesam mais".
- Solução 7: o que se aprova até o início de novembro é a medição de dez/2026 como linha de base, mais o orçamento e a contratação para dez/2027. Reforço opcional com a equipe atual, em bases sorteadas, já em dez/2026. A meta de dezembro foi ajustada a isso.
- A 2a tem resultado em 60 dias, e a 2b é decidida em seguida.
- O "esperado 1,1" do piloto 1 foi identificado como medido contra o horário publicado.
- Azul 5,7 incluída no Anexo A e no Anexo D.
- Vendaval de 10 a 12/12 explicado: os dois dias mais o dia de recuperação.
- "Sai mais barato" trocado por "tende a gerar menos reclamações".

## Publicação (14/10/2026)

- Fabian aprovou o relatório e o painel depois da 8ª rodada.
- Repositório público Fabi3105/diagnostico-atrasos-aviacao, com GitHub Pages a partir de main (raiz). Painel em https://fabi3105.github.io/diagnostico-atrasos-aviacao/.
- About preenchido com site e tópicos (airline, anac, aviation, brazil, customer-experience, dashboard, data-analysis, portfolio, python).
- Painel e links do relatório (PDF e texto) conferidos no ar.
- Ajuste posterior no README: frase do achado 1 alinhada com o relatório.
