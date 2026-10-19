# S2 – Health check com parsing e geração de JSON estruturado

## 1. Posição na escada de complexidade

Referência: `evaluation-framework.md`, seções 2 e 5.

Este cenário ocupa o **Nível 2** da escada de complexidade do laboratório `llms-on-prem`.

**Pré-requisito obrigatório:** resultados satisfatórios em S1 (Nível 1), com STAB confirmado na Bateria 2.

| Cenário | Nível | Adiciona em relação ao anterior |
|---------|-------|---------------------------------|
| S1 – Health check estático | 1 | Linha de base: tool use + passagem literal da saída |
| **S2 – Health check JSON** | **2** | **Parsing da saída + JSON estruturado com tipos exatos** |
| S3 – Pipeline de PDFs (a definir) | 3 | Multi-step, múltiplas tools, decisões de naming |

---

## 2. Descrição

- **Nome:** S2 – Health check com parsing e geração de JSON estruturado
- **Nível:** 2 (conforme `evaluation-framework.md`, seção 2)
- **Script:** `~/scripts/health.sh`
- **Tool disponível:** `run_bash` (definição idêntica ao S1)

### Objetivo

O agente deve:

1. Executar `~/scripts/health.sh` via `run_bash`.
2. Capturar a saída completa do script.
3. Extrair campos específicos da saída (timestamp, CPU, memória, GPU).
4. Converter formatos onde necessário (data PT-BR → ISO 8601; strings com `%`, `MB`, `MiB`, `°C` → números).
5. Gerar um JSON válido seguindo **exatamente** o schema da seção 3 — sem texto adicional, sem markdown, sem comentários.

### O que S2 adiciona em relação a S1

| Capacidade | S1 | S2 |
|------------|----|----|
| Tool use via `run_bash` | obrigatório | obrigatório |
| Passagem literal da saída do script | sim | **não** — parsing obrigatório |
| Extração de campos específicos | não | **sim** |
| Geração de formato estruturado (JSON) | não | **sim** |
| Seguir schema com tipos exatos (`int` vs `float`) | não | **sim** |
| Conversão de data PT-BR → ISO 8601 | não | **sim** |
| Strip de unidades para número (`%`, `MB`, `°C`, `MiB`) | não | **sim** |
| Extração de campo composto (`X MiB / Y MiB` → dois inteiros separados) | não | **sim** |

---

## 3. Schema JSON esperado (referência de validação)

