# S3 Summary — qwen3:30b-a3b — 2026-06-01

## Metadados

| Campo                   | Valor                                                   |
|-------------------------|---------------------------------------------------------|
| Cenário                 | S3 – Análise de log, classificação e resumo             |
| Modelo                  | qwen3:30b-a3b                                                 |
| Bateria                 | 1                                                       |
| Data                    | 2026-06-01                                              |
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
| info-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 4263      | 46454.899999999994 | 42.5  | 0        |     |
| warning-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 3517      | 38031.5  | 41.8  | 0        |     |
| critical-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 3091      | 32694.0  | 41.1  | 0        |     |
| mixed-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 3077      | 30013.1  | 41.5  | 0        |     |

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
| mixed-001 | read_file | `./fixtures/health-logs/mixed/mixed-001.log` | True | True | 0 | 4 | 4 |

## Arquivos de runs

- [`S3-qwen3-30b-a3b-2026-06-01-case-info-001.txt`](S3-qwen3-30b-a3b-2026-06-01-case-info-001.txt)
- [`S3-qwen3-30b-a3b-2026-06-01-case-warning-001.txt`](S3-qwen3-30b-a3b-2026-06-01-case-warning-001.txt)
- [`S3-qwen3-30b-a3b-2026-06-01-case-critical-001.txt`](S3-qwen3-30b-a3b-2026-06-01-case-critical-001.txt)
- [`S3-qwen3-30b-a3b-2026-06-01-case-mixed-001.txt`](S3-qwen3-30b-a3b-2026-06-01-case-mixed-001.txt)

## Próximos passos

- [ ] Ler os 4 arquivos de run e atribuir notas na tabela acima.
- [ ] Avaliar SUMMARY-QUAL manualmente (ler campo `summary` em cada run).
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s3-benchmark.py` em 2026-06-01_