#!/usr/bin/env python3
"""
generate-stats.py — Parse benchmark summary files and generate statistics + plots.

Outputs:
  results/stats/raw-data.csv
  results/stats/throughput-stats.csv
  results/stats/latency-stats.csv
  results/stats/stab-delta.csv
  results/plots/plot-throughput.png
  results/plots/plot-latency.png
  results/plots/plot-stab-delta.png
  results/plots/plot-latency-vs-throughput.png
"""

import re
import sys
from pathlib import Path
from typing import Optional

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

APPROVED_MODELS: frozenset[str] = frozenset({
    "gemma4:e4b",
    "qwen3.5:9b",
    "qwen3:14b",
    "llama3.1:8b",
    "llama3-groq-tool-use:8b",
})

# Scenarios where latency is in ms_total column (repeat-run scenarios)
MS_TOTAL_SCENARIOS: frozenset[str] = frozenset({"S1", "S2", "S2B"})

MODEL_COLORS: dict[str, str] = {
    "gemma4:e4b": "#388E3C",
    "qwen3.5:9b": "#1976D2",
    "qwen3:14b": "#0D47A1",
    "llama3.1:8b": "#F57C00",
    "llama3-groq-tool-use:8b": "#BF360C",
}

MODEL_LABELS: dict[str, str] = {
    "gemma4:e4b": "gemma4:e4b",
    "qwen3.5:9b": "qwen3.5:9b",
    "qwen3:14b": "qwen3:14b",
    "llama3.1:8b": "llama3.1:8b",
    "llama3-groq-tool-use:8b": "llama3-groq",
}

REPO_ROOT = Path(__file__).parent.parent
BENCHMARKS_DIR = REPO_ROOT / "results" / "benchmarks"
STATS_DIR = REPO_ROOT / "results" / "stats"
PLOTS_DIR = REPO_ROOT / "results" / "plots"

# CORREÇÃO 1: Regex com escape duplo incorreto corrigida para raw string
SCENARIO_RE = re.compile(r"^(S[0-9]+(?:B(?:v2)?)?)-(.+)-(\d{4}-\d{2}-\d{2})-summary$")
TAG_RE = re.compile(r"^[0-9a-z]+$")


# ── Parsing ────────────────────────────────────────────────────────────────────


def parse_filename(path: Path) -> Optional[dict]:
    """Return {scenario, model, date, path} or None if the filename doesn't match."""
    m = SCENARIO_RE.match(path.stem)
    if not m:
        return None
    scenario, model_raw, date = m.group(1), m.group(2), m.group(3)
    # Convert filename separator back to ollama tag format: e.g. llama3-groq-tool-use-8b → llama3-groq-tool-use:8b
    parts = model_raw.rsplit("-", 1)
    model = f"{parts[0]}:{parts[1]}" if len(parts) == 2 and TAG_RE.match(parts[1]) else model_raw
    return {"scenario": scenario, "model": model, "date": date, "path": path}


def parse_results_table(text: str) -> list[dict]:
    """Extract the markdown table from the ## Resultados section."""
    lines = text.splitlines()

    # Advance to ## Resultados
    start = next((i for i, l in enumerate(lines) if l.strip().startswith("## Resultados")), None)
    if start is None:
        return []
    lines = lines[start:]

    # Collect contiguous pipe-delimited lines (first table found)
    table_lines: list[str] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and "|" in stripped[1:]:
            in_table = True
            table_lines.append(stripped)
        elif in_table:
            break  # first blank or non-table line ends the table

    if len(table_lines) < 3:  # header + separator + ≥1 data row
        return []

    header = [h.strip() for h in table_lines[0].split("|")[1:-1]]
    rows = []
    for line in table_lines[2:]:  # skip separator row
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return rows


def to_float(value: str) -> Optional[float]:
    try:
        # Remover milissegundos se houver
        clean_value = value.replace("ms", "").strip()
        return float(clean_value)
    except (ValueError, TypeError):
        return None


