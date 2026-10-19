#!/usr/bin/env bash
# =============================================================================
# run-s1-benchmark.sh
#
# Executa o cenário S1 (Health check estático) definido em:
#   docs/benchmarks/evaluation-framework.md — seções 4.1 a 4.5
#
# Para cada run:
#   - Envia o prompt S1 ao modelo via `docker exec ollama ollama run`.
#   - Salva a resposta bruta em results/benchmarks/S1-{modelo}-{data}-run{N}.txt.
# Ao final:
#   - Gera results/benchmarks/S1-{modelo}-{data}-summary.md com a tabela vazia
#     para preenchimento manual das notas CON, TOOL-CON, INST, TOOL-ACC.
#
# Uso:
#   bash scripts/run-s1-benchmark.sh <modelo>
#
# Exemplo:
#   bash scripts/run-s1-benchmark.sh qwen3.5:9b
#
# O script deve ser executado a partir da raiz do repositório llms-on-prem.
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# DECISÃO: verificar que o script está sendo executado do diretório correto.
# A presença de docs/benchmarks/evaluation-framework.md é o marcador da raiz.
# Isso evita que os paths relativos de results/ apontem para o lugar errado.
# -----------------------------------------------------------------------------
if [[ ! -f "docs/benchmarks/evaluation-framework.md" ]]; then
    echo "ERRO: execute este script a partir da raiz do repositório llms-on-prem."
    echo "       Uso: bash scripts/run-s1-benchmark.sh <modelo>"
    exit 1
fi

# -----------------------------------------------------------------------------
# ARGUMENTO: nome do modelo Ollama (obrigatório).
# DECISÃO: argumento posicional em vez de flag para simplicidade de uso.
# O nome deve ser exatamente como retornado por `ollama list`
# (ex.: qwen3.5:9b, deepseek-r1:8b).
# -----------------------------------------------------------------------------
MODEL="${1:?ERRO: informe o nome do modelo. Uso: bash scripts/run-s1-benchmark.sh <modelo>}"

# -----------------------------------------------------------------------------
# K = 5 execuções por bateria.
# DECISÃO: conforme evaluation-framework.md e plano de experimento S1,
# K=5 é o mínimo para observar variação intra-bateria sem custo excessivo.
# Aumentar para K=10 apenas após confirmar que o fluxo de registro funciona.
# -----------------------------------------------------------------------------
K=5

# -----------------------------------------------------------------------------
# DATA no formato YYYY-MM-DD.
# DECISÃO: ordenação lexicográfica garante que arquivos fiquem em sequência
# cronológica nos listagens de results/benchmarks/ (evaluation-framework.md 4.5).
# -----------------------------------------------------------------------------
DATE=$(date +%Y-%m-%d)
RESULTS_DIR="results/benchmarks"
mkdir -p "$RESULTS_DIR"

# -----------------------------------------------------------------------------
# NOME SEGURO para uso em caminhos de arquivo.
# DECISÃO: substituir ':' por '-' porque ':' é inválido em nomes de arquivo
# em vários sistemas e causa problemas com path expansion no bash.
# Exemplo: qwen3.5:9b → qwen3.5-9b
# -----------------------------------------------------------------------------
MODEL_SAFE="${MODEL//:/-}"

# -----------------------------------------------------------------------------
# PROMPT exato do cenário S1.
# FONTE: docs/benchmarks/evaluation-framework.md, seção 4.2.
# DECISÃO: o prompt é definido aqui como variável fixa e NÃO é alterado entre
# runs nem entre baterias. Qualquer alteração no prompt invalida a comparação
# de CON e STAB, violando os antiobjetivos do projeto (ADR-0001).
# A formatação em negrito (**exata**) foi removida pois é markdown — o modelo
# via pipe recebe texto plano; manter asteriscos seria ruído desnecessário.
# -----------------------------------------------------------------------------
PROMPT='Execute o script ~/scripts/health.sh e encaminhe a saída exata, sem alterar nada (sem resumo, sem comentários, sem tradução, sem reordenação), para o destino configurado como MONITOR_HEALTH.

Se não conseguir executar o script, responda apenas com a mensagem:
ERRO: não consegui executar health.sh
e não tente inventar a saída.'

# -----------------------------------------------------------------------------
# PAUSA ENTRE RUNS: 30 segundos.
# DECISÃO: reduz risco de reutilização de cache de KV entre runs independentes.
# Fonte: plano de experimento S1, seção 4 (passo 8).
# Diminuir ou remover apenas se confirmado que o Ollama não reutiliza cache
# entre chamadas distintas de `ollama run` para o mesmo modelo.
# -----------------------------------------------------------------------------
SLEEP_BETWEEN_RUNS=30

