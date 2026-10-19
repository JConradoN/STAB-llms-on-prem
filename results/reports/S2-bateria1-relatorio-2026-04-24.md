# S2 Bateria 1 — Relatório de Resultados

## 1. Cabeçalho

| Campo               | Valor                                                                         |
|---------------------|-------------------------------------------------------------------------------|
| Título              | S2 Bateria 1 — Health check com parsing e geração de JSON estruturado        |
| Data                | 2026-04-24                                                                    |
| Cenário             | S2 – Health check com parsing e JSON (Nível 2)                               |
| Hardware            | RTX 3060 12 GB, i5-10400F, 32 GB RAM, Ubuntu 24                              |
| Script S2           | `scripts/run-s2-benchmark.py`                                                 |
| Script S2B          | `scripts/run-s2b-benchmark.py`                                                |
| Temperatura         | 0                                                                             |
| K (runs)            | 5 por modelo (S2) / 2 por modelo (S2B qwen3.5:2b — bug interrompeu)         |
| Timeout             | não registrado                                                                |
| Tool                | `run_bash` (execução real via subprocess no host)                            |
| API                 | POST http://localhost:11434/api/chat                                          |
| Variante S2         | Prompt original (`S2-health-check-json.md`, seção 4)                         |
| Variante S2B        | Prompt refinado — instrução de tool explícita + restrições de formato reforçadas |

**Diferença entre prompts:**

- **S2** inicia com: `"Execute o script ~/scripts/health.sh, capture a saída..."` — não especifica o nome da tool nem o comando exato.
- **S2B** inicia com: `"Use a tool run_bash com o comando exato: ~/scripts/health.sh"` — nome da tool e argumento explícitos. Acrescenta restrições de formato mais fortes: `"NÃO use markdown. NÃO use blocos de código. NÃO adicione texto antes ou depois. A resposta começa com { e termina com }."`.

---

## 2. Modelos avaliados

| Modelo         | Família  | VRAM (MiB) | Tamanho | Status S2             | Status S2B                            |
|----------------|----------|------------|---------|----------------------|---------------------------------------|
| qwen3.5:9b     | Qwen3.5  | 7 953      | 6,6 GB  | falhou (TOOL-ACC=0)  | passou (4/4/4/4/4)                    |
| qwen3.5:2b     | Qwen3.5  | 3 829      | 2,7 GB  | parcial (INST=2)     | inválido — bug de captura (2/2 runs)  |
| qwen3:14b      | Qwen3    | 9 437      | 9,3 GB  | passou (4/4/4/4/4)   | não testado                           |
| gemma4:e4b     | Gemma4   | 9 821      | 9,6 GB  | passou (4/4/4/4/4)   | não testado                           |

**Fontes de VRAM:** campo `VRAM usada` do stdout do `health.sh` nos runs. qwen3.5:9b confirmado em `S2B-qwen3.5-9b-2026-04-24-run1.txt` (7 953 MiB); qwen3.5:2b confirmado em `S2B-qwen3.5-2b-2026-04-24-run1.txt` (3 831 MiB); qwen3:14b e gemma4:e4b confirmados nos summaries S1.

---

## 3. Resultados S2 — prompt original

Notas atribuídas com base na leitura dos arquivos de run (runs 1–5 de cada modelo).
Escala 0–4 conforme `docs/decisions/ADR-0001-criterios-de-avaliacao.md`.

---

### 3.1 qwen3.5:9b

**Argumento usado:** `cat ~/scripts/health.sh` em todos os 5 runs
_(Fonte: `S2-qwen3.5-9b-2026-04-24-run1.txt` a `run4.txt`, seção "TOOL CHAMADA PELO MODELO"; confirmado no summary, coluna "Argumento")_

**O que aconteceu:** o modelo interpretou a instrução "Execute o script" como "leia o conteúdo do script". Chamou `run_bash` com `cat ~/scripts/health.sh`, o que retornou o código-fonte bash do script — não a saída de execução. Com código-fonte em vez de dados de saúde, o modelo não conseguiu gerar o JSON e retornou resposta vazia em todos os 5 runs.

**TOOL-ACC: 0**
- Fato: `cat ~/scripts/health.sh` lê o conteúdo do arquivo; não executa `health.sh` nem produz os dados de saúde do sistema. _(Fonte: `run1.txt`, seção "STDOUT RETORNADO" — stdout contém `#!/bin/bash export LC_ALL=C echo...`, não dados de CPU/GPU.)_
- Fato: `Exec OK: True` em todos os runs, mas "OK" refere-se à execução do `cat`, não do health check. _(Fonte: `run1.txt` a `run4.txt`, seção "TOOL CHAMADA PELO MODELO".)_
- Critério: nenhuma das K execuções usou uma sequência de tool que resultasse em execução bem-sucedida do `health.sh`. TOOL-ACC = 0.

**TOOL-CON: 4**
- Fato: mesma tool (`run_bash`) e mesmo argumento (`cat ~/scripts/health.sh`) em 5/5 runs, sem `Extra tool calls`. _(Fonte: summary, tabela "Observações brutas", colunas "Tool chamada", "Argumento completo", "Extra calls".)_
- Nota: a consistência é perfeita — na escolha errada. TOOL-CON e TOOL-ACC são dimensões complementares: TOOL-CON=4 + TOOL-ACC=0 descrevem um modelo que é "confiavelmente errado". A corretude da escolha pertence a TOOL-ACC.

