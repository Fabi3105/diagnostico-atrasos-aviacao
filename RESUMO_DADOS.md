# Resumo dos dados

Validação completa em `resultados/validacao_dados.csv` (gerada por `scripts/validar_dados.py`). Todas as checagens passaram.

## Fontes

| Base | Origem | Período | Linhas |
|---|---|---|---|
| Voo Regular Ativo (VRA) | ANAC, sistemas.anac.gov.br | set/2024 a ago/2026 (24 arquivos mensais) | 2.016.781 voos |
| Reclamações do setor aéreo no consumidor.gov.br | ANAC (dados do consumidor.gov.br com o Código Classificador ANAC) | jan/2024 a dez/2025 | 193.935 reclamações |
| Dados Estatísticos do Transporte Aéreo | ANAC (passageiros, assentos, bagagem por companhia, rota e mês) | 2024 a 2026 | usados para normalizar por passageiro e testar ocupação e bagagem |
| VRA de 2019 com código de justificativa | ANAC | 2019 | usado só para estimar os motivos de cancelamento da ponte aérea |
| METAR (boletins meteorológicos) | Iowa Environmental Mesonet | 2019 e set/2024 a ago/2026; 50 aeroportos pedidos, 48 com dados (SBVC e SBSI sem boletim, 0,4% dos voos) | usado para separar o efeito do clima |

Endereços e filtros de cada arquivo: `dados/FONTES.md`.

Os dois conjuntos se sobrepõem de set/2024 a dez/2025 (16 meses). É o período usado sempre que voos e reclamações são cruzados.

## O que entra na análise de voos (definição B)

- **1.580.343 voos domésticos regulares com horário previsto**, sendo 1.548.607 realizados e 31.736 cancelados. Entre 60,2 mil e 70,0 mil voos por mês, sem mês faltando.
- Azul (35,5%), LATAM (33,4%) e Gol (28,1%) fazem 97,0% desses voos. Os demais são Azul Conecta (2,0%), Voepass (0,4%), SID (0,3%), ABJ (0,2%), MAP (0,1%) e outras regionais.
- **Ficam fora:** voos internacionais, cargueiros e charters. Ficam fora também 57.247 registros sem horário previsto, todos realizados e 87% com número de voo de prefixo Z, tratados como voos não programados (extras, traslados, retornos ao pátio e testes).
- **Correção de 21/11/2026:** a versão anterior contava 181.860 registros sem horário previsto e dizia que todos eram voos não programados. Isso estava errado: 124.613 deles tinham horário previsto com fração de segundo (`.100000000`), que a carga não lia. Desses, 9.392 são voos domésticos regulares do período e agora estão no escopo.

## Indicadores gerais do escopo

| Indicador | Valor |
|---|---|
| Partida com mais de 30 min de atraso | 7,9% |
| Chegada com mais de 30 min de atraso | 7,9% |
| Partida antes do horário previsto | 56,1% |
| Cancelamento (cancelados ÷ previstos) | 2,0% |

## Cuidados com os dados

1. **Causa do atraso não existe na base.** O campo de justificativa está vazio desde 2020, quando a IAC 1504 foi revogada. Clima, controle de tráfego, manutenção e falhas da própria companhia não podem ser separados.
2. **Horários em horário de Brasília.** As durações previstas de GRU para MAO e de MAO para GRU são iguais, e Congonhas aparece operando das 6h às 22h. Para analisar por hora do relógio local, aeroportos de outro fuso são ajustados pelo estado.
3. **Partida = saída do pátio** (retirada do calço), não a decolagem.
4. **Cancelamento sem antecedência.** A base não informa se o voo foi cancelado com dias de aviso ou na hora. Um cancelamento de malha comunicado com antecedência pesa igual a um cancelamento no portão.
5. **Valores extremos:** 15 atrasos acima de 24 horas e 150 partidas mais de 2 horas antes do previsto. A maior parte é erro de data (129 voos com a partida prevista registrada em outro dia), que fica fora das taxas e dos minutos; os demais continuam nas taxas e pesam pouco nas medianas.
6. **Aeroportos:** o VRA usa código ICAO (SBGR) e as reclamações usam IATA (GRU). A tabela de tradução foi montada pelo analista e cobre 99,40% dos voos e 99,9% das citações domésticas (`scripts/base.py`).

## Reclamações

- **Volume:** 90.595 em 2024 e 103.340 em 2025. Azul, LATAM e Gol respondem por 81,8%; o restante são companhias estrangeiras.
- **Classificação:** 98% trazem o Código Classificador ANAC (Portaria 9.128/SAS), que informa:
  - **Local:** aeroporto em código IATA, ou o canal (site, aplicativo, telefone, loja, agência). 30,7% das reclamações citam um aeroporto.
  - **Tipo de operação:** doméstica ou internacional.
  - **Assunto:** um ou mais códigos de tema (Anexo II).
  - **Avaliação da própria companhia:** 38% procedente, 21% parcialmente procedente, 23% improcedente, 18% não informou.
- **Gravidade (definição F, pelo pior tema da reclamação):** alta 27,6%, média 33,3%, baixa 39,1%.
- **Avaliação do consumidor:** 49% não deram nota, e 27 mil reclamações ainda não estavam finalizadas na data do arquivo. Entram no volume, mas não na taxa de resolução.
- **Limitação:** a reclamação não informa o número do voo. A ligação com os voos é feita por companhia × aeroporto × mês.

## Qualidade dos dados (revisão de 14/10/2026)

- **Erros de data no VRA:** 129 voos (0,008%) têm a partida prevista registrada em outro dia, com atraso perto de um múltiplo de 24 horas (ex.: AZU 2612, CNF–PVH, em nov/2024). Ficam fora das taxas de atraso e dos minutos (`base.voos_escopo`, coluna `erro_data`). Com isso, os minutos de atraso passam de 8,86 para 8,79 milhões; nenhuma taxa muda na primeira casa decimal.
- **Voos duplicados** (empresa, número e partida prevista): 6, desprezível.
- **Reclamações:** 1.163 linhas (0,6%) são iguais em todos os campos menos o protocolo e foram mantidas; 3.952 (2%) não têm Código Classificador e ficam fora das análises por tema.
- **Denominadores:** reclamações por 10 mil voos e o A15 de 2025 usam os voos domésticos e internacionais regulares da companhia, porque as reclamações incluem voos internacionais.
- **Reprodução independente:** 22 números centrais foram recalculados direto no banco, sem os scripts do projeto; todos bateram depois de declarados os denominadores.
