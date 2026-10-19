#!/usr/bin/env python3
"""
run-s1-benchmark.py

Executa o cenário S1 (Health check estático) com tool use real via API Ollama.
Implementa o fluxo de agente definido em docs/benchmarks/evaluation-framework.md,
seção 4, usando as métricas do ADR-0001.

Uso:
    python3 scripts/run-s1-benchmark.py <modelo>

Exemplo:
    python3 scripts/run-s1-benchmark.py qwen3.5:9b

Requerimentos:
    pip install requests  (stdlib: subprocess, json, sys, os, datetime, time, pathlib)
"""

import sys
import os
import json
import subprocess
import datetime
import time
import requests
from pathlib import Path

# =============================================================================
# CONSTANTES E CONFIGURAÇÕES
# =============================================================================

# DECISÃO: API REST do Ollama em vez de `ollama run` pipe.
# Motivo: /api/chat permite definir tools via JSON schema (tool calling real),
# controlar temperatura de forma precisa e capturar tool_calls estruturados.
# O script bash anterior (run-s1-benchmark.sh) usava pipe sem definição de
# tools — esse script implementa o fluxo de agente completo.
OLLAMA_API_URL = os.environ.get("LOP_SHIM_URL", "http://localhost:11434/api/chat")

# DECISÃO: temperatura 0 em todos os modelos.
# Motivo: maximizar determinismo das respostas para medir CON e STAB com
# menor variação introduzida por amostragem. Conforme constraints-and-priorities.md:
# consistência é a prioridade número 1.
TEMPERATURE = 0

# DECISÃO: K=5 runs por bateria.
# Motivo: mínimo definido em evaluation-framework.md para observar variação
# intra-bateria sem custo excessivo de tempo.
K = 5

# DECISÃO: timeout de 120 segundos por run completo (request + tool + request).
# Motivo: modelos menores (2b–4b) respondem em <30s; modelos maiores (14b)
# podem levar >60s na RTX 3060. 120s é margem segura sem bloquear o script
# indefinidamente em caso de travamento.
TIMEOUT_SECONDS = 300

# DECISÃO: pausa de 30 segundos entre runs.
# Motivo: reduzir risco de reutilização de cache de KV entre runs independentes.
# Conforme plano de experimento S1.
SLEEP_BETWEEN_RUNS = 30

# DECISÃO: diretório de resultados relativo à raiz do repositório.
# O script verifica que está na raiz antes de criar arquivos.
RESULTS_DIR = Path("results/benchmarks")

# =============================================================================
# DEFINIÇÃO DA TOOL run_bash
# DECISÃO: apenas uma tool disponível para o modelo em S1.
# Motivo: S1 é nível 1 de complexidade (evaluation-framework.md seção 2).
# Múltiplas tools introduziriam ruído na análise de TOOL-CON e TOOL-ACC.
# A tool executa comandos no HOST (não no container) via subprocess.
# =============================================================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": (
                "Executa um comando bash no servidor local e retorna o stdout exato. "
                "Use esta tool para executar scripts e comandos no host."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "O comando bash a executar no host."
                    }
                },
                "required": ["command"]
            }
        }
    }
]

# =============================================================================
# PROMPT DO CENÁRIO S1
# DECISÃO: texto fixo, nunca alterado entre runs nem entre baterias.
# Fonte: docs/benchmarks/evaluation-framework.md, seção 4.2.
# Qualquer alteração no prompt invalida a comparação de CON e STAB.
# A formatação markdown (**negrito**) foi removida — o modelo recebe
# texto plano via API; asteriscos seriam interpretados como conteúdo.
# =============================================================================
S1_PROMPT = (
    "Execute o script ~/scripts/health.sh e encaminhe a saída exata, "
    "sem alterar nada, sem resumo, sem comentários. "
    "Se não conseguir executar, responda apenas: "
    "ERRO: não consegui executar health.sh"
)

# NOME DAS TOOLS VÁLIDAS para detecção de tool inventada
VALID_TOOL_NAMES = {"run_bash"}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def check_repo_root() -> None:
    """
    Verifica que o script está sendo executado da raiz do repositório.
    DECISÃO: marcador é docs/benchmarks/evaluation-framework.md.
    Evita salvar resultados em diretório errado.
    """
    if not Path("docs/benchmarks/evaluation-framework.md").exists():
        print("ERRO: execute este script a partir da raiz do repositório llms-on-prem.")
        print("      python3 scripts/run-s1-benchmark.py <modelo>")
        sys.exit(1)