**INST: 0**
- Fato: `RESPOSTA FINAL DO MODELO: (vazia)` em todos os 5 runs. _(Fonte: `run1.txt` a `run4.txt`, seção "RESPOSTA FINAL DO MODELO"; padrão confirmado no summary — campos presentes: 0/13 em todos.)_
- Critério: nenhum dos 6 pontos de verificação INST é atendido (JSON não foi produzido). INST = 0.
- Inferência: o modelo não halucinou valores — retornou vazio em vez de fabricar JSON. Isso é preferível à alucinação, mas ainda é falha total de INST.

**CON: 0**
- Fato: nenhum run produziu JSON válido. _(Fonte: summary, coluna `json_valid` = False em todos os 5 runs.)_
- Critério: "0 = comportamento imprevisível ou maioria das runs não produz JSON válido." Todos os runs falham. CON = 0.
- Nota: o comportamento É previsível (sempre cat → sempre vazio), mas o critério de CON=0 é satisfeito pela ausência total de JSON.

**JSON-ACC: 0**
- Fato: `json_acc_auto: 0` em todos os 5 runs. _(Fonte: summary, coluna "JSON-ACC"; confirmado nos runs individuais, campo `json_acc_auto`.)_

| Dimensão | Nota | Base factual |
|----------|------|--------------|
| TOOL-ACC | 0    | `cat` não executa health.sh; stdout = código-fonte bash |
| TOOL-CON | 4    | Mesma tool + mesmo argumento errado em 5/5 runs |
| INST     | 0    | Resposta vazia em 5/5 runs |
| CON      | 0    | json_valid=False em 5/5 runs |
| JSON-ACC | 0    | json_acc_auto=0 em 5/5 runs |

---

### 3.2 qwen3.5:2b

**Argumento usado:** `~/scripts/health.sh` em todos os 5 runs
_(Fonte: `S2-qwen3.5-2b-2026-04-24-run1.txt` a `run4.txt`, seção "TOOL CHAMADA PELO MODELO"; confirmado no summary.)_

**O que aconteceu:** o modelo executou o script corretamente, capturou a saída de saúde do sistema, extraiu todos os 13 campos, converteu os tipos e o timestamp corretamente — mas envolveu o JSON em bloco de código markdown (````json ... ````) em todos os 5 runs, violando a instrução "sem markdown, sem bloco de código".

**TOOL-ACC: 4**
- Fato: `run_bash` com `~/scripts/health.sh`, `Exec OK: True` em 5/5 runs; stdout retornou dados reais de CPU/GPU/memória. _(Fonte: `run1.txt` a `run4.txt`, seções "TOOL CHAMADA PELO MODELO" e "STDOUT RETORNADO".)_
- Critério: todas as K execuções usaram sequência de tool que resultou em execução bem-sucedida. TOOL-ACC = 4.

**TOOL-CON: 4**
- Fato: mesma tool e mesmo argumento em 5/5 runs; `Extra tool calls: 0` em todos. _(Fonte: summary, tabela "Observações brutas".)_

**INST: 2**
- Fato: `texto_extra: True` em todos os 5 runs — resposta contém bloco markdown. _(Fonte: `run1.txt` a `run4.txt`, seção "VALIDAÇÃO DO JSON", campo `texto extra: True`; confirmado no summary, coluna `texto_extra`.)_
- Exemplo concreto (run1, seção "RESPOSTA FINAL DO MODELO"):  
  ````json` `{...}` ` ``` `
- Fatos que SIM passam: json_valid=True, 13/13 campos, tipo_ok=True, ts_ok=True em 5/5 runs.
- Critério: desvio frequente em um dos seis pontos INST (o ponto 1: "resposta é JSON puro sem markdown") em todas as K execuções; os outros 5 pontos passam consistentemente. INST = 2.

**CON: 3**
- Fato: comportamento absolutamente idêntico em 5/5 runs — sempre markdown wrapper, sempre JSON interno correto, sempre 13/13 campos. _(Fonte: summary, colunas json_valid, campos, tipo_ok, ts_ok, texto_extra — valores idênticos em todos os runs.)_
- Critério: comportamento consistente, mas o formato de saída viola a instrução em todos os runs. Não atinge CON=4 porque "todas as K execuções produzem JSON puro" é condição do 4 (o formato é consistentemente errado). CON = 3.

**JSON-ACC: 3** (avaliação manual — json_acc_auto=-1 em todos os runs)
- Fato: `json_acc_auto: -1 (requer avaliação manual)` em 5/5 runs, pois `texto_extra=True`. _(Fonte: summary, coluna "JSON-ACC".)_
- Avaliação manual: json_valid=True ✓, json_schema_ok=True (13/13) ✓, json_types_ok=True ✓, json_values_ok=True (valores compatíveis com stdout da mesma run, verificados em run1-run4) ✓, json_clean_output=False ✗ (wrapper markdown).
- Quatro de cinco verificações passam. JSON-ACC = 3.

| Dimensão | Nota | Base factual |
|----------|------|--------------|
| TOOL-ACC | 4    | Tool correta, execução OK em 5/5 runs |
| TOOL-CON | 4    | Mesma tool + mesmo argumento em 5/5 runs |
| INST     | 2    | JSON correto mas wrapper markdown em 5/5 runs |
| CON      | 3    | Comportamento consistente; formato sistematicamente errado |
| JSON-ACC | 3    | 4/5 verificações passam; falha apenas em json_clean_output |

---

### 3.3 qwen3:14b

**Argumento usado:** `bash ~/scripts/health.sh` em todos os 5 runs
_(Fonte: `S2-qwen3-14b-2026-04-24-run1.txt` a `run3.txt`, seção "TOOL CHAMADA PELO MODELO"; confirmado no summary.)_

**O que aconteceu:** o modelo executou o script, capturou a saída e gerou JSON formatado (com indentação) sem texto adicional, sem markdown, em todos os 5 runs. Passou em todas as verificações automáticas.

