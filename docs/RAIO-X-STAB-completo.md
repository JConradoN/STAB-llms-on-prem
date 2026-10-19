# Raio-X completo do STAB — da concepção ao camera-ready

**Documento de referência denso, escrito pra reconstruir o entendimento do projeto do zero.**
Não é resumo executivo — é o "porquê" por trás de cada decisão, cada cenário, cada achado, na
ordem em que aconteceram, incluindo os becos sem saída e as correções de rumo no caminho.

---

## Sumário

1. [O que é este documento e por que ele existe](#1-o-que-é-este-documento-e-por-que-ele-existe)
2. [Concepção: de onde veio o STAB](#2-concepção-de-onde-veio-o-stab)
3. [O laboratório maior por trás do paper: ABS + llms-on-prem](#3-o-laboratório-maior-por-trás-do-paper-abs--llms-on-prem)
4. [O framework STAB em detalhe](#4-o-framework-stab-em-detalhe)
5. [Ambiente experimental](#5-ambiente-experimental)
6. [Os 8 modelos avaliados, um a um](#6-os-8-modelos-avaliados-um-a-um)
7. [Taxonomia de falhas: as 5 camadas e os códigos H/AP](#7-taxonomia-de-falhas-as-5-camadas-e-os-códigos-hap)
8. [Os achados principais, com a história completa de cada um](#8-os-achados-principais-com-a-história-completa-de-cada-um)
9. [Discussão: o que os achados significam juntos](#9-discussão-o-que-os-achados-significam-juntos)
10. [Limitações reconhecidas e trabalho futuro](#10-limitações-reconhecidas-e-trabalho-futuro)
11. [O programa de pesquisa mais amplo: a tese das propriedades arquiteturais](#11-o-programa-de-pesquisa-mais-amplo-a-tese-das-propriedades-arquiteturais)
12. [A jornada até o camera-ready](#12-a-jornada-até-o-camera-ready)
13. [Linha do tempo consolidada](#13-linha-do-tempo-consolidada)
14. [Glossário rápido de referência](#14-glossário-rápido-de-referência)
15. [Onde isso te deixa agora](#15-onde-isso-te-deixa-agora)

---

## 1. O que é este documento e por que ele existe

Você pediu este raio-X porque, nas suas palavras, "talvez eu nunca tenha conhecido bem" o STAB por
dentro, ou não lembra mais das decisões e do porquê de cada uma — TDAH grave, informação some da
cabeça de verdade, não é falta de atenção comum. Este documento não pressupõe que você lembre de
nada. Ele reconstrói tudo: o problema que motivou o projeto, cada escolha metodológica com a razão
por trás, os 8 modelos testados e o que aconteceu com cada um, os achados e como eles foram
descobertos (incluindo hipóteses que mudaram de forma no meio do caminho), e a jornada até o
artigo ser aceito e o camera-ready ser enviado hoje.

Fonte primária: o artigo final (`paper/kdmile2026/main-ptbr.tex`, já submetido), cruzado com os
ADRs e as notas de achado (`docs/decisions/`, `docs/notes/`) que documentam o raciocínio por trás
de cada número que está no artigo.

---

## 2. Concepção: de onde veio o STAB

### O problema real

A pergunta que deu origem a tudo: **fazer um LLM local invocar ferramentas de forma confiável —
não apenas responder perguntas — é mais difícil do que parece.** Modelos que se saem bem em
benchmarks padrão de linguagem falham sistematicamente quando colocados em contexto agêntico
(precisam agir, não só responder): pulam a invocação de ferramenta e inventam um resultado
plausível, alucinam dados, ou devolvem um JSON tecnicamente correto encapsulado dentro de um bloco
de markdown que o script chamador não consegue processar.

### Por que os benchmarks existentes não capturam isso

Dois benchmarks de referência na área — **BFCL** (Berkeley Function Calling Leaderboard) e
**AgentBench** — não expõem esses problemas porque operam sob condições que não existem em
implantação local real: compute praticamente ilimitado, e a possibilidade de repetir a tentativa
quando algo dá errado. Um terceiro, **SLM-Bench**, já introduz controle de hardware e métricas de
impacto ambiental — mais próximo da metodologia do STAB, mas ainda sem o eixo que faltava.

O gap identificado: nenhum desses benchmarks testa sob as condições reais de quem roda IA local em
casa ou numa empresa pequena — **temperatura zero, execução em tentativa única (one-shot), hardware
de consumidor**. É exatamente esse gap que o STAB foi desenhado para preencher.

### O nome e o que ele significa

"STAB" não é explicado como sigla no texto final do artigo (decisão editorial — o nome virou marca
própria do framework), mas nos rascunhos originais do projeto ele nasceu como sigla de **Stability,
Tooling, Adherence, and Behavior**. A versão final do paper usa STAB como nome do framework em si
e também como nome de uma métrica específica dentro dele (a métrica de estabilidade temporal —
ver Seção 4).

### Trabalhos relacionados — contra o que o STAB se posiciona, especificamente

A Seção 2 do artigo não é um parágrafo de obrigação acadêmica solto — cada citação foi escolhida
porque delimita uma fronteira específica que o STAB cruza. Vale conhecer cada uma:

**Benchmarks de agentes e uso de ferramentas.**
- **BFCL** (Berkeley Function Calling Leaderboard, Patil et al. 2025) — o benchmark de referência
  pra avaliação de ferramentas, mas com foco predominante em modelos de nuvem e LLMs de grande
  porte. É o "padrão ouro" que o STAB explicitamente não tenta substituir, só complementar num
  regime de hardware que o BFCL não cobre.
- **AgentBench** (Liu et al. 2024) — avaliação em múltiplos ambientes, oito domínios distintos.
  Já identifica o seguimento de instruções como o principal obstáculo à autonomia — achado que o
  STAB confirma de forma mais granular (a distinção entre falha comportamental e arquitetural).
- **SLM-Bench** (Pham et al. 2025) — o mais próximo metodologicamente: já introduz métricas de
  impacto ambiental e configuração de hardware controlada. É o único dos três que já se aproxima da
  filosofia de "medir sob restrição real", mas ainda sem o eixo de estabilidade temporal nem a
  sondagem explícita de viés contextual que o STAB adiciona.

**Modos de falha e seguimento de instruções.**
- Cemri et al. (2025) propõem uma taxonomia de **14 modos de falha em sistemas multiagente**,
  destacando desobediência a especificações como padrão recorrente — a taxonomia de 5 camadas do
  STAB é uma versão mais compacta e focada em agente único (não multiagente), mas herda o mesmo
  espírito de nomear causas raiz em vez de só contar erros.
- Kavathekar et al. (2025) mapeiam desempenho de SLMs (small language models) pra function calling
  em dispositivos de borda — hardware restrito, tema próximo, mas sem o framework de progressão em
  níveis de complexidade.
- Jhandi et al. (2026) demonstram que SLMs de até 350M parâmetros podem **superar** modelos maiores
  em uso de ferramentas com ajuste fino direcionado — evidência externa e independente que reforça
  a conclusão do próprio STAB de que tamanho de modelo é proxy fraco pra confiabilidade agêntica.
- Murthy et al. (2024), via o dataset KCIF, documentam queda de conformidade com instruções em
  modelos menores — achado que o STAB não contradiz (`qwen3.5:2b`, o menor dos 8 testados, é
  justamente um dos 3 descartados), mas qualifica: o tamanho por si só não é o fator decisivo (o
  `gemma4:e4b`, também relativamente pequeno, é a referência de maior confiabilidade do estudo
  inteiro).
- Zeng et al. (2024) exploram pipelines de treinamento pra cenários corporativos que exigem uso
  determinístico de ferramentas — o tipo de solução de produção que o achado H14 (grounding
  silencioso) do STAB argumenta ser insuficiente sozinha, sem um validador semântico externo.

**Padrões fundacionais de agentes com ferramentas.**
- **ReAct** (Yao et al. 2023) — o paradigma que intercala raciocínio e ação no mesmo loop de
  geração, base conceitual de praticamente todo agente de tool-calling atual, incluindo os testados
  no STAB.
- **Toolformer** (Schick et al. 2023) — demonstrou que LLMs podem aprender a decidir *quando*
  invocar uma ferramenta de forma auto-supervisionada. Nem ReAct nem Toolformer avaliam essa
  robustez sob restrição real de hardware ou execuções repetidas — exatamente o gap que o STAB
  preenche.
- **Geração restrita por gramática formal** (Geng et al. 2023) — uma linha ortogonal à engenharia
  de prompt, que restringe o espaço de tokens gerados a saídas estruturalmente válidas via
  gramática formal. O STAB não testa essa técnica, mas a discute explicitamente como mitigação
  candidata pro anti-padrão AP2 (wrapper de markdown) e pra casos resistentes a instrução direta
  como o `qwen3.5:2b` — ver Seção 9.

**A frase de diferenciação do próprio artigo, na íntegra:** *"O STAB tem um posicionamento
diferente: foca em hardware on-premise, introduz uma bateria de estabilidade temporal e sonda
explicitamente vieses contextuais como nomeação semântica — nenhum desses aspectos aparece nos
benchmarks acima."*

---

## 3. O laboratório maior por trás do paper: ABS + llms-on-prem

O STAB, como publicado no KDMiLe, é o recorte de publicação de um programa de pesquisa bem mais
amplo que já vinha rodando neste repositório (`llms-on-prem`) desde abril de 2026 — e que continua
rodando depois da submissão do artigo. Entender essa origem ajuda a explicar por que certas
decisões do artigo final (K pequeno, hardware único, fixtures sintéticas) são escolhas conscientes
de escopo, não limitações de improviso.

### O ADR-0001 original — de onde vêm as métricas

O primeiro documento de decisão do laboratório (`docs/decisions/ADR-0001-criterios-de-avaliacao.md`,
abril/2026) já definia o vocabulário que sobrevive até o artigo final: **CON** (consistência),
**TOOL-CON** (consistência de tool use), **INST** (aderência a instrução), **TOOL-ACC** (correção
funcional de tool use), **STAB** (estabilidade sob repetição). A motivação original era exatamente
a mesma que aparece no artigo, só em linguagem mais crua: "sem critérios claros de avaliação,
qualquer teste de modelo, prompt ou arquitetura será julgado de forma subjetiva" — e um dos
antiobjetivos explícitos do laboratório desde o início era **não trocar múltiplas variáveis ao
mesmo tempo**, princípio que molda todo o desenho experimental até hoje.

### ABS vs. LOP — duas frentes complementares, não a mesma coisa

O laboratório roda duas frentes de avaliação em paralelo, com escopos e condições de hardware
diferentes:

- **ABS** (o benchmark mais rápido/amplo, rodado sobre uma bateria grande de modelos — chegou a 17
  modelos numa das baterias): mede capacidade de raciocínio e tool calling em **contexto curto**
  (`num_ctx=4096` fixo — `ADR-0002-num-ctx-4096.md`). Essa escolha foi validada experimentalmente,
  não é convenção arbitrária: medição real mostrou que o cenário mais longo de toda a bateria ABS
  consome só 1.128 tokens (27,6% da janela de 4096), e um experimento controlado (`num_ctx=16384`
  vs `4096` no `gemma4:e4b`) mostrou variação de score de apenas +0,01 — dentro do ruído. Ou seja:
  aumentar o contexto não muda nada porque os cenários nunca chegam perto do limite. **ABS mede
  capacidade em interações curtas e focadas, por design.**
- **LOP (llms-on-prem, S1→S4)**: essa é a frente que evoluiu diretamente para o STAB. Usa o
  contexto default de cada modelo (não fixado em 4096), tentando se aproximar mais de condição de
  produção real (`ADR-0003-lop-ctx-vs-abs-ctx.md`). As duas frentes **não são diretamente
  comparáveis em termos de condição de hardware** — avaliam dimensões complementares do
  comportamento agêntico, cada uma de propósito.

### O experimento de contexto (H_context) — por que 4096 não é arbitrário

Vale entender esse experimento em detalhe porque ele exemplifica bem o rigor que o laboratório
exige antes de aceitar até uma decisão de configuração aparentemente pequena. A dúvida: será que
`num_ctx=4096` estaria penalizando modelos com arquitetura otimizada pra janelas longas (ex:
mecanismo GDN/atenção linear do `qwen3.5`)?

Antes de rodar qualquer coisa, mediu-se o consumo real de tokens por série de cenário no
`gemma4:e4b`:

| Série | Tokens máximos | Tokens médios | % da janela de 4096 (máx/médio) |
|---|---|---|---|
| T | 481 | 169 | 11,7% / 4,1% |
| C | 728 | 414 | 17,8% / 10,1% |
| L | 679 | 278 | 16,6% / 6,8% |
| Q | 1.128 | 446 | 27,5% / 10,9% |
| M | 767 | 485 | 18,7% / 11,8% |

**O cenário mais longo de toda a bateria consome 1.128 tokens — 27,6% da janela disponível.**
Rodando o experimento mesmo assim (`num_ctx=16384` vs `4096`, mesmo modelo, mesma bateria):

| Métrica | 4096 | 16384 | Δ |
|---|---|---|---|
| Score geral | 3,54 | 3,55 | +0,01 |
| tok/s | 57,5 | 59,7 | +2,2 |

Diferença de +0,01 no score — dentro do ruído. **Conclusão:** aumentar o contexto de 4× não muda
nada porque os cenários nunca chegam perto de usar o que já está disponível. Não era preciso
"acreditar" que 4096 bastava — foi medido.

Uma verificação complementar de VRAM (rodada contra vários modelos, contextos crescentes até
131.072) confirmou outro ponto: **nenhum modelo testado chegou a fazer spill de KV cache pra RAM
da CPU** em nenhum contexto testado — o Ollama simplesmente distribui automaticamente entre as duas
GPUs quando o cache não cabe numa só (ex: `qwen3:8b` passa de single-GPU pra dual-GPU a partir de
16K de contexto, sem perda de throughput). Achado prático, não hipotético: `granite4.1:30b` já
mostra o teto de VRAM mais apertado, com 86-87% de uso de GPU mesmo em 16-32K de contexto.

### A pergunta metodológica que atravessa todo o laboratório

Um documento posterior (`NOTE-0007-protocolo-falha-comportamental-vs-arquitetural.md`, formalizado
em julho/2026) descreve o protocolo de diagnóstico que o laboratório desenvolveu pra responder à
pergunta mais importante de todas quando um modelo falha: **a falha é comportamental (corrigível
por engenharia de prompt) ou arquitetural (codificada no treinamento, só corrigível trocando de
modelo)?** O protocolo: rodar o ABS, identificar um padrão de falha reconhecível, formular uma
hipótese de intervenção pontual (ex: um prefixo de sistema, uma instrução mais explícita), testar
essa intervenção isolada, e diagnosticar pelo resultado — se a intervenção não melhora (ou piora),
é arquitetural, descarta o modelo sem mais tentativas de prompt; se melhora, é comportamental,
mantém o modelo em consideração com o prompt ajustado. Essa é exatamente a lógica que aparece nos
experimentos H12 e H15 do STAB (ver Seção 8) — testar se uma intervenção corrige o comportamento é
o método central do laboratório inteiro, não uma técnica inventada especificamente pro artigo.

---

## 4. O framework STAB em detalhe

### A escada de complexidade S1→S4

O STAB organiza a avaliação em quatro níveis, cada um pressupondo o domínio das capacidades do
nível anterior:

| Nível | Nome | Ferramenta | Objetivo | K | Métrica |
|---|---|---|---|---|---|
| S1 | Protocolo | `run_bash` | Invocação + retorno de ferramenta | 5 | TOOL-ACC |
| S2 | Extração | `run_bash` | Saída JSON estruturada | 5 | JSON-ACC |
| S3 | Análise de Log | `read_file` | Classificação semântica | 4 | CLASS-ACC |
| S4 | Multi-log | `read_file` | Triagem e ranking multi-etapa | 3 | TRIAGE-ACC |

O framework usa **fixtures sintéticas** em vez de logs de produção reais, de propósito: cada
fixture é um arquivo `.log` de entrada mais um `.expected.json` de referência, com vocabulário
controlado (`high_cpu_usage`, `database_unavailable`) que transforma uma avaliação em princípio
aberta numa tarefa de classificação e extração rigorosa e comparável. O trade-off é explícito e
reconhecido: reprodutibilidade total e isolamento de variável, ao custo de não capturar o ruído
real de logs de produção (timestamp malformado, encoding inconsistente, entrada truncada).

**Protocolo de execução:** cada teste roda em dois turnos via API REST do Ollama (`/api/chat`). No
Turno 1, o modelo recebe o prompt e o JSON Schema das ferramentas disponíveis, e deve produzir uma
`tool_call` estruturada. O script executa a operação real no host e captura o `stdout`. No Turno 2,
esse resultado é devolvido ao modelo, que gera a resposta final. Determinismo garantido por
`temperature=0` e `stream=false`.

### Por que K muda de sentido entre os níveis (esclarecido na sessão de hoje)

Um ponto que confunde à primeira vista: K cai de 5 (S1/S2) para 4 (S3) e 3 (S4) — parece que
"testaram menos coisa difícil". Não é isso. **K não significa a mesma coisa em todo nível:**

- **S1 e S2 (K=5):** 5 repetições do *mesmo* input — mede se o modelo é consistente fazendo a
  mesma coisa 5 vezes seguidas (a métrica CON/TOOL-CON do ADR-0001 original).
- **S3 (K=4):** 4 casos *diferentes* — um pra cada tipo de fixture (info, warning, critical,
  mixed) — mede cobertura de tipo de situação, não repetição.
- **S4 (K=3):** 3 sub-cenários *diferentes* (S4-A, S4-B, S4-C, cada um com composição de logs e
  regra de triagem distinta) — de novo, cobertura, não repetição do mesmo teste.

Ou seja: nos níveis simples, K mede **estabilidade** (mesma tarefa, várias vezes). Nos níveis
complexos, K mede **cobertura** (tarefas diferentes, uma vez cada). Se alguém perguntar "por que K
caiu de 5 pra 3", essa é a resposta real — não é corte de rigor, é mudança de propósito.

### O dicionário completo de métricas

Cada sigla usada no artigo vem de algum lugar específico do protocolo — vale ter a lista completa
num único lugar em vez de precisar deduzir do contexto toda vez:

| Métrica | Descrição |
|---|---|
| **CON** | Consistência: estabilidade estrutural e decisória entre execuções |
| **TOOL-CON** | Consistência de ferramenta: invocações válidas repetidas |
| **INST** | Aderência a instrução: conformidade de formato e restrições |
| **TOOL-ACC** | Correção funcional: ferramenta correta, execução bem-sucedida |
| **JSON-ACC** | Acurácia JSON: validade do schema e precisão de valores |
| **CLASS-ACC** | Acurácia de classificação: severidade global correta |
| **PARSE-ACC** | Acurácia de extração: host, problema e timestamp precisos |
| **CHAIN-ACC** | Acurácia de encadeamento: número correto de chamadas de ferramenta (ex: 3 de 3 arquivos lidos) |
| **TRIAGE-ACC** | Acurácia de triagem: ranking de prioridade e regra de escalada corretos |
| **STAB** | Estabilidade temporal: manutenção dos escores acima entre as baterias de 12h |

Todas numa escala ordinal de **0 a 4**: 4 é execução perfeita (ferramenta certa, JSON válido,
conteúdo semanticamente preciso); 0 é falha completa. A distinção operacional mais importante:
**falha crítica** é um escore 0 numa métrica *bloqueante* do nível (TOOL-ACC em S1, JSON-ACC em
S2) — provoca descarte do modelo e interrompe a progressão pra níveis seguintes, porque cada nível
pressupõe o anterior como pré-condição. **Falhas não críticas** (escore 1 a 3) mantêm o modelo na
progressão e ficam registradas na taxonomia, mas não impedem tentar o próximo nível.

### O protocolo de estabilidade temporal (a métrica STAB propriamente dita)

Cada modelo aprovado (que sobreviveu até pelo menos completar os níveis iniciais) executa o
conjunto completo de cenários **duas vezes** — Bateria 1 e Bateria 2 — com **intervalo mínimo de
12 horas**, hardware, prompts, temperatura e ordem de cenários idênticos entre as duas execuções.
O intervalo existe pra isolar variância técnica temporal (GPU esfriando/aquecendo, cache do
sistema operacional, estado interno do Ollama entre reinicializações) da variância intrínseca real
do modelo. **O escore STAB de um cenário é a diferença absoluta entre Bateria 1 e Bateria 2** —
`STAB=4` significa escore idêntico nas duas execuções, degradando conforme a diferença aumenta.

### A taxonomia de falhas em 5 camadas

As falhas observadas em toda a bateria foram classificadas por causa raiz, não por sintoma:

- **Protocolo:** violação estrutural do formato de chamada de ferramenta (o modelo nem usa a
  estrutura de API correta).
- **Decisão:** erro de raciocínio contextual — ex: inferir um resultado sem executar a ferramenta
  necessária pra confirmá-lo.
- **Formato:** saída sintaticamente correta em conteúdo, mas não conforme às restrições de
  apresentação pedidas.
- **Grounding:** resposta estruturalmente válida, mas factualmente fabricada.
- **Instrução:** interpretação ambígua da ação pedida.

Cada falha específica dentro dessas camadas ganha um código único: prefixo **H** para achados
orientados por hipótese, testados e confirmados via experimento controlado; prefixo **AP**
("anti-pattern") pra padrões anômalos identificados durante execução padrão, sem um experimento
dedicado de confirmação por trás.

---

## 5. Ambiente experimental

| Componente | Especificação |
|---|---|
| CPU | Intel Core i5-10400F (6c/12t) |
| RAM | 32 GB DDR4 |
| GPU | NVIDIA RTX 3060 (12 GB VRAM) |
| SO | Ubuntu 24.04 |
| Runtime | Ollama (REST `/api/chat`), T=0, `stream=false` |

Hardware de consumidor, deliberadamente — não é servidor de laboratório de fabricante de GPU. A
escolha é o próprio ponto do estudo: representar o cenário mais comum de quem implanta IA local de
verdade, não um ambiente de referência artificialmente generoso.

### Decisões de implementação que moldam o protocolo (o "porquê" por trás de cada escolha técnica)

Estas são decisões tomadas na implementação original do primeiro cenário (S1), documentadas no
momento em que foram tomadas — cada uma tem uma razão específica, não é escolha arbitrária:

**API REST em vez de CLI com pipe.** A primeira versão do script usava
`docker exec ollama ollama run` — o modelo recebia o prompt como texto puro, sem schema de
ferramenta disponível de verdade. Isso tornava impossível avaliar TOOL-ACC e TOOL-CON com rigor:
não havia chamada de ferramenta real, só texto do modelo *dizendo* que ia fazer algo. A troca pra
`POST /api/chat` permite definir as ferramentas via JSON Schema de verdade, capturar `tool_calls`
estruturados na resposta, executar a ferramenta no host e devolver o resultado ao modelo, e
controlar a temperatura com precisão via parâmetro explícito — é o que torna o protocolo de dois
turnos (Seção 4) sequer possível.

**Temperatura zero — e a limitação conhecida disso.** Decisão pra maximizar determinismo, pra que
CON e STAB meçam variação real do comportamento do modelo, não variação introduzida por
amostragem estocástica. Consistência era a prioridade número 1 declarada desde o `ADR-0001`.
**Limitação reconhecida desde o início:** greedy decoding em T=0 pode fazer o modelo sempre
produzir a mesma resposta — desejável pra medir consistência, mas pode mascarar problemas de
variação que só aparecem em temperaturas mais altas, que são as usadas em produção real na maioria
dos casos. Registrado como item pra fase posterior, nunca chegou a ser sistematicamente testado
dentro do escopo do STAB em si.

**Nenhum framework de agente — sem LangChain, sem LiteLLM, sem Pydantic.** Frameworks de agente
adicionam comportamento não controlado (retries automáticos, reformatação silenciosa de tool
calls, logging interno que pode mascarar o que realmente aconteceu). Pra um benchmark de
consistência, cada variável extra não controlada é ruído que contamina a medição. Consequência
aceita: o script fica mais verboso de escrever, mas cada linha de comportamento é explícita e
auditável — dá pra saber exatamente o que aconteceu em cada run, sem intermediário.

**Tool única por nível, não um catálogo de ferramentas.** Múltiplas ferramentas disponíveis
tornariam TOOL-CON ambíguo — variação na *escolha* entre ferramentas igualmente válidas não é o
que os níveis iniciais pretendem medir. S1/S2 medem se o modelo decide executar a ação certa, não
se sabe escolher entre opções.

**Execução do comando via lista de argumentos, nunca via string com `shell=True`.** Detalhe de
segurança real: com `shell=True` e uma string, o comando passa por `/bin/sh -c`, que pode
interpretar metacaracteres (aspas, espaços, `&&`, `|`) de forma diferente do bash. Como o comando
executado **vem do modelo**, isso é superfície de risco real — se o modelo gerar um path com
caractere especial, o comportamento seria imprevisível. Usando lista de argumentos com `bash -c`
explícito, a interpretação de metacaractere fica sempre a cargo do bash de forma previsível. Aviso
documentado no próprio código: este é um ambiente de pesquisa controlado, não uma prática seguirse
em produção sem sandboxing adicional.

**Pausa de 30 segundos entre execuções independentes.** Precaução conservadora contra reuso de
cache de KV entre runs que deveriam ser estatisticamente independentes — o comportamento exato do
Ollama nesse ponto não estava documentado publicamente na época, então a pausa foi a escolha mais
segura disponível, mesmo sem certeza de que fosse estritamente necessária.

---

## 6. Os 8 modelos avaliados, um a um

| Modelo | Família | VRAM (MiB) | Tipo | Status final |
|---|---|---|---|---|
| `gemma4:e4b` | Gemma4 | 9.821 | Zero-shot | **Referência** (único S1→S4 perfeito) |
| `qwen3.5:9b` | Qwen3.5 | 7.953 | Zero-shot | Aprovado (S2B) |
| `qwen3:14b` | Qwen3 | 9.437 | Zero-shot | Aprovado (S1–S3) |
| `llama3.1:8b` | Llama3.1 | 4.868 | Zero-shot | Aprovado (Parcial) |
| `llama3-groq-tool-use:8b` | Llama3 | 4.754 | Fine-tuned | Aprovado (Parcial) |
| `mistral:7b` | Mistral | 4.458 | Zero-shot | **Descartado** (H14) |
| `phi4-mini` | Phi4 | 2.500 | Zero-shot | **Descartado** (H13) |
| `qwen3.5:2b` | Qwen3.5 | 3.829 | Zero-shot | **Descartado** (H16) |

### `gemma4:e4b` — o único que fechou a escada inteira

Nota máxima em todos os quatro níveis (S1→S4), STAB=4 (repetiu idêntico 12h depois), throughput de
73,0 tok/s. Um detalhe técnico interessante achado no laboratório (`NOTE-0003-gemma4-arquitetura.md`):
apesar do throughput alto sugerir arquitetura MoE, o `gemma4:e4b` é **denso** (8,0B parâmetros
efetivos, não Mixture-of-Experts) — a hipótese H9 de que MoE explicaria a velocidade foi
**refutada**. O throughput vem de ter menos parâmetros que o `qwen3.5:9b` (8,0B vs 9,7B) na mesma
quantização. O modelo também roda com `temperature=1` por padrão em uso real fora do protocolo do
STAB (que fixa T=0) — vale sempre especificar temperatura explicitamente em qualquer integração de
produção, já que o default não é determinístico.

Seu raciocínio interno (thinking) é ativado **seletivamente**, só nos cenários de desambiguação de
alta complexidade (S4-C, tipo desempate por timestamp) — não em todo turno. Isso é lido no artigo
como "escalonamento cognitivo adaptativo": o modelo reserva o raciocínio explícito pra quando
realmente precisa, não gasta esse custo indiscriminadamente.

### `qwen3.5:9b` — aprovado só depois de reforçar o prompt (S2B)

Na primeira tentativa (S2, prompt original), esse modelo teve `TOOL-ACC=0` — não porque não
soubesse usar a ferramenta, mas por um erro de **decisão**: usou `cat` pra ler o conteúdo do script
em vez de efetivamente executá-lo (esse é o anti-padrão **AP1**, "Ambiguidade de Ação"). Com
instrução de tool mais explícita (variante S2B), corrigiu totalmente — `TOOL-ACC=4`. Depois, em S3,
mostrou o padrão que originou o achado H10 (ortogonalidade): acertava o conteúdo semântico
perfeitamente (`CLASS-ACC=4`, `PARSE-ACC=4` em 4/4 casos), mas embrulhava a resposta em bloco de
markdown (` ```json `), violando a instrução de formato puro — esse é o **AP2**. Interessante: nos
casos em que o markdown wrapper apareceu, o JSON *dentro* dele estava sempre correto — nunca houve
correlação entre presença do wrapper e erro de conteúdo, o que é justamente a evidência que sustenta
H10.

### `qwen3:14b` — aprovado até S3, mas nasceu ali o achado H12

Passou limpo em S1, S2 e S3 (todos com nota 4), mas **colapsou completamente no S4** (nota 0 nos
três sub-cenários) — o exemplo mais claro no artigo de que "níveis complexos revelam teto que
tarefas de etapa única não revelam". A causa raiz é o achado mais citado do artigo inteiro:
**H12, tool-skipping semântico** (ver Seção 8) — descoberto exatamente com este modelo.

Um detalhe interessante do laboratório mais amplo (`HYP-0011`): esse foi o único modelo, entre
todos testados, que ativou **thinking no segundo turno** de forma consistente e preventiva (não
só como reação a algo inesperado) — volume de 976 a 1.729 caracteres dependendo da complexidade do
caso. A hipótese investigada era que esse "pensar antes de responder" funcionaria como mecanismo de
revisão pré-output, ajudando o modelo a manter conformidade de formato (`INST=4` mantido mesmo em
S3). A hipótese foi confirmada parcialmente: o mecanismo de fato correlaciona com formato estável,
mas **não previne falhas de decisão** — o mesmo modelo que usa esse "pensar duas vezes" pra acertar
o formato ainda caiu no tool-skipping do S4. São capacidades independentes.

### `llama3.1:8b` e `llama3-groq-tool-use:8b` — fine-tuning vs. zero-shot, resultado dividido

Os dois compartilham a mesma base (Llama3.1:8b), mas o `llama3-groq-tool-use:8b` passou por
fine-tuning específico pra uso de ferramentas. No S3-mixed (aplicar uma regra de precedência
binária: qualquer linha `CRITICAL` no log, mesmo cercada de ruído `INFO`/`WARNING`, define a
severidade do log inteiro como crítica), o modelo especializado ganhou com folga (`Groq=4` vs
`Llama=2`) — especialização funciona pra conformidade estrutural em etapa única. Mas em S4-B e
S4-C (decisões de múltiplas etapas), **os dois falharam igualmente**. A pergunta que isso levanta,
e que o artigo deixa em aberto como achado de discussão: fine-tuning pra uso de ferramentas melhora
aderência estrutural, mas não ensina raciocínio multi-etapa — são coisas diferentes que pipelines
de ajuste fino atuais não necessariamente cobrem juntas.

Vale notar que essa mesma falha (classificar `mixed-001.log`, que tem linhas `CRITICAL` cercadas de
ruído, como `warning` em vez de `critical`) foi investigada a fundo no laboratório mais amplo como
**H15** (`H15-s4b-escalation-ambiguity.md`) — só o `gemma4:e4b` aplicou a regra binária
corretamente de cara; todos os outros fizeram uma "avaliação proporcional implícita" (maioria das
linhas não-crítica → classificaram como warning, ignorando a regra explícita de que uma única linha
crítica basta). Um experimento de acompanhamento (`EXP-S4B-v2`) testou se reforçar a instrução
resolvia isso pros modelos que falharam: resultado **tripartido** — `qwen3.5:9b` melhorou
parcialmente (mas introduziu um novo erro em outra dimensão), `llama3.1:8b` e
`llama3-groq-tool-use:8b` **não mudaram nada** com a instrução mais forte — falha estrutural
confirmada nesses dois, não corrigível só com prompt.

### `mistral:7b` — descartado pelo achado mais sério do estudo (H14)

Em S2 e S2B, produziu um JSON **estruturalmente perfeito** (13/13 campos, tipos corretos, sem texto
extra) sem nunca ter chamado a ferramenta `run_bash`. Os dados eram **100% fabricados**: timestamp
de três anos no passado, GPU inexistente no servidor (`GTX 1650` reportada, servidor real tem RTX
3060), RAM incorreta (8GB reportado, servidor real tem 32GB). Mesmo com instrução reforçada em S2B
("use `run_bash` com o comando exato"), o modelo continuou sem chamar a ferramenta — só que o
prompt mais forte eliminou o wrapper de markdown que antes acionava o validador automático,
produzindo um **falso positivo perigoso**: `json_acc_auto=4` num resultado completamente
inventado. Esse é o **H14**, e é o achado que o artigo trata como o mais crítico
operacionalmente — ver Seção 8.

### `phi4-mini` — descartado por falha de protocolo, nem chegou a S2 (H13)

Alternou entre dois comportamentos incorretos, de forma imprevisível entre tentativas: serializar o
JSON da chamada de ferramenta manualmente dentro do campo `content` (em vez de usar o campo
`tool_calls` da API), ou simplesmente ignorar a ferramenta disponível e alucionar uma resposta
plausível no texto (ex: perguntado a temperatura em Paris, respondeu "16°C" sem consultar nada).
Por não reconhecer a estrutura correta da API de tool-calling **independentemente da instrução
dada**, essa classe de falha não é candidata a correção por prompt — nenhuma tentativa de correção
foi sequer testada, o descarte foi direto.

### `qwen3.5:2b` — resistência estrutural a instrução de formato (H16)

Mesmo padrão de wrapper de markdown do irmão maior (`qwen3.5:9b`), mas **resistente a instrução
direta**: mesmo com o prompt mais explícito possível ("NÃO use markdown. NÃO use blocos de código.
A resposta começa com `{` e termina com `}`."), testado inclusive via chamada crua à API (sem
passar pelo script, pra eliminar qualquer suspeita de bug de captura), o wrapper persistiu. Isso
sugere causa no próprio template de chat ou no treinamento do modelo — não é ambiguidade
corrigível em tempo de inferência, ao contrário do que aconteceu com o `qwen3.5:9b`.

### Aprofundamento: o mecanismo de "pensar antes de responder" no turno 2

Vale um detalhe técnico a mais sobre o `qwen3:14b`, porque a hipótese sobre o mecanismo (HYP-0011)
teve evidência real por trás, não é só especulação. O volume de thinking gerado no segundo turno
(depois de já ter o resultado da ferramenta em mãos, antes de emitir a resposta final) variou por
caso, de um jeito que faz sentido com a ideia de "revisão antes de responder":

| Caso (cenário S3) | Thinking no turno 2 | Complexidade do cenário |
|---|---|---|
| info-001 | 976 caracteres | Mais simples — todas as linhas são INFO |
| warning-001 | **1.729 caracteres** (o maior) | Intermediário — 2 tipos de WARNING misturados |
| critical-001 | 1.244 caracteres | Alto — 3 linhas CRITICAL explícitas |
| mixed-001 | 1.577 caracteres | Alto — níveis mistos (INFO+WARNING+CRITICAL) |

O caso que gerou mais raciocínio não foi o mais "grave" (critical-001), foi o `warning-001` — que
exige distinguir corretamente "nenhuma linha CRITICAL" de "pelo menos uma WARNING", uma
verificação mais delicada de ausência do que de presença. Isso é consistente com a hipótese de que
o modelo está genuinamente confirmando a ausência de CRITICAL antes de assumir `"severity":
"warning"`, não só gerando texto de enchimento.

Comparação com os outros dois modelos testados nesse mesmo cenário S3: `gemma4:e4b` e
`qwen3.5:9b` produziram **0 caracteres** de thinking no turno 2, nos 4 casos, os dois. O
`gemma4:e4b` ainda assim manteve `INST=4` — prova de que o thinking T2 é **um caminho possível**
pra conformidade de formato, não o único; ele chega no mesmo resultado por um mecanismo de
treinamento diferente, mais robusto de fábrica.

**O limite real do mecanismo:** apesar de manter formato perfeito em S3 com esse "pensar duas
vezes", o próprio `qwen3:14b` ainda caiu de cabeça no tool-skipping do H12 no S4. Ou seja, o
mecanismo de revisão ajuda a garantir que o *formato* da resposta final saia certo, mas não previne
uma *decisão* errada tomada antes (não ler o arquivo). São camadas de comportamento distintas — uma
não compensa a outra.

### Aprofundamento: quando instrução mais forte funciona, e quando não funciona (EXP-S4B-v2)

O experimento de acompanhamento do H15 (reforçar a regra de classificação binária no prompt do
S4-B, testado nos 3 modelos que tinham falhado) produziu um resultado tripartido — vale ver a
tabela completa, porque cada linha é um tipo diferente de "corrigibilidade":

| Modelo | Nota original (S4-B) | Nota com instrução reforçada | O que mudou |
|---|---|---|---|
| `gemma4:e4b` | 4 (já passava) | — (não precisou rodar de novo) | — |
| `llama3.1:8b` | 2 | 2 | **Nenhuma mudança** — falha estrutural confirmada |
| `llama3-groq-tool-use:8b` | 2 | 2 | **Nenhuma mudança** — falha estrutural confirmada |
| `qwen3.5:9b` | 2 | 3 | Melhora parcial — `escalation_correct` foi de `False` pra `True`, mas **introduziu um novo erro** em `rank_order` que não existia antes |

Essa tabela sustenta uma categorização de três níveis de corrigibilidade que o laboratório passou a
usar depois desse experimento:

- **Intrínseco** (`gemma4:e4b`): aplica a regra binária corretamente sem precisar de nenhuma
  instrução especial — já vem assim.
- **Corrigível** (`qwen3.5:9b`): melhora com instrução explícita, e — não por acaso — foi o único
  dos três que **ativou thinking no turno 2** ao receber essa instrução reforçada (306 caracteres),
  correlação direta entre "o modelo pensou mais" e "o comportamento mudou".
- **Estrutural** (`llama3.1:8b`, `llama3-groq-tool-use:8b`): não responde à instrução de jeito
  nenhum, mesmo com a regra reescrita de forma bem mais explícita — indica que a causa não é
  ambiguidade de prompt, é algo mais profundo no comportamento consolidado do modelo.

Custo real observado do thinking no `qwen3.5:9b` nesse experimento: 22,3 segundos e 3.285 tokens,
contra ~10 segundos e ~2.450 tokens dos modelos que não pensaram — o "pensar mais pra acertar mais"
tem preço real de latência, relevante pra qualquer decisão de produção que envolva esse trade-off.

---

## 7. Taxonomia de falhas: as 5 camadas e os códigos H/AP

| Camada | Tipo | Código | Exemplo concreto | Modelo |
|---|---|---|---|---|
| Protocolo | Alucinação de Protocolo | H13 | JSON em `content` em vez de `tool_calls` | phi4-mini |
| Protocolo | Echo-tool | H16 | Entrega JSON via `run_bash echo` | qwen3.5:2b |
| Decisão | Tool-Skipping Semântico | H12 | Leitura omitida; severidade inferida do nome do arquivo | qwen3:14b |
| Formato | Markdown Wrapper | AP2 | JSON correto encapsulado em ` ```json ` | qwen3.5:9b |
| Grounding | Grounding Silencioso | H14 | JSON perfeito com dados de hardware fabricados | mistral:7b |
| Instrução | Ambiguidade de Ação | AP1 | Usou `cat` em vez de executar o script | qwen3.5:9b |

Essa tabela é, junto com o gráfico de throughput, o que mais resume visualmente o artigo — cada
linha é rastreável a um modelo real e um evento real observado, não uma categoria teórica.

---

## 8. Os achados principais, com a história completa de cada um

### H12 — Tool-Skipping Semântico

**O fenômeno:** o `qwen3:14b`, em cenários S4, recebia arquivos de log com nomes semanticamente
descritivos (ex: `critical-001.log`) e **simplesmente não os lia** — inferia a severidade só pelo
nome do arquivo e gerava a resposta a partir dessa inferência, sem nunca invocar `read_file`.

**Como foi confirmado (experimento controlado, não suposição):** a mesma bateria foi rodada duas
vezes, variando **só** o nome dos arquivos, mantendo conteúdo, prompt de sistema, schema e
temperatura idênticos:
- Com nomes descritivos (`info-001.log`, `warning-001.log`, `critical-001.log`): `read_file`
  chamado 0 vezes, `CHAIN-ACC=0`. O modelo gerou até hosts e timestamps inventados.
- Com nomes opacos (`log-alpha.log`, `log-beta.log`, `log-gamma.log`), mesmo conteúdo interno:
  `read_file` chamado 3 vezes (todos os arquivos), `CHAIN-ACC=4`. O thinking do modelo, capturado
  nessa rodada, dizia literalmente: *"Let me start by reading each file one by one."*

A hipótese sobre o mecanismo: o `qwen3:14b`, com maior volume de conhecimento implícito de
treinamento, reconhece o padrão semântico do nome do arquivo como pista suficiente pra inferir a
resposta sem verificação — um atalho cognitivo. Modelos menores testados no mesmo experimento
(`qwen3.5:9b`, `gemma4:e4b`) não fizeram esse atalho — hipótese: menos confiança no conhecimento
implícito, seguem a instrução literal com mais rigor.

**Mitigação testada e confirmada:** uma instrução explícita de leitura obrigatória
(*"ATENÇÃO: Você DEVE usar a tool `read_file` para ler CADA arquivo antes de qualquer análise. Não
infira o conteúdo pelos nomes dos arquivos."*) eliminou completamente o problema — o modelo voltou
a ler os 3 arquivos corretamente, com o thinking mostrando: *"The user emphasized not to infer the
content from the filenames, so I need to read each one."* Isso classifica H12 como falha
**comportamental**, corrigível por prompt — não arquitetural.

**Ângulo de segurança (destacado no artigo, Seção de Discussão):** se o nome do arquivo é
suficiente pra induzir o modelo a uma inferência plausível, a ferramenta de leitura **nunca é de
fato executada** — em produção, isso significa que qualquer sistema que dependa de nomes
descritivos corre o risco real de nunca verificar o conteúdo verdadeiro do que está processando.
Mitigação recomendada: identificadores opacos, ou a instrução explícita de leitura obrigatória.

### H10 — Ortogonalidade de Formato e Acurácia Semântica

**O fenômeno:** conformidade de formato (o output está no formato pedido, sem markdown, sem texto
extra) e acurácia semântica (o conteúdo está correto) são **dimensões independentes** — um modelo
pode ter uma perfeita e a outra ruim, ao mesmo tempo, no mesmo run.

**Evidência principal:** `qwen3.5:9b` em S3 teve `CLASS-ACC=4` e `PARSE-ACC=4` em 4 de 4 casos
(conteúdo sempre correto), mas `INST=2` em 2 desses 4 casos por causa do wrapper de markdown — e,
crucialmente, **nos casos com markdown, o JSON de dentro do wrapper estava sempre correto**. Nunca
houve correlação entre "teve o problema de formato" e "também errou o conteúdo" — as duas coisas
variam de forma completamente independente.

**A dimensão extra que o achado ganhou depois — grounding:** o `mistral:7b` (H14) revelou uma
terceira possibilidade que o desenho original de H10 não previa: formato certo + conteúdo
fabricado. `INST=4` (schema perfeito), mas `grounding=0` (dado inventado do zero). Isso expandiu a
taxonomia de duas pra três dimensões ortogonais: **formato (INST)**, **acurácia semântica
(CLASS-ACC/CON)**, e **grounding** (os dados têm origem real verificável, ou foram inventados?). As
três variam de forma independente — um modelo pode ter as duas primeiras perfeitas e ainda assim
fabricar tudo.

**A evidência de suporte que veio antes, em S2/S2B, e por que ela importa.** O `qwen3.5:9b`, no
prompt original de S2, teve `TOOL-ACC=0` e `INST=0` — mas essa falha **não era de acurácia
semântica**, era de decisão de ação (usou `cat` em vez de executar o script — o próprio AP1). Como
o modelo nunca chegou a produzir um JSON de verdade nesse caso, não havia conteúdo pra sequer
avaliar semanticamente. Já em S2B (prompt refinado, com instrução de ferramenta mais explícita),
o mesmo modelo conseguiu `TOOL-ACC=4`, `INST=4` e `JSON-ACC=4` em 5 de 5 execuções — confirmando
que a acurácia semântica **já estava presente** desde o início; o que mudou entre S2 e S2B foi só
a força da instrução de ação/formato, não a capacidade de entender e responder corretamente. Em
nenhum run de S2 ou S3, em nenhum modelo testado, um JSON que foi extraído com sucesso teve o
conteúdo errado — todas as falhas observadas foram sempre de ação (sem JSON pra avaliar) ou de
formato (JSON correto dentro de markdown), nunca de interpretação semântica em si.

**O comportamento por modelo, resumido:** cada modelo testado se encaixou num perfil diferente de
como lida com a etapa de formatação da resposta final — `gemma4:e4b` tem formato intrinsecamente
estável, sem precisar de instrução explícita; `qwen3:14b` mantém formato estável com instrução
padrão, aparentemente com ajuda do mecanismo de "pensar antes de responder" descrito na Seção 6;
`qwen3.5:9b` tem formato instável com instrução moderada, precisando de instrução de alta
especificidade pra suprimir o wrapper — e mesmo assim sem garantia total; `qwen3.5:2b` é o caso
extremo, resistente a qualquer instrução direta testada. Isso reforça a implicação prática mais
direta de H10 pra quem constrói agente: combinar um modelo semanticamente fraco com instrução de
formato forte não resolve a acurácia; e combinar um modelo semanticamente forte com instrução de
formato fraca só funciona se o modelo já for "instruction-stable" de fábrica — pros modelos que não
são, as duas dimensões precisam ser endereçadas separadamente, uma não compensa a outra.

### H14 — Grounding Silencioso (o achado que o artigo trata como o mais sério)

Já descrito na Seção 6 (perfil do `mistral:7b`). O que faz esse achado ser, nas palavras do próprio
artigo, "o resultado mais relevante operacionalmente a levar adiante": **um validador de schema
JSON nunca vai capturar essa falha**, porque o formato está estruturalmente correto — só um
validador semântico externo (que compare o dado reportado contra a realidade, ex: hardware real do
servidor) pegaria isso. A conclusão prática do artigo: **validadores semânticos externos não são
opcionais em produção — são a única proteção real contra esse modo de falha específico.**

Vale registrar que esse mesmo padrão de fabricação silenciosa não é exclusivo do `mistral:7b` no
laboratório mais amplo — outros modelos em outras baterias (fora do escopo dos 8 do artigo) já
mostraram o mesmo comportamento, reforçando que não é peculiaridade de um modelo isolado, mas um
modo de falha real que qualquer sistema de produção precisa se proteger contra, independente de
qual modelo estiver rodando.

### Fine-tuning vs. zero-shot — resultado dividido, sem vencedor único

Já descrito na Seção 6. A conclusão de discussão do artigo: fine-tuning pra tool use melhora
aderência estrutural em decisões de etapa única, mas **não necessariamente** ensina o raciocínio
multi-etapa necessário pra decisões encadeadas — os dois modelos (especializado e zero-shot)
falharam igualmente assim que a tarefa exigiu mais de um passo de decisão.

### Throughput e três clusters de performance

Variação de throughput entre as duas baterias (12h de intervalo) ficou **abaixo de 0,2%** para
todos os modelos — confirma que a velocidade é limitada pelo hardware, não por variação do prompt
ou do processamento em si. A primeira execução de cada bateria foi excluída das médias (penalidade
de cold start, efeito real e esperado). Três clusters de desempenho emergiram: `gemma4:e4b` e a
família Llama no topo (mais rápidos), `qwen3.5:9b` no meio, e `qwen3:14b` na base — a latência
desse último especificamente inflada pelo extenso trace de raciocínio interno no S2 (o mesmo
mecanismo de thinking descrito acima em detalhe).

### Estabilidade temporal — só uma anomalia, e não era real

Todos os 5 modelos aprovados completaram a Bateria 2 (12h depois) **sem degradação**: decisões
agênticas e acurácia semântica mantiveram `STAB=4` ao longo de todo o protocolo. A única exceção
aparente foi o `qwen3:14b`, cujo volume de raciocínio interno variou 7% entre as duas baterias —
mas a **saída final foi idêntica** nos dois casos. Conclusão: isso é uma peculiaridade estrutural
do processo de chain-of-thought desse modelo (o "quanto" ele pensa varia um pouco run a run), não
instabilidade real de decisão ou de resultado.

---

## 9. Discussão: o que os achados significam juntos

### Falhas são instrucionais, não de capacidade bruta

Esse é o fio condutor mais importante do artigo inteiro, e tem dois experimentos corretivos reais
sustentando-o: a instrução de formato explícita recuperou o `qwen3.5:9b` de `S2B=2` pra `4`; a
diretiva de leitura obrigatória eliminou completamente o tool-skipping do `qwen3:14b`. **Nenhuma
das duas correções exigiu trocar de modelo ou re-treinar** — só ajuste de prompt. Isso torna
tamanho de modelo um proxy fraco pra confiabilidade agêntica: os modelos acima de 8B testados
claramente possuem a lógica subjacente necessária; o que quebra é desalinhamento de contexto, e
isso é corrigível na camada de instrução, não um limite de capacidade.

### Recomendações práticas concretas

- **12GB de VRAM:** `gemma4:e4b` é a escolha óbvia — consistência perfeita, 73 tok/s, sem precisar
  de nenhuma engenharia de prompt adicional.
- **Menos de 6GB:** `llama3.1` funciona, mas precisa de uma camada fina de pós-processamento pra
  tratar falhas de formato que ele ainda comete.
- **Ângulo de segurança do H12** já descrito: nomes de arquivo descritivos criam um risco real de a
  ferramenta nunca ser de fato executada.

### Decodificação com restrição gramatical — a mitigação que o artigo aponta mas não testou

O `AP2` (wrapper de markdown) e a resistência total à instrução do `qwen3.5:2b` são falhas de
**formato**, não de conteúdo — o modelo "sabe" a resposta certa, só a emite de um jeito que o
parser não aceita. Engenharia de prompt resolve isso só parcialmente (recuperou o `qwen3.5:9b`, não
o `qwen3.5:2b`). A alternativa discutida: **decodificação com restrição gramatical** (GBNF via
`llama.cpp`, Outlines, ou `format=json` do próprio Ollama) — em vez de atacar a camada de entrada
(o prompt), ataca a camada de **decodificação** (a geração de token em si), tornando a violação de
formato **impossível** independentemente de o modelo "cooperar" ou não. É a candidata natural
exatamente pros casos resistentes a instrução direta, como o `qwen3.5:2b`. **O STAB não testou essa
técnica** — fica registrado explicitamente como extensão natural de trabalho futuro, não como algo
esquecido.

---

## 10. Limitações reconhecidas e trabalho futuro

O artigo é direto sobre os próprios limites, sem esconder nada:

- **Uma única configuração de hardware, fixtures sintéticas.** Trade-off deliberado — tornou
  possível reprodutibilidade total e isolamento de variável, ao custo de não capturar o ruído real
  de logs de produção (timestamps malformados, encoding inconsistente, entrada truncada, múltiplos
  problemas concorrentes no mesmo log).
- **K pequeno (5/5/4/3).** Reduz poder estatístico — os resultados devem ser lidos como
  **diagnóstico qualitativo**, não como taxa de erro com significância estatística formal. Essa
  ressalva já está escrita no artigo, não é algo que precisa ser escondido se alguém perguntar.
- **S4 é o candidato mais provável a degradar ainda mais sob ruído real** — é já o nível de queda
  mais acentuada mesmo com fixtures limpas; validação direta com logs reais fica como extensão
  natural.
- **A bateria de 12h também não responde** se deployments muito mais longos (dias, semanas)
  expõem padrões de degradação que não apareceram nesse intervalo mais curto.

Essas não são lacunas escondidas — são exatamente as perguntas que os próprios dados deste estudo
levantam, e o artigo termina dizendo isso explicitamente: são extensões naturais "não por
convenção, mas porque os dados deste estudo levantam essas questões específicas".

---

## 11. O programa de pesquisa mais amplo: a tese das propriedades arquiteturais

Esse conteúdo **não está no artigo STAB** (é trabalho paralelo/posterior do mesmo laboratório), mas
ajuda a situar o STAB dentro de um programa de pesquisa maior que continua ativo.

### O problema que motivou a tese

Rankings de benchmark de LLM pra uso agêntico local são **instáveis entre ciclos de avaliação** —
mesmo sem mudar o protocolo intencionalmente. Evidência direta coletada no laboratório: o
`qwen3.5:9b` registrou 3,64 numa bateria de maio/2026 e 3,35 em junho/2026 — mesma tag de modelo,
possivelmente um blob GGUF atualizado silenciosamente por trás. O `gemma4:e4b` variou entre 3,20 e
3,54. O modelo "líder" mudou entre praticamente cada ciclo. Conclusão registrada: **congelar o
stack é ilusão de controle num sistema vivo** — o campo evolui mais rápido que qualquer snapshot de
avaliação.

### A tese central

> "Propriedades arquiteturais predizem capacidade agêntica de forma mais robusta do que contagem de
> parâmetros ou scores pontuais de benchmark."

Três evidências robustas, estáveis entre ciclos diferentes:

1. **Tipo de mecanismo de atenção prediz desempenho multi-turn.** Modelos com arquitetura SSM ou
   híbrida SSM/attention falharam sistematicamente em cenários multi-turno com handoff de contexto
   — e esse padrão se repetiu em arquiteturas de fabricantes diferentes (Liquid/`lfm2`,
   Qwen), sugerindo que é fator arquitetural, não coincidência de uma família específica.
2. **Tamanho de parâmetros não prediz qualidade agêntica.** `granite4.1:8b` (8B) superou
   `qwen3.6:27b` (27B) em score geral (3,57 vs 3,48) — modelo maior da mesma classe de tarefa não
   supera sistematicamente o menor.
3. **Prompt engineering não corrige limitações arquiteturais (H1, rejeitada como intervenção
   universal).** Um prefixo de sistema (`/no_think`) testado no `qwen3:30b-a3b` não só não
   corrigiu o comportamento de "pensar em voz alta" indesejado como **piorou** o resultado em 2 de
   6 cenários testados — evidência de que esse comportamento está codificado no treinamento, não é
   uma escolha de prompt reversível.

Essa tese é o pano de fundo intelectual que também explica por que o STAB, especificamente, foca
tanto em separar **falha comportamental** de **falha arquitetural** (H12 corrigível por prompt;
H13/H14 não) — é a mesma pergunta de fundo aplicada a um recorte publicável e mais compacto.

**Uma quarta evidência**, complementar às três acima: tool calling **perfeito** (`TOOL-ACC=4,00`)
se mostrou reproduzível e previsível num conjunto amplo de modelos com arquitetura densa padrão e
treinamento robusto de instruction-following — não é exclusividade de nenhuma família específica
nem correlaciona com tamanho (a lista de modelos que atingiram isso de forma consistente inclui
tanto modelos pequenos quanto grandes, densos e MoE). O preditor real parece ser "arquitetura densa
+ treinamento de chat com function calling", não parâmetro nenhum isolado.

### O protocolo H1/H2 que originou o método de diagnóstico (o caso completo)

Vale ver o experimento original que deu origem ao protocolo comportamental-vs-arquitetural descrito
na Seção 3, porque ele é o modelo de como qualquer hipótese nova deveria ser testada nesse
laboratório — hipótese, intervenção cirúrgica isolada, rerun controlado, diagnóstico pelo
resultado, sem ambiguidade.

Modelo testado: `qwen3:30b-a3b` (MoE, 3B parâmetros ativos por vez).

| Hipótese | Intervenção testada | Cenários testados | Resultado | Diagnóstico |
|---|---|---|---|---|
| **H1** | Prefixo de sistema `/no_think` | 6 cenários (C4, M1-A, M1-H, M2-A, M2-H, L3) | 0 melhoras, **2 pioras** | **Arquitetural** |
| **H2** | Instrução explícita de grounding | Q2 | 0,0 → 1,5 (melhora parcial) | **Comportamental** (parcial) |

Em H1, o modelo continuou produzindo cadeia de raciocínio verbal mesmo com instrução explícita de
suprimi-la — e ainda piorou em 2 dos 6 cenários testados (ruído introduzido pelo prefixo, sem
ganho compensatório em nenhum lugar). Conclusão: "pensar em voz alta" está codificado no
treinamento desse modelo, não é uma escolha reversível por prompt.

Em H2, uma instrução de grounding mais explícita elevou o score de Q2 de 0,0 pra 1,5 — melhora
real, mas parcial (não total). Classificado como comportamental: o modelo tinha a capacidade
subjacente, só precisava de instrução mais explícita pra exercê-la de verdade — mas "melhora
parcial" também é reconhecida como uma zona cinzenta real: o critério de corte entre "comportamental
resolvido" e "comportamental mas ainda insuficiente pra produção" não chegou a ser formalizado.

### Como essa tese seria estruturada como paper próprio (rascunho ainda não publicado)

O laboratório já esboçou a estrutura argumentativa completa pra essa tese virar um artigo
independente do STAB, em 5 movimentos:

1. **Motivação** — praticantes usam benchmarks pontuais pra escolher modelo; mostrar que esses
   rankings são instáveis mesmo com a mesma tag de modelo entre ciclos.
2. **Evidência negativa** — dois rankings lado a lado (maio vs. junho/2026), delta ≥0,3 em modelos
   nominalmente idênticos, enumerar as fontes de variância (atualização silenciosa de blob GGUF,
   temperatura default não fixada, versão de runtime/driver). Conclusão: scores absolutos têm
   validade preditiva limitada.
3. **Identificação de preditores estáveis** — as propriedades estruturais que se repetem entre
   baterias, famílias e configurações de hardware diferentes.
4. **Implicação prática** — quem sabe que "SSM falha em multi-turn" e "8B já basta pra tool
   calling" toma decisão melhor do que quem segue o ranking mais recente de um paper de 6 meses
   atrás.
5. **Contribuição metodológica** — o próprio protocolo de avaliação como ferramenta de análise
   estrutural, não só de ranking pontual.

Título candidato registrado: *"Beyond Point-in-Time Rankings: Architectural Properties as Robust
Predictors of On-Premises LLM Agentic Performance"* (versão PT-BR: *"Além dos Rankings Pontuais:
Propriedades Arquiteturais como Preditores Robustos de Desempenho Agêntico em LLMs
On-Premises"*).

**Limitações já reconhecidas nesse rascunho**, mesma cultura de honestidade do STAB: avaliação
feita num hardware específico (Xeon E5-2696v3 + 2× RTX 3060 12GB, diferente inclusive do setup de
uma GPU do próprio STAB); temperatura não fixada em 0 em toda a bateria mais ampla (diferente do
STAB, que fixa T=0 rigorosamente); protocolo ainda não validado externamente por terceiros; amostra
pequena (12 runs por modelo) na série multi-turn especificamente; e uma ressalva metodológica
importante — a instabilidade de ranking observada pode refletir melhoria real dos modelos ao longo
do tempo, não só ruído de medição, e essa possibilidade ainda não foi isolada da outra.

---

## 12. A jornada até o camera-ready

### Submissão original e aceite

O artigo foi submetido em PT-BR (corpo em português, título/abstract/keywords obrigatoriamente em
inglês pelas regras do evento) via JEMS3 (`jems3.sbc.org.br/kdmile2026`), trilha Main Track,
submissão #29261. **Resultado forte:** 3 revisores, todos recomendaram aceite (notas 5, 5, e 4 —
"weak accept"). Dois dos três marcaram "talvez" pra categoria de melhor artigo.

### Os 9 pontos de revisão incorporados no camera-ready

Cada revisor levantou pontos de melhoria (não bloqueantes — já era aceite garantido), todos
incorporados na versão final:

1. Aprofundamento da discussão sobre como o framework lidaria com ruído não-determinístico de logs
   reais de produção vs. fixtures sintéticas (especificamente no nível S4).
2. Expansão sobre decodificação com restrição gramatical como mitigação agnóstica ao modelo pra
   erros de formato.
3. Comentário sobre se houve tentativa de refatorar prompt pros 3 modelos eliminados antes de
   descartá-los (mesma técnica que funcionou pro H12).
4. Detalhamento dos motivos estruturais específicos de cada um dos 3 modelos eliminados nos níveis
   iniciais — `phi4-mini` (H13, S1), `qwen3.5:2b` (H16, S2), `mistral:7b` (H14, S2).
5. Correção de formatação — linhas estourando a margem na página 6 (causa raiz real: travessão
   colado direto na palavra seguinte sem espaço, combinado com palavra sem ponto de hifenização
   válido — corrigido com `\allowbreak` sistematicamente em todo o corpo do texto, 28 ocorrências).
6. Ampliação de trabalhos relacionados (bibliografia limitada na versão original).
7. Definição formal do que conta como "falha" nos testes (crítica vs. não-crítica).
8. Explicação melhor da metodologia da bateria de estabilidade de 12h.
9. Reconhecimento explícito da limitação de poucos testes por nível de complexidade.

O documento ficou em **8 páginas exatas** (dentro do limite do evento, com folga real — a página 8
só vai até a metade).

### A submissão do camera-ready — hoje, dia do próprio deadline

O deadline real do camera-ready era **24/ago/2026, 23:59** — hoje. Um lembrete automático tinha
sido agendado pra 21/ago como gatilho antecipado, mas não resultou em envio na hora certa; ainda
assim, o prazo real não foi perdido. Antes do upload, o PDF final foi verificado ponto a ponto
contra os 9 itens de revisão listados acima (todos presentes, confirmados um a um), contagem de
páginas (8, confirmado), e conformidade de idioma (título/abstract/keywords em inglês, corpo em
PT-BR, conforme regra do evento). Arquivo final:
`29261_Nogueira_STAB_KDMiLe2026_camera-ready.pdf`, submetido no JEMS3.

### Apresentação confirmada

Formato definido pelos organizadores (resposta direta do chair Jorge Soares): **presencial, oral,
com slides, 15 minutos**, em Cuiabá-MT (Centro de Eventos do UniSENAI, 19–22 de outubro de 2026).
Não presencial não era opção. O deck de slides pra essa apresentação formal ainda não foi
construído — é entregável separado e distinto de qualquer material informal já preparado pra outras
ocasiões (ex: uma live com um professor amigo).

---

## 13. Linha do tempo consolidada

Pra ancorar tudo isso numa sequência real, sem precisar reconstruir a ordem de cabeça:

| Data | Evento |
|---|---|
| Abril/2026 | `ADR-0001` — critérios de avaliação definidos (CON, TOOL-CON, INST, TOOL-ACC, STAB), fundação de todo o vocabulário usado até o artigo final |
| 24-25/abril/2026 | Implementação e execução de S1→S4 pros primeiros modelos; descoberta de H12 (tool-skipping), H13 (phi4-mini), H14 (mistral), H15 (escalation em log misto); experimento EXP-S4B-v2 |
| 01/junho/2026 | Caso original H1/H2 (`qwen3:30b-a3b`) que originou o protocolo de diagnóstico comportamental vs. arquitetural |
| 03/junho/2026 | Rascunho da tese de propriedades arquiteturais (`NOTE-0005`), motivada pela instabilidade de ranking observada entre ciclos de bateria |
| 03-04/junho/2026 | Experimento H_context — validação de que `num_ctx=4096` não penaliza nenhum modelo testado (cenários nunca usam mais de ~28% da janela) |
| 08/junho/2026 | Deadline original de submissão do KDMiLe 2026 |
| ~mai-jun/2026 | Compilação e submissão do artigo STAB (PT-BR, JEMS3, submissão #29261, trilha Main Track) |
| 10/julho/2026 | Formalização do protocolo de diagnóstico comportamental vs. arquitetural (`NOTE-0007`) como método replicável, pronto pra citação |
| 17-18/agosto/2026 | Notificação de aceite — 3 revisores, notas 5/5/4, "weak accept" na pior delas, 2 marcaram "talvez" pra melhor artigo |
| 18/agosto/2026 | Incorporação dos 9 pontos de revisão no camera-ready; correção de vazamento de margem (`\allowbreak`); confirmação de 8 páginas exatas |
| 19/agosto/2026 | Apresentação confirmada como presencial, oral, com slides, 15 minutos (resposta do chair Jorge Soares) |
| **24/agosto/2026** | **Camera-ready verificado ponto a ponto e enviado no JEMS3** — dia do próprio deadline (23:59) |
| 19-22/outubro/2026 | Evento KDMiLe 2026, Cuiabá-MT (Centro de Eventos do UniSENAI) — apresentação oral agendada |

---

## 14. Glossário rápido de referência

Pra consulta pontual sem precisar reler a seção inteira:

- **STAB** — o framework como um todo; também o nome da métrica de estabilidade temporal
  especificamente (diferença de escore entre Bateria 1 e Bateria 2, 12h de intervalo).
- **S1→S4** — a escada de complexidade: Protocolo → Extração → Análise de Log → Multi-log.
- **K** — número de execuções por nível; muda de sentido: repetição do mesmo input em S1/S2
  (mede consistência), casos diferentes em S3/S4 (mede cobertura).
- **T=0** — temperatura zero, decodificação determinística/gulosa, usada em todo o protocolo por
  reprodutibilidade.
- **H (código)** — achado confirmado por experimento controlado com hipótese testada
  explicitamente (ex: H12, H14).
- **AP (código)** — anti-padrão observado durante execução padrão, sem experimento dedicado de
  confirmação por trás (ex: AP1, AP2).
- **Falha comportamental** — corrigível por engenharia de prompt; o modelo tem a capacidade, só
  precisa de instrução melhor.
- **Falha arquitetural** — codificada no treinamento; nenhuma instrução de prompt resolve, o
  remédio é trocar de modelo.
- **Grounding** — se o dado reportado pelo modelo tem origem real verificável, ou foi inventado
  (H14 é o caso extremo: formato perfeito, conteúdo 100% fabricado).
- **Tool-skipping** — o modelo pula a chamada de ferramenta e infere/alucina o resultado (H12,
  gatilho: nome de arquivo semanticamente descritivo).
- **Ortogonalidade (H10)** — formato, acurácia semântica e grounding variam de forma independente
  entre si; nenhum prediz o outro.
- **ABS** — a frente de avaliação mais ampla do laboratório, contexto curto fixo (`num_ctx=4096`),
  chegou a testar 17 modelos numa bateria.
- **LOP (S1→S4)** — a frente que evoluiu diretamente pro STAB, contexto default de cada modelo, mais
  próxima de condição de produção.
- **LOP2 / benchmark-llms-on-premise** — o projeto sucessor, repositório separado, matriz e modelos
  de referência diferentes — não é este raio-X, é continuação do mesmo espírito metodológico noutro
  escopo.

---

## 15. Onde isso te deixa agora

O STAB, como projeto de pesquisa isolado, está numa posição sólida: artigo aceito por 3 revisores
sem ressalva bloqueante, camera-ready enviado dentro do prazo, apresentação formal já confirmada
pra outubro. Os achados centrais (H12, H10/H14, a discussão de fine-tuning vs. zero-shot) são
resultado de experimento controlado real, não de opinião — e o próprio artigo já é honesto sobre
onde ficam as lacunas (fixtures sintéticas, K pequeno, decodificação restrita não testada).

O trabalho que sucede o STAB dentro deste mesmo programa de pesquisa mais amplo já está em
andamento em um repositório separado (`benchmark-llms-on-premise`, o "LOP2-Infraestrutura") — uma
matriz mais recente, com modelos de referência diferentes (Qwen3.8-27B, Qwen3.6-35B-A3B, Muse
Glimmer-30B, Gemma-4-26B-A4B), 3 harnesses de agente (Claude Code, Hermes, DSH) e 9 cenários
próprios, herdando o mesmo espírito metodológico do STAB (medir capacidade real, não confiar em
impressão subjetiva, separar causa comportamental de causa estrutural) mas com escopo e cenários
completamente distintos — é um projeto separado, não uma continuação direta deste raio-X.
