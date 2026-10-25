#!/usr/bin/env python3
"""motion_gate.py — refuse a "video" that is really a slideshow.

Measured on our own output: twelve cinematic shots were delivered with a mean frame difference of 0.07-0.89 while a
known-moving control sat at 3.1-3.7. Existence and duration checks passed; nothing was moving. This gate is the check
that was missing.

Thresholds are calibrated against our own clips, not invented:
  control (city walks, visibly moving): mean 3.13-3.65, p95 7.45-15.76
  static failures                     : mean 0.07-0.89, p95 0.21-2.20

Usage: motion_gate.py <clip> [<clip> ...]  [--min-mean 1.5] [--min-p95 3.0]
Exit code 1 if any clip fails.
"""
import argparse
import sys

import cv2
import numpy as np


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
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--min-mean", type=float, default=1.5)
    ap.add_argument("--min-p95", type=float, default=3.0)
    args = ap.parse_args()

    failed = 0
    print(f"{'clip':40s} {'frames':>6s} {'mean':>6s} {'p95':>6s}  verdict")
    for clip in args.clips:
        n, mean, p95 = motion(clip)
        ok = mean >= args.min_mean and p95 >= args.min_p95
        if not ok:
            failed += 1
        print(f"{clip.split('/')[-1][:40]:40s} {n:6d} {mean:6.2f} {p95:6.2f}  "
              f"{'PASS' if ok else 'FAIL — effectively static'}")
    if failed:
        print(f"\n{failed} clip(s) failed the motion gate. Do not deliver a still as video.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
