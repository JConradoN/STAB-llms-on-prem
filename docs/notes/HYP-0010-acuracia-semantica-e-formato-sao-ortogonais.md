# HYP-0010 — Acurácia semântica e conformidade de formato são dimensões ortogonais

## Data
2026-04-24

## Status
Não confirmada — evidência inicial de S3 Bateria 1.

## Enunciado

A qualidade de classificação semântica (acurácia de leitura, interpretação e extração de campos) e a qualidade de formato de saída (conformidade com instrução de apresentação — JSON puro, sem markdown, sem texto adicional) são dimensões **ortogonais** nos modelos testados.

A consequência prática: um modelo pode ter CLASS-ACC=4 e PARSE-ACC=4 com INST=2 no mesmo run — o conteúdo é correto e o formato é errado simultaneamente, sem que um afete o outro. A relação de cada modelo com instruções de formato é uma característica estrutural do modelo (consolidada em treinamento), não uma função do prompt ou da complexidade da tarefa.

---

## Base factual

### Evidência principal — S3 Bateria 1

**qwen3.5:9b:**
- CLASS-ACC=4 e PARSE-ACC=4 em 4/4 casos: `severity_match=True`, `primary_issue_match=True`, `secondary_issues_match=True`, `host_match=True`, `timestamp_match=True` em todos. _(Fonte: seções "VALIDAÇÃO DETALHADA" dos 4 case files S3.)_
- INST=2 e CON=2: markdown wrapper (` ```json ... ``` `) presente em 2/4 casos (warning-001 e mixed-001), violando a instrução "Responda APENAS com o JSON. Sem markdown." _(Confirmado em `S3-qwen3.5-9b-2026-04-24-case-warning-001.txt` e `case-mixed-001.txt`, seção "RESPOSTA FINAL DO MODELO".)_
- Nos 2 casos com markdown, o conteúdo interno é idêntico ao esperado: json_valid=True, 7/7 campos corretos. O markdown é camada de apresentação que envolve o JSON correto sem alterá-lo.

**gemma4:e4b e qwen3:14b:**
- CLASS-ACC=4, PARSE-ACC=4, INST=4 e CON=4 em 4/4 casos cada. Ambos demonstram que é possível ter acurácia perfeita E conformidade de formato perfeita com instrução padrão. _(Confirmado nos respectivos case files S3.)_

### Evidência de suporte — S2/S2B

**qwen3.5:9b S2 (prompt original):** TOOL-ACC=0, INST=0 — a falha era de decisão de ação (`cat` em vez de executar o script), não de acurácia semântica. Não houve output JSON para avaliar conteúdo.

**qwen3.5:9b S2B (prompt refinado):** TOOL-ACC=4, INST=4, JSON-ACC=4 — com instrução de tool explícita + formato muito forçado ("NÃO use markdown. A resposta começa com {"), o modelo produziu JSON puro em 5/5 runs com conteúdo correto. Confirma que a acurácia semântica estava presente desde S2; o que variou foi a força da instrução de formato. _(Fonte: relatório S2, seções 4.1 e 6.1.)_

### Padrão transversal

Em nenhum run de S2 ou S3 um modelo que produziu JSON válido (extraído do output) errou o conteúdo semântico. Quando o JSON foi extraível, estava correto. As falhas foram sempre de ação (S2 orig 9b: ação errada → sem JSON) ou de formato (S3 9b: JSON correto dentro de markdown) — nunca de interpretação semântica.

---

## Camada do sistema envolvida

**Modelo — comportamento de template de output consolidado em treinamento.**

A ortogonalidade observada não é propriedade do prompt, do schema da tool, da orquestração ou do parser. É uma propriedade de como cada modelo trata a etapa de formatação da resposta final:

- **gemma4:e4b**: formato intrinsecamente estável — não requer instrução de formato explícita. Comportamento consolidado no treinamento.
- **qwen3:14b**: formato estável com instrução padrão; pensa no T2 antes de emitir (possível mecanismo de revisão — ver HYP-0011).
- **qwen3.5:9b**: formato instável com instrução moderada; requer instrução de alta especificidade para suprimir o markdown wrapper, e mesmo assim não há garantia de 100%.
- **qwen3.5:2b**: formato resistente a qualquer instrução direta — markdown wrapper persiste mesmo com "NÃO use markdown. A resposta começa com {". _(Fonte: NOTE-0004.)_

A acurácia semântica (classificação, extração de campos, identificação de primary_issue) envolve a camada de compreensão e raciocínio do modelo — aparentemente separada da camada de formatação de output.

---

## Critério de confirmação / refutação

### Confirmada se

1. Em cenários futuros (S4, Bateria 2), qwen3.5:9b continua produzindo CLASS-ACC=4 e PARSE-ACC=4 em runs com e sem markdown wrapper — ou seja, a taxa de erros de acurácia permanece 0 independentemente da presença do markdown.
2. Variações na instrução de formato (mais explícita vs. mais genérica) alteram INST do 9b sem alterar CLASS-ACC/PARSE-ACC do mesmo modelo.
3. O mesmo padrão se repete em modelos adicionados à shortlist no futuro.

