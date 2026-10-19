#!/usr/bin/env python3
"""
run-s3-benchmark.py

Executa o cenário S3 (Análise de log estruturado, classificação de severidade
e geração de resumo) com tool use real via API Ollama.

Evolução direta de run-s2-benchmark.py para o cenário S3. Reutiliza sem alteração:
OLLAMA_API_URL, TEMPERATURE, TIMEOUT_SECONDS, call_ollama_chat, extract_tool_calls,
extract_perf, combine_perf, _fmt_perf, sanitize_model_name.

Diferenças em relação ao S2:
  - Tool: read_file (leitura direta via Path.read_text, sem subprocess)
  - K = 4 (um run por caso de fixture, não K runs do mesmo prompt)
  - Sem SLEEP_BETWEEN_RUNS (casos são independentes)
  - Validação: validate_s3_response() compara contra .expected.json
  - Arquivos de run: S3-{model}-{data}-case-{case_id}.txt
  - Métricas específicas: CLASS-ACC, PARSE-ACC, SUMMARY-QUAL

Uso:
    python3 scripts/run-s3-benchmark.py <modelo>

Exemplo:
    python3 scripts/run-s3-benchmark.py qwen3:14b

Requerimentos:
    pip install requests  (stdlib: json, re, sys, os, datetime, pathlib)
"""

import sys
import os
import json
import re
import datetime
import requests
from pathlib import Path

# =============================================================================
# CONSTANTES E CONFIGURAÇÕES
# Copiadas de run-s2-benchmark.py sem alteração.
# =============================================================================

OLLAMA_API_URL  = os.environ.get("LOP_SHIM_URL", "http://localhost:11434/api/chat")
TEMPERATURE     = 0
TIMEOUT_SECONDS = 300
RESULTS_DIR     = Path("results/benchmarks")
FIXTURES_DIR    = Path("fixtures/health-logs")

# K derivado dos casos — não alterar manualmente.
CASES = [
    ("info-001",     "info"),
    ("warning-001",  "warning"),
    ("critical-001", "critical"),
    ("mixed-001",    "mixed"),
]
K = len(CASES)

# =============================================================================
# DEFINIÇÃO DA TOOL read_file
# S3 usa apenas read_file — sem run_bash, sem rename_file.
# Implementação: Path(path).read_text(encoding='utf-8') — sem subprocess.
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
# PROMPT DO CENÁRIO S3
# DECISÃO: template fixo, nunca alterar entre runs nem entre baterias.
# Fonte: docs/benchmarks/S3-log-analysis-classify.md, seção 5.
# {log_path} é substituído por .replace() para evitar conflito com as chaves
# JSON no próprio template.
# =============================================================================

S3_PROMPT_TEMPLATE = """\
Leia o arquivo de log em {log_path} e analise seu conteúdo.
Com base nas linhas do log, gere um JSON com o seguinte schema:
{{
  "case_id": "<nome do arquivo de log sem extensão, ex: warning-001>",
  "severity": "<info|warning|critical>",
  "primary_issue": "<identificador snake_case do problema principal, ex: disk_full, service_failed, high_cpu. Use 'none' se tudo OK>",
  "secondary_issues": ["<lista de problemas secundários>"],
  "host": "<hostname extraído do log>",
  "timestamp": "<timestamp da última linha do log em ISO 8601 com Z>",
  "requires_action": <true se severity for warning ou critical, false se info>,
  "summary": "<resumo operacional em português do Brasil, 1 a 2 frases>"
}}
Regras de classificação:
- critical: qualquer linha com level=CRITICAL
- warning: nenhuma CRITICAL, mas pelo menos uma WARNING
- info: todas as linhas são INFO
Use APENAS os seguintes identificadores para primary_issue e secondary_issues:
  none
  high_cpu_usage
  elevated_application_latency
  database_unavailable
  disk_critical_on_var
  postgresql_service_failed
  redis_service_failed
  backup_volume_high_usage
  session_api_error_rate_elevated
Não use frases livres nem outros identificadores.
Responda APENAS com o JSON. Sem markdown. Sem texto adicional."""


