# S1 Bateria 1 — Relatório de Resultados

## 1. Cabeçalho

| Campo       | Valor                                             |
|-------------|---------------------------------------------------|
| Data        | 2026-04-24                                        |
| Cenário     | S1 – Health check estático (Nível 1)              |
| Hardware    | RTX 3060 12 GB, i5-10400F, 32 GB RAM, Ubuntu 24  |
| Script      | scripts/run-s1-benchmark.py                       |
| Temperatura | 0                                                 |
| K           | 5 runs por modelo                                 |
| Timeout     | 120s por run                                      |
| Tool        | run_bash (execução real via subprocess no host)   |
| API         | POST http://localhost:11434/api/chat              |

---

## 2. Modelos avaliados

| Modelo              | Família  | VRAM em uso (MiB) | Tamanho (Ollama) | Status    |
|---------------------|----------|-------------------|------------------|-----------|
| qwen3.5:2b          | Qwen3.5  | 3829              | 2.7 GB           | passou    |
| qwen3.5:4b          | Qwen3.5  | 5493–5495         | 3.4 GB           | passou    |
| qwen3.5:9b          | Qwen3.5  | 7951–7953         | 6.6 GB           | passou    |
| qwen3:14b           | Qwen3    | 9437              | 9.3 GB           | passou    |
| gemma4:e4b          | Gemma4   | 9821              | 9.6 GB           | passou    |
| deepseek-r1:8b      | DeepSeek | n/a               | 5.2 GB           | excluído  |

**Fonte dos valores de VRAM:** campo "VRAM usada" do stdout de `~/scripts/health.sh` capturado nos runs.
**deepseek-r1:8b:** excluído por erro 400 da API Ollama ("does not support tools") — documentado em `docs/notes/NOTE-0002-deepseek-r1-sem-suporte-tools.md`.

---

## 3. Resultados de tool use (CON, TOOL-CON, INST, TOOL-ACC)

Notas atribuídas com base na leitura dos arquivos de run (runs 1–5 de cada modelo).
Escala 0–4 conforme `docs/decisions/ADR-0001-criterios-de-avaliacao.md`, seção 4.4.
Fatos observados e inferências separados abaixo de cada nota.

---

### qwen3.5:2b

**TOOL-ACC: 4**
- Fato: em todos os 5 runs chamou `run_bash` com argumento `~/scripts/health.sh`; `Execução OK: True` em todos.
- Fato: não foi registrada nenhuma tool inexistente nem path inválido.

**TOOL-CON: 4**
- Fato: mesmo nome de tool (`run_bash`) e mesmo argumento (`~/scripts/health.sh`) em todos os 5 runs. `Extra tool calls: 0` em todos.
- Inferência: argumento sem `bash` explícito (diferente do qwen3.5:4b e qwen3:14b); não afeta validade, é variação de estilo dentro da família.

**INST: 4**
- Fato: resposta final idêntica ao stdout do script em todos os 5 runs; nenhum comentário, resumo, saudação ou texto adicional em nenhum run.
- Fato: frase de erro especificada não foi emitida (script executou com sucesso em todos os runs).

**CON: 4**
- Fato: comportamento idêntico nas 5 runs — tool chamada, output retornado literalmente, sem adição de conteúdo. Variações de valores (CPU%, temperatura, memória) são do sistema, não do modelo.
- Inferência: thinking chars variam levemente entre runs (t2: 109–114 chars), mas isso não afeta o conteúdo da resposta final.

---

### qwen3.5:4b

**TOOL-ACC: 4**
- Fato: em todos os 5 runs chamou `run_bash` com argumento `bash ~/scripts/health.sh`; `Execução OK: True` em todos.
- Fato: o argumento `bash ~/scripts/health.sh` é funcionalmente equivalente a `~/scripts/health.sh` — ambos resultam em execução bem-sucedida do script.

**TOOL-CON: 4**
- Fato: mesmo nome de tool e mesmo argumento (`bash ~/scripts/health.sh`) em todos os 5 runs. `Extra tool calls: 0` em todos.
- Fato: consistência total dentro dos 5 runs; a forma `bash ~/scripts/health.sh` difere de qwen3.5:2b e qwen3.5:9b, mas é interna ao modelo e constante.