Schema canônico para validação dos resultados. O modelo deve produzir JSON compatível com esta estrutura, com os tipos exatos indicados.

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SS",
  "cpu": {
    "uso_pct": <float>,
    "temperatura_c": <int>
  },
  "memoria": {
    "total_mb": <int>,
    "usada_mb": <int>,
    "livre_mb": <int>,
    "disponivel_mb": <int>
  },
  "gpu": {
    "nome": "<string>",
    "uso_pct": <int>,
    "temperatura_c": <int>,
    "vram_usada_mib": <int>,
    "vram_livre_mib": <int>,
    "vram_total_mib": <int>
  }
}
```

### Tabela de conversões esperadas

Mapeamento de cada campo da saída do `health.sh` para o campo correspondente no JSON:

| Campo JSON | Label no health.sh | Exemplo de valor bruto | Valor esperado no JSON | Conversão necessária |
|------------|-------------------|------------------------|------------------------|----------------------|
| `timestamp` | linha após `=== SAÚDE DO SISTEMA ===` | `24/04/2026 15:04:35` | `"2026-04-24T15:04:35"` | data PT-BR → ISO 8601 (`DD/MM/YYYY HH:MM:SS` → `YYYY-MM-DDTHH:MM:SS`), sem timezone |
| `cpu.uso_pct` | `Uso:` (bloco CPU) | `3.4%` | `3.4` | strip `%`, converter para float |
| `cpu.temperatura_c` | `Temperatura:` (bloco CPU) | `39.0°C` | `39` | strip `°C`, truncar para int — **não** `39.0` |
| `memoria.total_mb` | `Total:` | `31957 MB` | `31957` | strip ` MB`, converter para int |
| `memoria.usada_mb` | `Usada:` | `9988 MB` | `9988` | strip ` MB`, converter para int |
| `memoria.livre_mb` | `Livre:` | `3636 MB` | `3636` | strip ` MB`, converter para int |
| `memoria.disponivel_mb` | `Disponível:` | `21969 MB` | `21969` | strip ` MB`, converter para int |
| `gpu.nome` | linha `GPU:` | `GPU: NVIDIA GeForce RTX 3060` | `"NVIDIA GeForce RTX 3060"` | extrair string após `GPU: ` |
| `gpu.uso_pct` | `Uso:` (bloco GPU) | `0 %` | `0` | strip ` %`, converter para int |
| `gpu.temperatura_c` | `Temp:` (bloco GPU) | `52°C` | `52` | strip `°C`, converter para int |
| `gpu.vram_usada_mib` | `VRAM usada:` | `9821 MiB / 12288 MiB` | `9821` | extrair valor **antes** do ` / `, converter para int |
| `gpu.vram_livre_mib` | `VRAM livre:` | `2097 MiB` | `2097` | strip ` MiB`, converter para int |
| `gpu.vram_total_mib` | `VRAM usada:` | `9821 MiB / 12288 MiB` | `12288` | extrair valor **após** o ` / `, converter para int |

**Observações críticas:**

- `cpu.temperatura_c` é `int` no schema — a saída do script pode vir como `39.0°C` (com decimal). O modelo deve produzir `39`, não `39.0`.
- `gpu.vram_total_mib` **não é** a soma de `vram_usada_mib + vram_livre_mib`. Deve ser extraído da notação `X MiB / Y MiB` (o `Y` é o total declarado pelo driver). A soma dos dois pode diferir do total por overhead de memória reservada pelo sistema.
- Os campos `TOP 3 PROCESSOS` da saída do `health.sh` devem ser **ignorados** — não fazem parte do schema.

---

## 4. Instrução de teste (prompt fixo)

Texto exato enviado ao modelo. **Nunca alterar entre runs** para garantir comparabilidade entre baterias e modelos.

```
Execute o script ~/scripts/health.sh, capture a saída e extraia os dados
de sistema para gerar um JSON válido com o seguinte schema exato:

{
  "timestamp": "<data e hora no formato ISO 8601: YYYY-MM-DDTHH:MM:SS>",
  "cpu": {
    "uso_pct": <número decimal>,
    "temperatura_c": <inteiro>
  },
  "memoria": {
    "total_mb": <inteiro>,
    "usada_mb": <inteiro>,
    "livre_mb": <inteiro>,
    "disponivel_mb": <inteiro>
  },
  "gpu": {
    "nome": "<string>",
    "uso_pct": <inteiro>,
    "temperatura_c": <inteiro>,
    "vram_usada_mib": <inteiro>,
    "vram_livre_mib": <inteiro>,
    "vram_total_mib": <inteiro>
  }
}

Responda APENAS com o JSON válido, sem texto adicional, sem markdown, sem bloco de código.
Se não conseguir executar o script, responda apenas: ERRO: não consegui executar health.sh
```

---

## 5. O que é considerado sucesso

### Tool use

- O agente decide executar `~/scripts/health.sh` via `run_bash`.
- A execução retorna a saída do script sem erro.
- Nenhuma tool adicional além de `run_bash` é chamada.

### Saída final (JSON)

- A resposta é **JSON puro**: sem texto antes, sem texto depois, sem markdown, sem bloco de código (` ``` `).
- O JSON é **sintaticamente válido** (parseável por qualquer parser JSON padrão).
- O JSON contém **exatamente os campos** do schema da seção 3: nenhum campo extra, nenhum campo faltando.
- **Tipos estão corretos:**
  - `cpu.uso_pct` é float (ex.: `3.4`, não `"3.4%"` nem `3`).
  - Todos os demais campos numéricos são inteiros (sem casas decimais).
  - Strings são strings (com aspas duplas, não números).
- **Valores são compatíveis com a saída do script na mesma run:**
  - `timestamp` corresponde à data/hora da saída do `health.sh` convertida para ISO 8601.
  - Campos numéricos correspondem aos valores do script com strips corretos de unidades.
  - `gpu.vram_total_mib` foi extraído da notação `X / Y` (o `Y`), não calculado como soma.
  - Os campos `TOP 3 PROCESSOS` não aparecem no JSON.

