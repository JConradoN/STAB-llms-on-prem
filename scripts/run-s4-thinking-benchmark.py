#!/usr/bin/env python3
"""
run-s4-thinking-benchmark.py

Variante de run-s4-benchmark.py com thinking habilitado ("think": True).

Objetivo: comparar o comportamento do modelo quando o thinking está ativo,
especialmente em S4-B (desempate entre 3 logs críticos), onde o modelo base
(think=False) falhou por exaurir MAX_TOOL_TURNS.

Diferenças em relação a run-s4-benchmark.py:
  - "think": True no payload da API Ollama
  - Prefixo de saída: S4think- (para não sobrescrever resultados originais)
  - TIMEOUT_SECONDS elevado para 600s (thinking aumenta latência)

Uso:
    python3 scripts/run-s4-thinking-benchmark.py <modelo>

Exemplo:
    python3 scripts/run-s4-thinking-benchmark.py gemma4:26b-a4b-it-q4_K_M

Requerimentos:
    pip install requests  (stdlib: json, re, sys, os, datetime, pathlib)
"""

import sys
import os
import json
import datetime
import requests
from pathlib import Path

# =============================================================================
# CONSTANTES E CONFIGURAÇÕES
# =============================================================================

OLLAMA_API_URL   = os.environ.get("LOP_SHIM_URL", "http://localhost:11434/api/chat")
TEMPERATURE      = 0
TIMEOUT_SECONDS  = 600  # thinking aumenta latência
RESULTS_DIR      = Path("results/benchmarks")
FIXTURES_DIR_S4  = Path("fixtures/triage-s4")
FIXTURES_DIR_LOG = Path("fixtures/health-logs")

MAX_TOOL_TURNS   = 4  # 3 read_file + 1 turno de resposta final

CASES = [
    "S4-A",
    "S4-B",
    "S4-C",
]
K = len(CASES)

# =============================================================================
# DEFINIÇÃO DA TOOL read_file
# Idêntica ao S3 — sem alteração.
# =============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lê um arquivo local e retorna seu conteúdo como string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho absoluto do arquivo a ser lido."
                    }
                },
                "required": ["path"]
            }
        }
    }
]

VALID_TOOL_NAMES = {"read_file"}

# =============================================================================
# PROMPT DO CENÁRIO S4
# {triage_id}, {log_path_1}, {log_path_2}, {log_path_3} são substituídos
# por .replace() para evitar conflito com as chaves JSON do schema.
# =============================================================================

S4_PROMPT_TEMPLATE = """\
Você é um agente de triagem de infraestrutura. Analise os 3 arquivos de log a seguir.

Arquivos para análise:
1. {log_path_1}
2. {log_path_2}
3. {log_path_3}

Use a tool read_file para ler cada arquivo. Em seguida:
- Classifique a severidade de cada host (info/warning/critical)
  - critical: qualquer linha com level=CRITICAL
  - warning: nenhuma CRITICAL, mas pelo menos uma WARNING
  - info: todas as linhas são INFO
- Ordene os 3 hosts por prioridade: critical > warning > info
  (em empate de severidade, priorize pelo primary_issue mais grave)
- Gere o JSON de triagem com o schema abaixo.

Identificadores snake_case válidos para primary_issue e secondary_issues:
  none, high_cpu_usage, elevated_application_latency, database_unavailable,
  disk_critical_on_var, postgresql_service_failed, redis_service_failed,
  backup_volume_high_usage, session_api_error_rate_elevated

Schema de saída:
{{
  "triage_id": "{triage_id}",
  "hosts_analisados": 3,
  "timestamp_triage": "<ISO 8601 com Z do log mais recente entre os 3>",
  "prioridade": [
    {{
      "rank": 1,
      "host": "<hostname>",
      "case_id": "<nome do arquivo sem extensão>",
      "severity": "<info|warning|critical>",
      "primary_issue": "<snake_case>",
      "escalation": "<immediate|monitor|none>",
      "summary": "<1 frase em PT-BR>"
    }},
    {{"rank": 2, "...": "..."}},
    {{"rank": 3, "...": "..."}}
  ],
  "acao_geral": "<frase curta em PT-BR>"
}}

Regras de escalation: critical → immediate | warning → monitor | info → none

Responda APENAS com o JSON. Sem markdown. Sem texto adicional."""


