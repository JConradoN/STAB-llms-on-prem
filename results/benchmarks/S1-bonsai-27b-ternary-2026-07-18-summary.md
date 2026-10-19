# S1 Summary — bonsai:27b-ternary — 2026-07-18

## Metadados

| Campo                   | Valor                              |
|-------------------------|------------------------------------|
| Cenário                 | S1 – Health check estático         |
| Modelo                  | bonsai:27b-ternary                            |
| Bateria                 | 1                                  |
| Data                    | 2026-07-18                         |
| K (runs)                | 5                                |
| Temperatura             | 0                      |
| API                     | http://localhost:11435/api/chat/api/chat          |
| Tool disponível         | run_bash                           |
| Execução real no host   | sim (subprocess)                   |
| VRAM disponível início  | _(preencher manualmente)_          |

## Resultados

Preencher CON, TOOL-CON, INST com notas 0–4 após leitura dos runs.
TOOL-ACC=0 já marcado onde nenhuma tool válida foi chamada.
Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`
           `docs/benchmarks/evaluation-framework.md`, seção 4.4

| Run | Tool chamada | Argumento | CON | TOOL-CON | INST | TOOL-ACC | tok_total | ms_total | tok/s | thinking | Obs |
|-----|-------------|-----------|-----|----------|------|----------|-----------|----------|-------|----------|-----|
| 1 | run_bash | `~/scripts/health.sh` | 4 | 4 | 4 | 4 | 1587      | N/A      | N/A   | 0        |     |
| 2 | run_bash | `~/scripts/health.sh` | 4 | 4 | 4 | 4 | 1615      | N/A      | N/A   | 0        |     |
| 3 | run_bash | `~/scripts/health.sh` | 4 | 4 | 4 | 4 | 1615      | N/A      | N/A   | 0        |     |
| 4 | run_bash | `~/scripts/health.sh` | 4 | 4 | 4 | 4 | 1613      | N/A      | N/A   | 0        |     |
| 5 | run_bash | `~/scripts/health.sh` | 4 | 4 | 4 | 4 | 1613      | N/A      | N/A   | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** 4 — saída idêntica ao stdout do script em todas as 5 execuções, sem variação
- **TOOL-CON:** 4 — mesma tool (`run_bash`) e mesmo argumento (`~/scripts/health.sh`) em todas as 5 execuções
- **INST:** 4 — saída final idêntica byte-a-byte ao stdout do script em todas as 5 execuções, sem comentários/resumos
- **TOOL-ACC:** 4 — script correto executado com sucesso, 5/5
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls |
|-----|-------------|-------------------|-------------|---------|-------------|
| 1 | run_bash | `~/scripts/health.sh` | True | True | 0 |
| 2 | run_bash | `~/scripts/health.sh` | True | True | 0 |
| 3 | run_bash | `~/scripts/health.sh` | True | True | 0 |
| 4 | run_bash | `~/scripts/health.sh` | True | True | 0 |
| 5 | run_bash | `~/scripts/health.sh` | True | True | 0 |

## Arquivos de runs

- [`S1-bonsai-27b-ternary-2026-07-18-run1.txt`](S1-bonsai-27b-ternary-2026-07-18-run1.txt)
- [`S1-bonsai-27b-ternary-2026-07-18-run2.txt`](S1-bonsai-27b-ternary-2026-07-18-run2.txt)
- [`S1-bonsai-27b-ternary-2026-07-18-run3.txt`](S1-bonsai-27b-ternary-2026-07-18-run3.txt)
- [`S1-bonsai-27b-ternary-2026-07-18-run4.txt`](S1-bonsai-27b-ternary-2026-07-18-run4.txt)
- [`S1-bonsai-27b-ternary-2026-07-18-run5.txt`](S1-bonsai-27b-ternary-2026-07-18-run5.txt)

## Próximos passos

- [ ] Ler os 5 arquivos de run e atribuir notas na tabela acima.
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist:
      `docs/benchmarks/S1-models-selected.md`

---

_Gerado automaticamente por `scripts/run-s1-benchmark.py` em 2026-07-18_