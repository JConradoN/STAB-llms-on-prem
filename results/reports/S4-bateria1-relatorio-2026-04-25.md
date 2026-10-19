# S4 Bateria 1 — Relatório de Resultados

## 1. Cabeçalho

| Campo               | Valor                                                                                     |
|---------------------|-------------------------------------------------------------------------------------------|
| Título              | S4 Bateria 1 — Triagem multi-log, tool-skipping por naming semântico e experimento H12    |
| Data                | 2026-04-25                                                                                |
| Cenário             | S4 – Triagem de múltiplos logs e decisão de escalonamento (Nível 4)                      |
| Hardware            | RTX 3060 12 GB, i5-10400F, 32 GB RAM, Ubuntu 24                                          |
| Script              | `scripts/run-s4-benchmark.py`                                                             |
| Temperatura         | 0                                                                                         |
| K (casos)           | 3 casos distintos por modelo (S4-A, S4-B, S4-C)                                         |
| Tool disponível     | `read_file` (leitura direta via Python — sem subprocess)                                  |
| MAX_TOOL_TURNS      | 4                                                                                         |
| API                 | POST http://localhost:11434/api/chat                                                      |
| Prompt fonte        | `docs/benchmarks/S4-triage-multi-log.md`, seção 4                                        |
| Fixtures usados     | `fixtures/health-logs/info/info-001.log`                                                 |
|                     | `fixtures/health-logs/info/info-003.log`                                                 |
|                     | `fixtures/health-logs/warning/warning-001.log`                                           |
|                     | `fixtures/health-logs/warning/warning-003.log`                                           |
|                     | `fixtures/health-logs/critical/critical-001.log`                                         |
|                     | `fixtures/health-logs/critical/critical-003.log`                                         |
|                     | `fixtures/health-logs/mixed/mixed-001.log`                                               |

**Diferença em relação a S3:** S4 é a primeira avaliação de planejamento multi-step autônomo — o agente deve decidir sozinho que precisa executar 3 chamadas encadeadas de `read_file` antes de produzir a saída. K=3 corresponde a 3 casos distintos: uma de cada severidade (S4-A), três críticos com desempate (S4-B), e sem críticos com desempate por recência (S4-C). O cenário introduz a métrica TRIAGE-ACC e CHAIN-ACC, específicas para a tarefa de triagem multi-log. Durante a bateria foi conduzido o experimento H12 (nomes de arquivo opacos vs. descritivos), documentado em `docs/notes/HYP-0012-tool-skipping-naming-semantico.md`.

---

## 2. Modelos avaliados

| Modelo         | Família  | Tamanho aprox. | Status S3              |
|----------------|----------|----------------|------------------------|
| gemma4:e4b     | Gemma4   | 9,6 GB         | passou (4/4/4/4/4/4)  |
| qwen3.5:9b     | Qwen3.5  | 6,6 GB         | parcial (INST=2, CON=2)|
| qwen3:14b      | Qwen3    | 9,3 GB         | passou (4/4/4/4/4/4)  |

**Nota:** qwen3.5:2b continua aguardando re-run S2B após correção do bug de captura. Não avança para S4 até conclusão da etapa anterior.

---

## 3. Resultados por modelo

Notas atribuídas com base na leitura dos 9 arquivos de case (3 por modelo).
Escala 0–4 conforme `docs/decisions/ADR-0001-criterios-de-avaliacao.md`.
Fatos observados e inferências separados.

---

### 3.1 gemma4:e4b

**Formato de saída:** JSON minificado (uma linha), sem markdown, sem texto adicional, em todos os 3 casos.
_(Fonte: seção "RESPOSTA FINAL DO MODELO" dos 3 case files gemma4.)_

**TRIAGE-ACC: 4**
- Fato: `rank_order_correct=True`, `escalation_correct=True`, `all_hosts_present=True`, `schema_valid=True`, `acao_geral_present=True` em 3/3 casos. `triage_acc_auto=4` em todos. _(Fonte: seção "VALIDAÇÃO DETALHADA" dos 3 case files.)_

**CHAIN-ACC: 4**
- Fato: `read_file` chamada 3 vezes em todos os 3 casos. Todas as chamadas no Turno 1 (execução paralela). `loop_exhausted=False` em 3/3 casos. _(Fonte: seção "TOOL CALLS DO MODELO" dos 3 case files.)_

**TOOL-ACC: 4**
- Fato: `read_file` chamada com caminho absoluto correto do fixture em 9/9 chamadas (3 por caso); `Sucesso: True` em todas. _(Confirmado em todos os case files.)_

**TOOL-CON: 4**
- Fato: mesma tool (`read_file`), mesmo padrão de argumento (caminho absoluto), 3 chamadas por caso, em 3/3 casos. _(Confirmado nos 3 case files.)_

**INST: 4**
- Fato: resposta final em JSON puro (sem markdown) em 3/3 casos. _(Confirmado nos case files, seção "RESPOSTA FINAL DO MODELO".)_
- Fato: todos os 10 pontos do checklist INST S4 passam em 3/3 casos: `triage_id` correto, `hosts_analisados=3`, `prioridade` lista de 3 itens com ranks 1/2/3, `severity` e `escalation` enums válidos, `primary_issue` do vocabulário controlado, `summary` em PT-BR por host, `timestamp_triage` ISO 8601 com Z, `acao_geral` não vazia. _(Confirmado na seção "VALIDAÇÃO DETALHADA" dos 3 case files.)_