def sanitize_model_name(model: str) -> str:
    """
    Converte nome do modelo para uso seguro em caminhos de arquivo.
    DECISÃO: substituir ':' por '-', pois ':' é inválido em nomes de arquivo
    em vários sistemas e causa problemas com path expansion.
    Exemplo: qwen3.5:9b -> qwen3.5-9b
    """
    return model.replace(":", "-").replace("/", "_")


def execute_bash(command: str) -> tuple[str, bool]:
    """
    Executa um comando bash no host via subprocess e retorna (stdout, sucesso).

    DECISÃO: usar ['bash', '-c', command] (lista) em vez de shell=True com string.
    Motivo: com shell=True e uma string, o shell interpreta metacaracteres do
    comando — se o modelo gerar um comando malformado, pode causar comportamento
    inesperado. Com lista e bash -c, o comando é passado literalmente ao bash
    sem expansão adicional pelo Python.

    DECISÃO: expandir '~' explicitamente com os.path.expanduser antes de passar
    ao bash, garantindo que o path seja resolvido mesmo em ambientes onde o
    shell de destino não expande ~ corretamente.

    AVISO: este script executa comandos gerados pelo modelo no host.
    É uma ferramenta de pesquisa controlada — não usar em produção.
    """
    expanded = os.path.expanduser(command)
    try:
        result = subprocess.run(
            ["bash", "-c", expanded],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS
        )
        stdout = result.stdout
        if result.returncode != 0 and not stdout:
            stdout = f"[ERRO returncode={result.returncode}] {result.stderr.strip()}"
        return stdout, result.returncode == 0
    except subprocess.TimeoutExpired:
        return f"[ERRO] Timeout após {TIMEOUT_SECONDS}s na execução do comando.", False
    except Exception as e:
        return f"[ERRO] subprocess falhou: {e}", False


def call_ollama_chat(
    model: str,
    messages: list,
    tools: list,
    temperature: int = 0
) -> dict:
    """
    Chama POST /api/chat da API Ollama com tool use.

    DECISÃO: stream=false para capturar a resposta completa de uma vez.
    Com stream=true, a resposta vem em chunks e o parser de tool_calls
    precisaria ser implementado — complexidade desnecessária nesta fase.

    DECISÃO: timeout é passado como parâmetro de requests, não como opção
    do modelo. O timeout do modelo (num_predict) não limita o tempo de
    resposta da API — o timeout de requests sim.

    Retorna o dict completo da resposta ou lança RuntimeError em caso de falha.
    """
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature
        }
    }

    try:
        resp = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Timeout ({TIMEOUT_SECONDS}s) na chamada à API Ollama.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Não foi possível conectar à API Ollama em " + OLLAMA_API_URL)
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Erro HTTP da API Ollama: {e} — body: {resp.text[:300]}")


def extract_tool_calls(api_response: dict) -> list:
    """
    Extrai tool_calls da resposta da API Ollama.

    DECISÃO: tratar 'arguments' como dict ou string (ambos ocorrem dependendo
    da versão do Ollama e do modelo). Se vier como string JSON, deserializar.
    Isso evita KeyError silencioso em diferentes versões do Ollama.
    """
    message = api_response.get("message", {})
    raw_calls = message.get("tool_calls", [])
    calls = []
    for tc in raw_calls:
        fn = tc.get("function", {})
        name = fn.get("name", "")
        args = fn.get("arguments", {})
        # Normalizar arguments para dict
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"_raw": args}
        calls.append({"name": name, "arguments": args})
    return calls


# =============================================================================
# FUNÇÕES DE PERFORMANCE
# Capturam os campos retornados pela API Ollama com stream=false.
# Fonte dos campos: prompt_eval_count, prompt_eval_duration, eval_count,
# eval_duration, total_duration (nanosegundos), message.thinking (opcional).
# DECISÃO: funções separadas da lógica de agente para não misturar
# responsabilidades e facilitar manutenção independente.
# =============================================================================

