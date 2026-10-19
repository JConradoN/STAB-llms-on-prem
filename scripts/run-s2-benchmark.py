#!/usr/bin/env python3
"""
run-s2-benchmark.py

Executa o cenário S2 (Health check com parsing e geração de JSON estruturado)
com tool use real via API Ollama.

Evolução direta de run-s1-benchmark.py para o cenário S2. Reutiliza sem alteração:
OLLAMA_API_URL, TEMPERATURE, K, TIMEOUT_SECONDS, SLEEP_BETWEEN_RUNS, RESULTS_DIR,
TOOLS, execute_bash, call_ollama_chat, extract_tool_calls, extract_perf,
combine_perf, _fmt_perf, sanitize_model_name.

Adições em relação ao S1:
  - S2_PROMPT: prompt fixo do cenário S2 (docs/benchmarks/S2-health-check-json.md)
  - SCHEMA_ESPERADO / EXPECTED_FIELDS: schema e lista de validação com tipos
  - validate_json_response(): validação automática do JSON gerado pelo modelo
  - Seção ## VALIDAÇÃO DO JSON nos arquivos de run
  - Tabela de summary com colunas de validação automática

Uso:
    python3 scripts/run-s2-benchmark.py <modelo>

Exemplo:
    python3 scripts/run-s2-benchmark.py qwen3.5:9b

Requerimentos:
    pip install requests  (stdlib: subprocess, json, re, sys, os, datetime, time, pathlib)
"""

import sys
import os
import json
import re
import subprocess
import datetime
import time
import requests
from pathlib import Path

# =============================================================================
# CONSTANTES E CONFIGURAÇÕES
# Copiadas de run-s1-benchmark.py sem alteração.
# S2 usa a mesma infraestrutura de API, temperatura, K e timeouts.
# =============================================================================

OLLAMA_API_URL     = os.environ.get("LOP_SHIM_URL", "http://localhost:11434/api/chat")
TEMPERATURE        = 0
K                  = 5
TIMEOUT_SECONDS    = 300
SLEEP_BETWEEN_RUNS = 30
RESULTS_DIR        = Path("results/benchmarks")

# =============================================================================
# DEFINIÇÃO DA TOOL run_bash
# Copiada de run-s1-benchmark.py sem alteração.
# S2 usa a mesma tool única — a complexidade adicional é cognitiva (parsing +
# geração de JSON), não estrutural (não requer tools extras).
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

VALID_TOOL_NAMES = {"run_bash"}

# =============================================================================
# PROMPT DO CENÁRIO S2
# DECISÃO: texto fixo, nunca alterar entre runs nem entre baterias.
# Fonte: docs/benchmarks/S2-health-check-json.md, seção 4.
# O schema no prompt usa linguagem PT-BR (<inteiro>, <número decimal>) em vez
# de nomes de tipo Python — mais natural para o modelo e consistente com o
# documento de especificação que o orienta.
# =============================================================================
S2_PROMPT = """\
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
  "gpus": [
    {
      "nome": "<string>",
      "uso_pct": <inteiro>,
      "temperatura_c": <inteiro>,
      "vram_usada_mib": <inteiro>,
      "vram_livre_mib": <inteiro>,
      "vram_total_mib": <inteiro>
    }
  ]
}

O campo "gpus" é um array. Se o servidor tiver mais de uma GPU, inclua um objeto por GPU.
Responda APENAS com o JSON válido, sem texto adicional, sem markdown, sem bloco de código.
Se não conseguir executar o script, responda apenas: ERRO: não consegui executar health.sh"""

# =============================================================================
# SCHEMA DE VALIDAÇÃO
# DECISÃO: duas representações do mesmo schema, com papéis distintos.
#
# SCHEMA_ESPERADO: dict nested para referência e documentação — espelha a
# estrutura do JSON esperado. O valor de cada folha é o tipo Python aceito.
#
# EXPECTED_FIELDS: lista plana de (caminho_ponto, tipo) usada pela validação —
# mais eficiente para iterar e verificar tipos sem recursão.
#
# Se o schema mudar, ambas as estruturas devem ser atualizadas em sincronia.
# Fonte: docs/benchmarks/S2-health-check-json.md, seção 3.
# =============================================================================

