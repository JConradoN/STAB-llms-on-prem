# S2 Summary — qwen3.6-35b-a3b-nothink — 2026-07-05

## Metadados

| Campo                   | Valor                                        |
|-------------------------|----------------------------------------------|
| Cenário                 | S2 – Health check com parsing e JSON         |
| Modelo                  | qwen3.6-35b-a3b-nothink                                      |
| Bateria                 | 1                                            |
| Data                    | 2026-07-05                                   |
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
| 1 | run_bash | `cat ~/scripts/health.sh` | 0 | 4 | 0 | 4 |  0        | False      | 0/13    | True    | False | False       | 1941      | N/A      | N/A   | 0        |     |
| 2 | run_bash | `cat ~/scripts/health.sh` | 0 | 4 | 0 | 4 |  0        | False      | 0/13    | True    | False | False       | 1941      | N/A      | N/A   | 0        |     |
| 3 | run_bash | `cat ~/scripts/health.sh` | 0 | 4 | 0 | 4 |  0        | False      | 0/13    | True    | False | False       | 1941      | N/A      | N/A   | 0        |     |
| 4 | run_bash | `cat ~/scripts/health.sh` | 0 | 4 | 0 | 4 |  0        | False      | 0/13    | True    | False | False       | 1941      | N/A      | N/A   | 0        |     |
| 5 | run_bash | `cat ~/scripts/health.sh` | 0 | 4 | 0 | 4 |  0        | False      | 0/13    | True    | False | False       | 1941      | N/A      | N/A   | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** 4 — comportamento consistente nas 5 execuções — mas consistentemente ERRADO (mesmo comando incorreto, mesma resposta vazia)
- **TOOL-CON:** 4 — sempre escolhe `run_bash`, argumento sempre `cat ~/scripts/health.sh` — consistente, porém comando errado (lê o código-fonte do script em vez de executá-lo)
- **INST:** 0 — resposta final VAZIA em todas as 5 execuções — nem produz o JSON pedido, nem a mensagem de erro alternativa exigida pelo prompt ("ERRO: não consegui executar health.sh"); falha total de aderência à instrução
- **TOOL-ACC:** 0 — comando `cat` em vez de execução real — nunca captura dados reais do sistema, 0/13 campos presentes em todas as 5 execuções. GAP FUNDAMENTAL: escolheu a ferramenta errada para a tarefa (ver nota abaixo sobre config -nothink)
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls | json_acc_auto |
|-----|-------------|-------------------|-------------|---------|-------------|---------------|
| 1 | run_bash | `cat ~/scripts/health.sh` | True | True | 0 | 0 |
| 2 | run_bash | `cat ~/scripts/health.sh` | True | True | 0 | 0 |
| 3 | run_bash | `cat ~/scripts/health.sh` | True | True | 0 | 0 |
| 4 | run_bash | `cat ~/scripts/health.sh` | True | True | 0 | 0 |
| 5 | run_bash | `cat ~/scripts/health.sh` | True | True | 0 | 0 |

## Arquivos de runs

- [`S2-qwen3.6-35b-a3b-nothink-2026-07-05-run1.txt`](S2-qwen3.6-35b-a3b-nothink-2026-07-05-run1.txt)
- [`S2-qwen3.6-35b-a3b-nothink-2026-07-05-run2.txt`](S2-qwen3.6-35b-a3b-nothink-2026-07-05-run2.txt)
- [`S2-qwen3.6-35b-a3b-nothink-2026-07-05-run3.txt`](S2-qwen3.6-35b-a3b-nothink-2026-07-05-run3.txt)
- [`S2-qwen3.6-35b-a3b-nothink-2026-07-05-run4.txt`](S2-qwen3.6-35b-a3b-nothink-2026-07-05-run4.txt)
- [`S2-qwen3.6-35b-a3b-nothink-2026-07-05-run5.txt`](S2-qwen3.6-35b-a3b-nothink-2026-07-05-run5.txt)

## Próximos passos

- [ ] Ler os 5 arquivos de run e atribuir notas na tabela acima.
- [ ] Verificar manualmente os runs com json_acc_auto=-1.
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s2-benchmark.py` em 2026-07-05_