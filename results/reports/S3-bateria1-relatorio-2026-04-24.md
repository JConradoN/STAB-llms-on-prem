# S3 Bateria 1 — Relatório de Resultados

## 1. Cabeçalho

| Campo               | Valor                                                                              |
|---------------------|------------------------------------------------------------------------------------|
| Título              | S3 Bateria 1 — Análise de log estruturado, classificação de severidade e resumo    |
| Data                | 2026-04-24                                                                         |
| Cenário             | S3 – Análise de log, classificação e geração de JSON (Nível 3)                    |
| Hardware            | RTX 3060 12 GB, i5-10400F, 32 GB RAM, Ubuntu 24                                   |
| Script              | `scripts/run-s3-benchmark.py`                                                      |
| Temperatura         | 0                                                                                  |
| K (casos)           | 4 casos distintos por modelo (info-001, warning-001, critical-001, mixed-001)      |
| Tool disponível     | `read_file` (leitura direta via Python — sem subprocess)                           |
| API                 | POST http://localhost:11434/api/chat                                               |
| Prompt fonte        | `docs/benchmarks/S3-log-analysis-classify.md`, seção 5                            |
| Fixtures usados     | `fixtures/health-logs/info/info-001.log`                                          |
|                     | `fixtures/health-logs/warning/warning-001.log`                                    |
|                     | `fixtures/health-logs/critical/critical-001.log`                                  |
|                     | `fixtures/health-logs/mixed/mixed-001.log`                                        |

**Diferença em relação a S2:** em S3 não há execução de script via subprocess — a única tool disponível é `read_file`. A tarefa exige ler o log, classificar a severidade global, extrair campos estruturados e gerar um resumo operacional em português. K=4 corresponde a 4 casos distintos (não repetições do mesmo input), um por fixture.

---

## 2. Modelos avaliados

| Modelo         | Família  | VRAM (MiB) | Tamanho | Status S3       |
|----------------|----------|------------|---------|-----------------|
| gemma4:e4b     | Gemma4   | 9 821      | 9,6 GB  | passou (4/4/4/4/4/4) |
| qwen3:14b      | Qwen3    | 9 437      | 9,3 GB  | passou (4/4/4/4/4/4) |
| qwen3.5:9b     | Qwen3.5  | 7 953      | 6,6 GB  | parcial (CLASS-ACC=4, INST=2) |

**Nota sobre VRAM:** valores de referência dos relatórios S1 e S2 (não registrados no script S3). Todos os três modelos foram carregados individualmente; não houve rodada com dois modelos simultâneos.

**Modelos ausentes em S3:** qwen3.5:2b aguarda re-run S2B após correção do bug de captura (documentado no relatório S2, seção 6.3). Não avança para S3 até conclusão da etapa anterior.

---

## 3. Resultados por modelo

Notas atribuídas com base na leitura dos 12 arquivos de case (4 por modelo).
Escala 0–4 conforme `docs/decisions/ADR-0001-criterios-de-avaliacao.md`.
Fatos observados e inferências separados.

---

### 3.1 gemma4:e4b

**Formato de saída:** JSON minificado (uma linha) sem markdown, sem texto adicional, em todos os 4 casos.
_(Fonte: `case-info-001.txt`, `case-warning-001.txt`, `case-critical-001.txt`, `case-mixed-001.txt`, seção "RESPOSTA FINAL DO MODELO".)_

**CLASS-ACC: 4**
- Fato: `severity_match=True`, `primary_issue_match=True`, `requires_action_match=True` em 4/4 casos. `class_acc_auto=4` em todos. _(Fonte: summaries S3 e seções "VALIDAÇÃO DETALHADA" dos 4 case files.)_

**PARSE-ACC: 4**
- Fato: `primary_issue_match=True`, `secondary_issues_match=True`, `host_match=True` em 4/4 casos. `parse_acc_auto=4` em todos. _(Fonte: idem.)_
- Fato: `timestamp_match=True` em 4/4 casos. _(Confirmado nos case files, seção "VALIDAÇÃO DETALHADA".)_

**TOOL-ACC: 4**
- Fato: tool `read_file` chamada em 4/4 casos; argumento = caminho absoluto correto do fixture em todos; `Leitura OK: True` em todos; `Extra tool calls: 0` em todos. _(Fonte: seção "TOOL CHAMADA PELO MODELO" dos 4 case files.)_

**TOOL-CON: 4**
- Fato: mesma tool (`read_file`), mesmo padrão de argumento (caminho absoluto), 0 extra calls em 4/4 casos. _(Confirmado na tabela "Observações brutas" do summary.)_

**INST: 4**
- Fato: resposta final em JSON puro (sem markdown, sem texto adicional) em 4/4 casos. _(Confirmado nos case files, seção "RESPOSTA FINAL DO MODELO".)_
- Fato: campo `severity` usa apenas valores permitidos; campo `summary` em português do Brasil; nenhum campo ausente; argumento do `read_file` corresponde ao caminho do fixture no prompt — em 4/4 casos. _(Confirmado em todos os case files, seção "VALIDAÇÃO DETALHADA".)_

