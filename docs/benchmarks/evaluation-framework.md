# Evaluation Framework para LLMs on-prem e agentes

## 1. Objetivo

Este documento define **como aplicar na prática** os critérios de avaliação estabelecidos no ADR-0001 aos modelos e agentes usados no laboratório `llms-on-prem`.

Foco:
- LLMs rodando on-prem (principalmente via Ollama).
- Agentes que executam tools (scripts, comandos, operações em arquivos).
- Métricas centrais: CON, TOOL-CON, INST, TOOL-ACC, STAB (conforme ADR-0001).

Este framework não é uma bateria fixa de testes, e sim um **método** para construir cenários de benchmark com complexidade crescente de forma disciplinada.

## 2. Escada de complexidade de cenários

Os cenários de teste serão organizados em níveis de complexidade, seguindo o princípio:

> Sempre começar pelo mais simples e verificável, e só então aumentar a complexidade.

### Nível 1 – Script simples, saída literal

- Tarefas:
  - Executar um script local.
  - Capturar a saída completa.
  - Encaminhar a saída literal para um destino (ex.: chat, log, arquivo).
- Propriedades:
  - Saída determinística.
  - Ground truth trivial (stdout do script).
  - Poucas decisões: tool correta + respeito à instrução de “não alterar”.
- Principalmente útil para medir:
  - TOOL-ACC (script certo, comando certo, sem inventar tools).
  - TOOL-CON (escolha de tool consistente entre execuções).
  - INST (seguir instrução de repassar saída sem modificar).
  - CON/STAB em pipeline simples.

### Nível 2 – Script + parsing leve

- Tarefas:
  - Executar script.
  - Capturar saída.
  - Extrair campos específicos (ex.: uso de CPU, temperatura, VRAM).
  - Gerar resumo estruturado (ex.: JSON ou tabela).
- Propriedades:
  - Mesma fonte determinística (`stdout`).
  - Mais espaço para erro de parsing e formatação.
- Útil para:
  - TOOL-ACC em conjunto com parsing.
  - INST (seguir esquema de saída).
  - CON/STAB sob parsing repetido.

### Nível 3 – Workflow de arquivos com análise

- Tarefas:
  - Ler diretório.
  - Abrir arquivos.
  - Entender conteúdo (ex.: reconhecer artigo científico, revista, data).
  - Classificar.
  - Renomear/mover conforme padrão (ex.: `Bioscience-09-05-2026-Titulo_do_artigo.pdf`).
- Propriedades:
  - Multi-step.
  - Mais tools envolvidas (FS + parsing + geração de strings).
  - Alto potencial de divergência entre execuções.
- Útil para:
  - CON/STAB em workflows complexos.
  - TOOL-ACC em cadeia de tools.
  - INST (seguir rigorosamente convenções de nome).

### Nível 4+ – Workflows com decisões e efeitos persistentes

- Tarefas:
  - Incluem decisões mais soltas (ex.: políticas, rotinas de manutenção, planos de ação).
  - A serem considerados apenas depois de resultados satisfatórios nos níveis 1–3.

Na fase atual do projeto, o foco é **Nível 1**, com plano de evoluir para Nível 2 e 3 somente após bons resultados em tarefas simples.

## 3. Critérios e métricas (resumo operacional)

A partir do ADR-0001:

- **CON** – Consistência de resposta:
  - Se a estrutura e o conteúdo essencial da resposta se mantêm entre execuções com a mesma entrada.
- **TOOL-CON** – Consistência de tool use:
  - Se o agente escolhe as mesmas tools e strategy de chamada entre execuções.
- **INST** – Aderência a instruções:
  - Se o agente respeita formato, estilo, idioma e restrições do prompt.
- **TOOL-ACC** – Correção funcional de tool use:
  - Se usa tools existentes, com argumentos válidos, que resultam em execução bem-sucedida.
- **STAB** – Estabilidade sob repetição:
  - Se as métricas acima se mantêm estáveis ao longo de múltiplas runs e sessões.

Escala inicial para cada dimensão: 0 (inaceitável) a 4 (excelente), com foco em comparação relativa entre modelos/configurações.

## 4. Cenário S1 – Health check estático (Nível 1)

### 4.1. Descrição

