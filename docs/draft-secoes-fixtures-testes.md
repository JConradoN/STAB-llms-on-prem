### 3.4 Design das Fixtures

Para garantir a reprodutibilidade e o isolamento de variáveis, o framework STAB utiliza um conjunto de *fixtures* sintéticas em vez de logs de produção reais. Esta decisão metodológica visa eliminar o ruído de dados sensíveis e permitir o controle preciso sobre os fenômenos agênticos avaliados, como a detecção de limiares de severidade e a aplicação de regras de precedência.

**Estrutura e Conceito de Fixture**
Cada unidade de teste, ou *fixture*, é composta por um par de arquivos: um arquivo de entrada bruta (`.log`) e um arquivo de "verdade fundamental" (*ground truth*) em formato estruturado (`.expected.json`). Durante a execução, o modelo não recebe o conteúdo do log diretamente no prompt; ele deve utilizar a ferramenta `read_file` para acessar o arquivo `.log`. O validador automático então compara a resposta final do modelo com os campos definidos no `.expected.json`.

**Campos e Vocabulário Controlado**
O *ground truth* é composto por campos operacionais críticos: `case_id`, `severity_expected` (info, warning ou critical), `primary_issue`, `secondary_issues`, `host`, `timestamp`, `requires_action` (booleano) e `expected_summary`. Para evitar a ambiguidade semântica comum em avaliações de linguagem natural, o framework utiliza um **vocabulário controlado** para a identificação de problemas (ex: `high_cpu_usage`, `database_unavailable`, `postgresql_service_failed`). Esta restrição transforma a avaliação de uma tarefa de escrita livre em uma tarefa de classificação e extração rigorosa, permitindo medições precisas de acurácia automática.

**Cenários de Análise de Log (S3)**
As fixtures de nível S3 foram desenhadas para testar quatro perfis distintos de comportamento:
*   **info-001:** Log de operação normal. Testa se o modelo é capaz de manter a neutralidade e não alucinar problemas onde não existem.
*   **warning-001:** Log com degradação moderada. Avalia a sensibilidade do modelo a limiares de alerta.
*   **critical-001:** Falha grave e imediata. Verifica a detecção de severidade máxima.
*   **mixed-001:** Este é o cenário mais discriminativo do benchmark. Ele apresenta múltiplos eventos de diferentes severidades no mesmo arquivo. O sucesso depende da aplicação da **regra de precedência binária**: a presença de qualquer evento `CRITICAL` deve elevar a severidade global para `critical`, independentemente do volume de mensagens informativas ou de alerta.

**Cenários de Triagem Multi-log (S4)**
As fixtures de nível S4 consistem em conjuntos de múltiplos logs que devem ser lidos sequencialmente para triagem e escalonamento:
*   **S4-A:** Composto por três logs com severidades distintas (info-001, warning-001, critical-001). Testa a capacidade básica de ordenação seguindo a hierarquia crítica > warning > info.
*   **S4-B:** Composto por três logs de severidade crítica (critical-001, critical-003, mixed-001). Introduz ambiguidade ao exigir um desempate baseado na gravidade do `primary_issue`, priorizando cascatas de infraestrutura (ex: disco cheio afetando banco de dados) sobre falhas isoladas de serviço ou de aplicação.
*   **S4-C:** Introduz uma regra de desempate por recência: se dois hosts apresentam a mesma severidade (ex: ambos `info`), o modelo deve priorizar o host com o *timestamp* mais recente, exigindo capacidades avançadas de raciocínio temporal.

**Experimento Controlado H12**
Para investigar o fenômeno de *tool-skipping*, foram criadas três fixtures **H12** (`log-alpha.log`, `log-beta.log`, `log-gamma.log`), que espelham os conteúdos de S4, mas com nomes de arquivos opacos em vez de nomes reveladores (como `critical-001.log`). Esta variável isolada permite confirmar se o modelo decide pular a leitura técnica baseando-se apenas em pistas semânticas presentes no contexto (o nome do arquivo), o que caracteriza uma falha grave de integridade agêntica.

