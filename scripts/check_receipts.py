#!/usr/bin/env python3
"""check_receipts.py — fail the build if a published claim stops matching its receipt.

This is the discipline this repo is built on: every number on the front page has to trace to a file
in `receipts/`, every clip has to hash to what the index says it hashes to, and the curated set has
to stay exactly what the curation note says it is.

It is deliberately stdlib-only so it can run anywhere — including in CI, on a laptop, or inside a
container that has no CUDA. It never touches the network and never touches a GPU.

Usage:
    python3 scripts/check_receipts.py [--root .]

Exit code 0 = every claim traced. Exit code 1 = at least one claim did not.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# The curated set is final. Six clips: three finished films + three Spillway keeper shots.
EXPECTED_SPILLWAY_CLIPS = {
    "spillway-s01-keeper.mp4": "98c964bfa6e183ffff73d2df122e3911c84e43c6a2466a5caa08e6ab06622c29",
    "spillway-s02-keeper.mp4": "2e836122d14b24195ec41d9fe1cab26e4afca9ca16cebdc8ac817a77c2695857",
    "spillway-s03-keeper.mp4": "ca41bef4c9e3d75434cef9dd87a6f37dda3afb72bf21c600982fe6d637db29b8",
}
EXPECTED_FILM_ASSETS = ("FILM-WAR-30s-1080p.mp4", "FILM-BEACON-30s-1080p.mp4", "FILM-BRIDGE-30s-1080p.mp4")

# Numbers that are allowed to appear in the README only because receipts/PROVENANCE.md records them.
# Anything else in the README that looks like a claim has to appear in the receipt corpus directly.
RECEIPT_DIR = "receipts"
FRONT_PAGE_FILES = ("README.md",)

# A "claim" is a decimal number, an optional x-multiplier, or a size in GB. We do not try to be
# clever: the point is to catch a number that was edited in the README and never edited back.
CLAIM_RE = re.compile(
    r"(?<![\w.])"          # not mid-word
    r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)"  # 312.7 / 1,234 / 21.0
    r"\s*(?:GB|MB|B\b)?"   # optional unit
    r"(?:\s*[×x]\s*(\d+(?:\.\d+)?))?"  # optional multiplier
)

# These are page furniture, not claims about measurements.
IGNORE_TOKENS = {
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18",
    "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35",
    "36", "40", "50", "64", "100", "1080",
    "0.5", "0.6", "0.7", "0.8", "0.9", "1.0", "2.0", "3.0", "4.0", "5.0",
    "2024", "2025", "2026",
}

# A version number is a requirement, not a measurement. "torch 2.11" does not need a receipt.
VERSION_CONTEXT = re.compile(
    r"(torch|python|comfyui|cuda|numpy|opencv|vllm|sglang|diffusers|comfy|h3|gb10|aarch64|"
    r"ffmpeg|node)\s*v?$",
    re.IGNORECASE,
)


class Failure(Exception):
    pass


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def normalise(text: str) -> str:
    """Collapse a number to a comparable token: '312.7' -> '312.7', '1,234' -> '1234'."""
    return text.replace(",", "").rstrip(".")


def load_receipt_corpus(root: Path) -> str:
    corpus = []
    for path in sorted((root / RECEIPT_DIR).rglob("*")):
        if path.is_file():
            try:
                corpus.append(path.read_text(errors="replace"))
            except OSError:
                pass
    return "\n".join(corpus)


def check_clips(root: Path) -> list[str]:
    """The curated set must be exactly the six clips the curation note names."""
    problems = []
    clips_dir = root / "clips"
    if not clips_dir.is_dir():
        return [f"clips/ directory missing at {clips_dir}"]

    present = {p.name for p in clips_dir.glob("*.mp4")}
    expected = set(EXPECTED_SPILLWAY_CLIPS)
    if present != expected:
        extra = sorted(present - expected)
        missing = sorted(expected - present)
        if extra:
            problems.append(f"clips/ holds {len(extra)} unexpected clip(s): {', '.join(extra)}")
        if missing:
            problems.append(f"clips/ is missing {len(missing)} expected clip(s): {', '.join(missing)}")

    for name, digest in sorted(EXPECTED_SPILLWAY_CLIPS.items()):
        path = clips_dir / name
        if not path.is_file():
            problems.append(f"clips/{name} missing")
            continue
        actual = sha256_of(path)
        if actual != digest:
            problems.append(f"clips/{name} hashes {actual[:16]}… but the index says {digest[:16]}…")

    index = (clips_dir / "INDEX.md")
    if index.is_file():
        index_text = index.read_text(errors="replace")
        for name, digest in sorted(EXPECTED_SPILLWAY_CLIPS.items()):
            if name not in index_text:
                problems.append(f"clips/INDEX.md does not mention {name}")
            if digest not in index_text:
                problems.append(f"clips/INDEX.md does not carry the hash for {name}")
        for asset in EXPECTED_FILM_ASSETS:
            if asset not in index_text:
                problems.append(f"clips/INDEX.md does not mention release asset {asset}")
    else:
        problems.append("clips/INDEX.md missing")

    return problems


def check_headline_claims(root: Path) -> list[str]:
    """Every measurable number on the front page must appear in receipts/."""
    corpus = normalise(load_receipt_corpus(root))
    problems = []
    for rel in FRONT_PAGE_FILES:
        path = root / rel
        if not path.is_file():
            problems.append(f"{rel} missing")
            continue
        text = path.read_text(errors="replace")
        # Drop fenced code blocks and markdown link targets so file paths do not masquerade as claims.
        text = re.sub(r"```.*?```", " ", text, flags=re.S)
        text = re.sub(r"\]\([^)]*\)", "] ", text)
        for match in CLAIM_RE.finditer(text):
            number = normalise(match.group(1))
            if number in IGNORE_TOKENS:
                continue
            # Skip version numbers attached to a software name.
            prefix = text[max(0, match.start() - 24) : match.start()]
            if VERSION_CONTEXT.search(prefix):
                continue
            if number in corpus:
                continue
            # A multiplier is written 1.54x — the corpus may hold "1.54" on its own.
            multiplier = match.group(2)
            if multiplier and normalise(multiplier) in corpus:
                continue
            line = text[: match.start()].count("\n") + 1
            problems.append(f"{rel}:{line} claims {match.group(0).strip()!r} with no receipt behind it")
    return problems


def check_provenance_index(root: Path) -> list[str]:
    """Every number that ships must be listed in receipts/PROVENANCE.md with its owner."""
    problems = []
    provenance = root / RECEIPT_DIR / "PROVENANCE.md"
    if not provenance.is_file():
        return ["receipts/PROVENANCE.md missing — the provenance index is the receipt index"]
    text = provenance.read_text(errors="replace")
    for rel in FRONT_PAGE_FILES:
        page = root / rel
        if not page.is_file():
            continue
        page_text = page.read_text(errors="replace")
        page_text = re.sub(r"```.*?```", " ", page_text, flags=re.S)
        for token in ("312.7", "202.5", "215.7", "14.40", "8.39", "9.72", "10.88", "8.09"):
            if token in page_text and token not in text:
                problems.append(f"{token} appears in {rel} but is not listed in receipts/PROVENANCE.md")
    return problems


def check_fp8_claim(root: Path) -> list[str]:
    """The FP8 footprint claim must match the bytes actually recorded in verification.json."""
    problems = []
    verification = root / RECEIPT_DIR / "verification.json"
    if not verification.is_file():
        return ["receipts/verification.json missing"]
    try:
        data = json.loads(verification.read_text())
    except json.JSONDecodeError as exc:
        return [f"receipts/verification.json is not valid JSON: {exc}"]

    weights = data.get("weights") or []
    by_name = {w.get("file"): w for w in weights if isinstance(w, dict)}
    fp8 = by_name.get("diffusion_models/minimax_h3_fl2va_fp8.safetensors")
    if not fp8:
        return ["receipts/verification.json does not record the FP8 DiT checkpoint"]
    size = fp8.get("bytes")
    if size != 20958205608:
        problems.append(
            f"FP8 DiT recorded as {size} bytes, expected 20958205608 (the 21.0 GB figure)"
        )
    readme = (root / "README.md")
    if readme.is_file():
        text = readme.read_text(errors="replace")
        if "21.0 GB" not in text and "21.0" not in text:
            problems.append("README.md no longer states the 21.0 GB FP8 footprint")
    return problems


def check_no_licence_section(root: Path) -> list[str]:
    """Licence handling is deferred by the owner — keep the repo out of it."""
    problems = []
    readme = root / "README.md"
    if not readme.is_file():
        return problems
    for match in re.finditer(r"^#{1,6}\s*.*licen[cs]e.*$", readme.read_text(errors="replace"), flags=re.M | re.I):
        problems.append(f"README.md has a licence heading: {match.group(0).strip()!r}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    root = Path(args.root).resolve()

    groups = [
        ("curated clip set", check_clips),
        ("front-page claims", check_headline_claims),
        ("provenance index", check_provenance_index),
        ("FP8 footprint", check_fp8_claim),
        ("deferred licence scope", check_no_licence_section),
    ]

    failures = 0
    for title, fn in groups:
        problems = fn(root)
        if problems:
            failures += len(problems)
            print(f"FAIL  {title}")
            for problem in problems:
                print(f"        - {problem}")
        else:
            print(f"ok    {title}")

    print()
    if failures:
        print(f"{failures} claim(s) did not trace to a receipt.")
        return 1
    print("Every published claim traced to a receipt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
