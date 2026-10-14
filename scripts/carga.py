# -*- coding: utf-8 -*-
"""Carrega os arquivos brutos da ANAC no SQLite.

Tabelas:
- voos: um registro por voo do VRA (set/2024 a ago/2026), com atrasos calculados em minutos.
- reclamacoes: um registro por reclamação (2024 e 2025), com a companhia em código ICAO e a gravidade máxima.
- rec_codigos: uma linha por reclamação x grupo do classificador x código de assunto
  (local, tipo de operação, operador e assunto, Portaria 9.128/SAS, Anexo I)."""
import glob
import numpy as np, pandas as pd
from base import BRUTOS, DB, con, EMPRESA_ICAO, gravidade

def ler_csv(f, **kw):
    return pd.read_csv(f, sep=";", skiprows=1, encoding="utf-8-sig", dtype=str, na_values=["null", "N/A", ""], **kw)

# --- voos
cols = {"ICAO Empresa Aérea": "empresa", "Número Voo": "voo", "Código Autorização (DI)": "di",
        "Código Tipo Linha": "tipo_linha", "ICAO Aeródromo Origem": "origem", "ICAO Aeródromo Destino": "destino",
        "Partida Prevista": "partida_prev", "Partida Real": "partida_real", "Chegada Prevista": "chegada_prev",
        "Chegada Real": "chegada_real", "Situação Voo": "situacao", "Código Justificativa": "justificativa"}
partes = []
for f in sorted(glob.glob(str(BRUTOS / "VRA_*.csv"))):
    d = ler_csv(f).rename(columns=cols)
    d["arquivo"] = f.split("VRA_")[1][:-4]
    partes.append(d)
v = pd.concat(partes, ignore_index=True)
for c in ["partida_prev", "partida_real", "chegada_prev", "chegada_real"]:
    v[c] = pd.to_datetime(v[c], format="%Y-%m-%d %H:%M:%S", errors="coerce")
v["atraso_partida"] = (v.partida_real - v.partida_prev).dt.total_seconds() / 60
v["atraso_chegada"] = (v.chegada_real - v.chegada_prev).dt.total_seconds() / 60
v["duracao_prev"] = (v.chegada_prev - v.partida_prev).dt.total_seconds() / 60
v["duracao_real"] = (v.chegada_real - v.partida_real).dt.total_seconds() / 60
v["data"] = v.partida_prev.dt.strftime("%Y-%m-%d")
v["mes"] = v.partida_prev.dt.strftime("%Y-%m")
v["hora"] = v.partida_prev.dt.hour
v["dia_semana"] = v.partida_prev.dt.dayofweek          # 0 = segunda
for c in ["partida_prev", "partida_real", "chegada_prev", "chegada_real"]:
    v[c] = v[c].dt.strftime("%Y-%m-%d %H:%M:%S")

# --- reclamações
r = pd.concat([ler_csv(BRUTOS / f"dadosconsumidor{a}.csv") for a in (2024, 2025)], ignore_index=True)
r.insert(0, "id", np.arange(1, len(r) + 1))
r = r.rename(columns={"UF": "uf", "Data Abertura": "data_abertura", "Nome Fantasia": "empresa_nome",
                      "Grupo Problema": "grupo_problema", "Problema": "problema", "Procurou Empresa": "procurou_empresa",
                      "Respondida": "respondida", "Situação": "situacao", "Avaliação Reclamação": "avaliacao",
                      "Nota do Consumidor": "nota", "Tempo Resposta (em dias)": "tempo_resposta",
                      "Código Classificador ANAC": "codigo", "Forma Contrato": "forma_contrato", "Assunto": "assunto"})
r["empresa"] = r.empresa_nome.map(EMPRESA_ICAO)
r["mes"] = r.data_abertura.str[:7]
r["nota"] = pd.to_numeric(r.nota, errors="coerce")
r["tempo_resposta"] = pd.to_numeric(r.tempo_resposta, errors="coerce")
p = r.codigo.fillna("").str.split(";")
r["atendimento_cod"] = p.str[0].replace("", None)   # S = o consumidor também reclama do atendimento prévio da companhia
r["avaliacao_empresa"] = p.str[1]        # P procedente, I improcedente, M parcialmente, N não informou

linhas = []
for i, parts in zip(r.id, p):
    if len(parts) < 6 or (len(parts) - 2) % 4:
        continue
    for g, k in enumerate(range(2, len(parts), 4), start=1):
        loc, op, oper, ass = parts[k:k + 4]
        for a in ass.split("/"):
            linhas.append((i, g, loc, op, oper, a))
rc = pd.DataFrame(linhas, columns=["id", "grupo", "local", "operacao", "operador", "assunto"])
rc["tema2"] = pd.to_numeric(rc.assunto.str[:2], errors="coerce")
rc["gravidade"] = rc.assunto.map(gravidade)
ordem = {"alta": 3, "média": 2, "baixa": 1}
gmax = rc.assign(o=rc.gravidade.map(ordem)).groupby("id").o.max().map({v: k for k, v in ordem.items()})
r["gravidade"] = r.id.map(gmax)
r["n_grupos"] = r.id.map(rc.groupby("id").grupo.max()).fillna(0).astype(int)
r = r[["id", "data_abertura", "mes", "uf", "empresa_nome", "empresa", "assunto", "grupo_problema", "problema",
       "forma_contrato", "procurou_empresa", "respondida", "situacao", "avaliacao", "nota", "tempo_resposta",
       "codigo", "atendimento_cod", "avaliacao_empresa", "n_grupos", "gravidade"]]

DB.parent.mkdir(parents=True, exist_ok=True)
with con() as c:
    v.to_sql("voos", c, if_exists="replace", index=False, chunksize=100000)
    r.to_sql("reclamacoes", c, if_exists="replace", index=False)
    rc.to_sql("rec_codigos", c, if_exists="replace", index=False)
    for sql in ["CREATE INDEX iv1 ON voos(empresa, origem, mes)", "CREATE INDEX iv2 ON voos(tipo_linha, situacao)",
                "CREATE INDEX ir1 ON reclamacoes(empresa, mes)", "CREATE INDEX ic1 ON rec_codigos(id)"]:
        c.execute(sql)
print(f"voos {len(v):,} | reclamacoes {len(r):,} | rec_codigos {len(rc):,} -> {DB}")