**TOOL-ACC: 4**, **TOOL-CON: 4**, **INST: 4**, **CON: 4**, **JSON-ACC: 4**
- Fato: `json_valid=True`, `13/13 campos`, `tipo_ok=True`, `ts_ok=True`, `texto_extra=False`, `json_acc_auto=4` em todos os 5 runs. _(Fonte: summary, todas as colunas de validação; confirmado em `run1.txt`, `run2.txt`, `run3.txt`, seção "VALIDAÇÃO DO JSON".)_
- Fato: comportamento consistente entre runs para tool use e formato de saída, a despeito da variação de thinking.
- Observação (fato): significativa variação de thinking entre runs — run1: 9 213 chars; runs 2–5: 5 910–6 338 chars. _(Fonte: summary, coluna "thinking".)_ A variação não afeta o resultado, mas é o padrão de cold-start já documentado para este modelo em S1.

| Dimensão | Nota | Base factual |
|----------|------|--------------|
| TOOL-ACC | 4    | `bash ~/scripts/health.sh`, Exec OK em 5/5 runs |
| TOOL-CON | 4    | Mesmo argumento em 5/5 runs |
| INST     | 4    | JSON puro, 6/6 pontos em 5/5 runs |
| CON      | 4    | Estrutura e comportamento consistentes em 5/5 runs |
| JSON-ACC | 4    | json_acc_auto=4 em 5/5 runs |

---

### 3.4 gemma4:e4b

**Argumento usado:** `~/scripts/health.sh` em todos os 5 runs
_(Fonte: `S2-gemma4-e4b-2026-04-24-run1.txt` a `run3.txt`, seção "TOOL CHAMADA PELO MODELO"; confirmado no summary.)_

**O que aconteceu:** o modelo executou o script e produziu JSON minificado (em uma linha) sem markdown, sem texto adicional, em todos os 5 runs. Passou em todas as verificações automáticas.

**TOOL-ACC: 4**, **TOOL-CON: 4**, **INST: 4**, **CON: 4**, **JSON-ACC: 4**
- Fato: `json_valid=True`, `13/13 campos`, `tipo_ok=True`, `ts_ok=True`, `texto_extra=False`, `json_acc_auto=4` em todos os 5 runs. _(Fonte: summary, todas as colunas de validação; confirmado em `run1.txt`, `run2.txt`, `run3.txt`, seção "VALIDAÇÃO DO JSON".)_
- Fato: tokens totais extremamente estáveis — 1 621–1 623 em todos os runs. _(Fonte: summary, coluna `tok_total`.)_
- Fato: thinking chars = 0 no turno 2 em todos os runs _(confirmado em `run1.txt`, `run2.txt`, `run3.txt`, seção "PERFORMANCE / Turno 2")_ — consistente com o comportamento do mesmo modelo em S1.
- Fato: JSON no formato minificado (uma linha), sem indentação. _(Fonte: `run1.txt`, seção "RESPOSTA FINAL DO MODELO": `{"timestamp": "2026-04-24T16:46:21", ...}`)._

| Dimensão | Nota | Base factual |
|----------|------|--------------|
| TOOL-ACC | 4    | `~/scripts/health.sh`, Exec OK em 5/5 runs |
| TOOL-CON | 4    | Mesmo argumento em 5/5 runs |
| INST     | 4    | JSON puro, 6/6 pontos em 5/5 runs |
| CON      | 4    | Estrutura e comportamento consistentes em 5/5 runs |
| JSON-ACC | 4    | json_acc_auto=4 em 5/5 runs |

---

### 3.5 Resumo das notas — S2 Bateria 1

| Modelo         | TOOL-ACC | TOOL-CON | INST | CON | JSON-ACC | Resultado |
|----------------|----------|----------|------|-----|----------|-----------|
| qwen3.5:9b     | **0**    | 4        | **0**| **0**| **0**  | falhou    |
| qwen3.5:2b     | 4        | 4        | **2**| 3   | 3        | parcial   |
| qwen3:14b      | 4        | 4        | 4    | 4   | 4        | passou    |
| gemma4:e4b     | 4        | 4        | 4    | 4   | 4        | passou    |

---

## 4. Resultados S2B — prompt refinado

### 4.1 qwen3.5:9b — análise completa

**Argumento usado:** `~/scripts/health.sh` em todos os 5 runs
_(Fonte: `S2B-qwen3.5-9b-2026-04-24-summary.md`, tabela "Observações brutas"; confirmado em `run1.txt`, `run2.txt`, `run3.txt`, seção "TOOL CHAMADA PELO MODELO".)_

**TOOL-ACC: 4**, **TOOL-CON: 4**, **INST: 4**, **CON: 4**, **JSON-ACC: 4**

- Fato: `json_valid=True`, `13/13 campos`, `tipo_ok=True`, `ts_ok=True`, `texto_extra=False`, `json_acc_auto=4` em todos os 5 runs. _(Fonte: `S2B-qwen3.5-9b-2026-04-24-summary.md`, todas as colunas de validação.)_
- Fato: JSON minificado (uma linha) sem markdown. _(Confirmado em `S2B-qwen3.5-9b-2026-04-24-run1.txt`, `run2.txt`, `run3.txt`, seção "RESPOSTA FINAL DO MODELO".)_
- Fato: thinking chars no turno 1 = 195 em 5/5 runs; thinking chars no turno 2 = 0 em 5/5 runs. _(Confirmado nos três run files disponíveis.)_

