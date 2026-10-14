# -*- coding: utf-8 -*-
"""Roda o estudo do zero: carga, validação e análises, na ordem. Uso: python rodar_tudo.py [de] [ate]
(índices da lista ETAPAS, para retomar de um ponto). Banco em ANAC_SQLITE ou dados/anac.sqlite."""
import subprocess, sys, time
from pathlib import Path
ETAPAS = ["testes.py", "carga.py", "clima.py", "validar_dados.py", "indicadores_padrao.py", "q1_companhias_aeroportos.py", "q2_fluxo_diario.py",
          "q2b_origem_do_atraso.py", "q3_folga_horarios.py", "q4_sazonalidade.py", "q_clima.py", "q5_reclamacoes.py", "q6_companhia_aeroporto.py", "q7_apoio_metas.py", "q8_ponte_aerea.py", "q9_motivos_cancelamento_2019.py", "q10_revisao_senior.py", "q11_passageiros.py", "q12_revisao_camada1.py",
          "graficos.py", "painel_dados.py", "painel_montar.py", "conferir_relatorio.py"]   # análises entram aqui conforme forem aprovadas
de = int(sys.argv[1]) if len(sys.argv) > 1 else 0
ate = int(sys.argv[2]) if len(sys.argv) > 2 else len(ETAPAS)
aqui = Path(__file__).parent
for i, s in enumerate(ETAPAS[de:ate], start=de):
    t = time.time(); print(f"[{i}] {s} ...", flush=True)
    subprocess.run([sys.executable, str(aqui / s)], check=True, cwd=aqui)
    print(f"[{i}] ok em {time.time() - t:.0f}s")
