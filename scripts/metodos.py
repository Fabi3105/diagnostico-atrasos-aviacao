# -*- coding: utf-8 -*-
"""Contas sensíveis usadas em mais de um script, num lugar só e com testes (testes.py)."""
import numpy as np


def mde_diferenca(dif, dias=90):
    """Menor efeito detectável (80% de poder, 5% de alarme falso) para uma série diária que JÁ É a diferença
    entre o grupo do piloto e o de comparação. Desconta a autocorrelação de 1ª ordem: dias efetivos = n(1-ρ)/(1+ρ).
    Não multiplicar por raiz de 2: a série já é a diferença. Retorna (dp, ρ, dias efetivos, MDE em 90 dias, em 180 dias)."""
    rho = dif.autocorr(1)
    ef = dias * (1 - rho) / (1 + rho)
    sd = dif.std()
    return sd, rho, ef, 2.8 * sd / np.sqrt(ef), 2.8 * sd / np.sqrt(ef * 2)


def casos_por_grupo(p0, efeito):
    """Casos por grupo para provar uma melhora de p0 para p0 + efeito numa proporção (80% de poder, 5% bilateral)."""
    p1 = p0 + efeito
    return 7.84 * (p0 * (1 - p0) + p1 * (1 - p1)) / efeito ** 2


def erro_de_data(atraso_min):
    """Atraso a menos de 90 min de um múltiplo de 24 h (fora o zero): data da partida prevista trocada no VRA."""
    a = np.abs(atraso_min)
    return (a >= 1350) & ((a % 1440 < 90) | (a % 1440 > 1350))


def br(v, c=0):
    """Número no formato brasileiro, como o relatório escreve (ponto de milhar, vírgula decimal)."""
    return f"{v:,.{c}f}".replace(",", "X").replace(".", ",").replace("X", ".")
