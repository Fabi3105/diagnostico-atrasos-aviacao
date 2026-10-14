# -*- coding: utf-8 -*-
"""Funções e tabelas comuns a todos os scripts do estudo.

Banco: SQLite. O caminho padrão é dados/anac.sqlite; a variável de ambiente ANAC_SQLITE troca o caminho
(necessário quando a pasta do projeto está num disco de rede ou montado, onde o SQLite pode falhar).
Ordem de execução: carga.py -> validar_dados.py -> análises (ver rodar_tudo.py)."""
import os, sqlite3
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos"
RES = RAIZ / "resultados"
DB = Path(os.environ.get("ANAC_SQLITE", RAIZ / "dados" / "anac.sqlite"))

# Período comum às duas bases (voos: set/2024 a ago/2026; reclamações: 2024 e 2025)
CRUZ_INI, CRUZ_FIM = "2024-09-01", "2026-01-01"
# Período completo de voos (24 meses)
VOO_INI, VOO_FIM = "2024-09-01", "2026-09-01"
ATRASO_MIN = 30          # definição A: atraso = partida mais de 30 min após o previsto (classe oficial ANAC)
GRANDES = ["AZU", "TAM", "GLO"]

def con():
    return sqlite3.connect(DB)

def ler(sql, **kw):
    with con() as c:
        return pd.read_sql_query(sql, c, **kw)

def salvar(df, nome, **kw):
    RES.mkdir(exist_ok=True)
    kw.setdefault("index", False)
    df.to_csv(RES / nome, encoding="utf-8-sig", **kw)
    return df

# Companhias: nome no consumidor.gov.br -> código ICAO usado no VRA
EMPRESA_ICAO = {
    "Azul Linhas Aéreas": "AZU", "Latam Airlines (Tam)": "TAM", "Gol Linhas Aéreas": "GLO",
    "Voepass Linhas Aéreas": "PTB", "MAP Linhas Aéreas": "PAM", "TAP Air Portugal": "TAP",
    "Iberia Lineas Aereas": "IBE", "Avianca - Voos internacionais": "AVA", "Copa Airlines": "CMP",
    "American Airlines": "AAL", "Aerolíneas Argentinas": "ARG", "Italia Trasporto Aereo (ITA Airways)": "ITY",
    "Air France": "AFR", "Sky Airline": "SKU", "British Airways": "BAW", "United Airlines": "UAL",
    "Qatar Airways": "QTR", "Delta Air Lines": "DAL", "KLM": "KLM", "ARAJET S.A.": "DWI", "Lufthansa": "DLH",
    "JetSMART Airlines - Chile": "JAT", "JetSMART Airlines - Argentina": "JES", "Air Europa": "AEA",
    "Turkish Airlines": "THY", "Air Canada": "ACA", "Flybondi": "FBZ", "Emirates": "UAE",
    "Ethiopian Airlines": "ETH", "Swiss": "SWR", "Royal Air Maroc": "RAM", "TAAG - Linhas Aéreas de Angola": "DTA",
    "Aeromexico": "AMX", "South African Airways": "SAA", "Alitalia": "AZA", "Air China": "CCA",
    "Boliviana de Aviación - BoA": "BOV", "Virgin Atlantic Airways ": "VIR", "Cabo Verde Airlines": "TCV",
    "EL AL": "ELY", "Amaszonas Línea Aérea": "AZN", "Edelweiss Air": "EDW", "Surinam Airways": "SLM",
    "Avior Airlines": "ROI", "Paranair": "ARP",
}
NOME_CURTO = {"AZU": "Azul", "TAM": "LATAM", "GLO": "Gol", "PTB": "Voepass", "ACN": "Azul Conecta"}