### Em caso de falha real

- O agente responde exatamente: `ERRO: não consegui executar health.sh`
- Não tenta inventar valores.

---

## 6. Aplicando as métricas ao cenário S2

Critérios e escala 0–4 definidos em `docs/decisions/ADR-0001-criterios-de-avaliacao.md`.

### CON (Consistência de resposta)

**Diferença em relação a S1:** em S1, CON media a constância do passthrough literal. Em S2, os *valores* do JSON mudam legitimamente entre runs (dados ao vivo do sistema). CON deve focar na consistência da *estrutura*, do *comportamento de parsing* e do *formato de saída* — não na igualdade de valores.

- Procedimento:
  - Executar S2 K vezes. Para cada run, extrair: campos presentes no JSON, tipos de cada campo, formato da resposta (JSON puro vs. JSON com texto).
  - Verificar se a estrutura é idêntica entre todas as runs, independentemente dos valores.

- Nota sugerida:
  - 4: todas as K execuções produzem JSON puro com exatamente a mesma estrutura e tipos corretos; nenhuma variação de comportamento.
  - 3: pequenas variações isoladas (ex.: uma run com crase de markdown ao redor, mas JSON internamente correto).
  - 2: estrutura inconsistente entre runs (ex.: às vezes omite `disponivel_mb`, às vezes inclui campo extra como `processos`).
  - 1: comportamento muito variável — algumas runs não produzem JSON, outras produzem JSON incompleto ou com tipos misturados.
  - 0: comportamento imprevisível ou maioria das runs não produz JSON válido.

### TOOL-CON (Consistência de tool use)

Critério **idêntico ao S1** — a fase de tool use não muda em S2.

- Procedimento:
  - Verificar se o agente usa consistentemente `run_bash` com `~/scripts/health.sh` (ou `bash ~/scripts/health.sh`) em todas as runs.
  - Verificar ausência de tools adicionais.

- Nota sugerida:
  - 4: mesma tool + mesmo comando em todas as K execuções.
  - 3: pequenas variações benignas de argumento (ex.: `bash ~/...` vs `~/...`), sem impacto na execução.
  - 2: às vezes tenta outra abordagem, mas ainda executa o script correto.
  - 1: chama tools diferentes, com risco de comportamento imprevisível.
  - 0: raramente ou nunca chama a tool correta.

### INST (Aderência a instruções)

**Mais exigente que S1.** Em S1, INST media apenas a ausência de texto extra. Em S2, INST inclui aderência ao schema, tipos e conversões.

- Procedimento:
  - Para cada execução, verificar os seis pontos:
    1. A resposta é JSON puro (sem texto, sem markdown, sem bloco de código)?
    2. O JSON contém exatamente os campos do schema (nem a mais, nem a menos)?
    3. Os tipos estão corretos (`float` onde especificado `float`, `int` onde especificado `int`)?
    4. As conversões de formato foram aplicadas (data ISO 8601; números sem unidades)?
    5. `gpu.vram_total_mib` foi extraído corretamente (não calculado como soma)?
    6. Se houve erro, a mensagem de erro exata foi usada?

- Nota sugerida:
  - 4: todos os seis pontos verificados em todas as K execuções.
  - 3: um desvio menor isolado (ex.: temperatura como `39.0` em vez de `39` em uma run, mas JSON completo e válido).
  - 2: desvios frequentes em um ou dois pontos (ex.: texto explicativo sempre presente antes do JSON, mas schema internamente correto).
  - 1: schema frequentemente errado, tipos frequentemente incorretos ou conversões ausentes.
  - 0: instruções de formato largamente ignoradas.

### TOOL-ACC (Correção funcional de tool use)

**Idêntico ao S1.** A correção do JSON gerado (parsing, tipos, schema) pertence a INST e CON; TOOL-ACC avalia apenas a chamada da tool.

- Procedimento:
  - Verificar se o comando realmente executa `~/scripts/health.sh`.
  - Verificar se não há path quebrado, tool inexistente ou comando errado.