def extract_perf(api_response: dict) -> dict:
    """
    Extrai métricas de performance de uma resposta da API Ollama.

    DECISÃO: retorna None para cada campo ausente em vez de lançar exceção.
    Motivo: modelos antigos ou erros parciais podem omitir alguns campos —
    o script não deve quebrar por ausência de dado de performance.

    DECISÃO: thinking_chars mede len() do campo message.thinking, se presente.
    Modelos com raciocínio interno (ex.: deepseek-r1, qwen3-thinking) emitem
    esse campo separado do content final. Capturá-lo revela se o modelo
    gastou tokens de reasoning e quantos caracteres produziu internamente.
    """
    tokens_input      = api_response.get("prompt_eval_count")
    tokens_output     = api_response.get("eval_count")
    eval_duration_ns  = api_response.get("eval_duration")
    total_duration_ns = api_response.get("total_duration")

    # Calcular tokens_total apenas se ambos os campos estão presentes
    tokens_total = (
        tokens_input + tokens_output
        if tokens_input is not None and tokens_output is not None
        else None
    )

    # Converter nanosegundos → milissegundos (arredondado a 1 decimal)
    duracao_ms = (
        round(total_duration_ns / 1_000_000, 1)
        if total_duration_ns is not None
        else None
    )

    # Tokens por segundo: eval_count / (eval_duration em segundos)
    # DECISÃO: usar eval_duration (tempo de geração) e não total_duration,
    # pois total inclui tempo de carregamento do prompt — distorceria tok/s.
    tokens_por_segundo = (
        round(tokens_output / (eval_duration_ns / 1_000_000_000), 1)
        if tokens_output is not None
        and eval_duration_ns is not None
        and eval_duration_ns > 0
        else None
    )

    # thinking chars: presente em modelos com raciocínio interno
    thinking = api_response.get("message", {}).get("thinking", "") or ""
    thinking_chars = len(thinking)

    return {
        "tokens_input":       tokens_input,
        "tokens_output":      tokens_output,
        "tokens_total":       tokens_total,
        "duracao_ms":         duracao_ms,
        "tokens_por_segundo": tokens_por_segundo,
        "thinking_chars":     thinking_chars,
    }


def combine_perf(p1: dict, p2: dict) -> dict:
    """
    Agrega métricas de performance de dois turnos de API.

    DECISÃO: tratar None como 0 nas somas parciais para que um turno
    ausente (p2={}) não anule os dados do turno existente (p1).
    Exemplo: se turno 2 não ocorreu, total_tokens = tokens do turno 1.

    DECISÃO: média ponderada de tok/s por tokens_output de cada turno.
    Média simples seria imprecisa — um turno com 5 tokens e outro com
    500 tokens não deveriam ter o mesmo peso.
    """
    def safe_sum(a, b):
        if a is None and b is None:
            return None
        return (a or 0) + (b or 0)

    t1_tps = p1.get("tokens_por_segundo")
    t1_out = p1.get("tokens_output") or 0
    t2_tps = p2.get("tokens_por_segundo")
    t2_out = p2.get("tokens_output") or 0
    total_out = t1_out + t2_out

    if total_out > 0 and (t1_tps is not None or t2_tps is not None):
        weighted = ((t1_tps or 0) * t1_out) + ((t2_tps or 0) * t2_out)
        media_tps = round(weighted / total_out, 1)
    else:
        media_tps = None

    return {
        "total_tokens_input":       safe_sum(p1.get("tokens_input"),   p2.get("tokens_input")),
        "total_tokens_output":      safe_sum(p1.get("tokens_output"),  p2.get("tokens_output")),
        "total_tokens":             safe_sum(p1.get("tokens_total"),   p2.get("tokens_total")),
        "total_duracao_ms":         safe_sum(p1.get("duracao_ms"),     p2.get("duracao_ms")),
        "media_tokens_por_segundo": media_tps,
    }


def _fmt_perf(val, spec: str = "") -> str:
    """
    Formata um valor de performance para exibição.
    DECISÃO: retornar 'N/A' para None — nunca quebrar por campo ausente.
    """
    if val is None:
        return "N/A"
    if spec:
        return f"{val:{spec}}"
    return str(val)


