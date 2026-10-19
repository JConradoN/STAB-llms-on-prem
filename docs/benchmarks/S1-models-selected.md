# S1 – Modelos selecionados para benchmark

## Data de seleção

2026-04-24

## Critérios de seleção

- Tag `ferramentas` oficial no catálogo Ollama.
- Pesos locais disponíveis (sem cloud-only).
- Tamanho viável para RTX 3060 12 GB (inteiro na VRAM ou com offload controlado).
- Representar papéis distintos: controle ultra-leve, controle inferior, controle principal,
  reasoning, agente/visão, linha vazando VRAM, comparativo de geração anterior.
- Fonte: catálogo Ollama filtrado por ferramentas, ordenado por mais recentes, cruzado
  com ollama list do servidor em 2026-04-24.

---

## Shortlist ativa

| Papel                        | Modelo                    | Tamanho | Família  | Atualizado | Status no servidor |
|------------------------------|---------------------------|---------|----------|------------|--------------------|
| Controle ultra-leve          | qwen3.5:2b                | 2.7 GB  | Qwen3.5  | 3 semanas  | pull necessário    |
| Controle inferior            | qwen3.5:4b                | 3.4 GB  | Qwen3.5  | 3 semanas  | disponível         |
| Controle principal           | qwen3.5:9b                | 6.6 GB  | Qwen3.5  | 3 semanas  | disponível         |
| Reasoning                    | deepseek-r1:8b            | 5.2 GB  | DeepSeek | 9 meses    | disponível         |
| Comparativo geração anterior | qwen3:8b                  | 5.2 GB  | Qwen3    | 6 meses    | disponível         |
| Agente/visão                 | gemma4:e4b                | 9.6 GB  | Gemma4   | 1 semana   | disponível         |
| Linha vazando VRAM           | qwen3:14b                 | 9.3 GB  | Qwen3    | 6 meses    | disponível         |
| Baseline legado tool-use     | llama3-groq-tool-use:8b   | 4.7 GB  | Llama3   | 1 ano      | disponível         |

---

## Ordem de teste recomendada para S1

Seguindo o princípio: sempre começar pelo mais simples e verificável.

1. qwen3.5:2b — ver o limite mínimo absoluto de tool use viável.
2. qwen3.5:4b — controle inferior dentro da mesma família.
3. qwen3.5:9b — controle principal, referência central do benchmark.
4. deepseek-r1:8b — comparativo reasoning vs instrução em S1.
5. gemma4:e4b — comparativo de família diferente, mais recente.
6. qwen3:8b — comparativo de geração anterior do Qwen.
7. qwen3:14b — linha vazando VRAM, medir ganho vs custo.
8. llama3-groq-tool-use:8b — baseline legado, rodar por último para referência histórica.

---

## Modelos fora do escopo S1

| Modelo                    | Motivo de exclusão do S1                        |
|---------------------------|-------------------------------------------------|
| nemotron-cascade-2:latest | 24 GB — inviável para benchmark consistente     |
| fortejus-llm:latest       | Modelo customizado, papel não definido no bench |
| claude-sonnet-4-6:latest  | Proxy/alias, não é peso local real              |
| nomic-embed-text:latest   | Embedding — não é modelo de agente              |
| qwen3.5-fast:9b           | Redundante com qwen3.5:9b                       |
| qwen3.5:latest            | Mesmo ID que qwen3.5:9b — redundante            |
| qwen3.5-48k:latest        | Variante contexto reduzido — redundante         |

---

## Pull pendente

docker exec ollama ollama pull qwen3.5:2b

---

## Próximos passos

- Realizar pull do qwen3.5:2b.
- Criar plano de experimento S1 iniciando pelo qwen3.5:9b como referência central.
- Registrar resultados em results/benchmarks/ usando o formato definido em
  docs/benchmarks/evaluation-framework.md.
- Após S1 completo com todos os modelos da shortlist, revisar quais avançam para S2.
