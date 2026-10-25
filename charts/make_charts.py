#!/usr/bin/env python3
"""make_charts.py — draw the charts straight out of the receipts.

The charts are parsed from `receipts/bench-results.md` and `receipts/bench-matrix.tsv` rather than
hard-coded, so a number that changes in a receipt changes in the chart. If a receipt is edited
without the chart being regenerated, this script says so.

Usage:
    python3 charts/make_charts.py            # writes charts/end-to-end.png, charts/per-step.png, charts/keel-ab.png
"""
from __future__ import annotations

import pathlib
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "receipts" / "bench-results.md"
MATRIX = ROOT / "receipts" / "bench-matrix.tsv"
AB_RECEIPT = ROOT / "receipts" / "our-acceleration-ab.md"
PUBLISHED = ROOT / "receipts" / "published-comparisons.md"
SIZES = ROOT / "receipts" / "checkpoint-sizes.md"
OUT = ROOT / "charts"

INK = "#e8eaed"
MUTED = "#9aa0a6"
ACCENT = "#58a6ff"
CONTROL = "#3a3f45"
WARN = "#d97706"
DPI = 150


def parse_table(text: str, header: str) -> list[tuple[str, float]]:
    """Pull a `| Config | value | ratio |` table out of the receipt markdown."""
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == header)
    except StopIteration:
        raise SystemExit(f"could not find the section header {header!r} in {RECEIPT}")

    rows: list[tuple[str, float]] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= {"-", " "}:
            continue
        match = re.search(r"([\d.]+)\s*s\b", cells[1]) or re.fullmatch(r"([\d.]+)", cells[1])
        if not match:
            continue
        rows.append((cells[0], float(match.group(1))))
    if not rows:
        raise SystemExit(f"no rows parsed from the {header!r} section")
    return rows


def parse_matrix() -> dict[str, float]:
    """The first-party matrix: config -> wall seconds."""
    rows: dict[str, float] = {}
    for line in MATRIX.read_text().splitlines()[1:]:
        cells = line.split("\t")
        if len(cells) != 6:
            continue
        rows[cells[0]] = float(cells[5])
    if not rows:
        raise SystemExit(f"no rows parsed from {MATRIX}")
    return rows


def parse_sixteen_step_accel() -> float:
    """The 16-step accelerated arm, which is corroborated by the per-step figures in the receipt."""
    text = AB_RECEIPT.read_text()
    match = re.search(r"\*\*16 steps\*\*,.*?\|\s*[\d.]+\s*s\s*\|\s*\*\*([\d.]+)\s*s\*\*", text)
    if not match:
        raise SystemExit(f"could not find the 16-step accelerated arm in {AB_RECEIPT}")
    return float(match.group(1))


def _rows_under(text: str, header: str) -> list[list[str]]:
    """Every `| ... |` row under the given table header line, as stripped cells."""
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == header)
    except StopIteration:
        raise SystemExit(f"could not find the table header {header!r}")
    rows = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if set(cells[0]) <= {"-", " ", ":"}:
            continue
        rows.append(cells)
    if not rows:
        raise SystemExit(f"no rows parsed under {header!r}")
    return rows


def _number(cell: str) -> float:
    match = re.search(r"([\d.]+)", cell.replace(",", ""))
    if not match:
        raise SystemExit(f"no number in cell {cell!r}")
    return float(match.group(1))


def parse_nvidia_pairs() -> list[tuple[str, float, float]]:
    """NVIDIA's Sol-Engine speedups table: platform -> (baseline seconds, optimized seconds)."""
    text = PUBLISHED.read_text()
    header = "| Hardware | GPUs | Workload | Baseline (s) | Optimized (s) | Speedup | Config |"
    rows = _rows_under(text, header)
    pairs = []
    for cells in rows:
        label = cells[0].replace(" (DGX Spark)", "")
        pairs.append((label, _number(cells[3]), _number(cells[4])))
    if len(pairs) < 2:
        raise SystemExit(f"expected several rows in the NVIDIA speedups table, got {len(pairs)}")
    return pairs