# Aeroportos brasileiros: código ICAO (VRA) -> código IATA (reclamações). Montada pelo analista para os
# aeródromos com voo doméstico regular relevante; conferida contra as duas bases em validar_dados.py.
ICAO_IATA = {
    "SBGR": "GRU", "SBSP": "CGH", "SBCF": "CNF", "SBBR": "BSB", "SBKP": "VCP", "SBGL": "GIG", "SBRF": "REC",
    "SBRJ": "SDU", "SBSV": "SSA", "SBCT": "CWB", "SBPA": "POA", "SBFZ": "FOR", "SBBE": "BEL", "SBFL": "FLN",
    "SBGO": "GYN", "SBVT": "VIX", "SBEG": "MAO", "SBCY": "CGB", "SBMO": "MCZ", "SBPS": "BPS", "SBNF": "NVT",
    "SBSG": "NAT", "SBFI": "IGU", "SBSL": "SLZ", "SBJP": "JPA", "SBUL": "UDI", "SBCG": "CGR", "SBAR": "AJU",
    "SBSR": "SJP", "SBRP": "RAO", "SBTE": "THE", "SBMG": "MGF", "SBLO": "LDB", "SBPJ": "PMW", "SBCH": "XAP",
    "SBIL": "IOS", "SBJV": "JOI", "SBMQ": "MCP", "SBPV": "PVH", "SBSN": "STM", "SBMK": "MOC", "SBCA": "CAC",
    "SBFN": "FEN", "SBJU": "JDO", "SBPL": "PNZ", "SBSI": "OPS", "SBRB": "RBR", "SBVC": "VDC", "SBMA": "MAB",
    "SBIZ": "IMP", "SBDN": "PPB", "SBIP": "IPN", "SBBV": "BVB", "SBCJ": "CKS", "SBCX": "CXJ", "SBKG": "CPV",
    "SBPF": "PFB", "SBJE": "JJD", "SBZM": "IZA", "SBGV": "GVR", "SBAU": "ARU", "SBUR": "UBA", "SBAE": "JTC",
    "SBPK": "PET", "SBJA": "JJG", "SBTT": "TBT", "SBAQ": "AQA", "SBNM": "GEL", "SBHT": "ATM", "SBML": "MII",
    "SBPO": "PTO", "SBTF": "TFF", "SBSM": "RIA", "SBRD": "ROO", "SBCN": "CLV", "SBAT": "AFL", "SBAX": "AAX",
    "SBBW": "BPG", "SBCZ": "CZS", "SBSJ": "SJK", "SBUG": "URG", "SBJI": "JPR", "SBPP": "PMG", "SBIH": "ITB",
    "SBTB": "TMT", "SBPB": "PHB", "SBTC": "UNA", "SBVG": "VAG", "SBCR": "CMG", "SBVH": "BVH", "SBUA": "SJL",
    "SBDO": "DOU", "SBTU": "TUR", "SBLE": "LEC", "SBMD": "MEU", "SBBH": "PLU", "SBCP": "CAW", "SBCB": "CFB",
    "SBMS": "MVF", "SBTG": "TJL", "SBMY": "MNX", "SBOI": "OIA", "SBPG": "PNG",
    # aeródromos regionais
    "SNBR": "BRA", "SNGI": "GNM", "SNDV": "DIQ", "SBDB": "BYO", "SBSO": "SMT", "SWPI": "PIN", "SNVS": "BVS",
    "SWKO": "CIZ", "SWLC": "RVD", "SNRU": "CAU", "SWBC": "BAZ", "SWEI": "ERN", "SWTP": "IRZ", "SWCA": "CAF",
    "SWLB": "LBR", "SSUM": "UMU", "SSGG": "GPB", "SNPD": "POJ", "SNTO": "TFL", "SSKW": "OAL", "SBJR": "RRJ",
}
IATA_ICAO = {v: k for k, v in ICAO_IATA.items()}

# Definição F (aprovada em 10/10/2026): gravidade pelo tema oficial da ANAC (Portaria 9.128/SAS, Anexo II).
# Chave = dois primeiros dígitos do código de assunto.
def gravidade(cod):
    if not cod or len(cod) < 2 or not cod[:2].isdigit():
        return None
    g = int(cod[:2])
    if g in (22, 23, 33, 34, 35, 41, 43) or 61 <= g <= 69:
        return "alta"      # deixou de voar, ficou retido sem assistência, perdeu a bagagem, PNAE
    if g in (21, 29, 31, 32, 39, 42, 44, 45) or 51 <= g <= 54:
        return "média"     # atraso, alteração pela empresa, embarque, bagagem avariada, reembolso
    return "baixa"         # compra, tarifa, alteração pelo passageiro, opcionais, fidelidade, outros

TEMA = {  # grupos do Anexo II, para leitura
    **{g: "Oferta e compra" for g in range(1, 10)}, **{g: "Alteração pelo passageiro" for g in range(11, 19)},
    21: "Alteração pela empresa: aviso", 22: "Alteração pela empresa: alternativas",
    23: "Alteração pela empresa: assistência", 29: "Alteração pela empresa: outros",
    31: "Check-in e embarque", 32: "Comunicação sobre atraso/cancelamento",
    33: "Alternativas em atraso/cancelamento/preterição", 34: "Assistência material no atraso",
    35: "Preterição (overbooking)", 39: "Execução do voo: outros (atraso, conexão, desembarque)",
    41: "Bagagem extraviada", 42: "Bagagem avariada", 43: "Bagagem violada", 44: "Bagagem: outros", 45: "Bagagem: outros",
    **{g: "Reembolso" for g in range(51, 55)}, **{g: "Passageiro com necessidade especial" for g in range(61, 70)},
    **{g: "Itens opcionais" for g in range(71, 80)}, 80: "Programa de fidelidade", **{g: "Outros" for g in range(90, 100)},
}

