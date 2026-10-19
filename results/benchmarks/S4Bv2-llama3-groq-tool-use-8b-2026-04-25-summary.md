# S4 Summary — llama3-groq-tool-use:8b — 2026-04-25

## Metadados

| Campo                   | Valor                                                    |
|-------------------------|----------------------------------------------------------|
| Cenário                 | S4 – Triagem multi-log e decisão de escalonamento        |
| Modelo                  | llama3-groq-tool-use:8b                                                  |
| Bateria                 | 1                                                        |
| Data                    | 2026-04-25                                               |
| K (casos)               | 1                                                      |
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
| S4-B | 2          | 4         | True         | True      | True    | False  | True      | 3              | 2538      | 9184.1   | 67.9  | 0        |     |

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
| S4-B | 3 | False | 2 | 4 | True | True | False |

## Arquivos de runs

- [`S4-llama3-groq-tool-use-8b-2026-04-25-case-S4-B.txt`](S4-llama3-groq-tool-use-8b-2026-04-25-case-S4-B.txt)

## Próximos passos

- [ ] Ler os 3 arquivos de run e atribuir notas INST/CON/TOOL-CON/TOOL-ACC.
- [ ] Verificar manualmente a qualidade do campo `acao_geral` em cada run.
- [ ] Executar Bateria 2 após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Atualizar hipóteses H10/H11 com dados S4.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s4-benchmark.py` em 2026-04-25_