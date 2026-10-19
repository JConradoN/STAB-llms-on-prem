# EXP-S4B-v2 — Instrução Binária Explícita para Classificação de CRITICAL em Log Misto

**Data planejamento:** 2026-04-25
**Status:** Planejado — rodar após STAB2
**Relacionado a:** H15, H6, H12

---

## Motivação

No S4-B (Bateria 1), todos os modelos exceto gemma4:e4b classificaram
mixed-001 como warning/monitor, ignorando duas linhas CRITICAL presentes
no log. A instrução do prompt original diz:

> "critical: qualquer linha com level=CRITICAL"

Apesar de explícita, a regra não impediu os modelos de fazer avaliação
proporcional implícita (maioria de linhas não-critical → classificaram como warning).

Esse padrão é análogo ao H12 (tool-skipping semântico) e ao H6 (falhas
corrigíveis por instrução). O S4-B-v2 testa se uma instrução binária
mais explícita resolve a falha.

---

## Desenho do experimento

**Variável manipulada:** instrução de classificação de severidade no prompt S4.

**Variante original (S4-B):**
critical: qualquer linha com level=CRITICAL

warning: nenhuma CRITICAL, mas pelo menos uma WARNING

info: todas as linhas são INFO

text

**Variante experimental (S4-B-v2):**
critical: qualquer linha com level=CRITICAL — MESMO QUE A MAIORIA DAS
LINHAS SEJA INFO OU WARNING. Uma linha CRITICAL é suficiente.

warning: nenhuma linha CRITICAL, mas pelo menos uma WARNING

info: todas as linhas são INFO

text

**Fixture:** idêntico ao S4-B (critical-001, critical-003, mixed-001)
**Expected:** idêntico ao S4-B-expected.json
**Modelos:** llama3.1:8b, llama3-groq-tool-use:8b, qwen3.5:9b
(os que falharam em S4-B — gemma4:e4b não precisa pois já passou)

---

## Resultado esperado

Se H6 se confirma (falhas são corrigíveis por instrução):
- Modelos que falharam em S4-B passam em S4-B-v2
- escalation_correct=True para mixed-001
- TRIAGE-ACC sobe de 2 para 4

Se falha é estrutural (instrução não resolve):
- Modelos continuam classificando mixed-001 como warning
- TRIAGE-ACC permanece 2
- Sugere limitação de capacity, não de instrução

---

## Implicação para o artigo

Qualquer resultado é contribuição:
- Se resolver: reforça H6 e o anti-pattern de instrução binária fraca
- Se não resolver: evidencia limite de instruction-following em logs mistos,
  mesmo com instrução explícita — nova categoria de falha estrutural

Comparação direta S4-B vs S4-B-v2 é um experimento controlado limpo,
análogo ao H12 (nomes semânticos vs opacos).

---

## Pendências antes de rodar

1. Criar script run-s4b-v2-benchmark.py com prompt modificado
2. Rodar após STAB2 (para não misturar dados)
3. Comparar resultados com S4-B Bateria 1 e Bateria 2 (STAB)

---

## Resultados (2026-04-25)

| Modelo | S4-B orig | S4B-v2 | escalation | rank_ok | TRIAGE-ACC | thinking T2 |
|--------|-----------|--------|-----------|---------|-----------|-------------|
| gemma4:e4b | 4 | — (já passou) | ✅ | ✅ | 4 | não |
| llama3.1:8b | 2 | 2 | ❌→❌ | ✅→✅ | sem melhora | não |
| llama3-groq-tool-use:8b | 2 | 2 | ❌→❌ | ✅→✅ | sem melhora | não |
| qwen3.5:9b | 2 | 3 | ❌→✅ | ✅→❌ | melhora parcial | sim (306 chars) |

## Conclusão

### H6 (falhas corrigíveis por instrução)
- **Confirmada parcialmente para qwen3.5:9b:** instrução binária melhorou
  escalation_correct de False para True, mas introduziu erro em rank_order.
- **Refutada para llama3.1:8b e llama3-groq-tool-use:8b:** instrução
  binária não alterou o comportamento — falha estrutural confirmada.

### H15-B (dificuldade real de síntese em log misto)
Confirmada e ampliada. Três categorias de corrigibilidade identificadas:

| Categoria | Modelo(s) | Comportamento |
|-----------|-----------|---------------|
| Intrínseco | gemma4:e4b | Aplica regra binária sem instrução especial |
| Corrigível | qwen3.5:9b | Melhora com instrução explícita + ativa thinking T2 |
| Estrutural | llama3.1:8b, llama3-groq-tool-use:8b | Não responde à instrução |

### H11 (thinking T2 como mecanismo de revisão)
qwen3.5:9b foi o único modelo que ativou thinking T2 (306 chars) e o único
que respondeu à instrução binária. Correlação direta: instrução mais restritiva
→ thinking ativado → mudança de comportamento em escalation.
Suporte adicional para H11.

### Custo do thinking
qwen3.5:9b: 22.3s e 3285 tokens vs ~10s e ~2450 tokens dos outros.
O thinking T2 tem custo real de latência — relevante para sistemas de produção.

## Implicação para o artigo

Experimento controlado com resultado tripartido — contribuição metodológica clara:
a corrigibilidade de falhas de instruction-following varia por modelo e não é
garantida mesmo com instruções de alta especificidade. Benchmarks de agentes
devem incluir variantes de instrução para mapear essa dimensão.
