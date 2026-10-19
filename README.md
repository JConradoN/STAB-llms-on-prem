# STAB-llms-on-prem

Código, fixtures, scripts e resultados do artigo **STAB: A Complexity-Ladder Framework for Evaluating Local LLMs as Autonomous Agents** (KDMiLe 2026, BRACIS 2026).

STAB é uma escada de quatro níveis de complexidade (S1 → S4) para avaliar LLMs locais como agentes autônomos com ferramentas, combinada a um protocolo de estabilidade temporal. Os experimentos rodam em hardware local (GPU NVIDIA RTX 3060, 12 GB VRAM).

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `paper/kdmile2026/` | Fontes LaTeX do artigo (`main.tex`, `main-ptbr.tex`), bibliografia e figura |
| `scripts/` | Runners dos níveis S1–S4, validação de ferramentas e análise |
| `fixtures/` | Logs sintéticos de saúde de host com gabarito JSON (`.log` e `.expected.json`) |
| `results/` | Saídas brutas e sumários das baterias (`benchmarks/`), gráficos (`plots/`), relatórios (`reports/`) e avaliações (`evals/`) |
| `docs/` | Protocolo, datasets e notas de hipóteses |

## Reprodução

Os runners estão em `scripts/run-s1-benchmark.py` a `scripts/run-s4b-v2-benchmark.py`. Eles dependem de um servidor de inferência local compatível com as ferramentas usadas (ver `docs/architecture/current-stack.md`).

## Limitações declaradas

Amostras pequenas por nível (K entre 3 e 5), execução one-shot com T=0, sem varredura de seeds e fixtures sintéticos. O artigo discute cada uma dessas limitações. Os resultados são um diagnóstico qualitativo de modos de falha, não uma estimativa estatisticamente generalizável.

## Citação

Nogueira, J. C. V. *STAB: A Complexity-Ladder Framework for Evaluating Local LLMs as Autonomous Agents.* KDMiLe 2026.

## Licença

Código e dados sob licença MIT (ver `LICENSE`).
