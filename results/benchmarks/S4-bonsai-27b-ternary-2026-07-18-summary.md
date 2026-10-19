# S4 Summary — bonsai:27b-ternary — 2026-07-18

## Metadados

| Campo                   | Valor                                                    |
|-------------------------|----------------------------------------------------------|
| Cenário                 | S4 – Triagem multi-log e decisão de escalonamento        |
| Modelo                  | bonsai:27b-ternary                                                  |
| Bateria                 | 1                                                        |
| Data                    | 2026-07-18                                               |
| K (casos)               | 3                                                      |
| Temperatura             | 0                                            |
| API                     | http://localhost:11435/api/chat                                         |
| Tool disponível         | read_file                                                |
| Tool calls esperados    | 3 por caso (CHAIN-ACC)                                   |
| MAX_TOOL_TURNS          | 4                                         |
| Fixtures S4             | fixtures/triage-s4/                                      |
| VRAM disponível início  | _(preencher manualmente)_                                |

## Resultados

Colunas auto: TRIAGE-ACC, CHAIN-ACC, schema_valid, all_hosts, rank_ok, esc_ok, acao_geral.
Colunas manuais: INST, CON, TOOL-CON, TOOL-ACC (critérios: ADR-0001).
Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`
           `docs/benchmarks/S4-triage-multi-log.md`, seções 6–7

| Case | TRIAGE-ACC | CHAIN-ACC | schema_valid | all_hosts | rank_ok | esc_ok | acao_geral | read_file_calls | tok_total | ms | tok/s | thinking | Obs |
|------|-----------|-----------|-------------|-----------|---------|--------|-----------|----------------|-----------|----|----|----------|-----|
| S4-A | 4          | 4         | True         | True      | True    | True   | True      | 3              | 4165      | N/A      | 0.0   | 0        |     |
| S4-B | 4          | 4         | True         | True      | True    | True   | True      | 3              | 5048      | N/A      | 0.0   | 0        |     |
| S4-C | 4          | 4         | True         | True      | True    | True   | True      | 3              | 3580      | N/A      | 0.0   | 0        |     |

## Notas por dimensão (Bateria 1)

- **TRIAGE-ACC** (agregado): 4 — rank_ok + esc_ok + all_hosts = True nos 3/3 casos
- **CHAIN-ACC** (agregado): 4 — exatamente 3 chamadas read_file nos 3/3 casos (planejamento multi-step correto e autônomo)
- **CON:** 4 — severity/escalation coerentes, sem hosts duplicados, timestamp_triage plausível nos 3 casos
- **INST:** 4 — JSON puro, triage_id correto, hosts_analisados=3, escalation no vocabulário controlado, acao_geral presente, 3/3
- **TOOL-CON:** 4 — sempre 3x read_file por caso, mesma estratégia de planejamento multi-step nos 3 casos
- **TOOL-ACC:** 4 — leitura real bem-sucedida dos 3 arquivos em todos os 3 casos
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Case | read_file calls | loop_exhausted | triage_acc_auto | chain_acc | all_hosts | rank_ok | esc_ok |
|------|----------------|----------------|-----------------|-----------|-----------|---------|--------|
| S4-A | 3 | False | 4 | 4 | True | True | True |
| S4-B | 3 | False | 4 | 4 | True | True | True |
| S4-C | 3 | False | 4 | 4 | True | True | True |

## Arquivos de runs

- [`S4-bonsai-27b-ternary-2026-07-18-case-S4-A.txt`](S4-bonsai-27b-ternary-2026-07-18-case-S4-A.txt)
- [`S4-bonsai-27b-ternary-2026-07-18-case-S4-B.txt`](S4-bonsai-27b-ternary-2026-07-18-case-S4-B.txt)
- [`S4-bonsai-27b-ternary-2026-07-18-case-S4-C.txt`](S4-bonsai-27b-ternary-2026-07-18-case-S4-C.txt)

## Próximos passos

- [ ] Ler os 3 arquivos de run e atribuir notas INST/CON/TOOL-CON/TOOL-ACC.
- [ ] Verificar manualmente a qualidade do campo `acao_geral` em cada run.
- [ ] Executar Bateria 2 após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Atualizar hipóteses H10/H11 com dados S4.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s4-benchmark.py` em 2026-07-18_