**CON: 4**
- Fato: comportamento estruturalmente idêntico em 4/4 casos — JSON minificado, sem markdown, thinking=0 no turno 2, mesma tool, mesmo padrão de argumento. _(Confirmado nos 4 case files.)_
- Inferência: a consistência de comportamento do gemma4:e4b, observada em S1 e S2, se mantém em S3 com tarefa de maior complexidade semântica.

**SUMMARY-QUAL: 4**
- Fato: todos os 4 summaries estão em português do Brasil, mencionam o `primary_issue` e fornecem contexto operacional adequado, com comprimento entre 20 e 300 caracteres, `summary_present=True` em 4/4 casos. _(Confirmado nos case files, seção "RESPOSTA FINAL DO MODELO".)_
- Exemplos (fatos):
  - info-001: "O sistema passou por uma verificação de saúde completa e todos os componentes, incluindo CPU, memória e disco, estão operando dentro dos limites normais."
  - warning-001: "O sistema apresentou alta utilização de CPU e latência elevada na API de workers, indicando necessidade de investigação imediata."
  - critical-001: "O sistema está em estado crítico devido ao disco estar quase cheio, falha no serviço PostgreSQL e indisponibilidade do banco de dados."
  - mixed-001: "O sistema apresentou falha crítica devido à indisponibilidade do serviço Redis. Além disso, foi detectado alto uso do volume de backup e taxa elevada de erros na API de sessão."

| Dimensão     | Nota | Base factual |
|--------------|------|--------------|
| CLASS-ACC    | 4    | severity+primary+requires_action corretos em 4/4 casos |
| PARSE-ACC    | 4    | primary+secondary+host+timestamp corretos em 4/4 casos |
| TOOL-ACC     | 4    | read_file, caminho correto, leitura OK, 0 extra calls em 4/4 |
| TOOL-CON     | 4    | Mesma tool e padrão de argumento em 4/4 casos |
| INST         | 4    | JSON puro, todos os critérios INST em 4/4 casos |
| CON          | 4    | Comportamento estruturalmente idêntico em 4/4 casos |
| SUMMARY-QUAL | 4    | Summaries em pt-BR, precisos, contextualizados em 4/4 casos |

---

### 3.2 qwen3:14b

**Formato de saída:** JSON indentado (multi-linha) sem markdown, sem texto adicional, em todos os 4 casos.
_(Fonte: seção "RESPOSTA FINAL DO MODELO" dos 4 case files.)_

**Comportamento notável:** qwen3:14b é o ÚNICO modelo desta bateria que usa thinking em ambos os turnos (T1 e T2). Os outros dois modelos têm thinking=0 no turno 2. _(Fato: confirmado nas seções "PERFORMANCE / Turno 2" de todos os case files dos 3 modelos.)_

**CLASS-ACC: 4**
- Fato: `severity_match=True`, `primary_issue_match=True`, `requires_action_match=True` em 4/4 casos. `class_acc_auto=4` em todos. _(Fonte: summary e seções "VALIDAÇÃO DETALHADA" dos 4 case files.)_

**PARSE-ACC: 4**
- Fato: `primary_issue_match=True`, `secondary_issues_match=True`, `host_match=True`, `timestamp_match=True` em 4/4 casos. `parse_acc_auto=4` em todos. _(Confirmado nos case files.)_

**TOOL-ACC: 4**
- Fato: tool `read_file` chamada com caminho correto, `Leitura OK: True`, `Extra tool calls: 0` em 4/4 casos. _(Confirmado nos case files, seção "TOOL CHAMADA PELO MODELO".)_

**TOOL-CON: 4**
- Fato: mesma tool e padrão de argumento em 4/4 casos; `Extra tool calls: 0` em todos. _(Fonte: summary, tabela "Observações brutas".)_

**INST: 4**
- Fato: resposta final em JSON puro (sem markdown, sem texto adicional) em 4/4 casos. _(Confirmado em todos os case files.)_
- Fato: todos os 6 pontos do checklist INST S3 passam em 4/4 casos. _(Fonte: case files, seção "VALIDAÇÃO DETALHADA": `json_valid=True`, `summary_present=True` em todos.)_
- Observação: o summary do caso mixed-001 contém os termos "outage" e "backup volume" em inglês dentro de frase em português. _(Fato: "Falha crítica no serviço Redis causou outage primário, com backup volume em 89% de uso…")_ INST permanece 4 porque o campo summary\_present=True e o conteúdo é preciso; o uso de jargão técnico em inglês é contextual em ambiente de TI.

**CON: 4**
- Fato: comportamento estruturalmente consistente em 4/4 casos — JSON indentado, sem markdown, mesma tool, mesmo padrão de argumento. _(Confirmado nos 4 case files.)_
- Fato: variação de thinking total entre casos (T1+T2): info-001=2521, warning-001=3442, critical-001=2805, mixed-001=2867. Variação de ~36% entre menor e maior. _(Confirmado nos case files, seção "PERFORMANCE".)_
- Inferência: a variação de thinking não afeta CON (a dimensão avalia o output final, não o processo interno); o output é estruturalmente consistente apesar da variação de raciocínio.