# cpu.uso_pct aceita (float, int) porque JSON não distingue os dois —
# 3.4 parseará como float, 3 como int; ambos são semanticamente corretos
# para uso percentual de CPU.
SCHEMA_ESPERADO = {
    "timestamp": str,
    "cpu": {
        "uso_pct":      (float, int),
        "temperatura_c": int
    },
    "memoria": {
        "total_mb":      int,
        "usada_mb":      int,
        "livre_mb":      int,
        "disponivel_mb": int
    },
    # gpus: array de objetos — um por GPU detectada pelo health.sh.
    # Substituiu o objeto único "gpu" para suportar servidores multi-GPU.
    # ADR: mudança de schema em 2026-06-04 motivada por upgrade dual-GPU.
    "gpus": [{
        "nome":          str,
        "uso_pct":       int,
        "temperatura_c": int,
        "vram_usada_mib": int,
        "vram_livre_mib": int,
        "vram_total_mib": int
    }]
}

# EXPECTED_FIELDS: campos escalares validados por caminho ponto.
# gpus é tratado separadamente em validate_json_response (array).
EXPECTED_FIELDS = [
    ("timestamp",              str),
    ("cpu.uso_pct",            (float, int)),
    ("cpu.temperatura_c",      int),
    ("memoria.total_mb",       int),
    ("memoria.usada_mb",       int),
    ("memoria.livre_mb",       int),
    ("memoria.disponivel_mb",  int),
]

# Campos obrigatórios por item do array gpus.
GPU_ITEM_FIELDS = [
    ("nome",           str),
    ("uso_pct",        int),
    ("temperatura_c",  int),
    ("vram_usada_mib", int),
    ("vram_livre_mib", int),
    ("vram_total_mib", int),
]

# TOTAL_FIELDS = 7 escalares + 6 por GPU (mínimo 1 GPU = 13).
# Exibido como "X/13+" dependendo do número de GPUs.
TOTAL_FIELDS = len(EXPECTED_FIELDS) + len(GPU_ITEM_FIELDS)  # 13 para 1 GPU

# Regex para validar formato ISO 8601 sem timezone (YYYY-MM-DDTHH:MM:SS).
# DECISÃO: validar apenas o formato, não a validade calendárica do valor.
# O objetivo é verificar se o modelo converteu a data PT-BR corretamente;
# detectar datas impossíveis (ex.: mês 13) está fora do escopo de S2.
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


# =============================================================================
# FUNÇÕES COPIADAS DE run-s1-benchmark.py SEM ALTERAÇÃO
# =============================================================================

def sanitize_model_name(model: str) -> str:
    """
    Converte nome do modelo para uso seguro em caminhos de arquivo.
    Exemplo: qwen3.5:9b → qwen3.5-9b
    """
    return model.replace(":", "-").replace("/", "_")