def parse_xmarre_e2e() -> list[tuple[str, float]]:
    """The xmarre SOL A/B, end-to-end seconds for the three published runs."""
    text = PUBLISHED.read_text()
    header = "| Run | SOL | `dense_evaluations` | Logical | Actual | Forecast | H3 sampler | End-to-end |"
    rows = _rows_under(text, header)
    wanted = {
        "metrics_00321": "SOL on, default",
        "metrics_00322": "SOL off, control",
        "metrics_00323": "SOL on, speed mode",
    }
    out = []
    for cells in rows:
        run = cells[0].strip("`")
        if run in wanted:
            out.append((wanted[run], _number(cells[7])))
    if len(out) != 3:
        raise SystemExit(f"expected 3 xmarre runs, got {len(out)}")
    order = ["SOL off, control", "SOL on, default", "SOL on, speed mode"]
    return sorted(out, key=lambda r: order.index(r[0]))


def parse_residency() -> list[tuple[str, float]]:
    """The residency ladder: DiT + encoder + both decoders, in GB, against the 121 GB a Spark shows."""
    text = SIZES.read_text()
    header = "| DiT | Encoder | + VAEs | Total (bytes) | Total (GB) | Fits 121 GB? |"
    rows = _rows_under(text, header)
    out = []
    for cells in rows:
        dit = cells[0].replace("**", "")
        label = f"{dit} + {cells[1].replace('**', '')}"
        out.append((label, _number(cells[4])))
    if len(out) < 3:
        raise SystemExit(f"expected several residency rows, got {len(out)}")
    return out


def draw(rows, title, subtitle, xlabel, out_path, highlight_last=True):
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    best = min(values)

    fig, ax = plt.subplots(figsize=(10, 0.85 * len(rows) + 2.1), dpi=DPI)
    fig.patch.set_facecolor("#111315")
    ax.set_facecolor("#111315")

    colors = []
    for value in values:
        if value == best:
            colors.append(ACCENT)
        elif highlight_last and value == values[-1]:
            colors.append(ACCENT)
        else:
            colors.append(CONTROL)
    if highlight_last and len(colors) > 1:
        colors[-1] = ACCENT

    bars = ax.barh(range(len(rows)), values, color=colors, height=0.58)
    ax.invert_yaxis()

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"{value:g} s",
            va="center",
            ha="left",
            color=INK,
            fontsize=11,
            fontfamily="monospace",
        )

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, color=INK, fontsize=9.5)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9.5)
    ax.set_title(title, color=INK, fontsize=14, fontweight="bold", loc="left", pad=22)
    ax.text(
        0,
        1.012,
        subtitle,
        transform=ax.transAxes,
        color=WARN,
        fontsize=9,
        va="bottom",
        ha="left",
    )

    ax.xaxis.grid(True, color="#25292d", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
    ax.set_xlim(0, max(values) * 1.18)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(ROOT)}")


def draw_pairs(rows, title, subtitle, xlabel, out_path, baseline_label, optimized_label):
    """Paired bars: the same workload before and after the acceleration."""
    labels = [r[0] for r in rows]
    baseline = [r[1] for r in rows]
    optimized = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(10, 0.95 * len(rows) + 2.4), dpi=DPI)
    fig.patch.set_facecolor("#111315")
    ax.set_facecolor("#111315")

    index = range(len(rows))
    ax.barh([i - 0.19 for i in index], baseline, height=0.34, color=CONTROL, label=baseline_label)
    ax.barh([i + 0.19 for i in index], optimized, height=0.34, color=ACCENT, label=optimized_label)
    ax.invert_yaxis()

    top = max(baseline)
    for i, (b, o) in enumerate(zip(baseline, optimized)):
        ax.text(b + top * 0.012, i - 0.19, f"{b:g} s", va="center", ha="left",
                color=MUTED, fontsize=9.5, fontfamily="monospace")
        ax.text(o + top * 0.012, i + 0.19, f"{o:g} s", va="center", ha="left",
                color=INK, fontsize=10, fontfamily="monospace")

    ax.set_yticks(list(index))
    ax.set_yticklabels(labels, color=INK, fontsize=9.5)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9.5)
    ax.set_title(title, color=INK, fontsize=14, fontweight="bold", loc="left", pad=22)
    ax.text(0, 1.012, subtitle, transform=ax.transAxes, color=WARN, fontsize=9, va="bottom", ha="left")

    ax.xaxis.grid(True, color="#25292d", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
    ax.set_xlim(0, top * 1.22)
    legend = ax.legend(loc="lower right", frameon=False, fontsize=9)
    for text in legend.get_texts():
        text.set_color(MUTED)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(ROOT)}")