**INST: 4**
- Fato: resposta final idêntica ao stdout do script em todos os 5 runs; nenhum texto adicional em nenhum run.

**CON: 4**
- Fato: comportamento idêntico nas 5 runs — tool chamada, output retornado literalmente, sem adição.
- Fato: thinking chars fixos em 402 em todos os 5 runs (t1=280, t2=122) — menor variação interna observada na família Qwen3.5.

---

### qwen3.5:9b

**TOOL-ACC: 4**
- Fato: em todos os 5 runs chamou `run_bash` com argumento `~/scripts/health.sh`; `Execução OK: True` em todos.

**TOOL-CON: 4**
- Fato: mesmo nome de tool e mesmo argumento em todos os 5 runs. `Extra tool calls: 0` em todos.

**INST: 4**
- Fato: resposta final idêntica ao stdout do script em todos os 5 runs; nenhum texto adicional.

**CON: 4**
- Fato: comportamento idêntico nas 5 runs.
- Fato: thinking chars zero no turno 2 em todos os runs (apenas turno 1 raciocina). Diferença comportamental em relação ao 2b e 4b — o modelo não raciocina ao devolver o resultado da tool.
- Inferência: a ausência de thinking no turno 2 é consistente e não afeta a qualidade da resposta — pode indicar que o modelo reconhece o turno 2 como uma operação de passagem direta, não de raciocínio.

---

### qwen3:14b

**TOOL-ACC: 4**
- Fato: em todos os 5 runs chamou `run_bash` com argumento `bash ~/scripts/health.sh`; `Execução OK: True` em todos.

**TOOL-CON: 4**
- Fato: mesmo nome de tool e mesmo argumento em todos os 5 runs. `Extra tool calls: 0` em todos.

**INST: 4**
- Fato: resposta final idêntica ao stdout do script em todos os 5 runs; nenhum texto adicional.

**CON: 4**
- Fato: comportamento de tool use e conteúdo da resposta final idênticos nas 5 runs.
- Fato: tokens totais variam entre runs 2–5 (1661–1830) — variação maior do que nos demais modelos, causada por thinking interno variável.
- Inferência: a variação de tokens e thinking não afeta CON (dimensão do output final), mas é relevante para STAB (será avaliado na Bateria 2). A anomalia do run 1 (94 177 ms, 11 158 thinking chars) é tratada na seção 5.

---

### gemma4:e4b

**TOOL-ACC: 4**
- Fato: em todos os 5 runs chamou `run_bash` com argumento `~/scripts/health.sh`; `Execução OK: True` em todos.

**TOOL-CON: 4**
- Fato: mesmo nome de tool e mesmo argumento em todos os 5 runs. `Extra tool calls: 0` em todos.

**INST: 4**
- Fato: resposta final idêntica ao stdout do script em todos os 5 runs; nenhum texto adicional.

**CON: 4**
- Fato: comportamento idêntico nas 5 runs.
- Fato: thinking chars fixos em 955 no turno 1 e 0 no turno 2 nos runs 2–5. Mesma característica do qwen3.5:9b: sem thinking no turno de devolução do resultado.
- Fato: menor token count total da bateria (~1112 tokens por run) — resposta mais enxuta com o mesmo resultado correto.

---

### Resumo das notas — Bateria 1

| Modelo         | TOOL-ACC | TOOL-CON | INST | CON | Média |
|----------------|----------|----------|------|-----|-------|
| qwen3.5:2b     | 4        | 4        | 4    | 4   | 4.0   |
| qwen3.5:4b     | 4        | 4        | 4    | 4   | 4.0   |
| qwen3.5:9b     | 4        | 4        | 4    | 4   | 4.0   |
| qwen3:14b      | 4        | 4        | 4    | 4   | 4.0   |
| gemma4:e4b     | 4        | 4        | 4    | 4   | 4.0   |
| deepseek-r1:8b | —        | —        | —    | —   | —     |

**STAB:** n/a — aguardar Bateria 2.

**Nota metodológica:** todas as notas 4/4/4/4 indicam que S1 (Nível 1) não diferencia modelos por qualidade de comportamento. A diferenciação nesta bateria é exclusivamente por performance (seção 4). Isso é esperado e confirma o design da escada de complexidade do `evaluation-framework.md`.

