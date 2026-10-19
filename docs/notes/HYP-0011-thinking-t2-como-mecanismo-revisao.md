# HYP-0011 — Thinking no turno 2 como mecanismo de revisão pré-output

## Data
2026-04-24

## Status
Não confirmada — evidência inicial de S3 Bateria 1, com precaução de N=1.

## Enunciado

O thinking gerado pelo qwen3:14b no turno 2 (após receber o resultado da tool e antes de emitir a resposta final) pode funcionar como um mecanismo de **revisão pré-output**: o modelo verifica o conteúdo que vai emitir, identificando e corrigindo possíveis desvios de formato ou conteúdo antes de finalizá-los. Isso explicaria por que o qwen3:14b mantém INST=4 e CON=4 em S3 apesar da complexidade semântica crescente, enquanto o qwen3.5:9b — que tem T2 thinking=0 — apresenta INST=2 com desvios de formato não corrigidos.

**Corolário:** o gemma4:e4b atingir INST=4 com T2 thinking=0 indica que T2 thinking **não é condição necessária** para conformidade de formato — é um dos caminhos possíveis. O gemma4 alcança o mesmo resultado por treinamento de formato mais robusto.

---

## Base factual

### Thinking T2 por modelo em S3

| Modelo         | T2 thinking — info-001 | T2 thinking — warning-001 | T2 thinking — critical-001 | T2 thinking — mixed-001 | INST S3 |
|----------------|------------------------|---------------------------|---------------------------|------------------------|---------|
| qwen3:14b      | 976 chars              | 1 729 chars               | 1 244 chars               | 1 577 chars            | **4**   |
| gemma4:e4b     | 0 chars                | 0 chars                   | 0 chars                   | 0 chars                | **4**   |
| qwen3.5:9b     | 0 chars                | 0 chars                   | 0 chars                   | 0 chars                | **2**   |

_(Fonte: seção "PERFORMANCE / Turno 2" dos 12 case files S3.)_

### Consistência histórica do padrão

- **S1:** qwen3:14b usa T2 thinking em todos os runs (runs 2–5: 807 chars no run1, variação menor nos demais). gemma4 e qwen3.5:9b: T2=0 consistentemente. _(Fonte: relatório S1, seção 5.4.)_
- **S2:** qwen3:14b usa T2 thinking em todos os 5 runs. qwen3.5:9b S2 orig: T2=132 chars ao receber resultado inesperado (código-fonte bash); T2=0 em S2B ao receber resultado esperado. _(Fonte: relatório S2, seções 3.3, 5.5.)_
- **S3:** padrão confirma: qwen3:14b T2>0 em 4/4 casos; outros dois T2=0 em 4/4 casos.

O padrão T2>0 para o qwen3:14b é estável em S1, S2 e S3 — não é artefato de um cenário específico.

### Evidência de suporte — qwen3.5:9b S2 T2 thinking como sinal de perturbação

Em S2 (prompt original), qwen3.5:9b recebeu código-fonte bash em vez de dados de saúde (resultado inesperado) e gerou T2 thinking=132 chars — o único caso em que este modelo produziu T2>0 — sem conseguir se corrigir. Em S2B, recebeu resultado esperado e produziu T2=0 com resposta correta. _(Fonte: relatório S2, seção 7.5 — hipótese H7.)_

Isso sugere que, para o 9b, o T2 thinking aparece como reação a perturbação, mas não é capaz de corrigir o problema (falhou em S2, produziu resposta vazia). O qwen3:14b, por outro lado, usa T2 thinking preventivamente em todos os casos — não só nos perturbados.

### Variação do T2 thinking do qwen3:14b entre casos

| Caso | T2 thinking | Complexidade do cenário |
|------|-------------|------------------------|
| info-001 | 976 chars | Mais simples — todas as linhas INFO |
| warning-001 | 1 729 chars | Intermediário — 2 tipos de WARNING |
| critical-001 | 1 244 chars | Alto — 3 linhas CRITICAL explícitas |
| mixed-001 | 1 577 chars | Alto — níveis mistos (INFO+WARNING+CRITICAL) |

