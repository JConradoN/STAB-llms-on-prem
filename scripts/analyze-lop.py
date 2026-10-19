#!/usr/bin/env python3
"""
LOP Analysis — extrai métricas auto-computadas dos summaries S1/S2/S3/S4
e gera ranking comparativo dos modelos.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

BENCHMARKS = Path(__file__).parent.parent / "results" / "benchmarks"
REPORTS = Path(__file__).parent.parent / "results" / "reports"

# Canonical model name mapping (normaliza variações de nome)
MODEL_ALIASES = {
    "gemma4-e4b": "gemma4:e4b",
    "gemma4-e4b-it-q4_K_M": "gemma4:e4b-q4km",
    "gemma4-e4b-it-q8_0": "gemma4:e4b-q8",
    "gemma4-26b": "gemma4:26b",
    "gemma4-26b-a4b-it-q4_K_M": "gemma4:26b-q4km",
    "gemma4-12b-unsloth-q4km": "gemma4:12b-unsloth",
    "hf.co_unsloth_gemma-4-12b-it-GGUF-Q4_K_M": "gemma4:12b-unsloth(hf)",
    "granite4.1-3b": "granite4.1:3b",
    "granite4.1-8b": "granite4.1:8b",
    "granite4.1-8b-ctx16k": "granite4.1:8b-ctx16k",
    "granite4.1-30b": "granite4.1:30b",
    "qwen3-8b": "qwen3:8b",
    "qwen3-14b": "qwen3:14b",
    "qwen3-14b-q8_0": "qwen3:14b-q8",
    "qwen3-30b-a3b": "qwen3:30b-a3b",
    "qwen3.5-2b": "qwen3.5:2b",
    "qwen3.5-4b": "qwen3.5:4b",
    "qwen3.5-9b": "qwen3.5:9b",
    "qwen3.6-27b": "qwen3.6:27b",
    "phi4-14b": "phi4:14b",
    "devstral-small-2-24b": "devstral-small-2:24b",
    "lfm2.5-8b": "lfm2.5:8b",
    "lfm2-24b-a2b": "lfm2:24b-a2b",
    "llama3.1-8b": "llama3.1:8b",
    "llama3-groq-tool-use-8b": "llama3-groq:8b",
    "ministral-3-8b": "ministral:8b",
    "ministral-3-14b": "ministral:14b",
    "mistral-7b": "mistral:7b",
    "glm-4.7-flash-q4_K_M": "glm-4.7-flash",
    "rnj-1-8b": "rnj-1:8b",
}


def normalize_model(raw: str) -> str:
    return MODEL_ALIASES.get(raw, raw.replace("-", ":"))


def parse_s1_summary(path: Path) -> dict:
    """S1: CLI text mode — check if model consistently said ERRO or produced output."""
    text = path.read_text()
    runs_dir = path.parent
    model_slug = re.search(r"S1-(.+?)-\d{4}-\d{2}-\d{2}-summary", path.name)
    if not model_slug:
        return {}
    slug = model_slug.group(1)
    date = re.search(r"(\d{4}-\d{2}-\d{2})", path.name).group(1)

    # Parse tok/s from summary table
    tok_s_vals = re.findall(r"\|\s*\d+\s*\|\s*[\w\/~.]+.*?\|\s*([\d.]+)\s*\|", text)
    # Try to extract from Resultados table
    rows = re.findall(r"\|\s*(\d+)\s*\|.*?\|\s*([\d.]+)\s*\|\s*\d+\s*\|", text)

    # Count runs that hit ERRO pattern in run files
    run_files = sorted(runs_dir.glob(f"S1-{slug}-{date}-run*.txt"))
    total = len(run_files)
    erro_count = 0
    tool_called = 0
    tok_s_list = []

    for rf in run_files:
        content = rf.read_text()
        if "ERRO: não consegui executar health.sh" in content:
            erro_count += 1
        # Check if tool was actually invoked (old API runs have tool_valid)
        if "Tool válida: True" in content or "run_bash" in content.lower():
            tool_called += 1
        # Extract tok/s
        m = re.search(r"tok/s\s*[=:]\s*([\d.]+)", content)
        if m:
            tok_s_list.append(float(m.group(1)))

    # Extract tok/s from summary table (S1 CLI runs have different format)
    # Look for the results table in summary
    table_rows = re.findall(
        r"\|\s*\d\s*\|[^|]*\|[^|]*\|\s*[\d.]+\s*\|\s*[\d.]+\s*\|\s*([\d.]+)\s*\|",
        text,
    )
    if table_rows:
        tok_s_list = [float(x) for x in table_rows]

    avg_toks = sum(tok_s_list) / len(tok_s_list) if tok_s_list else None

    # S1 score: did model obey instruction?
    # ERRO = correct (can't execute), but we check consistency
    # "ERRO" across all runs = TOOL-CON=4 (consistent), INST=4 (followed protocol)
    # Producing fake output = bad
    if total == 0:
        return {}

    erro_rate = erro_count / total

    return {
        "scenario": "S1",
        "model_slug": slug,
        "date": date,
        "total_runs": total,
        "erro_rate": erro_rate,
        "tool_called_rate": tool_called / total if total else 0,
        "avg_tok_s": avg_toks,
        # Derived score: consistency of correct response
        "s1_consistency": round(erro_rate * 4, 1),  # 4 = all said ERRO correctly
    }


def parse_s2_summary(path: Path) -> dict:
    """S2: API + tool call + JSON output."""
    text = path.read_text()
    model_slug = re.search(r"S2-(.+?)-\d{4}-\d{2}-\d{2}-summary", path.name)
    if not model_slug:
        return {}

    # Extract auto rows from Observações brutas table
    # Format: | Run | Tool | Argumento | Tool válida | Exec OK | Extra calls | json_acc_auto |
    obs_rows = re.findall(
        r"\|\s*\d\s*\|\s*(\w+)\s*\|[^|]+\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(\d+)\s*\|\s*([\d-]+)\s*\|",
        text,
    )

    # Extract results table rows
    # Format: | Run | Tool | Arg | INST | TOOL-CON | TOOL-ACC | CON | JSON-ACC | json_valid | campos | tipo_ok | ts_ok | texto_extra | ...
    result_rows = re.findall(
        r"\|\s*\d\s*\|[^|]+\|[^|]+\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*([\d-]+)\s*\|\s*(True|False)\s*\|\s*([\d/]+)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|",
        text,
    )

    json_acc_vals = []
    tool_valid_count = 0
    exec_ok_count = 0
    total = 0
    avg_tok_s = None
    campos_ok = 0

    for row in obs_rows:
        tool, tool_valid, exec_ok, extra, json_acc = row
        total += 1
        if tool_valid == "True":
            tool_valid_count += 1
        if exec_ok == "True":
            exec_ok_count += 1
        try:
            json_acc_vals.append(int(json_acc))
        except ValueError:
            pass

    if not json_acc_vals and result_rows:
        for row in result_rows:
            json_acc, json_valid, campos, tipo_ok, ts_ok, texto_extra = row
            total += 1
            try:
                json_acc_vals.append(int(json_acc))
            except ValueError:
                pass
            campos_match = re.match(r"(\d+)/(\d+)", campos)
            if campos_match:
                campos_ok += int(campos_match.group(1)) == int(campos_match.group(2))

    # Extract tok/s from results table
    tok_s_matches = re.findall(
        r"\|\s*\d\s*\|[^|]+\|[^|]+(?:\|[^|]+){10,}\|\s*([\d.]+)\s*\|\s*\d+\s*\|",
        text,
    )
    if tok_s_matches:
        try:
            avg_tok_s = sum(float(x) for x in tok_s_matches) / len(tok_s_matches)
        except ValueError:
            pass

    if total == 0:
        return {}

    avg_json_acc = sum(json_acc_vals) / len(json_acc_vals) if json_acc_vals else None

    return {
        "scenario": "S2",
        "model_slug": model_slug.group(1),
        "date": re.search(r"(\d{4}-\d{2}-\d{2})", path.name).group(1),
        "total_runs": total,
        "tool_valid_rate": tool_valid_count / total if total else 0,
        "exec_ok_rate": exec_ok_count / total if total else 0,
        "avg_json_acc": avg_json_acc,
        "avg_tok_s": avg_tok_s,
    }


def parse_s3_summary(path: Path) -> dict:
    """S3: Log classification + JSON output."""
    text = path.read_text()
    model_slug = re.search(r"S3-(.+?)-\d{4}-\d{2}-\d{2}-summary", path.name)
    if not model_slug:
        return {}

    # Extract from Observações brutas
    # Format: | Case | Tool | Argumento | Tool válida | Leitura OK | Extra calls | class_acc_auto | parse_acc_auto |
    obs_rows = re.findall(
        r"\|\s*\w+-\w+\s*\|\s*(\w+)\s*\|[^|]+\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(\d+)\s*\|\s*([\d]+)\s*\|\s*([\d]+)\s*\|",
        text,
    )

    # Also extract from results table
    # Format: | case | Tool | Path | CLASS-ACC | PARSE-ACC | json_valid | severity | primary_ok | secondary_ok | req_action_ok | summary_ok | ...
    result_rows = re.findall(
        r"\|\s*\w+-\d+\s*\|[^|]+\|[^|]+\|\s*([\d]+)\s*\|\s*([\d]+)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|",
        text,
    )

    class_acc_vals = []
    parse_acc_vals = []
    tool_valid_count = 0
    total = 0
    avg_tok_s = None

    for row in obs_rows:
        tool, tool_valid, read_ok, extra, class_acc, parse_acc = row
        total += 1
        if tool_valid == "True":
            tool_valid_count += 1
        class_acc_vals.append(int(class_acc))
        parse_acc_vals.append(int(parse_acc))

    if not class_acc_vals and result_rows:
        for row in result_rows:
            class_acc, parse_acc, *rest = row
            total += 1
            class_acc_vals.append(int(class_acc))
            parse_acc_vals.append(int(parse_acc))

    # tok/s from results table
    tok_s_matches = re.findall(
        r"\|\s*\w+-\d+\s*\|[^|]+\|[^|]+(?:\|[^|]+){8,}\|\s*([\d.]+)\s*\|\s*\d+\s*\|",
        text,
    )
    if tok_s_matches:
        try:
            avg_tok_s = sum(float(x) for x in tok_s_matches) / len(tok_s_matches)
        except ValueError:
            pass

    if total == 0:
        return {}

    return {
        "scenario": "S3",
        "model_slug": model_slug.group(1),
        "date": re.search(r"(\d{4}-\d{2}-\d{2})", path.name).group(1),
        "total_cases": total,
        "tool_valid_rate": tool_valid_count / total if total else 0,
        "avg_class_acc": sum(class_acc_vals) / len(class_acc_vals) if class_acc_vals else None,
        "avg_parse_acc": sum(parse_acc_vals) / len(parse_acc_vals) if parse_acc_vals else None,
        "avg_tok_s": avg_tok_s,
    }


def parse_s4_summary(path: Path) -> dict:
    """S4: Multi-log triage + escalation decision."""
    text = path.read_text()
    model_slug = re.search(r"S4-(.+?)-\d{4}-\d{2}-\d{2}-summary", path.name)
    if not model_slug:
        return {}

    # Observações brutas
    # Format: | Case | read_file calls | loop_exhausted | triage_acc_auto | chain_acc | all_hosts | rank_ok | esc_ok |
    obs_rows = re.findall(
        r"\|\s*S4-[ABC]\s*\|\s*(\d+)\s*\|\s*(True|False)\s*\|\s*([\d]+)\s*\|\s*([\d]+)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|",
        text,
    )

    # Results table
    # Format: | Case | TRIAGE-ACC | CHAIN-ACC | schema_valid | all_hosts | rank_ok | esc_ok | acao_geral | read_file_calls | ...
    result_rows = re.findall(
        r"\|\s*S4-[ABC]\s*\|\s*([\d]+)\s*\|\s*([\d]+)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(True|False)\s*\|\s*(\d+)\s*\|",
        text,
    )

    triage_acc_vals = []
    chain_acc_vals = []
    rf_calls = []
    loop_exhausted_count = 0
    total = 0
    avg_tok_s = None

    for row in obs_rows:
        rf, loop_ex, triage_acc, chain_acc, all_hosts, rank_ok, esc_ok = row
        total += 1
        rf_calls.append(int(rf))
        if loop_ex == "True":
            loop_exhausted_count += 1
        triage_acc_vals.append(int(triage_acc))
        chain_acc_vals.append(int(chain_acc))

    if not triage_acc_vals and result_rows:
        for row in result_rows:
            triage_acc, chain_acc, schema_valid, all_hosts, rank_ok, esc_ok, acao_geral, rf = row
            total += 1
            triage_acc_vals.append(int(triage_acc))
            chain_acc_vals.append(int(chain_acc))
            rf_calls.append(int(rf))

    # tok/s from results table
    tok_s_matches = re.findall(
        r"\|\s*S4-[ABC]\s*(?:\|[^|]+){8,}\|\s*([\d.]+)\s*\|\s*\d+\s*\|",
        text,
    )
    if tok_s_matches:
        try:
            avg_tok_s = sum(float(x) for x in tok_s_matches) / len(tok_s_matches)
        except ValueError:
            pass

    if total == 0:
        return {}

    avg_rf = sum(rf_calls) / len(rf_calls) if rf_calls else 0
    # Expected: 3 read_file calls per case. chain_acc = 4 if all 3 called
    chain_complete_rate = sum(1 for r in rf_calls if r >= 3) / total if total else 0

    return {
        "scenario": "S4",
        "model_slug": model_slug.group(1),
        "date": re.search(r"(\d{4}-\d{2}-\d{2})", path.name).group(1),
        "total_cases": total,
        "avg_triage_acc": sum(triage_acc_vals) / len(triage_acc_vals) if triage_acc_vals else None,
        "avg_chain_acc": sum(chain_acc_vals) / len(chain_acc_vals) if chain_acc_vals else None,
        "avg_rf_calls": avg_rf,
        "chain_complete_rate": chain_complete_rate,
        "loop_exhausted_rate": loop_exhausted_count / total if total else 0,
        "avg_tok_s": avg_tok_s,
    }


def get_latest(records: list[dict]) -> dict | None:
    """Return the most recent record by date."""
    if not records:
        return None
    return sorted(records, key=lambda x: x.get("date", ""), reverse=True)[0]


def main():
    # Collect all summaries
    data = defaultdict(lambda: {"S1": [], "S2": [], "S3": [], "S4": []})

    for f in sorted(BENCHMARKS.glob("S1-*-summary.md")):
        r = parse_s1_summary(f)
        if r:
            data[r["model_slug"]]["S1"].append(r)

    for f in sorted(BENCHMARKS.glob("S2-*-summary.md")):
        r = parse_s2_summary(f)
        if r:
            data[r["model_slug"]]["S2"].append(r)

    for f in sorted(BENCHMARKS.glob("S3-*-summary.md")):
        r = parse_s3_summary(f)
        if r:
            data[r["model_slug"]]["S3"].append(r)

    for f in sorted(BENCHMARKS.glob("S4-*-summary.md")):
        r = parse_s4_summary(f)
        if r:
            data[r["model_slug"]]["S4"].append(r)

    # Build ranking table
    rows = []
    for slug, scenarios in data.items():
        s1 = get_latest(scenarios["S1"])
        s2 = get_latest(scenarios["S2"])
        s3 = get_latest(scenarios["S3"])
        s4 = get_latest(scenarios["S4"])

        model = normalize_model(slug)

        # Scores (0–4 scale)
        s1_score = s1.get("s1_consistency", None) if s1 else None
        s2_score = s2.get("avg_json_acc", None) if s2 else None
        s3_score = s3.get("avg_class_acc", None) if s3 else None
        s4_score = s4.get("avg_triage_acc", None) if s4 else None

        # Composite: average of available scores
        scores = [x for x in [s1_score, s2_score, s3_score, s4_score] if x is not None]
        composite = round(sum(scores) / len(scores), 2) if scores else None

        # Tool chaining (S4 chain_complete_rate)
        chain = s4.get("chain_complete_rate", None) if s4 else None

        # Speed (best available)
        toks = [
            x.get("avg_tok_s") for x in [s1, s2, s3, s4]
            if x and x.get("avg_tok_s") is not None
        ]
        avg_speed = round(sum(toks) / len(toks), 1) if toks else None

        rows.append({
            "model": model,
            "slug": slug,
            "S1": round(s1_score, 2) if s1_score is not None else "-",
            "S2": round(s2_score, 2) if s2_score is not None else "-",
            "S3": round(s3_score, 2) if s3_score is not None else "-",
            "S4": round(s4_score, 2) if s4_score is not None else "-",
            "composite": composite if composite is not None else "-",
            "chain_ok": f"{chain:.0%}" if chain is not None else "-",
            "tok_s": avg_speed if avg_speed is not None else "-",
            "scenarios_covered": len(scores),
        })

    # Sort by composite desc, then by coverage
    rows.sort(key=lambda x: (
        x["scenarios_covered"],
        float(x["composite"]) if x["composite"] != "-" else 0,
    ), reverse=True)

    # Print report
    print("=" * 100)
    print("LOP — ANÁLISE COMPARATIVA (métricas auto-computadas, escala 0–4)")
    print("=" * 100)
    print(f"\n{'Modelo':<32} {'S1':>5} {'S2':>5} {'S3':>5} {'S4':>5} {'Comp':>6} {'Chain':>7} {'tok/s':>7} {'Cob':>4}")
    print("-" * 100)
    for r in rows:
        print(
            f"{r['model']:<32} {str(r['S1']):>5} {str(r['S2']):>5} "
            f"{str(r['S3']):>5} {str(r['S4']):>5} {str(r['composite']):>6} "
            f"{str(r['chain_ok']):>7} {str(r['tok_s']):>7} {r['scenarios_covered']:>4}"
        )

    print("\nLegenda:")
    print("  S1=consistência ERRO correta  S2=JSON-ACC  S3=CLASS-ACC  S4=TRIAGE-ACC")
    print("  Comp=média dos 4  Chain=S4 tool-chain completo (3 read_file/caso)")
    print("  Cob=quantos cenários têm dados\n")

    # S2 tool-use detail
    print("=" * 100)
    print("S2 — TOOL USE DETAIL (exec_ok_rate, tool_valid_rate)")
    print("=" * 100)
    print(f"\n{'Modelo':<32} {'Tool%':>7} {'ExecOK%':>8} {'JSON-ACC':>9}")
    print("-" * 60)
    for slug, scenarios in sorted(data.items()):
        s2 = get_latest(scenarios["S2"])
        if not s2:
            continue
        model = normalize_model(slug)
        print(
            f"{model:<32} {s2.get('tool_valid_rate', 0):>7.0%} "
            f"{s2.get('exec_ok_rate', 0):>8.0%} "
            f"{s2.get('avg_json_acc', 0):>9.2f}"
        )

    # S3 detail
    print("\n" + "=" * 100)
    print("S3 — CLASSIFICATION DETAIL")
    print("=" * 100)
    print(f"\n{'Modelo':<32} {'CLASS-ACC':>10} {'PARSE-ACC':>10} {'tok/s':>7}")
    print("-" * 65)
    for slug, scenarios in sorted(data.items()):
        s3 = get_latest(scenarios["S3"])
        if not s3:
            continue
        model = normalize_model(slug)
        print(
            f"{model:<32} {s3.get('avg_class_acc', 0):>10.2f} "
            f"{s3.get('avg_parse_acc', 0):>10.2f} "
            f"{s3.get('avg_tok_s', 0) or 0:>7.1f}"
        )

    # S4 detail
    print("\n" + "=" * 100)
    print("S4 — TRIAGE DETAIL (tool chaining)")
    print("=" * 100)
    print(f"\n{'Modelo':<32} {'TRIAGE-ACC':>11} {'CHAIN-ACC':>10} {'RF-calls/caso':>14} {'Loop%':>6} {'tok/s':>7}")
    print("-" * 85)
    for slug, scenarios in sorted(data.items()):
        s4 = get_latest(scenarios["S4"])
        if not s4:
            continue
        model = normalize_model(slug)
        print(
            f"{model:<32} {s4.get('avg_triage_acc', 0):>11.2f} "
            f"{s4.get('avg_chain_acc', 0):>10.2f} "
            f"{s4.get('avg_rf_calls', 0):>14.1f} "
            f"{s4.get('loop_exhausted_rate', 0):>6.0%} "
            f"{s4.get('avg_tok_s', 0) or 0:>7.1f}"
        )

    # Save full report
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "lop-bateria-final-analise.md"
    lines = []
    lines.append("# LOP — Análise Bateria Final (jun/2026)\n\n")
    lines.append("> Métricas extraídas automaticamente dos summaries S1–S4.\n")
    lines.append("> S1=consistência ERRO | S2=JSON-ACC | S3=CLASS-ACC | S4=TRIAGE-ACC (escala 0–4)\n\n")
    lines.append("## Ranking Geral\n\n")
    lines.append(f"| {'Modelo':<30} | S1 | S2 | S3 | S4 | Comp | Chain | tok/s | Cob |\n")
    lines.append(f"|{'-'*32}|----|----|----|----|----|-------|-------|-----|\n")
    for r in rows:
        lines.append(
            f"| {r['model']:<30} | {str(r['S1']):>4} | {str(r['S2']):>4} | "
            f"{str(r['S3']):>4} | {str(r['S4']):>4} | {str(r['composite']):>4} | "
            f"{str(r['chain_ok']):>5} | {str(r['tok_s']):>5} | {r['scenarios_covered']} |\n"
        )
    out.write_text("".join(lines))
    print(f"\n✓ Relatório salvo: {out}")


if __name__ == "__main__":
    main()