---

### 3.5 Anatomia dos Testes

A execução dos testes segue um protocolo rigoroso de interação via API, projetado para simular o ciclo de vida de um agente autônomo em ambiente de produção local.

**Fluxo de Execução (The Agent Loop)**
Cada teste é processado através de uma interação multi-turno com o runtime Ollama (via `/api/chat`). O fluxo consiste em:
1.  **Turno 1 (Chamada):** O script envia o prompt do cenário com a definição das ferramentas disponíveis (JSON Schema). O modelo deve responder com uma `tool_call` estruturada (ex: chamando `read_file` com o path do log).
2.  **Execução:** O script intercepta a chamada, executa a operação no sistema host via subprocesso e captura o `stdout`.
3.  **Turno 2 (Resposta):** O resultado da ferramenta é devolvido ao modelo. O modelo processa os dados técnicos e produz a resposta final em formato JSON.

**Parâmetros de Estabilidade e Cobertura (K)**
Para garantir o determinismo e a comparabilidade, todos os modelos são configurados com **temperatura zero** e `stream=false`, com pausas de 30 segundos entre runs para limpeza de cache de VRAM. A quantidade de execuções ($K$) segue uma distinção metodológica:
*   **S1 e S2 (K=5):** São realizados 5 runs idênticos do mesmo input para medir a variabilidade intra-modelo e a estabilidade das notas CON e STAB.
*   **S3 (K=4):** Execução de 4 casos distintos (um para cada tipo de fixture: info, warning, critical, mixed) para medir a cobertura de regras de classificação.
*   **S4 (K=3):** Execução de 3 sub-cenários distintos (S4-A, S4-B, S4-C) com composições de logs e regras de triagem variadas.

**Coleta de Métricas e Performance**
Além da corretude da resposta, o framework captura métricas granulares de performance: *tokens* de entrada e saída, duração total em milissegundos e velocidade de geração (*tokens/s*). Capturamos também o campo de **raciocínio interno (*thinking*) do segundo turno (T2)**, permitindo correlacionar o esforço cognitivo do modelo com a complexidade da tarefa de síntese final.

**Lógica do Validador Automático**
O validador atua em dimensões específicas para cada nível da escada de complexidade:
*   **S1 (Protocolo):** Verifica se a ferramenta correta foi chamada (`tool_valid`) e se o comando foi bem-sucedido no host (`tool_success`).
*   **S2 (Formato):** Valida a estrutura do JSON, a presença de todos os campos obrigatórios e a precisão do *timestamp* extraído.
*   **S3 (Semântica):** Compara a severidade (`class_acc`) e a aderência ao vocabulário controlado (`primary_issue_match`).
*   **S4 (Planejamento):** Mede o encadeamento (`chain_acc`), verificando se todos os logs foram lidos (ex: 3/3 chamadas) e se a ordenação de prioridade segue a lógica esperada.

**A Dimensão Crítica de Grounding**
Um diferencial do framework STAB é o tratamento da dimensão de **Grounding** como um requisito obrigatório para a nota máxima. Identificamos que modelos podem produzir saídas JSON estruturalmente perfeitas baseadas em alucinação (H14), sem nunca terem executado a ferramenta de leitura. O validador penaliza qualquer resposta que apresente acurácia de dados sem a correspondente `tool_call` registrada nos logs de execução, distinguindo entre conformidade de formato e integridade factual.

**Diferenciação de Falhas**
A anatomia do teste permite distinguir entre:
*   **Falhas de Protocolo (H13):** O modelo falha em usar a interface de `tool_calls` da API, tentando serializar o JSON diretamente no conteúdo da mensagem.
*   **Falhas de Decisão (H12):** O modelo usa a interface corretamente, mas decide pular passos de execução por excesso de confiança ou viés contextual.