# -----------------------------------------------------------------------------
# NOTA IMPORTANTE — LIMITAÇÃO DE TOOL USE COM `ollama run`:
#
# O comando `ollama run` em modo pipe (stdin não-interativo) não fornece
# definições de tools ao modelo. Portanto, o modelo não pode emitir chamadas
# de tool estruturadas da forma que um framework de agente esperaria.
#
# O que este script realmente testa em S1:
#   - Se o modelo indica intenção de executar ~/scripts/health.sh (TOOL-ACC).
#   - Se essa indicação é consistente entre runs (TOOL-CON).
#   - Se o modelo segue as instruções de formato do prompt (INST).
#   - Se as respostas são estruturalmente equivalentes entre runs (CON).
#
# O que este script NÃO testa:
#   - Execução real do script no servidor.
#   - Chamada de tool via schema JSON/function calling.
#
# Para testes com tool calling real, a próxima evolução deve usar a API REST
# do Ollama (POST /api/chat com "tools": [...]) ou um framework de agente.
# Isso deve ser registrado como ADR quando a fase de testes avançar.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# NOTA — TEMPERATURA VIA `ollama run`:
#
# O subcomando `ollama run` não expõe --temperature como flag CLI direta.
# Para controlar temperatura=0 com precisão, as alternativas são:
#   (a) Criar um Modelfile com `PARAMETER temperature 0` e usar o modelo derivado.
#   (b) Usar a API REST: POST /api/generate com "options": {"temperature": 0}.
#
# Nesta versão inicial, o script usa o modelo sem modificação de temperatura
# e documenta essa limitação. O comportamento do modelo com a temperatura
# padrão (geralmente 0.7–1.0) pode introduzir variação extra nos resultados.
# Registrar no summary qual temperatura estava ativa é responsabilidade do
# avaliador (verificar via `ollama show <modelo>` antes de rodar).
# -----------------------------------------------------------------------------

# =============================================================================
# EXECUÇÃO DAS K RUNS
# =============================================================================

echo "=========================================================="
echo "  S1 Benchmark"
echo "  Modelo : ${MODEL}"
echo "  Data   : ${DATE}"
echo "  K runs : ${K}"
echo "  Pausa  : ${SLEEP_BETWEEN_RUNS}s entre runs"
echo "=========================================================="
echo ""

for i in $(seq 1 $K); do
    OUTPUT_FILE="${RESULTS_DIR}/S1-${MODEL_SAFE}-${DATE}-run${i}.txt"
    RUN_TS=$(date +"%Y-%m-%d %H:%M:%S")

    echo "[Run ${i}/${K}] ${RUN_TS}"

    # -------------------------------------------------------------------------
    # CABEÇALHO DE METADADOS no arquivo de output.
    # DECISÃO: incluir metadados no próprio arquivo de run para rastreabilidade
    # independente do summary. Facilita revisão posterior sem abrir outros arquivos.
    # -------------------------------------------------------------------------
    {
        printf "# S1 — Run %d\n" "$i"
        printf "# Modelo    : %s\n" "$MODEL"
        printf "# Data/hora : %s\n" "$RUN_TS"
        printf "# Prompt    : evaluation-framework.md seção 4.2 (inalterado)\n"
        printf "# Runner    : docker exec ollama ollama run%s\n" "${THINK_FLAG:+ $THINK_FLAG}"
        printf "# Temp      : padrão do modelo (ver nota no script)\n"
        printf "# ----------------------------------------------------------\n"
        printf "\n"
    } > "$OUTPUT_FILE"

    # -------------------------------------------------------------------------
    # EXECUÇÃO DO MODELO via docker exec.
    # DECISÃO: usar -i (não -it) porque stdin é pipe, não TTY.
    #   -t aloca um pseudo-TTY — se stdin não for um terminal, causa erro
    #   "the input device is not a TTY" e corrompe o output.
    # DECISÃO: redirecionar stderr para o mesmo arquivo (2>&1) para capturar
    #   erros do Ollama (ex.: modelo não encontrado, OOM) junto com a resposta,
    #   facilitando o diagnóstico sem perder contexto.
    # DECISÃO: usar `sed` para remover escape codes ANSI caso o Ollama os emita
    #   mesmo sem TTY (comportamento inconsistente entre versões).
    # DECISÃO: --think=false para modelos Qwen3 (qwen3.*:*).
    #   Sem esse flag, o Qwen3 emite "Thinking...\n<CoT>\n...done thinking.\n"
    #   antes da resposta — contamina CON e INST. --think=false suprime o bloco
    #   na fonte (sem geração de tokens de CoT). Flag é no-op em modelos sem
    #   suporte a thinking (phi4, granite, mistral etc.).
    # -------------------------------------------------------------------------
    THINK_FLAG=""
    case "$MODEL" in
        qwen3:*|qwen3.*:*) THINK_FLAG="--think=false" ;;
    esac

    # shellcheck disable=SC2086
    echo "$PROMPT" \
        | docker exec -i ollama ollama run $THINK_FLAG "$MODEL" 2>&1 \
        | sed 's/\x1B\[[0-9;?]*[A-Za-z]//g; s/\r//g; s/[⠀-⣿]//g' \
        >> "$OUTPUT_FILE"

    echo "  -> salvo: ${OUTPUT_FILE}"

    # -------------------------------------------------------------------------
    # PAUSA entre runs (exceto após o último).
    # -------------------------------------------------------------------------
    if [[ "$i" -lt "$K" ]]; then
        echo "  -> aguardando ${SLEEP_BETWEEN_RUNS}s..."
        sleep "$SLEEP_BETWEEN_RUNS"
    fi

    echo ""