def build_s4_prompt(triage_id: str, log_paths: list) -> str:
    """Substitui os placeholders no template pelo triage_id e 3 caminhos absolutos."""
    prompt = S4_PROMPT_TEMPLATE
    prompt = prompt.replace("{triage_id}", triage_id)
    prompt = prompt.replace("{log_path_1}", str(log_paths[0]))
    prompt = prompt.replace("{log_path_2}", str(log_paths[1]))
    prompt = prompt.replace("{log_path_3}", str(log_paths[2]))
    return prompt


# =============================================================================
# FUNÇÕES COPIADAS DE run-s3-benchmark.py SEM ALTERAÇÃO
# =============================================================================

def sanitize_model_name(model: str) -> str:
    return model.replace(":", "-").replace("/", "_")


def call_ollama_chat(model: str, messages: list, tools: list, temperature: int = 0) -> dict:
    payload = {
        "model":    model,
        "messages": messages,
        "tools":    tools,
        "stream":   False,
        "think":    True,
        "options":  {"temperature": temperature}
    }
    try:
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Timeout ({TIMEOUT_SECONDS}s) na chamada à API Ollama.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Não foi possível conectar à API Ollama em " + OLLAMA_API_URL)
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Erro HTTP da API Ollama: {e} — body: {resp.text[:300]}")


def extract_tool_calls(api_response: dict) -> list:
    message   = api_response.get("message", {})
    raw_calls = message.get("tool_calls", [])
    calls     = []
    for tc in raw_calls:
        fn   = tc.get("function", {})
        name = fn.get("name", "")
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"_raw": args}
        calls.append({"name": name, "arguments": args})
    return calls


def extract_perf(api_response: dict) -> dict:
    tokens_input      = api_response.get("prompt_eval_count")
    tokens_output     = api_response.get("eval_count")
    eval_duration_ns  = api_response.get("eval_duration")
    total_duration_ns = api_response.get("total_duration")

    tokens_total = (
        tokens_input + tokens_output
        if tokens_input is not None and tokens_output is not None
        else None
    )
    duracao_ms = (
        round(total_duration_ns / 1_000_000, 1)
        if total_duration_ns is not None else None
    )
    tokens_por_segundo = (
        round(tokens_output / (eval_duration_ns / 1_000_000_000), 1)
        if tokens_output is not None
        and eval_duration_ns is not None
        and eval_duration_ns > 0
        else None
    )
    thinking       = api_response.get("message", {}).get("thinking", "") or ""
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
    def safe_sum(a, b):
        if a is None and b is None:
            return None
        return (a or 0) + (b or 0)

    t1_tps    = p1.get("tokens_por_segundo")
    t1_out    = p1.get("tokens_output") or 0
    t2_tps    = p2.get("tokens_por_segundo")
    t2_out    = p2.get("tokens_output") or 0
    total_out = t1_out + t2_out

    if total_out > 0 and (t1_tps is not None or t2_tps is not None):
        weighted  = ((t1_tps or 0) * t1_out) + ((t2_tps or 0) * t2_out)
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
    if val is None:
        return "N/A"
    if spec:
        return f"{val:{spec}}"
    return str(val)


# =============================================================================
# FUNÇÕES ESPECÍFICAS DO S4
# =============================================================================

def check_repo_root() -> None:
    if not Path("docs/benchmarks/S4-triage-multi-log.md").exists():
        print("ERRO: execute este script a partir da raiz do repositório llms-on-prem.")
        print("      python3 scripts/run-s4-benchmark.py <modelo>")
        sys.exit(1)
    if not FIXTURES_DIR_S4.exists():
        print(f"ERRO: diretório de fixtures não encontrado: {FIXTURES_DIR_S4}")
        sys.exit(1)


def load_expected_s4(triage_id: str) -> dict:
    path = FIXTURES_DIR_S4 / f"{triage_id}.expected.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERRO ao carregar expected.json de {path}: {e}")
        sys.exit(1)


def resolve_log_paths(expected: dict) -> list:
    """
    Retorna lista de 3 caminhos absolutos na ordem definida em expected['cases'].
    log_files mapeia case_id → path relativo à raiz do repo.
    """
    log_files = expected.get("log_files", {})
    paths = []
    for case_id in expected.get("cases", []):
        rel = log_files.get(case_id, "")
        paths.append(Path(rel).resolve())
    return paths