**SUMMARY-QUAL: 3**
- Fato: 3/4 summaries estão inteiramente em português e são precisos (info-001, critical-001, warning-001). O summary do mixed-001 contém "outage" e "backup volume" em inglês. _(Confirmado nos case files.)_
- Exemplos (fatos):
  - info-001: "Verificação de saúde concluída sem anomalias detectadas. Todos os componentes reportam status normal."
  - warning-001: "CPU usage ultrapassou o limite de 80% por 12 minutos e a latência da aplicação worker-api está elevada, causando status degradado no sistema."
  - critical-001: "Servidor fox-node-03 apresenta disco /var em 97% de uso e falha no serviço postgresql, resultando em banco de dados indisponível. Requer intervenção imediata."
  - mixed-001: "Falha crítica no serviço Redis causou outage primário, com backup volume em 89% de uso e taxa de erros elevada na API de sessão."
- Critério: "4 = Resumo preciso, em português"; o uso de inglês em mixed-001 abaixa para 3 o agregado.

| Dimensão     | Nota | Base factual |
|--------------|------|--------------|
| CLASS-ACC    | 4    | severity+primary+requires_action corretos em 4/4 casos |
| PARSE-ACC    | 4    | primary+secondary+host+timestamp corretos em 4/4 casos |
| TOOL-ACC     | 4    | read_file, caminho correto, leitura OK, 0 extra calls em 4/4 |
| TOOL-CON     | 4    | Mesma tool e padrão de argumento em 4/4 casos |
| INST         | 4    | JSON puro, todos os critérios INST em 4/4 casos |
| CON          | 4    | Comportamento estruturalmente consistente em 4/4 casos |
| SUMMARY-QUAL | 3    | 3/4 summaries em pt-BR puro; mixed-001 contém jargão em inglês |

---

### 3.3 qwen3.5:9b

**Formato de saída:** variável entre casos — inconsistência de formato é o achado central para este modelo.
_(Fato: observado diretamente nas seções "RESPOSTA FINAL DO MODELO" dos 4 case files.)_

| Caso | Formato observado |
|------|-------------------|
| info-001 | JSON minificado, sem markdown ✓ |
| warning-001 | JSON indentado, COM wrapper ```json ... ``` ✗ |
| critical-001 | JSON indentado, sem markdown ✓ |
| mixed-001 | JSON indentado, COM wrapper ```json ... ``` ✗ |

**CLASS-ACC: 4**
- Fato: `severity_match=True`, `primary_issue_match=True`, `requires_action_match=True` em 4/4 casos. `class_acc_auto=4` em todos. _(Fonte: summary e seções "VALIDAÇÃO DETALHADA" dos 4 case files.)_
- Fato: o parser do script extrai JSON válido mesmo dos cases com markdown wrapper; `json_valid=True` em 4/4 casos. _(Confirmado em seção "VALIDAÇÃO DETALHADA" de todos os case files.)_

**PARSE-ACC: 4**
- Fato: `primary_issue_match=True`, `secondary_issues_match=True`, `host_match=True`, `timestamp_match=True` em 4/4 casos. `parse_acc_auto=4` em todos. _(Confirmado nos case files.)_

**TOOL-ACC: 4**
- Fato: tool `read_file` chamada com caminho correto, `Leitura OK: True`, `Extra tool calls: 0` em 4/4 casos. _(Confirmado nos case files, seção "TOOL CHAMADA PELO MODELO".)_

**TOOL-CON: 4**
- Fato: mesma tool e padrão de argumento em 4/4 casos; `Extra tool calls: 0` em todos. _(Fonte: summary, tabela "Observações brutas".)_

**INST: 2**
- Fato: o ponto 3 do checklist INST S3 ("A resposta final é JSON puro, sem markdown, sem texto adicional") falha em 2/4 casos (warning-001 e mixed-001). _(Confirmado nos case files: resposta inicia com ` ```json ` e termina com ` ``` `.)_
- Fato: os demais 5 pontos do checklist INST passam em 4/4 casos. _(Confirmado na seção "VALIDAÇÃO DETALHADA": severity usa valores permitidos, summary em pt-BR, nenhum campo ausente, argumento correto.)_
- Critério: desvio em um ponto crítico (formato de saída) em 2/4 casos; os outros pontos passam sistematicamente. INST = 2.
- Nota: a instrução do prompt S3 inclui "Responda APENAS com o JSON. Sem markdown. Sem texto adicional." — mesmo com instrução explícita, o modelo viola o formato em 50% dos casos. O parser do script trata o markdown e extrai o JSON correto, de modo que CLASS-ACC e PARSE-ACC não são afetados; a violação é de formato, não de conteúdo.

**CON: 2**
- Fato: o formato de saída varia entre casos — 1 minificado sem markdown, 1 indentado sem markdown, 2 indentados com markdown wrapper. _(Confirmado nos 4 case files.)_
- Critério: variação estrutural (não apenas de "detalhes de redação") em 3 dos 4 casos (não há formato único estável). CON = 2.
- Nota: o conteúdo (classificação, campos) é consistente em 4/4 casos; a inconsistência é exclusivamente de formato de output.

