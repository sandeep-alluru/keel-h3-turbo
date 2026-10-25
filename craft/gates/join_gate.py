#!/usr/bin/env python3
"""join_gate.py — measure the seams on a delivered film.

H3 renders a short clip at a time, and a film is several of those clips put together. The
seam between two clips is where a film breaks, so the seam is measured on the delivered file
rather than on the shots: the re-encode shifts the luma, and a cut can land a frame late.

Where the cuts are, from two independent detectors:
  * PySceneDetect's ContentDetector, threshold 27.0;
  * ffmpeg's own scene filter, threshold 0.4.
The film's cuts are the union of what both found.

At every boundary, on a fixed 240x240 canvas:
  * palette correlation — the two frames share a place and a light  (bar: at least 0.35)
  * luma jump          — the exposure steps between them             (bar: at most 45)

The brightness track comes from ffmpeg's signalstats filter, one YAVG per frame, averaged
over six frames either side of the cut.

Usage: join_gate.py <film> [<film> ...] [--json <path>]
Exit code 1 if any boundary sits outside the bars.
Exit code 2 if a measurement could not run.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

PALETTE_BAR = 0.35
LUMA_JUMP_BAR = 45.0
BRIGHTNESS_WINDOW = 6
CONTENT_THRESHOLD = 27.0
FFMPEG_SCENE_THRESHOLD = 0.4
CANVAS = (240, 240)


def _which(name):
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def brightness_track(film):
    """The per-frame brightness of the file, from ffmpeg's signalstats filter.

    Returns (yavg, ymin, ymax): three lists, one entry per frame, in frame order.
    """
    if not _which("ffmpeg"):
        return None, None, None
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-v", "error", "-i", film,
           "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    except Exception:
        return None, None, None
    yavg, ymin, ymax = [], [], []
    for line in (out.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("lavfi.signalstats.YAVG="):
            yavg.append(float(line.split("=", 1)[1]))
        elif line.startswith("lavfi.signalstats.YMIN="):
            ymin.append(float(line.split("=", 1)[1]))
        elif line.startswith("lavfi.signalstats.YMAX="):
            ymax.append(float(line.split("=", 1)[1]))
    if not yavg:
        return None, None, None
    return yavg, ymin, ymax


def pyscenedetect_cuts(film, threshold=CONTENT_THRESHOLD):
    """The cut times PySceneDetect finds in the file."""
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
    except Exception:
        return None, "pyscenedetect (not installed)"
    try:
        video = open_video(film)
        manager = SceneManager()
        manager.add_detector(ContentDetector(threshold=threshold))
        manager.detect_scenes(video)
        scenes = manager.get_scene_list()
    except Exception as exc:
        return None, "pyscenedetect (%s)" % exc
    cuts = []
    for start, _end in scenes[1:]:
        try:
            cuts.append(round(float(start.get_seconds()), 3))
        except Exception:
            cuts.append(round(float(start), 3))
    return cuts, "pyscenedetect"


def ffmpeg_cuts(film, threshold=FFMPEG_SCENE_THRESHOLD):
    """The cut times ffmpeg's own scene detector finds — a second, independent opinion."""
    if not _which("ffmpeg"):
        return None, "ffmpeg (not installed)"
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", film,
           "-filter:v", "select='gt(scene,%.2f)',showinfo" % threshold, "-f", "null", "-"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    except Exception:
        return None, "ffmpeg (did not run)"
    times = []
    for match in re.finditer(r"pts_time:([0-9.]+)", out.stderr or ""):
        times.append(round(float(match.group(1)), 3))
    return times, "ffmpeg"


def frame_at(film, index):
    """One frame of the file, decoded from the file itself, on the fixed canvas."""
    import cv2
    cap = cv2.VideoCapture(film)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(index))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    return cv2.resize(frame, CANVAS, interpolation=cv2.INTER_AREA)


def luma(img):
    import cv2
    return float(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean())


