# Clip chaining — six short generations, one 31-second film, every seam measured

**Measured here.** 2026-10-25, on a DGX Spark (GB10, `sm_121`, 121 GB of visible unified memory).

H3 renders a short clip at a time. A 31-second film is six of them: six spans of 124 frames at
24 fps, each **5.166688 s**, giving **744** frames and **31.104 s** of container duration once they
are cut together.

## The two ways a film is put together

**The cut film.** Six independent generations, one per shot, each from its own keyframe and its own
prompt, cut together. This is how the three delivered films were made, and it is the shape of a
film: six shots, five seams.

**The continuous take.** One generation that runs past the model's window, carried from span to span
by the Motion Context node pack. Each span saves its latent tail, the next span loads that latent
and continues from it, and a trim node drops the overlapping frames so the join carries no cut.
This is `h3_comfy.py --mode chain`; `RECIPE.md` §6 has the procedure.

The difference matters when a seam is measured. A cut film has five seams and every one of them is
a place where the picture can change abruptly. A continuous take has none.

## How a seam is verified

The measurement runs on the delivered file, not on the shots: the re-encode shifts the luma, and a
cut can land a frame late, so a seam that holds in the shots can still break in the film.

`craft/gates/join_gate.py` does it in three steps.

1. **Where the cuts are.** Two independent detectors: PySceneDetect's ContentDetector at threshold
   27.0, and ffmpeg's own scene filter at threshold 0.4. The film's cuts are the union of what both
   found.
2. **The brightness track.** ffmpeg's `signalstats` filter, one `YAVG` per frame, averaged over
   six frames either side of each cut.
3. **The score at each boundary.** On a fixed 240×240 canvas: the palette correlation between the
   last frame before the cut and the first frame after it, and the luma jump across the cut.

Two bars, and a boundary is outside them when either one is crossed:

| Measure | Bar | Reads as |
|---|---|---|
| Palette correlation | at least **0.35** | the two sides of the cut are the same place and the same light |
| Luma jump | at most **45** | the exposure steps across the cut |

The gate prints one line per boundary and exits 1 when a boundary sits outside the bars.

## What the three delivered films measure

Measured with `craft/gates/join_gate.py` on the release assets, OpenCV 5.0.0. The machine-readable
form is `receipts/clip-chaining-measurements.json`.

| Film | SHA-256 | Boundaries measured | Holding the bars | Outside the bars |
|---|---|---:|---:|---:|
| `FILM-WAR-1920x1056.mp4` | `18cdfd1f4e5ae550b8c854efb71832802eddf4a3a47bbe547d7bd09e03c7c627` | 5 | 3 | 2 |
| `FILM-BEACON-1920x1056.mp4` | `03b4500d0fab85cf11e1cf859a16b77326900a4637042b81faea3f119104e220` | 9 | 8 | 1 |
| `FILM-BRIDGE-1920x1056.mp4` | `64a2b1c86b3bc89594ad1cadf4b0b0cad5f3adaf3dfab0175df78ce2cd6b18c2` | 8 | 4 | 4 |

Every one of the three films is a cut film, so every one of them has seams, and the gate names
which seams read as breaks rather than leaving them to be found by eye.

## The boundaries, one by one

The five seams of the War film are the five span joins: 5.167 s, 10.333 s, 15.500 s, 20.667 s and
25.833 s. The bars are crossed at the first and the last of them, on palette correlation.

The Beacon film has nine boundaries — its five span joins and four more inside the spans — and one
of them crosses the bars: the seam at 25.833 s, on palette correlation and on both luma measures,
with a signalstats luma jump of 103.97 and a cv2 luma jump of 120.06.

The Bridge film has eight boundaries — its five span joins and three more inside the spans — and
four of them cross the palette bar.

## Two things worth knowing about the numbers

**The palette correlation moves a little between OpenCV releases.** The same file measured with a
different OpenCV build gives a slightly different palette figure, which can move a boundary that
sits close to the bar. Every receipt therefore records the OpenCV version it was measured with, so
two numbers can be compared rather than merely lined up.

**A boundary outside the bars is a reading, not a defect on its own.** A cut to a different location
has a low palette correlation by construction — that is what a cut to a new place looks like. What
the gate gives you is the list: which seams read as breaks, where they are, and by how much. A seam
you meant to cut reads one way and a seam you did not reads another, and both are on the list.