def execute_bash(command: str) -> tuple:
    """
    Executa um comando bash no host via subprocess e retorna (stdout, sucesso).

    DECISÃO: ['bash', '-c', command] em vez de shell=True.
    DECISÃO: os.path.expanduser para garantir expansão de '~'.
    Veja run-s1-benchmark.py para justificativas completas.

    AVISO: executa comandos gerados pelo modelo no host. Ferramenta de pesquisa
    controlada — não usar em produção.
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


def call_ollama_chat(model: str, messages: list, tools: list, temperature: int = 0) -> dict:
    """
    Chama POST /api/chat da API Ollama com tool use.
    DECISÃO: stream=false, timeout via requests. Veja run-s1-benchmark.py.
    """
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
    """
    Extrai tool_calls da resposta da API Ollama.
    DECISÃO: normalizar 'arguments' para dict (str ou dict, depende da versão).
    Veja run-s1-benchmark.py.
    """
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
    """
    Extrai métricas de performance de uma resposta da API Ollama.
    DECISÃO: retornar None para campos ausentes; thinking_chars via len().
    Veja run-s1-benchmark.py.
    """
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
    """
    Agrega métricas de performance de dois turnos de API.
    DECISÃO: média ponderada de tok/s por tokens_output; None tratado como 0.
    Veja run-s1-benchmark.py.
    """
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
    """Formata valor de performance; retorna 'N/A' para None."""
    if val is None:
        return "N/A"
    if spec:
        return f"{val:{spec}}"
    return str(val)


# =============================================================================
# FUNÇÕES ESPECÍFICAS DO S2
# =============================================================================

def check_repo_root() -> None:
    """
    Verifica que o script está sendo executado da raiz do repositório.
    DECISÃO S2: marcador alterado para docs/benchmarks/S2-health-check-json.md.
    Motivo: confirmar que o repositório contém a especificação do cenário S2,
    não apenas do S1. Marcador mais específico → verificação mais precisa.
    """
    if not Path("docs/benchmarks/S2-health-check-json.md").exists():
        print("ERRO: execute este script a partir da raiz do repositório llms-on-prem.")
        print("      python3 scripts/run-s2-benchmark.py <modelo>")
        sys.exit(1)


def _get_nested(data: dict, dotted_key: str) -> tuple:
    """
    Recupera um valor de um dict nested usando notação de ponto.
    Retorna (valor, encontrado).

    DECISÃO: função separada para não poluir validate_json_response com loops
    aninhados. Retorna (None, False) em qualquer nível em que a chave não existe
    ou o nó intermediário não é um dict — trata schema mal-formado graciosamente.
    """
    keys    = dotted_key.split(".")
    current = data
    for k in keys:
        if not isinstance(current, dict) or k not in current:
            return None, False
        current = current[k]
    return current, True


def validate_json_response(text: str) -> dict:
    """
    Valida a resposta final do modelo para o cenário S2.

    Retorna dict com:
      json_valid      : bool   — JSON é parseável?
      json_parsed     : dict|None — objeto parseado (None se inválido)
      fields_present  : list[str] — campos encontrados (notação ponto)
      fields_missing  : list[str] — campos ausentes do schema
      type_errors     : list[str] — erros de tipo descritivos
      timestamp_valid : bool   — timestamp bate com regex ISO 8601?
      has_extra_text  : bool   — há texto fora do JSON na resposta?
      json_acc_auto   : int    — 4 (perfeito) | 0 (JSON inválido) | -1 (avaliar manualmente)

    DECISÃO: usar json.JSONDecoder.raw_decode() a partir do primeiro '{'.
    Motivo: este método encontra e parseia o JSON mesmo quando há texto antes
    ou depois (incluindo markdown ```json ... ```), e retorna o índice de fim
    do JSON — permitindo detectar texto extra antes e depois sem regex frágil.

    DECISÃO: markdown ```json ... ``` é tratado como has_extra_text=True mas
    não como json_valid=False.
    Motivo: alguns modelos são treinados para sempre envolver JSON em blocos
    de código. O conteúdo pode estar correto semanticamente mesmo que a instrução
    "sem markdown" tenha sido violada. A distinção é capturada em has_extra_text
    para que o avaliador humano possa aplicar INST separadamente de json_acc_auto.

    DECISÃO: bool é excluído das verificações de int.
    Motivo: isinstance(True, int) == True em Python. Sem exclusão explícita,
    o valor JSON `true` seria aceito como inteiro válido — comportamento incorreto.
    """
    stripped      = text.strip() if text else ""
    has_extra_text = False
    json_valid     = False
    data           = None

    # Localizar o primeiro '{' e tentar parsear a partir daí.
    # raw_decode retorna (objeto, índice_fim) — índice_fim aponta para o
    # caractere após o fim do JSON, permitindo detectar texto após o objeto.
    start = stripped.find("{")
    if start != -1:
        try:
            decoder       = json.JSONDecoder()
            data, end_idx = decoder.raw_decode(stripped, start)
            json_valid    = True
            before        = stripped[:start].strip()
            after         = stripped[end_idx:].strip()
            has_extra_text = bool(before or after)
        except json.JSONDecodeError:
            json_valid = False

    # JSON inválido: retornar imediatamente com todos os campos ausentes.
    if not json_valid:
        return {
            "json_valid":      False,
            "json_parsed":     None,
            "fields_present":  [],
            "fields_missing":  [f for f, _ in EXPECTED_FIELDS],
            "type_errors":     [],
            "timestamp_valid": False,
            "has_extra_text":  has_extra_text,
            "json_acc_auto":   0,
        }

    # Verificar presença e tipos de cada campo escalar do schema.
    fields_present = []
    fields_missing = []
    type_errors    = []

    for field_path, expected_type in EXPECTED_FIELDS:
        val, found = _get_nested(data, field_path)

        if not found:
            fields_missing.append(field_path)
            continue

        fields_present.append(field_path)

        # Verificar tipo — excluir bool de int (isinstance(True, int) == True).
        if expected_type is int:
            if isinstance(val, bool) or not isinstance(val, int):
                type_errors.append(
                    f"{field_path}: esperado int, recebeu {type(val).__name__} ({val!r})"
                )
        elif expected_type is str:
            if not isinstance(val, str):
                type_errors.append(
                    f"{field_path}: esperado str, recebeu {type(val).__name__} ({val!r})"
                )
        elif expected_type == (float, int):
            # cpu.uso_pct: float preferido, int tolerado (3.4 vs 3)
            if isinstance(val, bool) or not isinstance(val, (float, int)):
                type_errors.append(
                    f"{field_path}: esperado float/int, recebeu {type(val).__name__} ({val!r})"
                )

    # Validar array gpus: deve existir, ser lista não vazia, e cada item
    # deve conter todos os GPU_ITEM_FIELDS com os tipos corretos.
    gpus_val = data.get("gpus")
    gpu_count = 0
    if not isinstance(gpus_val, list) or len(gpus_val) == 0:
        fields_missing.append("gpus")
    else:
        gpu_count = len(gpus_val)
        for idx, gpu_item in enumerate(gpus_val):
            if not isinstance(gpu_item, dict):
                type_errors.append(f"gpus[{idx}]: esperado dict, recebeu {type(gpu_item).__name__}")
                continue
            for sub_field, sub_type in GPU_ITEM_FIELDS:
                full_path = f"gpus[{idx}].{sub_field}"
                if sub_field not in gpu_item:
                    fields_missing.append(full_path)
                    continue
                fields_present.append(full_path)
                sub_val = gpu_item[sub_field]
                if sub_type is int:
                    if isinstance(sub_val, bool) or not isinstance(sub_val, int):
                        type_errors.append(
                            f"{full_path}: esperado int, recebeu {type(sub_val).__name__} ({sub_val!r})"
                        )
                elif sub_type is str:
                    if not isinstance(sub_val, str):
                        type_errors.append(
                            f"{full_path}: esperado str, recebeu {type(sub_val).__name__} ({sub_val!r})"
                        )

    # Validar formato do timestamp com regex (apenas formato, não validade calendárica).
    ts_val, ts_found = _get_nested(data, "timestamp")
    timestamp_valid  = (
        ts_found
        and isinstance(ts_val, str)
        and bool(TIMESTAMP_RE.match(ts_val))
    )

    # Calcular json_acc_auto conforme critérios da especificação:
    #   4 = perfeito em todas as dimensões automaticamente verificáveis
    #   0 = JSON inválido (já retornado acima; incluído aqui por completude)
    #  -1 = JSON válido mas com defeito — requer avaliação humana
    if (
        json_valid
        and not fields_missing
        and not type_errors
        and timestamp_valid
        and not has_extra_text
    ):
        json_acc_auto = 4
    else:
        json_acc_auto = -1  # json_valid=True mas algo falhou → avaliação manual

    return {
        "json_valid":      json_valid,
        "json_parsed":     data,
        "fields_present":  fields_present,
        "fields_missing":  fields_missing,
        "type_errors":     type_errors,
        "timestamp_valid": timestamp_valid,
        "has_extra_text":  has_extra_text,
        "json_acc_auto":   json_acc_auto,
        "gpu_count":       gpu_count,
    }


def run_single_s2(model: str, run_number: int) -> dict:
    """
    Executa um único run do cenário S2 e retorna um dict com todos os dados.

    Fluxo idêntico ao S1 (2 turnos, 1 tool call máximo). A diferença está na
    resposta esperada: em S2 o modelo deve parsear o stdout e gerar JSON.
    A validação do JSON é feita ao final do run, antes de retornar.

    DECISÃO S2: máximo de 1 turno de tool calling (mesmo que S1).
    S2 é nível 2 mas a complexidade é cognitiva (parsing + JSON), não estrutural.
    Um modelo que chame run_bash mais de uma vez em S2 seria uma anomalia a registrar.
    """
    ts_start = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    messages = [{"role": "user", "content": S2_PROMPT}]

    result = {
        "run":              run_number,
        "timestamp":        ts_start,
        "model":            model,
        "tool_called":      "NENHUMA",
        "tool_argument":    "",
        "tool_valid":       None,
        "tool_stdout":      "",
        "tool_success":     None,
        "final_response":   "",
        "error":            None,
        "extra_tool_calls": 0,
        "perf_t1":          {},
        "perf_t2":          {},
        "perf_total":       {},
        # ADIÇÃO S2: validação inicializada com texto vazio para que save_run_file
        # sempre encontre a chave mesmo em caso de erro antes da validação.
        "validation":       validate_json_response(""),
    }

    try:
        resp1         = call_ollama_chat(model, messages, TOOLS, temperature=TEMPERATURE)
        assistant_msg = resp1.get("message", {})
        tool_calls    = extract_tool_calls(resp1)
        result["perf_t1"] = extract_perf(resp1)

        if not tool_calls:
            result["final_response"] = assistant_msg.get("content") or ""
            result["perf_t2"]        = {}
            result["perf_total"]     = combine_perf(result["perf_t1"], {})
            # ADIÇÃO S2: validar mesmo sem tool call — o modelo pode ter
            # respondido com JSON diretamente (incomum, mas possível).
            result["validation"] = validate_json_response(result["final_response"])
            # Grounding check: JSON sem evidência de execução real não pode receber nota máxima.
            # Captura H14: modelo fabrica dados estruturalmente perfeitos sem chamar tool.
            if result["validation"]["json_acc_auto"] == 4:
                result["validation"] = dict(result["validation"], json_acc_auto=-1, grounding_fail=True)
            else:
                result["validation"].setdefault("grounding_fail", False)
            return result

        result["extra_tool_calls"] = max(0, len(tool_calls) - 1)
        tc        = tool_calls[0]
        tool_name = tc["name"]
        tool_args = tc["arguments"]
        result["tool_called"] = tool_name

        if tool_name in VALID_TOOL_NAMES:
            result["tool_valid"]    = True
            command                  = tool_args.get("command", "")
            result["tool_argument"] = command
            stdout, success          = execute_bash(command)
            result["tool_stdout"]   = stdout
            result["tool_success"]  = success
        else:
            result["tool_valid"]    = False
            result["tool_argument"] = json.dumps(tool_args)
            result["tool_stdout"]   = f"ERRO: tool '{tool_name}' não existe no ambiente."
            result["tool_success"]  = False

        messages.append({
            "role":       "assistant",
            "content":    assistant_msg.get("content") or "",
            "tool_calls": resp1["message"].get("tool_calls", [])
        })
        messages.append({
            "role":    "tool",
            "name":    tool_name,
            "content": result["tool_stdout"]
        })

        resp2 = call_ollama_chat(model, messages, TOOLS, temperature=TEMPERATURE)
        result["final_response"] = resp2.get("message", {}).get("content") or ""
        result["perf_t2"]        = extract_perf(resp2)
        result["perf_total"]     = combine_perf(result["perf_t1"], result["perf_t2"])

        # ADIÇÃO S2: validar a resposta final contra o schema S2.
        # Feito após o turno 2 para garantir que validamos a resposta final,
        # não um texto intermediário do turno 1.
        result["validation"] = validate_json_response(result["final_response"])
        result["validation"].setdefault("grounding_fail", False)

    except RuntimeError as e:
        result["error"]          = str(e)
        result["final_response"] = f"[ERRO DE API] {e}"

    return result


def _fmt_json_acc(json_acc_auto: int) -> str:
    """
    Formata o valor de json_acc_auto para exibição em arquivos e terminal.
    DECISÃO: mapeamento explícito para evitar que -1 apareça como número bruto
    sem contexto nos arquivos de resultado.
    """
    return {4: "4", 0: "0", -1: "-1 (requer avaliação manual)"}.get(
        json_acc_auto, str(json_acc_auto)
    )


def save_run_file(run_data: dict, model_safe: str, date_str: str) -> Path:
    """
    Salva o resultado de um único run S2 em arquivo texto estruturado.

    ADIÇÃO S2: seção ## VALIDAÇÃO DO JSON inserida após ## RESPOSTA FINAL
    e antes de ## PERFORMANCE — ordem lógica: contexto → resultado → validação
    do resultado → métricas de geração → erros.
    """
    filepath = RESULTS_DIR / f"S2-{model_safe}-{date_str}-run{run_data['run']}.txt"

    v               = run_data.get("validation", {})
    fields_n        = len(v.get("fields_present", []))
    fields_missing  = v.get("fields_missing", [])
    type_errors     = v.get("type_errors", [])
    missing_str     = ", ".join(fields_missing) if fields_missing else "nenhum"
    type_err_str    = "; ".join(type_errors)     if type_errors    else "nenhum"

    lines = [
        f"# S2 — Run {run_data['run']}",
        f"# Modelo         : {run_data['model']}",
        f"# Timestamp      : {run_data['timestamp']}",
        f"# Temperatura    : {TEMPERATURE}",
        f"# API            : {OLLAMA_API_URL}",
        f"# Prompt fonte   : S2-health-check-json.md seção 4",
        "#" + "-" * 60,
        "",
        "## PROMPT ENVIADO",
        "",
        S2_PROMPT,
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
        "## VALIDAÇÃO DO JSON",
        "",
        f"  json_valid      : {v.get('json_valid', False)}",
        f"  timestamp_valid : {v.get('timestamp_valid', False)}",
        f"  gpu_count       : {v.get('gpu_count', 0)}",
        f"  campos presentes: {fields_n}/{TOTAL_FIELDS + (v.get('gpu_count', 1) - 1) * len(GPU_ITEM_FIELDS)}",
        f"  campos ausentes : {missing_str}",
        f"  erros de tipo   : {type_err_str}",
        f"  texto extra     : {v.get('has_extra_text', False)}",
        f"  json_acc_auto   : {_fmt_json_acc(v.get('json_acc_auto', 0))}",
        f"  grounding_fail  : {v.get('grounding_fail', False)}",
        "",
    ]

    # Seção ## PERFORMANCE — idêntica ao S1
    p1 = run_data.get("perf_t1", {})
    p2 = run_data.get("perf_t2", {})
    pt = run_data.get("perf_total", {})

    def _f(val, spec=""):
        return _fmt_perf(val, spec)

    t2_label = "Turno 2 (tool result → resposta final)"
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
        "### Turno 1 (prompt → tool call)",
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


def save_summary(all_runs: list, model: str, model_safe: str, date_str: str) -> Path:
    """
    Gera o arquivo summary S2 com tabela estendida de validação automática.

    ADIÇÃO S2: colunas json_valid, campos, tipo_ok, ts_ok, texto_extra, JSON-ACC
    são preenchidas automaticamente pelo script.
    Colunas INST, TOOL-CON, TOOL-ACC, CON permanecem em branco para o avaliador
    humano (critérios: ADR-0001, seção 4.4 via S2-health-check-json.md seção 6).

    DECISÃO: JSON-ACC como coluna separada de INST.
    Motivo: a validade estrutural do JSON pode ser aferida automaticamente, enquanto
    INST exige julgamento sobre grau de aderência (ex.: JSON correto com texto extra
    tem JSON-ACC=-1 mas INST depende da leitura humana do contexto).
    """
    filepath = RESULTS_DIR / f"S2-{model_safe}-{date_str}-summary.md"

    lines = [
        f"# S2 Summary — {model} — {date_str}",
        "",
        "## Metadados",
        "",
        "| Campo                   | Valor                                        |",
        "|-------------------------|----------------------------------------------|",
        "| Cenário                 | S2 – Health check com parsing e JSON         |",
        f"| Modelo                  | {model}                                      |",
        "| Bateria                 | 1                                            |",
        f"| Data                    | {date_str}                                   |",
        f"| K (runs)                | {K}                                          |",
        f"| Temperatura             | {TEMPERATURE}                                |",
        f"| API                     | {OLLAMA_API_URL}                             |",
        "| Tool disponível         | run_bash                                     |",
        "| Execução real no host   | sim (subprocess)                             |",
        f"| Schema campos           | {TOTAL_FIELDS}+ (timestamp, cpu×2, memoria×4, gpus[N]×6) |",
        "| VRAM disponível início  | _(preencher manualmente)_                    |",
        "",
        "## Resultados",
        "",
        "Colunas auto: json_valid, campos, tipo_ok, ts_ok, texto_extra, JSON-ACC.",
        "Colunas manuais: INST, TOOL-CON, TOOL-ACC, CON (critérios: ADR-0001).",
        "JSON-ACC=-1: JSON parseável mas com defeito — requer avaliação humana.",
        f"Critérios: `docs/decisions/ADR-0001-criterios-de-avaliacao.md`",
        f"           `docs/benchmarks/S2-health-check-json.md`, seção 6",
        "",
        "| Run | Tool | Argumento | INST | TOOL-CON | TOOL-ACC | CON | JSON-ACC | json_valid | campos | tipo_ok | ts_ok | texto_extra | tok_total | ms_total | tok/s | thinking | Obs |",
        "|-----|------|-----------|------|----------|----------|-----|----------|------------|--------|---------|-------|-------------|-----------|----------|-------|----------|-----|",
    ]

    for r in all_runs:
        v          = r.get("validation", {})
        fields_n   = len(v.get("fields_present", []))
        tipo_ok    = not bool(v.get("type_errors"))
        ts_ok      = v.get("timestamp_valid", False)
        txt_extra  = v.get("has_extra_text", False)
        json_valid = v.get("json_valid", False)
        json_acc   = v.get("json_acc_auto", 0)

        # TOOL-ACC automático: 0 se tool inválida ou ausente (fato observável sem julgamento)
        tool_acc_auto = "0" if (r["tool_valid"] is False or r["tool_called"] == "NENHUMA") else ""

        tool_arg_short = (
            r["tool_argument"][:35] + "…"
            if len(r["tool_argument"]) > 35
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
            f"| {r['run']} | {r['tool_called']} | `{tool_arg_short}` "
            f"|      |          | {tool_acc_auto:<8} |     | {json_acc:<8} "
            f"| {str(json_valid):<10} | {fields_n}/{TOTAL_FIELDS:<5} "
            f"| {str(tipo_ok):<7} | {str(ts_ok):<5} | {str(txt_extra):<11} "
            f"| {tok:<9} | {ms:<8} | {tps:<5} | {thinking:<8} |     |"
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
        "| Run | Tool chamada | Argumento completo | Tool válida | Exec OK | Extra calls | json_acc_auto |",
        "|-----|-------------|-------------------|-------------|---------|-------------|---------------|",
    ]

    for r in all_runs:
        arg      = r["tool_argument"].replace("|", "\\|")
        v        = r.get("validation", {})
        json_acc = v.get("json_acc_auto", "N/A")
        lines.append(
            f"| {r['run']} | {r['tool_called']} | `{arg}` "
            f"| {r['tool_valid']} | {r['tool_success']} "
            f"| {r['extra_tool_calls']} | {json_acc} |"
        )

    lines += [
        "",
        "## Arquivos de runs",
        "",
    ]
    for r in all_runs:
        fn = f"S2-{model_safe}-{date_str}-run{r['run']}.txt"
        lines.append(f"- [`{fn}`]({fn})")

    lines += [
        "",
        "## Próximos passos",
        "",
        f"- [ ] Ler os {K} arquivos de run e atribuir notas na tabela acima.",
        "- [ ] Verificar manualmente os runs com json_acc_auto=-1.",
        "- [ ] Executar Bateria 2 com o mesmo script após mínimo de 12h.",
        "- [ ] Calcular STAB comparando notas das duas baterias.",
        "- [ ] Avançar para o próximo modelo da shortlist.",
        "",
        "---",
        "",
        f"_Gerado automaticamente por `scripts/run-s2-benchmark.py` em {date_str}_",
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
        print("Uso: python3 scripts/run-s2-benchmark.py <modelo>")
        print("Exemplo: python3 scripts/run-s2-benchmark.py qwen3.5:9b")
        sys.exit(1)

    model      = sys.argv[1]
    model_safe = sanitize_model_name(model)
    date_str   = datetime.date.today().isoformat()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  S2 Benchmark — Health check com parsing e JSON")
    print(f"  Modelo  : {model}")
    print(f"  Data    : {date_str}")
    print(f"  K runs  : {K}")
    print(f"  Temp    : {TEMPERATURE}")
    print(f"  Timeout : {TIMEOUT_SECONDS}s")
    print(f"  Schema  : {TOTAL_FIELDS} campos obrigatórios")
    print(f"  API     : {OLLAMA_API_URL}")
    print("=" * 60)
    print()

    all_runs = []

    for i in range(1, K + 1):
        print(f"[Run {i}/{K}] iniciando...")
        run_data = run_single_s2(model, i)
        all_runs.append(run_data)

        filepath = save_run_file(run_data, model_safe, date_str)

        status   = "OK" if run_data["error"] is None else "ERRO"
        v        = run_data.get("validation", {})
        fields_n = len(v.get("fields_present", []))
        n_errors = len(v.get("type_errors", []))
        json_acc = v.get("json_acc_auto", 0)

        # Métricas de performance (mesmo formato do S1)
        pt           = run_data.get("perf_total", {})
        p1           = run_data.get("perf_t1", {})
        p2           = run_data.get("perf_t2", {})
        th           = (p1.get("thinking_chars") or 0) + (p2.get("thinking_chars") or 0)
        thinking_str = f"sim ({th} chars)" if th > 0 else "não"

        print(f"  -> tool chamada   : {run_data['tool_called']}")
        print(f"  -> tool válida    : {run_data['tool_valid']}")
        print(f"  -> status         : {status}")
        print(f"  -> salvo em       : {filepath}")
        print(f"  -> tokens/s       : {_fmt_perf(pt.get('media_tokens_por_segundo'), '.1f')} tok/s")
        print(f"  -> tokens total   : {_fmt_perf(pt.get('total_tokens'))}")
        print(f"  -> duração        : {_fmt_perf(pt.get('total_duracao_ms'))} ms")
        print(f"  -> thinking       : {thinking_str}")
        # ADIÇÃO S2: validação do JSON por run
        print(f"  -> json válido    : {v.get('json_valid', False)}")
        print(f"  -> campos ok      : {fields_n}/{TOTAL_FIELDS}")
        print(f"  -> tipo erros     : {n_errors}")
        print(f"  -> timestamp ok   : {v.get('timestamp_valid', False)}")
        print(f"  -> texto extra    : {v.get('has_extra_text', False)}")
        print(f"  -> json_acc_auto  : {_fmt_json_acc(json_acc)}")
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
    print("  2. Verifique manualmente os runs com json_acc_auto=-1.")
    print("  3. Preencha as notas INST/TOOL-CON/TOOL-ACC/CON conforme ADR-0001.")
    print("  4. Execute novamente após 12h para a Bateria 2 (STAB).")


if __name__ == "__main__":
    main()
