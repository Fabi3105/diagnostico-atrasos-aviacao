# Briefing do negócio: quem gerou estes dados (rascunho para aprovação)

Etapa feita **antes** da análise exploratória, como manda o método: entender quem produz os dados, para quê, e quem é o "cliente" do estudo.

## 1. Quem produz os dados

- **ANAC (Agência Nacional de Aviação Civil)**, a reguladora do setor. Não opera voos nem vende passagens: regula, fiscaliza e publica informações para o mercado e o consumidor.
- **Voo Regular Ativo (VRA):** cada etapa de voo regular das companhias aéreas, com horário **previsto** e **realizado** de partida e chegada e a situação (realizado ou cancelado). A ANAC monta o VRA cruzando dois cadastros que as próprias companhias enviam: os voos planejados (Registro de Serviços Aéreos) e os voos realizados (Dados Estatísticos). Atualização mensal; contato: Gerência de Acompanhamento de Mercado (GEAC).
- **Reclamações do consumidor.gov.br contra companhias aéreas:** a ANAC aderiu à plataforma em dez/2016 e, desde o 2º trimestre de 2019, ela é o **único canal eletrônico de reclamação** que a ANAC adota para o setor aéreo. Pela Resolução ANAC nº 400/2016 (art. 39), as companhias são **obrigadas** a estar ativas na plataforma e a responder no prazo. A ANAC acrescenta um **código classificador próprio** (Portaria nº 764/SAS/2019), mais detalhado que a classificação genérica da plataforma. Atualização anual; contato: GTEQ.

## 2. O que a base é e o que não tem

| Item | Situação |
|---|---|
| Cobertura | Base **completa**, não amostra: todos os voos regulares informados e todas as reclamações do setor aéreo no consumidor.gov.br |
| Período baixado | VRA de set/2024 a ago/2026 (24 meses); reclamações de 2024 e 2025 |
| Motivo do atraso | **Não existe mais**: o campo de justificativa deixou de ser exigido em abril de 2020 (revogação da IAC 1504). Não será possível dizer se o atraso foi por clima, tráfego, manutenção ou companhia |
| Passageiros por voo | Não está no VRA baixado (só no conjunto Dados Estatísticos). Para "reclamações por passageiro" será preciso baixar essa base ou usar voos como denominador |
| Faixas oficiais de atraso | A ANAC classifica partida e chegada em: antecipado, pontual, atraso de 30 a 60 min, 60 a 120, 120 a 240 e acima de 240 min |
| Reclamações sem código ANAC | Quando a companhia não informa o código, a ANAC estima o tema ou usa um **modelo de IA** próprio (só tema e subtema). Isso precisa entrar nos cuidados de leitura |
| Custos, receitas, tarifas | Não estão nestas bases |

## 3. Quem é o "cliente" do estudo (decisão do Fabian)

Diferente da Olist, aqui não há uma empresa dona dos dados vendendo serviço. As leituras possíveis:

| Perspectiva | Pergunta central | Quem controla as alavancas |
|---|---|---|
| **Companhia aérea** (gestão de operações) | Onde a pontualidade se perde (rotas, aeroportos, horários, épocas) e quanto isso pesa nas reclamações e na nota do passageiro | A companhia: malha, horários, folga entre voos, atendimento |
| **ANAC / regulador** | Quais companhias, aeroportos e rotas entregam pior serviço ao passageiro, e se as reclamações são bem resolvidas | ANAC: regras, fiscalização, transparência |
| **Passageiro** | Em que voo, horário e companhia o risco de atraso e de problema é menor | O passageiro só escolhe; não muda a operação |

**Decisão do Fabian (10/10/2026): companhia aérea.** O estudo é escrito para a gestão de operações e de atendimento de uma companhia aérea: onde a pontualidade se perde, o que cabe à companhia mudar e quanto isso pesa nas reclamações. Comparações entre companhias servem de referência de mercado (benchmark), não de fiscalização.

## 4. Quem controla cada alavanca (a confirmar)

| Alavanca | Quem controla | Confiança |
|---|---|---|
| Horário programado e folga entre voos (malha) | Companhia aérea | Alta |
| Atendimento e resposta às reclamações | Companhia aérea (obrigada a responder no prazo) | Alta |
| Infraestrutura e capacidade do aeroporto | Operador do aeroporto e governo | Alta |
| Controle de tráfego aéreo | DECEA (Comando da Aeronáutica) | Alta |
| Clima | Ninguém | Alta |
| Causa de cada atraso | **Não observável** nos dados desde 2020 | — |

## 5. Perguntas que fazem sentido, que exigem cuidado e que a base não responde

- **Fazem:** pontualidade e cancelamento por companhia, aeroporto, rota, horário, dia da semana e mês; efeito cascata ao longo do dia; a promessa de horário (o previsto) é realista?; relação entre pontualidade e reclamações; o que o passageiro reclama, se é resolvido, em quanto tempo e com que nota.
- **Com cuidado:** comparar companhias de tamanhos e malhas diferentes (normalizar por voo e por rota); ligar reclamação a voo (não há o número do voo na reclamação, só a companhia, a data e o tema).
- **Não fazem com estas bases:** causa do atraso, custo do atraso, receita, tarifa.

## Fontes

- ANAC, metadados do VRA: https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/voo-regular-ativo-vra/62-voo-regular-ativo-vra
- ANAC, metadados dos dados do consumidor.gov: https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/dados-do-consumidor-gov/52-dados-do-consumidor-gov
- Servidor de dados abertos da ANAC: https://sistemas.anac.gov.br/dadosabertos/