# Definição B (aprovada): voos domésticos regulares com horário previsto, no período completo.
# Voos sem horário previsto são voos não programados (extras, traslados, retornos, testes): não são promessa
# ao passageiro e ficam fora das taxas de pontualidade e de cancelamento.
ESCOPO = (f"tipo_linha = 'N' AND partida_prev IS NOT NULL "
          f"AND partida_prev >= '{VOO_INI}' AND partida_prev < '{VOO_FIM}'")

# Os horários do VRA estão no horário de Brasília (verificado em validar_dados.py). Para ler o horário do
# relógio local, soma-se a diferença de fuso do aeroporto (horas; sem horário de verão no período).
# Aeroportos não listados estão no horário de Brasília.
FUSO_AEROPORTO = {
    **{a: -1 for a in ["SBEG", "SBPV", "SBCY", "SBCG", "SBBV", "SBSI", "SBRD", "SBTT", "SBTF", "SBAT", "SBBW",
                       "SBCR", "SBDO", "SBJI", "SBVH", "SSKW", "SWPI", "SWKO", "SWBC", "SWLB", "SWCA", "SWTP",
                       "SBPP", "SBTG", "SBDB", "SBSO", "SBUA", "SBMY", "SBUY"]},
    **{a: -2 for a in ["SBRB", "SBCZ", "SWEI"]},
    "SBFN": +1,
}

COLS_PADRAO = ("empresa, voo, origem, destino, situacao, atraso_partida, atraso_chegada, duracao_prev, "
               "duracao_real, data, mes, hora, dia_semana, CAST(strftime('%M', partida_prev) AS INTEGER) AS minuto_prev")

def voos_escopo(cols=COLS_PADRAO):
    """Voos do escopo (definição B) com colunas derivadas padrão:
    atrasado (partida > 30 min), cancelado, hora_local e minutos_atraso (minutos além do previsto nos voos
    atrasados, limitados a 24 h para que um caso extremo não pese como dezenas de voos)."""
    import numpy as np
    cache = DB.parent / "voos_escopo.pkl"          # cópia de trabalho ao lado do banco (refeita se o banco mudar)
    fonte = max(DB.stat().st_mtime, Path(__file__).stat().st_mtime, (Path(__file__).parent / "metodos.py").stat().st_mtime)   # refeito se o banco, este arquivo ou metodos.py mudarem
    if cols == COLS_PADRAO and cache.exists() and cache.stat().st_mtime > fonte:
        return pd.read_pickle(cache)
    v = ler(f"SELECT {cols} FROM voos WHERE {ESCOPO}")
    for c in v.columns:          # texto vira categoria para caber na memória (1,6 milhão de linhas)
        if v[c].dtype == object:
            v[c] = v[c].astype("category")
    for c in v.select_dtypes("float64").columns:
        v[c] = v[c].astype("float32")
    v["cancelado"] = v.situacao == "CANCELADO"
    real = ~v.cancelado
    v["atrasado"] = np.where(real, v.atraso_partida > ATRASO_MIN, np.nan)
    v["atrasado_chegada"] = np.where(real, v.atraso_chegada > ATRASO_MIN, np.nan)
    # erro de data no VRA: atraso a menos de 90 min de um múltiplo de 24 h (ex.: partida prevista no dia seguinte ao real).
    # São 0,008% dos voos; ficam fora das taxas de atraso e dos minutos (ver validar_dados.py).
    from metodos import erro_de_data
    v["erro_data"] = real & erro_de_data(v.atraso_partida.fillna(0))
    v.loc[v.erro_data, ["atrasado", "atrasado_chegada"]] = np.nan
    v["minutos_atraso"] = np.where(real & ~v.erro_data & (v.atraso_partida > ATRASO_MIN), v.atraso_partida.clip(upper=1440), 0.0)
    v["hora_local"] = ((v.hora + v.origem.astype(str).map(FUSO_AEROPORTO).fillna(0)) % 24).astype("float32")
    if cols == COLS_PADRAO:
        v.to_pickle(cache)
    return v
