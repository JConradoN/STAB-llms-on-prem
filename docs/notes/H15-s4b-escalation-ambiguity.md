# H15 — mixed-001: Falha de Classificação de Severidade em Log Misto com CRITICAL

**Data:** 2026-04-25
**Status:** ✅ Investigada e resolvida — H15-B confirmada

---

## Diagnóstico

O S4-B apresentou `escalation_correct: False` em todos os modelos exceto
gemma4:e4b. Após inspeção do fixture e das respostas, a causa está identificada:

**O mixed-001.log contém duas linhas CRITICAL:**
level=CRITICAL service=redis status=failed
level=CRITICAL overall_status=failed

text

Pela regra do prompt: "critical = qualquer linha com level=CRITICAL"
→ mixed-001 deve ser classificado como severity=critical, escalation=immediate.

O expected.json está correto. Os modelos que falharam classificaram
mixed-001 como warning/monitor, ignorando as linhas CRITICAL presentes.

---

## Modelos e comportamento

| Modelo | Classificou mixed-001 | Correto? |
|--------|-----------------------|----------|
| gemma4:e4b | critical / immediate | ✅ |
| llama3.1:8b | warning / monitor | ❌ |
| llama3-groq-tool-use:8b | ? | ❌ (escalation_correct=False) |
| qwen3.5:9b | ? | ❌ (mesmo padrão em S3) |
| qwen3:14b | — | — (falhou em CHAIN-ACC) |

---

## Causa raiz

Os modelos que falharam foram influenciados pelo "ruído" do log misto:
4 linhas INFO/WARNING vs 2 linhas CRITICAL. Em vez de aplicar a regra
binária ("qualquer CRITICAL → severity=critical"), fizeram uma avaliação
proporcional implícita — maioria não-critical → classificaram como warning.

Esse comportamento é análogo ao tool-skipping semântico (H12): o modelo
usa atalho cognitivo (proporção de linhas) em vez de seguir a instrução
explícita (presença de qualquer CRITICAL).

---

## Relação com outras hipóteses

- **H12 (tool-skipping):** mesmo padrão — atalho semântico sobrepõe instrução explícita
- **H6 (falhas de instrução):** confirmada novamente — instrução existe e é clara,
  mas modelos menores não a seguem consistentemente
- **H10 (dimensões ortogonais):** CHAIN-ACC=4 (leu o arquivo) + TRIAGE-ACC=2
  (classificou errado) — ferramenta usada, análise incorreta. Dimensões independentes confirmadas.

---

## Implicação para o artigo

**gemma4:e4b é o único modelo que aplica corretamente regras binárias em logs mistos.**
Os demais fazem avaliação proporcional implícita, ignorando a instrução explícita.

Isso reforça a descoberta principal: falhas são de instrução/seguimento de regra,
não de capacidade de leitura. Todos os modelos leram o arquivo — apenas gemma4:e4b
aplicou a regra corretamente.

Contribuição para o framework: logs mistos com CRITICAL entre ruído INFO/WARNING
são o caso de teste mais discriminante para avaliar seguimento de instrução binária.
Recomenda-se incluir esse padrão explicitamente em benchmarks de agentes locais.

---

## Correção na H15 original

A hipótese inicial (H15-A: fixture ambíguo) foi descartada após inspeção.
O fixture está correto. A falha é dos modelos — H15-B confirmada.