def run_single_s1(model: str, run_number: int) -> dict:
    """
    Executa um único run do cenário S1 e retorna um dict com todos os dados.

    Fluxo do agente:
      1. Enviar prompt S1 com tool run_bash disponível.
      2. Se o modelo chamar run_bash: executar o comando no host.
      3. Devolver o resultado ao modelo.
      4. Capturar a resposta final.

    Se o modelo não chamar nenhuma tool, registrar tool="NENHUMA".
    Se o modelo chamar uma tool inexistente, registrar o nome e marcar como inválida.

    DECISÃO: máximo de 1 turno de tool calling por run.
    Motivo: S1 é nível 1 — a tarefa requer exatamente 1 chamada de tool.
    Múltiplos turnos indicariam comportamento inesperado (anotado nas observações).
    """
    ts_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    messages = [
        {"role": "user", "content": S1_PROMPT}
    ]

    result = {
        "run": run_number,
        "timestamp": ts_start,
        "model": model,
        "tool_called": "NENHUMA",
        "tool_argument": "",
        "tool_valid": None,       # True=tool existe, False=tool inventada, None=nenhuma
        "tool_stdout": "",
        "tool_success": None,
        "final_response": "",
        "error": None,
        "extra_tool_calls": 0,   # número de tool calls além do primeiro (anomalia)
        # ADIÇÃO: dicts de performance por turno e agregado.
        # Inicializados como {} para que save_run_file sempre encontre as chaves,
        # mesmo em caso de erro antes da extração.
        "perf_t1":    {},  # turno 1: prompt → tool call
        "perf_t2":    {},  # turno 2: tool result → resposta final
        "perf_total": {},  # agregado dos dois turnos
    }

    try:
        # TURNO 1: enviar prompt com tools disponíveis
        resp1 = call_ollama_chat(model, messages, TOOLS, temperature=TEMPERATURE)
        assistant_msg = resp1.get("message", {})
        tool_calls = extract_tool_calls(resp1)

        # ADIÇÃO: extrair métricas de performance do turno 1.
        # Feito antes do early return para capturar perf mesmo sem tool call.
        result["perf_t1"] = extract_perf(resp1)

        if not tool_calls:
            # Modelo não chamou nenhuma tool — capturar resposta direta
            result["final_response"] = assistant_msg.get("content", "")
            # ADIÇÃO: turno 2 não ocorreu; perf_total reflete apenas turno 1.
            result["perf_t2"] = {}
            result["perf_total"] = combine_perf(result["perf_t1"], {})
            return result

        # Processar apenas o primeiro tool call
        # (S1 requer exatamente 1; extras são registrados como anomalia)
        result["extra_tool_calls"] = max(0, len(tool_calls) - 1)
        tc = tool_calls[0]
        tool_name = tc["name"]
        tool_args = tc["arguments"]

        result["tool_called"] = tool_name

        if tool_name in VALID_TOOL_NAMES:
            result["tool_valid"] = True
            command = tool_args.get("command", "")
            result["tool_argument"] = command
            stdout, success = execute_bash(command)
            result["tool_stdout"] = stdout
            result["tool_success"] = success
        else:
            # DECISÃO: se tool inventada, registrar o nome, não executar e
            # devolver mensagem de erro como conteúdo da tool response.
            result["tool_valid"] = False
            result["tool_argument"] = json.dumps(tool_args)
            result["tool_stdout"] = f"ERRO: tool '{tool_name}' não existe no ambiente."
            result["tool_success"] = False
            stdout = result["tool_stdout"]

        # Montar mensagem do assistente com tool_calls para o histórico
        # DECISÃO: incluir tool_calls no dict da mensagem do assistente
        # conforme formato esperado pela maioria das versões do Ollama.
        messages.append({
            "role": "assistant",
            "content": assistant_msg.get("content", ""),
            "tool_calls": resp1["message"].get("tool_calls", [])
        })

        # Adicionar resultado da tool ao histórico
        # DECISÃO: incluir campo 'name' além de 'role' e 'content'.
        # Algumas versões do Ollama exigem 'name' para correlacionar a tool call.
        messages.append({
            "role": "tool",
            "name": tool_name,
            "content": result["tool_stdout"]
        })

        # TURNO 2: obter resposta final do modelo após execução da tool
        resp2 = call_ollama_chat(model, messages, TOOLS, temperature=TEMPERATURE)
        result["final_response"] = resp2.get("message", {}).get("content", "")

        # ADIÇÃO: extrair métricas de performance do turno 2 e calcular total.
        result["perf_t2"]    = extract_perf(resp2)
        result["perf_total"] = combine_perf(result["perf_t1"], result["perf_t2"])

    except RuntimeError as e:
        result["error"] = str(e)
        result["final_response"] = f"[ERRO DE API] {e}"

    return result