**Conclusão:** a mudança de `"Execute o script ~/scripts/health.sh"` para `"Use a tool run_bash com o comando exato: ~/scripts/health.sh"` eliminou completamente a falha. O modelo passa com 4/4/4/4/4 em S2B. A falha em S2 era de ambiguidade de instrução, não de limitação do modelo.

---

### 4.2 qwen3.5:2b — bug de captura (runs inválidos)

**Argumento usado:** `~/scripts/health.sh` em ambos os runs
_(Fonte: `S2B-qwen3.5-2b-2026-04-24-run1.txt` e `run2.txt`, seção "TOOL CHAMADA PELO MODELO".)_

**Fatos observados:**
- Tool use correta: `run_bash` com `~/scripts/health.sh`, `Exec OK: True` em run1 e run2. _(Fonte: runs, seção "TOOL CHAMADA PELO MODELO".)_
- Stdout do script retornado corretamente (dados reais de CPU/GPU/memória). _(Fonte: `run1.txt` e `run2.txt`, seção "STDOUT RETORNADO".)_
- `RESPOSTA FINAL DO MODELO: (vazia)` em run1 e run2. _(Fonte: `run1.txt` e `run2.txt`, seção "RESPOSTA FINAL DO MODELO".)_
- json_valid=False, json_acc=0 em ambos os runs. _(Fonte: runs, seção "VALIDAÇÃO DO JSON".)_
- **Thinking chars no turno 2 = 1** em run1 e run2. _(Fonte: `run1.txt`: "Turno 2 / thinking chars: 1"; `run2.txt`: idem.)_
- Output tokens no turno 2 = 247 (run1) e 254 (run2) — o modelo gerou conteúdo. _(Fonte: runs, seção "PERFORMANCE / Turno 2".)_

**Diagnóstico do bug (detalhado na seção 6.3):** o script S2B apresenta falha na extração do `content` da resposta quando o turno 2 contém qualquer thinking (mesmo 1 char). O modelo gerou 247–254 tokens de resposta, mas o script capturou `None` e registrou `(vazia)`. Os dados do 2b em S2B são **inválidos** e precisam ser recoletados.

**Confirmação via curl direto:** teste manual com curl direto à API Ollama confirmou que o `qwen3.5:2b`, mesmo com o prompt S2B (que instrui explicitamente contra markdown e adiciona `"NÃO use markdown. NÃO use blocos de código. A resposta começa com { e termina com }"`), **continua usando wrapper markdown**. A falha de INST permanece.

**Notas para S2B qwen3.5:2b:** não atribuir — dados inválidos por bug de captura.

---

## 5. Métricas de performance

Médias calculadas excluindo run 1 (anomalia de cold start, conforme metodologia do relatório S1).
Runs considerados: 2, 3, 4, 5.

### 5.1 Comparativo S2 vs S2B — qwen3.5:9b

| Variante | tok/s médio | ms/run médio | tokens totais | thinking total |
|----------|-------------|--------------|---------------|----------------|
| S2       | 46,5        | 4 201        | 1 951         | 359            |
| S2B      | 46,4        | 5 712        | 1 753         | 195            |

**Cálculos S2 (runs 2–5):**
- ms: (4 195,8 + 4 199,9 + 4 177,2 + 4 231,3) / 4 = **4 201**
- tok/s: (46,4 + 46,5 + 46,6 + 46,6) / 4 = **46,5**
- tokens: 1 951 (idêntico em todos os runs). _(Fonte: summary, coluna `tok_total`.)_
- thinking: 359 (idêntico em todos os runs — T1=227, T2=132). _(Fonte: `run1.txt`, `run2.txt`, seção "PERFORMANCE".)_

**Cálculos S2B (runs 2–5):**
- ms: (5 697,0 + 5 694,8 + 5 709,4 + 5 746,9) / 4 = **5 712**
- tok/s: (46,5 + 46,5 + 46,4 + 46,3) / 4 = **46,4**
- tokens: (1 755 + 1 755 + 1 755 + 1 747) / 4 = **1 753**. _(Fonte: summary, coluna `tok_total`.)_
- thinking: 195 (idêntico em todos os runs — T1=195, T2=0). _(Fonte: `run1.txt`, `run2.txt`, `run3.txt`, seção "PERFORMANCE".)_

**Observação:** S2B é mais lento em ms/run (5 712 vs 4 201) apesar de ter menos tokens (1 753 vs 1 951). Explicação: em S2, a resposta final é vazia (poucos tokens para gerar); em S2B, o modelo gera o JSON completo (~146 tokens no turno 2). Os tokens totais menores em S2B refletem que o `tool_result` de S2B (saída do `health.sh`, ~200 chars) é muito menor que o de S2 (`cat health.sh` = código-fonte com ~1 100 chars), que domina o input do turno 2.

---

### 5.2 Tabela geral S2 — todos os modelos (runs 2–5)

| Modelo         | tok/s | ms/run  | tokens totais | thinking chars | JSON-ACC |
|----------------|-------|---------|---------------|----------------|----------|
| qwen3.5:2b     | 105,4 | 7 080   | 2 133         | 1 196          | 3 (manual) |
| gemma4:e4b     | 72,9  | 8 586   | 1 622         | 1 052          | 4        |
| qwen3.5:9b     | 46,5  | 4 201   | 1 951         | 359            | 0        |
| qwen3:14b      | 33,4  | 52 085  | 2 871         | 6 199          | 4        |

_(Tabela ordenada por tok/s decrescente.)_

**Cálculos detalhados:**

**qwen3.5:2b** — ms: (7 107,0 + 7 088,0 + 7 147,0 + 6 977,5) / 4 = **7 080**; tok/s: (105,5 + 105,5 + 105,3 + 105,4) / 4 = **105,4**; tokens: (2 136 + 2 136 + 2 136 + 2 125) / 4 = **2 133**; thinking: (1 198 + 1 198 + 1 199 + 1 188) / 4 = **1 196**. _(Fonte: summary, colunas ms_total, tok/s, tok_total, thinking.)_

