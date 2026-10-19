# S4 Summary — qwen3:14b — 2026-04-25

## Metadados

| Campo                   | Valor                                                    |
|-------------------------|----------------------------------------------------------|
| Cenário                 | S4 – Triagem multi-log e decisão de escalonamento        |
| Modelo                  | qwen3:14b                                                  |
| Bateria                 | 1                                                        |
| Data                    | 2026-04-25                                               |
| K (casos)               | 3                                                      |
| Temperatura             | 0                                            |
| API                     | http://localhost:11434/api/chat                                         |
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
| S4-A | 1          | 0         | True         | False     | False   | True   | True      | 0              | 1516      | 32836.7  | 33.2  | 2653     |     |
| S4-B | 3          | 4         | True         | True      | False   | True   | True      | 3              | 4759      | 79392.4  | 32.0  | 8025     |     |
| S4-C | 1          | 0         | True         | False     | False   | True   | True      | 0              | 1553      | 27675.3  | 33.1  | 2717     |     |

## Notas por dimensão (Bateria 1)

- **TRIAGE-ACC** (agregado): _(derivar de triage_acc_auto acima)_
- **CHAIN-ACC** (agregado): _(derivar de read_file_calls acima — 3 em todos = nota 4)_
- **CON:** _(preencher após leitura dos runs — verificar: severity ↔ escalation, rank sem duplicatas, timestamp_triage coerente)_
- **INST:** _(preencher após leitura dos runs — checklist S4-triage-multi-log.md seção 8)_
- **TOOL-CON:** _(preencher após leitura dos runs)_
- **TOOL-ACC:** _(preencher após leitura dos runs)_
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Case | read_file calls | loop_exhausted | triage_acc_auto | chain_acc | all_hosts | rank_ok | esc_ok |
|------|----------------|----------------|-----------------|-----------|-----------|---------|--------|
| S4-A | 0 | False | 1 | 0 | False | False | True |
| S4-B | 3 | False | 3 | 4 | True | False | True |
| S4-C | 0 | False | 1 | 0 | False | False | True |

## Arquivos de runs

- [`S4-qwen3-14b-2026-04-25-case-S4-A.txt`](S4-qwen3-14b-2026-04-25-case-S4-A.txt)
- [`S4-qwen3-14b-2026-04-25-case-S4-B.txt`](S4-qwen3-14b-2026-04-25-case-S4-B.txt)
- [`S4-qwen3-14b-2026-04-25-case-S4-C.txt`](S4-qwen3-14b-2026-04-25-case-S4-C.txt)

## Próximos passos

- [ ] Ler os 3 arquivos de run e atribuir notas INST/CON/TOOL-CON/TOOL-ACC.
- [ ] Verificar manualmente a qualidade do campo `acao_geral` em cada run.
- [ ] Executar Bateria 2 após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Atualizar hipóteses H10/H11 com dados S4.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s4-benchmark.py` em 2026-04-25_