def save_run_file(run_data: dict, model_safe: str, date_str: str) -> Path:
    """
    Salva o resultado de um único run em arquivo texto estruturado.

    DECISÃO: arquivo por run (não um único arquivo acumulado).
    Motivo: facilita leitura individual de cada run pelo avaliador e evita
    que um run corrompido invalide os outros.
    """
    filepath = RESULTS_DIR / f"S1-{model_safe}-{date_str}-run{run_data['run']}.txt"

    lines = [
        f"# S1 — Run {run_data['run']}",
        f"# Modelo         : {run_data['model']}",
        f"# Timestamp      : {run_data['timestamp']}",
        f"# Temperatura    : {TEMPERATURE}",
        f"# API            : {OLLAMA_API_URL}",
        f"# Prompt fonte   : evaluation-framework.md seção 4.2",
        "#" + "-" * 60,
        "",
        "## PROMPT ENVIADO",
        "",
        S1_PROMPT,
        "",
        "## TOOL CHAMADA PELO MODELO",
        "",
        f"Nome      : {run_data['tool_called']}",
        f"Argumento : {run_data['tool_argument']}",
        f"Tool válida: {run_data['tool_valid']}",
        f"Execução OK: {run_data['tool_success']}",
        f"Extra tool calls (anomalia): {run_data['extra_tool_calls']}",
        "",
        "## STDOUT RETORNADO PELA EXECUÇÃO",
        "",
        run_data["tool_stdout"] if run_data["tool_stdout"] else "(nenhum)",
        "",
        "## RESPOSTA FINAL DO MODELO",
        "",
        run_data["final_response"] if run_data["final_response"] else "(vazia)",
        "",
    ]

    # ADIÇÃO: seção ## PERFORMANCE ao final do arquivo de run.
    # DECISÃO: inserida após ## RESPOSTA FINAL e antes de ## ERRO DE EXECUÇÃO
    # para manter a ordem lógica: contexto → tool → resultado → performance → erros.
    # _fmt_perf retorna 'N/A' para campos ausentes — nunca quebra por API antiga.
    p1 = run_data.get("perf_t1", {})
    p2 = run_data.get("perf_t2", {})
    pt = run_data.get("perf_total", {})

    def _fmts(val, spec=""):
        return _fmt_perf(val, spec)

    t2_label = "Turno 2 (tool result → resposta final)"
    t2_block = [
        f"### {t2_label}",
        f"  tokens input   : {_fmts(p2.get('tokens_input'))}",
        f"  tokens output  : {_fmts(p2.get('tokens_output'))}",
        f"  duração        : {_fmts(p2.get('duracao_ms'))} ms",
        f"  velocidade     : {_fmts(p2.get('tokens_por_segundo'), '.1f')} tok/s",
        f"  thinking chars : {_fmts(p2.get('thinking_chars'))}",
    ] if p2 else [f"### {t2_label}", "  (turno não ocorreu — modelo não chamou tool)"]

    lines += [
        "## PERFORMANCE",
        "",
        "### Turno 1 (prompt → tool call)",
        f"  tokens input   : {_fmts(p1.get('tokens_input'))}",
        f"  tokens output  : {_fmts(p1.get('tokens_output'))}",
        f"  duração        : {_fmts(p1.get('duracao_ms'))} ms",
        f"  velocidade     : {_fmts(p1.get('tokens_por_segundo'), '.1f')} tok/s",
        f"  thinking chars : {_fmts(p1.get('thinking_chars'))}",
        "",
        *t2_block,
        "",
        "### Total do run",
        f"  tokens total   : {_fmts(pt.get('total_tokens'))}",
        f"  duração total  : {_fmts(pt.get('total_duracao_ms'))} ms",
        f"  velocidade avg : {_fmts(pt.get('media_tokens_por_segundo'), '.1f')} tok/s",
        "",
    ]

    if run_data["error"]:
        lines += ["## ERRO DE EXECUÇÃO", "", run_data["error"], ""]

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def save_summary(all_runs: list, model: str, model_safe: str, date_str: str) -> Path:
    """
    Gera o arquivo summary com tabela vazia para preenchimento manual das notas.

    DECISÃO: notas CON/TOOL-CON/INST/TOOL-ACC ficam em branco.
    O script preenche automaticamente apenas TOOL-ACC=0 nos casos em que
    nenhuma tool foi chamada ou a tool foi inventada — isso é um fato observável
    sem julgamento subjetivo (ADR-0001: "taxa de chamadas de tool que usam
    uma tool existente").

    Para as demais dimensões, o avaliador aplica os critérios do ADR-0001
    após leitura de cada run.
    """
    filepath = RESULTS_DIR / f"S1-{model_safe}-{date_str}-summary.md"

    lines = [
        f"# S1 Summary — {model} — {date_str}",
        "",
        "## Metadados",
        "",
        f"| Campo                   | Valor                              |",
        f"|-------------------------|------------------------------------|",
        f"| Cenário                 | S1 – Health check estático         |",
        f"| Modelo                  | {model}                            |",
        f"| Bateria                 | 1                                  |",
        f"| Data                    | {date_str}                         |",
        f"| K (runs)                | {K}                                |",
        f"| Temperatura             | {TEMPERATURE}                      |",
        f"| API                     | {OLLAMA_API_URL}/api/chat          |",
        f"| Tool disponível         | run_bash                           |",
        f"| Execução real no host   | sim (subprocess)                   |",
        f"| VRAM disponível início  | _(preencher manualmente)_          |",
        "",
        "## Resultados",
        "",
        "Preencher CON, TOOL-CON, INST com notas 0–4 após leitura dos runs.",
        "TOOL-ACC=0 já marcado onde nenhuma tool válida foi chamada.",
        "Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`",
        "           `docs/benchmarks/evaluation-framework.md`, seção 4.4",
        "",
        # ADIÇÃO: colunas tok_total, ms_total, tok/s e thinking após TOOL-ACC.
        # Preenchidas automaticamente com dados de perf_total de cada run.
        "| Run | Tool chamada | Argumento | CON | TOOL-CON | INST | TOOL-ACC | tok_total | ms_total | tok/s | thinking | Obs |",
        "|-----|-------------|-----------|-----|----------|------|----------|-----------|----------|-------|----------|-----|",
    ]

    for r in all_runs:
        # TOOL-ACC: atribuir 0 automaticamente se tool inválida ou ausente.
        # Isso é um fato observável (tool inexistente = TOOL-ACC mínimo).
        if r["tool_valid"] is False or r["tool_called"] == "NENHUMA":
            tool_acc = "0"
        else:
            tool_acc = ""  # avaliador preenche

        tool_arg_short = r["tool_argument"][:40] + "…" if len(r["tool_argument"]) > 40 else r["tool_argument"]

        # ADIÇÃO: extrair métricas de performance para a linha da tabela.
        pt = r.get("perf_total", {})
        p1 = r.get("perf_t1", {})
        p2 = r.get("perf_t2", {})
        tok_total = _fmt_perf(pt.get("total_tokens"))
        ms_total  = _fmt_perf(pt.get("total_duracao_ms"))
        tps       = _fmt_perf(pt.get("media_tokens_por_segundo"), ".1f")
        th_chars  = (p1.get("thinking_chars") or 0) + (p2.get("thinking_chars") or 0)
        thinking  = str(th_chars) if th_chars else "0"

        lines.append(
            f"| {r['run']} | {r['tool_called']} | `{tool_arg_short}` "
            f"|     |          |      | {tool_acc:<8} | {tok_total:<9} | {ms_total:<8} | {tps:<5} | {thinking:<8} |     |"
        )

    lines += [
        "",
        "## Notas por dimensão (Bateria 1)",
        "",
        f"- **CON:** _(preencher após leitura dos {K} runs)_",
        f"- **TOOL-CON:** _(preencher após leitura dos {K} runs)_",
        f"- **INST:** _(preencher após leitura dos {K} runs)_",
        f"- **TOOL-ACC:** _(preencher após leitura dos {K} runs)_",
        "- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)",
        "",
        "## Observações brutas (geradas automaticamente)",
        "",
        "| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls |",
        "|-----|-------------|-------------------|-------------|---------|-------------|",
    ]

    for r in all_runs:
        arg = r["tool_argument"].replace("|", "\\|")
        lines.append(
            f"| {r['run']} | {r['tool_called']} | `{arg}` "
            f"| {r['tool_valid']} | {r['tool_success']} | {r['extra_tool_calls']} |"
        )

    lines += [
        "",
        "## Arquivos de runs",
        "",
    ]
    for r in all_runs:
        fn = f"S1-{model_safe}-{date_str}-run{r['run']}.txt"
        lines.append(f"- [`{fn}`]({fn})")

    lines += [
        "",
        "## Próximos passos",
        "",
        f"- [ ] Ler os {K} arquivos de run e atribuir notas na tabela acima.",
        "- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.",
        "- [ ] Calcular STAB comparando notas das duas baterias.",
        "- [ ] Avançar para o próximo modelo da shortlist:",
        "      `docs/benchmarks/S1-models-selected.md`",
        "",
        "---",
        "",
        f"_Gerado automaticamente por `scripts/run-s1-benchmark.py` em {date_str}_",
    ]

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    check_repo_root()

    if len(sys.argv) < 2:
        print("ERRO: informe o nome do modelo.")
        print("Uso: python3 scripts/run-s1-benchmark.py <modelo>")
        print("Exemplo: python3 scripts/run-s1-benchmark.py qwen3.5:9b")
        sys.exit(1)

    model = sys.argv[1]
    model_safe = sanitize_model_name(model)
    date_str = datetime.date.today().isoformat()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"  S1 Benchmark — Tool use real via API Ollama")
    print(f"  Modelo  : {model}")
    print(f"  Data    : {date_str}")
    print(f"  K runs  : {K}")
    print(f"  Temp    : {TEMPERATURE}")
    print(f"  Timeout : {TIMEOUT_SECONDS}s")
    print(f"  API     : {OLLAMA_API_URL}")
    print("=" * 60)
    print()

    all_runs = []

    for i in range(1, K + 1):
        print(f"[Run {i}/{K}] iniciando...")
        run_data = run_single_s1(model, i)
        all_runs.append(run_data)

        filepath = save_run_file(run_data, model_safe, date_str)

        status = "OK" if run_data["error"] is None else "ERRO"
        print(f"  -> tool chamada : {run_data['tool_called']}")
        print(f"  -> tool válida  : {run_data['tool_valid']}")
        print(f"  -> status       : {status}")
        print(f"  -> salvo em     : {filepath}")

        # ADIÇÃO: exibir métricas de performance por run no terminal.
        # DECISÃO: mostrar os 4 campos pedidos na spec: tok/s, tokens, ms, thinking.
        # thinking exibe "sim (N chars)" se > 0, "não" caso contrário —
        # mais informativo do que um booleano para identificar modelos com reasoning.
        pt = run_data.get("perf_total", {})
        p1 = run_data.get("perf_t1", {})
        p2 = run_data.get("perf_t2", {})
        th = (p1.get("thinking_chars") or 0) + (p2.get("thinking_chars") or 0)
        thinking_str = f"sim ({th} chars)" if th > 0 else "não"
        print(f"  -> tokens/s     : {_fmt_perf(pt.get('media_tokens_por_segundo'), '.1f')} tok/s")
        print(f"  -> tokens total : {_fmt_perf(pt.get('total_tokens'))}")
        print(f"  -> duração      : {_fmt_perf(pt.get('total_duracao_ms'))} ms")
        print(f"  -> thinking     : {thinking_str}")
        print()

        if i < K:
            print(f"  aguardando {SLEEP_BETWEEN_RUNS}s...")
            time.sleep(SLEEP_BETWEEN_RUNS)
            print()

    print("=" * 60)
    print(f"  {K} runs concluídos.")
    print("=" * 60)
    print()

    summary_path = save_summary(all_runs, model, model_safe, date_str)
    print(f"Summary gerado : {summary_path}")
    print()
    print("Próximos passos:")
    print(f"  1. Leia os arquivos de run em {RESULTS_DIR}/")
    print("  2. Preencha as notas no summary conforme ADR-0001 seção 4.4.")
    print("  3. Execute novamente após 12h para a Bateria 2 (STAB).")


if __name__ == "__main__":
    main()