**SUMMARY-QUAL: 4**
- Fato: todos os 4 summaries estão em português do Brasil, mencionam o `primary_issue`, têm comprimento adequado e `summary_present=True`. _(Confirmado nos case files.)_
- Exemplos (fatos):
  - info-001: "Verificação de saúde concluida com sucesso, todos os recursos e serviços estão operando normalmente."
  - warning-001: "O nó fox-node-02 apresenta uso de CPU elevado e latência de aplicação aumentada, exigindo investigação."
  - critical-001: "O disco de /var atingiu 97% de uso, causando falha no serviço PostgreSQL e tornando a base de dados indisponível."
  - mixed-001: "Falha crítica no serviço Redis que causou a queda do sistema, com volume de backup próximo da capacidade e taxa de erro da API de sessões elevada."

| Dimensão     | Nota | Base factual |
|--------------|------|--------------|
| CLASS-ACC    | 4    | severity+primary+requires_action corretos em 4/4 casos |
| PARSE-ACC    | 4    | primary+secondary+host+timestamp corretos em 4/4 casos |
| TOOL-ACC     | 4    | read_file, caminho correto, leitura OK, 0 extra calls em 4/4 |
| TOOL-CON     | 4    | Mesma tool e padrão de argumento em 4/4 casos |
| INST         | **2**| Markdown wrapper em 2/4 casos, violando "JSON puro" |
| CON          | **2**| Formato varia entre casos: minified/indented/markdown-wrapped |
| SUMMARY-QUAL | 4    | Summaries em pt-BR, precisos em 4/4 casos |

---

### 3.4 Resumo das notas — S3 Bateria 1

| Modelo         | CLASS-ACC | PARSE-ACC | TOOL-ACC | TOOL-CON | INST | CON | SUMMARY-QUAL | Resultado |
|----------------|-----------|-----------|----------|----------|------|-----|--------------|-----------|
| gemma4:e4b     | 4         | 4         | 4        | 4        | 4    | 4   | 4            | passou    |
| qwen3:14b      | 4         | 4         | 4        | 4        | 4    | 4   | 3            | passou    |
| qwen3.5:9b     | 4         | 4         | 4        | 4        | **2**| **2**| 4           | parcial   |

---

## 4. Métricas de performance

Médias calculadas sobre os 4 casos (info-001, warning-001, critical-001, mixed-001).
Nota metodológica: em S3, K=4 corresponde a casos distintos, não repetições do mesmo input. Não existe exclusão de "run 1 por cold start" como metodologia padrão. O caso info-001 do qwen3.5:9b apresenta ms anomalamente alto (17 487 ms vs. 8 165–8 679 ms nos outros 3 casos), consistente com o padrão de cold start observado em S1 e S2. Médias alternativas excluindo info-001 são fornecidas onde relevante.

### 4.1 Tabela de performance por modelo (todos os 4 casos)

| Modelo         | tok/s médio | ms/caso médio | tok_total médio | thinking T1 médio | thinking T2 médio |
|----------------|-------------|---------------|-----------------|-------------------|-------------------|
| gemma4:e4b     | 72,8        | 8 061         | 1 783           | 1 207             | 0                 |
| qwen3.5:9b     | 46,2        | 10 676        | 1 943           | 515               | 0                 |
| qwen3.5:9b*    | 46,2        | 8 406         | 1 951           | 521               | 0                 |
| qwen3:14b      | 33,5        | 28 134        | 2 168           | 1 527             | 1 382             |

_* média excluindo info-001 (cold start — ms=17 487, ~2× os demais casos)._

_(Tabela ordenada por tok/s decrescente.)_

**Cálculos detalhados:**

**gemma4:e4b:**
- tok/s: (73,0 + 72,9 + 72,6 + 72,7) / 4 = **72,8**
- ms: (7 836,4 + 7 998,4 + 8 589,2 + 7 818,5) / 4 = **8 061**
- tokens: (1 764 + 1 808 + 1 779 + 1 781) / 4 = **1 783**
- thinking T1: (1 183 + 1 219 + 1 298 + 1 126) / 4 = **1 207**
- thinking T2: 0 em 4/4 casos. _(Fonte: seção "PERFORMANCE / Turno 2" dos 4 case files.)_

**qwen3.5:9b:**
- tok/s: (46,3 + 46,3 + 46,1 + 46,1) / 4 = **46,2**
- ms (todos): (17 486,6 + 8 374,0 + 8 679,4 + 8 164,8) / 4 = **10 676**
- ms (ex. info-001): (8 374,0 + 8 679,4 + 8 164,8) / 3 = **8 406**
- tokens (todos): (1 917 + 1 976 + 1 925 + 1 952) / 4 = **1 943**
- thinking T1: (552 + 557 + 563 + 389) / 4 = **515**
- thinking T2: 0 em 4/4 casos. _(Confirmado nos case files.)_

**qwen3:14b:**
- tok/s: (33,7 + 33,4 + 33,5 + 33,4) / 4 = **33,5**
- ms: (32 297,7 + 29 121,6 + 25 230,0 + 25 885,9) / 4 = **28 134**
- tokens: (2 069 + 2 306 + 2 114 + 2 184) / 4 = **2 168**
- thinking T1: (1 545 + 1 713 + 1 561 + 1 290) / 4 = **1 527**
- thinking T2: (976 + 1 729 + 1 244 + 1 577) / 4 = **1 382**

### 4.2 Thinking chars por modelo e caso