- Nome: **S1 – Health check estático**
- Script: `~/scripts/health.sh`
- Comportamento conhecido (exemplo):

  ```text
  === SAÚDE DO SISTEMA ===
  24/04/2026 12:36:02

  CPU
    Uso:         3.2%
    Temperatura: 35.0°C

  MEMÓRIA
    Total:      31957 MB
    Usada:      10014 MB
    Livre:      1067 MB
    Disponível: 21942 MB

  GPU: NVIDIA GeForce RTX 3060
    Uso:        0 %
    Temp:       40°C
    VRAM usada: 7955 MiB / 12288 MiB
    VRAM livre: 3963 MiB

  TOP 3 PROCESSOS (CPU)
    message+     1.0%  clickhouse-server
    conrado      0.4%  claude
    root         0.2%  /app/venv_k3s/bin/python3

  TOP 3 PROCESSOS (MEMÓRIA)
    conrado      5.7%  openclaw-gateway
    root         4.4%  /usr/bin/ollama
    root         3.4%  /usr/local/bin/python3
  ```

- Objetivo do cenário:
  - O agente deve:
    1. Executar `~/scripts/health.sh`.
    2. Capturar a saída completa.
    3. Encaminhar a saída **literal**, sem qualquer alteração de conteúdo, formatação ou ordem de linhas, para um destino (por exemplo, um “chat de monitoramento” ou log definido no contexto do teste).

### 4.2. Instrução de teste (exemplo)

Prompt do usuário, adaptado ao ambiente:

> Execute o script `~/scripts/health.sh` e encaminhe a saída **exata**, sem alterar nada (sem resumo, sem comentários, sem tradução, sem reordenação), para o destino configurado como `MONITOR_HEALTH`.  
>  
> Se não conseguir executar o script, responda apenas com a mensagem:  
> `ERRO: não consegui executar health.sh`  
> e não tente inventar a saída.

(Em ambiente real, `MONITOR_HEALTH` será implementado via tool/integração; para benchmark manual, considerar a resposta do modelo como se fosse o “encaminhamento”.)

### 4.3. O que é considerado sucesso

- Tool certa:
  - O agente resolve executar `~/scripts/health.sh` (diretamente ou via ferramenta de execução de comando).
- Saída:
  - A saída encaminhada é **idêntica** ao `stdout` do script, salvo:
    - variação esperada de timestamp (se houver);
    - diferenças triviais de whitespace que não mudem semântica (idealmente nenhuma).
- Sem enfeite:
  - Nenhum comentário, explicação, resumo ou tradução é adicionado.
  - Nenhuma linha é removida.
- Em caso de falha real na execução:
  - A resposta é exatamente a mensagem de erro especificada.

### 4.4. Aplicando as métricas ao cenário S1

#### CON (Consistência de resposta)

- Procedimento:
  - Executar o cenário S1 K vezes (por exemplo, K = 5) com a mesma configuração de modelo/agente.
  - Comparar as saídas:
    - Se todas são literal copy da saída do script (ou da string de erro esperada) → CON tende a 4.
    - Qualquer variação de conteúdo extra (explicações, resumos, comentários) reduz a nota.
- Nota sugerida:
  - 4: todas as K execuções produziram exatamente a mesma saída literal.
  - 3: pequenas variações não essenciais (ex.: whitespace não crítico), sem comentários extras.
  - 2: algumas execuções trazem comentários/resumos, mas a saída principal está presente.
  - 1: boa parte das execuções altera conteúdo de forma relevante.
  - 0: a maioria das execuções não retorna a saída esperada.

#### TOOL-CON (Consistência de tool use)

- Procedimento:
  - Observar como o agente decide executar `health.sh` em cada run.
  - Verificar:
    - se sempre usa a mesma tool/estratégia (ex.: sempre “run_shell_command” com o mesmo comando);
    - se não inventa outras tools desnecessárias.
- Nota sugerida:
  - 4: mesma tool + mesmo comando em todas as K execuções.
  - 3: pequenas variações benignas (ex.: uso de `bash ~/scripts/health.sh` vs `~/scripts/health.sh`), sem impacto.
  - 2: às vezes tenta outra abordagem, mas ainda executa o script correto.
  - 1: chama tools diferentes, com risco de comportamento imprevisível.
  - 0: raramente/ou nunca chama a tool correta.

#### INST (Aderência a instruções)

