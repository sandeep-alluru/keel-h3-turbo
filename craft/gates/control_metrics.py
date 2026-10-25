#!/usr/bin/env python3
"""control_metrics.py — choreography fidelity instrument for the H3 production.

Why this exists: the production's recurring defect is a shot that performs one plausible action and
stops ("the soldier shot the bullet only once; it should show blast action"). A motion-mean
gate never sees that — a shot with one trigger and a shot with six distinct events can carry
the same mean. What differs is the *shape* of motion over time: where the events are.

So this measures the shape, not the amount:

  motion signature  per-frame mean absolute grey difference, normalised to [0,1]
  event peaks       local maxima in the smoothed signature, with a minimum separation
  signature r       Pearson correlation of two signatures on a common time grid
  event timing      matched peaks -> mean |dt| in seconds
  event count       distinct events each clip shows

Usage:
  control_metrics.py --profile CLIP.mp4                 # signature stats + event times
  control_metrics.py SOURCE.mp4 GENERATED.mp4 [--json]  # choreography comparison
  control_metrics.py --profile A.mp4 --profile B.mp4    # several profiles

Read-only. CPU only. Touches nothing else.
"""

import argparse
import json
import sys

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    sys.exit("control_metrics.py needs cv2 (opencv-python) on this box")


def read_grey(path, width=320):
    """Decode a clip to a list of float32 grey frames, downscaled for speed."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"control_metrics: unable to open {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 24.0)
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = grey.shape[:2]
        nw = width
        nh = max(1, int(round(h * width / w)))
        grey = cv2.resize(grey, (nw, nh), interpolation=cv2.INTER_AREA)
        frames.append(grey.astype(np.float32))
    cap.release()
    if len(frames) < 3:
        raise SystemExit(f"control_metrics: {path} has only {len(frames)} frames")
    return frames, (fps if fps > 1 else 24.0)


def signature(frames):
    """Per-frame mean absolute grey difference, normalised to [0,1]."""
    out = []
    for i in range(1, len(frames)):
        out.append(float(np.mean(np.abs(frames[i] - frames[i - 1]))) / 255.0)
    return np.asarray(out, dtype=np.float64)


def smooth(x, k=3):
    if k <= 1 or len(x) < k:
        return x
    pad = k // 2
    xp = np.pad(x, (pad, pad), mode="edge")
    return np.convolve(xp, np.ones(k) / k, mode="valid")[: len(x)]


def find_peaks(sig, min_sep_frames=4, rel=0.5, rel_max=0.45, abs_floor=0.015):
    """Local maxima of the smoothed signature that clear three bars.

    Bar 1 (adaptive): median + rel * (p90 - median) — finds candidates in any clip's own
        energy range.
    Bar 2 (relative to the clip's own peak): a candidate must reach rel_max of the strongest
        moment in the clip.
    Bar 3 (absolute): a candidate must also clear abs_floor in normalised grey difference.
        Bars 1 and 2 alone were not enough: bridge-S1 (motion mean 0.008) reported seven
        "events" whose amplitudes were all ~0.011 — noise. The absolute bar sits just above
        the motion gate's own "this is moving" line (p95 >= 3.0/255 = 0.0118), so an event
        is by definition a moment of real movement.
    """
    if len(sig) < 3:
        return []
    s = smooth(sig, 3)
    med = float(np.median(s))
    p90 = float(np.percentile(s, 90))
    thr = med + rel * max(p90 - med, 1e-6)
    floor = max(rel_max * float(s.max()), abs_floor)
    peaks = []
    for i in range(1, len(s) - 1):
        if s[i] >= thr and s[i] >= floor and s[i] > s[i - 1] and s[i] >= s[i + 1]:
            if peaks and (i - peaks[-1]) < min_sep_frames:
                if s[i] > s[peaks[-1]]:
                    peaks[-1] = i
                continue
            peaks.append(i)
    return peaks


def znorm(x):
    x = np.asarray(x, dtype=np.float64)
    sd = float(x.std())
    if sd < 1e-9:
        return np.zeros_like(x)
    return (x - x.mean()) / sd


def to_grid(sig, fps, grid):
    """Resample a signature onto a common time grid (seconds) for a fair correlation."""
    if len(sig) == 0:
        return np.zeros(len(grid))
    t = np.arange(len(sig)) / float(fps)
    return np.interp(grid, t, sig, left=sig[0], right=sig[-1])


def pearson(a, b):
    n = min(len(a), len(b))
    if n < 3:
        return float("nan")
    a = a[:n] - a[:n].mean()
    b = b[:n] - b[:n].mean()
    da = float(np.sqrt((a * a).sum()))
    db = float(np.sqrt((b * b).sum()))
    if da < 1e-9 or db < 1e-9:
        return float("nan")
    return float((a * b).sum() / (da * db))


def match_peaks(pa, pb, fps_a, fps_b, tol_s=0.6):
    """Greedy in-order matching of event peaks. Returns (matched, mean_abs_dt, pairs)."""
    ta = [p / fps_a for p in pa]
    tb = [p / fps_b for p in pb]
    used = set()
    pairs = []
    for t in ta:
        best, bd = None, tol_s
        for j, u in enumerate(tb):
            if j in used:
                continue
            d = abs(u - t)
            if d <= bd:
                bd, best = d, j
        if best is not None:
            used.add(best)
            pairs.append({"t_a": round(t, 3), "t_b": round(tb[best], 3), "dt": round(bd, 3)})
    dts = [p["dt"] for p in pairs]
    return len(pairs), (float(np.mean(dts)) if dts else float("nan")), pairs


def profile(path, width=320):
    frames, fps = read_grey(path, width)
    sig = signature(frames)
    peaks = find_peaks(sig)
    return {
        "path": path,
        "fps": round(fps, 3),
        "frames": len(frames),
        "duration_s": round(len(frames) / fps, 3),
        "motion_mean": round(float(sig.mean()), 5),
        "motion_p95": round(float(np.percentile(sig, 95)), 5),
        "motion_max": round(float(sig.max()), 5),
        "events": len(peaks),
        "event_times_s": [round(p / fps, 3) for p in peaks],
        "event_amplitudes": [round(float(sig[p]), 5) for p in peaks],
    }


def compare(src_path, gen_path, width=320, tol_s=0.6):
    sf, s_fps = read_grey(src_path, width)
    gf, g_fps = read_grey(gen_path, width)
    s_sig = signature(sf)
    g_sig = signature(gf)

    dur = min(len(s_sig) / s_fps, len(g_sig) / g_fps)
    grid = np.arange(0, dur, 1.0 / 24.0)
    gs = to_grid(s_sig, s_fps, grid)
    gg = to_grid(g_sig, g_fps, grid)
    # Shape correlation: z-normalised so the two clips may differ in energy and still be
    # compared on the shape of their motion over time (where the events are).
    r = pearson(znorm(gs), znorm(gg))
    r_raw = pearson(gs, gg)

    s_peaks = find_peaks(s_sig)
    g_peaks = find_peaks(g_sig)
    matched, mean_dt, pairs = match_peaks(s_peaks, g_peaks, s_fps, g_fps, tol_s)

    return {
        "source": profile(src_path, width),
        "generated": profile(gen_path, width),
        "signature_r": None if r != r else round(r, 4),
        "signature_r_raw_energy": None if r_raw != r_raw else round(r_raw, 4),
        "events_source": len(s_peaks),
        "events_generated": len(g_peaks),
        "events_matched": matched,
        "event_timing_mean_dt_s": None if mean_dt != mean_dt else round(mean_dt, 3),
        "event_pairs": pairs,
        "motion_ratio_gen_over_src": round(
            float(g_sig.mean() / s_sig.mean()), 3) if s_sig.mean() > 0 else None,
    }


def timeline(path, width=320, bucket_s=1.0):
    """Per-second motion energy — shows *where* in a clip the movement actually is."""
    frames, fps = read_grey(path, width)
    sig = signature(frames)
    n = max(1, int(round(bucket_s * fps)))
    rows = []
    for i in range(0, len(sig), n):
        chunk = sig[i:i + n]
        if len(chunk) == 0:
            continue
        rows.append((i / fps, float(chunk.mean()), float(chunk.max())))
    return rows


# The bar for "the movement is STRUCTURED, not noise" (R3-L2).
#
# A frozen frame with heavy film grain differs from its neighbour in EVERY pixel by a
# little, so a plain frame-difference metric calls it movement: a still with
# noise=alls=25 measured peak motion 0.0162 - above the aliveness floor - and passed
# the motion gate at mean 8.23 / p95 8.26. No frame-difference THRESHOLD can separate
# that from a fast uniform camera move, because they are the same number.
#
# What separates them is the SPATIAL STRUCTURE of the difference image. A moved edge,
# a moving body or a pan produce a difference image whose neighbours differ together
# (lag-1 autocorrelation near 1). Film grain produces white noise (autocorrelation near
# 0), and the autocorrelation NEVER cares how strong the grain is - white noise is
# white noise at any amplitude. Measured on the production's own material:
#
#   the 15-clip delivered library      0.930 - 0.999
#   the production's rendered spans     0.901 - 0.985
#   the cellular-automaton fixture     0.154
#   grain (alls=25, temporal)          0.011
#
# So the bar is 0.10: an order of magnitude below every real clip, an order of
# magnitude above white noise, and clear of the production's own synthetic source.
STRUCTURE_MIN = 0.10


def motion_structure(path, width=320):
    """(autocorrelation, peak_mean_difference) for the busiest frame pair in the clip.

    The lag-1 spatial autocorrelation of the frame difference image: how much a pixel's
    change resembles its neighbour's change. One number, shared by the motion gate and
    the aliveness gate (R3-L2, R3-OE6: one implementation of a shared helper).
    """
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(path)
    prev, best = None, (0.0, 0.0)
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            d = np.abs(g - prev)
            mean = float(d.mean())
            if mean > best[1]:
                x = d - d.mean()
                den = float((x * x).mean()) or 1e-9
                best = (float((x[:, :-1] * x[:, 1:]).mean()) / den, mean)
        prev = g
    cap.release()
    return best[0], best[1]


def sparkline(rows, width=60):
    if not rows:
        return ""
    vals = [r[1] for r in rows]
    hi = max(vals) or 1.0
    blocks = " .:-=+*#%@"
    out = []
    for v in vals:
        idx = min(len(blocks) - 1, int(v / hi * (len(blocks) - 1)))
        out.append(blocks[idx])
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="*", help="SOURCE GENERATED for a comparison")
    ap.add_argument("--profile", action="append", default=[],
                    help="profile one clip (signature stats + event times); repeatable")
    ap.add_argument("--timeline", action="append", default=[],
                    help="per-second motion energy for one clip; repeatable")
    ap.add_argument("--width", type=int, default=320, help="analysis width in px (default 320)")
    ap.add_argument("--tol", type=float, default=0.6, help="peak match tolerance in seconds")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    out = {"profiles": [profile(p, args.width) for p in args.profile]}

    if args.timeline:
        out["timelines"] = []
        for p in args.timeline:
            rows = timeline(p, args.width)
            out["timelines"].append({"path": p, "buckets": len(rows),
                                     "sparkline": sparkline(rows)})

    if len(args.clips) == 2:
        out["comparison"] = compare(args.clips[0], args.clips[1], args.width, args.tol)
    elif len(args.clips) == 1:
        out["profiles"].append(profile(args.clips[0], args.width))
    elif len(args.clips) > 2:
        raise SystemExit("give exactly two clips for a comparison")

    if args.json:
        print(json.dumps(out, indent=2))
        return

    for p in out["profiles"]:
        print(f"\n== {p['path']}")
        print(f"   {p['frames']}f @ {p['fps']}fps  ({p['duration_s']}s)")
        print(f"   motion mean {p['motion_mean']:.5f}  p95 {p['motion_p95']:.5f}  max {p['motion_max']:.5f}")
        print(f"   events: {p['events']} at {p['event_times_s']}")
        if p.get("event_amplitudes"):
            print(f"   event amplitudes: {p['event_amplitudes']}")

    for p in out.get("timelines", []):
        print(f"\n== {p['path']}  ({p['buckets']}s buckets)")
        print(f"   {p['sparkline']}")
        print("   (each char = 1s of motion energy, low -> high)")

    c = out.get("comparison")
    if c:
        print("\n== choreography comparison")
        print(f"   signature r        : {c['signature_r']}")
        print(f"   events source/gen  : {c['events_source']} / {c['events_generated']}"
              f"  (matched {c['events_matched']})")
        print(f"   event timing |dt|  : {c['event_timing_mean_dt_s']} s")
        print(f"   motion gen/source  : {c['motion_ratio_gen_over_src']}")
        for p in c["event_pairs"]:
            print(f"     src {p['t_a']:.3f}s -> gen {p['t_b']:.3f}s  (dt {p['dt']:.3f}s)")


if __name__ == "__main__":
    main()
