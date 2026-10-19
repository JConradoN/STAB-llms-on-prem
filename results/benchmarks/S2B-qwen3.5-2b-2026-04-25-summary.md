# S2B Summary — qwen3.5:2b — 2026-04-25

## Metadados

| Campo                   | Valor                                        |
|-------------------------|----------------------------------------------|
| Cenário                 | S2B – Health check com parsing e JSON        |
| Modelo                  | qwen3.5:2b                                      |
| Bateria                 | 1                                            |
| Data                    | 2026-04-25                                   |
| K (runs)                | 5                                          |
| Temperatura             | 0                                |
| API                     | http://localhost:11434/api/chat                             |
| Tool disponível         | run_bash                                     |
| Execução real no host   | sim (subprocess)                             |
| Schema campos           | 13 (timestamp, cpu×2, memoria×4, gpu×6) |
| Prompt                  | S2B — prompt refinado                        |
| VRAM disponível início  | _(preencher manualmente)_                    |

## Resultados

Colunas auto: json_valid, campos, tipo_ok, ts_ok, texto_extra, JSON-ACC.
Colunas manuais: INST, TOOL-CON, TOOL-ACC, CON (critérios: ADR-0001).
JSON-ACC=-1: JSON parseável mas com defeito — requer avaliação humana.
Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`
           `docs/benchmarks/S2-health-check-json.md`, seção 6

| Run | Tool | Argumento | INST | TOOL-CON | TOOL-ACC | CON | JSON-ACC | json_valid | campos | tipo_ok | ts_ok | texto_extra | tok_total | ms_total | tok/s | thinking | Obs |
|-----|------|-----------|------|----------|----------|-----|----------|------------|--------|---------|-------|-------------|-----------|----------|-------|----------|-----|
| 1 | run_bash | `~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 1899      | 4362.6   | 105.7 | 377      |     |
| 2 | run_bash | `~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 1900      | 4238.5   | 105.6 | 377      |     |
| 3 | run_bash | `~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 1900      | 4274.200000000001 | 105.4 | 377      |     |
| 4 | run_bash | `~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 1900      | 4289.6   | 105.4 | 377      |     |
| 5 | run_bash | `~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 1900      | 4274.0   | 105.5 | 377      |     |

## Notas por dimensão (Bateria 1)

- **CON:** _(preencher após leitura dos 5 runs)_
- **TOOL-CON:** _(preencher após leitura dos 5 runs)_
- **INST:** _(preencher após leitura dos 5 runs)_
- **TOOL-ACC:** _(preencher após leitura dos 5 runs)_
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls | json_acc_auto |
|-----|-------------|-------------------|-------------|---------|-------------|---------------|
| 1 | run_bash | `~/scripts/health.sh` | True | True | 0 | 0 |
| 2 | run_bash | `~/scripts/health.sh` | True | True | 0 | 0 |
| 3 | run_bash | `~/scripts/health.sh` | True | True | 0 | 0 |
| 4 | run_bash | `~/scripts/health.sh` | True | True | 0 | 0 |
| 5 | run_bash | `~/scripts/health.sh` | True | True | 0 | 0 |

## Arquivos de runs

- [`S2B-qwen3.5-2b-2026-04-25-run1.txt`](S2B-qwen3.5-2b-2026-04-25-run1.txt)
- [`S2B-qwen3.5-2b-2026-04-25-run2.txt`](S2B-qwen3.5-2b-2026-04-25-run2.txt)
- [`S2B-qwen3.5-2b-2026-04-25-run3.txt`](S2B-qwen3.5-2b-2026-04-25-run3.txt)
- [`S2B-qwen3.5-2b-2026-04-25-run4.txt`](S2B-qwen3.5-2b-2026-04-25-run4.txt)
- [`S2B-qwen3.5-2b-2026-04-25-run5.txt`](S2B-qwen3.5-2b-2026-04-25-run5.txt)

## Próximos passos

- [ ] Ler os 5 arquivos de run e atribuir notas na tabela acima.
- [ ] Verificar manualmente os runs com json_acc_auto=-1.
- [ ] Comparar resultados com S2 para avaliar impacto do prompt refinado.
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.

---

_Gerado automaticamente por `scripts/run-s2b-benchmark.py` em 2026-04-25_