| Modelo         | info-001     | warning-001  | critical-001 | mixed-001    |
|----------------|--------------|--------------|--------------|--------------|
| gemma4:e4b     | T1=1183, T2=0 | T1=1219, T2=0 | T1=1298, T2=0 | T1=1126, T2=0 |
| qwen3.5:9b     | T1=552, T2=0  | T1=557, T2=0  | T1=563, T2=0  | T1=389, T2=0  |
| qwen3:14b      | T1=1545, T2=976 | T1=1713, T2=1729 | T1=1561, T2=1244 | T1=1290, T2=1577 |

_(Fonte: seção "PERFORMANCE" de cada case file.)_

---

## 5. Análises e achados

### 5.1 Thinking no turno 2: característica diferenciadora entre modelos

**Fato observado:** gemma4:e4b e qwen3.5:9b produzem thinking=0 no turno 2 em todos os 4 casos S3. qwen3:14b produz thinking>0 no turno 2 em todos os 4 casos, com valores entre 976 e 1 729 chars. _(Fonte: seção "PERFORMANCE / Turno 2" de todos os 12 case files.)_

**Fato observado:** este padrão (T2=0 para gemma4 e 9b, T2>0 para 14b) é consistente com o comportamento observado em S1 e S2B para estes modelos.

**Inferência:** o thinking no turno 2 indica que o qwen3:14b delibera sobre a classificação ao formular a resposta final, não apenas no turno de decisão da tool. Os outros dois modelos tratam o turno 2 como operação de síntese direta, sem raciocínio adicional. Se o thinking no T2 funciona como indicador de incerteza na classificação (hipótese H7, relatório S2), o qwen3:14b expressa maior incerteza no momento de consolidar a resposta — o que pode ser um sinal de maior cuidado, não de dificuldade.

**Inferência:** a variação do thinking T2 no qwen3:14b entre casos (976 em info-001 → 1 729 em warning-001) sugere que o modelo investe mais raciocínio quando a classificação envolve distinções mais sutis. O caso warning-001 (que exige distinguir entre warning e info, com dois tipos de problema) gerou o maior thinking T2 (1 729 chars), maior até do que critical-001 (1 244 chars), onde o log explicita CRITICAL em múltiplas linhas. Isso é coerente com a hipótese de que logs com severidade explícita requerem menos deliberação no T2 do que logs com múltiplos alertas moderados.

---

### 5.2 Variação de thinking T1 no qwen3.5:9b

**Fato observado:** thinking T1 do qwen3.5:9b varia entre casos: info-001=552, warning-001=557, critical-001=563, mixed-001=389. Os três primeiros casos têm valores muito próximos (552–563); o mixed-001 é notavelmente menor (389, -29%). _(Confirmado nos case files.)_

**Fato observado:** o caso mixed-001 é o de maior complexidade estrutural (contém níveis INFO, WARNING e CRITICAL no mesmo arquivo, o que exige aplicar a regra de precedência). Apesar disso, gerou menos thinking que os casos mais simples.

**Inferência:** não há correlação direta entre complexidade do log e volume de thinking T1 para o qwen3.5:9b nesta bateria. Uma hipótese alternativa é que o modelo já havia "aquecido" o contexto nos cases anteriores e processou mixed-001 com menos overhead. Com K=1 por caso não é possível confirmar; seria necessário repetir.

---

### 5.3 Inconsistência de formato no qwen3.5:9b

**Fato observado:** qwen3.5:9b produz markdown wrapper em 2/4 casos (warning-001 e mixed-001) e JSON puro nos outros 2 (info-001 e critical-001). A instrução do prompt S3 explicita "Responda APENAS com o JSON. Sem markdown. Sem texto adicional." em todos os casos. _(Confirmado nos case files, seção "RESPOSTA FINAL DO MODELO".)_

**Fato observado:** o script extrai JSON válido mesmo dos casos com markdown (json_valid=True em 4/4), de modo que CLASS-ACC e PARSE-ACC não são afetados. A inconsistência impacta INST e CON, não a acurácia semântica.

**Fato observado:** em S2B, com instrução mais explícita ("NÃO use markdown. NÃO use blocos de código. A resposta começa com { e termina com }."), o qwen3.5:9b produziu JSON puro em 5/5 runs. Em S3, com instrução moderadamente explícita, 50% dos casos têm markdown. _(Referência: relatório S2, seções 4.1 e 6.1.)_

**Inferência:** a instrução mais detalhada de S2B suprimiu o markdown do 9b completamente. A instrução de S3 — ligeiramente menos explícita — suprime em apenas 50% dos casos. Este gradiente confirma que o comportamento de markdown wrapper no 9b é sensível à força da instrução de formato, mas não foi eliminado de forma robusta: é suprimível com instrução de alta especificidade, mas não com instrução moderada.

**Inferência:** a sensibilidade ao formato de instrução é uma característica do qwen3.5:9b que já foi documentada em S2 e se confirma em S3. Para uso em produção com saída JSON, o 9b requer a formulação mais explícita (estilo S2B) e ainda assim não garante 100% de conformidade.

---

### 5.4 Diferença de latência: 9b vs. 14b vs. gemma4:e4b