def palette_corr(a, b):
    """Correlation of colour histograms (0..1). High = same place and light."""
    import cv2
    import numpy as np

    def hist(img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
        cv2.normalize(h, h)
        return h.flatten()

    ha, hb = hist(a), hist(b)
    return float(np.dot(ha, hb))


def measure(film, fps=24.0):
    """Measure every seam of a delivered film."""
    import hashlib

    receipt = {
        "film": os.path.basename(film),
        "verdict": "ERROR",
        "reason": "",
        "measured_on": "the delivered file itself",
        "bars": {"palette_corr_min": PALETTE_BAR, "luma_jump_max": LUMA_JUMP_BAR},
        "boundaries": [],
    }
    if not os.path.isfile(film):
        receipt["reason"] = "the file is not there: %s" % film
        return receipt

    # The palette correlation moves a little between OpenCV releases, so the version
    # is part of the receipt: a number without it sits beside a number measured
    # elsewhere rather than beside the same measurement.
    try:
        import cv2
        receipt["opencv_version"] = cv2.__version__
    except Exception:
        receipt["opencv_version"] = "not available"

    digest = hashlib.sha256()
    with open(film, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    receipt["sha256"] = digest.hexdigest()
    receipt["bytes"] = os.path.getsize(film)

    yavg, _ymin, _ymax = brightness_track(film)
    if not yavg:
        receipt["reason"] = "the ffmpeg signalstats brightness track could not be produced"
        return receipt
    receipt["frames_in_track"] = len(yavg)

    cuts_ps, tool_ps = pyscenedetect_cuts(film)
    cuts_ff, tool_ff = ffmpeg_cuts(film)
    receipt["cuts"] = {
        "pyscenedetect": {"tool": tool_ps, "times": cuts_ps},
        "ffmpeg": {"tool": tool_ff, "times": cuts_ff},
    }
    if cuts_ps is None and cuts_ff is None:
        receipt["cuts_found"] = 0
        receipt["breaks"] = 0
        receipt["verdict"] = "UNCERTAIN"
        receipt["reason"] = ("neither cut detector could run on this file "
                             "(pyscenedetect: %s; ffmpeg: %s) - the seams were not measured"
                             % (tool_ps, tool_ff))
        return receipt
    if cuts_ps is None:
        cuts_ps, tool_ps = cuts_ff, tool_ff
    elif cuts_ff:
        cuts_ps = sorted(set(cuts_ps) | set(cuts_ff))
    if not cuts_ps:
        receipt["cuts_found"] = 0
        receipt["breaks"] = 0
        receipt["verdict"] = "PASS"
        receipt["reason"] = "no cut was found in the file - there are no seams to measure"
        return receipt

    boundaries = []
    for cut in cuts_ps:
        index = int(round(cut * fps))
        before = [yavg[i] for i in range(max(0, index - BRIGHTNESS_WINDOW), index) if i < len(yavg)]
        after = [yavg[i] for i in range(index, min(len(yavg), index + BRIGHTNESS_WINDOW))]
        signal_out = sum(before) / len(before) if before else None
        signal_in = sum(after) / len(after) if after else None
        signal_jump = (abs(signal_in - signal_out)
                       if signal_out is not None and signal_in is not None else None)

        frame_out = frame_at(film, max(0, index - 1))
        frame_in = frame_at(film, index)
        palette = palette_corr(frame_out, frame_in) if frame_out is not None and frame_in is not None else None
        cv2_jump = (abs(luma(frame_in) - luma(frame_out))
                    if frame_out is not None and frame_in is not None else None)

        within = True
        reasons = []
        if palette is None or cv2_jump is None:
            within = False
            reasons.append("the frames either side could not be read")
        else:
            if palette < PALETTE_BAR:
                within = False
                reasons.append("palette %.4f below %.2f" % (palette, PALETTE_BAR))
            if cv2_jump > LUMA_JUMP_BAR:
                within = False
                reasons.append("luma jump %.2f above %.1f" % (cv2_jump, LUMA_JUMP_BAR))

        boundaries.append({
            "time_s": cut,
            "frame": index,
            "palette_corr": palette,
            "cv2_luma_jump": cv2_jump,
            "signalstats_luma_jump": signal_jump,
            "within_bars": within,
            "reasons": reasons,
        })

    breaks = sum(1 for b in boundaries if not b["within_bars"])
    receipt["cuts_found"] = len(boundaries)
    receipt["breaks"] = breaks
    receipt["boundaries"] = boundaries
    receipt["verdict"] = "PASS" if breaks == 0 else "REJECT"
    receipt["reason"] = ("%d boundary/boundaries measured, %d outside the bars"
                         % (len(boundaries), breaks))
    return receipt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("films", nargs="+")
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--json", default=None, help="write the receipts to this path")
    args = ap.parse_args()

    receipts = []
    print(f"{'film':44s} {'cuts':>5s} {'breaks':>7s}  verdict")
    for film in args.films:
        receipt = measure(film, fps=args.fps)
        receipts.append(receipt)
        print(f"{os.path.basename(film):44s} {receipt.get('cuts_found', 0):5d} "
              f"{receipt.get('breaks', 0):7d}  {receipt['verdict']} — {receipt['reason']}")
        for boundary in receipt.get("boundaries", []):
            print("    boundary at %8.3f s (frame %4d): palette %s, luma jump %s, signalstats %s"
                  % (boundary["time_s"], boundary["frame"],
                     _fmt(boundary["palette_corr"]), _fmt(boundary["cv2_luma_jump"]),
                     _fmt(boundary["signalstats_luma_jump"]))
                  + ("  — " + "; ".join(boundary["reasons"]) if boundary["reasons"] else ""))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"films": receipts}, fh, indent=2)
        print("receipts written to %s" % args.json)

    rejected = sum(1 for r in receipts if r["verdict"] == "REJECT")
    errored = sum(1 for r in receipts if r["verdict"] in ("ERROR", "UNCERTAIN"))
    if errored:
        return 2
    return 1 if rejected else 0


def _fmt(value):
    return "-" if value is None else ("%.4f" % value if abs(value) < 10 else "%.2f" % value)


if __name__ == "__main__":
    sys.exit(main())
