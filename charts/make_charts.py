#!/usr/bin/env python3
"""make_charts.py — draw the ladder straight out of the receipt.

The charts are parsed from `receipts/bench-results.md` rather than hard-coded, so a number that
changes in the receipt changes in the chart. If the receipt is edited without the chart being
regenerated, this script says so.

Usage:
    python3 charts/make_charts.py            # writes charts/end-to-end.png + charts/per-step.png
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
OUT = ROOT / "charts"

INK = "#e8eaed"
MUTED = "#9aa0a6"
ACCENT = "#76b900"
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
            colors.append("#3a3f45")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
