#!/usr/bin/env python3
"""Benchmark charts for the SM121 MiniMax-H3 stack.

All numbers are measured on one DGX Spark (GB10, sm_121), 864x480, 124 frames,
20 steps, res_multistep/simple, cool chip with no competing GPU process.
Single series per chart -> no legend box; every bar is direct-labeled.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).parent

# categorical slot 1 (validated palette), light / dark steps
BLUE = {"light": "#2a78d6", "dark": "#3987e5"}
ACCENT = {"light": "#1baf7a", "dark": "#199e70"}   # slot 3, for the winning row
SURFACE = {"light": "#fcfcfb", "dark": "#1a1a19"}
INK = {"light": "#0b0b0b", "dark": "#ffffff"}
MUTED = {"light": "#52514e", "dark": "#c3c2b7"}

# (label, seconds-per-step) — dense first, best last
PER_STEP = [
    ("Dense (stock ComfyUI)", 14.40),
    ("+ Sol-Attn (kijai)", 11.11),
    ("+ Sol-Attn (KingGore)", 10.88),
    ("+ FirstBlockCache only", 9.72),
    ("+ Full stack", 8.39),
]
# (label, end-to-end wall seconds)
E2E = [
    ("Dense (stock ComfyUI)", 312.7),
    ("+ FirstBlockCache only", 215.7),
    ("+ Full stack", 202.5),
]


def barchart(rows, baseline, title, subtitle, xlabel, fname, mode, unit="s"):
    surface, ink, muted = SURFACE[mode], INK[mode], MUTED[mode]
    labels = [r[0] for r in rows][::-1]
    values = [r[1] for r in rows][::-1]
    # highlight the best (fastest) row; everything else is the primary series hue
    best = min(values)
    colors = [ACCENT[mode] if v == best else BLUE[mode] for v in values]

    fig, ax = plt.subplots(figsize=(9, 0.62 * len(rows) + 2.0), dpi=200)
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)

    bars = ax.barh(labels, values, height=0.52, color=colors, zorder=3)

    for bar, v in zip(bars, values):
        speedup = baseline / v
        txt = f"{v:.2f} {unit}" if unit == "s/step" else f"{v:.1f} {unit}"
        if speedup > 1.005:
            txt += f"   {speedup:.2f}x"
        ax.text(v + max(values) * 0.015, bar.get_y() + bar.get_height() / 2,
                txt, va="center", ha="left", color=ink, fontsize=10.5,
                fontweight="medium")

    ax.set_xlim(0, max(values) * 1.30)
    ax.xaxis.grid(True, color=muted, alpha=0.18, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.yaxis.grid(False)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0, colors=ink, labelsize=10.5)
    ax.tick_params(axis="x", length=0, colors=muted, labelsize=9)
    ax.set_xlabel(xlabel, color=muted, fontsize=9.5, labelpad=8)

    ax.set_title(title, color=ink, fontsize=13.5, fontweight="semibold",
                 loc="left", pad=22)
    ax.text(0, 1.035, subtitle, transform=ax.transAxes, color=muted,
            fontsize=9.5, va="bottom", ha="left")

    fig.tight_layout()
    suffix = "" if mode == "light" else "-dark"
    fig.savefig(OUT / f"{fname}{suffix}.png", facecolor=surface,
                bbox_inches="tight", pad_inches=0.28)
    plt.close(fig)


for mode in ("light", "dark"):
    barchart(PER_STEP, 14.40,
             "Denoising cost per step",
             "MiniMax-H3 · 864x480 · 124 frames · 20 steps · 1x DGX Spark (GB10, sm_121)",
             "seconds per step  (lower is better)",
             "per-step", mode, unit="s/step")
    barchart(E2E, 312.7,
             "End-to-end render time, 5-second clip with audio",
             "MiniMax-H3 · 864x480 · 124 frames · 20 steps · 1x DGX Spark (GB10, sm_121)",
             "seconds, prompt to finished mp4  (lower is better)",
             "end-to-end", mode)

print("wrote:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))