O caso warning-001 gerou o maior T2 thinking (1 729 chars), mais do que o critical-001 (1 244). Isso é consistente com a hipótese de revisão: classificar um cenário de warning — que exige distinguir "nenhuma CRITICAL" e "pelo menos uma WARNING" — pode demandar mais verificação do que um cenário de critical, onde o log explicita CRITICAL em múltiplas linhas. O modelo pode estar confirmando que não há CRITICAL antes de emitir `"severity": "warning"`.

---

## Camada do sistema envolvida

**Modelo — comportamento de raciocínio multi-turno específico do qwen3:14b.**

O thinking T2 não é induzível por prompt padrão nos outros modelos testados (gemma4 e 9b não produzem T2>0 com os prompts atuais). É uma característica do template de reasoning do qwen3:14b — provavelmente relacionada ao seu treinamento para usar o thinking como processo de autoconferência, não apenas como espaço de planejamento inicial.

Não envolve mudança de prompt, schema de tool, orquestração, parser ou hardware.

---

## Critério de confirmação / refutação

### Confirmada se

1. Rodar qwen3.5:9b com instrução explícita de revisão no T2 ("antes de responder, verifique se o JSON está sem markdown") induz T2 thinking>0 e reduz a taxa de markdown wrapper — demonstrando que T2 thinking é causalmente ligado à conformidade de formato.
2. Em S4 ou cenários futuros com temperatura>0, o volume de T2 thinking do qwen3:14b em um run dado correlacionar positivamente com a conformidade de formato naquele run (mais thinking T2 → menos desvios de formato).
3. Se for possível suprimir o thinking T2 do qwen3:14b (via prompt ou configuração), e isso causar degradação de INST/CON — seria evidência forte de causalidade.

### Confirmada parcialmente se

- A instrução de revisão no 9b induz T2>0 e **reduz** (mas não elimina) os desvios de formato. Isso sugere que T2 thinking é um fator causal parcial.

### Refutada se

1. Induzir T2 thinking no qwen3.5:9b via prompt não alterar a taxa de desvios de formato — indicando que o thinking T2 é epifenômeno, não mecanismo de correção.
2. O qwen3:14b apresentar INST<4 em algum cenário futuro apesar de manter T2>0 — indicando que T2 thinking não é suficiente para garantir conformidade.

### Observação sobre o corolário

A hipótese é compatível com o resultado do gemma4:e4b (INST=4 com T2=0) porque postula que T2 thinking é **um caminho** para conformidade de formato, não o único. O gemma4 pode atingir o mesmo resultado por mecanismo diferente (comportamento de template mais rigoroso no treinamento). A hipótese seria refutada se o gemma4 precisasse de T2 thinking para manter INST=4 em cenários de maior complexidade.

---

## Próximo passo de teste

### Teste 1 — Indução de T2 thinking no qwen3.5:9b

Adicionar ao prompt de S3 do qwen3.5:9b (no turno 2, via system prompt ou instrução extra) algo como:

```
Antes de emitir o JSON final, verifique internamente:
1. O JSON começa com { e termina com }?
2. Não há markdown, blocos de código, nem texto antes ou depois?
Se houver, corrija antes de responder.
```

Registrar:
- Se T2 thinking aumenta para o 9b
- Se a taxa de markdown wrapper cai
- Se CLASS-ACC e PARSE-ACC se mantêm em 4

### Teste 2 — Temperatura>0 no qwen3:14b

Rodar qwen3:14b no cenário S3 com temperatura=0,5, K=5 repetições por caso.
Registrar T2 thinking por run e comparar com presença/ausência de desvios de formato.
Se T2 thinking maior correlacionar com menos desvios, a hipótese ganha suporte quantitativo.

### Teste 3 — Gemma4 em cenário de maior complexidade

