# S3 Summary — bonsai:27b-ternary — 2026-07-18

## Metadados

| Campo                   | Valor                                                   |
|-------------------------|---------------------------------------------------------|
| Cenário                 | S3 – Análise de log, classificação e resumo             |
| Modelo                  | bonsai:27b-ternary                                                 |
| Bateria                 | 1                                                       |
| Data                    | 2026-07-18                                              |
| K (casos)               | 4                                                     |
| Temperatura             | 0                                           |
| API                     | http://localhost:11435/api/chat                                        |
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
| info-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 1946      | N/A      | N/A   | 0        |     |
| warning-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 2345      | N/A      | N/A   | 0        |     |
| critical-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 2469      | N/A      | N/A   | 0        |     |
| mixed-001 | read_file | `./…` | 4         | 4         | True       | True     | True       | True         | True          | True       | 2291      | N/A      | N/A   | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** 4 — estratégia consistente e correta nos 4 casos: sempre lê o arquivo real e produz JSON grounded
- **TOOL-CON:** 4 — sempre chama `read_file` com o path correto, 4/4 casos
- **INST:** 4 — JSON puro sem markdown, schema respeitado 100%, summary em PT-BR presente e dentro do limite de caracteres, 4/4 casos
- **TOOL-ACC:** 4 — leitura real do arquivo bem-sucedida em todos os 4 casos, dados extraídos do conteúdo real
- **CLASS-ACC** (agregado): 4 — severity bate com o expected nos 4/4 casos
- **PARSE-ACC** (agregado): 4 — primary_issue, secondary_issues e host corretos nos 4/4 casos
- **SUMMARY-QUAL** (agregado): 4 — resumos precisos, mencionam primary_issue e contexto numérico real (ex: '87% CPU', 'disco /var 97%'), grounded no conteúdo real do log
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Case | Tool chamada | Argumento completo | Tool válida | Leitura OK | Extra calls | class_acc_auto | parse_acc_auto |
|------|-------------|-------------------|-------------|------------|-------------|----------------|----------------|
| info-001 | read_file | `./fixtures/health-logs/info/info-001.log` | True | True | 0 | 4 | 4 |
| warning-001 | read_file | `./fixtures/health-logs/warning/warning-001.log` | True | True | 0 | 4 | 4 |
| critical-001 | read_file | `./fixtures/health-logs/critical/critical-001.log` | True | True | 0 | 4 | 4 |
| mixed-001 | read_file | `./fixtures/health-logs/mixed/mixed-001.log` | True | True | 0 | 4 | 4 |

## Arquivos de runs

- [`S3-bonsai-27b-ternary-2026-07-18-case-info-001.txt`](S3-bonsai-27b-ternary-2026-07-18-case-info-001.txt)
- [`S3-bonsai-27b-ternary-2026-07-18-case-warning-001.txt`](S3-bonsai-27b-ternary-2026-07-18-case-warning-001.txt)
- [`S3-bonsai-27b-ternary-2026-07-18-case-critical-001.txt`](S3-bonsai-27b-ternary-2026-07-18-case-critical-001.txt)
- [`S3-bonsai-27b-ternary-2026-07-18-case-mixed-001.txt`](S3-bonsai-27b-ternary-2026-07-18-case-mixed-001.txt)

## Próximos passos

- [ ] Ler os 4 arquivos de run e atribuir notas na tabela acima.
- [ ] Avaliar SUMMARY-QUAL manualmente (ler campo `summary` em cada run).
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s3-benchmark.py` em 2026-07-18_