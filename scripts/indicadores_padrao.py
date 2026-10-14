# -*- coding: utf-8 -*-
"""Indicadores gerais do estudo, fonte única para relatório e painel. Saída: resultados/indicadores_padrao.csv"""
import pandas as pd
from base import ler, salvar, voos_escopo, CRUZ_INI, CRUZ_FIM, GRANDES

v = voos_escopo()
r = v[~v.cancelado]
L = [("voos previstos (escopo)", len(v)), ("voos realizados", len(r)), ("voos cancelados", int(v.cancelado.sum())),
     ("taxa de cancelamento %", 100 * v.cancelado.mean()), ("partidas com atraso > 30 min %", 100 * r.atrasado.mean()),
     ("chegadas com atraso > 30 min %", 100 * r.atrasado_chegada.mean()),
     ("partidas antes do previsto %", 100 * (r.atraso_partida < 0).mean()),
     ("atraso mediano dos voos atrasados (min)", r.loc[r.atrasado == 1, "atraso_partida"].median()),
     ("minutos de atraso acumulados (milhões)", r.minutos_atraso.sum() / 1e6),
     ("participação Azul+LATAM+Gol nos voos %", 100 * v.empresa.isin(GRANDES).mean())]
c = ler(f"SELECT empresa, gravidade, nota, avaliacao FROM reclamacoes WHERE data_abertura >= '{CRUZ_INI}' AND data_abertura < '{CRUZ_FIM}'")
vc = v[(v.mes.astype(str) >= CRUZ_INI[:7]) & (v.mes.astype(str) < CRUZ_FIM[:7])]
L += [("reclamações no período comum (set/2024-dez/2025)", len(c)),
      ("reclamações de Azul+LATAM+Gol por 10 mil voos (período comum)",
       1e4 * c.empresa.isin(GRANDES).sum() / vc.empresa.isin(GRANDES).sum()),
      ("reclamações de gravidade alta %", 100 * (c.gravidade == "alta").mean()),
      ("nota média do consumidor", c.nota.mean())]
out = salvar(pd.DataFrame(L, columns=["indicador", "valor"]).round(2), "indicadores_padrao.csv")
print(out.to_string())