- Procedimento:
  - Verificar, para cada execução:
    - se não há comentários extras;
    - se não há resumo ou alteração da saída;
    - se a frase de erro (se usada) é exatamente a especificada.
- Nota sugerida:
  - 4: segue a instrução de forma exata em todas as K execuções.
  - 3: um ou outro desvio menor, sem comprometer a ideia principal.
  - 2: desvios frequentes, mas ainda reconhecíveis como tentativa de seguir instrução.
  - 1: instruções são frequentemente ignoradas.
  - 0: quase nunca segue instruções.

#### TOOL-ACC (Correção funcional de tool use)

- Procedimento:
  - Verificar:
    - se o comando realmente executa `~/scripts/health.sh`;
    - se não há path quebrado, tool inexistente ou comando errado.
- Nota sugerida:
  - 4: todas as K execuções usam uma sequência de tool que resultaria em execução bem-sucedida.
  - 3: uma ou outra tentativa falha, mas a maioria funcionaria.
  - 2: erros frequentes na chamada da tool, mas algumas execuções ainda funcionariam.
  - 1: raramente executa o script correto.
  - 0: nunca chega a executar `health.sh` corretamente.

#### STAB (Estabilidade sob repetição)

- Procedimento:
  - Repetir o conjunto de K execuções em momentos diferentes (ex.: hoje, amanhã, próxima semana).
  - Observar se as notas de CON, TOOL-CON, INST e TOOL-ACC se mantêm.
- Nota sugerida:
  - 4: notas muito próximas entre baterias (diferença máxima de 1 ponto em qualquer dimensão).
  - 3: algumas flutuações, mas padrão geral semelhante.
  - 2: variação significativa (ex.: de 4 para 1 em uma dimensão), sem motivo aparente.
  - 1: comportamento muito diferente entre dias.
  - 0: impossível confiar que o comportamento de hoje se repetirá.

### 4.5. Registro do cenário S1

Sugestão de tabela (markdown ou planilha) para `results/benchmarks/`:

| Data       | Modelo         | Configuração         | Run | CON | TOOL-CON | INST | TOOL-ACC | STAB-nota-local | Observações curtas |
|-----------|----------------|----------------------|-----|-----|----------|------|----------|------------------|--------------------|
| 2026-04-24 | qwen-3.5-9b    | temp=0, no_stream    | 1   | 4   | 4        | 4    | 4        | n/a              |                    |
| 2026-04-24 | qwen-3.5-9b    | temp=0, no_stream    | 2   | 4   | 4        | 4    | 4        | n/a              |                    |
| ...       | ...            | ...                  | ... | ... | ...      | ...  | ...      | ...              |                    |

Depois, STAB é calculado comparando agrupamentos de runs por data/época.

## 5. Próximos cenários (Nível 2 e 3)

Este framework prevê expansão incremental:

- Nível 2 (a definir):
  - Baseado no mesmo `health.sh`, mas exigindo parsing e geração de JSON/relatório.
- Nível 3 (a definir):
  - Pipeline de renomeação de PDFs científicos:
    - ler diretório;
    - analisar conteúdo;
    - classificar (ex.: revista, tipo de documento);
    - extrair data e título;
    - renomear `p0746.pdf` → `Bioscience-09-05-2026-Titulo_do_artigo.pdf`, seguindo convenções estritas.

Esses cenários serão formalizados apenas depois de resultados robustos em S1.

## 6. Regras de uso deste framework

- Nenhum teste ou benchmark deve ser considerado “válido” se:
  - não estiver associado a um cenário nomeado (ex.: S1, S2…);
  - não tiver aplicação explícita das dimensões CON, TOOL-CON, INST, TOOL-ACC, STAB.
- Qualquer nova métrica ou dimensão deve ser:
  - descrita num ADR específico;
  - integrada neste documento em seção apropriada.

## 7. Revisão do framework

Este documento deve ser revisado quando:

- existir pelo menos:
  - 1 cenário de Nível 2 formalizado;
  - 1 cenário de Nível 3 formalizado;
  - 2 modelos/configurações diferentes avaliados em S1;
- surgirem necessidades práticas de:
  - automatizar coleta de métricas;
  - integrar ferramentas de tracing/monitoring para agentes;
  - refinar a escala de 0–4 em métricas numéricas mais detalhadas.

Até lá, este framework é a referência operacional para qualquer benchmark no laboratório `llms-on-prem`.
