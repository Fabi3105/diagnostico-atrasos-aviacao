# -*- coding: utf-8 -*-
"""Monta o index.html: injeta resultados/painel_dados.json (painel_dados.py) no modelo scripts/painel_modelo.html."""
from base import RAIZ, RES
modelo = (RAIZ / "scripts" / "painel_modelo.html").read_text(encoding="utf-8")
dados = (RES / "painel_dados.json").read_text(encoding="utf-8")
(RAIZ / "index.html").write_text(modelo.replace("__DATA__", dados), encoding="utf-8")
print("ok: index.html")
