# S2 Summary — claudio-9b-v2 — 2026-06-18

## Metadados

| Campo                   | Valor                                        |
|-------------------------|----------------------------------------------|
| Cenário                 | S2 – Health check com parsing e JSON         |
| Modelo                  | claudio-9b-v2                                      |
| Bateria                 | 1                                            |
| Data                    | 2026-06-18                                   |
| K (runs)                | 5                                          |
| Temperatura             | 0                                |
| API                     | http://localhost:11434/api/chat                             |
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
| 1 | run_bash | `bash ~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 2255      | 3799.1   | 46.2  | 0        |     |
| 2 | run_bash | `bash ~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 2255      | 3253.0   | 44.2  | 0        |     |
| 3 | run_bash | `bash ~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 2254      | 3137.0   | 44.6  | 0        |     |
| 4 | run_bash | `bash ~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 2254      | 3256.2   | 44.3  | 0        |     |
| 5 | run_bash | `bash ~/scripts/health.sh` |      |          |          |     | 0        | False      | 0/13    | True    | False | False       | 2254      | 3276.8999999999996 | 44.1  | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** _(preencher após leitura dos 5 runs)_
- **TOOL-CON:** _(preencher após leitura dos 5 runs)_
- **INST:** _(preencher após leitura dos 5 runs)_
- **TOOL-ACC:** _(preencher após leitura dos 5 runs)_
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls | json_acc_auto |
|-----|-------------|-------------------|-------------|---------|-------------|---------------|
| 1 | run_bash | `bash ~/scripts/health.sh` | True | True | 0 | 0 |
| 2 | run_bash | `bash ~/scripts/health.sh` | True | True | 0 | 0 |
| 3 | run_bash | `bash ~/scripts/health.sh` | True | True | 0 | 0 |
| 4 | run_bash | `bash ~/scripts/health.sh` | True | True | 0 | 0 |
| 5 | run_bash | `bash ~/scripts/health.sh` | True | True | 0 | 0 |

## Arquivos de runs

- [`S2-claudio-9b-v2-2026-06-18-run1.txt`](S2-claudio-9b-v2-2026-06-18-run1.txt)
- [`S2-claudio-9b-v2-2026-06-18-run2.txt`](S2-claudio-9b-v2-2026-06-18-run2.txt)
- [`S2-claudio-9b-v2-2026-06-18-run3.txt`](S2-claudio-9b-v2-2026-06-18-run3.txt)
- [`S2-claudio-9b-v2-2026-06-18-run4.txt`](S2-claudio-9b-v2-2026-06-18-run4.txt)
- [`S2-claudio-9b-v2-2026-06-18-run5.txt`](S2-claudio-9b-v2-2026-06-18-run5.txt)

## Próximos passos

- [ ] Ler os 5 arquivos de run e atribuir notas na tabela acima.
- [ ] Verificar manualmente os runs com json_acc_auto=-1.
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s2-benchmark.py` em 2026-06-18_