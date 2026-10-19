## Enunciado
Modelos com maior capacidade de inferência contextual tendem a pular tool calls
quando o prompt contém pistas semânticas suficientes para inferir a resposta
sem executar as ferramentas disponíveis.

## Status
Confirmada — experimento H12 em 2026-04-25

## Evidência empírica (fatos observados)

S4-A (nomes descritivos):
- Arquivos: info-001.log, warning-001.log, critical-001.log
- qwen3:14b: read_file chamadas = 0, CHAIN-ACC = 0
- Modelo gerou JSON com hosts inventados e timestamp de 2023

H12 (nomes opacos — mesmos conteúdos):
- Arquivos: log-alpha.log, log-beta.log, log-gamma.log
- qwen3:14b: read_file chamadas = 3, CHAIN-ACC = 4
- Thinking observado: "Let me start by reading each file one by one"
- Modelo leu os arquivos e gerou triagem correta

Variável isolada: apenas o nome dos arquivos no prompt foi alterado.
Conteúdo dos logs, prompt de sistema, schema, tool disponível e temperatura
foram idênticos nos dois cenários.

## Modelos testados
- qwen3:14b: confirmado — falha com nomes descritivos, passa com nomes opacos
- qwen3.5:9b: não falhou em S4 (chamou read_file em todos os casos, incluindo S4-A)
- gemma4:e4b: não falhou em S4

## Hipótese sobre o mecanismo
O qwen3:14b, com maior volume de conhecimento implícito de treinamento, reconhece
os padrões semânticos em nomes como "critical-001", "warning-001", "info-001"
como pistas suficientes para inferir a resposta sem verificação.
Modelos menores (9b, gemma4) não fazem esse shortcut — possivelmente porque
têm menos confiança no conhecimento implícito e seguem a instrução literal.

## Implicação prática para design de agentes
- Nunca usar nomes de arquivo semanticamente reveladores em prompts de tool use
  quando o modelo deve ler o arquivo antes de responder
- Isso se aplica a: paths, variáveis, IDs, nomes de chave em dicionários
- O fenômeno é mais provável em modelos maiores e mais capazes
- Mitigação: usar nomes opacos (UUIDs, hashes, sequências numéricas sem semântica)
  ou adicionar instrução explícita "Você DEVE ler o arquivo antes de qualquer conclusão"

## Próximos passos
- Testar se a instrução explícita "Leia o arquivo antes de responder"
  é suficiente para mitigar o tool-skipping no qwen3:14b com nomes descritivos
- Verificar se o fenômeno aparece em outros modelos maiores (ex: qwen3:30b+)
- Registrar como anti-pattern de design de agentes na documentação do laboratório

## Referências
- fixtures/triage-s4/S4-A.expected.json
- results/benchmarks/S4-qwen3-14b-2026-04-25-case-S4-A.txt
- fixtures/h12-opaque-names/

## Experimento de mitigação (2026-04-25)

Teste: mesmo prompt S4-A com nomes descritivos + instrução explícita adicionada:
"ATENÇÃO: Você DEVE usar a tool read_file para ler CADA arquivo antes de qualquer
análise. Não infira o conteúdo pelos nomes dos arquivos. Leia os arquivos primeiro."

Resultado: qwen3:14b chamou read_file 3 vezes corretamente.
Thinking observado: "The user emphasized not to infer the content from the
filenames, so I need to read each one."

Conclusão: o tool-skipping é corrigível por instrução explícita.
A mitigação mais simples e eficaz é adicionar a instrução de leitura obrigatória
diretamente no prompt, independente do naming dos arquivos.