def draw_against_limit(rows, title, subtitle, xlabel, out_path, limit, limit_label, highlight):
    """Bars measured against a hard ceiling, with the ceiling drawn in."""
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    fig, ax = plt.subplots(figsize=(10, 0.85 * len(rows) + 2.1), dpi=DPI)
    fig.patch.set_facecolor("#111315")
    ax.set_facecolor("#111315")

    colors = [ACCENT if label == highlight else CONTROL for label in labels]
    bars = ax.barh(range(len(rows)), values, color=colors, height=0.58)
    ax.invert_yaxis()

    top = max(max(values), limit) * 1.18
    for bar, value in zip(bars, values):
        ax.text(bar.get_width() + top * 0.012, bar.get_y() + bar.get_height() / 2,
                f"{value:g} GB", va="center", ha="left", color=INK, fontsize=10.5,
                fontfamily="monospace")

    ax.axvline(limit, color=WARN, linewidth=1.6, linestyle="--")
    ax.set_ylim(len(rows) + 0.25, -0.6)
    ax.text(limit, len(rows) + 0.05, limit_label, color=WARN, fontsize=9, va="center", ha="center")

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(labels, color=INK, fontsize=9.5)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9.5)
    ax.set_title(title, color=INK, fontsize=14, fontweight="bold", loc="left", pad=22)
    ax.text(0, 1.012, subtitle, transform=ax.transAxes, color=WARN, fontsize=9, va="bottom", ha="left")

    ax.xaxis.grid(True, color="#25292d", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
    ax.set_xlim(0, top)

    fig.tight_layout()
    fig.savefig(out_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(ROOT)}")


def main() -> int:
    text = RECEIPT.read_text()
    OUT.mkdir(exist_ok=True)

    e2e = parse_table(text, "## End-to-end (prompt → finished mp4)")
    per_step = parse_table(text, "## Denoising cost per step")

    provenance = (
        "Published benchmark — upstream host spark-13b3, not re-measured here. "
        "See receipts/PROVENANCE.md."
    )

    draw(
        e2e,
        "MiniMax H3 · end-to-end, prompt to finished mp4",
        provenance,
        "wall clock (seconds)",
        OUT / "end-to-end.png",
    )
    draw(
        per_step,
        "MiniMax H3 · denoising cost per step",
        provenance,
        "seconds per step",
        OUT / "per-step.png",
    )

    matrix = parse_matrix()
    accel16 = parse_sixteen_step_accel()
    draw(
        [
            ("8 steps, plain control", matrix["B1_8s_704_plain"]),
            ("8 steps, acceleration on", matrix["B4_8s_704_accel"]),
            ("16 steps, plain control", matrix["BASELINE_16s_704"]),
            ("16 steps, acceleration on", accel16),
            ("4 steps, turbo LoRA", matrix["B5_turbo4_704"]),
        ],
        "MiniMax H3 · plain control against the accelerated arm",
        "Measured on one DGX Spark, 1280x704 — wall clock includes the model load.",
        "wall clock (seconds)",
        OUT / "keel-ab.png",
        highlight_last=False,
    )

    draw_pairs(
        parse_nvidia_pairs(),
        "MiniMax H3 · NVIDIA Sol-Engine, baseline against the optimized run",
        "Published benchmark — NVlabs/Sana, branch sol-engine. Not re-measured here.",
        "wall clock (seconds)",
        OUT / "nvidia-speedups.png",
        "stock MiniMax H3",
        "Sol-Engine, full opt",
    )

    draw(
        parse_xmarre_e2e(),
        "MiniMax H3 · ComfyUI-Sol-H3, SOL off against SOL on",
        "Published benchmark — xmarre/ComfyUI-Sol-H3 on an RTX PRO 6000 (SM120). "
        "Not re-measured here.",
        "end-to-end wall clock (seconds)",
        OUT / "comfyui-sol-h3.png",
    )

    draw_against_limit(
        parse_residency(),
        "MiniMax H3 · what a weight set costs in unified memory",
        "Byte-exact sums from receipts/checkpoint-sizes.md. Measured here.",
        "denoiser + conditioner + both decoders (GB)",
        OUT / "residency.png",
        121.0,
        "121 GB — what one DGX Spark shows the runtime",
        "Pruned FP8 20.96 GB + NVFP4 15.69 GB",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
