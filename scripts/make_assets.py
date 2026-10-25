#!/usr/bin/env python3
"""make_assets.py — render the Keel brand assets and the clip posters.

Two jobs, one file:

1. **Brand** — the wordmark, the square mark, and the social-preview card. These are pure
   geometry plus a font, so they render identically on any machine with Pillow and the DejaVu
   fonts. Every run overwrites the previous output; the files are deterministic.

2. **Posters** — one poster per clip, cut from the real footage, plus a short teaser cut from
   the strongest clip. This part needs source video. Point it at a directory of films and a
   directory of shots:

       python3 scripts/make_assets.py --films /path/to/films --clips /path/to/clips

Output lands in `assets/`.

Requires: Pillow, and ffmpeg/ffprobe on PATH for the poster and teaser part.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
POSTERS = ASSETS / "posters"

# Palette — the same one the demo video is drawn in, so the card and the film agree.
INK = (14, 16, 18)
PAPER = (232, 234, 237)
MUTED = (150, 158, 166)
ACCENT = (88, 166, 255)
PANEL = (20, 23, 26)

SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

WORDMARK = "keel"
HEADLINE = "Accelerated MiniMax H3 video diffusion inference on a single DGX Spark."

# The mark: a hull meeting a keel. Two swept strokes for the hull, one straight stroke for the
# spine below the vertex. Drawn in a 120-unit box and scaled wherever it is placed.
HULL_L = ((13, 40), (58, 77))
HULL_R = ((107, 40), (62, 77))
SPINE = ((60, 77), (60, 112))
MARK_STROKE = 15


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


# --------------------------------------------------------------------------- the mark


def draw_mark(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], colour, scale: float = 1.0):
    """Draw the keel mark inside an axis-aligned box, scaled to fit."""
    x0, y0, x1, y1 = box
    side = min(x1 - x0, y1 - y0)
    ox = x0 + ((x1 - x0) - side) / 2
    oy = y0 + ((y1 - y0) - side) / 2
    u = side / 120.0

    def pt(p):
        return (ox + p[0] * u, oy + p[1] * u)

    width = max(1, int(round(MARK_STROKE * u)))
    for a, b in (HULL_L, HULL_R, SPINE):
        draw.line([pt(a), pt(b)], fill=colour, width=width, joint="curve")
        r = width / 2
        for p in (a, b):
            cx, cy = pt(p)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)


def mark_svg(x: float, y: float, size: float, colour: str) -> str:
    """The same mark as SVG geometry, so the vector and the raster are one design."""
    u = size / 120.0
    w = MARK_STROKE * u
    parts = []
    for a, b in (HULL_L, HULL_R, SPINE):
        parts.append(
            f'<line x1="{x + a[0] * u:.2f}" y1="{y + a[1] * u:.2f}" '
            f'x2="{x + b[0] * u:.2f}" y2="{y + b[1] * u:.2f}" '
            f'stroke="{colour}" stroke-width="{w:.2f}" stroke-linecap="round"/>'
        )
    return "".join(parts)


# --------------------------------------------------------------------------- the wordmark


def text_width(word: str, fnt: ImageFont.FreeTypeFont, tracking: float) -> int:
    if not word:
        return 0
    widths = [fnt.getlength(ch) for ch in word]
    return int(round(sum(widths) + tracking * (len(word) - 1)))


def draw_tracked(draw: ImageDraw.ImageDraw, xy, word: str, fnt: ImageFont.FreeTypeFont,
                 fill, tracking: float):
    """Draw a word with letter-spacing, which Pillow leaves to the caller."""
    x, y = xy
    for ch in word:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + tracking
    return x


def tracked_svg(x: float, y: float, word: str, size: float, tracking: float, fill: str,
                weight: str = "700") -> str:
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="DejaVu Sans, Helvetica, Arial, sans-serif" '
        f'font-size="{size:.2f}" font-weight="{weight}" letter-spacing="{tracking:.2f}" '
        f'fill="{fill}">{word}</text>'
    )


# --------------------------------------------------------------------------- brand


def logo_layout() -> dict:
    """One geometry, shared by the raster and the vector."""
    return {
        "width": 1280,
        "height": 320,
        "mark": (56, 76, 236, 256),   # x0, y0, x1, y1
        "word_x": 292,
        "word_size": 132,
        "tracking": 9.0,
    }


def make_logo(path: pathlib.Path, dark: bool) -> None:
    lay = logo_layout()
    bg = INK if dark else None
    word_colour = PAPER if dark else INK
    mark_colour = ACCENT
    if dark:
        img = Image.new("RGB", (lay["width"], lay["height"]), bg)
    else:
        img = Image.new("RGBA", (lay["width"], lay["height"]), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    draw_mark(draw, lay["mark"], mark_colour)

    fnt = font(SANS_B, lay["word_size"])
    bbox = fnt.getbbox(WORDMARK)
    # Baseline placement: centre the glyph box on the mark's vertical centre.
    baseline = lay["mark"][1] + (lay["mark"][3] - lay["mark"][1]) / 2 - (bbox[1] + bbox[3]) / 2
    draw_tracked(draw, (lay["word_x"], baseline), WORDMARK, fnt, word_colour, lay["tracking"])
    img.save(path)


def make_mark_png(path: pathlib.Path) -> None:
    img = Image.new("RGBA", (512, 512), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw_mark(draw, (16, 16, 496, 496), ACCENT)
    img.save(path)


def make_social_preview(path: pathlib.Path, strip: list[pathlib.Path] | None) -> None:
    """The card a link unfurls into: mark, wordmark, one line of what this is."""
    W, H = 1280, 640
    img = Image.new("RGB", (W, H), INK)
    draw = ImageDraw.Draw(img)

    # A soft wash so the card is not a flat rectangle.
    for i in range(H):
        t = i / max(1, H - 1)
        shade = tuple(int(INK[c] + (PANEL[c] - INK[c]) * (1 - t) * 0.85) for c in range(3))
        draw.line([(0, i), (W, i)], fill=shade)

    draw_mark(draw, (72, 72, 232, 232), ACCENT)

    word_f = font(SANS_B, 96)
    draw_tracked(draw, (266, 92), WORDMARK, word_f, PAPER, 7.0)

    rule_y = 232
    draw.rectangle([72, rule_y, 72 + 96, rule_y + 5], fill=ACCENT)

    head_f = font(SANS, 34)
    y = rule_y + 46
    for line in (
        "Accelerated MiniMax H3 video diffusion inference",
        "on a single DGX Spark.",
    ):
        draw.text((72, y), line, font=head_f, fill=PAPER)
        y += 46

    sub_f = font(MONO, 22)
    draw.text((72, y + 18), "comfyui node packs  ·  resident weights  ·  checked numbers",
              font=sub_f, fill=MUTED)

    if strip:
        band_h = 150
        band_y = H - band_h
        n = len(strip)
        slot = W // n
        for i, src in enumerate(strip):
            frame = Image.open(src).convert("RGB")
            fw, fh = frame.size
            scale = max(slot / fw, band_h / fh)
            frame = frame.resize((max(1, int(fw * scale)), max(1, int(fh * scale))), Image.LANCZOS)
            left = max(0, (frame.width - slot) // 2)
            frame = frame.crop((left, 0, left + slot, band_h))
            img.paste(frame, (i * slot, band_y))
        draw.rectangle([0, band_y, W, band_y + 2], fill=ACCENT)

    img.save(path, "PNG")


# --------------------------------------------------------------------------- posters


def ffprobe_duration(path: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def grab(path: pathlib.Path, at: float, dest: pathlib.Path, width: int = 1280, height: int = 720) -> None:
    """One frame, cropped to fill the target box."""
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", str(path),
         "-frames:v", "1",
         "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height}",
         str(dest)],
        check=True)


def make_poster(frame_path: pathlib.Path, dest: pathlib.Path, title: str, subtitle: str,
                size: tuple[int, int] = (1280, 720)) -> None:
    W, H = size
    frame = Image.open(frame_path).convert("RGB")
    fw, fh = frame.size
    scale = max(W / fw, H / fh)
    frame = frame.resize((int(fw * scale + 1), int(fh * scale + 1)), Image.LANCZOS)
    frame = frame.crop(((frame.width - W) // 2, (frame.height - H) // 2,
                         (frame.width - W) // 2 + W, (frame.height - H) // 2 + H))
    img = frame.convert("RGBA")

    # Scrim so the label reads over any frame.
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(scrim)
    for i in range(190):
        a = int(215 * (i / 190) ** 1.6)
        sdraw.line([(0, H - 190 + i), (W, H - 190 + i)], fill=(14, 16, 18, a))
    img = Image.alpha_composite(img, scrim)

    draw = ImageDraw.Draw(img)
    draw.rectangle([64, H - 122, 64 + 58, H - 117], fill=ACCENT)
    draw.text((64, H - 104), title, font=font(SANS_B, 40), fill=PAPER)
    draw.text((64, H - 54), subtitle, font=font(MONO, 22), fill=MUTED)
    img.convert("RGB").save(dest, "PNG")


# The teaser is cut from the clip that carries the most movement: a walk through a burning
# street, with the subject moving toward camera and a crowd behind.
TEASER_SOURCE = "FILM-BEACON-1920x1056.mp4"
TEASER_START = 3.5
TEASER_LENGTH = 12.0
# The teaser's own geometry, and the hero poster's: 1920x1056 scaled to 1280 wide.
TEASER_WIDTH = 1280
TEASER_HEIGHT = 704


def make_teaser(films: pathlib.Path, dest: pathlib.Path) -> None:
    src = films / TEASER_SOURCE
    if not src.is_file():
        raise SystemExit(f"teaser source not found: {src}")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-ss", f"{TEASER_START:.3f}", "-t", f"{TEASER_LENGTH:.3f}", "-i", str(src),
         "-vf", f"scale={TEASER_WIDTH}:{TEASER_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={TEASER_WIDTH}:{TEASER_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
         "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", "-c:a", "aac", "-b:a", "128k",
         str(dest)],
        check=True)


# --------------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--films", help="directory holding the finished films")
    parser.add_argument("--clips", help="directory holding the Spillway shots")
    parser.add_argument("--skip-posters", action="store_true", help="brand assets only")
    args = parser.parse_args()

    ASSETS.mkdir(exist_ok=True)
    POSTERS.mkdir(exist_ok=True)

    make_logo(ASSETS / "keel-logo.png", dark=False)
    make_logo(ASSETS / "keel-logo-dark.png", dark=True)
    make_mark_png(ASSETS / "keel-mark.png")

    lay = logo_layout()
    light_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{lay["width"]}" height="{lay["height"]}" '
        f'viewBox="0 0 {lay["width"]} {lay["height"]}" role="img" aria-label="Keel">'
        f'<title>Keel</title>'
        f'{mark_svg(lay["mark"][0], lay["mark"][1], 180, "#58A6FF")}'
        f'{tracked_svg(lay["word_x"], 232, WORDMARK, lay["word_size"], lay["tracking"], "#0E1012")}'
        f'</svg>\n'
    )
    dark_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{lay["width"]}" height="{lay["height"]}" '
        f'viewBox="0 0 {lay["width"]} {lay["height"]}" role="img" aria-label="Keel">'
        f'<title>Keel</title>'
        f'<rect width="{lay["width"]}" height="{lay["height"]}" fill="#0E1012"/>'
        f'{mark_svg(lay["mark"][0], lay["mark"][1], 180, "#58A6FF")}'
        f'{tracked_svg(lay["word_x"], 232, WORDMARK, lay["word_size"], lay["tracking"], "#E8EAED")}'
        f'</svg>\n'
    )
    (ASSETS / "keel-logo.svg").write_text(light_svg)
    (ASSETS / "keel-logo-dark.svg").write_text(dark_svg)

    strip: list[pathlib.Path] = []
    if args.films and not args.skip_posters:
        films = pathlib.Path(args.films)
        tmp = ASSETS / ".tmp"
        tmp.mkdir(exist_ok=True)
        picks = [
            ("FILM-BEACON-1920x1056.mp4", "film-beacon", 6.0, "Beacon",
             "finished film · 1920x1056 · 31.104 s"),
            ("FILM-WAR-1920x1056.mp4", "film-war", 6.0, "War",
             "finished film · 1920x1056 · 31.104 s"),
            ("FILM-BRIDGE-1920x1056.mp4", "film-bridge", 15.0, "Bridge",
             "finished film · 1920x1056 · 31.104 s"),
        ]
        for fname, stem, at, title, sub in picks:
            src = films / fname
            if not src.is_file():
                print(f"skip {fname}: not found in {films}", file=sys.stderr)
                continue
            frame = tmp / f"{stem}.png"
            grab(src, at, frame)
            make_poster(frame, POSTERS / f"{stem.lower()}.png", title, sub)
            strip.append(frame)

        hero_src = films / "FILM-BEACON-1920x1056.mp4"
        if hero_src.is_file():
            hero_frame = tmp / "hero.png"
            # The poster carries the teaser's geometry exactly, so the still the reader sees
            # before the video starts is the video's own framing, and nothing shifts.
            grab(hero_src, 6.0, hero_frame, width=TEASER_WIDTH, height=TEASER_HEIGHT)
            make_poster(hero_frame, ASSETS / "hero-poster.png", "MiniMax H3",
                        "rendered on one DGX Spark", size=(TEASER_WIDTH, TEASER_HEIGHT))
            make_teaser(films, ASSETS / "keel-teaser.mp4")

    if args.clips and not args.skip_posters:
        clips = pathlib.Path(args.clips)
        tmp = ASSETS / ".tmp"
        tmp.mkdir(exist_ok=True)
        shots = [
            ("spillway-s01.mp4", "shot-s01", 3.5, "Spillway S01",
             "Spillway shot · 1024x576 · 8.0 s"),
            ("spillway-s02.mp4", "shot-s02", 3.5, "Spillway S02",
             "Spillway shot · 1024x576 · 8.0 s"),
            ("spillway-s03.mp4", "shot-s03", 3.5, "Spillway S03",
             "Spillway shot · 1024x576 · 8.0 s"),
        ]
        for fname, stem, at, title, sub in shots:
            src = clips / fname
            if not src.is_file():
                print(f"skip {fname}: not found in {clips}", file=sys.stderr)
                continue
            frame = tmp / f"{stem}.png"
            grab(src, at, frame)
            make_poster(frame, POSTERS / f"{stem}.png", title, sub)

    make_social_preview(ASSETS / "keel-social-preview.png", strip)
    shutil.rmtree(ASSETS / ".tmp", ignore_errors=True)

    for p in sorted(ASSETS.rglob("*")):
        if p.is_file():
            print(f"{p.relative_to(ROOT)}  {p.stat().st_size:,} B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
