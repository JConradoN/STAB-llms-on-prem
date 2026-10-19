# S2 Summary — bonsai:27b-ternary — 2026-07-18

## Metadados

| Campo                   | Valor                                        |
|-------------------------|----------------------------------------------|
| Cenário                 | S2 – Health check com parsing e JSON         |
| Modelo                  | bonsai:27b-ternary                                      |
| Bateria                 | 1                                            |
| Data                    | 2026-07-18                                   |
| K (runs)                | 5                                          |
| Temperatura             | 0                                |
| API                     | http://localhost:11435/api/chat                             |
| Tool disponível         | run_bash                                     |
| Execução real no host   | sim (subprocess)                             |
| Schema campos           | 13+ (timestamp, cpu×2, memoria×4, gpus[N]×6) |
| VRAM disponível início  | _(preencher manualmente)_                    |

## Resultados

Colunas auto: json_valid, campos, tipo_ok, ts_ok, texto_extra, JSON-ACC.
Colunas manuais: INST, TOOL-CON, TOOL-ACC, CON (critérios: ADR-0001).
JSON-ACC=-1: JSON parseável mas com defeito — requer avaliação humana.
Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`
           `docs/benchmarks/S2-health-check-json.md`, seção 6

| Run | Tool | Argumento | INST | TOOL-CON | TOOL-ACC | CON | JSON-ACC | json_valid | campos | tipo_ok | ts_ok | texto_extra | tok_total | ms_total | tok/s | thinking | Obs |
|-----|------|-----------|------|----------|----------|-----|----------|------------|--------|---------|-------|-------------|-----------|----------|-------|----------|-----|
| 1 | run_bash | `~/scripts/health.sh 2>&1` | 4 | 4 | 4 | 4 |  4        | True       | 19/13    | True    | True  | False       | 2508      | N/A      | N/A   | 0        |     |
| 2 | run_bash | `~/scripts/health.sh 2>&1` | 4 | 4 | 4 | 4 |  4        | True       | 19/13    | True    | True  | False       | 2355      | N/A      | N/A   | 0        |     |
| 3 | run_bash | `~/scripts/health.sh 2>&1` | 4 | 4 | 4 | 4 |  4        | True       | 19/13    | True    | True  | False       | 2484      | N/A      | N/A   | 0        |     |
| 4 | run_bash | `~/scripts/health.sh 2>&1` | 4 | 4 | 4 | 4 |  4        | True       | 19/13    | True    | True  | False       | 2355      | N/A      | N/A   | 0        |     |
| 5 | run_bash | `~/scripts/health.sh 2>&1` | 4 | 4 | 4 | 4 |  4        | True       | 19/13    | True    | True  | False       | 2356      | N/A      | N/A   | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** 4 — JSON estruturalmente idêntico (19/19 campos) e comportamento idêntico nas 5 execuções
- **TOOL-CON:** 4 — sempre `run_bash` com `~/scripts/health.sh 2>&1` (comando correto) nas 5 execuções
- **INST:** 4 — JSON puro, sem markdown, sem texto extra, schema respeitado 100% (19/19 campos) em todas as 5 execuções
- **TOOL-ACC:** 4 — script de fato executado com sucesso, dados reais capturados, 5/5
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls | json_acc_auto |
|-----|-------------|-------------------|-------------|---------|-------------|---------------|
| 1 | run_bash | `~/scripts/health.sh 2>&1` | True | True | 0 | 4 |
| 2 | run_bash | `~/scripts/health.sh 2>&1` | True | True | 0 | 4 |
| 3 | run_bash | `~/scripts/health.sh 2>&1` | True | True | 0 | 4 |
| 4 | run_bash | `~/scripts/health.sh 2>&1` | True | True | 0 | 4 |
| 5 | run_bash | `~/scripts/health.sh 2>&1` | True | True | 0 | 4 |

## Arquivos de runs

- [`S2-bonsai-27b-ternary-2026-07-18-run1.txt`](S2-bonsai-27b-ternary-2026-07-18-run1.txt)
- [`S2-bonsai-27b-ternary-2026-07-18-run2.txt`](S2-bonsai-27b-ternary-2026-07-18-run2.txt)
- [`S2-bonsai-27b-ternary-2026-07-18-run3.txt`](S2-bonsai-27b-ternary-2026-07-18-run3.txt)
- [`S2-bonsai-27b-ternary-2026-07-18-run4.txt`](S2-bonsai-27b-ternary-2026-07-18-run4.txt)
- [`S2-bonsai-27b-ternary-2026-07-18-run5.txt`](S2-bonsai-27b-ternary-2026-07-18-run5.txt)

## Próximos passos

- [ ] Ler os 5 arquivos de run e atribuir notas na tabela acima.
- [ ] Verificar manualmente os runs com json_acc_auto=-1.
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s2-benchmark.py` em 2026-07-18_