Rodar gemma4:e4b em S4 (ou cenário multi-step) e verificar se mantém T2=0 e INST=4.
Se gemma4 mantiver INST=4 sem T2 thinking em S4, confirma que T2 thinking não é condição necessária para conformidade — o modelo tem outro mecanismo.
Se gemma4 começar a ter desvios de formato em S4 sem T2 thinking, sugere que T2 thinking torna-se necessário em complexidade maior.

---

## Relação com hipóteses anteriores

| Hipótese | Relação |
|----------|---------|
| H7 (S2): T2 thinking como sinal de perturbação | H11 estende H7: para o qwen3:14b, T2 thinking é preventivo (sempre presente), não apenas reativo a perturbação. Para o 9b, H7 ainda se aplica (T2 aparece só quando perturbado). |
| HYP-0010: acurácia e formato são ortogonais | H11 fornece mecanismo que explicaria por que o qwen3:14b evita a dissociação — o T2 reviewing "sincroniza" acurácia e formato ao verificar o output antes de emitir. |

---

## Referências

| Arquivo | Relevância |
|---------|-----------|
| `results/reports/S3-bateria1-relatorio-2026-04-24.md` | Fonte primária — seções 4.2, 5.1, 8.3 |
| `results/reports/S2-bateria1-relatorio-2026-04-24.md` | Evidência de suporte — seções 3.3, 7.5 (H7) |
| `results/reports/S1-bateria1-relatorio-2026-04-24.md` | Estabelece T2=0 como padrão histórico de gemma4 e 9b — seção 5.4 |
| `docs/decisions/ADR-0001-criterios-de-avaliacao.md` | Definição de INST, CON |
| `docs/notes/HYP-0010-acuracia-semantica-e-formato-sao-ortogonais.md` | Hipótese complementar |

---

## Atualização 2026-04-25 — Novos modelos S1→S4

### Novos dados de thinking T2

| Modelo | T2 thinking | INST | Grounding | Perfil |
|--------|------------|------|-----------|--------|
| llama3.1:8b | 0 chars (todos os cenários) | 4 | Real ✅ | Formato estável sem thinking |
| llama3-groq-tool-use:8b | 0 chars (todos os cenários) | 4 | Real ✅ | Formato estável sem thinking |
| mistral:7b | 0 chars | 4 (S2B) | Fabricado ❌ | Formato ok, grounding zero |

### Implicação para H11

**Corolário reforçado:** llama3.1:8b e llama3-groq-tool-use:8b confirmam que
T2 thinking=0 é compatível com INST=4 — não é condição necessária para
conformidade de formato. gemma4:e4b, llama3.1:8b e llama3-groq-tool-use:8b
atingem INST=4 sem T2 thinking por mecanismos distintos (treinamento robusto
de formato ou fine-tuning).

**Nova evidência sobre limites do T2 thinking:** qwen3:14b usa T2 thinking
preventivamente e manteve INST=4 em S3, mas falhou em CHAIN-ACC em S4
(tool-skipping — H12). Isso demonstra que T2 thinking melhora conformidade
de formato mas não previne falhas de decisão de tool use. São mecanismos
que atuam em camadas diferentes do comportamento do modelo.

**Mistral:7b como caso extremo:** T2=0 + grounding=0 + INST=4 (estrutural).
O modelo não usa thinking para revisar e não tem grounding real — mas mantém
conformidade de formato. Reforça que formato, thinking e grounding são
capacidades independentes.

### Relação com H15

O caso S4-B (mixed-001 classificado errado) mostra que nenhum dos novos
modelos usou T2 thinking para revisar a classificação de severidade.
O gemma4:e4b, que passou em S4-B, também não usa T2 thinking — logo a
capacidade de aplicar regras binárias corretamente em logs mistos não
depende de T2 thinking, mas de treinamento de instruction-following.

### Status atualizado

**Confirmada parcialmente — corolário fortalecido.**
T2 thinking é um mecanismo de revisão presente no qwen3:14b mas ausente
nos demais. Sua presença melhora conformidade de formato nesse modelo
específico, mas não é condição necessária nem suficiente para acurácia
global do agente. A hipótese principal aguarda o teste de indução de
T2 thinking no qwen3.5:9b para avaliar causalidade.