def load_summary(info: dict, date_map: dict) -> list[dict]:
    scenario: str = info["scenario"]
    model: str = info["model"]
    date: str = info["date"]
    path: Path = info["path"]

    rows = parse_results_table(path.read_text())
    if not rows:
        return []

    latency_col = "ms_total" if scenario in MS_TOTAL_SCENARIOS else "ms"
    
    # CORREÇÃO: Lógica de battery baseada no mapeamento de datas por modelo
    # REGRAS S4: Forçar battery=1 para todos os cenários S4 (S4 e S4Bv2)
    if scenario.startswith("S4"):
        battery = 1
    else:
        dates = date_map.get(model, [date])
        try:
            battery = dates.index(date) + 1
        except ValueError:
            battery = 1

    records = []
    for idx, row in enumerate(rows):
        tok_s = to_float(row.get("tok/s", ""))
        ms_val = to_float(row.get(latency_col, ""))
        if tok_s is None or ms_val is None:
            continue
        run_key = row.get("Run") or row.get("Case") or str(idx + 1)
        records.append({
            "scenario": scenario,
            "model": model,
            "date": date,
            "battery": battery,
            "run_or_case": run_key,
            "run_index": idx + 1,
            "tok_s": tok_s,
            "ms": ms_val,
        })
    return records


def filter_cold_start(records: list[dict], scenario: str) -> list[dict]:
    """Exclude run index 1 for repeat-run scenarios (model cold-start artefact)."""
    if scenario in MS_TOTAL_SCENARIOS:
        return [r for r in records if r["run_index"] != 1]
    return records


# ── Statistics ─────────────────────────────────────────────────────────────────


def compute_stats(records: list[dict]) -> dict:
    toks = [r["tok_s"] for r in records]
    ms = [r["ms"] for r in records]
    return {
        "n": len(records),
        "mean_toks": float(np.mean(toks)),
        "stdev_toks": float(np.std(toks, ddof=1)) if len(toks) > 1 else 0.0,
        "mean_ms": float(np.mean(ms)),
        "stdev_ms": float(np.std(ms, ddof=1)) if len(ms) > 1 else 0.0,
    }


# ── Plotting ───────────────────────────────────────────────────────────────────


def _model_bar_positions(
    models: list[str],
    scenarios: list[str],
) -> tuple[np.ndarray, float]:
    bar_width = 0.8 / max(len(models), 1)
    x = np.arange(len(scenarios))
    return x, bar_width


def plot_grouped_bars(
    df: pd.DataFrame,
    y_col: str,
    err_col: str,
    title: str,
    ylabel: str,
    out_path: Path,
    models: list[str],
    scenarios: list[str],
) -> None:
    if not models or not scenarios:
        return

    x, bar_width = _model_bar_positions(models, scenarios)
    fig, ax = plt.subplots(figsize=(max(10, len(scenarios) * 1.8), 6))

    for i, model in enumerate(models):
        offsets = x + (i - len(models) / 2 + 0.5) * bar_width
        means = []
        errs = []
        for scenario in scenarios:
            row = df[(df["model"] == model) & (df["scenario"] == scenario)]
            if row.empty:
                means.append(0.0)
                errs.append(0.0)
            else:
                means.append(float(row.iloc[0][y_col]))
                errs.append(float(row.iloc[0][err_col]))

        ax.bar(
            offsets, means, bar_width * 0.9,
            yerr=errs,
            color=MODEL_COLORS.get(model, "#999999"),
            label=MODEL_LABELS.get(model, model),
            capsize=3,
            error_kw={"linewidth": 1.0},
        )

    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved {out_path.name}")


def plot_stab_delta(
    df: pd.DataFrame,
    y_col: str,
    title: str,
    ylabel: str,
    out_path: Path,
    models: list[str],
    scenarios: list[str],
) -> None:
    if not models or not scenarios:
        return

    x, bar_width = _model_bar_positions(models, scenarios)
    fig, ax = plt.subplots(figsize=(max(10, len(scenarios) * 1.8), 6))

    for i, model in enumerate(models):
        offsets = x + (i - len(models) / 2 + 0.5) * bar_width
        values = []
        for scenario in scenarios:
            row = df[(df["model"] == model) & (df["scenario"] == scenario)]
            val = float(row.iloc[0][y_col]) if not row.empty and row.iloc[0][y_col] is not None else 0.0
            values.append(val)

        bars = ax.bar(
            offsets, values, bar_width * 0.9,
            color=MODEL_COLORS.get(model, "#999999"),
            label=MODEL_LABELS.get(model, model),
        )
        for bar, val in zip(bars, values):
            bar.set_alpha(0.85 if val >= 0 else 0.55)

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved {out_path.name}")


SCATTER_MARKERS = ["o", "s", "^", "D", "v", "P", "*", "X", "h"]