def read_file_tool(path: str) -> tuple:
    """
    Implementação da tool read_file.
    Retorna (conteúdo, sucesso). Sem subprocess — leitura direta via Python.
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
        return content, True
    except Exception as e:
        return f"ERRO ao ler arquivo '{path}': {e}", False


def combine_perf_list(perf_list: list) -> dict:
    """Combina uma lista de dicts de perf (acumula tokens e duração, média ponderada de tok/s)."""
    total_input  = 0
    total_output = 0
    total_tokens = 0
    total_ms     = 0.0
    weighted_tps = 0.0

    for p in perf_list:
        total_input  += p.get("tokens_input")  or 0
        total_output += p.get("tokens_output") or 0
        total_tokens += p.get("tokens_total")  or 0
        total_ms     += p.get("duracao_ms")    or 0.0
        out  = p.get("tokens_output") or 0
        tps  = p.get("tokens_por_segundo") or 0.0
        weighted_tps += tps * out

    media_tps = round(weighted_tps / total_output, 1) if total_output > 0 else None

    return {
        "total_tokens_input":       total_input  or None,
        "total_tokens_output":      total_output or None,
        "total_tokens":             total_tokens or None,
        "total_duracao_ms":         round(total_ms, 1) if total_ms else None,
        "media_tokens_por_segundo": media_tps,
    }


def validate_s4_response(response_text: str, expected: dict) -> dict:
    """
    Valida a resposta final do modelo para o cenário S4.

    Retorna dict com:
      schema_valid        : bool — JSON válido sem markdown, campos obrigatórios presentes
      all_hosts_present   : bool — os 3 hosts esperados aparecem no JSON
      rank_order_correct  : bool — sequência de hosts bate com prioridade_expected
      escalation_correct  : bool — escalation de cada host bate com severity esperada
      acao_geral_present  : bool — campo acao_geral existe com len >= 10
      triage_acc_auto     : int  — 0|1|2|3|4
    """
    stripped   = response_text.strip() if response_text else ""
    schema_valid = False
    data = None

    start = stripped.find("{")
    if start != -1:
        try:
            decoder = json.JSONDecoder()
            data, _ = decoder.raw_decode(stripped, start)
            schema_valid = isinstance(data, dict)
        except json.JSONDecodeError:
            schema_valid = False

    if not schema_valid or data is None:
        return {
            "schema_valid":       False,
            "all_hosts_present":  False,
            "rank_order_correct": False,
            "escalation_correct": False,
            "acao_geral_present": False,
            "triage_acc_auto":    0,
        }

    prioridade = data.get("prioridade") or []
    hosts_in_response = [item.get("host", "") for item in prioridade]
    hosts_expected    = expected.get("hosts_expected", [])

    all_hosts_present = set(hosts_expected) == set(hosts_in_response)
    rank_order_correct = hosts_in_response == hosts_expected

    # Mapa de severity esperada por host
    sev_map = {
        item["host"]: item["severity"]
        for item in expected.get("prioridade_expected", [])
    }
    esc_map = {"critical": "immediate", "warning": "monitor", "info": "none"}

    escalation_correct = True
    for item in prioridade:
        host      = item.get("host", "")
        esc_resp  = item.get("escalation", "")
        sev_exp   = sev_map.get(host)
        if sev_exp is None:
            continue
        if esc_map.get(sev_exp) != esc_resp:
            escalation_correct = False
            break

    acao_geral = data.get("acao_geral") or ""
    acao_geral_present = isinstance(acao_geral, str) and len(acao_geral) >= 10

    # TRIAGE-ACC
    if rank_order_correct and escalation_correct and all_hosts_present:
        triage_acc_auto = 4
    elif escalation_correct and all_hosts_present:
        triage_acc_auto = 3
    elif all_hosts_present:
        triage_acc_auto = 2
    elif schema_valid:
        triage_acc_auto = 1
    else:
        triage_acc_auto = 0

    return {
        "schema_valid":       schema_valid,
        "all_hosts_present":  all_hosts_present,
        "rank_order_correct": rank_order_correct,
        "escalation_correct": escalation_correct,
        "acao_geral_present": acao_geral_present,
        "triage_acc_auto":    triage_acc_auto,
    }


def run_single_s4(model: str, run_number: int, triage_id: str,
                  log_paths: list, expected: dict) -> dict:
    """
    Executa um único run do cenário S4 (um caso de triagem) e retorna dados completos.

    Fluxo: até MAX_TOOL_TURNS turnos de API.
      T1: prompt (3 paths) → modelo chama read_file(log_1)
      T2: conteúdo log_1   → modelo chama read_file(log_2)
      T3: conteúdo log_2   → modelo chama read_file(log_3)
      T4: conteúdo log_3   → modelo gera JSON de triagem

    CHAIN-ACC: número de chamadas read_file == 3 em todos os casos.
    """
    ts_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt   = build_s4_prompt(triage_id, log_paths)
    messages = [{"role": "user", "content": prompt}]

    result = {
        "run":             run_number,
        "triage_id":       triage_id,
        "timestamp":       ts_start,
        "model":           model,
        "prompt_sent":     prompt,
        "tool_call_count": 0,
        "files_read":      [],
        "final_response":  "",
        "error":           None,
        "loop_exhausted":  False,
        "perf_turns":      [],
        "perf_total":      {},
        "validation":      validate_s4_response("", expected),
    }

    try:
        for turn_idx in range(MAX_TOOL_TURNS):
            resp         = call_ollama_chat(model, messages, TOOLS, temperature=TEMPERATURE)
            perf         = extract_perf(resp)
            result["perf_turns"].append(perf)
            assistant_msg = resp.get("message", {})
            tool_calls    = extract_tool_calls(resp)

            if not tool_calls:
                # Turno sem tool call — é a resposta final
                result["final_response"] = assistant_msg.get("content", "") or ""
                break

            # Apende mensagem do assistente com os tool_calls
            messages.append({
                "role":       "assistant",
                "content":    assistant_msg.get("content", "") or "",
                "tool_calls": resp["message"].get("tool_calls", [])
            })

            # Processa cada tool call do turno (esperado: 1 por turno)
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["arguments"]
                path_arg  = tool_args.get("path", "") if isinstance(tool_args, dict) else ""

                if tool_name in VALID_TOOL_NAMES:
                    result["tool_call_count"] += 1
                    content, success = read_file_tool(path_arg)
                    result["files_read"].append({
                        "turn":    turn_idx + 1,
                        "path":    path_arg,
                        "success": success,
                    })
                    tool_output = content
                else:
                    tool_output = f"ERRO: tool '{tool_name}' não existe no ambiente."
                    result["files_read"].append({
                        "turn":    turn_idx + 1,
                        "path":    path_arg,
                        "success": False,
                    })

                messages.append({
                    "role":    "tool",
                    "name":    tool_name,
                    "content": tool_output
                })
        else:
            result["loop_exhausted"] = True
            result["final_response"] = (
                f"[LOOP EXPIRADO: {MAX_TOOL_TURNS} turnos sem resposta final]"
            )

        result["perf_total"] = combine_perf_list(result["perf_turns"])
        result["validation"] = validate_s4_response(result["final_response"], expected)

    except RuntimeError as e:
        result["error"]          = str(e)
        result["final_response"] = f"[ERRO DE API] {e}"
        result["perf_total"]     = combine_perf_list(result["perf_turns"])

    return result


def save_case_file(run_data: dict, model_safe: str, date_str: str,
                   expected: dict) -> Path:
    """
    Salva o resultado de um único run S4 em arquivo texto estruturado.

    Nome: S4-{model_safe}-{date_str}-case-{triage_id}.txt
    """
    triage_id = run_data["triage_id"]
    filepath  = RESULTS_DIR / f"S4think-{model_safe}-{date_str}-case-{triage_id}.txt"
    v         = run_data.get("validation", {})

    def _bool(key):
        return str(v.get(key, False))

    lines = [
        f"# S4 — Case {triage_id}  (Run {run_data['run']})",
        f"# Modelo         : {run_data['model']}",
        f"# Timestamp      : {run_data['timestamp']}",
        f"# Temperatura    : {TEMPERATURE}",
        f"# API            : {OLLAMA_API_URL}",
        f"# Prompt fonte   : S4-triage-multi-log.md seção 4",
        "#" + "-" * 60,
        "",
        "## PROMPT ENVIADO",
        "",
        run_data["prompt_sent"],
        "",
        "## TOOL CALLS DO MODELO",
        "",
        f"Total read_file chamadas : {run_data['tool_call_count']}",
        f"Loop expirado            : {run_data['loop_exhausted']}",
        "",
    ]

    for i, fr in enumerate(run_data["files_read"], start=1):
        lines += [
            f"### Tool call {i}",
            f"  Turno   : {fr['turn']}",
            f"  Path    : {fr['path']}",
            f"  Sucesso : {fr['success']}",
            "",
        ]

    if not run_data["files_read"]:
        lines += ["  (nenhuma chamada read_file registrada)", ""]

    lines += [
        "## RESPOSTA FINAL DO MODELO",
        "",
        run_data["final_response"] if run_data["final_response"] else "(vazia)",
        "",
        "## VALIDAÇÃO DETALHADA",
        "",
        f"  schema_valid        : {_bool('schema_valid')}",
        f"  all_hosts_present   : {_bool('all_hosts_present')}",
        f"    expected : {expected.get('hosts_expected', [])}",
        f"  rank_order_correct  : {_bool('rank_order_correct')}",
        f"    expected : {[p['host'] for p in expected.get('prioridade_expected', [])]}",
        f"  escalation_correct  : {_bool('escalation_correct')}",
        f"  acao_geral_present  : {_bool('acao_geral_present')}",
        f"  triage_acc_auto     : {v.get('triage_acc_auto', 0)}",
        f"  chain_acc           : {'4 (read_file x3)' if run_data['tool_call_count'] == 3 else '0 (read_file x' + str(run_data['tool_call_count']) + ')'}",
        "",
        "## PERFORMANCE POR TURNO",
        "",
    ]

    for i, p in enumerate(run_data["perf_turns"], start=1):
        lines += [
            f"### Turno {i}",
            f"  tokens input   : {_fmt_perf(p.get('tokens_input'))}",
            f"  tokens output  : {_fmt_perf(p.get('tokens_output'))}",
            f"  duração        : {_fmt_perf(p.get('duracao_ms'))} ms",
            f"  velocidade     : {_fmt_perf(p.get('tokens_por_segundo'), '.1f')} tok/s",
            f"  thinking chars : {_fmt_perf(p.get('thinking_chars'))}",
            "",
        ]

    pt = run_data.get("perf_total", {})
    lines += [
        "### Total do run",
        f"  tokens total   : {_fmt_perf(pt.get('total_tokens'))}",
        f"  duração total  : {_fmt_perf(pt.get('total_duracao_ms'))} ms",
        f"  velocidade avg : {_fmt_perf(pt.get('media_tokens_por_segundo'), '.1f')} tok/s",
        "",
    ]

    total_thinking = sum(
        (p.get("thinking_chars") or 0) for p in run_data["perf_turns"]
    )
    lines += [
        f"  thinking total : {total_thinking} chars",
        "",
    ]

    if run_data["error"]:
        lines += ["## ERRO DE EXECUÇÃO", "", run_data["error"], ""]

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def save_summary(all_cases: list, model: str, model_safe: str, date_str: str) -> Path:
    """
    Gera o arquivo summary S4 com tabela de resultados por caso.
    """
    filepath = RESULTS_DIR / f"S4think-{model_safe}-{date_str}-summary.md"

    lines = [
        f"# S4 Summary — {model} — {date_str}",
        "",
        "## Metadados",
        "",
        "| Campo                   | Valor                                                    |",
        "|-------------------------|----------------------------------------------------------|",
        "| Cenário                 | S4 – Triagem multi-log e decisão de escalonamento        |",
        f"| Modelo                  | {model}                                                  |",
        "| Bateria                 | 1                                                        |",
        f"| Data                    | {date_str}                                               |",
        f"| K (casos)               | {K}                                                      |",
        f"| Temperatura             | {TEMPERATURE}                                            |",
        f"| API                     | {OLLAMA_API_URL}                                         |",
        "| Tool disponível         | read_file                                                |",
        "| Tool calls esperados    | 3 por caso (CHAIN-ACC)                                   |",
        f"| MAX_TOOL_TURNS          | {MAX_TOOL_TURNS}                                         |",
        "| Fixtures S4             | fixtures/triage-s4/                                      |",
        "| VRAM disponível início  | _(preencher manualmente)_                                |",
        "",
        "## Resultados",
        "",
        "Colunas auto: TRIAGE-ACC, CHAIN-ACC, schema_valid, all_hosts, rank_ok, esc_ok, acao_geral.",
        "Colunas manuais: INST, CON, TOOL-CON, TOOL-ACC (critérios: ADR-0001).",
        f"Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`",
        f"           `docs/benchmarks/S4-triage-multi-log.md`, seções 6–7",
        "",
        "| Case | TRIAGE-ACC | CHAIN-ACC | schema_valid | all_hosts | rank_ok | esc_ok | acao_geral | read_file_calls | tok_total | ms | tok/s | thinking | Obs |",
        "|------|-----------|-----------|-------------|-----------|---------|--------|-----------|----------------|-----------|----|----|----------|-----|",
    ]

    for r in all_cases:
        v           = r.get("validation", {})
        triage_acc  = v.get("triage_acc_auto", 0)
        chain_acc   = 4 if r["tool_call_count"] == 3 else 0
        schema_ok   = v.get("schema_valid", False)
        all_hosts   = v.get("all_hosts_present", False)
        rank_ok     = v.get("rank_order_correct", False)
        esc_ok      = v.get("escalation_correct", False)
        acao_ok     = v.get("acao_geral_present", False)
        rf_calls    = r["tool_call_count"]

        pt  = r.get("perf_total", {})
        tok = _fmt_perf(pt.get("total_tokens"))
        ms  = _fmt_perf(pt.get("total_duracao_ms"))
        tps = _fmt_perf(pt.get("media_tokens_por_segundo"), ".1f")
        th  = sum((p.get("thinking_chars") or 0) for p in r.get("perf_turns", []))

        lines.append(
            f"| {r['triage_id']} | {triage_acc}          | {chain_acc}         "
            f"| {str(schema_ok):<12} | {str(all_hosts):<9} "
            f"| {str(rank_ok):<7} | {str(esc_ok):<6} "
            f"| {str(acao_ok):<9} | {rf_calls:<14} "
            f"| {tok:<9} | {ms:<8} | {tps:<5} | {th:<8} |     |"
        )

    lines += [
        "",
        "## Notas por dimensão (Bateria 1)",
        "",
        "- **TRIAGE-ACC** (agregado): _(derivar de triage_acc_auto acima)_",
        "- **CHAIN-ACC** (agregado): _(derivar de read_file_calls acima — 3 em todos = nota 4)_",
        "- **CON:** _(preencher após leitura dos runs — verificar: severity ↔ escalation, rank sem duplicatas, timestamp_triage coerente)_",
        "- **INST:** _(preencher após leitura dos runs — checklist S4-triage-multi-log.md seção 8)_",
        "- **TOOL-CON:** _(preencher após leitura dos runs)_",
        "- **TOOL-ACC:** _(preencher após leitura dos runs)_",
        "- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)",
        "",
        "## Observações brutas (geradas automaticamente)",
        "",
        "| Case | read_file calls | loop_exhausted | triage_acc_auto | chain_acc | all_hosts | rank_ok | esc_ok |",
        "|------|----------------|----------------|-----------------|-----------|-----------|---------|--------|",
    ]

    for r in all_cases:
        v          = r.get("validation", {})
        chain_acc  = 4 if r["tool_call_count"] == 3 else 0
        lines.append(
            f"| {r['triage_id']} | {r['tool_call_count']} | {r['loop_exhausted']} "
            f"| {v.get('triage_acc_auto', 0)} | {chain_acc} "
            f"| {v.get('all_hosts_present', False)} | {v.get('rank_order_correct', False)} "
            f"| {v.get('escalation_correct', False)} |"
        )

    lines += [
        "",
        "## Arquivos de runs",
        "",
    ]
    for r in all_cases:
        fn = f"S4think-{model_safe}-{date_str}-case-{r['triage_id']}.txt"
        lines.append(f"- [`{fn}`]({fn})")

    lines += [
        "",
        "## Próximos passos",
        "",
        "- [ ] Ler os 3 arquivos de run e atribuir notas INST/CON/TOOL-CON/TOOL-ACC.",
        "- [ ] Verificar manualmente a qualidade do campo `acao_geral` em cada run.",
        "- [ ] Executar Bateria 2 após mínimo de 12h.",
        "- [ ] Calcular STAB comparando notas das duas baterias.",
        "- [ ] Atualizar hipóteses H10/H11 com dados S4.",
        "- [ ] Avançar para o próximo modelo da shortlist.",
        "",
        "---",
        "",
        f"_Gerado automaticamente por `scripts/run-s4-thinking-benchmark.py` em {date_str}_",
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
        print("Uso: python3 scripts/run-s4-benchmark.py <modelo>")
        print("Exemplo: python3 scripts/run-s4-benchmark.py qwen3:14b")
        sys.exit(1)

    model      = sys.argv[1]
    model_safe = sanitize_model_name(model)
    date_str   = datetime.date.today().isoformat()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  S4 Benchmark — Triagem multi-log, 3 tool calls encadeados")
    print(f"  Modelo         : {model}")
    print(f"  Data           : {date_str}")
    print(f"  K casos        : {K}")
    print(f"  Temp           : {TEMPERATURE}")
    print(f"  Timeout        : {TIMEOUT_SECONDS}s")
    print(f"  MAX_TOOL_TURNS : {MAX_TOOL_TURNS}")
    print(f"  Tool           : read_file (leitura direta via Python)")
    print(f"  API            : {OLLAMA_API_URL}")
    print("=" * 60)
    print()

    all_cases = []

    for run_number, triage_id in enumerate(CASES, start=1):
        expected  = load_expected_s4(triage_id)
        log_paths = resolve_log_paths(expected)

        print(f"[Run {run_number}/{K}] triage_id={triage_id}")
        for i, p in enumerate(log_paths, start=1):
            print(f"  log_{i}: {p}")

        run_data = run_single_s4(model, run_number, triage_id, log_paths, expected)
        all_cases.append(run_data)

        filepath  = save_case_file(run_data, model_safe, date_str, expected)

        v          = run_data.get("validation", {})
        triage_acc = v.get("triage_acc_auto", 0)
        chain_acc  = 4 if run_data["tool_call_count"] == 3 else 0
        status     = "OK" if run_data["error"] is None else "ERRO"

        print(f"  -> read_file chamadas   : {run_data['tool_call_count']}")
        print(f"  -> CHAIN-ACC            : {chain_acc}")
        print(f"  -> schema_valid         : {v.get('schema_valid', False)}")
        print(f"  -> all_hosts_present    : {v.get('all_hosts_present', False)}")
        print(f"  -> rank_order_correct   : {v.get('rank_order_correct', False)}")
        print(f"  -> escalation_correct   : {v.get('escalation_correct', False)}")
        print(f"  -> TRIAGE-ACC           : {triage_acc}")
        print(f"  -> loop_exhausted       : {run_data['loop_exhausted']}")
        print(f"  -> status               : {status}")
        print(f"  -> salvo em             : {filepath}")

        pt = run_data.get("perf_total", {})
        th = sum((p.get("thinking_chars") or 0) for p in run_data.get("perf_turns", []))
        print(f"  -> tokens/s             : {_fmt_perf(pt.get('media_tokens_por_segundo'), '.1f')} tok/s")
        print(f"  -> tokens total         : {_fmt_perf(pt.get('total_tokens'))}")
        print(f"  -> duração total        : {_fmt_perf(pt.get('total_duracao_ms'))} ms")
        print(f"  -> thinking total       : {'sim (' + str(th) + ' chars)' if th > 0 else 'não'}")
        print()

    print("=" * 60)
    print(f"  {K} casos concluídos.")
    print("=" * 60)
    print()

    summary_path = save_summary(all_cases, model, model_safe, date_str)
    print(f"Summary gerado : {summary_path}")
    print()
    print("Próximos passos:")
    print(f"  1. Leia os arquivos de run em {RESULTS_DIR}/")
    print("  2. Atribua notas INST/CON/TOOL-CON/TOOL-ACC conforme ADR-0001.")
    print("  3. Execute novamente após 12h para a Bateria 2 (STAB).")
    print("  4. Atualize hipóteses H10/H11 com dados S4.")


if __name__ == "__main__":
    main()