def build_prompt(log_path_abs: Path) -> str:
    """Substitui {log_path} no template pelo caminho absoluto real."""
    return S3_PROMPT_TEMPLATE.replace("{log_path}", str(log_path_abs))


# =============================================================================
# FUNÇÕES COPIADAS DE run-s2-benchmark.py SEM ALTERAÇÃO
# =============================================================================

def sanitize_model_name(model: str) -> str:
    return model.replace(":", "-").replace("/", "_")


def call_ollama_chat(model: str, messages: list, tools: list, temperature: int = 0) -> dict:
    payload = {
        "model":    model,
        "messages": messages,
        "tools":    tools,
        "stream":   False,
        "think":    False,
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
# FUNÇÕES ESPECÍFICAS DO S3
# =============================================================================

def check_repo_root() -> None:
    """Verifica que o script está sendo executado da raiz do repositório."""
    if not Path("docs/benchmarks/S3-log-analysis-classify.md").exists():
        print("ERRO: execute este script a partir da raiz do repositório llms-on-prem.")
        print("      python3 scripts/run-s3-benchmark.py <modelo>")
        sys.exit(1)
    if not FIXTURES_DIR.exists():
        print(f"ERRO: diretório de fixtures não encontrado: {FIXTURES_DIR}")
        sys.exit(1)


def load_expected(case_id: str, subdir: str) -> dict:
    """Carrega o .expected.json do caso de fixture."""
    path = FIXTURES_DIR / subdir / f"{case_id}.expected.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERRO ao carregar expected.json de {path}: {e}")
        sys.exit(1)


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


def validate_s3_response(response_text: str, expected: dict) -> dict:
    """
    Valida a resposta final do modelo para o cenário S3.

    Retorna dict com:
      json_valid              : bool
      severity_match          : bool — response.severity == expected.severity_expected
      primary_issue_match     : bool — response.primary_issue == expected.primary_issue
      secondary_issues_match  : bool — set(response) == set(expected), ordem não importa
      requires_action_match   : bool — response.requires_action == expected.requires_action
      host_match              : bool — response.host == expected.host
      timestamp_match         : bool — response.timestamp == expected.timestamp
      summary_present         : bool — 20 <= len(summary) <= 300
      matches_total           : int  — soma dos bool acima
      class_acc_auto          : int  — 0|2|3|4
      parse_acc_auto          : int  — 0|2|3|4

    DECISÃO: usar json.JSONDecoder.raw_decode() a partir do primeiro '{' —
    mesma abordagem de validate_json_response() em run-s2-benchmark.py.
    Isso tolera markdown wrapper sem tratar o JSON como inválido.
    """
    stripped   = response_text.strip() if response_text else ""
    json_valid = False
    data       = None

    start = stripped.find("{")
    if start != -1:
        try:
            decoder    = json.JSONDecoder()
            data, _    = decoder.raw_decode(stripped, start)
            json_valid = isinstance(data, dict)
        except json.JSONDecodeError:
            json_valid = False

    if not json_valid or data is None:
        return {
            "json_valid":             False,
            "severity_match":         False,
            "primary_issue_match":    False,
            "secondary_issues_match": False,
            "requires_action_match":  False,
            "host_match":             False,
            "timestamp_match":        False,
            "summary_present":        False,
            "matches_total":          0,
            "class_acc_auto":         0,
            "parse_acc_auto":         0,
        }

    severity_match = data.get("severity") == expected.get("severity_expected")
    primary_issue_match = data.get("primary_issue") == expected.get("primary_issue")

    resp_secondary = data.get("secondary_issues") or []
    exp_secondary  = expected.get("secondary_issues") or []
    secondary_issues_match = set(resp_secondary) == set(exp_secondary)

    requires_action_match = data.get("requires_action") == expected.get("requires_action")
    host_match            = data.get("host") == expected.get("host")
    timestamp_match       = data.get("timestamp") == expected.get("timestamp")

    summary = data.get("summary") or ""
    summary_present = isinstance(summary, str) and 20 <= len(summary) <= 300

    bools = [
        severity_match, primary_issue_match, secondary_issues_match,
        requires_action_match, host_match, timestamp_match, summary_present,
    ]
    matches_total = sum(1 for b in bools if b)

    # class_acc_auto: baseado nos critérios da seção 8 de S3-log-analysis-classify.md
    if severity_match and primary_issue_match and requires_action_match:
        class_acc_auto = 4
    elif severity_match and primary_issue_match:
        class_acc_auto = 3
    elif severity_match:
        class_acc_auto = 2
    else:
        class_acc_auto = 0

    # parse_acc_auto: baseado nos critérios da seção 8 de S3-log-analysis-classify.md
    if primary_issue_match and secondary_issues_match and host_match:
        parse_acc_auto = 4
    elif primary_issue_match:
        parse_acc_auto = 3
    else:
        parse_acc_auto = 2  # json_valid=True mas primary_issue errado

    return {
        "json_valid":             True,
        "severity_match":         severity_match,
        "primary_issue_match":    primary_issue_match,
        "secondary_issues_match": secondary_issues_match,
        "requires_action_match":  requires_action_match,
        "host_match":             host_match,
        "timestamp_match":        timestamp_match,
        "summary_present":        summary_present,
        "matches_total":          matches_total,
        "class_acc_auto":         class_acc_auto,
        "parse_acc_auto":         parse_acc_auto,
    }