---

## 4. Métricas de performance

Médias calculadas excluindo run 1 (anomalia de cold start — modelo ainda não carregado em VRAM).
Runs considerados: 2, 3, 4, 5.

| Modelo         | tok/s médio | ms/run médio | tokens totais médios | thinking chars médios |
|----------------|-------------|--------------|----------------------|-----------------------|
| qwen3.5:2b     | 105.9       | 4 493        | 1 405                | 369                   |
| gemma4:e4b     | 73.0        | 8 202        | 1 112                | 955                   |
| qwen3.5:4b     | 66.4        | 7 203        | 1 418                | 402                   |
| qwen3.5:9b     | 46.4        | 9 307        | 1 384                | 278                   |
| qwen3:14b      | 33.8        | 30 053       | 1 742                | 3 064                 |
| deepseek-r1:8b | n/a         | n/a          | n/a                  | n/a                   |

_(Tabela ordenada por tok/s decrescente.)_

**Cálculos detalhados (runs 2–5):**

**qwen3.5:2b:**
tok/s: (106,0 + 105,8 + 105,6 + 106,1) / 4 = **105,9**
ms: (4487,0 + 4493,5 + 4484,9 + 4506,5) / 4 = **4493**
tokens: (1405 + 1405 + 1405 + 1403) / 4 = **1405**
thinking: (371 + 366 + 371 + 366) / 4 = **369**

**qwen3.5:4b:**
tok/s: (66,2 + 66,5 + 66,5 + 66,4) / 4 = **66,4**
ms: (7204,3 + 7188,4 + 7232,8 + 7187,4) / 4 = **7203**
tokens: (1416 + 1418 + 1418 + 1418) / 4 = **1418**
thinking: (402 + 402 + 402 + 402) / 4 = **402**

**qwen3.5:9b:**
tok/s: (46,3 + 46,4 + 46,4 + 46,4) / 4 = **46,4**
ms: (9327,4 + 9319,7 + 9330,8 + 9249,0) / 4 = **9307**
tokens: (1384 + 1386 + 1386 + 1380) / 4 = **1384**
thinking: (278 + 278 + 278 + 278) / 4 = **278**

**qwen3:14b:**
tok/s: (33,7 + 33,8 + 33,8 + 33,7) / 4 = **33,8**
ms: (30814,4 + 27726,1 + 29059,5 + 32611,8) / 4 = **30053**
tokens: (1771 + 1661 + 1705 + 1830) / 4 = **1742**
thinking: (3136 + 2725 + 2993 + 3403) / 4 = **3064**

**gemma4:e4b:**
tok/s: (72,9 + 73,0 + 73,1 + 73,1) / 4 = **73,0**
ms: (8211,6 + 8204,9 + 8184,9 + 8207,2) / 4 = **8202**
tokens: (1111 + 1111 + 1111 + 1113) / 4 = **1112**
thinking: (955 + 955 + 955 + 955) / 4 = **955**

### Eficiência VRAM vs. throughput

| Modelo         | VRAM (MiB) | tok/s | tok/s por GiB de VRAM |
|----------------|------------|-------|-----------------------|
| qwen3.5:2b     | 3 829      | 105,9 | 28,4                  |
| qwen3.5:4b     | 5 494      | 66,4  | 12,4                  |
| gemma4:e4b     | 9 821      | 73,0  | 7,6                   |
| qwen3.5:9b     | 7 952      | 46,4  | 5,9                   |
| qwen3:14b      | 9 437      | 33,8  | 3,7                   |

**Observação:** `qwen3.5:2b` apresenta a melhor eficiência de VRAM da bateria (28,4 tok/s por GiB). `gemma4:e4b` tem a segunda melhor velocidade absoluta com VRAM próxima ao limite de 12 GB.

---

## 5. Anomalias e observações notáveis

### 5.1 Run 1 — anomalia de cold start (todos os modelos)

