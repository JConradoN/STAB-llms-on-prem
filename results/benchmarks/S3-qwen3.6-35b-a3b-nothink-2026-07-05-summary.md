# S3 Summary — qwen3.6-35b-a3b-nothink — 2026-07-05

## Metadados

| Campo                   | Valor                                                   |
|-------------------------|---------------------------------------------------------|
| Cenário                 | S3 – Análise de log, classificação e resumo             |
| Modelo                  | qwen3.6-35b-a3b-nothink                                                 |
| Bateria                 | 1                                                       |
| Data                    | 2026-07-05                                              |
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
| info-001 | NENHUMA | `` | 4         | 3         | True       | True     | True       | True         | True          | True       | 765       | N/A      | N/A   | 0        |     |
| warning-001 | NENHUMA | `` | 2         | 2         | True       | True     | False      | False        | True          | True       | 788       | N/A      | N/A   | 0        |     |
| critical-001 | NENHUMA | `` | 2         | 2         | True       | True     | False      | False        | True          | True       | 799       | N/A      | N/A   | 0        |     |
| mixed-001 | NENHUMA | `` | 2         | 2         | True       | True     | False      | False        | True          | True       | 791       | N/A      | N/A   | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** 4 — comportamento consistente nos 4 casos — mas consistentemente fabricado: NUNCA chama read_file, sempre inventa um JSON plausível a partir do nome do caso
- **TOOL-CON:** 0 — GAP FUNDAMENTAL: read_file nunca é chamado em nenhum dos 4 casos (tool disponível, obrigatória pelo prompt, ignorada sistematicamente)
- **INST:** 1 — formato JSON é sempre válido e sem markdown (segue a forma da instrução), mas o núcleo da instrução -- "leia o arquivo e analise seu conteúdo" -- nunca é cumprido; nota baixa por violação do requisito central apesar do formato correto
- **TOOL-ACC:** 0 — 0/4 -- nunca executa a leitura real do arquivo
- **CLASS-ACC** (agregado): 4 — severity bate em 4/4 casos, MAS ver ressalva: o nome do arquivo no prompt (ex: critical-001.log) provavelmente vaza a severidade esperada sem necessidade de leitura real -- não é evidência confiável de compreensão
- **PARSE-ACC** (agregado): 0 — primary_issue correto em apenas 1/4 casos (info-001); nos outros 3, host, timestamp e primary_issue são inteiramente fabricados (mesmo timestamp genérico 2023-10-27T14:3X:XXZ reaparece em todos os casos -- sinal claro de template alucinado, não leitura real)
- **SUMMARY-QUAL** (agregado): 2 — textos fluentes e bem formados em PT-BR, mas com conteúdo fabricado em 3/4 casos (host genérico tipo app-server-01/prod-db-01 em vez dos hostnames reais fox-node-XX; primary_issue errado). Só info-001 é genuinamente correto (nota 4); os outros 3 ficam em nota 1 -- média (4+1+1+1)/4 = 1.75 ≈ 2
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Case | Tool chamada | Argumento completo | Tool válida | Leitura OK | Extra calls | class_acc_auto | parse_acc_auto |
|------|-------------|-------------------|-------------|------------|-------------|----------------|----------------|
| info-001 | NENHUMA | `` | None | None | 0 | 4 | 3 |
| warning-001 | NENHUMA | `` | None | None | 0 | 2 | 2 |
| critical-001 | NENHUMA | `` | None | None | 0 | 2 | 2 |
| mixed-001 | NENHUMA | `` | None | None | 0 | 2 | 2 |

## Arquivos de runs

- [`S3-qwen3.6-35b-a3b-nothink-2026-07-05-case-info-001.txt`](S3-qwen3.6-35b-a3b-nothink-2026-07-05-case-info-001.txt)
- [`S3-qwen3.6-35b-a3b-nothink-2026-07-05-case-warning-001.txt`](S3-qwen3.6-35b-a3b-nothink-2026-07-05-case-warning-001.txt)
- [`S3-qwen3.6-35b-a3b-nothink-2026-07-05-case-critical-001.txt`](S3-qwen3.6-35b-a3b-nothink-2026-07-05-case-critical-001.txt)
- [`S3-qwen3.6-35b-a3b-nothink-2026-07-05-case-mixed-001.txt`](S3-qwen3.6-35b-a3b-nothink-2026-07-05-case-mixed-001.txt)

## Próximos passos

- [ ] Ler os 4 arquivos de run e atribuir notas na tabela acima.
- [ ] Avaliar SUMMARY-QUAL manualmente (ler campo `summary` em cada run).
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s3-benchmark.py` em 2026-07-05_