def plot_scatter(
    df: pd.DataFrame,
    out_path: Path,
    models: list[str],
    scenarios: list[str],
) -> None:
    if df.empty:
        return

    scenario_markers = {s: SCATTER_MARKERS[i % len(SCATTER_MARKERS)] for i, s in enumerate(scenarios)}
    fig, ax = plt.subplots(figsize=(9, 6))

    # CORREÇÃO 3: Adicionar jitter horizontal para separar pontos sobrepostos
    # Jitter de ±2% do range do eixo X
    x_range = df["mean_ms"].max() - df["mean_ms"].min()
    if x_range == 0: x_range = 1000 # fallback
    jitter_strength = 0.02 * x_range
    
    model_jitter = {model: (i - len(models)/2) * jitter_strength for i, model in enumerate(models)}

    for model in models:
        mdf = df[df["model"] == model]
        jitter = model_jitter[model]
        for _, row in mdf.iterrows():
            ax.scatter(
                row["mean_ms"] + jitter, row["mean_toks"],
                color=MODEL_COLORS.get(model, "#999999"),
                marker=scenario_markers.get(row["scenario"], "o"),
                s=80, zorder=3, alpha=0.8
            )

    model_patches = [
        mpatches.Patch(color=MODEL_COLORS.get(m, "#999999"), label=MODEL_LABELS.get(m, m))
        for m in models
    ]
    scenario_handles = [
        plt.Line2D(
            [0], [0],
            marker=scenario_markers.get(s, "o"),
            color="gray", markersize=7, linestyle="None", label=s,
        )
        for s in scenarios
    ]

    leg1 = ax.legend(handles=model_patches, loc="lower left", fontsize=8, title="Modelo")
    ax.add_artist(leg1)
    ax.legend(handles=scenario_handles, loc="upper right", fontsize=8, title="Cenário")

    ax.set_xlabel("Latência média (ms) [com jitter para visualização]")
    ax.set_ylabel("Throughput médio (tok/s)")
    ax.set_title("Latência vs Throughput — Bateria 1 (Run 1 excluído)")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved {out_path.name}")


# ── Main ───────────────────────────────────────────────────────────────────────


