# -*- coding: utf-8 -*-
"""Gera RELATORIO.pdf a partir de RELATORIO.md, via HTML e Chromium (Edge ou Chrome instalado).

O quadro de números da primeira página é lido do próprio sumário, para o PDF nunca divergir do texto.
Dependências, só para esta etapa: markdown e playwright."""
import base64
import re
import sys
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA, SAIDA = RAIZ / "RELATORIO.md", RAIZ / "RELATORIO.pdf"
RODAPE = "Atrasos, cancelamentos e reclamações: onde agir"
AEROPORTOS = ("GRU", "CGH", "VCP", "GIG", "SDU", "BSB", "CNF", "REC", "SSA", "POA", "CWB", "FOR", "MAO", "BEL", "FLN")

CSS = """
@page { size: A4; }
* { box-sizing: border-box; }
body { margin: 0; color: #111827; font: 9.4pt/1.42 Verdana, "DejaVu Sans", sans-serif; }
h1 { margin: 0 0 8pt; padding-bottom: 8pt; border-bottom: 3px solid #f5b301; color: #0f1b2d; font-size: 18.5pt; line-height: 1.22; }
h2 { margin: 14pt 0 7pt; padding-left: 7pt; border-left: 5px solid #f5b301; color: #0f1b2d; font-size: 13pt; break-after: avoid; }
h3 { margin: 11pt 0 5pt; color: #0f1b2d; font-size: 10.6pt; break-after: avoid; }
h4 { margin: 9pt 0 4pt; color: #0f1b2d; font-size: 9.6pt; break-after: avoid; }
p { margin: 0 0 5.5pt; }
ul, ol { margin: 0 0 6pt; padding-left: 17pt; }
li { margin-bottom: 3.5pt; }
hr { margin: 9pt 0; border: 0; border-top: 1px solid #d7dbe2; }
table { width: 100%; margin: 6pt 0 8pt; border-collapse: collapse; font-size: 7.9pt; line-height: 1.32; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th { padding: 4pt 5pt; background: #0f1b2d; color: #fff; text-align: left; vertical-align: top; }
td { padding: 3.5pt 5pt; border: 1px solid #dfe3e8; vertical-align: top; }
tbody tr:nth-child(even) td { background: #f7f8fa; }
img { display: block; width: 76%; margin: 6pt auto 8pt; break-inside: avoid; }
code, .ap { font-family: Consolas, "DejaVu Sans Mono", monospace; font-size: .96em; }
a { color: #0f3f7a; text-decoration: none; }
.quadro { margin: 9pt 0; padding: 8pt 10pt 10pt; border-radius: 5px; background: #0b1420; color: #fff; break-inside: avoid; }
.quadro header { display: flex; justify-content: space-between; padding-bottom: 6pt; border-bottom: 1px solid #263244; color: #f5b301; font: 7pt Consolas, monospace; letter-spacing: .08em; }
.quadro header span:last-child { color: #9aa6b6; letter-spacing: 0; }
.quadro section { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6pt; margin-top: 7pt; }
.quadro div { padding: 6pt 8pt; border-radius: 3px; background: #151f2e; }
.quadro small { display: block; min-height: 15pt; color: #c6cfdb; font: 6.4pt/1.2 Consolas, monospace; text-transform: uppercase; }
.quadro b { color: #f5b301; font: 700 16pt Consolas, monospace; }
"""


def achar(padrao, texto, nome):
    achado = re.search(padrao, texto)
    if not achado:
        sys.exit(f"Não encontrei no sumário: {nome}")
    return achado.group(1)


def quadro(md):
    sumario = md.split("## 1. Diagnóstico")[0]
    itens = [
        ("Partidas com atraso > 30 min", achar(r"(\d+,\d)% das partidas domésticas regulares", sumario, "atraso") + "%"),
        ("Cancelamento", achar(r"e (\d+,\d)% dos voos foram cancelados", sumario, "cancelamento") + "%"),
        ("Mediana do atraso", achar(r"na mediana, (\d+) minutos", sumario, "mediana") + " min"),
        ("Minutos de atraso", achar(r"foram (\d+,\d) milhões de minutos", sumario, "minutos") + " mi"),
    ]
    celulas = "".join(f"<div><small>{nome}</small><b>{valor}</b></div>" for nome, valor in itens)
    return ('<aside class="quadro"><header><span>PARTIDAS · DOMÉSTICO REGULAR</span>'
            f"<span>set/2024 a ago/2026 · todas as companhias</span></header><section>{celulas}</section></aside>")


def embutir_imagens(html):
    def trocar(achado):
        caminho = RAIZ / achado.group(1)
        if not caminho.exists():
            sys.exit(f"Imagem não encontrada: {achado.group(1)}")
        return f'src="data:image/png;base64,{base64.b64encode(caminho.read_bytes()).decode()}"'
    return re.sub(r'src="([^"]+\.png)"', trocar, html)


def marcar_aeroportos(html):
    padrao = re.compile(r"\b(" + "|".join(AEROPORTOS) + r")\b")
    partes = re.split(r"(<[^>]+>)", html)
    return "".join(p if p.startswith("<") else padrao.sub(r'<span class="ap">\1</span>', p) for p in partes)


def montar():
    md = ENTRADA.read_text(encoding="utf-8")
    corpo = markdown.markdown(md, extensions=["tables", "sane_lists"])
    corpo = marcar_aeroportos(corpo).replace("<hr />", quadro(md) + "<hr />", 1)
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Relatório voos ANAC</title>'
            f"<style>{CSS}</style></head><body>{embutir_imagens(corpo)}</body></html>")


def main():
    rodape = (f'<div style="width:100%;text-align:center;font:6.5pt Verdana,sans-serif;color:#555">{RODAPE} · '
              '<span class="pageNumber"></span>/<span class="totalPages"></span></div>')
    with sync_playwright() as p:
        for canal in ("msedge", "chrome"):
            try:
                navegador = p.chromium.launch(channel=canal, headless=True)
                break
            except Exception:
                navegador = None
        if navegador is None:
            sys.exit("Instale o Edge ou o Chrome para gerar o PDF.")
        pagina = navegador.new_page()
        pagina.set_content(montar(), wait_until="load")
        pagina.pdf(path=str(SAIDA), format="A4", print_background=True, display_header_footer=True,
                   header_template="<span></span>", footer_template=rodape,
                   margin={"top": "15mm", "bottom": "16mm", "left": "17mm", "right": "17mm"})
        navegador.close()
    print(f"PDF gerado: {SAIDA.name}")


if __name__ == "__main__":
    main()
