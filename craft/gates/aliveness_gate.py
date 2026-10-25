#!/usr/bin/env python3
"""aliveness_gate.py — a video-level liveness gate.

motion_gate.py asks "does this clip move at all" — it catches a still photo shipped as
video (mean >= 1.5/255, p95 >= 3.0/255). It never catches a video that moves for five
seconds and then holds a frame for the other twenty-five. That defect shipped:

  CITY-mara-solene-30s.mp4   alive in only 16.1 % of its seconds
  MARA-G-approved-keys-30s    alive in only 12.9 % of its seconds

while the other thirteen delivered videos sit at 42-65 %. A 30-second video that is alive
for five seconds is a five-second video with padding.

Criterion: a delivered video must be alive (per-second motion energy >= 25 % of that
clip's own peak) in at least 35 % of its duration. 35 % is set from the measured
distribution of the delivered library: it passes thirteen of fifteen videos and rejects
exactly the two dead ones. A shot-level rule is separate — a 5 s shot must show at least
two discrete events, which control_metrics.py reports.

Usage:
  aliveness_gate.py CLIP.mp4 [CLIP.mp4 ...] [--min-alive 0.35] [--json]
  aliveness_gate.py --dir h3-clips --min-alive 0.35
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from control_metrics import timeline  # noqa: E402


def aliveness(path, bucket_s=1.0, width=320):
    rows = timeline(path, width, bucket_s)
    if not rows:
        raise SystemExit(f"aliveness_gate: no frames in {path}")
    vals = [r[1] for r in rows]
    peak = max(vals) or 1e-9
    alive = sum(1 for v in vals if v >= 0.25 * peak) / len(vals)
    quiet = sum(1 for v in vals if v >= 0.10 * peak) / len(vals)
    return {
        "path": path,
        "duration_s": round(len(rows) * bucket_s, 2),
        "alive_frac": round(alive, 4),
        "alive_frac_10pct": round(quiet, 4),
        "peak_motion": round(peak, 5),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="*")
    ap.add_argument("--dir", default=None, help="scan every mp4 in this directory")
    ap.add_argument("--min-alive", type=float, default=0.35)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files = list(args.clips)
    if args.dir:
        files += sorted(glob.glob(os.path.join(args.dir, "*.mp4")))
    if not files:
        raise SystemExit("give clips or --dir")

    rows = []
    rejected = []
    for f in files:
        r = aliveness(f)
        r["verdict"] = "PASS" if r["alive_frac"] >= args.min_alive else "REJECT — mostly still"
        rows.append(r)
        if r["verdict"].startswith("REJECT"):
            rejected.append(r)

    if args.json:
        print(json.dumps({"min_alive": args.min_alive, "clips": rows}, indent=2))
    else:
        print(f"{'clip':<40} {'alive':>7} {'(>=10%)':>9} {'dur':>6}  verdict")
        for r in rows:
            print(f"{os.path.basename(r['path']):<40} {r['alive_frac']*100:>6.1f}% "
                  f"{r['alive_frac_10pct']*100:>8.1f}% {r['duration_s']:>6}  {r['verdict']}")

    if rejected:
        print(f"\n{len(rejected)} clip(s) are mostly still — do not deliver them as video.")
        raise SystemExit(1)
    print(f"\nall {len(rows)} clip(s) alive in at least {args.min_alive*100:.0f}% of their duration")


if __name__ == "__main__":
    main()
