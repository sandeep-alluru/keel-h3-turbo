#!/usr/bin/env python3
"""Face-embedding identity metric (InsightFace buffalo_l, cosine similarity).

Used by EXP-1/EXP-4 to answer one question with a number: does the generated video keep the
reference face? Compares every sampled frame of a clip against the approved anchor.

Usage:
    face_metric.py --anchor anchor.png --clip clip.mp4 [--frames 5] [--out receipt.json]

Reports mean / min cosine across sampled frames, plus per-frame values and the detected face box.
"""

import argparse
import json
import os
import tempfile

import cv2
import numpy as np


def load_embedder():
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    return app


def embed(app, image):
    faces = app.get(image)
    if not faces:
        return None, None
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    emb = face.normed_embedding
    return emb, [float(v) for v in face.bbox]


def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--frames", type=int, default=5)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    app = load_embedder()

    anchor_img = cv2.imread(args.anchor)
    if anchor_img is None:
        raise SystemExit(f"cannot read anchor {args.anchor}")
    anchor_emb, anchor_box = embed(app, anchor_img)
    if anchor_emb is None:
        raise SystemExit("no face detected in the anchor")

    cap = cv2.VideoCapture(args.clip)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    picks = [int(round(i * (total - 1) / max(1, args.frames - 1))) for i in range(args.frames)]

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for idx in picks:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue
            path = os.path.join(tmp, f"f{idx}.png")
            cv2.imwrite(path, frame)
            emb, box = embed(app, frame)
            rows.append({
                "frame": idx,
                "cosine": None if emb is None else round(cosine(anchor_emb, emb), 4),
                "face_box": box,
            })
    cap.release()

    values = [r["cosine"] for r in rows if r["cosine"] is not None]
    receipt = {
        "anchor": os.path.abspath(args.anchor),
        "clip": os.path.abspath(args.clip),
        "model": "insightface buffalo_l",
        "frames_sampled": len(rows),
        "frames_with_face": len(values),
        "cosine_mean": round(float(np.mean(values)), 4) if values else None,
        "cosine_min": round(float(np.min(values)), 4) if values else None,
        "per_frame": rows,
        "pass": bool(values and float(np.mean(values)) >= 0.85 and float(np.min(values)) >= 0.80),
    }
    print(json.dumps({k: receipt[k] for k in
                      ("frames_with_face", "cosine_mean", "cosine_min", "pass")}, indent=2))
    if args.out:
        with open(args.out, "w") as handle:
            json.dump(receipt, handle, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
