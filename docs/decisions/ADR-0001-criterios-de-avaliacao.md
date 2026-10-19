# ADR-0001 Critérios de avaliação para LLMs on-prem e agentes

## Status

Aceita

## Contexto

O laboratório `llms-on-prem` existe para estudar e melhorar o comportamento de LLMs locais usados como agentes com tool use em um servidor com RTX 3060 12 GB, 32 GB RAM, i5-10400F, NVMe 512 GB e Ubuntu 24.

Os problemas centrais observados até agora são:
- alta variação entre respostas para entradas equivalentes;
- alucinação de conteúdo;
- tool use inconsistente ou imprevisível (tool errada, argumentos incorretos, tools inventadas).

Ao mesmo tempo, ainda não existem:
- benchmarks formais;
- critérios de avaliação escritos;
- hipóteses registradas;
- ADRs sobre modelos, arquitetura ou roteamento.

Sem critérios claros de avaliação, qualquer teste de modelo, prompt ou arquitetura será julgado de forma subjetiva, violando os antiobjetivos definidos para o projeto:
- não decidir por feeling;
- não colecionar testes soltos sem controle;
- não trocar múltiplas variáveis ao mesmo tempo.

A literatura recente de avaliação de LLMs recomenda explicitamente:
- múltiplos critérios em vez de uma métrica única (ex.: acurácia, relevância, consistência, segurança); [web:70][web:74][web:80]
- tratar **consistência** como critério separado da "qualidade média" da resposta; [web:69][web:71][web:77]
- para agentes, avaliar tool use com métricas específicas (tool selection accuracy, argument validity, step-level faithfulness). [web:72][web:75][web:78]

## Decisão

Definir um conjunto pequeno e explícito de critérios de avaliação para esta fase do laboratório, com foco em **agentes locais com tool use**.

### Dimensões principais

1. **Consistência de resposta (CON)**  
   - O quanto respostas para a mesma entrada (ou entradas equivalentes) se mantêm estáveis em estrutura, conteúdo essencial e decisão de tool. [web:71][web:74][web:77]  
   - Critério: mesma intenção → mesma estratégia e mesma tool (quando aplicável), com variação aceitável apenas em detalhes de redação.

2. **Consistência de tool use (TOOL-CON)**  
   - O quanto o agente escolhe as mesmas tools, com argumentos compatíveis, em execuções repetidas sob mesmas condições. [web:72][web:75]  
   - Critério: para um conjunto de N execuções por cenário, a porcentagem de execuções em que:
     - a mesma tool principal é chamada;
     - não há tools inventadas;
     - os argumentos passam em validações simples (schema/regex).

3. **Aderência a instruções (INST)**  
   - O quanto as respostas seguem o formato, o estilo e as regras do prompt (por exemplo: separar fatos de hipóteses, usar seções específicas, responder em português). [web:70][web:71]  
   - Critério: verificar se cada resposta:
     - inclui todas as seções exigidas;
     - respeita idioma e tom pedido;
     - não ignora restrições explícitas (ex.: não implementar código nesta fase).

4. **Correção funcional de tool use (TOOL-ACC)**  
   - O quanto as chamadas de tool são **funcionalmente corretas**: tool certa para o problema certo, argumentos válidos, sem alucinação de nomes ou campos. [web:72][web:75][web:78]  
   - Critério:
     - taxa de chamadas de tool que:
       - usam uma tool existente;
       - utilizam argumentos que batem com o schema esperado;
       - levam a uma execução bem-sucedida (do ponto de vista do sistema).

5. **Estabilidade sob repetição (STAB)**  
   - O quanto as métricas acima se mantêm ao repetir os mesmos cenários em diferentes dias/sessões, para o mesmo modelo/configuração. [web:62][web:77]  
   - Critério: repetir um conjunto fixo de prompts de teste ao longo do tempo e observar variação nas métricas CON, TOOL-CON, INST e TOOL-ACC.

### Escala de avaliação

- Cada dimensão será avaliada inicialmente em escala ordinal simples:
  - 0 = inaceitável
  - 1 = ruim
  - 2 = aceitável
  - 3 = bom
  - 4 = excelente

