# S1 Summary — claudio-9b-v1 — 2026-06-18

## Metadados

| Campo                   | Valor                              |
|-------------------------|------------------------------------|
| Cenário                 | S1 – Health check estático         |
| Modelo                  | claudio-9b-v1                            |
| Bateria                 | 1                                  |
| Data                    | 2026-06-18                         |
| K (runs)                | 5                                |
| Temperatura             | 0                      |
| API                     | http://localhost:11434/api/chat/api/chat          |
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
| 1 | run_bash | `bash ~/scripts/health.sh 2>&1` |     |          |      |          | 1492      | 11042.5  | 45.3  | 0        |     |
| 2 | run_bash | `bash ~/scripts/health.sh 2>&1` |     |          |      |          | 1492      | 10992.599999999999 | 45.3  | 0        |     |
| 3 | run_bash | `bash ~/scripts/health.sh 2>&1` |     |          |      |          | 1492      | 10976.199999999999 | 45.3  | 0        |     |
| 4 | run_bash | `bash ~/scripts/health.sh 2>&1` |     |          |      |          | 1508      | 11233.8  | 45.1  | 0        |     |
| 5 | run_bash | `bash ~/scripts/health.sh 2>&1` |     |          |      |          | 1500      | 11166.5  | 45.2  | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** _(preencher após leitura dos 5 runs)_
- **TOOL-CON:** _(preencher após leitura dos 5 runs)_
- **INST:** _(preencher após leitura dos 5 runs)_
- **TOOL-ACC:** _(preencher após leitura dos 5 runs)_
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls |
|-----|-------------|-------------------|-------------|---------|-------------|
| 1 | run_bash | `bash ~/scripts/health.sh 2>&1` | True | True | 0 |
| 2 | run_bash | `bash ~/scripts/health.sh 2>&1` | True | True | 0 |
| 3 | run_bash | `bash ~/scripts/health.sh 2>&1` | True | True | 0 |
| 4 | run_bash | `bash ~/scripts/health.sh 2>&1` | True | True | 0 |
| 5 | run_bash | `bash ~/scripts/health.sh 2>&1` | True | True | 0 |

## Arquivos de runs

- [`S1-claudio-9b-v1-2026-06-18-run1.txt`](S1-claudio-9b-v1-2026-06-18-run1.txt)
- [`S1-claudio-9b-v1-2026-06-18-run2.txt`](S1-claudio-9b-v1-2026-06-18-run2.txt)
- [`S1-claudio-9b-v1-2026-06-18-run3.txt`](S1-claudio-9b-v1-2026-06-18-run3.txt)
- [`S1-claudio-9b-v1-2026-06-18-run4.txt`](S1-claudio-9b-v1-2026-06-18-run4.txt)
- [`S1-claudio-9b-v1-2026-06-18-run5.txt`](S1-claudio-9b-v1-2026-06-18-run5.txt)

## Próximos passos

- [ ] Ler os 5 arquivos de run e atribuir notas na tabela acima.
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist:
      `docs/benchmarks/S1-models-selected.md`

---

_Gerado automaticamente por `scripts/run-s1-benchmark.py` em 2026-06-18_