def run_single_s3(model: str, run_number: int, case_id: str,
                  log_path_abs: Path, expected: dict) -> dict:
    """
    Executa um único run do cenário S3 (um caso de fixture) e retorna dados completos.

    Fluxo: 2 turnos (igual ao S2).
      Turno 1: prompt → modelo chama read_file
      Turno 2: conteúdo do arquivo → modelo gera JSON de classificação

    DECISÃO S3: máximo de 1 turno de tool calling.
    Um modelo que chame read_file mais de uma vez em S3 seria anomalia a registrar.
    """
    ts_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt   = build_prompt(log_path_abs)
    messages = [{"role": "user", "content": prompt}]

    result = {
        "run":                  run_number,
        "case_id":              case_id,
        "timestamp":            ts_start,
        "model":                model,
        "prompt_sent":          prompt,
        "tool_called":          "NENHUMA",
        "tool_argument":        "",
        "tool_valid":           None,
        "file_content_preview": "",
        "file_read_success":    None,
        "final_response":       "",
        "error":                None,
        "extra_tool_calls":     0,
        "perf_t1":              {},
        "perf_t2":              {},
        "perf_total":           {},
        "validation":           validate_s3_response("", expected),
    }

    try:
        resp1         = call_ollama_chat(model, messages, TOOLS, temperature=TEMPERATURE)
        assistant_msg = resp1.get("message", {})
        tool_calls    = extract_tool_calls(resp1)
        result["perf_t1"] = extract_perf(resp1)

        if not tool_calls:
            result["final_response"] = assistant_msg.get("content", "")
            result["perf_t2"]        = {}
            result["perf_total"]     = combine_perf(result["perf_t1"], {})
            result["validation"]     = validate_s3_response(result["final_response"], expected)
            return result

        result["extra_tool_calls"] = max(0, len(tool_calls) - 1)
        tc        = tool_calls[0]
        tool_name = tc["name"]
        tool_args = tc["arguments"]
        result["tool_called"] = tool_name

        if tool_name in VALID_TOOL_NAMES:
            result["tool_valid"]    = True
            path_arg                = tool_args.get("path", "")
            result["tool_argument"] = path_arg
            content, success        = read_file_tool(path_arg)
            result["file_read_success"] = success
            lines = content.splitlines() if success else [content]
            result["file_content_preview"] = "\n".join(lines[:20])
            tool_output = content
        else:
            result["tool_valid"]    = False
            result["tool_argument"] = json.dumps(tool_args)
            tool_output             = f"ERRO: tool '{tool_name}' não existe no ambiente."
            result["file_read_success"] = False
            result["file_content_preview"] = tool_output

        messages.append({
            "role":       "assistant",
            "content":    assistant_msg.get("content", ""),
            "tool_calls": resp1["message"].get("tool_calls", [])
        })
        messages.append({
            "role":    "tool",
            "name":    tool_name,
            "content": tool_output
        })

        resp2 = call_ollama_chat(model, messages, TOOLS, temperature=TEMPERATURE)
        result["final_response"] = resp2.get("message", {}).get("content", "")
        result["perf_t2"]        = extract_perf(resp2)
        result["perf_total"]     = combine_perf(result["perf_t1"], result["perf_t2"])
        result["validation"]     = validate_s3_response(result["final_response"], expected)

    except RuntimeError as e:
        result["error"]          = str(e)
        result["final_response"] = f"[ERRO DE API] {e}"

    return result


