# -*- coding: utf-8 -*-
"""Testes rápidos das contas sensíveis (não usam o banco). Rodar: python testes.py. Sai com erro se algum falhar."""
import sys
import numpy as np, pandas as pd
from metodos import mde_diferenca, casos_por_grupo, erro_de_data, br

falhas = []
def ok(cond, nome):
    print(("ok    " if cond else "FALHA ") + nome)
    if not cond:
        falhas.append(nome)

# 1. menor efeito detectável: fórmula sem raiz de 2 e coerente com a teoria quando não há autocorrelação
rng = np.random.default_rng(0)
dif = pd.Series(rng.normal(0, 0.05, 2000))
sd, rho, ef, m90, m180 = mde_diferenca(dif, 90)
ok(abs(m90 - 2.8 * sd / np.sqrt(ef)) < 1e-12, "MDE = 2,8 x dp / raiz(dias efetivos)")
ok(abs(m90 / (2.8 * 0.05 / np.sqrt(90)) - 1) < 0.1, "MDE perto do valor teórico sem autocorrelação")
ok(abs(m180 - m90 / np.sqrt(2)) < 1e-12, "180 dias reduz o MDE por raiz de 2")
ar = pd.Series(np.convolve(rng.normal(0, 1, 3000), [1, 0.8, 0.6, 0.4], mode="valid"))
ok(mde_diferenca(ar, 90)[3] > 2.8 * ar.std() / np.sqrt(90), "autocorrelação positiva aumenta o MDE")

# 2. casos por grupo: os valores do relatório (Gol, bagagem extraviada, 36,7% de resolução)
ok(round(casos_por_grupo(0.3673, 0.10)) == 377, "377 casos por grupo para +10 pontos")
ok(round(casos_por_grupo(0.3673, 0.28)) == 46, "46 casos por grupo para +28 pontos")

# 3. erros de data no VRA
a = np.array([-1440, 1440, 1500, 30, 2890, 1300, 0, 1380])
ok(list(erro_de_data(a)) == [True, True, True, False, True, False, False, True], "regra dos erros de data")

# 4. formato dos números do relatório
ok(br(1570951) == "1.570.951" and br(7.874, 1) == "7,9" and br(1234.5, 1) == "1.234,5", "formato brasileiro")

print(f"{len(falhas)} falha(s)")
sys.exit(1 if falhas else 0)