**Fato observado:**
- gemma4:e4b: ms médio = 8 061 (casos 1–4)
- qwen3.5:9b: ms médio = 8 406 (casos 2–4, ex. cold start)
- qwen3:14b: ms médio = 28 134 (casos 1–4) — 3,5× mais lento que o gemma4

_(Fonte: seção "PERFORMANCE / Total do run" dos 12 case files.)_

**Fato observado:** o throughput (tok/s) é estável por modelo em S3: gemma4=72,6–73,0, qwen3.5:9b=46,1–46,3, qwen3:14b=33,4–33,7. Esses valores são consistentes com os de S1 e S2.

**Fato observado:** a latência do qwen3:14b em S3 (28 134 ms médio) é menor do que em S2 (52 085 ms médio), apesar do thinking total ser comparável (S3: ~2 909 chars médio por caso; S2: ~6 199 chars médio por run). A diferença explica-se pelo design das tarefas: em S2, o modelo gerou muito mais tokens de reasoning ao processar os dados do health.sh (script longo); em S3, os logs são curtos e a resposta JSON é mais enxuta, reduzindo tanto os tokens de input no T2 quanto os tokens de output.

**Inferência:** a latência absoluta do qwen3:14b (28 s/caso) permanece significativamente maior que a dos outros dois modelos (~8 s/caso). Para pipelines operacionais que exigem análise de log em tempo próximo ao real, essa diferença é relevante. Em casos de uso offline (batch analysis, relatórios), o custo é aceitável se a qualidade adicional justificar.

---

### 5.5 Discrepância entre documentação S3 e expected.json no caso critical-001

**Fato observado:** a tabela de casos na documentação `docs/benchmarks/S3-log-analysis-classify.md`, seção 7, lista `primary_issue=database_unavailable` para o caso critical-001. Porém, as seções "VALIDAÇÃO DETALHADA" dos 3 case files de critical-001 mostram `primary_issue_match=True` com `expected: disk_critical_on_var`. _(Confirmado em `S3-gemma4-e4b-2026-04-24-case-critical-001.txt`, `S3-qwen3.5-9b-2026-04-24-case-critical-001.txt`, `S3-qwen3-14b-2026-04-24-case-critical-001.txt`.)_

**Inferência:** o arquivo `fixtures/health-logs/critical/critical-001.expected.json` (autoridade do script de validação) define `primary_issue=disk_critical_on_var`. A tabela na documentação está desatualizada. O disco cheio é a causa raiz da cadeia de falhas (disk → postgresql → database), portanto `disk_critical_on_var` como primary é semanticamente correto. A documentação deve ser corrigida.

---

## 6. Classificação final S3

| Modelo         | CLASS-ACC | PARSE-ACC | TOOL-ACC | TOOL-CON | INST | CON | tok/s | ms/caso | Avança para S4? |
|----------------|-----------|-----------|----------|----------|------|-----|-------|---------|-----------------|
| gemma4:e4b     | 4         | 4         | 4        | 4        | 4    | 4   | 72,8  | 8 061   | **sim**         |
| qwen3:14b      | 4         | 4         | 4        | 4        | 4    | 4   | 33,5  | 28 134  | **sim** (monitorar latência) |
| qwen3.5:9b     | 4         | 4         | 4        | 4        | **2**| **2**| 46,2 | 8 406   | **condicionado** (instrução S2B-level) |

**Justificativas:**

- **gemma4:e4b:** aprovado sem ressalvas. Mantém 4/4/4/4 em todas as dimensões pela terceira bateria consecutiva. Melhor relação qualidade/performance/consistência da shortlist atual.
- **qwen3:14b:** aprovado com observação de latência. Qualidade 4/4/4/4/4 em todas as dimensões de classificação e formato, apesar de latência 3,5× maior que o gemma4. SUMMARY-QUAL=3 por uso de jargão inglês em um caso — não compromete a aprovação. O thinking no T2 é uma característica estrutural do modelo, não uma anomalia.
- **qwen3.5:9b:** parcial — aprovado em acurácia (CLASS-ACC=4, PARSE-ACC=4), reprovado em formato (INST=2, CON=2). A acurácia semântica é excelente; a inconsistência de formato é o bloqueio. Pode avançar para S4 com instrução de formato no nível S2B ("NÃO use markdown. A resposta começa com { e termina com }."), mas o prompt precisa ser fortalecido antes de rodar.

---

## 7. Comparação acumulada S1 → S2 → S3

### 7.1 Notas por dimensão e cenário

_Nota: em S1, a métrica de acurácia de conteúdo não se aplica (o output era o stdout literal do script, sem extração de campos). Em S2, a métrica de acurácia de conteúdo é JSON-ACC. Em S3, são CLASS-ACC e PARSE-ACC. Dimensões comparáveis entre cenários: TOOL-ACC, TOOL-CON, INST, CON._

