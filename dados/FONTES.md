# Fontes dos dados e como reproduzir os arquivos

Os arquivos de dados não vão para o repositório (tamanho e termos de uso). Esta é a lista do que baixar, de onde e com que filtro, para refazer o estudo do zero.

## ANAC, portal de dados abertos (https://sistemas.anac.gov.br/dadosabertos/)

| Arquivo esperado | Onde está no portal | Filtro aplicado | Usado por |
|---|---|---|---|
| `dados/brutos/VRA_AAAAM.csv` (24 arquivos, set/2024 a ago/2026) | Voos e operações aéreas > Voo Regular Ativo (VRA), um arquivo por mês | Nenhum; arquivo mensal como publicado | `carga.py` |
| `dados/brutos/dadosconsumidor2024.csv` e `dadosconsumidor2025.csv` | Reclamações do consumidor.gov.br com o Código Classificador ANAC, um arquivo por ano | Nenhum | `carga.py` |
| `dados/externos/dados_estatisticos_2024_2026.csv` | Voos e operações aéreas > Dados Estatísticos do Transporte Aéreo (arquivo único, cerca de 360 MB, ordenado por ano) | Só as linhas de 2024 em diante (no estudo, baixadas por faixa de bytes a partir do byte 318.000.000 e cortadas na primeira linha completa; filtrar por `ANO >= 2024` dá o mesmo resultado) | `q11_passageiros.py` |
| `dados/externos/vra2019_justificados.csv` | VRA de 2019, 12 arquivos mensais | Linhas com `Código Justificativa` preenchido, todas as colunas originais, separador `;` | `q9_motivos_cancelamento_2019.py` |
| `dados/externos/vra2019_contagem_rotas.csv` | VRA de 2019, 12 arquivos mensais | Contagem de voos por empresa, tipo de linha, origem, destino e situação (colunas `empresa;tipo_linha;origem;destino;situacao;voos`). Este arquivo é pequeno e vai no repositório | `q9_motivos_cancelamento_2019.py` |
| `dados/externos/iac1504_codigos_cancelamento.csv` | IAC 1504, Anexo 2 (https://pergamum.anac.gov.br/pergamum/vinculos/IAC1504.pdf) | Códigos de cancelamento agrupados por motivo; vai no repositório | `q9_motivos_cancelamento_2019.py` |

## Iowa Environmental Mesonet, Iowa State University (METAR)

| Arquivo esperado | Como baixar | Usado por |
|---|---|---|
| `dados/externos/metar_aeroportos_2024-09_2026-08.csv` | Links e campos em `dados/externos/LINKS_METAR.md` (50 aeroportos pedidos, 48 com dados: SBVC e SBSI não devolveram boletim; horário de Brasília, mês a mês e depois unidos) | `clima.py` |
| `dados/externos/metar_aeroportos_2019.csv` | O mesmo pedido de `LINKS_METAR.md`, com `year1=2019&month1=1&day1=1&year2=2020&month2=1&day2=1` | `q9_motivos_cancelamento_2019.py` |

## Ordem

Com os arquivos no lugar: `pip install -r requirements.txt`, depois `cd scripts` e `python rodar_tudo.py`. O banco SQLite é criado em `dados/anac.sqlite` (ou no caminho de `ANAC_SQLITE`).