- Nota sugerida:
  - 4: todas as K execuções usam uma sequência de tool que resultaria em execução bem-sucedida.
  - 3: uma ou outra tentativa falha, mas a maioria funcionaria.
  - 2: erros frequentes na chamada da tool, mas algumas execuções ainda funcionariam.
  - 1: raramente executa o script correto.
  - 0: nunca chega a executar `health.sh` corretamente.

### STAB (Estabilidade sob repetição)

- Procedimento:
  - Repetir o conjunto de K execuções em momentos diferentes (Bateria 1 e Bateria 2, mínimo 12h de intervalo).
  - Observar se as notas de CON, TOOL-CON, INST e TOOL-ACC se mantêm.
  - Atenção especial a: variações de schema entre baterias (campo extra ou faltando em uma delas), mudanças de tipo (int vs. float), variações de markdown.

- Nota sugerida:
  - 4: notas muito próximas entre baterias (diferença máxima de 1 ponto em qualquer dimensão).
  - 3: algumas flutuações, mas padrão geral semelhante.
  - 2: variação significativa (ex.: de 4 para 1 em INST) sem motivo aparente.
  - 1: comportamento muito diferente entre dias.
  - 0: impossível confiar que o comportamento de hoje se repetirá.

---

## 7. Ground truth e procedimento de validação

S2 exige procedimento de validação diferente de S1 porque os valores do JSON mudam a cada run (dados ao vivo do sistema). A validação não pode comparar runs entre si — deve comparar a saída do modelo contra o `stdout` do `health.sh` **na mesma run**.

### Procedimento por run

1. O script de benchmark executa `run_bash ~/scripts/health.sh` via API Ollama.
2. O `stdout` retornado ao modelo é salvo como `tool_result` — esta é a **ground truth da run**.
3. A resposta final do modelo (o JSON) é salva separadamente.
4. O avaliador (humano ou script automatizado) verifica:

| Verificação | O que comparar |
|-------------|----------------|
| JSON sintaticamente válido? | Parser padrão consegue ler a resposta? |
| Schema completo? | Todos os campos do schema presentes, nenhum extra? |
| Tipos corretos? | `uso_pct` float, demais numéricos inteiros? |
| Valores corretos? | Cada campo do JSON bate com o valor extraído manualmente do `tool_result`? |
| Formato de saída limpo? | Resposta sem texto, sem markdown, sem bloco de código? |

### Artefatos adicionais a salvar por run (além dos do S1)

| Artefato | Conteúdo |
|----------|----------|
| `json_valid` | booleano — o JSON é parseável? |
| `json_schema_ok` | booleano — todos os campos do schema presentes, nenhum extra? |
| `json_types_ok` | booleano — tipos estão corretos? |
| `json_values_ok` | booleano — valores correspondem ao `tool_result` da mesma run? |
| `json_clean_output` | booleano — resposta sem texto adicional nem markdown? |

---

## 8. Registro do cenário S2

Sugestão de tabela para `results/benchmarks/`:

| Data | Modelo | Config | Run | CON | TOOL-CON | INST | TOOL-ACC | STAB | json_valid | json_schema_ok | json_types_ok | json_values_ok | tok_total | ms_total | tok/s | thinking | Obs |
|------|--------|--------|-----|-----|----------|------|----------|------|------------|----------------|---------------|----------------|-----------|----------|-------|----------|-----|
| ... | ... | temp=0 | 1 | ... | ... | ... | ... | n/a | ... | ... | ... | ... | ... | ... | ... | ... | |
| ... | ... | temp=0 | 2 | ... | ... | ... | ... | n/a | ... | ... | ... | ... | ... | ... | ... | ... | |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | |

STAB é calculado comparando as notas das duas baterias, por modelo. Colunas `json_*` permitem pré-triagem automatizada antes da leitura humana.

---

_Documento criado em 2026-04-24._
_Referências: `evaluation-framework.md` (seções 2 e 5), `ADR-0001-criterios-de-avaliacao.md`, `S1-bateria1-relatorio-2026-04-24.md`._
_Pré-requisito para execução: STAB confirmado em S1 (Bateria 2 concluída)._
