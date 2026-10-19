# H13 — Alucinação de Execução de Tool (phi4-mini)

**Data:** 2026-04-25
**Modelo afetado:** phi4-mini:latest (Microsoft Phi4-mini, 2.5GB)
**Status:** Descartado — não apto para tool use via API Ollama

---

## Observação

Durante validação de suporte a tool use via `validate-tools.py` e teste manual com
`curl`, o phi4-mini apresentou dois comportamentos distintos e nenhum deles correto:

### Comportamento 3b (validate-tools.py)
O modelo serializou manualmente o JSON da tool dentro do campo `content`:
"content": "Para começar, vou usar a função get_system_status...

text

O campo `tool_calls` estava ausente. O modelo sabe da existência da tool e tenta
representá-la, mas não usa o protocolo correto da API.

### Comportamento 3c (curl manual)
O modelo ignorou completamente a tool e alucionou uma resposta fabricada:

```json
{
  "content": "Para encontrar a temperatura atual em Paris, preciso usar o serviço
  de temperatura. Por favor, espere um momento.\n\n[Processo Detalhado: Usar o
  comando fornecido para obter a temperatura no local especificado]\n\n[Resultado]:
  A temperatura em Paris atualmente é 16°C."
}
```

`tool_calls`: ausente. Temperatura "16°C": fabricada.

---

## Classificação

| Tipo | Descrição | Modelo(s) |
|------|-----------|-----------|
| Anti-pattern 3a | Erro HTTP 400 — sem suporte na API | deepseek-r1:8b |
| Anti-pattern 3b | JSON da tool serializado no content, sem tool_calls | phi4-mini (variante) |
| Anti-pattern 3c | Ignora a tool, alucina resposta no content | phi4-mini (variante) |

O phi4-mini oscila entre 3b e 3c entre tentativas — comportamento imprevisível,
que é exatamente o problema central investigado neste projeto.

---

## Implicação para o artigo

O phi4-mini demonstra que a tag "ferramentas" no catálogo Ollama não garante
conformidade com o protocolo `tool_calls` da API. O modelo tem *awareness* semântico
da existência de ferramentas (sabe que deve usá-las) mas não tem *conformidade de
protocolo* (não usa o campo correto da API).

Isso introduz uma distinção importante na taxonomia de falhas:
- **Falha de protocolo** (3a/3b/3c): o modelo não usa a estrutura `tool_calls`
- **Falha de decisão** (H12): o modelo usa a estrutura mas decide não chamar a tool

Essa distinção pode ser explorada no Artigo A como uma dimensão adicional da
taxonomia de falhas.

---

## Decisão

phi4-mini **descartado** do roster de modelos.
Documentado como anti-pattern para o framework de avaliação.