**gemma4:e4b** — ms: (8 613,9 + 8 581,9 + 8 589,5 + 8 557,5) / 4 = **8 586**; tok/s: (72,6 + 72,9 + 73,0 + 73,1) / 4 = **72,9**; tokens: (1 623 + 1 622 + 1 622 + 1 621) / 4 = **1 622**; thinking: 1 052 (idêntico). _(Fonte: summary.)_

**qwen3.5:9b** — valores já calculados na seção 5.1.

**qwen3:14b** — ms: (54 675,6 + 51 939,3 + 48 665,9 + 53 058,4) / 4 = **52 085**; tok/s: 33,4 (idêntico); tokens: (2 956 + 2 866 + 2 761 + 2 902) / 4 = **2 871**; thinking: (6 338 + 6 223 + 5 910 + 6 324) / 4 = **6 199**. _(Fonte: summary, colunas ms_total, tok/s, tok_total, thinking — runs 2–5.)_

---

## 6. Experimento S2 vs S2B — análise comparativa

### 6.1 qwen3.5:9b

**S2 — comportamento observado:**
- Fato: o modelo chamou `run_bash` com `cat ~/scripts/health.sh` em todos os 5 runs. _(Fonte: summary e runs individuais, confirmados até run4.)_
- Fato: o stdout retornado foi o código-fonte bash do script (não dados de saúde). _(Confirmado em `run1.txt` a `run4.txt`, seção "STDOUT RETORNADO".)_
- Fato: thinking chars no turno 1 = 227, turno 2 = 132, total = 359 em todos os runs. _(Fonte: `run1.txt`, `run2.txt`, `run4.txt`, seção "PERFORMANCE".)_
- Fato: resposta final vazia em todos os runs. _(Confirmado nos run files.)_

**S2B — comportamento observado:**
- Fato: o modelo chamou `run_bash` com `~/scripts/health.sh` (comando correto) em todos os 5 runs. _(Fonte: `S2B-qwen3.5-9b-2026-04-24-summary.md` e `run1.txt`, `run2.txt`, `run3.txt`.)_
- Fato: JSON correto, sem markdown, em todos os 5 runs. _(Confirmado nos run files, json_acc_auto=4 em 5/5.)_
- Fato: thinking chars no turno 1 = 195, turno 2 = 0, total = 195 em todos os runs. _(Confirmado em `run1.txt`, `run2.txt`, `run3.txt`.)_

**Análise comparativa:**
A falha em S2 foi **100% corrigida por prompt** em S2B. O prompt original usava "Execute o script ~/scripts/health.sh" — a ambiguidade em "Execute o script" permitiu que o modelo interpretasse como "leia o arquivo do script" em vez de "rode o script". O prompt S2B especifica "Use a tool run_bash com o comando exato: ~/scripts/health.sh", eliminando a ambiguidade.

A diferença de thinking (359 em S2 vs 195 em S2B) aponta dois efeitos: (1) a instrução mais clara em S2B reduziu o pensamento no turno 1 (227 → 195 chars); (2) em S2, o turno 2 exigiu 132 chars de thinking porque o modelo recebeu resultado inesperado (código-fonte) e tentou processar; em S2B, o turno 2 tem 0 chars de thinking porque o modelo recebeu o resultado esperado (dados de saúde) e fez conversão direta.

**Conclusão (inferência):** a falha do 9b em S2 era de ambiguidade de instrução, não de limitação do modelo. Modelos sensíveis a prompt respondem à clareza da instrução. O comportamento do 9b no turno 2 (thinking=0 quando resultado é esperado, como em S1) indica que o modelo distingue "processamento direto" de "raciocínio sobre resultado inesperado."

---

### 6.2 qwen3.5:2b

**S2 — comportamento observado:**
- Fato: tool use correta (`~/scripts/health.sh`), execução OK, JSON com conteúdo correto. _(Fonte: runs 1–4 e summary.)_
- Fato: wrapper markdown presente em todos os 5 runs. _(Fonte: summary, coluna `texto_extra=True` em 5/5; confirmado em `run1.txt`, `run2.txt`, `run3.txt`, `run4.txt`.)_

**S2B — comportamento observado:**
- Fato: tool use correta, execução OK. _(Fonte: `run1.txt` e `run2.txt`, seção "TOOL CHAMADA PELO MODELO".)_
- Fato: resposta capturada como vazia por bug (ver seção 6.3). _(Fonte: `run1.txt` e `run2.txt`, seção "RESPOSTA FINAL DO MODELO: (vazia)".)_
- Fato (confirmação externa): teste via curl direto à API Ollama, com o prompt S2B, confirmou que o `qwen3.5:2b` **ainda usa wrapper markdown** mesmo com as instruções explícitas "NÃO use markdown", "A resposta começa com { e termina com }". _(Confirmado pelo usuário após identificação do bug.)_

**Análise comparativa:**
A falha de INST do 2b é de **natureza diferente** da falha do 9b. O 9b falhou por ambiguidade de instrução (corrigível); o 2b falha por comportamento de formato fortemente enraizado. O modelo ignora instruções de formato explícitas e negativas ("NÃO use markdown"), sugerindo que o padrão de "envolver código em markdown" está profundamente consolidado no treinamento do modelo e não é acessível via instrução direta.