| Modelo     | Cenário | TOOL-ACC | TOOL-CON | INST | CON | Acurácia conteúdo |
|------------|---------|----------|----------|------|-----|-------------------|
| gemma4:e4b | S1      | 4        | 4        | 4    | 4   | n/a               |
| gemma4:e4b | S2      | 4        | 4        | 4    | 4   | JSON-ACC=4        |
| gemma4:e4b | S3      | 4        | 4        | 4    | 4   | CLASS-ACC=4, PARSE-ACC=4 |
| qwen3:14b  | S1      | 4        | 4        | 4    | 4   | n/a               |
| qwen3:14b  | S2      | 4        | 4        | 4    | 4   | JSON-ACC=4        |
| qwen3:14b  | S3      | 4        | 4        | 4    | 4   | CLASS-ACC=4, PARSE-ACC=4 |
| qwen3.5:9b | S1      | 4        | 4        | 4    | 4   | n/a               |
| qwen3.5:9b | S2 (orig)| **0**   | 4        | **0**| **0**| JSON-ACC=**0**   |
| qwen3.5:9b | S2B     | 4        | 4        | 4    | 4   | JSON-ACC=4        |
| qwen3.5:9b | S3      | 4        | 4        | **2**| **2**| CLASS-ACC=4, PARSE-ACC=4 |

_(S2 orig = prompt original S2; S2B = prompt refinado com tool explícita e restrições de formato fortes.)_

### 7.2 Performance por cenário e modelo

| Modelo         | Cenário | tok/s | ms/run médio | thinking chars médio |
|----------------|---------|-------|--------------|----------------------|
| gemma4:e4b     | S1      | 73,0  | 8 202        | 955 (T1)             |
| gemma4:e4b     | S2      | 72,9  | 8 586        | 1 052 (T1)           |
| gemma4:e4b     | S3      | 72,8  | 8 061        | 1 207 (T1) + 0 (T2)  |
| qwen3:14b      | S1      | 33,8  | 30 053       | 3 064 (T1+T2)        |
| qwen3:14b      | S2      | 33,4  | 52 085       | 6 199 (T1+T2)        |
| qwen3:14b      | S3      | 33,5  | 28 134       | 2 909 (T1+T2)        |
| qwen3.5:9b     | S1      | 46,4  | 9 307        | 278 (T1)             |
| qwen3.5:9b     | S2      | 46,5  | 4 201        | 359 (T1+T2)          |
| qwen3.5:9b     | S2B     | 46,4  | 5 712        | 195 (T1)             |
| qwen3.5:9b     | S3      | 46,2  | 8 406*       | 515 (T1) + 0 (T2)    |

_* Média sobre casos 2–4 (excluindo info-001 com cold start de 17 487 ms)._

**Observações sobre tendências de performance (fatos):**
- gemma4:e4b: tok/s extremamente estável em S1-S2-S3 (73,0→72,9→72,8); ms/run ligeiramente menor em S3 do que em S2. Variação total <1% em tok/s nos 3 cenários.
- qwen3:14b: tok/s estável (33,8→33,4→33,5); ms/run varia por cenário conforme volume de output (S2 muito alto devido ao JSON extenso de saúde do sistema; S3 volta a patamares próximos de S1).
- qwen3.5:9b: tok/s estável (46,4→46,5→46,2); ms/run varia com o resultado da task (S2 orig muito baixo porque a resposta era vazia; S2B moderado; S3 sobe para ~8 400 ms com outputs de log completos).

---

## 8. Implicações para o laboratório

### 8.1 Hipótese principal emergente sobre modelo vs. instrução

Após três cenários (S1, S2, S3), a evidência acumulada aponta para a seguinte hipótese central:

**Hipótese H10 (nova):** a qualidade de classificação semântica (acurácia de leitura e interpretação) e a qualidade de formato de saída são dimensões **ortogonais** nos modelos testados, e a relação de cada modelo com instruções de formato é característica estrutural do modelo, não do prompt.

Evidências:
- **gemma4:e4b** e **qwen3:14b** demonstram conformidade de formato em S2 e S3 com instrução padronizada (sem forçamento extra). CLASS-ACC=4 e PARSE-ACC=4 em S3 mostram que a qualidade semântica é independente do formato.
- **qwen3.5:9b** alcança CLASS-ACC=4 e PARSE-ACC=4 em S3 (acurácia semântica perfeita) mas com INST=2 (formato inconsistente). A falha de formato não impede a classificação correta — o conteúdo é certo, a apresentação é instável.
- A instrução de formato afeta a conformidade do 9b: S2B (instrução forte) → INST=4; S3 (instrução moderada) → INST=2. Mas o gemma4 e o 14b mantêm INST=4 independentemente da força da instrução.

**Implicação para o design de agentes:** modelos como gemma4:e4b e qwen3:14b são "instruction-stable" em formato — o formato do output é uma característica consolidada do modelo que não precisa de instrução reforçada. Para qwen3.5:9b, a instrução de formato é uma variável de controle ativa: um sistema que use este modelo precisa incluir sempre a instrução mais explícita possível, e ainda assim o resultado pode não ser 100% confiável.

### 8.2 Posição consolidada de gemma4:e4b

**Fato:** gemma4:e4b obteve 4/4/4/4 em TOOL-ACC, TOOL-CON, INST e CON em S1, S2 e S3. CLASS-ACC=4 e PARSE-ACC=4 em S3. SUMMARY-QUAL=4 em S3.

