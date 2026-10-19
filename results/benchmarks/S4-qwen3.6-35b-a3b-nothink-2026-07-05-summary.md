# S4 Summary — qwen3.6-35b-a3b-nothink — 2026-07-05

## Metadados

| Campo                   | Valor                                                    |
|-------------------------|----------------------------------------------------------|
| Cenário                 | S4 – Triagem multi-log e decisão de escalonamento        |
| Modelo                  | qwen3.6-35b-a3b-nothink                                                  |
| Bateria                 | 1                                                        |
| Data                    | 2026-07-05                                               |
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
| S4-A | 4          | 4         | True         | True      | True    | True   | True      | 3              | 3164      | N/A      | 0.0   | 0        |     |
| S4-B | 1          | 0         | True         | False     | False   | True   | True      | 0              | 1181      | N/A      | 0.0   | 0        |     |
| S4-C | 1          | 0         | True         | False     | False   | True   | True      | 0              | 1166      | N/A      | 0.0   | 0        |     |

## Notas por dimensão (Bateria 1)

- **TRIAGE-ACC** (agregado): 1 — S4-A perfeito (rank+esc+hosts corretos), mas S4-B e S4-C têm all_hosts_present=False e rank_order_correct=False (2/3 casos com hosts fabricados) — nota 1 ("JSON válido mas hosts faltando em ≥1 caso")
- **CHAIN-ACC** (agregado): 0 — GAP FUNDAMENTAL: 0 chamadas read_file em S4-B e S4-C (2/3 casos) — só S4-A usa o planejamento multi-step de 3 leituras corretamente
- **CON:** 1 — comportamento muito inconsistente entre casos: S4-A correto e grounded, S4-B/S4-C totalmente fabricados sem nenhuma leitura — mesmo padrão de hosts genéricos (db-primary-01, web-app-02, cache-node-01) e timestamp fixo 2023-10-27T14:35:00Z reaparecendo, sinal de template alucinado reciclado do S3
- **INST:** 1 — formato JSON válido nos 3 casos (schema_valid=True sempre), mas em 2/3 o conteúdo é inteiramente inventado — viola o requisito central de ler os 3 logs antes de responder
- **TOOL-CON:** 1 — usa a estratégia certa (3x read_file) em apenas 1/3 casos; nos outros 2, pula a etapa de leitura inteiramente e vai direto para uma resposta fabricada
- **TOOL-ACC:** 1 — sucesso real em apenas 1/3 casos (S4-A); 2/3 nunca tocam os arquivos reais
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Case | read_file calls | loop_exhausted | triage_acc_auto | chain_acc | all_hosts | rank_ok | esc_ok |
|------|----------------|----------------|-----------------|-----------|-----------|---------|--------|
| S4-A | 3 | False | 4 | 4 | True | True | True |
| S4-B | 0 | False | 1 | 0 | False | False | True |
| S4-C | 0 | False | 1 | 0 | False | False | True |

## Arquivos de runs

- [`S4-qwen3.6-35b-a3b-nothink-2026-07-05-case-S4-A.txt`](S4-qwen3.6-35b-a3b-nothink-2026-07-05-case-S4-A.txt)
- [`S4-qwen3.6-35b-a3b-nothink-2026-07-05-case-S4-B.txt`](S4-qwen3.6-35b-a3b-nothink-2026-07-05-case-S4-B.txt)
- [`S4-qwen3.6-35b-a3b-nothink-2026-07-05-case-S4-C.txt`](S4-qwen3.6-35b-a3b-nothink-2026-07-05-case-S4-C.txt)

## Próximos passos

- [ ] Ler os 3 arquivos de run e atribuir notas INST/CON/TOOL-CON/TOOL-ACC.
- [ ] Verificar manualmente a qualidade do campo `acao_geral` em cada run.
- [ ] Executar Bateria 2 após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Atualizar hipóteses H10/H11 com dados S4.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s4-benchmark.py` em 2026-07-05_