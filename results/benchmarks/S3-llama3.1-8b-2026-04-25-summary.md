# S3 Summary — llama3.1:8b — 2026-04-25

## Metadados

| Campo                   | Valor                                                   |
|-------------------------|---------------------------------------------------------|
| Cenário                 | S3 – Análise de log, classificação e resumo             |
| Modelo                  | llama3.1:8b                                                 |
| Bateria                 | 1                                                       |
| Data                    | 2026-04-25                                              |
| K (casos)               | 4                                                     |
| Temperatura             | 0                                           |
| API                     | http://localhost:11434/api/chat                                        |
| Tool disponível         | read_file                                               |
| Execução de subprocess  | não (leitura direta via Python)                         |
| Fixtures                | info-001, warning-001, critical-001, mixed-001          |
| VRAM disponível início  | _(preencher manualmente)_                               |

## Resultados

Colunas auto: CLASS-ACC, PARSE-ACC, json_valid, severity, primary_ok, secondary_ok,
req_action_ok, summary_ok.
Colunas manuais: SUMMARY-QUAL, CON, TOOL-CON, INST, TOOL-ACC (critérios: ADR-0001).
Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`
           `docs/benchmarks/S3-log-analysis-classify.md`, seções 8–9

| Case | Tool | Path | CLASS-ACC | PARSE-ACC | json_valid | severity | primary_ok | secondary_ok | req_action_ok | summary_ok | tok_total | ms | tok/s | thinking | Obs |
|------|------|------|-----------|-----------|------------|----------|------------|--------------|---------------|------------|-----------|----|----|----------|-----|
| info-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 1312      | 5254.9   | 65.3  | 0        |     |
| warning-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 1351      | 3068.4   | 65.0  | 0        |     |
| critical-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 1321      | 3367.1000000000004 | 65.1  | 0        |     |
| mixed-001 | read_file | `./…` | 2         | 2         | True       | True     | False      | False        | True          | True       | 1363      | 3370.5   | 64.8  | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** _(preencher após leitura dos 4 runs)_
- **TOOL-CON:** _(preencher após leitura dos 4 runs)_
- **INST:** _(preencher após leitura dos 4 runs)_
- **TOOL-ACC:** _(preencher após leitura dos 4 runs)_
- **CLASS-ACC** (agregado): _(derivar de class_acc_auto acima)_
- **PARSE-ACC** (agregado): _(derivar de parse_acc_auto acima)_
- **SUMMARY-QUAL** (agregado): _(avaliação manual — ler campo summary em cada run)_
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Case | Tool chamada | Argumento completo | Tool válida | Leitura OK | Extra calls | class_acc_auto | parse_acc_auto |
|------|-------------|-------------------|-------------|------------|-------------|----------------|----------------|
| info-001 | read_file | `./fixtures/health-logs/info/info-001.log` | True | True | 0 | 4 | 4 |
| warning-001 | read_file | `./fixtures/health-logs/warning/warning-001.log` | True | True | 0 | 4 | 4 |
| critical-001 | read_file | `./fixtures/health-logs/critical/critical-001.log` | True | True | 0 | 4 | 4 |
| mixed-001 | read_file | `./fixtures/health-logs/mixed/mixed-001.log` | True | True | 0 | 2 | 2 |

## Arquivos de runs

- [`S3-llama3.1-8b-2026-04-25-case-info-001.txt`](S3-llama3.1-8b-2026-04-25-case-info-001.txt)
- [`S3-llama3.1-8b-2026-04-25-case-warning-001.txt`](S3-llama3.1-8b-2026-04-25-case-warning-001.txt)
- [`S3-llama3.1-8b-2026-04-25-case-critical-001.txt`](S3-llama3.1-8b-2026-04-25-case-critical-001.txt)
- [`S3-llama3.1-8b-2026-04-25-case-mixed-001.txt`](S3-llama3.1-8b-2026-04-25-case-mixed-001.txt)

## Próximos passos

- [ ] Ler os 4 arquivos de run e atribuir notas na tabela acima.
- [ ] Avaliar SUMMARY-QUAL manualmente (ler campo `summary` em cada run).
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s3-benchmark.py` em 2026-04-25_