- **Fato:** o run 1 de todos os modelos apresenta duration significativamente maior do que os runs 2–5.
  - qwen3.5:2b: run 1 = 10 541 ms vs. média 2–5 = 4 493 ms (+2,3×)
  - qwen3.5:4b: run 1 = 15 172 ms vs. média 2–5 = 7 203 ms (+2,1×)
  - qwen3.5:9b: run 1 = 19 067 ms vs. média 2–5 = 9 307 ms (+2,0×)
  - qwen3:14b: run 1 = 94 178 ms vs. média 2–5 = 30 053 ms (+3,1×)
  - gemma4:e4b: run 1 = 21 610 ms vs. média 2–5 = 8 202 ms (+2,6×)
- **Inferência:** o overhead do run 1 é causado pelo carregamento do modelo na VRAM antes do primeiro token. Runs 2–5 reutilizam o modelo já carregado.
- **Impacto:** run 1 excluído das médias de performance para evitar distorção. Esta exclusão é justificada e deve ser mantida nas próximas baterias.

### 5.2 qwen3:14b — variação anômala de thinking no run 1

- **Fato:** thinking chars no run 1 = 11 158 (turno 1: 10 351, turno 2: 807). Nos runs 2–5, thinking chars = 2 725–3 403.
- **Fato:** token total no run 1 = 3 498. Nos runs 2–5 = 1 661–1 830.
- **Fato:** tok/s permanece estável entre todos os runs (~33,7–33,8), indicando que o modelo processa a mesmos velocidade — o run 1 simplesmente gerou mais tokens de reasoning.
- **Inferência:** a anomalia do run 1 no qwen3:14b pode ser causada por raciocínio adicional na primeira execução (ausência de cache de KV, contexto "frio"). Isso é diferente dos demais modelos onde o run 1 é mais lento mas não gera significativamente mais tokens.
- **Relevância para STAB:** a variabilidade de thinking (2 725–3 403 nos runs 2–5) é ~25%, superior à variabilidade dos outros modelos. A Bateria 2 determinará se esse padrão se repete.

### 5.3 qwen3.5:4b e qwen3:14b — argumento com `bash` explícito

- **Fato:** qwen3.5:4b e qwen3:14b usaram `bash ~/scripts/health.sh` enquanto qwen3.5:2b, qwen3.5:9b e gemma4:e4b usaram `~/scripts/health.sh`.
- **Fato:** ambos os formatos resultaram em execução bem-sucedida.
- **Inferência:** a presença ou ausência de `bash` explícito parece não ser determinada pelo tamanho do modelo, mas possivelmente pelo template de tool use de cada família (Qwen3.5 4b e Qwen3 14b compartilham essa característica).
- **Impacto em TOOL-CON:** não afeta a nota (4) pois o argumento é consistente dentro das runs do mesmo modelo.

### 5.4 qwen3.5:9b e gemma4:e4b — thinking zero no turno 2

- **Fato:** qwen3.5:9b e gemma4:e4b produziram thinking_chars = 0 no turno 2 em todos os runs. qwen3.5:2b e qwen3.5:4b produziram thinking_chars > 0 no turno 2.
- **Inferência:** modelos que não raciocinam ao devolver o resultado da tool podem estar tratando o turno 2 como passagem direta (comportamento mais eficiente para S1). Modelos que raciocinam no turno 2 podem estar verificando o resultado antes de enviá-lo — comportamento potencialmente mais adequado em tarefas de maior complexidade.
- **Impacto em S1:** nenhum — o conteúdo final é idêntico. Relevante para cenários S2/S3 onde a verificação do resultado seria valiosa.

### 5.5 deepseek-r1:8b — exclusão por incompatibilidade de API

- **Fato:** runs 1 e 2 retornaram HTTP 400: `"deepseek-r1:8b does not support tools"`.
- **Fato:** o benchmark foi interrompido após 2 runs (conforme NOTE-0002).
- **Impacto:** modelo removido da shortlist ativa. Lição documentada: verificar suporte a tools antes de incluir modelo no benchmark.

### 5.6 gemma4:e4b — menor token count da bateria

- **Fato:** gemma4:e4b gerou em média 1 112 tokens por run (runs 2–5), versus 1 384–1 418 para os modelos Qwen3.5.
- **Inferência:** o gemma4:e4b produz respostas mais compactas nos dois turnos, sem comprometer o conteúdo (saída literal do script). Isso sugere que o template de tool use do Gemma4 é mais enxuto. Relevante para cenários com maior volume de chamadas.

