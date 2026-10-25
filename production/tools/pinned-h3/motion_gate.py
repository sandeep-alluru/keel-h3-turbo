#!/usr/bin/env python3
"""motion_gate.py — refuse a "video" that is really a slideshow.

Measured on our own output: twelve cinematic shots were delivered with a mean frame difference of 0.07-0.89 while a
known-moving control sat at 3.1-3.7. Existence and duration checks passed; nothing was moving. This gate is the check
that was missing.

Thresholds are calibrated against our own clips, not invented:
  control (city walks, visibly moving): mean 3.13-3.65, p95 7.45-15.76
  static failures                     : mean 0.07-0.89, p95 0.21-2.20

R3-L2: a FROZEN frame with heavy film grain also has a big frame difference - every
pixel differs from its neighbour by a little - so a still with noise=alls=25 measured
mean 8.23 / p95 8.26 and PASSED this gate. The gate now also asks whether the
difference is STRUCTURED (a moved edge, a moving body) or white noise (grain). The
bar is 0.5: the production's own material measures 0.900-0.999, grain measures 0.02.

Usage: motion_gate.py <clip> [<clip> ...]  [--min-mean 1.5] [--min-p95 3.0]
Exit code 1 if any clip fails.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ONE implementation of the shared helpers (they were duplicated in three files).
from artifact import read_paths_file, sha256_of  # noqa: E402
from control_metrics import STRUCTURE_MIN, motion_structure  # noqa: E402

# The thresholds, as module constants: the clip renderer used to COPY them, so the
# gate and the renderer could drift (R3-OE6). There is one number now.
MOTION_MIN_MEAN = 1.5
MOTION_MIN_P95 = 3.0


def motion(path):
    cap = cv2.VideoCapture(path)
    prev, diffs = None, []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            diffs.append(float(np.abs(g - prev).mean()))
        prev = g
    cap.release()
    if not diffs:
        return 0, 0.0, 0.0
    d = np.array(diffs)
    return len(diffs) + 1, float(d.mean()), float(np.percentile(d, 95))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="*",
                    help="the clips to measure (prefer --paths-file: the gate is given paths, "
                         "never a composed name)")
    ap.add_argument("--paths-file", default=None,
                    help="a manifest (artifact.py) or a plain list of paths, one per line")
    ap.add_argument("--min-mean", type=float, default=MOTION_MIN_MEAN)
    ap.add_argument("--min-p95", type=float, default=MOTION_MIN_P95)
    args = ap.parse_args()

    # FIX 2: the gate is given the exact paths to measure.
    if args.paths_file:
        args.clips = read_paths_file(args.paths_file)
    if not args.clips:
        print("no clips to measure", file=sys.stderr)
        return 4

    failed = 0
    print(f"{'clip':40s} {'frames':>6s} {'mean':>6s} {'p95':>6s} {'struct':>7s}  verdict")
    for clip in args.clips:
        n, mean, p95 = motion(clip)
        struct, _peak = motion_structure(clip)
        ok = mean >= args.min_mean and p95 >= args.min_p95
        if ok and struct < STRUCTURE_MIN:
            # R3-L2: the movement is not movement - it is grain. Every pixel changed a
            # little and nothing else moved.
            ok = False
            reason = "FAIL — noise, not movement"
        elif not ok:
            reason = "FAIL — effectively static"
        else:
            reason = "PASS"
        if not ok:
            failed += 1
        print(f"{clip.split('/')[-1][:40]:40s} {n:6d} {mean:6.2f} {p95:6.2f} {struct:7.3f}  {reason}")
    print("\ngraded files (sha256, path):")
    for p in args.clips:
        print(f"  {(sha256_of(p) or 'UNREADABLE')[:16]}  {p}")
    if failed:
        print(f"\n{failed} clip(s) failed the motion gate. Do not deliver a still as video.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
