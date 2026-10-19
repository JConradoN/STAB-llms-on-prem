# S2 Summary — granite4.1:8b-ctx16k — 2026-05-25

## Metadados

| Campo                   | Valor                                        |
|-------------------------|----------------------------------------------|
| Cenário                 | S2 – Health check com parsing e JSON         |
| Modelo                  | granite4.1:8b-ctx16k                                      |
| Bateria                 | 1                                            |
| Data                    | 2026-05-25                                   |
| K (runs)                | 5                                          |
| Temperatura             | 0                                |
| API                     | http://localhost:11434/api/chat                             |
| Tool disponível         | run_bash                                     |
| Execução real no host   | sim (subprocess)                             |
| Schema campos           | 13 (timestamp, cpu×2, memoria×4, gpu×6) |
| VRAM disponível início  | _(preencher manualmente)_                    |

## Resultados

Colunas auto: json_valid, campos, tipo_ok, ts_ok, texto_extra, JSON-ACC.
Colunas manuais: INST, TOOL-CON, TOOL-ACC, CON (critérios: ADR-0001).
JSON-ACC=-1: JSON parseável mas com defeito — requer avaliação humana.
Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`
           `docs/benchmarks/S2-health-check-json.md`, seção 6

| Run | Tool | Argumento | INST | TOOL-CON | TOOL-ACC | CON | JSON-ACC | json_valid | campos | tipo_ok | ts_ok | texto_extra | tok_total | ms_total | tok/s | thinking | Obs |
|-----|------|-----------|------|----------|----------|-----|----------|------------|--------|---------|-------|-------------|-----------|----------|-------|----------|-----|
| 1 | run_bash | `~/scripts/health.sh` |      |          |          |     | -1       | True       | 13/13    | True    | False | False       | 1478      | 4823.2   | 56.6  | 0        |     |
| 2 | run_bash | `~/scripts/health.sh` |      |          |          |     | -1       | True       | 7/13    | True    | False | False       | 1559      | 6379.400000000001 | 56.5  | 0        |     |
| 3 | run_bash | `~/scripts/health.sh` |      |          |          |     | 4        | True       | 13/13    | True    | True  | False       | 1480      | 4776.2   | 56.6  | 0        |     |
| 4 | run_bash | `~/scripts/health.sh` |      |          |          |     | 4        | True       | 13/13    | True    | True  | False       | 1480      | 4679.6   | 56.8  | 0        |     |
| 5 | run_bash | `~/scripts/health.sh` |      |          |          |     | -1       | True       | 7/13    | True    | False | False       | 1559      | 6404.9   | 56.4  | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** _(preencher após leitura dos 5 runs)_
- **TOOL-CON:** _(preencher após leitura dos 5 runs)_
- **INST:** _(preencher após leitura dos 5 runs)_
- **TOOL-ACC:** _(preencher após leitura dos 5 runs)_
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls | json_acc_auto |
|-----|-------------|-------------------|-------------|---------|-------------|---------------|
| 1 | run_bash | `~/scripts/health.sh` | True | True | 0 | -1 |
| 2 | run_bash | `~/scripts/health.sh` | True | True | 0 | -1 |
| 3 | run_bash | `~/scripts/health.sh` | True | True | 0 | 4 |
| 4 | run_bash | `~/scripts/health.sh` | True | True | 0 | 4 |
| 5 | run_bash | `~/scripts/health.sh` | True | True | 0 | -1 |

## Arquivos de runs

- [`S2-granite4.1-8b-ctx16k-2026-05-25-run1.txt`](S2-granite4.1-8b-ctx16k-2026-05-25-run1.txt)
- [`S2-granite4.1-8b-ctx16k-2026-05-25-run2.txt`](S2-granite4.1-8b-ctx16k-2026-05-25-run2.txt)
- [`S2-granite4.1-8b-ctx16k-2026-05-25-run3.txt`](S2-granite4.1-8b-ctx16k-2026-05-25-run3.txt)
- [`S2-granite4.1-8b-ctx16k-2026-05-25-run4.txt`](S2-granite4.1-8b-ctx16k-2026-05-25-run4.txt)
- [`S2-granite4.1-8b-ctx16k-2026-05-25-run5.txt`](S2-granite4.1-8b-ctx16k-2026-05-25-run5.txt)

## Próximos passos

- [ ] Ler os 5 arquivos de run e atribuir notas na tabela acima.
- [ ] Verificar manualmente os runs com json_acc_auto=-1.
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s2-benchmark.py` em 2026-05-25_