- Na fase 1, priorizar **comparação relativa** (modelo A vs. modelo B no mesmo cenário) em vez de tentar definir "limiares absolutos perfeitos". [web:70][web:74][web:80]

### Unidade de avaliação

- A unidade base de avaliação será o **cenário de teste**:
  - um conjunto pequeno de prompts representativos de uso real;
  - com expectativa clara de:
    - se tool deve ser chamada;
    - qual tool seria ideal;
    - qual estrutura/formato de resposta é desejável.

- Para cada cenário e modelo/configuração:
  - executar K repetições (ex.: K = 5 ou 10, definido no documento de framework de avaliação);
  - registrar outputs e chamadas de tool;
  - calcular métricas CON, TOOL-CON, INST, TOOL-ACC e STAB.

### Objetivo da fase 1 com esses critérios

- Não é ainda "certificar" modelos, e sim:
  - conseguir comparar opções;
  - identificar padrões de falha;
  - priorizar hipóteses sobre origem da inconsistência (modelo vs. prompt vs. tool design vs. orquestração).

## Consequências

### Positivas

- Cria um vocabulário comum para discutir resultados de testes (CON, TOOL-CON, INST, TOOL-ACC, STAB) em vez de "pareceu melhor/pior". [web:70][web:71]  
- Garante que qualquer experimento futuro possa ser relatado com base em critérios explícitos. [web:65][web:74]  
- Previne que decisões de modelo/arquitetura sejam tomadas apenas por impressão subjetiva. [file:6]  
- Alinha o laboratório com práticas modernas de avaliação de LLMs e agentes (múltiplas métricas, consistência e reliability como dimensões principais). [web:71][web:72][web:75][web:78]

### Negativas

- Adiciona custo inicial de definição de cenários e coleta de dados mesmo para testes rápidos. [web:65]  
- Pode tornar a fase de experimentação mais lenta no curto prazo, já que testes "ad-hoc" passam a ser menos aceitáveis sem mapeamento mínimo de cenário.  
- Requer disciplina para não inflar o número de métricas nem cair em excesso de complexidade.

### Trade-offs

- Troca:
  - velocidade de iteração no início,
  - por estrutura para comparar resultados no médio prazo.
- Aceita uma escala simples (0–4) em vez de métricas numéricas sofisticadas, para manter o processo viável sem ferramentas externas de avaliação nesta fase. [web:70][web:74][web:80]

## Alternativas consideradas

1. **Avaliar apenas "qualidade textual" da resposta**  
   - Rejeitada porque não captura:
     - consistência de tool use;
     - aderência a instruções;
     - estabilidade ao longo do tempo. [web:70][web:72][web:74]

2. **Usar diretamente uma ferramenta externa de avaliação completa (ex.: plataforma de LLM eval SaaS)**  
   - Rejeitada nesta fase por:
     - foco em ambiente on-prem e baixo custo;
     - necessidade de primeiro entender os critérios que importam para este laboratório, antes de investir em tooling pesado. [web:72][web:75][web:80]

3. **Definir dezenas de métricas detalhadas desde o início**  
   - Rejeitada para a fase 1:
     - aumenta a complexidade;
     - dificulta aplicação manual;
     - pode atrasar a fase de experimentação sem ganho proporcional.

## Critério de revisão futura

Este ADR deve ser revisado quando:

- houver pelo menos:
  - 1 documento de framework de avaliação em `docs/benchmarks/evaluation-framework.md`;
  - 1 benchmark completo rodado com 2+ modelos / configurações diferentes;
- surgirem necessidades práticas de:
  - adicionar novas dimensões (ex.: latência, consumo de VRAM, custo energético, segurança);
  - ajustar a escala (por exemplo, trocando a escala ordinal 0–4 por métricas quantitativas derivadas de scripts);
  - introduzir ferramentas automatizadas de avaliação (bulk comparison, LLM-as-a-judge, dashboards de monitoramento). [web:62][web:72][web:77][web:78]

Enquanto isso, este ADR é a referência principal para:
- desenho de cenários de teste;
- registro de resultados;
- comparação entre modelos e configurações no laboratório `llms-on-prem`.
