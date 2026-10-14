# -*- coding: utf-8 -*-
"""Carrega o METAR (Iowa Environmental Mesonet) e classifica cada aeroporto x hora (horário de Brasília) em
tempo normal, moderado ou severo. Grava a tabela clima_hora no SQLite.

Critérios (pior boletim da hora; altura de nuvem em pés, visibilidade em milhas):
- severo: trovoada no aeródromo (TS, TSRA), chuva forte (+RA, +SHRA, +TSRA), visibilidade < 1 mi (1,6 km),
  teto (BKN/OVC/VV) abaixo de 500 ft, ou rajada >= 35 kt;
- moderado: trovoada nas proximidades (VCTS), chuva (RA, SHRA), nevoeiro (FG), visibilidade de 1 a 3 mi
  (1,6 a 4,8 km), teto de 500 a 999 ft, ou rajada de 25 a 34 kt;
- normal: o resto. Horas sem boletim ficam como "sem dado".
Os limites seguem as categorias de voo por instrumentos (IFR/LIFR) e os fenômenos que mais restringem pousos."""
import numpy as np, pandas as pd
from base import RAIZ, con

m = pd.read_csv(RAIZ / "dados" / "externos" / "metar_aeroportos_2024-09_2026-08.csv", dtype=str)
for c in ["vsby", "skyl1", "skyl2", "skyl3", "sknt", "gust"]:
    m[c] = pd.to_numeric(m[c], errors="coerce")
wx = m.wxcodes.fillna("")
teto = pd.Series(np.inf, index=m.index)
for i in (1, 2, 3):
    camada = m[f"skyc{i}"].isin(["BKN", "OVC", "VV"])
    teto = np.where(camada & (m[f"skyl{i}"] < teto), m[f"skyl{i}"], teto)
m["teto_ft"] = teto
ts_local = wx.str.contains(r"(?<!VC)TS", regex=True)
forte = wx.str.contains(r"\+(?:TS)?(?:SH)?RA", regex=True)
sev = ts_local | forte | (m.vsby < 1) | (m.teto_ft < 500) | (m.gust >= 35)
mod = wx.str.contains("VCTS") | wx.str.contains(r"(?:^|\s)-?(?:SH)?RA") | wx.str.contains(r"(?:^|\s)FG") | \
      m.vsby.between(1, 3, inclusive="left") | ((m.teto_ft >= 500) & (m.teto_ft < 1000)) | m.gust.between(25, 34.9)
m["nivel"] = np.select([sev, mod], [2, 1], 0)
m["trovoada"] = (ts_local | wx.str.contains("VCTS")).astype(int)
m["chuva_forte"] = forte.astype(int)
m["baixa_visib_teto"] = ((m.vsby < 3) | (m.teto_ft < 1000)).astype(int)
t = pd.to_datetime(m.valid)
m["data"] = t.dt.strftime("%Y-%m-%d"); m["hora"] = t.dt.hour
h = m.groupby(["station", "data", "hora"]).agg(nivel=("nivel", "max"), trovoada=("trovoada", "max"),
                                               chuva_forte=("chuva_forte", "max"), baixa_visib_teto=("baixa_visib_teto", "max"),
                                               boletins=("nivel", "size")).reset_index()
h["categoria"] = h.nivel.map({0: "normal", 1: "moderado", 2: "severo"})
with con() as c:
    h.to_sql("clima_hora", c, if_exists="replace", index=False)
    c.execute("CREATE INDEX icl ON clima_hora(station, data, hora)")
print(len(m), "boletins;", len(h), "aeroporto-horas;", h.station.nunique(), "aeroportos")
print(h.categoria.value_counts(normalize=True).round(3).to_dict())
print(h.groupby("station").nivel.apply(lambda s: (s == 2).mean()).sort_values().round(3).tail(8).to_dict())
