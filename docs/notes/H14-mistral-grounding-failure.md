# H14 — Falha de Grounding Silenciosa (mistral:7b)

**Data:** 2026-04-25
**Modelo afetado:** mistral:7b (Mistral, 4.4GB)
**Status:** Descartado em S2 — falha de grounding não corrigível por instrução

---

## Observação

Em S2 e S2B, o mistral:7b produziu JSON estruturalmente perfeito (13/13 campos,
tipos corretos, sem texto extra) sem nunca ter chamado a tool run_bash.
Os dados são 100% fabricados:

- Timestamp: "2023-05-15T14:30:00" — 3 anos no passado, inventado
- GPU: "NVIDIA GeForce GTX 1650" — hardware errado (servidor tem RTX 3060 12GB)
- RAM total: 8192 MB — errado (servidor tem 32768 MB / 32GB)

O modelo ignorou completamente a instrução de chamar a tool em ambos os prompts
(S2 original e S2B com instrução forte "Use a tool run_bash com o comando exato").

---

## Comportamento S2 vs S2B

| Cenário | tool chamada | json_acc_auto | Dados reais? |
|---------|-------------|---------------|--------------|
| S2 (5 runs) | NENHUMA | -1 (texto extra) | Não — fabricados |
| S2B run1 | NENHUMA | 4 ✅ | Não — fabricados |

**O S2B gerou um falso positivo (json_acc_auto=4) porque:**
- O prompt refinado eliminou o wrapper markdown (texto extra: False)
- O validator automático só verifica estrutura, não origem dos dados
- O modelo atendeu os critérios formais sem executar nenhuma ação real

---

## Classificação da falha

| Dimensão | Nota | Descrição |
|----------|------|-----------|
| TOOL-ACC | 0/4 | Nunca chamou tool em S2 nem S2B |
| INST | 2/4 | Seguiu formato mas ignorou instrução de tool use |
| CON | 1/4 | Dados fabricados — internamente consistentes mas falsos |
| JSON-FORMAT | 4/4 | Estrutura perfeita — falso positivo perigoso |

---

## Distinção em relação a outros anti-patterns

| Anti-pattern | Comportamento | Detectável automaticamente? |
|---|---|---|
| 3a (deepseek) | Erro HTTP 400 | ✅ Sim — erro explícito |
| 3b/3c (phi4-mini) | Serializa tool no content / alucina | ✅ Sim — tool_calls ausente + conteúdo suspeito |
| **H14 (mistral)** | **JSON perfeito com dados fabricados** | **❌ Não — falso positivo no validator** |

A falha H14 é a mais perigosa para sistemas de produção: o agente parece
funcionar corretamente, passa em todas as validações de schema, mas entrega
dados completamente inventados. Só é detectável por inspeção do conteúdo
(ex: comparar hardware reportado com hardware real).

---

## Implicação para o framework

O validator automático (json_acc_auto) deve ser expandido com:
- Verificação de `tool_calls` ocorrido antes de atribuir nota 4
- Flag `GROUNDING-FAIL` quando json_acc_auto=4 mas tool_calls=NENHUMA
- Regra: json_acc_auto ≤ 2 se nenhuma tool foi chamada, independente do schema

---

## Implicação para o artigo

Contribuição metodológica nova: a validação de schema é necessária mas não
suficiente para avaliar agentes com tool use. Um modelo pode atingir pontuação
máxima no eixo de formato sem ter executado nenhuma ação real — produzindo
resultados indistinguíveis de dados reais sem inspeção do conteúdo.

Isso reforça a necessidade do framework S1→S4 em escada: S1 valida tool use
antes de S2 avaliar JSON, impedindo que falhas de grounding passem despercebidas.