**Conclusão (inferência):** a falha de INST do qwen3.5:2b é **resistente à instrução direta**. Isso o torna inadequado para uso em agentes que dependem de saída estruturada sem pós-processamento externo. Abordagens alternativas (estruturação de sistema, output parsing, format enforcement via gramática) precisariam ser testadas antes de descartar o modelo completamente.

---

### 6.3 Bug identificado no script S2B

**Descrição do bug:**

O script `scripts/run-s2b-benchmark.py` apresenta falha na extração do bloco `content` da resposta da API quando o turno 2 contém **qualquer** token de thinking — mesmo que seja apenas 1 char. Nessa situação, o campo `content` é capturado como `None`, e o script registra a resposta final como `(vazia)`.

**Evidência:**

- `S2B-qwen3.5-2b-2026-04-24-run1.txt`: Turno 2 tem `thinking chars: 1` e `tokens output: 247`, mas resposta = `(vazia)`. _(Fonte: `run1.txt`, seção "PERFORMANCE / Turno 2" e "RESPOSTA FINAL DO MODELO".)_
- `S2B-qwen3.5-2b-2026-04-24-run2.txt`: Turno 2 tem `thinking chars: 1` e `tokens output: 254`, mas resposta = `(vazia)`. _(Fonte: `run2.txt`, mesmas seções.)_

A presença de 247–254 tokens de output com resposta vazia confirma que o modelo gerou conteúdo; o bug está na extração, não na geração.

**Como foi identificado:**

Após observar as respostas vazias, o usuário executou curl direto à API Ollama com o mesmo prompt S2B e confirmou que o modelo efetivamente retorna uma resposta — ainda que com wrapper markdown.

**Impacto sobre os dados coletados:**

| Modelo       | Afetado? | Reasoning |
|--------------|----------|-----------|
| qwen3.5:9b   | Não      | Thinking no turno 2 = 0 em todos os runs S2B (confirmado nos run files). O bug só ocorre quando thinking > 0 no turno 2. |
| qwen3.5:2b   | Sim      | Thinking no turno 2 = 1 char em run1 e run2. Ambos os runs são inválidos. |

Os dados S2B do qwen3.5:9b são **válidos**. Os dados S2B do qwen3.5:2b são **inválidos** e precisam ser recoletados após correção do bug.

---

## 7. Análises e achados

### 7.1 Dois tipos de falha identificados

**Fato observado:**
- qwen3.5:9b (S2): falha de **decisão de ação** — o modelo decidiu executar o comando errado (`cat` em vez de executar o script). A falha ocorreu na escolha do que fazer, antes de qualquer etapa de parsing ou formatação. A ação foi consistentemente errada em 5/5 runs.
- qwen3.5:2b (S2): falha de **formato de saída** — o modelo executou a ação correta, obteve os dados certos, fez o parsing correto, mas envolveu o JSON em markdown. A falha ocorreu exclusivamente na apresentação final, não na ação ou no parsing.

**Inferência:** os dois tipos de falha têm origens distintas e respondem diferentemente a intervenções de prompt. Falhas de decisão de ação tendem a ser corrigíveis por maior especificidade da instrução (como demonstrou S2B com o 9b). Falhas de formato de saída podem ser resistentes a instruções diretas se o comportamento de formatação for fortemente consolidado no treinamento (como demonstrou o 2b).

Esta distinção é relevante para design de agentes: um agente que decide errado é perigoso; um agente que decide certo mas formata errado é corrigível com pós-processamento (parsing externo do JSON, strip de markdown).

---

### 7.2 Sensibilidade ao prompt

**Fato observado:**
- qwen3.5:9b é **sensível ao prompt** para decisão de ação: o prompt S2 com "Execute o script" gerou `cat` em 5/5 runs; o prompt S2B com "Use a tool run_bash com o comando exato: ~/scripts/health.sh" corrigiu para execução correta em 5/5 runs.
- qwen3.5:2b é **resistente ao prompt** para formato de saída: o prompt S2 com "sem markdown, sem bloco de código" gerou markdown em 5/5 runs; o prompt S2B com "NÃO use markdown. NÃO use blocos de código. A resposta começa com { e termina com }." foi confirmado via curl como insuficiente para remover o wrapper.

**Inferência:** "sensível ao prompt" não é sinônimo de "frágil". Para o 9b, a sensibilidade ao prompt é uma característica positiva — o modelo responde à clareza das instruções. Para o 2b, a resistência ao prompt em questões de formatação indica que o comportamento pode estar em um nível mais profundo (template de chat, token especial, estilo de treinamento) que não é acessível via instrução de usuário.

---

### 7.3 Posição do gemma4:e4b

**Fato observado:** gemma4:e4b passa com 4/4/4/4/4 em S2, com:
- 72,9 tok/s (segundo maior throughput da bateria, atrás apenas do 2b)
- 8 586 ms/run (latência muito inferior ao qwen3:14b)
- 1 622 tokens/run (menor token count da bateria S2, ainda menor que em S1)
- Comportamento consistente e previsível (thinking fixo em 1 052 chars, tokens estáveis em 1 621–1 623)

**Inferência:** gemma4:e4b consolida sua posição como o **modelo de melhor relação qualidade/performance** da shortlist atual. Passa no mesmo critério de qualidade que o qwen3:14b com 83% menos latência (8 586 ms vs 52 085 ms) e 74% menos tokens de thinking (1 052 vs 6 199). Ocupa 9 821 MiB de VRAM (próximo ao limite da RTX 3060), o que é uma restrição, mas viável para uso exclusivo.

---

### 7.4 Posição do qwen3:14b