done

echo "=========================================================="
echo "  ${K} runs concluídos."
echo "=========================================================="
echo ""

# =============================================================================
# GERAÇÃO DO SUMMARY
# FORMATO: tabela markdown de evaluation-framework.md seção 4.5.
# DECISÃO: notas CON/TOOL-CON/INST/TOOL-ACC ficam INTENCIONALMENTE em branco —
# devem ser preenchidas pelo avaliador após leitura de cada run,
# aplicando os critérios de ADR-0001 e evaluation-framework.md seção 4.4.
# O script não atribui notas automaticamente para não introduzir viés de
# julgamento computacional na fase em que a escala é ordinal e manual.
# =============================================================================

SUMMARY_FILE="${RESULTS_DIR}/S1-${MODEL_SAFE}-${DATE}-summary.md"

{
    printf "# S1 Summary — %s — %s\n\n" "$MODEL" "$DATE"

    printf "## Metadados\n\n"
    printf "| Campo                  | Valor                                     |\n"
    printf "|------------------------|-------------------------------------------|\n"
    printf "| Cenário                | S1 – Health check estático                |\n"
    printf "| Modelo                 | %s                                        |\n" "$MODEL"
    printf "| Bateria                | 1                                         |\n"
    printf "| Data                   | %s                                        |\n" "$DATE"
    printf "| K (runs)               | %d                                        |\n" "$K"
    printf "| Temperatura            | _(verificar via \`ollama show %s\`)_      |\n" "$MODEL"
    printf "| Stream                 | não (pipe não-interativo)                 |\n"
    printf "| Runner                 | docker exec ollama ollama run             |\n"
    printf "| Tool use real          | não — modo texto puro (ver script)        |\n"
    printf "| VRAM disponível início | _(preencher manualmente)_                 |\n"
    printf "\n"

    printf "## Resultados\n\n"
    printf "Preencher as colunas CON, TOOL-CON, INST e TOOL-ACC com notas de 0 a 4\n"
    printf "conforme critérios definidos em:\n"
    printf "- \`docs/decisions/ADR-0001-criterios-de-avaliacao.md\`\n"
    printf "- \`docs/benchmarks/evaluation-framework.md\`, seção 4.4\n\n"

    printf "| Data       | Modelo | Configuração | Run | CON | TOOL-CON | INST | TOOL-ACC | STAB-nota-local | Observações curtas |\n"
    printf "|------------|--------|--------------|-----|-----|----------|------|----------|-----------------|--------------------|\n"
    for i in $(seq 1 $K); do
        printf "| %s | %s | temp=padrão, no_stream | %d |     |          |      |          | n/a             |                    |\n" \
            "$DATE" "$MODEL" "$i"
    done

    printf "\n"
    printf "## Notas por dimensão (Bateria 1)\n\n"
    printf "- **CON:** _(preencher após leitura dos %d runs)_\n" "$K"
    printf "- **TOOL-CON:** _(preencher após leitura dos %d runs)_\n" "$K"
    printf "- **INST:** _(preencher após leitura dos %d runs)_\n" "$K"
    printf "- **TOOL-ACC:** _(preencher após leitura dos %d runs)_\n" "$K"
    printf "- **STAB:** n/a — aguardar Bateria 2 (sessão separada, mínimo 12h)\n"
    printf "\n"

    printf "## Arquivos de runs\n\n"
    for i in $(seq 1 $K); do
        printf -- "- [\`S1-%s-%s-run%d.txt\`](S1-%s-%s-run%d.txt)\n" \
            "$MODEL_SAFE" "$DATE" "$i" \
            "$MODEL_SAFE" "$DATE" "$i"
    done
    printf "\n"

    printf "## Observações gerais\n\n"
    printf "_(preencher manualmente após revisão de todos os runs)_\n\n"

    printf "## Próximos passos\n\n"
    printf "- [ ] Ler os %d arquivos de run e atribuir notas na tabela acima.\n" "$K"
    printf "- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.\n"
    printf "- [ ] Calcular STAB comparando notas das duas baterias.\n"
    printf "- [ ] Após Bateria 2, executar o mesmo script para o próximo modelo da shortlist.\n"
    printf "      Ordem definida em: \`docs/benchmarks/S1-models-selected.md\`\n"
    printf "\n"

    printf "---\n\n"
    printf "_Gerado automaticamente por \`scripts/run-s1-benchmark.sh\` em %s_\n" "$DATE"
} > "$SUMMARY_FILE"

echo "Summary gerado: ${SUMMARY_FILE}"
echo ""
echo "Próximo passo:"
echo "  1. Leia cada arquivo de run em results/benchmarks/."
echo "  2. Preencha as notas no summary conforme ADR-0001 e evaluation-framework.md seção 4.4."
echo "  3. Execute o script novamente em outra sessão (mín. 12h) para a Bateria 2."