---

## 6. Hipóteses levantadas nesta bateria

Hipóteses derivadas dos dados observados — nenhuma foi confirmada nem refutada pela Bateria 1 isolada.

**H1: S1 (Nível 1) é simples demais para diferenciar modelos por qualidade comportamental.**
- Base: todos os 5 modelos completados obtiveram 4/4/4/4 em CON, TOOL-CON, INST, TOOL-ACC.
- Próximo passo: confirmar se isso se mantém na Bateria 2 (STAB) e se S2 revela diferenciação.

**H2: O throughput (tok/s) é inversamente proporcional ao tamanho do modelo na RTX 3060.**
- Base: qwen3.5:2b (106 tok/s, 3,7 GB VRAM) → qwen3:14b (34 tok/s, 9,2 GB VRAM).
- Exceção aparente: gemma4:e4b (73 tok/s, 9,6 GB VRAM) — velocidade alta com VRAM alta. Pode ser arquitetura MoE ou quantização diferente.
- Próximo passo: verificar arquitetura e quantização do gemma4:e4b.

**H3: A variação de thinking chars do qwen3:14b entre runs é um comportamento estrutural do modelo, não artefato do run 1.**
- Base: runs 2–5 ainda mostram variação de 25% nos thinking chars (2 725–3 403).
- Próximo passo: verificar se a Bateria 2 reproduz essa variabilidade.

**H4: O suporte a tools via API Ollama não está garantido pela tag "ferramentas" do catálogo.**
- Base: deepseek-r1:8b tem tag "ferramentas" mas retornou erro 400.
- Próximo passo: validar todos os modelos restantes da shortlist com o procedimento da NOTE-0002 antes de rodar o benchmark.

**H5: Modelos que não raciocinam no turno 2 (qwen3.5:9b, gemma4:e4b) podem ser mais frágeis em tarefas que exigem verificação do resultado.**
- Base: ausência de thinking no turno 2 sugere passagem direta sem validação.
- Próximo passo: observar comportamento em S2 (parsing leve), onde a verificação do resultado seria mais relevante.

---

## 7. Próximos passos

### Imediato (antes de avançar para S2)

- [ ] Executar Bateria 2 para todos os 5 modelos aprovados (mínimo 12h após Bateria 1).
      Comando: `python3 scripts/run-s1-benchmark.py <modelo>`
- [ ] Calcular STAB comparando notas da Bateria 1 vs. Bateria 2.
- [ ] Validar suporte a tools dos modelos ainda não testados da shortlist:
      `qwen3.5:2b` (pull pendente), `qwen3:8b`, `llama3-groq-tool-use:8b`
      Comando de validação: `docs/notes/NOTE-0002-deepseek-r1-sem-suporte-tools.md`

### Médio prazo (após STAB confirmado)

- [ ] Formalizar ADR sobre critério de exclusão por falta de suporte a tools.
- [ ] Formalizar cenário S2 (health.sh + parsing JSON) conforme `evaluation-framework.md`, seção 5.
- [ ] Revisar se gemma4:e4b usa arquitetura MoE (explicaria tok/s alto com VRAM alta).
- [ ] Registrar hipóteses H1–H5 como entradas formais em `docs/notes/`.

### Referências desta bateria

| Arquivo | Conteúdo |
|---------|----------|
| `docs/decisions/ADR-0001-criterios-de-avaliacao.md` | Critérios e escala usados |
| `docs/benchmarks/evaluation-framework.md` | Framework e cenário S1 |
| `docs/benchmarks/S1-models-selected.md` | Shortlist e tamanhos |
| `docs/notes/NOTE-0002-deepseek-r1-sem-suporte-tools.md` | Exclusão do deepseek-r1:8b |
| `scripts/run-s1-benchmark.py` | Script que gerou os dados |
| `results/benchmarks/S1-*-2026-04-24-*.txt` | Runs brutos (25 arquivos) |

---

_Relatório gerado manualmente em 2026-04-24 com base na leitura dos arquivos de run e summary da Bateria 1._
_Próxima revisão: após Bateria 2 (STAB)._