**Fato observado:** qwen3:14b passa com 4/4/4/4/4 em S2, mas com:
- 33,4 tok/s (menor throughput da bateria)
- 52 085 ms/run médio (runs 2–5) — mais de 52 segundos por run
- 6 199 chars de thinking médio (muito superior aos demais modelos)
- Variação significativa de thinking entre runs (5 910–6 338 chars nos runs 2–5; 9 213 no run 1)

**Inferência:** o qwen3:14b é capaz mas custoso. Para S2 (uma pergunta com uma tool call e um JSON de ~200 tokens), gastar 52 segundos e 6 000+ chars de thinking é desproporcionalmente alto. Em S3 (multi-step, múltiplas tools), a latência e o uso de tokens de reasoning escalariam de forma preocupante. A candidatura do 14b para S3 depende de o maior poder de reasoning se traduzir em vantagem qualitativa real — o que precisa ser verificado.

---

### 7.5 Thinking chars S2 vs S2B no qwen3.5:9b

**Fato observado:**
- S2: thinking total = 359 chars (T1=227, T2=132). _(Fonte: `run1.txt` a `run4.txt`, seção "PERFORMANCE".)_
- S2B: thinking total = 195 chars (T1=195, T2=0). _(Fonte: `run1.txt` a `run3.txt`, seção "PERFORMANCE".)_

**Inferência:**
- A redução no T1 (227 → 195 chars) indica que o prompt S2B, ao especificar tool e argumento explicitamente, reduziu o espaço de decisão — o modelo precisou de menos raciocínio para determinar o que fazer.
- A eliminação do T2 (132 → 0 chars) é o achado mais relevante: em S2, o modelo recebeu código-fonte inesperado e usou 132 chars tentando extrair dados de saúde de um arquivo bash — fracassando silenciosamente. Em S2B, recebeu os dados corretos e fez passagem direta (0 thinking), consistente com o comportamento do mesmo modelo em S1 (também 0 thinking no T2 quando o resultado é direto).
- Os 132 chars de thinking no T2 de S2 são o "sinal de perturbação" — o modelo sabia que algo estava errado com o resultado, mas não conseguiu se corrigir nem sinalizar o erro corretamente (deveria ter retornado "ERRO: não consegui executar health.sh").

---

## 8. Classificação final S2 — Bateria 1

| Modelo      | TOOL-ACC | TOOL-CON | INST | CON | JSON-ACC | tok/s | ms/run  | Avança para S3?                     |
|-------------|----------|----------|------|-----|----------|-------|---------|-------------------------------------|
| gemma4:e4b  | 4        | 4        | 4    | 4   | 4        | 72,9  | 8 586   | **sim**                             |
| qwen3:14b   | 4        | 4        | 4    | 4   | 4        | 33,4  | 52 085  | **sim** (observar custo em S3)      |
| qwen3.5:9b  | 0        | 4        | 0    | 0   | 0        | 46,5  | 4 201   | **sim com prompt S2B**              |
| qwen3.5:2b  | 4        | 4        | 2    | 3   | 3        | 105,4 | 7 080   | **aguardar fix + re-run S2B**       |

**Justificativas:**

- **gemma4:e4b:** aprovado sem ressalvas. Melhor relação qualidade/performance da bateria.
- **qwen3:14b:** aprovado com observação. Qualidade 4/4/4/4/4, mas latência muito alta (52s/run). S3 dirá se o investimento em reasoning justifica o custo.
- **qwen3.5:9b:** aprovado com condição de usar prompt S2B. A falha em S2 foi de instrução ambígua, corrigida com um prompt mais explícito. O modelo é capaz e demonstrou 4/4/4/4/4 em S2B. S3 deve usar o prompt refinado como baseline.
- **qwen3.5:2b:** pendente. O comportamento de markdown wrapper é resistente a instrução direta. O bug no script S2B impede conclusão definitiva. Necessário: (1) corrigir bug, (2) re-rodar S2B, (3) se confirmada resistência ao prompt, avaliar alternativas antes de passar para S3.

---

## 9. Implicações para o laboratório

### 9.1 O que muda na shortlist

**Fato:** gemma4:e4b passou em S1 e S2 com 4/4/4/4 em todos os critérios, melhor performance relativa, comportamento previsível e estável.
**Inferência:** gemma4:e4b sobe para posição de candidato preferencial para S3. Combina confiabilidade de saída (JSON limpo, sem markdown) com velocidade adequada e uso de VRAM gerenciável.

**Fato:** qwen3.5:9b falhou em S2 com prompt original mas passou com S2B.
**Inferência:** o modelo permanece na shortlist para S3, mas com a condição de usar o prompt S2B como mínimo. A sensibilidade ao prompt é previsível e gerenciável.

**Fato:** qwen3.5:2b tem resistência ao prompt para formato de saída.
**Inferência:** se a re-run S2B confirmar que o wrapper markdown persiste mesmo com instrução explícita, o 2b será adequado apenas para uso com pós-processamento externo (strip de markdown, regex). Para uso em agentes que dependem de JSON puro, o 2b tem uma limitação funcional que não é corrigível por engenharia de prompt simples.

### 9.2 O que aprendemos sobre engenharia de prompt para agentes locais

**Achado 1 (fato):** a mesma instrução pode produzir resultados radicalmente diferentes dependendo da ambiguidade residual. A diferença entre "Execute o script ~/scripts/health.sh" e "Use a tool run_bash com o comando exato: ~/scripts/health.sh" é a diferença entre TOOL-ACC=0 e TOOL-ACC=4 no qwen3.5:9b.

**Achado 2 (inferência):** para agentes locais, especificidade de ferramenta (nome da tool + argumento exato) é mais confiável do que descrição de tarefa (verbo + objeto). Quando o agente precisa usar uma tool específica, nomear a tool explicitamente no prompt aumenta a confiabilidade.

