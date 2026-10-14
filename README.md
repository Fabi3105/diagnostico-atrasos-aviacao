# Atrasos, cancelamentos e reclamações na aviação doméstica: onde uma companhia aérea deve agir (ANAC, 2024-2026)

Estudo independente de dados abertos da ANAC, do ponto de vista de uma companhia aérea. Responde a três perguntas: onde o atraso e o cancelamento se formam, quanto deles a companhia controla e como eles viram reclamação.

- **Relatório:** [RELATORIO.pdf](RELATORIO.pdf) (versão em texto: [RELATORIO.md](RELATORIO.md))
- **Painel interativo:** [fabi3105.github.io/diagnostico-atrasos-aviacao](https://fabi3105.github.io/diagnostico-atrasos-aviacao/) (arquivo: [index.html](index.html))
- **Decisões e revisões, com data:** [DIARIO_DECISOES.md](DIARIO_DECISOES.md)
- **Perspectiva e alavancas:** [BRIEFING_NEGOCIO.md](BRIEFING_NEGOCIO.md) · **Dados e validação:** [RESUMO_DADOS.md](RESUMO_DADOS.md)

## Principais conclusões

1. **O atraso nasce em poucos aeroportos e se espalha pela malha da própria companhia.** Da parte do atraso que se consegue explicar, hora e mês pesam mais; da diferença entre Azul, LATAM e Gol, 86% vem do aeroporto, não da companhia. GRU e Congonhas concentram 27% dos minutos de atraso do país.
2. **Os horários têm pouca folga; com a mesma quantidade de minutos, a folga direcionada evita quase 30% mais atrasos do que a folga igual para todos.** Testado fora da amostra: regra aprendida no 1º ano e aplicada no 2º.
3. **Cerca de 14% dos atrasos estão ligados ao clima.** O fim de ano (1 a 23 de dezembro) é o pior período mesmo com tempo bom.
4. **A ponte aérea cancela 2,4 vezes mais que o resto da rede das três grandes**, e cerca de 39% a 47% dos cancelamentos estimados têm motivo técnico-operacional.
5. **Nas reclamações, a nota depende quase só da resolução, e cada companhia repete os próprios problemas.**

O relatório termina com oito soluções ordenadas por custo e três pilotos (de 90 a 180 dias) dimensionados para dar resultado conclusivo.

## Dados

| Base | Fonte | Período |
|---|---|---|
| Voo Regular Ativo (VRA) | ANAC, sistemas.anac.gov.br/dadosabertos | set/2024 a ago/2026 (24 arquivos mensais) |
| Reclamações do consumidor.gov.br com Código Classificador | ANAC, mesma origem | 2024 e 2025 |
| Dados Estatísticos do Transporte Aéreo (passageiros, assentos, bagagem) | ANAC, mesma origem | 2024 a 2026 |
| VRA 2019 (com código de justificativa) | ANAC, mesma origem | 2019 |
| METAR (boletins meteorológicos dos aeroportos) | Iowa Environmental Mesonet, Iowa State University | 2019 e set/2024 a ago/2026 |

Os arquivos de dados não estão no repositório. O endereço de cada um, a pasta onde colocá-lo e os filtros aplicados estão em [dados/FONTES.md](dados/FONTES.md).

## Como reproduzir

```
pip install -r requirements.txt
cd scripts
python rodar_tudo.py            # testes, carga, validação, análises, gráficos, painel e conferência do relatório
python testes.py                # só os testes das contas sensíveis (sem banco)
python rodar_tudo.py 5 9        # retoma do passo 5 ao 8 (a lista está em rodar_tudo.py)
```

O banco SQLite fica em `dados/anac.sqlite`. Em pasta sincronizada ou de rede, defina `ANAC_SQLITE` com um caminho local. A rodada completa leva cerca de 15 minutos. O último passo, `conferir_relatorio.py`, confere cada número-chave do relatório contra as tabelas de `resultados/` e lista os que não batem.

## Estrutura

```
RELATORIO.md / RELATORIO.pdf   relatório para gestão (sumário, diagnóstico, soluções, pilotos, metas, anexos)
index.html                     painel interativo (gerado por scripts/painel_montar.py)
scripts/                       testes, carga, validação, análises (q1 a q12), gráficos, painel e conferência
resultados/                    tabelas (CSV) e gráficos (PNG) de cada análise
dados/FONTES.md                de onde baixar cada arquivo de dados
DIARIO_DECISOES.md             decisões e revisões, com data
```

## Licença

Código e textos sob a licença MIT ([LICENSE](LICENSE)). Os dados seguem os termos das fontes (ANAC e Iowa Environmental Mesonet).

## Summary in English

Independent study of all scheduled domestic flights in Brazil (ANAC open data, Sep/2024 to Aug/2026, 1.57 million flights) and all airline complaints filed on consumidor.gov.br (2024 and 2025), written from the point of view of an airline's operations and customer-service management.

1. **Delay starts at a few airports and spreads through each airline's own network.** Among Azul, LATAM and Gol, the airport accounts for 86% of the delay difference explained by airline and airport; GRU and Congonhas hold 27% of all delay minutes.
2. **Schedules have little buffer, and targeted buffer pays off more.** With the same number of minutes, buffer placed by airport, month and time of day avoids almost 30% more delays than a flat buffer (rule learned on year 1, tested on year 2).
3. **Weather matters, but it is not the main cause.** About 14% of delays are weather-related; the year-end peak (1 to 23 December) persists in good weather.
4. **The São Paulo–Rio shuttle cancels 2.4 times more than the rest of the big three's network**, and an estimated 39% to 47% of its cancellations are technical or operational.
5. **Complaint scores depend almost entirely on resolution, and each airline repeats its own problems.**

The report ends with eight solutions ranked by cost and three pilots sized to give a conclusive answer. The full report and the interactive dashboard are in Portuguese.

## Autoria

Fabian Aliatti Mayer definiu a perspectiva e as perguntas, tomou as decisões de método e revisou cada resultado. A execução técnica teve apoio de inteligência artificial (Claude), como descrito no Anexo A do relatório.