**Inferência:** gemma4:e4b consolidou a posição de modelo de referência para agentes on-prem com saída estruturada neste laboratório. Nenhum cenário testado até agora revelou falha. A próxima etapa relevante para avaliar seus limites é aumentar a complexidade da tarefa (S4 ou multi-step com múltiplas tools) ou testar sob variação de temperatura e repetição (STAB).

### 8.3 Hipótese sobre qwen3:14b e thinking T2

**Hipótese H11 (nova):** o thinking no turno 2 do qwen3:14b pode ser um mecanismo de verificação pré-output que explica sua consistência de formato em tarefas de maior complexidade. Ao "revisar" a resposta antes de emiti-la (T2>0), o modelo pode estar corrigindo possíveis desvios de formato ou conteúdo que seriam emitidos sem revisão.

Base: qwen3:14b usa T2>0 em S3 e mantém INST=4; qwen3.5:9b e gemma4 usam T2=0 e: gemma4 mantém INST=4 (possivelmente por comportamento de treinamento mais robusto); 9b tem INST=2 (sem revisão T2, o formato instável não é corrigido).

Próximo passo: verificar se seria possível induzir thinking no T2 do 9b via prompt (ex.: "revise sua resposta antes de emitir") e observar se isso reduz a inconsistência de formato.

### 8.4 Consistência de throughput como evidência de que tok/s é hardware-bound

**Fato:** tok/s é extremamente estável para cada modelo entre S1, S2 e S3 (variação <1%), independentemente do tamanho ou complexidade do output. Para gemma4: 73,0→72,9→72,8. Para 14b: 33,8→33,4→33,5. Para 9b: 46,4→46,5→46,2. _(Fatos compilados das seções de performance dos relatórios S1, S2 e S3.)_

**Inferência:** o throughput (tok/s) é determinado pelo modelo carregado na VRAM e pelo hardware, não pela natureza da tarefa. Toda variação de latência entre cenários se explica por variação em número de tokens gerados (output), não em velocidade de geração. Isso simplifica estimativas de latência para novos cenários: latência ≈ tokens_totais / tok/s_do_modelo.

---

## 9. Próximos passos

### 9.1 Bateria 2 — estabilidade temporal (STAB)

- [ ] **Executar S3 Bateria 2** para gemma4:e4b, qwen3:14b e qwen3.5:9b — mínimo 12h após Bateria 1.
  - Usar o mesmo script, mesmo prompt, mesmos fixtures, temperatura 0.
  - Objetivo: calcular STAB comparando notas da Bateria 1 vs. Bateria 2.
  - Para qwen3.5:9b: rodar Bateria 2 com prompt S3 padrão e também com instrução reforçada (estilo S2B) para comparar.

### 9.2 S4 — próximo nível de complexidade

- [ ] **Definir cenário S4** em `docs/benchmarks/S4-[nome].md`:
  - Aumentar complexidade vs. S3: múltiplas tools, multi-step, ou múltiplos arquivos de log.
  - Incluir gemma4:e4b e qwen3:14b como candidatos principais.
  - Avaliar inclusão do qwen3.5:9b com instrução de formato reforçada.

### 9.3 Pendências anteriores (de S1/S2)

- [ ] **Corrigir bug do script S2B** (content=None quando thinking>0 no T2) e re-rodar S2B qwen3.5:2b.
- [ ] **Executar Bateria 2 de S1** (STAB S1) — ainda pendente.
- [ ] **Corrigir documentação S3:** tabela de casos na seção 7 lista `primary_issue=database_unavailable` para critical-001; o expected.json correto é `disk_critical_on_var`.
- [ ] **Verificar arquitetura gemma4:e4b** (`ollama show gemma4:e4b`) — hipótese H9 (MoE) ainda pendente.
- [ ] **Registrar hipóteses H10 e H11** em `docs/notes/`.

### 9.4 Relatório consolidado

- [ ] **Gerar relatório consolidado S1+S2+S3 Bateria 1** após conclusão das três baterias acima — síntese de hipóteses confirmadas, modelos candidatos para produção e próxima fase.

---

### Referências desta bateria

| Arquivo | Conteúdo |
|---------|----------|
| `docs/decisions/ADR-0001-criterios-de-avaliacao.md` | Critérios e escala usados |
| `docs/benchmarks/S3-log-analysis-classify.md` | Definição do cenário S3 |
| `results/reports/S1-bateria1-relatorio-2026-04-24.md` | Referência da Bateria 1 S1 |
| `results/reports/S2-bateria1-relatorio-2026-04-24.md` | Referência da Bateria 1 S2 |
| `results/benchmarks/S3-gemma4-e4b-2026-04-24-summary.md` | Summary gemma4:e4b |
| `results/benchmarks/S3-qwen3.5-9b-2026-04-24-summary.md` | Summary qwen3.5:9b |
| `results/benchmarks/S3-qwen3-14b-2026-04-24-summary.md` | Summary qwen3:14b |
| `results/benchmarks/S3-*-2026-04-24-case-*.txt` | Runs brutos S3 (12 arquivos, 3 modelos × 4 casos) |

---

_Relatório gerado em 2026-04-24 com base na leitura dos 12 arquivos de case e 3 summaries da Bateria 1._
_qwen3.5:2b: ausente em S3 — aguardar re-run S2B após correção do bug._