### Refutada se

1. Em algum cenário futuro, a presença do markdown wrapper no 9b correlacionar com aumento de erros de conteúdo (o markdown indicaria confusão do modelo que também afeta a classificação).
2. Instrução de formato mais restritiva causar degradação de CLASS-ACC ou PARSE-ACC em qualquer modelo (indicando trade-off entre acurácia e conformidade de formato).
3. A acurácia semântica do 9b cair para abaixo de 4 em algum cenário enquanto o formato melhora — sugerindo que o "esforço" de obedecer a instrução de formato compete com a acurácia semântica.

---

## Próximo passo de teste

**Teste direto (S3 Bateria 2):**

Rodar qwen3.5:9b nos mesmos 4 casos de S3 com duas variantes de prompt em paralelo:

- **Variante A** (padrão S3): "Responda APENAS com o JSON. Sem markdown. Sem texto adicional."
- **Variante B** (estilo S2B): "NÃO use markdown. NÃO use blocos de código. A resposta começa com { e termina com }."

Para cada variante, registrar:
- CLASS-ACC e PARSE-ACC por caso (espera-se: 4 em ambos, independente da variante)
- Taxa de markdown wrapper por variante (espera-se: maior em A do que em B)
- Se CLASS-ACC ou PARSE-ACC variar entre variantes, a hipótese H10 teria evidência de refutação.

**Critério quantitativo:** se CLASS-ACC e PARSE-ACC permanecerem 4/4 em ambas as variantes enquanto a taxa de markdown wrapper variar, a ortogonalidade está demonstrada empiricamente.

---

## Implicação para design de agentes

Se H10 for confirmada, o design de agentes locais deve tratar acurácia semântica e conformidade de formato como preocupações separadas com estratégias distintas:

- Acurácia semântica: seleção de modelo com capacidade adequada para a tarefa.
- Conformidade de formato: seleção de modelo com comportamento de output estável **ou** uso de instrução de formato de alta especificidade **ou** pós-processamento externo (strip de markdown, parser permissivo).

Combinar um modelo semanticamente fraco com instrução de formato forte não resolve a acurácia. Combinar um modelo semanticamente forte com instrução de formato fraca pode ser suficiente se o modelo for "instruction-stable" (gemma4, 14b). Para o 9b, ambas as dimensões precisam ser endereçadas separadamente.

---

## Referências

| Arquivo | Relevância |
|---------|-----------|
| `results/reports/S3-bateria1-relatorio-2026-04-24.md` | Fonte primária — seções 3.3, 5.1, 5.3, 8.1 |
| `results/reports/S2-bateria1-relatorio-2026-04-24.md` | Evidência de suporte — seções 4.1, 6.1, 7.1, 7.2 |
| `docs/decisions/ADR-0001-criterios-de-avaliacao.md` | Definição de INST, CON, CLASS-ACC |
| `docs/notes/NOTE-0004-qwen3.5-2b-descartado-s3.md` | Caso extremo de resistência a instrução de formato |
| `docs/notes/HYP-0011-thinking-t2-como-mecanismo-revisao.md` | Hipótese complementar sobre mecanismo do qwen3:14b |

---

## Atualização 2026-04-25 — Novos modelos S1→S4

### Novos dados

| Modelo | INST/formato | Acurácia semântica | Padrão |
|--------|-------------|-------------------|--------|
| llama3.1:8b | 4 (sem wrapper) | Falhou mixed-001 S3, S4-B/C | Formato estável, acurácia parcial |
| llama3-groq-tool-use:8b | 4 (sem wrapper) | Falhou S4-B/C | Formato estável, acurácia parcial |
| mistral:7b | 4 (sem wrapper em S2B) | Dados 100% fabricados | Falso positivo — H14 |

### Implicação para H10

**H10 recebe suporte adicional e uma nuance importante:**

llama3.1:8b e llama3-groq-tool-use:8b confirmam a ortogonalidade — ambos
mantêm formato estável (INST=4, sem markdown) enquanto a acurácia semântica
varia por caso (S3 mixed-001, S4-B/C).

**Nuance nova (mistral:7b / H14):** existe um terceiro cenário além dos dois
mapeados originalmente (formato errado + conteúdo certo / formato certo + conteúdo certo):
formato certo + conteúdo fabricado. O modelo nunca chamou a tool e inventou dados
estruturalmente perfeitos. O json_acc_auto=4 mascarou a falha completa de grounding.

Isso expande a taxonomia de H10:
- Dimensão 1: conformidade de formato (INST)
- Dimensão 2: acurácia semântica (CON/CLASS-ACC)
- **Dimensão 3 (nova): grounding — os dados têm origem real ou são fabricados?**

As três dimensões são ortogonais: um modelo pode ter INST=4, CON=4 (schema válido)
e grounding=0 (dados inventados) — como demonstrou o mistral:7b.

### Status atualizado

**Confirmada e expandida** — dados de S1→S4 com 5 modelos distintos suportam a
ortogonalidade. A adição da dimensão de grounding fortalece a contribuição para o artigo.