def main() -> None:
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # CORREÇÃO: Pré-scan para descobrir datas por modelo
    print("=== Pré-scan de arquivos ===")
    all_summary_files = sorted(BENCHMARKS_DIR.glob("*-summary.md"))
    model_dates = {}
    for path in all_summary_files:
        info = parse_filename(path)
        if info and info["model"] in APPROVED_MODELS:
            model = info["model"]
            date = info["date"]
            if model not in model_dates:
                model_dates[model] = set()
            model_dates[model].add(date)
    
    date_map = {m: sorted(list(d)) for m, d in model_dates.items()}
    for m, dates in date_map.items():
        print(f"  {m}: {len(dates)} data(s) encontrada(s) {dates}")

    print("\n=== Carregando arquivos de summary ===")
    all_records: list[dict] = []

    # Diagnóstico de parsing
    total_files = 0
    parsed_files = 0

    for path in all_summary_files:
        total_files += 1
        info = parse_filename(path)
        if info is None:
            print(f"  SKIP (nome inválido): {path.name}", file=sys.stderr)
            continue
        if info["model"] not in APPROVED_MODELS:
            print(f"  SKIP (modelo não aprovado): {path.name} ({info['model']})", file=sys.stderr)
            continue

        records = load_summary(info, date_map)
        if not records:
            print(f"  WARN (sem dados): {path.name}", file=sys.stderr)
            continue

        all_records.extend(records)
        parsed_files += 1
        print(f"  OK  {path.name}  →  {len(records)} linhas")

    print(f"\nArquivos processados: {parsed_files} de {total_files}")

    if not all_records:
        print("ERRO: nenhum dado encontrado.", file=sys.stderr)
        sys.exit(1)

    df_raw = pd.DataFrame(all_records)

    # ── CSV 1: raw data ────────────────────────────────────────────────────────
    df_raw.to_csv(STATS_DIR / "raw-data.csv", index=False)
    print(f"\nSalvo: raw-data.csv  ({len(df_raw)} linhas)")

    # ── CSV 2 & 3: aggregated stats (excluding Run 1 for S1/S2/S2B) ───────────
    stats_rows: list[dict] = []
    for (model, scenario, battery), group in df_raw.groupby(["model", "scenario", "battery"]):
        filtered = filter_cold_start(group.to_dict("records"), scenario)
        if not filtered:
            continue
        s = compute_stats(filtered)
        stats_rows.append({"model": model, "scenario": scenario, "battery": battery, **s})

    df_stats = pd.DataFrame(stats_rows)

    df_stats[["model", "scenario", "battery", "n", "mean_toks", "stdev_toks"]].to_csv(
        STATS_DIR / "throughput-stats.csv", index=False
    )
    df_stats[["model", "scenario", "battery", "n", "mean_ms", "stdev_ms"]].to_csv(
        STATS_DIR / "latency-stats.csv", index=False
    )
    print(f"Salvo: throughput-stats.csv  ({len(df_stats)} linhas)")
    print(f"Salvo: latency-stats.csv  ({len(df_stats)} linhas)")

    # ── CSV 4: STAB delta (B2 − B1) ───────────────────────────────────────────
    # CORREÇÃO 2: Diagnóstico de cálculo STAB
    print("\n=== Diagnóstico STAB ===")
    stab_rows: list[dict] = []
    for (model, scenario), group in df_stats.groupby(["model", "scenario"]):
        b1 = group[group["battery"] == 1]
        b2 = group[group["battery"] == 2]
        if b1.empty or b2.empty:
            continue
        b1r, b2r = b1.iloc[0], b2.iloc[0]
        
        b1_mean_toks = b1r["mean_toks"]
        b2_mean_toks = b2r["mean_toks"]
        delta_pct = (b2_mean_toks - b1_mean_toks) / b1_mean_toks * 100
        
        print(f"  {model} @ {scenario}: B1={b1_mean_toks:.2f}, B2={b2_mean_toks:.2f}, Δ={delta_pct:.2f}%")
        
        stab_rows.append({
            "model": model,
            "scenario": scenario,
            "b1_mean_toks": b1_mean_toks,
            "b2_mean_toks": b2_mean_toks,
            "delta_toks": b2_mean_toks - b1_mean_toks,
            "delta_toks_pct": delta_pct,
            "b1_mean_ms": b1r["mean_ms"],
            "b2_mean_ms": b2r["mean_ms"],
            "delta_ms": b2r["mean_ms"] - b1r["mean_ms"],
            "delta_ms_pct": (b2r["mean_ms"] - b1r["mean_ms"]) / b1r["mean_ms"] * 100,
        })

    df_stab = pd.DataFrame(stab_rows) if stab_rows else pd.DataFrame()
    df_stab.to_csv(STATS_DIR / "stab-delta.csv", index=False)
    print(f"Salvo: stab-delta.csv  ({len(df_stab)} linhas)")

    # ── Plots ──────────────────────────────────────────────────────────────────
    print("\n=== Gerando gráficos ===")

    models = sorted(APPROVED_MODELS & set(df_stats["model"].unique()))
    scenarios = sorted(df_stats["scenario"].unique())
    df_b1 = df_stats[df_stats["battery"] == 1]

    plot_grouped_bars(
        df_b1,
        y_col="mean_toks", err_col="stdev_toks",
        title="Throughput por cenário — Bateria 1 (Run 1 excluído)",
        ylabel="tok/s",
        out_path=PLOTS_DIR / "plot-throughput.png",
        models=models, scenarios=scenarios,
    )

    plot_grouped_bars(
        df_b1,
        y_col="mean_ms", err_col="stdev_ms",
        title="Latência por cenário — Bateria 1 (Run 1 excluído)",
        ylabel="ms",
        out_path=PLOTS_DIR / "plot-latency.png",
        models=models, scenarios=scenarios,
    )

    if not df_stab.empty:
        stab_scenarios = sorted(df_stab["scenario"].unique())
        plot_stab_delta(
            df_stab,
            y_col="delta_toks_pct",
            title="STAB: variação de throughput — Bateria 2 vs Bateria 1 (%)",
            ylabel="Δ tok/s (%)",
            out_path=PLOTS_DIR / "plot-stab-delta.png",
            models=models, scenarios=stab_scenarios,
        )
    else:
        print("  SKIP plot-stab-delta.png (sem dados STAB com ambas as baterias)")

    plot_scatter(
        df_b1,
        out_path=PLOTS_DIR / "plot-latency-vs-throughput.png",
        models=models, scenarios=scenarios,
    )

    print("\nConcluído.")
    print(f"  Stats: {STATS_DIR}")
    print(f"  Plots: {PLOTS_DIR}")


if __name__ == "__main__":
    main()