def save_case_file(run_data: dict, model_safe: str, date_str: str) -> Path:
    """
    Salva o resultado de um único run S3 em arquivo texto estruturado.

    Nome do arquivo: S3-{model_safe}-{date_str}-case-{case_id}.txt
    Seções: prompt enviado, tool chamada, conteúdo do arquivo (20 linhas),
    resposta final, validação detalhada campo a campo, performance.
    """
    case_id  = run_data["case_id"]
    filepath = RESULTS_DIR / f"S3-{model_safe}-{date_str}-case-{case_id}.txt"

    v = run_data.get("validation", {})

    def _bool(key):
        return str(v.get(key, False))

    expected_path = (
        FIXTURES_DIR / _case_subdir(case_id) / f"{case_id}.expected.json"
    )
    try:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
    except Exception:
        expected = {}

    lines = [
        f"# S3 — Case {case_id}  (Run {run_data['run']})",
        f"# Modelo         : {run_data['model']}",
        f"# Timestamp      : {run_data['timestamp']}",
        f"# Temperatura    : {TEMPERATURE}",
        f"# API            : {OLLAMA_API_URL}",
        f"# Prompt fonte   : S3-log-analysis-classify.md seção 5",
        "#" + "-" * 60,
        "",
        "## PROMPT ENVIADO",
        "",
        run_data["prompt_sent"],
        "",
        "## TOOL CHAMADA PELO MODELO",
        "",
        f"Nome      : {run_data['tool_called']}",
        f"Argumento : {run_data['tool_argument']}",
        f"Tool válida: {run_data['tool_valid']}",
        f"Leitura OK : {run_data['file_read_success']}",
        f"Extra tool calls (anomalia): {run_data['extra_tool_calls']}",
        "",
        "## CONTEÚDO DO ARQUIVO LIDO (primeiras 20 linhas)",
        "",
        run_data["file_content_preview"] if run_data["file_content_preview"] else "(nenhum)",
        "",
        "## RESPOSTA FINAL DO MODELO",
        "",
        run_data["final_response"] if run_data["final_response"] else "(vazia)",
        "",
        "## VALIDAÇÃO DETALHADA",
        "",
        f"  json_valid              : {_bool('json_valid')}",
        f"  severity_match          : {_bool('severity_match')}",
        f"    expected : {expected.get('severity_expected', 'N/A')}",
        f"  primary_issue_match     : {_bool('primary_issue_match')}",
        f"    expected : {expected.get('primary_issue', 'N/A')}",
        f"  secondary_issues_match  : {_bool('secondary_issues_match')}",
        f"    expected : {expected.get('secondary_issues', [])}",
        f"  requires_action_match   : {_bool('requires_action_match')}",
        f"    expected : {expected.get('requires_action', 'N/A')}",
        f"  host_match              : {_bool('host_match')}",
        f"    expected : {expected.get('host', 'N/A')}",
        f"  timestamp_match         : {_bool('timestamp_match')}",
        f"    expected : {expected.get('timestamp', 'N/A')}",
        f"  summary_present         : {_bool('summary_present')}",
        f"  matches_total           : {v.get('matches_total', 0)}/7",
        f"  class_acc_auto          : {v.get('class_acc_auto', 0)}",
        f"  parse_acc_auto          : {v.get('parse_acc_auto', 0)}",
        "",
    ]

    p1 = run_data.get("perf_t1", {})
    p2 = run_data.get("perf_t2", {})
    pt = run_data.get("perf_total", {})

    def _f(val, spec=""):
        return _fmt_perf(val, spec)

    t2_label = "Turno 2 (conteúdo do arquivo → JSON de classificação)"
    t2_block = (
        [
            f"### {t2_label}",
            f"  tokens input   : {_f(p2.get('tokens_input'))}",
            f"  tokens output  : {_f(p2.get('tokens_output'))}",
            f"  duração        : {_f(p2.get('duracao_ms'))} ms",
            f"  velocidade     : {_f(p2.get('tokens_por_segundo'), '.1f')} tok/s",
            f"  thinking chars : {_f(p2.get('thinking_chars'))}",
        ]
        if p2 else
        [f"### {t2_label}", "  (turno não ocorreu — modelo não chamou tool)"]
    )

    lines += [
        "## PERFORMANCE",
        "",
        "### Turno 1 (prompt → tool call read_file)",
        f"  tokens input   : {_f(p1.get('tokens_input'))}",
        f"  tokens output  : {_f(p1.get('tokens_output'))}",
        f"  duração        : {_f(p1.get('duracao_ms'))} ms",
        f"  velocidade     : {_f(p1.get('tokens_por_segundo'), '.1f')} tok/s",
        f"  thinking chars : {_f(p1.get('thinking_chars'))}",
        "",
        *t2_block,
        "",
        "### Total do run",
        f"  tokens total   : {_f(pt.get('total_tokens'))}",
        f"  duração total  : {_f(pt.get('total_duracao_ms'))} ms",
        f"  velocidade avg : {_f(pt.get('media_tokens_por_segundo'), '.1f')} tok/s",
        "",
    ]

    if run_data["error"]:
        lines += ["## ERRO DE EXECUÇÃO", "", run_data["error"], ""]

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def _case_subdir(case_id: str) -> str:
    """Retorna o subdiretório de fixture para um dado case_id."""
    for cid, subdir in CASES:
        if cid == case_id:
            return subdir
    return case_id.split("-")[0]


