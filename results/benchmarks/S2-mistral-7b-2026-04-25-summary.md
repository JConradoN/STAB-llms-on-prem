# S2 Summary — mistral:7b — 2026-04-25

## Metadados

| Campo                   | Valor                                        |
|-------------------------|----------------------------------------------|
| Cenário                 | S2 – Health check com parsing e JSON         |
| Modelo                  | mistral:7b                                      |
| Bateria                 | 1                                            |
| Data                    | 2026-04-25                                   |
| K (runs)                | 5                                          |
| Temperatura             | 0                                |
| API                     | http://localhost:11434/api/chat                             |
| Tool disponível         | run_bash                                     |
| Execução real no host   | sim (subprocess)                             |
| Schema campos           | 13 (timestamp, cpu×2, memoria×4, gpu×6) |
| VRAM disponível início  | _(preencher manualmente)_                    |

## Resultados

Colunas auto: json_valid, campos, tipo_ok, ts_ok, texto_extra, JSON-ACC.
Colunas manuais: INST, TOOL-CON, TOOL-ACC, CON (critérios: ADR-0001).
JSON-ACC=-1: JSON parseável mas com defeito — requer avaliação humana.
Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`
           `docs/benchmarks/S2-health-check-json.md`, seção 6

| Run | Tool | Argumento | INST | TOOL-CON | TOOL-ACC | CON | JSON-ACC | json_valid | campos | tipo_ok | ts_ok | texto_extra | tok_total | ms_total | tok/s | thinking | Obs |
|-----|------|-----------|------|----------|----------|-----|----------|------------|--------|---------|-------|-------------|-----------|----------|-------|----------|-----|
| 1 | NENHUMA | `` |      |          | 0        |     | -1       | True       | 13/13    | True    | True  | True        | 665       | 5536.6   | 69.1  | 0        |     |
| 2 | NENHUMA | `` |      |          | 0        |     | -1       | True       | 13/13    | True    | True  | True        | 665       | 3636.8   | 69.2  | 0        |     |
| 3 | NENHUMA | `` |      |          | 0        |     | -1       | True       | 13/13    | True    | True  | True        | 665       | 3642.1   | 69.2  | 0        |     |
| 4 | NENHUMA | `` |      |          | 0        |     | -1       | True       | 13/13    | True    | True  | True        | 665       | 3637.9   | 69.2  | 0        |     |
| 5 | NENHUMA | `` |      |          | 0        |     | -1       | True       | 13/13    | True    | True  | True        | 665       | 3676.3   | 69.2  | 0        |     |

## Notas por dimensão (Bateria 1)

- **CON:** _(preencher após leitura dos 5 runs)_
- **TOOL-CON:** _(preencher após leitura dos 5 runs)_
- **INST:** _(preencher após leitura dos 5 runs)_
- **TOOL-ACC:** _(preencher após leitura dos 5 runs)_
- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)

## Observações brutas (geradas automaticamente)

| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls | json_acc_auto |
|-----|-------------|-------------------|-------------|---------|-------------|---------------|
| 1 | NENHUMA | `` | None | None | 0 | -1 |
| 2 | NENHUMA | `` | None | None | 0 | -1 |
| 3 | NENHUMA | `` | None | None | 0 | -1 |
| 4 | NENHUMA | `` | None | None | 0 | -1 |
| 5 | NENHUMA | `` | None | None | 0 | -1 |

## Arquivos de runs

- [`S2-mistral-7b-2026-04-25-run1.txt`](S2-mistral-7b-2026-04-25-run1.txt)
- [`S2-mistral-7b-2026-04-25-run2.txt`](S2-mistral-7b-2026-04-25-run2.txt)
- [`S2-mistral-7b-2026-04-25-run3.txt`](S2-mistral-7b-2026-04-25-run3.txt)
- [`S2-mistral-7b-2026-04-25-run4.txt`](S2-mistral-7b-2026-04-25-run4.txt)
- [`S2-mistral-7b-2026-04-25-run5.txt`](S2-mistral-7b-2026-04-25-run5.txt)

## Próximos passos

- [ ] Ler os 5 arquivos de run e atribuir notas na tabela acima.
- [ ] Verificar manualmente os runs com json_acc_auto=-1.
- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.
- [ ] Calcular STAB comparando notas das duas baterias.
- [ ] Avançar para o próximo modelo da shortlist.

---

_Gerado automaticamente por `scripts/run-s2-benchmark.py` em 2026-04-25_