**Achado 3 (fato):** instruções de formato explícitas e negativas ("NÃO use markdown") não são suficientes para sobrescrever comportamentos de formatação fortemente consolidados em modelos menores (qwen3.5:2b). Instrução ≠ controle.

**Achado 4 (inferência):** modelos maiores (qwen3:14b, gemma4:e4b) parecem seguir instruções de formato com mais confiabilidade do que o qwen3.5:2b, sugerindo correlação entre capacidade de instruction-following e tamanho/qualidade do treinamento.

### 9.3 Hipóteses novas levantadas por S2/S2B

**H6: Falhas de decisão de ação são mais corrigíveis por prompt do que falhas de formato de saída.**
- Base: qwen3.5:9b passou de 0 para 4 em TOOL-ACC com prompt S2B; qwen3.5:2b manteve INST=2 mesmo com instrução mais forte.
- Próximo passo: testar qwen3.5:2b com abordagem alternativa (system prompt, output grammar, few-shot com exemplo de JSON puro).

**H7: O volume de thinking no turno 2 pode ser um indicador de "perturbação" — resultado inesperado pelo modelo.**
- Base: qwen3.5:9b gerou 132 chars de thinking no T2 de S2 (resultado inesperado: código-fonte bash) vs 0 chars no T2 de S2B (resultado esperado: dados de saúde). O mesmo padrão (T2 thinking=0) ocorreu em S1 quando o resultado era trivial.
- Próximo passo: monitorar thinking chars no T2 em S3 como proxy de "o modelo recebeu o que esperava?".

**H8: A variação de thinking do qwen3:14b entre runs é estrutural e não reduz com aquecimento de sessão.**
- Base: em S1, o run1 do 14b teve 11 158 chars de thinking; runs 2–5 tiveram 2 725–3 403. Em S2, o run1 teve 9 213 chars; runs 2–5 tiveram 5 910–6 338. A variação nos runs 2–5 ainda é significativa (~7%).
- Próximo passo: verificar se a Bateria 2 (quando ocorrer) reproduz essa variabilidade para confirmar como característica estável do modelo.

**H9: gemma4:e4b pode ter arquitetura MoE, explicando throughput alto com VRAM alta.**
- Base: hipótese H2 do relatório S1, ainda não verificada.
- Próximo passo: verificar parâmetros do modelo no Ollama (ollama show gemma4:e4b).

### 9.4 O que deve ser testado em S3

Com base nos resultados de S2:
- S3 deve incluir gemma4:e4b e qwen3:14b (passaram sem ressalvas).
- S3 deve incluir qwen3.5:9b com prompt S2B como baseline (sensível a instrução, capaz quando instrução é clara).
- S3 deve aguardar re-run do qwen3.5:2b após fix do bug antes de decidir inclusão.
- S3 deve aumentar a complexidade conforme planejado no `evaluation-framework.md` — multiツstep, múltiplas tools, decisões de naming.
- S3 deve medir thinking chars no T2 como proxy de perturbação (hipótese H7).

---

## 10. Próximos passos

### Imediato

- [ ] **Corrigir bug do script S2B** — o bug causa `content=None` quando thinking presente no turno 2. Reproduzível com qwen3.5:2b (thinking=1 char no T2). Correção: revisar extração do content block na resposta da API quando thinking e content coexistem.
- [ ] **Re-rodar S2B qwen3.5:2b** (5 runs) após correção do bug, para obter dados válidos.
- [ ] **Avaliar resultado do re-run:** se qwen3.5:2b ainda usar markdown com prompt S2B, documentar como limitação funcional e explorar alternativas (system prompt, grammar constraints, few-shot).

### Médio prazo

- [ ] **Formalizar cenário S3** em `docs/benchmarks/S3-[nome].md` — baseado nos resultados de S2 e no `evaluation-framework.md` (Nível 3: pipeline multi-step).
- [ ] **Definir modelos para S3** com base na classificação final desta bateria (seção 8).
- [ ] **Verificar arquitetura do gemma4:e4b** (`ollama show gemma4:e4b`) para confirmar ou refutar hipótese H9 (MoE).
- [ ] **Registrar hipóteses H6–H9** em `docs/notes/` como entradas formais.
- [ ] **Executar Bateria 2 de S1** (STAB), ainda pendente conforme relatório S1.

### Referências desta bateria

| Arquivo | Conteúdo |
|---------|----------|
| `docs/decisions/ADR-0001-criterios-de-avaliacao.md` | Critérios e escala usados |
| `docs/benchmarks/evaluation-framework.md` | Framework, escada de complexidade |
| `docs/benchmarks/S2-health-check-json.md` | Definição do cenário S2 |
| `results/reports/S1-bateria1-relatorio-2026-04-24.md` | Referência da Bateria 1 de S1 |
| `scripts/run-s2-benchmark.py` | Script que gerou os dados S2 |
| `scripts/run-s2b-benchmark.py` | Script que gerou os dados S2B (com bug identificado) |
| `results/benchmarks/S2-*-2026-04-24-*.txt` | Runs brutos S2 (20 arquivos, 4 modelos × 5 runs) |
| `results/benchmarks/S2B-qwen3.5-9b-2026-04-24-*.txt` | Runs brutos S2B qwen3.5:9b (5 arquivos) |
| `results/benchmarks/S2B-qwen3.5-2b-2026-04-24-*.txt` | Runs brutos S2B qwen3.5:2b — inválidos (2 arquivos) |

---

_Relatório gerado em 2026-04-24 com base na leitura dos arquivos de run e summary da Bateria 1._
_S2B qwen3.5:2b: dados inválidos — aguardar re-run após correção do bug no script S2B._