**CON: 4**
- Fato: formato de saída idêntico em 3/3 casos (JSON minificado, sem markdown); severity ↔ escalation coerente; rank sem duplicatas; timestamp_triage correto em 3/3 casos. _(Confirmado nos 3 case files.)_
- Observação: thinking T2 varia entre casos (S4-A=0, S4-B=0, S4-C=4314 chars). Variação é de processo interno, não de formato de output. CON avalia a consistência do output, não do raciocínio interno. CON=4 se mantém.

**Observação de conteúdo (não afeta score):**
- Fato: em S4-A, gemma4 atribuiu `primary_issue=elevated_application_latency` para warning-001 (fox-node-02). O expected é `high_cpu_usage`. Ambos são do vocabulário controlado; o log warning-001 contém ambos os issues. A ordenação dos hosts está correta (TRIAGE-ACC=4). _(Fonte: case S4-A, seção "RESPOSTA FINAL DO MODELO"; S4-triage-multi-log.md seção 5.)_
- Fato: em S4-B, gemma4 atribuiu `primary_issue=database_unavailable` para fox-node-03 (critical-001). O expected é `disk_critical_on_var`. Rank está correto. _(Fonte: case S4-B.)_

| Dimensão    | Nota | Base factual                                                        |
|-------------|------|---------------------------------------------------------------------|
| TRIAGE-ACC  | 4    | rank_ok + esc_ok + all_hosts em 3/3 casos                         |
| CHAIN-ACC   | 4    | 3 read_file calls em 3/3 casos                                     |
| TOOL-ACC    | 4    | read_file, caminho correto, sucesso=True em 9/9 chamadas           |
| TOOL-CON    | 4    | Mesma tool, mesmo padrão, 3 calls em 3/3 casos                     |
| INST        | 4    | JSON puro, todos os 10 pontos INST em 3/3 casos                    |
| CON         | 4    | Formato idêntico, escalation coerente, timestamp correto em 3/3    |

---

### 3.2 qwen3.5:9b

**Formato de saída:** variável entre casos — inconsistência de formato é o achado central para este modelo, replicando o padrão observado em S3.
_(Fato: observado diretamente nas seções "RESPOSTA FINAL DO MODELO" dos 3 case files.)_

| Caso | Formato observado                                |
|------|--------------------------------------------------|
| S4-A | JSON indentado, COM wrapper ` ```json ... ``` ` ✗ |
| S4-B | JSON indentado, COM wrapper ` ```json ... ``` ` ✗ |
| S4-C | JSON minificado, sem markdown ✓                  |

**TRIAGE-ACC: 4**
- Fato: `rank_order_correct=True`, `escalation_correct=True`, `all_hosts_present=True`, `schema_valid=True` em 3/3 casos. `triage_acc_auto=4` em todos. _(Fonte: seções "VALIDAÇÃO DETALHADA" dos 3 case files.)_
- Fato: o parser do script extrai JSON válido mesmo dos casos com markdown wrapper. `json_valid=True` em 3/3 casos. A violação é de formato, não de conteúdo.

**CHAIN-ACC: 4**
- Fato: `read_file` chamada 3 vezes em 3/3 casos. Todas as chamadas no Turno 1. `loop_exhausted=False` em 3/3 casos. _(Confirmado nos 3 case files.)_

**TOOL-ACC: 4**
- Fato: `read_file` chamada com caminho absoluto correto em 9/9 chamadas; `Sucesso: True` em todas. _(Confirmado nos 3 case files.)_

**TOOL-CON: 4**
- Fato: mesma tool, mesmo padrão de argumento, 3 chamadas por caso, em 3/3 casos. _(Confirmado nos 3 case files.)_