def save_summary(all_cases: list, model: str, model_safe: str, date_str: str) -> Path:
    """
    Gera o arquivo summary S3 com tabela de resultados por caso.

    Colunas auto: CLASS-ACC, PARSE-ACC, json_valid, severity, primary_ok,
    secondary_ok, req_action_ok, summary_ok, tok_total, ms, tok/s, thinking.
    Colunas manuais: SUMMARY-QUAL, CON, TOOL-CON, INST, TOOL-ACC (critérios: ADR-0001).
    """
    filepath = RESULTS_DIR / f"S3-{model_safe}-{date_str}-summary.md"

    lines = [
        f"# S3 Summary — {model} — {date_str}",
        "",
        "## Metadados",
        "",
        "| Campo                   | Valor                                                   |",
        "|-------------------------|---------------------------------------------------------|",
        "| Cenário                 | S3 – Análise de log, classificação e resumo             |",
        f"| Modelo                  | {model}                                                 |",
        "| Bateria                 | 1                                                       |",
        f"| Data                    | {date_str}                                              |",
        f"| K (casos)               | {K}                                                     |",
        f"| Temperatura             | {TEMPERATURE}                                           |",
        f"| API                     | {OLLAMA_API_URL}                                        |",
        "| Tool disponível         | read_file                                               |",
        "| Execução de subprocess  | não (leitura direta via Python)                         |",
        "| Fixtures                | info-001, warning-001, critical-001, mixed-001          |",
        "| VRAM disponível início  | _(preencher manualmente)_                               |",
        "",
        "## Resultados",
        "",
        "Colunas auto: CLASS-ACC, PARSE-ACC, json_valid, severity, primary_ok, secondary_ok,",
        "req_action_ok, summary_ok.",
        "Colunas manuais: SUMMARY-QUAL, CON, TOOL-CON, INST, TOOL-ACC (critérios: ADR-0001).",
        f"Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`",
        f"           `docs/benchmarks/S3-log-analysis-classify.md`, seções 8–9",
        "",
        "| Case | Tool | Path | CLASS-ACC | PARSE-ACC | json_valid | severity | primary_ok | secondary_ok | req_action_ok | summary_ok | tok_total | ms | tok/s | thinking | Obs |",
        "|------|------|------|-----------|-----------|------------|----------|------------|--------------|---------------|------------|-----------|----|----|----------|-----|",
    ]

    for r in all_cases:
        v             = r.get("validation", {})
        class_acc     = v.get("class_acc_auto", 0)
        parse_acc     = v.get("parse_acc_auto", 0)
        json_valid    = v.get("json_valid", False)
        severity_ok   = v.get("severity_match", False)
        primary_ok    = v.get("primary_issue_match", False)
        secondary_ok  = v.get("secondary_issues_match", False)
        req_action_ok = v.get("requires_action_match", False)
        summary_ok    = v.get("summary_present", False)

        tool_acc_auto = "0" if (r["tool_valid"] is False or r["tool_called"] == "NENHUMA") else ""

        tool_arg_short = (
            r["tool_argument"][:40] + "…"
            if len(r["tool_argument"]) > 40
            else r["tool_argument"]
        )

        pt       = r.get("perf_total", {})
        p1       = r.get("perf_t1", {})
        p2       = r.get("perf_t2", {})
        tok      = _fmt_perf(pt.get("total_tokens"))
        ms       = _fmt_perf(pt.get("total_duracao_ms"))
        tps      = _fmt_perf(pt.get("media_tokens_por_segundo"), ".1f")
        th       = (p1.get("thinking_chars") or 0) + (p2.get("thinking_chars") or 0)
        thinking = str(th) if th else "0"

        lines.append(
            f"| {r['case_id']} | {r['tool_called']} | `{tool_arg_short}` "
            f"| {class_acc}         | {parse_acc}         "
            f"| {str(json_valid):<10} | {str(severity_ok):<8} "
            f"| {str(primary_ok):<10} | {str(secondary_ok):<12} "
            f"| {str(req_action_ok):<13} | {str(summary_ok):<10} "
            f"| {tok:<9} | {ms:<8} | {tps:<5} | {thinking:<8} |     |"
        )

    lines += [
        "",
        "## Notas por dimensão (Bateria 1)",
        "",
        "- **CON:** _(preencher após leitura dos 4 runs)_",
        "- **TOOL-CON:** _(preencher após leitura dos 4 runs)_",
        "- **INST:** _(preencher após leitura dos 4 runs)_",
        "- **TOOL-ACC:** _(preencher após leitura dos 4 runs)_",
        "- **CLASS-ACC** (agregado): _(derivar de class_acc_auto acima)_",
        "- **PARSE-ACC** (agregado): _(derivar de parse_acc_auto acima)_",
        "- **SUMMARY-QUAL** (agregado): _(avaliação manual — ler campo summary em cada run)_",
        "- **STAB:** n/a — aguardar Bateria 2 (mínimo 12h em sessão separada)",
        "",
        "## Observações brutas (geradas automaticamente)",
        "",
        "| Case | Tool chamada | Argumento completo | Tool válida | Leitura OK | Extra calls | class_acc_auto | parse_acc_auto |",
        "|------|-------------|-------------------|-------------|------------|-------------|----------------|----------------|",
    ]

    for r in all_cases:
        arg       = r["tool_argument"].replace("|", "\\|")
        v         = r.get("validation", {})
        class_acc = v.get("class_acc_auto", "N/A")
        parse_acc = v.get("parse_acc_auto", "N/A")
        lines.append(
            f"| {r['case_id']} | {r['tool_called']} | `{arg}` "
            f"| {r['tool_valid']} | {r['file_read_success']} "
            f"| {r['extra_tool_calls']} | {class_acc} | {parse_acc} |"
        )

    lines += [
        "",
        "## Arquivos de runs",
        "",
    ]
    for r in all_cases:
        fn = f"S3-{model_safe}-{date_str}-case-{r['case_id']}.txt"
        lines.append(f"- [`{fn}`]({fn})")

    lines += [
        "",
        "## Próximos passos",
        "",
        "- [ ] Ler os 4 arquivos de run e atribuir notas na tabela acima.",
        "- [ ] Avaliar SUMMARY-QUAL manualmente (ler campo `summary` em cada run).",
        "- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.",
        "- [ ] Calcular STAB comparando notas das duas baterias.",
        "- [ ] Avançar para o próximo modelo da shortlist.",
        "",
        "---",
        "",
        f"_Gerado automaticamente por `scripts/run-s3-benchmark.py` em {date_str}_",
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
        print("Uso: python3 scripts/run-s3-benchmark.py <modelo>")
        print("Exemplo: python3 scripts/run-s3-benchmark.py qwen3:14b")
        sys.exit(1)

    model      = sys.argv[1]
    model_safe = sanitize_model_name(model)
    date_str   = datetime.date.today().isoformat()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  S3 Benchmark — Análise de log, classificação e resumo")
    print(f"  Modelo  : {model}")
    print(f"  Data    : {date_str}")
    print(f"  K casos : {K}")
    print(f"  Temp    : {TEMPERATURE}")
    print(f"  Timeout : {TIMEOUT_SECONDS}s")
    print(f"  Tool    : read_file (leitura direta via Python)")
    print(f"  API     : {OLLAMA_API_URL}")
    print("=" * 60)
    print()

    all_cases = []

    for run_number, (case_id, subdir) in enumerate(CASES, start=1):
        log_path_abs = (FIXTURES_DIR / subdir / f"{case_id}.log").resolve()
        expected     = load_expected(case_id, subdir)

        print(f"[Run {run_number}/{K}] case={case_id}  log={log_path_abs}")

        run_data = run_single_s3(model, run_number, case_id, log_path_abs, expected)
        all_cases.append(run_data)

        filepath = save_case_file(run_data, model_safe, date_str)

        status    = "OK" if run_data["error"] is None else "ERRO"
        v         = run_data.get("validation", {})
        class_acc = v.get("class_acc_auto", 0)

        print(f"  -> tool chamada         : {run_data['tool_called']}")
        print(f"  -> json_valid           : {v.get('json_valid', False)}")
        print(f"  -> severity_match       : {v.get('severity_match', False)}")
        print(f"  -> primary_issue_match  : {v.get('primary_issue_match', False)}")
        print(f"  -> class_acc_auto       : {class_acc}")
        print(f"  -> status               : {status}")
        print(f"  -> salvo em             : {filepath}")

        pt  = run_data.get("perf_total", {})
        p1  = run_data.get("perf_t1", {})
        p2  = run_data.get("perf_t2", {})
        th  = (p1.get("thinking_chars") or 0) + (p2.get("thinking_chars") or 0)
        print(f"  -> tokens/s             : {_fmt_perf(pt.get('media_tokens_por_segundo'), '.1f')} tok/s")
        print(f"  -> tokens total         : {_fmt_perf(pt.get('total_tokens'))}")
        print(f"  -> duração              : {_fmt_perf(pt.get('total_duracao_ms'))} ms")
        print(f"  -> thinking             : {'sim (' + str(th) + ' chars)' if th > 0 else 'não'}")
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
    print("  2. Avalie SUMMARY-QUAL manualmente (campo summary em cada run).")
    print("  3. Preencha as notas CON/TOOL-CON/INST/TOOL-ACC conforme ADR-0001.")
    print("  4. Execute novamente após 12h para a Bateria 2 (STAB).")


if __name__ == "__main__":
    main()