**INST: 2**
- Fato: o ponto "JSON puro, sem markdown" falha em 2/3 casos (S4-A e S4-B com ` ```json ` wrapper). Mesmo resultado que em S3 com instrução equivalente. _(Confirmado nos case files S4-A e S4-B.)_
- Fato: os outros 9 pontos do checklist INST passam em 3/3 casos. _(Confirmado em "VALIDAÇÃO DETALHADA".)_

**CON: 2**
- Fato: formato varia entre casos (2 com markdown wrapper, 1 JSON minificado sem markdown). _(Confirmado nos 3 case files.)_
- Critério: variação estrutural (não apenas de "detalhes de redação") em 2/3 casos.

**Observação de conteúdo:**
- Fato: em S4-B, qwen3.5:9b atribuiu `primary_issue=database_unavailable` para fox-node-03 (critical-001), mesmo que o expected seja `disk_critical_on_var`. Padrão idêntico ao gemma4 no mesmo caso. Rank correto.

| Dimensão    | Nota | Base factual                                                        |
|-------------|------|---------------------------------------------------------------------|
| TRIAGE-ACC  | 4    | rank_ok + esc_ok + all_hosts em 3/3 casos                         |
| CHAIN-ACC   | 4    | 3 read_file calls em 3/3 casos                                     |
| TOOL-ACC    | 4    | read_file, caminho correto, sucesso=True em 9/9 chamadas           |
| TOOL-CON    | 4    | Mesma tool, mesmo padrão em 3/3 casos                              |
| INST        | **2**| Markdown wrapper em 2/3 casos, violando "JSON puro"                |
| CON         | **2**| Formato varia entre casos: indented+markdown / minificado           |

---

### 3.3 qwen3:14b

**Achado central:** qwen3:14b é o único modelo da bateria que falhou em executar tool calls quando esperado. Não chamou `read_file` nos casos S4-A e S4-C, gerando alucinação completa dos dados. Chamou corretamente em S4-B mas cometeu erro de desempate.

**TRIAGE-ACC: 1**
- Fato S4-A: `all_hosts_present=False`, `rank_order_correct=False`. Hosts gerados: `host-critical-001`, `host-warning-001`, `host-info-001` (inventados). `triage_acc_auto=1`. _(Fonte: case S4-A, seção "VALIDAÇÃO DETALHADA".)_
- Fato S4-A: `timestamp_triage` gerado: `"2023-10-05T14:30:00Z"` (ano 2023, fabricado). O correto seria `"2026-04-24T16:44:25Z"`.
- Fato S4-B: `all_hosts_present=True`, `rank_order_correct=False`. Hosts presentes mas ordem errada: fox-node-10 > fox-node-04 > fox-node-03. Esperado: fox-node-03 > fox-node-10 > fox-node-04. `triage_acc_auto=3`. _(Fonte: case S4-B.)_
- Fato S4-C: `all_hosts_present=False`, `rank_order_correct=False`. Hosts gerados: `host-critical-001` (para case_id `info-001`, severity=critical — alucinação grave), `host-warning-003`, `host-info-003`. `triage_acc_auto=1`. `timestamp_triage`: `"2023-11-15T14:30:00Z"` (fabricado). _(Fonte: case S4-C.)_
- Critério TRIAGE-ACC=1: JSON válido produzido, mas hosts faltando ou errados em ≥1 caso. Dois casos com `all_hosts_present=False`.

**CHAIN-ACC: 0**
- Fato: `read_file` chamada 0 vezes em S4-A e S4-C; 3 vezes em S4-B. `chain_acc_auto=0` para S4-A e S4-C. _(Confirmado nos 3 case files.)_
- Critério: qualquer caso com ≠3 chamadas → CHAIN-ACC=0.

**TOOL-ACC: 1**
- Fato: nenhuma chamada de tool em S4-A e S4-C (0/6 chamadas esperadas não realizadas). 3 chamadas corretas em S4-B. _(Confirmado nos 3 case files.)_
- TOOL-ACC=1: tool correta em apenas 1/3 casos; falha de execução completa em 2/3 casos.

**TOOL-CON: 1**
- Fato: comportamento radicalmente inconsistente — 0 chamadas em S4-A, 3 chamadas em S4-B, 0 chamadas em S4-C. Nenhum padrão estável. _(Confirmado nos 3 case files.)_

**INST: 2**
- Fato: formato JSON puro (sem markdown) em 3/3 casos — a instrução de formato foi seguida. _(Confirmado nos 3 case files.)_
- Fato: a instrução central do prompt ("Use a tool read_file para ler cada arquivo") foi violada em S4-A e S4-C, onde nenhuma chamada foi executada. _(Confirmado: seção "TOOL CALLS DO MODELO" = 0 em ambos.)_
- Critério: desvio em instrução central (uso obrigatório de tool) em 2/3 casos. INST=2.

**CON: 1**
- Fato: comportamento estruturalmente inconsistente entre os 3 casos — alucinação completa em 2/3, tentativa parcialmente correta em 1/3. _(Confirmado nos 3 case files.)_
- Inferência: o modelo não tem padrão estável de comportamento em S4: a variável que determina se ele chama a tool ou não (o naming dos fixtures) é externa ao prompt e ao modelo. O comportamento é previsível dado o mecanismo, mas imprevisível do ponto de vista operacional.

**Observação sobre S4-C:**
- Fato: o modelo gerou `"host": "host-critical-001"` para o arquivo `info-001.log` com `"severity": "critical"`. O arquivo info-001 não contém nenhuma linha CRITICAL. _(Confirmado: case S4-C, campo "RESPOSTA FINAL DO MODELO"; definição de fixtures em S4-triage-multi-log.md seção 5.)_
- Inferência: o modelo parece ter ativado um padrão de memória de treinamento ("host-critical-001") ao processar o case_id "info-001", possivelmente confundindo a sequência numérica com hosts de treinamento. A alucinação não é aleatória — tem estrutura de nomenclatura plausível.

**Observação sobre S4-B:**
- Fato: o modelo leu os 3 arquivos corretamente mas atribuiu `primary_issue=disk_critical_on_var` para fox-node-10 (critical-003), enquanto o expected é `redis_service_failed` primary + `disk_critical_on_var` secondary. O modelo inverteu primary e secondary para esse host. _(Confirmado: case S4-B, "RESPOSTA FINAL DO MODELO" vs. S4-triage-multi-log.md seção 5.)_
- Fato: como consequência da inversão, fox-node-10 foi ranqueado como rank 1 (disk_critical_on_var primary) em vez de fox-node-03. O rank_order_correct=False. _(Confirmado: case S4-B, seção "VALIDAÇÃO DETALHADA".)_

| Dimensão    | Nota | Base factual                                                            |
|-------------|------|-------------------------------------------------------------------------|
| TRIAGE-ACC  | **1**| hosts ausentes/incorretos em 2/3 casos; rank errado em 3/3 casos       |
| CHAIN-ACC   | **0**| 0 chamadas em S4-A e S4-C; 3 em S4-B — critério: qualquer ≠3 → 0     |
| TOOL-ACC    | **1**| Correta apenas em S4-B; 0 chamadas em S4-A e S4-C                     |
| TOOL-CON    | **1**| Comportamento radicalmente inconsistente entre casos                    |
| INST        | **2**| Formato JSON puro ✓ em 3/3; instrução "use read_file" violada em 2/3  |
| CON         | **1**| Sem padrão estável; alucinação em 2/3 casos                            |

---

### 3.4 Resumo das notas — S4 Bateria 1

| Modelo         | TRIAGE-ACC | CHAIN-ACC | TOOL-ACC | TOOL-CON | INST | CON | Resultado   |
|----------------|-----------|-----------|----------|----------|------|-----|-------------|
| gemma4:e4b     | 4         | 4         | 4        | 4        | 4    | 4   | **passou**  |
| qwen3.5:9b     | 4         | 4         | 4        | 4        | **2**| **2**| **parcial** |
| qwen3:14b      | **1**     | **0**     | **1**    | **1**    | **2**| **1**| **reprovado** |

---

## 4. Métricas de performance

Médias calculadas sobre os 3 casos (S4-A, S4-B, S4-C). Nota metodológica: K=3 corresponde a 3 casos distintos — nenhum é repetição do mesmo input. Não há exclusão por cold start nesta bateria.

### 4.1 Tabela por modelo (médias dos 3 casos)

| Modelo         | tok/s médio | ms/caso médio | tok_total médio | thinking médio/caso |
|----------------|-------------|---------------|-----------------|---------------------|
| gemma4:e4b     | 70,2        | 30 151        | 3 899           | 3 563               |
| qwen3.5:9b     | 45,8        | 29 771        | 3 738           | 1 981               |
| qwen3:14b      | 32,9        | 47 523        | 2 609           | 4 465               |

_(Tabela ordenada por tok/s decrescente.)_

**Cálculos detalhados:**

**gemma4:e4b:**
- tok/s: (71,5 + 71,0 + 68,2) / 3 = **70,2**
- ms: (33 968,0 + 17 413,6 + 39 069,9) / 3 = **30 151**
- tokens: (3 422 + 3 430 + 4 846) / 3 = **3 899**
- thinking total por caso: (2 069 + 2 126 + 6 494) / 3 = **3 563**

**qwen3.5:9b:**
- tok/s: (46,0 + 45,9 + 45,6) / 3 = **45,8**
- ms: (25 296,0 + 15 747,8 + 48 270,4) / 3 = **29 771**
- tokens: (3 240 + 3 252 + 4 722) / 3 = **3 738**
- thinking total por caso: (359 + 353 + 5 230) / 3 = **1 981**

**qwen3:14b:**
- tok/s: (33,3 + 32,1 + 33,2) / 3 = **32,9**
- ms: (35 870,3 + 79 118,9 + 27 580,5) / 3 = **47 523**
- tokens: (1 516 + 4 759 + 1 553) / 3 = **2 609**
- thinking total por caso: (2 653 + 8 025 + 2 717) / 3 = **4 465**

_(Nota: tokens baixos do qwen3:14b refletem S4-A e S4-C com apenas 1 turno — o modelo não executou tool calls e encerrou em ~1 500 tokens. S4-B com 3 tool calls gerou 4 759 tokens.)_

### 4.2 Thinking por modelo e caso

| Modelo         | S4-A                     | S4-B                      | S4-C                      |
|----------------|--------------------------|---------------------------|---------------------------|
| gemma4:e4b     | T1=2069, T2=0 (tot=2069) | T1=2126, T2=0 (tot=2126)  | T1=2180, T2=4314 (tot=6494)|
| qwen3.5:9b     | T1=359, T2=0 (tot=359)   | T1=353, T2=0 (tot=353)    | T1=359, T2=4871 (tot=5230) |
| qwen3:14b      | T1=2653, T2=0 (tot=2653) | T1=2212, T2=5813 (tot=8025)| T1=2717, T2=0 (tot=2717)  |

_(Fonte: seção "PERFORMANCE POR TURNO" de cada case file.)_

**Observação crítica:** qwen3:14b não produziu T2 nos casos S4-A e S4-C porque não executou tool calls — o run completou em um único turno. Em S4-B, onde executou 3 tool calls, produziu T2=5813 chars — o maior T2 registrado em toda a bateria S1–S4.

---

## 5. Experimento H12 — Tool-skipping por naming semântico

_(Referência completa: `docs/notes/HYP-0012-tool-skipping-naming-semantico.md`)_

### 5.1 Hipótese

Modelos com maior capacidade de inferência contextual tendem a pular tool calls quando o prompt contém pistas semânticas suficientes para inferir a resposta sem executar as ferramentas disponíveis. O nome dos arquivos no prompt é uma forma de pista semântica.

### 5.2 Evidência observada em S4-A (nomes descritivos)

- Arquivos no prompt: `info-001.log`, `warning-001.log`, `critical-001.log`
- Pista semântica: os nomes revelam diretamente a severidade de cada arquivo
- **qwen3:14b:** read_file calls = 0; JSON gerado com hosts inventados (`host-critical-001`, `host-warning-001`, `host-info-001`) e timestamp de 2023; CHAIN-ACC=0, TRIAGE-ACC=1
- Fato: o modelo produziu a triagem "correta" em termos de ordenação (critical > warning > info) mas com dados completamente fabricados, incluindo timestamp de 2023 e hostnames não existentes nos fixtures. _(Fonte: case S4-A, seção "RESPOSTA FINAL DO MODELO".)_

**Controle:** gemma4:e4b e qwen3.5:9b executaram 3 read_file calls no mesmo caso S4-A com os mesmos nomes de arquivo, sem tool-skipping. _(Fonte: cases S4-A de ambos os modelos.)_

### 5.3 Evidência do experimento H12 (nomes opacos — mesmos conteúdos)

_(Os fixtures com nomes opacos foram criados especificamente para este experimento, documentados em `fixtures/h12-opaque-names/`.)_

- Arquivos no prompt: `log-alpha.log`, `log-beta.log`, `log-gamma.log`
- Conteúdo: idêntico aos fixtures de S4-A (info-001, warning-001, critical-001 respectivamente)
- **qwen3:14b:** read_file calls = 3; thinking observado: _"Let me start by reading each file one by one"_; triagem correta com hosts reais e timestamp correto; CHAIN-ACC=4
- Variável isolada: apenas o nome dos arquivos no prompt foi alterado. Conteúdo dos logs, prompt de sistema, schema, tool disponível e temperatura foram idênticos nos dois cenários.

### 5.4 Experimento de mitigação — instrução explícita com nomes descritivos

- Configuração: mesmo prompt S4-A com nomes descritivos (`info-001.log`, `warning-001.log`, `critical-001.log`) + instrução adicionada ao prompt:

  > _"ATENÇÃO: Você DEVE usar a tool read_file para ler CADA arquivo antes de qualquer análise. Não infira o conteúdo pelos nomes dos arquivos. Leia os arquivos primeiro."_

- **qwen3:14b:** read_file calls = 3; thinking observado: _"The user emphasized not to infer the content from the filenames, so I need to read each one."_; triagem correta. CHAIN-ACC=4.

### 5.5 Conclusão H12

**Fato:** o tool-skipping do qwen3:14b em S4-A e S4-C foi causado pelo naming semântico dos fixtures, não por falha estrutural de tool use do modelo. Com nomes opacos ou instrução explícita de leitura obrigatória, o modelo executou as 3 tool calls corretamente.

**Fato:** a variável causal isolada é o nome do arquivo no prompt — tudo o mais mantido constante.

**Fato:** modelos menores (qwen3.5:9b, gemma4:e4b) não apresentaram tool-skipping em S4-A com nomes descritivos, executando as 3 chamadas corretamente.

**Inferência:** o qwen3:14b, com maior volume de conhecimento implícito de treinamento, reconhece os padrões semânticos nos nomes como pistas suficientes para inferência direta, evitando a execução das tools. Modelos menores possivelmente têm menos confiança no conhecimento implícito e seguem a instrução literal. A mitigação mais simples e eficaz é a instrução explícita de leitura obrigatória diretamente no prompt.

---

## 6. Análises e achados

### 6.1 Por que S4-B funcionou no qwen3:14b mas S4-A e S4-C não

**Fatos:**
- S4-A fixtures: `info-001.log`, `warning-001.log`, `critical-001.log` — nomes revelam severidade distinta
- S4-B fixtures: `critical-001.log`, `critical-003.log`, `mixed-001.log` — nomes não permitem inferir rank
- S4-C fixtures: `info-001.log`, `info-003.log`, `warning-003.log` — nomes revelam 1 warning + 2 infos
- read_file calls: S4-A=0, S4-B=3, S4-C=0. _(Fonte: summaries e case files.)_

**Inferência:** em S4-A, o modelo infere corretamente a ordem `critical > warning > info` a partir dos nomes, sem necessidade de leitura. Em S4-C, o modelo infere que `warning > info` a partir dos nomes, mas não consegue resolver o desempate entre os dois infos por recência — mesmo assim não lê os arquivos, gerando alucinação. Em S4-B, os nomes `critical-001`, `critical-003`, `mixed-001` não permitem inferir rank (todos são "pesados"); o desempate exige conteúdo real dos logs. O modelo então executa as 3 chamadas.

**Inferência:** o threshold de tool-skipping parece ser determinado pela certeza percebida de que a resposta pode ser inferida, não pela complexidade residual do problema. Em S4-C o modelo alucinouencontrado apesar de haver uma etapa de desempate que ele não resolveria sem ler os arquivos.

### 6.2 Thinking T2 em S4-C: novo comportamento para gemma4:e4b e qwen3.5:9b

**Fato:** gemma4:e4b produziu T2=0 em todos os 4 casos de S3 e em S4-A e S4-B. Em S4-C, produziu T2=4314 chars. _(Fonte: case files S3-gemma4 e S4-gemma4-case-S4-C.txt.)_

**Fato:** qwen3.5:9b produziu T2=0 em todos os 4 casos de S3 e em S4-A e S4-B. Em S4-C, produziu T2=4871 chars — o maior T2 deste modelo em toda a série S1–S4. _(Fonte: case S4-qwen3.5-9b-case-S4-C.txt.)_

**Fato:** S4-C é o único caso da bateria que exige desempate entre dois hosts de mesma severidade (info-001 e info-003) por recência de timestamp — a regra mais sutil e menos explícita da especificação S4. _(Fonte: S4-triage-multi-log.md seção 5, regras de ordenação.)_

**Inferência:** o T2 thinking em S4-C para gemma4 e qwen3.5:9b está diretamente associado à complexidade do raciocínio de desempate por recência. Casos onde a ordenação é trivial (S4-A: trivial por severity; S4-B: desempate por primary_issue) não induziram T2>0 nesses modelos. O caso de desempate por timestamp exigiu deliberação adicional no turno de síntese.

**Atualização de H11:** a hipótese H11 (thinking T2 como característica exclusiva do qwen3:14b) é refutada pelos dados S4. gemma4:e4b e qwen3.5:9b também produzem T2>0 quando a complexidade de raciocínio no turno de síntese é suficientemente alta. T2 thinking é um fenômeno de complexidade de tarefa, não de arquitetura exclusiva do 14b.

### 6.3 Thinking T2 massivo do qwen3:14b em S4-B (8025 chars)

**Fato:** qwen3:14b produziu thinking total de 8025 chars em S4-B (T1=2212 + T2=5813). É o maior thinking total registrado para qualquer modelo em qualquer caso da série S1–S4. _(Fonte: case S4-qwen3-14b-case-S4-B.txt, seção "PERFORMANCE POR TURNO".)_

**Fato:** apesar do T2 massivo, o modelo cometeu erro de rank em S4-B (fox-node-10 ranqueado acima de fox-node-03). _(Fonte: case S4-B, seção "VALIDAÇÃO DETALHADA": `rank_order_correct=False`.)_

**Inferência:** o thinking extenso não garantiu acerto. A hipótese H11 de que T2 funciona como mecanismo de verificação que *garante* qualidade precisa ser revisada: T2 indica deliberação mais intensa, mas não correção. Em S4-B, o modelo deliberou mais (T2=5813) sobre um problema cujas regras de desempate ele não resolveu corretamente (inverteu primary e secondary do critical-003).

### 6.4 Padrão primary_issue em S4-B: divergência sistemática entre expected e modelos

**Fato:** gemma4:e4b e qwen3.5:9b atribuíram `primary_issue=database_unavailable` para fox-node-03 (critical-001) em S4-B. O expected é `disk_critical_on_var`. Ambos os modelos acertaram o rank (fox-node-03 = rank 1) mas erraram o primary_issue. _(Fonte: cases S4-B de ambos os modelos, seção "RESPOSTA FINAL DO MODELO" vs. S4-triage-multi-log.md seção 5.)_

**Fato:** os mesmos modelos, no caso S4-A (que também inclui critical-001), atribuíram corretamente `primary_issue=disk_critical_on_var` para fox-node-03. _(Fonte: cases S4-A dos dois modelos.)_

**Inferência:** no contexto de S4-B (todos os hosts são critical), os modelos parecem priorizar o efeito final mais visível (banco de dados indisponível) como primary em vez da causa raiz (disco cheio). No contexto de S4-A (mixed severity), com menos ambiguidade de contexto, identificam a causa raiz corretamente. Este fenômeno pode refletir que o raciocínio sobre primary_issue é sensível ao contexto de comparação entre os hosts.

### 6.5 Atualização de H10 com dados S4

**H10 revisada:** a ortogonalidade entre acurácia semântica e conformidade de formato, observada em S1–S3, se confirma e se expande em S4. S4 adiciona uma terceira dimensão ortogonal: **conformidade de tool use**.

- gemma4:e4b: acurácia=4, formato=4, tool use=4 (todas as dimensões altas e independentes)
- qwen3.5:9b: acurácia=4, formato=2, tool use=4 (formato baixo não afeta acurácia nem tool use)
- qwen3:14b: acurácia altamente variável (0 em S4-A/C, parcial em S4-B), formato=puro em 3/3, tool use=0/3 casos

**Fato que suporta:** qwen3:14b seguiu o formato JSON puro (sem markdown) em 3/3 casos — inclusive em S4-A e S4-C onde não executou nenhuma tool call. A conformidade de formato foi perfeita, mas o comportamento de tool use falhou em 2/3 casos. São dimensões independentes.

---

## 7. Classificação final S4

| Modelo         | TRIAGE-ACC | CHAIN-ACC | TOOL-ACC | TOOL-CON | INST | CON | tok/s | ms/caso | Avança para S5?     |
|----------------|-----------|-----------|----------|----------|------|-----|-------|---------|---------------------|
| gemma4:e4b     | 4         | 4         | 4        | 4        | 4    | 4   | 70,2  | 30 151  | **sim**             |
| qwen3.5:9b     | 4         | 4         | 4        | 4        | **2**| **2**| 45,8 | 29 771  | **condicionado**    |
| qwen3:14b      | **1**     | **0**     | **1**    | **1**    | **2**| **1**| 32,9 | 47 523  | **não** (bloqueado) |

**Justificativas:**

- **gemma4:e4b:** aprovado sem ressalvas. Quarta bateria consecutiva com todas as dimensões em 4/4. Referência estável do laboratório. Registrou T2>0 em S4-C pela primeira vez — fenômeno esperado pela atualização de H11 (T2 responde a complexidade de tarefa, não é exclusivo do 14b).

- **qwen3.5:9b:** parcial — aprovado em acurácia (TRIAGE-ACC=4, CHAIN-ACC=4, TOOL-ACC=4), reprovado em formato (INST=2, CON=2). Padrão idêntico ao S3: o modelo lê os arquivos corretamente, ordena corretamente, mas não segue a instrução de formato JSON puro. Para avançar, requer instrução de formato reforçada (nível S2B: "A resposta começa com { e termina com }.").

- **qwen3:14b:** reprovado. CHAIN-ACC=0 é bloqueante: o cenário S4 exige 3 tool calls em todos os casos como condição necessária. O modelo falhou em 2/3 casos por tool-skipping induzido por naming semântico. A causa foi identificada (H12 confirmada) e a mitigação existe (instrução explícita), mas o comportamento sem mitigação é inaceitável para produção. Pode re-run após inclusão da instrução de mitigação H12 no prompt.

---

## 8. Comparação acumulada S1 → S2 → S3 → S4

### 8.1 Notas por dimensão e cenário

_Dimensões comparáveis entre cenários: TOOL-ACC, TOOL-CON, INST, CON. Dimensões de acurácia variam por cenário: S2=JSON-ACC, S3=CLASS-ACC+PARSE-ACC, S4=TRIAGE-ACC+CHAIN-ACC._

| Modelo     | Cenário | TOOL-ACC | TOOL-CON | INST | CON | Acurácia conteúdo                         |
|------------|---------|----------|----------|------|-----|-------------------------------------------|
| gemma4:e4b | S1      | 4        | 4        | 4    | 4   | n/a                                       |
| gemma4:e4b | S2      | 4        | 4        | 4    | 4   | JSON-ACC=4                                |
| gemma4:e4b | S3      | 4        | 4        | 4    | 4   | CLASS-ACC=4, PARSE-ACC=4                  |
| gemma4:e4b | S4      | 4        | 4        | 4    | 4   | TRIAGE-ACC=4, CHAIN-ACC=4                 |
| qwen3:14b  | S1      | 4        | 4        | 4    | 4   | n/a                                       |
| qwen3:14b  | S2      | 4        | 4        | 4    | 4   | JSON-ACC=4                                |
| qwen3:14b  | S3      | 4        | 4        | 4    | 4   | CLASS-ACC=4, PARSE-ACC=4                  |
| qwen3:14b  | S4      | **1**    | **1**    | **2**| **1**| TRIAGE-ACC=**1**, CHAIN-ACC=**0**        |
| qwen3.5:9b | S1      | 4        | 4        | 4    | 4   | n/a                                       |
| qwen3.5:9b | S2 orig | **0**    | 4        | **0**| **0**| JSON-ACC=**0**                           |
| qwen3.5:9b | S2B     | 4        | 4        | 4    | 4   | JSON-ACC=4                                |
| qwen3.5:9b | S3      | 4        | 4        | **2**| **2**| CLASS-ACC=4, PARSE-ACC=4                 |
| qwen3.5:9b | S4      | 4        | 4        | **2**| **2**| TRIAGE-ACC=4, CHAIN-ACC=4                |

_(S2 orig = prompt original; S2B = prompt refinado com tool explícita e restrições de formato fortes.)_

### 8.2 Performance por cenário e modelo

| Modelo         | Cenário | tok/s | ms/run médio | thinking médio/caso  |
|----------------|---------|-------|--------------|----------------------|
| gemma4:e4b     | S1      | 73,0  | 8 202        | 955 (T1)             |
| gemma4:e4b     | S2      | 72,9  | 8 586        | 1 052 (T1)           |
| gemma4:e4b     | S3      | 72,8  | 8 061        | 1 207 (T1) + 0 (T2)  |
| gemma4:e4b     | S4      | 70,2  | 30 151       | 3 563 (T1+T2)        |
| qwen3:14b      | S1      | 33,8  | 30 053       | 3 064 (T1+T2)        |
| qwen3:14b      | S2      | 33,4  | 52 085       | 6 199 (T1+T2)        |
| qwen3:14b      | S3      | 33,5  | 28 134       | 2 909 (T1+T2)        |
| qwen3:14b      | S4      | 32,9  | 47 523       | 4 465 (T1+T2)        |
| qwen3.5:9b     | S1      | 46,4  | 9 307        | 278 (T1)             |
| qwen3.5:9b     | S2B     | 46,4  | 5 712        | 195 (T1)             |
| qwen3.5:9b     | S3      | 46,2  | 8 406*       | 515 (T1) + 0 (T2)    |
| qwen3.5:9b     | S4      | 45,8  | 29 771       | 1 981 (T1+T2)        |

_* S3: média excluindo info-001 com cold start de 17 487 ms._

**Observação sobre latência em S4:** o ms/run médio do S4 é substancialmente maior que S1–S3 para gemma4 e qwen3.5:9b (~30 000 ms vs. ~8 000 ms). Isso é esperado: S4 exige 4 turnos de API por caso (3 tool calls + resposta final) vs. 2 turnos em S3. O tok/s permanece estável (hardware-bound), confirmando que o aumento de latência é proporcional ao número de tokens gerados em 4 turnos.

**Observação sobre qwen3:14b S4:** a latência de 47 523 ms é distorcida pelo caso S4-B (79 119 ms — 3 tool calls + T2 massivo de 5 813 chars). Os casos S4-A e S4-C foram mais rápidos (35 870 ms e 27 581 ms) por não executar tool calls, mas produziram dados inválidos.

---

## 9. Implicações para o laboratório e design de agentes

### 9.1 Tool-skipping como anti-pattern documentado

**Implicação prática (H12 confirmada):** nomes de arquivo semanticamente reveladores em prompts de tool use podem induzir modelos maiores a pular chamadas de tool. Isso afeta qualquer agente que receba paths de arquivo como parte do prompt.

**Recomendação para design:** ao construir agentes on-prem com tool use baseado em leitura de arquivos:
1. Usar nomes opacos (UUIDs, hashes, IDs sequenciais sem semântica) quando possível
2. Se os nomes não puderem ser alterados, adicionar instrução explícita de leitura obrigatória: "Você DEVE ler cada arquivo antes de qualquer conclusão. Não infira o conteúdo pelo nome."
3. O fenômeno é mais provável em modelos maiores e mais capazes — modelos menores seguem a instrução literal com mais fidelidade

**Fato:** a mitigação por instrução explícita foi validada experimentalmente em H12 (qwen3:14b executou 3 calls corretamente com instrução adicionada ao prompt S4-A com nomes descritivos).

### 9.2 Posição consolidada de gemma4:e4b

**Fato:** gemma4:e4b obteve TOOL-ACC=4, TOOL-CON=4, INST=4, CON=4 em S1, S2, S3 e S4 — quatro baterias consecutivas com todas as dimensões máximas. Adicionalmente, TRIAGE-ACC=4 e CHAIN-ACC=4 em S4.

**Inferência:** gemma4:e4b é o modelo de referência do laboratório. Nenhum cenário testado até agora revelou falha em nenhuma dimensão. É o único modelo que chegou ao nível 4 (multi-step autônomo) sem regressão em nenhuma métrica.

### 9.3 Fragilidade do qwen3:14b em contexto de tool use com naming semântico

**Fato:** qwen3:14b passou S1, S2 e S3 com 4/4 em todas as dimensões. Em S4, CHAIN-ACC=0 por tool-skipping em 2/3 casos. A falha não é estrutural (o modelo é capaz de executar tool calls, como demonstrado em S4-B e H12) — é contextual e depende de pistas semânticas no prompt.

**Inferência:** o qwen3:14b tem alto risco de tool-skipping em pipelines de produção onde os nomes de recursos (arquivos, endpoints, chaves) sejam semanticamente reveladores. Qualquer agente construído com este modelo deve incluir instrução de leitura obrigatória no prompt de sistema.

### 9.4 Estabilidade do qwen3.5:9b: consistência em tool use, instabilidade em formato

**Fato:** qwen3.5:9b manteve TOOL-ACC=4 e CHAIN-ACC=4 em S4 — o modelo lê todos os arquivos corretamente, encadeia 3 chamadas e produz triagem semanticamente correta. O bloqueio é exclusivamente de formato (markdown wrapper em 2/3 casos), replicando S3.

**Implicação:** para uso em produção com saída JSON, qwen3.5:9b requer instrução de formato explícita e forte em cada invocação. O mecanismo de formatação não está consolidado — instrução moderada não é suficiente.

### 9.5 T2 thinking como indicador de complexidade de tarefa (não de arquitetura)

**Fato:** em S4-C, gemma4:e4b e qwen3.5:9b produziram T2>0 pela primeira vez (4314 e 4871 chars respectivamente) — ambos em resposta ao desempate por recência entre dois hosts de mesma severidade.

**Inferência:** T2 thinking indica que o modelo precisou deliberar ao formular a resposta final. Não é um atributo exclusivo do qwen3:14b, mas uma resposta adaptativa à complexidade do raciocínio de síntese. Para tarefas onde o output pode ser sintetizado diretamente dos dados lidos (S4-A, S4-B), T2=0. Para tarefas com regras de desempate sutis (S4-C), T2>0.

---

## 10. Próximos passos

### 10.1 Re-run do qwen3:14b com instrução de mitigação H12

- [ ] Adicionar instrução explícita de leitura obrigatória ao prompt S4 para o qwen3:14b
- [ ] Re-executar S4 Bateria 1 com o prompt modificado
- [ ] Verificar se CHAIN-ACC=4 em todos os 3 casos
- [ ] Documentar se o rank em S4-B (desempate entre críticos) melhora com os arquivos lidos corretamente
- [ ] Registrar como `S4-14b-mitigacao-h12-<data>.md` em `results/benchmarks/`

### 10.2 Bateria 2 — estabilidade temporal (STAB)

- [ ] Executar S4 Bateria 2 para gemma4:e4b e qwen3.5:9b após mínimo 12h
- [ ] Para qwen3:14b: executar Bateria 2 com prompt mitigado (após re-run de mitigação H12)
- [ ] Calcular STAB comparando Bateria 1 vs. Bateria 2 por modelo

### 10.3 Relatório consolidado S1–S4

- [ ] Gerar relatório consolidado S1+S2+S3+S4 após conclusão das baterias 2
- [ ] Sintetizar hipóteses confirmadas: H10 (ortogonalidade de dimensões), H11 (T2 como indicador de complexidade), H12 (tool-skipping por naming semântico)
- [ ] Avaliar inclusão do qwen3:14b na shortlist de produção com restrições documentadas
- [ ] Definir cenário S5 com base nos limites revelados em S4

### 10.4 Pendências anteriores

- [ ] Corrigir documentação S3: `primary_issue=database_unavailable` listado para critical-001 na tabela de casos (seção 7) — correto é `disk_critical_on_var`
- [ ] Executar S3 Bateria 2 para os 3 modelos (STAB S3 pendente)
- [ ] Re-run S2B do qwen3.5:2b após correção do bug de captura

---

## Referências

| Arquivo | Conteúdo |
|---------|----------|
| `docs/decisions/ADR-0001-criterios-de-avaliacao.md` | Critérios e escala usados |
| `docs/benchmarks/S4-triage-multi-log.md` | Definição do cenário S4 |
| `docs/notes/HYP-0012-tool-skipping-naming-semantico.md` | Hipótese H12 — tool-skipping por naming semântico |
| `docs/notes/HYP-0010-acuracia-semantica-e-formato-sao-ortogonais.md` | Hipótese H10 atualizada |
| `docs/notes/HYP-0011-thinking-t2-como-mecanismo-revisao.md` | Hipótese H11 atualizada |
| `results/benchmarks/S4-gemma4-e4b-2026-04-25-summary.md` | Summary gemma4:e4b |
| `results/benchmarks/S4-qwen3.5-9b-2026-04-25-summary.md` | Summary qwen3.5:9b |
| `results/benchmarks/S4-qwen3-14b-2026-04-25-summary.md` | Summary qwen3:14b |
| `results/benchmarks/S4-gemma4-e4b-2026-04-25-case-S4-{A,B,C}.txt` | Runs brutos gemma4 (3 cases) |
| `results/benchmarks/S4-qwen3.5-9b-2026-04-25-case-S4-{A,B,C}.txt` | Runs brutos qwen3.5:9b (3 cases) |
| `results/benchmarks/S4-qwen3-14b-2026-04-25-case-S4-{A,B,C}.txt` | Runs brutos qwen3:14b (3 cases) |
| `results/reports/S3-bateria1-relatorio-2026-04-24.md` | Referência bateria anterior |

---

_Relatório gerado em 2026-04-25 com base na leitura dos 9 arquivos de case, 3 summaries e docs de referência da Bateria 1._
_gemma4:e4b: referência estável — quarta bateria consecutiva com 4/4 em todas as dimensões._
_qwen3:14b: reprovado em S4 por CHAIN-ACC=0 — re-run com mitigação H12 pendente._
