# MiniMax-H3 Prompt Cookbook — Motion-Graphics Video

Desk research only. No model was run for this document; nothing here is a measured result.
Every syntax claim is tagged with a source code (resolved in [§8 Source index](#8-source-index)).

**Legend**

| Tag | Meaning |
|---|---|
| **[V]** | VERIFIED — read in a source: a local file, or a URL fetched during this research |
| **[I]** | INFERRED — my reading of examples; no source states it |
| **[X]** | NOT EVIDENCED — searched for, absent from every source read. Do not present as H3 capability |

**Our fixed render target.** 480×832 portrait, 124 frames, 24 fps → **5.167 s** of timeline.
Everything below is written for that budget. H3's documented envelope is 4–15 s at 24 fps
[H1]; the DGX Spark entry's validated workload is 1344×768 at 121 frames [L3]. 480×832 is
*our* setting, not a documented H3 preset — treat it as unvalidated.

---

## 1. Prompt schema

H3 has **no JSON prompt schema and no negative-prompt parameter**. A request carries
`task`, `prompt` (one string), `conditions`, `target {short_edge, aspect_ratio,
duration_seconds}` and `seed` [H4][L1]. All structure lives *inside* the prompt string as
labelled plain-text sections. Negations are therefore ordinary prose inside the description,
not a separate field [H4][S1].

### 1.1 Base modes (T2VA / I2VA / FL2VA / L2VA): three core fields

The three fields, in this exact order and with these exact snake_case names [H2 §2.2]:

| Field | What it does (quoted/paraphrased from [H2 §2.2]) |
|---|---|
| `integrated_multimodal_description` | "Describes visuals, actions, shots, speakers, dialogue, singing, and diegetic audio along the timeline." The main body. |
| `overall_soundscape` | "Summarizes ambient sound, physical action sounds, and non-verbal human sounds across the entire video." |
| `non_diegetic_music` | "Describes background music that the characters never hear and only the audience can hear." |

For I2VA/FL2VA/L2VA a one-line **instruction** precedes the fields, separated by exactly one
blank line [H2 §2.1]. I2VA's fixed sentence:

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
```

T2VA has no instruction line and "begins directly with the three core fields" [H2 §2.1]. All
three of our scenes are T2VA.

### 1.2 Full-reference mode (Ref2VA): six sections

For reference-driven prompts the body becomes six labelled sections in this order [H3 §1]:

| Section | Purpose [H3 §1] |
|---|---|
| `subject_definitions` | Defines referenced content and its labels (`<Subject N>`, `<Picture N>`, `<Video N>`, `<Audio N>`) |
| `summary` | Task type + target video + main reference relationships |
| `retention_analysis` | How each referenced item is preserved / transferred / reused |
| `detailed_description` | Visuals, actions, shots, sound, dialogue in playback order (**replaces** `integrated_multimodal_description`) |
| `overall_soundscape` | Ambience and physical sounds |
| `non_diegetic_music` | Audience-only score |

Verified differences from base mode [H3 §5.2]:

- Main field is `detailed_description`, not `integrated_multimodal_description`.
- Style is established in **one or two English sentences before `[Shot 1]`**, not after it.
- `summary` opens with a bracketed task-type prefix, types joined by ` + `, e.g.
  `[video editing + audio reference + audio reuse]` [H3 §3].
- `retention_analysis` uses fixed marker words: `fully_preserved`, `partially_preserved`,
  `attribute_transfer`, `weak_reference`; audio markers are `fully_copy`, `partially_copy`,
  `reference`, `weak_reference` [H3 §4.1–4.2].

**[I]** NVIDIA's twelve published showcase prompts use `subject_definitions` +
`detailed_description` + the two audio fields and **omit** `summary` and
`retention_analysis` [S1]. So when hand-writing rather than running H3-Context-IR, those two
analysis sections appear to be optional scaffolding. Not stated by any source.

### 1.3 Punctuation and labelling conventions actually observed

| Convention | Evidence |
|---|---|
| `field_name:` lower-case snake_case, colon, single space, body on the same line | [L1][H2][S1] |
| Fields separated by a newline; guide examples use a **blank line** between fields, the released demo uses a single `\n` | [H2 §2.2] vs [L1] |
| Shots as `[Shot N]` with square brackets, space after the closing bracket | [L1][H2][S1] |
| Cut times as `At MM:SS.mmm,` — two-digit minutes/seconds, three-digit milliseconds, comma after | [L1][H2 §4.2] |
| Speakers as `(S1)`, `(S2)`; simultaneous speakers `(S1,S2)` | [H2 §4.4] |
| Dialogue/lyrics wrapped in `<d>[Language] …</d>` | [H2 §4.4] |
| Visible on-screen text in **English double quotation marks**, verbatim, untranslated | [H2 §4.5] |
| Reference labels `<Subject 1>`, `<Picture 1>`, `<Video 1>`, `<Audio 1>` with angle brackets and a space before the number | [H3 §2][S1] |
| Instruction separator is an **em dash**: `How the reference pictures align with the target video — …` | [H2 §2.1] |
| Negations as a final comma-separated list inside the visual paragraph: `No cuts, readable text, logos, subtitles, reference-image flashes or freeze frames.` | [S1] |

### 1.4 One real example, verbatim

From `models/minimax_h3/demo_prompt.json` [L1], itself tagged
`"source": "MiniMaxAI/MiniMax-H3 scripts/readme/reproducible-768p-t2va-request.sh (H3-Context-IR output)"`.
`…` marks my elision; everything else is character-for-character:

```text
integrated_multimodal_description: [Shot 1] Cinematic, medium wide shot, pushing in slowly. In the cavernous, dimly lit bridge of a starship, sleek metallic consoles with glowing amber displays flank a massive, curved observation window. A female captain, in her late 40s with an athletic build and short silver-streaked black hair, stands in the center midground. … [Shot 2] At 00:04.500, the camera cuts to a close-up of the captain's face and shakes strongly. The brilliant blue-white light from the fleet's gathering energy reflects vividly in her dark eyes. …
overall_soundscape: A low, resonant hum of the ship's ambient life support systems serves as the baseline, soon drowned out by an audible, escalating, high-pitched electronic whine as the fleet outside charges its hyperdrives. …
non_diegetic_music: Cinematic space-opera orchestral score, slow tempo, featuring a solitary, mournful French horn melody over deep, sustained string dissonances …
```

Two things to notice, both **[I]**:

1. This is **Context-IR output**, not a hand-written prompt. It is the shape the model was
   trained to receive, so it is the best template we have — but it is machine prose, which is
   why its camera phrase is the loose `pushing in slowly` rather than the guide's controlled
   `The camera pushes in with small amplitude at slow speed`.
2. `[Shot 1]` carries the style tag *after* the bracket (`Cinematic, medium wide shot,
   pushing in slowly.`), which matches the guide's rule "At the beginning of `[Shot 1]`, state
   the overall style and initial composition" [H2 §4.1].

### 1.5 Two dialects, one grammar

| | Guide dialect [H2] | Showcase dialect [S1] |
|---|---|---|
| Visual sentence opener | `[Shot 1] Live-action, cinematic, a medium-wide shot frames…` | `[Shot 1] Photoreal product film in soft window daylight, a close view holds on…` |
| Camera | `The camera pushes in with small amplitude at slow speed…` | `In one continuous five-second shot, the camera tracks tightly with the nib…` |
| In-shot timing | not used | `From 1.5 to 3.2 seconds, …` |
| Dialogue | `<d>[English] …</d>` + `(S1)` | plain quoted line + "asks in clear conversational English" |
| Trailing negations | not specified | `No cuts, …, logos, subtitles, reference-image flashes or freeze frames.` |
| Music absent | `N/A` | `N/A` **or** `None.` |

**[I]** Both dialects demonstrably ship. Use the **guide dialect** when you want the documented
control surface (speaker IDs, `<d>`, amplitude/speed modifiers); use the **showcase dialect**
when you want a single continuous shot with beats inside it, which is closer to our 5-second,
one-pass workflow. `<d>` is a real tokenizer special token [H1], so prefer it over plain quotes
when the local tokenizer is the shipped one.

---

## 2. Shot and timing syntax

### 2.1 Cutting between shots [V]

Verified rules, all from [H2 §4.2]:

- **"Do not add a timestamp to the first shot."** `[Shot 1]` is bare.
- Later shots: `[Shot 2] At 00:03.500, the camera cuts to…` — cut time **strictly increasing**
  and **inside the video duration**.
- Cut verbs: `the camera cuts to`, `the shot cuts to`, `the shot transitions to`,
  `the shot changes to`, `the shot switches to`.
- `cross-dissolve`, `fade`, `wipe` are permitted **only when the user explicitly asks**.
- **"A cut should introduce new information about the subject, space, state, viewpoint, or
  time. If only the distance or a slight angle needs to change, prefer camera motion."**
- FL2VA "generally favors a single shot"; if multi-shot, "the last frame must be reached by the
  final `[Shot N]` at the end of the video" [H2 §3.2].

No source states a maximum shot count for T2VA. The reference demo packs 2 shots into 10 s with
the cut at 4.500 s [L1]; NVIDIA's showcase is 100% single-shot at 5 s [S1].

### 2.2 Timestamps inside a shot [V]

A second, independent timing mechanism appears in NVIDIA's showcase: phase beats **inside** a
continuous shot, in plain seconds, as `From X to Y seconds` [S1]:

```text
Shot description: one continuous, locked medium-wide view containing the raccoon, tart and counter. From 0.0 to 1.5 seconds, <Subject 1> leans slightly toward the tart, glances sideways and slowly extends one paw toward the single strawberry. From 1.5 to 3.2 seconds, the paw gently closes around the berry and lifts it clear of the tart in one readable motion. … From 3.2 to 5.0 seconds, a small offscreen wooden creak makes the raccoon straighten…
```

Also attested: `In the first two seconds, the daughter looks at her mother…` and
`During one continuous five-second shot, the camera pans slowly to follow…` [S1].

So there are **three time notations** in the corpus, and they are not interchangeable:

| Notation | Form | Where | Status |
|---|---|---|---|
| Shot boundary | `[Shot 2] At 00:04.500, the camera cuts to…` | base guide + demo | [V] documented |
| In-shot beat | `From 1.5 to 3.2 seconds, …` | showcase | [V] observed, **not** in the guide |
| Frame anchor | `Picture 2 (from Shot 1) aligns with the 8.00-second mark` | FL2VA/L2VA instruction | [V] documented |

### 2.3 Duration rules [V]

- H3 output range 4–15 s [H1]. At 24 fps our 124 frames = 5.167 s.
- "Always match the total duration of the description to the requested video length (4–15
  seconds)" [G1].
- Cut times must fall inside the duration [H2 §4.2]. With 124 frames, the last usable cue is
  ≈ 5.10 s; **keep every cut ≤ 00:04.500** to stay clear of the tail.
- The 15 s single-pass workflow in our reference pipeline is a *runtime* preset; it never
  changes the prompt grammar, only how many cues fit.

### 2.4 What I am inferring, and what I refuse to claim

- **[I]** 2–3 shots in 5.17 s is the practical ceiling: each shot needs ~1.5 s to read, and
  every cut risks a new identity sample (see §6).
- **[I]** Timestamps read as *semantic* anchors, not frame-accurate scheduling. No source
  promises the cut lands on the stated frame; the guide only requires the value to be inside
  the duration. Do not build an edit that depends on exact frame numbers.
- **[X]** No documented rule about shot count vs. quality, no "max shots" parameter, no
  per-shot duration field.

---

## 3. Camera vocabulary

### 3.1 The documented control surface [V]

H3's guide defines camera as **motion type + amplitude + speed** [H2 §4.3]. Exact strings:

| Dimension | Expressions (verbatim) |
|---|---|
| Motion type | `Zoom In` / `Zoom Out` · `Push In` / `Pull Out` · `Pan Left` / `Pan Right` · `Truck Left` / `Truck Right` · `Tilt Up` / `Tilt Down` · `Pedestal Up` / `Pedestal Down` · `Arc Shot` · `Tracking Shot` · `Static Shot` · `Shake Slightly` / `Shake Strongly` · `POV` · `Roll Clockwise` / `Roll Counterclockwise` |
| Amplitude | `with small amplitude`, `with large amplitude` |
| Speed | `at slow speed`, `at fast speed` |

Mechanics the guide gives for each [H2 §4.3]: Zoom = "focal length changes while the camera
body remains stationary"; Push = "camera moves forward / backward"; Pan = "remains in place
while the lens pivots horizontally"; Truck = "translates horizontally"; Tilt = "pivots
vertically"; Pedestal = "entire camera moves upward / downward"; Arc = "moves in an arc around
the subject"; Tracking = "follows a moving subject"; Static = "position and lens remain still".

Usage rule, verbatim [H2 §4.3]: camera motion "should be written as a natural English action
within the shot, rather than stacked as separate labels at the end of a sentence." Guide
examples:

```text
The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.
The camera pans right with large amplitude at fast speed, revealing the open doorway.
The camera holds a static shot as the runner exits the frame.
```

"Add amplitude and speed only when they are meaningful; medium amplitude and normal speed are
usually omitted" [H2 §4.3]. Negative form also attested: `no random camera shake` [G5].

### 3.2 Mapping the words we actually use

| Intent | Use this | Do **not** write | Evidence |
|---|---|---|---|
| push-in | `The camera pushes in with small amplitude at slow speed` | "dolly in" | [H2 §4.3] — "dolly" never appears |
| pull-back | `The camera pulls out…` | "dolly out" | [H2 §4.3] |
| orbit | `Arc Shot` / "the camera makes a slow small-amplitude arc around them" | "orbit" | [H2 §4.3][S1] |
| pan | `Pan Left` / `Pan Right` | "panorama" | [H2 §4.3] |
| tilt | `Tilt Up` / `Tilt Down` | "tilt down on" | [H2 §4.3] |
| lateral move | `Truck Left` / `Truck Right`; showcase: "the camera slowly moves sideways" | "dolly sideways" | [H2 §4.3][S1] |
| locked-off | `Static Shot`; showcase: "one continuous, locked medium-wide view" | "locked-off" | [H2 §4.3][S1] |
| handheld | "Subtle handheld camera" (showcase only) | — | **[V] but thin** — [S1] only, not in the guide's table |
| follow | `Tracking Shot`; showcase: "the camera tracks tightly with the nib" | "follow cam" | [H2 §4.3][S1] |
| shake | `Shake Slightly` / `Shake Strongly`; demo: "cuts to a close-up … and shakes strongly" | "handheld wobble" | [H2 §4.3][L1][S1] |

**Where evidence is thin.** `handheld` appears once, in NVIDIA prompt 5 (`Subtle handheld
camera, lifelike skin texture…`) [S1], and never in the official vocabulary table. The official
stability knob is `Shake Slightly / Shake Strongly`. "Locked-off", "dolly", "orbit", "crane",
"dolly zoom", "snorricam" are **[X]** — not attested anywhere. `POV` and `Roll …` are
documented but no example exists, so their real behaviour is unknown.

---

## 4. Effect vocabulary

This is where the docs are thinnest. H3's own guides describe **shots, camera, dialogue and
sound**; they do not maintain an effects lexicon. Treat this table as a map of what is
*attested*, not a feature list.

| Effect | Attested phrasing | Source | Status |
|---|---|---|---|
| Light sweep / edge highlight | "material highlight sweeps first, then text motion begins"; "revealed by an edge highlight"; "product-edge highlights … drive transitions" | [G2] | endorsed (product skill) |
| Light travelling across a surface | "Fierce orange friction light flickers through a small porthole and moves dynamically across the detailed flight suit, helmet, and visor"; "Tiny points of bioluminescent light play across their face"; "a narrow projection beam illuminates suspended dust across the booth" | [S1] | **[V]** observed in shipped prompts |
| Reflection / sheen beat | "a single moon reflection rolls over its refracting surface"; "the fresh ink retains a wet sheen" | [S1] | **[V]** |
| Flash / white-out | "a blinding white flash floods through the window, completely washing out the background"; "the intense white light fades abruptly" | [L1] | **[V]** — but [G2] calls "meaningless white flashes" a fake-premium tell |
| Whip pan | "same-direction whip pan"; "kinetic continuity such as same-direction pan or hand-occlusion match cut" | [G4] | **[V]** in skill doc only — absent from H3 guides |
| Hard cut as transition | "Editing must use hard cuts only. No fades, dissolves, or soft transitions." | [G4] | **[V]** skill-level rule, conflicts with [H2] which allows dissolve/fade/wipe when requested |
| Morph / transformation | "No transformations, readable text, logos…"; "No transformation, cuts, text or logos." | [S1] | **NEGATED** — never endorsed, only suppressed |
| Particles | allowed as "non-representational motion layers: masks, gradients, color fields, grids, glows, particles, trails, typography…" but "Avoid … random particles and stacked light effects" | [G3][G2] | contested: allowed as design layer, banned as decoration |
| Smoke | "转化必须连续自然，不使用硬切，不用烟雾遮挡" ("the transformation must be continuous and natural, no hard cut, no smoke obscuring") | [G5] | **NEGATED as an occluder** |
| Product reveal beats | "hero reveal -> interaction -> feature macro -> usage context -> result -> logo"; 5 s → 3–4 beats, 10 s → 5–7, 15 s → 6–9; peaks = "product action completion, variant entrance, second-half copy reveal, or full-product closing"; final beat = "stable single full-frame product closing + full single-line copy" | [G3][G2] | **[V]** skill-level; the most actionable beat grammar available |

**Read this before planning effects.** `flare` (lens flare) is **[X]** — the word appears in no
source I read. `morph` is worse than absent: both showcase prompts that must preserve an object
explicitly forbid transformation [S1], which suggests morphing is a known drift vector rather
than a control. If you need a transformation, the only attested approach is the co-op
template's *continuous* conversion with no hard cut [G5] — unverified for H3 at 5 s.

---

## 5. Audio tags

### 5.1 The two audio fields [V]

`overall_soundscape` [H2 §4.6]:

- "1–4 English sentences in one continuous paragraph."
- Covers ambient sound, physical action sounds, non-verbal human sounds (wind, rain, traffic,
  footsteps, fabric, impacts, breathing, laughter, panting).
- **Do not** repeat dialogue, singing or diegetic music here — those belong in the visual
  description.
- "Use `N/A` only when the user explicitly requests complete silence throughout the video."

`non_diegetic_music` [H2 §4.7]:

- "1–3 English sentences", instrumentation / speed / rhythm / dynamic change.
- "do not use abstract mood words or explain the emotional function of the score."
- Singing, radio, TV or phone music the characters can hear is *diegetic* and goes in the
  visual field instead.
- "Use `N/A` when there is no non-diegetic music."

Guide example, verbatim [H2 §4.6–4.7]:

```text
overall_soundscape: Steady rain taps against the café windows while low room ambience continues underneath. The entrance bell rings once, followed by wet footsteps and the soft scrape of a chair.

non_diegetic_music: Sparse piano notes at a slow tempo, joined by sustained low strings that gradually increase in volume before fading out.
```

### 5.2 Dialogue [V]

| Rule | Exact form |
|---|---|
| Speaker ID | `(S1)`, `(S2)`; group `(S1,S2)`; "A speaker keeps the same ID across shots; characters who never vocalize receive no speaker ID" |
| Line | `<d>[English] I get off at the next station.</d>` — language tag in square brackets inside `<d>` |
| Content | "Preserve every original word and punctuation mark verbatim; do not translate or rewrite them" |
| Outside `<d>` | identity phrase, ID, action, delivery all go **outside** the tag |
| Voiceover | exact phrase `says in an off-screen voiceover`, then immediately state the on-screen lips stay closed |
| Across a cut | `<scenetrans>` at the connecting points in both parts |
| Truncated by end | `<cutoff>` |

Verbatim examples [H2 §4.4]:

```text
The young woman with a quiet, breathy voice (S1) says: <d>[English] I get off at the next station.</d>
The two children (S1,S2) shout together, <d>[English] Wait for us!</d>
The man (S1) says in an off-screen voiceover: <d>[English] I still remember that road.</d> while his lips remain completely closed.
```

`<d>` is a special token: "We add several special tokens, such as `<d>`, to the tokenizer
configuration" [H1]. That is why the guide insists on it and why plain quotes (the showcase
style [S1]) are the weaker choice.

### 5.3 Silence and no-audio

Three verified routes, in order of documentary support:

1. **Guide route — `N/A`.** `overall_soundscape: N/A` "only when the user explicitly requests
   complete silence throughout the video"; `non_diegetic_music: N/A` when there is no music
   [H2 §4.6–4.7].
2. **Showcase route — state it in prose.** `overall_soundscape: … No speech.` /
   `… No dialogue.` keeps the field non-empty [S1].
3. **`None.`** appears in shipped material for music: `non_diegetic_music: None.`
   [S1 examples 01, 02, 06, 09, 10, 11][L4][L5] — while other showcase prompts use `N/A`
   [S1 examples 03, 04, 05, 07, 08, 12]. Both are attested; the guide prescribes `N/A`.

**[I]** `N/A` is the documented choice, but a non-empty field is the safer bet if a wrapper
validator rejects empty-ish values — `None.` has shipped in NVIDIA's own showcase. Our local
example file uses `None.` [L4], so match whatever the local harness already accepts.

Hard spec: output audio is 32 kHz stereo [H1]; dialogue is stable in 11 languages (Arabic,
Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish) [H1].
The audio has no separate seed, length or format fields — it is generated jointly with the
video [H1][H4].

---

## 6. What goes wrong

### 6.1 Identity drift — documented, not hypothetical [V]

- Sol-H3 Spark, on FL2VA: "H3's first/last frames are **conditioning tokens**, not hard pixel
  replacement… neither pixel-exact endpoint reproduction nor unchanged identity is
  guaranteed." [L3]
- Same file, on the two-stage recipe: "Cached generic conditioning is a quality/performance
  choice, **not a guarantee of unchanged identity in every generated scene**." [L3]
- H3's own mitigation is textual, not architectural: stable `(Sx)` IDs across shots [H2 §4.4],
  and in Ref2VA a `retention_analysis` line per subject marked `fully_preserved` /
  `partially_preserved` [H3 §4]. The markers are a *request*, not an enforcement.
- NVIDIA's showcase writes guardrails as prose: "Maintain one raccoon and one strawberry
  throughout"; "Keep his facial features, glasses and cardigan consistent, with physically
  continuous hands and machinery"; "Maintain each speaker's identity and clothing, one radio on
  the table" [S1].

**[I]** The strongest identity lever we have is *not cutting*. Every `[Shot N]` is a fresh
sample; a 2-shot 5-second clip doubles the chances of a different face or bottle. Prefer camera
motion over cuts — which the guide independently recommends [H2 §4.2].

### 6.2 Text and typography [V]

- On-screen text must be in **English double quotation marks**, original wording and
  punctuation preserved, no translation: `A red neon sign reading "营业中" glows above the
  doorway.` [H2 §4.5]
- Every showcase prompt **negates** text unless it is the subject: `No cuts, floating props,
  readable text, logos, subtitles, reference-image flashes or freeze frames.` [S1] — the model
  will otherwise invent signage.
- Do not let the model render separators as copy: "Do not write arrows, slashes, plus signs, or
  separators, because the model may render them as in-frame copy" [G2].
- One text line at a time: "At any moment, only one single-line English copy line may appear;
  forbid two text rows, upper/lower line splits, title + subtitle pairs, or multiple text blocks
  at the same time" [G2].
- If text is error-prone, cut the number of text beats: "for a 10-second film, usually use only
  one mid-film copy moment and one final copy moment" [G2].
- Small text is the known weak point: H3-Regenerate-2K exists partly to "recover information
  that conventional super-resolution methods would otherwise have to guess, such as **small
  text** and fine details" [H1]. At 480×832 there is no 2K regeneration stage, so assume small
  type will not survive.
- Never fake a mark: "Do not redraw or approximate logos, wordmarks, product UI, packaging…"
  [G3]; "Add a logo only when the user provides one. Do not generate a fake logo." [G2]

### 6.3 Motion blur — [X] no guidance exists

I searched every source; nothing documents shutter angle, motion blur amount, or a way to
request or suppress it. The only "blur" language in the corpus is **depth of field**:
`shallow depth of field` [H2 Case 2], `softly focused turquoise harbor` [S1], and the I2VA
example's rack-focus `hazy, out-of-focus blur` [H2 §Case 2]. Motion blur will be whatever the
24 fps prior produces. If you need a crisp product edge, say so in plain prose (e.g. "edges stay
sharp") — that phrasing is **[I]**, untested.

### 6.4 Other documented limits [V]

| Limit | Source |
|---|---|
| Duration 4–15 s; 24 fps; 32 kHz stereo; 768 px short edge default; ≤2K via Regenerate-2K | [H1] |
| Sparse attention is trained but **not** in the open-source release; inference is full attention | [H1] |
| Checkpoints are CFG-distilled → no negative-prompt field, negations must be prose | [H1][H4] |
| Ref2VA budgets: ≤9 images, ≤3 video clips (2–15 s each, total ≤15 s), ≤3 audio clips, ≤12 files total | [H1] |
| H3-Context-IR (the prompt rewriter) is **not** open-sourced; the API is the only faithful path | [H1] |
| Prompt/dialogue moderation may block content; false positives admitted | [H1] |
| Local two-stage recipe fixes Stage-2 text conditioning to a generic prompt, so scene control rides entirely on the Stage-1 prompt | [L3] |
| Guide's style cautions: no plot summary, no camera-label stacking, no unresolved reference labels, timing must match duration | [G1][H3 §5.2] |

---

## 7. Test matrix

Ten prompts, three scenes, one variable each. All are T2VA, written for 480×832 / 124 frames /
24 fps, and stay inside 1200 characters.

**How to run** (argument shape taken from the Spark entry; placeholders substituted) [L3]:

```bash
python infer.py --paths paths.json \
  --prompt "<prompt>" --seed 42 --output-dir outputs/<case>
```

Hold seed and `target` fixed across a baseline/variant pair, or the comparison is meaningless.

**Evaluation.** Score each pair blind, on one axis only: the axis the variable targets. For
camera tests, judge whether the *type* of move changed (not whether it looks nicer). For the
text test, judge legibility and spelling. For the cut test, count identity breaks.

### Scene A — perfume bottle product film

**A0 is the baseline for A1–A3.** One composition, slow push, no cuts, no text.

**A0 · baseline**
Hypothesis: n/a — this is the control. Establishes whether a plain product beat holds shape and
material for 5 s at 480×832.

```text
integrated_multimodal_description: [Shot 1] Photoreal product film in soft directional daylight, a low-angle close shot frames a single faceted glass perfume bottle on a matte stone plinth, filled with pale amber liquid. The camera pushes in with small amplitude at slow speed while a thin highlight travels along the bottle's front edge and the liquid holds steady. Fine dust drifts through the light behind the bottle against a deep charcoal backdrop. The bottle stays centered and fully visible, with no cuts and no on-screen text.
overall_soundscape: A quiet studio room tone with a faint glass chime as the bottle settles on the stone. A soft air movement passes behind the set.
non_diegetic_music: N/A
```

**A1 · variable: shot count 1 → 2**
Hypothesis: the added `[Shot 2]` cut at 00:02.500 yields a genuine new viewpoint (macro of the
atomiser) but introduces a second identity sample — expect a bottle silhouette/shoulder mismatch
across the cut more often than in A0.

```text
integrated_multimodal_description: [Shot 1] Photoreal product film in soft directional daylight, a low-angle close shot frames a single faceted glass perfume bottle on a matte stone plinth, filled with pale amber liquid. The camera pushes in with small amplitude at slow speed while a thin highlight travels along the bottle's front edge and the liquid holds steady. Fine dust drifts through the light behind the bottle against a deep charcoal backdrop. [Shot 2] At 00:02.500, the camera cuts to an extreme close-up of the brushed metal atomiser collar, where a single droplet of amber liquid sits on the nozzle lip. The droplet trembles once and holds, the metal stays sharp, and no on-screen text appears.
overall_soundscape: A quiet studio room tone with a faint glass chime as the bottle settles on the stone. A soft air movement passes behind the set.
non_diegetic_music: N/A
```

**A2 · variable: one on-screen copy line added**
Hypothesis: the quoted string renders as legible, correctly spelled type in the lower third
without extra invented signage. Known risk from [H1]: small text at 480p.

```text
integrated_multimodal_description: [Shot 1] Photoreal product film in soft directional daylight, a low-angle close shot frames a single faceted glass perfume bottle on a matte stone plinth, filled with pale amber liquid. The camera pushes in with small amplitude at slow speed while a thin highlight travels along the bottle's front edge and the liquid holds steady. Fine dust drifts through the light behind the bottle against a deep charcoal backdrop. The bottle stays centered and fully visible, with no cuts. A single line of off-white sans-serif text reading "NOIR ABSOLU" holds steady in the lower third of the frame.
overall_soundscape: A quiet studio room tone with a faint glass chime as the bottle settles on the stone. A soft air movement passes behind the set.
non_diegetic_music: N/A
```

**A3 · variable: light sweep added**
Hypothesis: the added sweep reads as a distinct lighting event crossing the glass edge, with no
change to bottle geometry. If it instead triggers a cut or a white flash, the sweep phrasing is
unreliable and should be dropped from the lexicon.

```text
integrated_multimodal_description: [Shot 1] Photoreal product film in soft directional daylight, a low-angle close shot frames a single faceted glass perfume bottle on a matte stone plinth, filled with pale amber liquid. The camera pushes in with small amplitude at slow speed while a thin highlight travels along the bottle's front edge and the liquid holds steady. A narrow band of light sweeps across the bottle from left to right, catching the cut glass edges, then clears. Fine dust drifts through the light behind the bottle against a deep charcoal backdrop. The bottle stays centered and fully visible, with no cuts and no on-screen text.
overall_soundscape: A quiet studio room tone with a faint glass chime as the bottle settles on the stone. A soft air movement passes behind the set.
non_diegetic_music: N/A
```

### Scene B — corridor walk toward camera

**B0 is the baseline for B1–B2.** Symmetrical corridor, subject walks to lens, static camera.

**B0 · baseline**
Hypothesis: n/a — control for walk cycle stability and face readability at the stop.

```text
integrated_multimodal_description: [Shot 1] Cinematic live-action, a symmetrical wide shot frames a long concrete corridor with daylight falling from a skylight at the far end. A woman in a long dark coat walks toward the camera at an even pace, her coat moving with each step. The camera holds a static shot as she approaches, her face becoming readable as she nears the lens, and she stops in a medium close-up. No cuts and no on-screen text.
overall_soundscape: Steady footsteps on concrete echo down the corridor beneath a low ventilation hum. Her coat fabric rustles with each step and her breathing is faintly audible as she stops.
non_diegetic_music: A low sustained synth pulse at a slow tempo, holding one level throughout.
```

**B1 · variable: camera motion type Static → Pull Out**
Hypothesis: the pull-out preserves her size in frame while the corridor geometry expands behind
her — a visible change in *type*, not just intensity. Watch for the corridor walls shearing.

```text
integrated_multimodal_description: [Shot 1] Cinematic live-action, a symmetrical wide shot frames a long concrete corridor with daylight falling from a skylight at the far end. A woman in a long dark coat walks toward the camera at an even pace, her coat moving with each step. The camera pulls out with small amplitude at slow speed, keeping her the same size in frame as she approaches, her face becoming readable as she nears the lens, and she stops in a medium close-up. No cuts and no on-screen text.
overall_soundscape: Steady footsteps on concrete echo down the corridor beneath a low ventilation hum. Her coat fabric rustles with each step and her breathing is faintly audible as she stops.
non_diegetic_music: A low sustained synth pulse at a slow tempo, holding one level throughout.
```

**B2 · variable: dialogue added (speaker ID + `<d>`)**
Hypothesis: the `<d>` block yields one audible English line in sync with visible mouth movement,
spoken once, finishing before the last second. Tests the documented dialogue path end to end.

```text
integrated_multimodal_description: [Shot 1] Cinematic live-action, a symmetrical wide shot frames a long concrete corridor with daylight falling from a skylight at the far end. A woman in a long dark coat walks toward the camera at an even pace, her coat moving with each step. The camera holds a static shot as she approaches, her face becoming readable as she nears the lens, and she stops in a medium close-up. The woman with a low, measured voice (S1) says: <d>[English] You already know the way.</d> Her lips move only for that line and settle closed. No cuts and no on-screen text.
overall_soundscape: Steady footsteps on concrete echo down the corridor beneath a low ventilation hum. Her coat fabric rustles with each step and her breathing is faintly audible as she stops.
non_diegetic_music: A low sustained synth pulse at a slow tempo, holding one level throughout.
```

### Scene C — poster / key-art motion piece

**C0 is the baseline for C1–C2.** Abstract type-free poster: geometric bars stand in for a title
block, so a text error here never contaminates the camera reading.

**C0 · baseline**
Hypothesis: n/a — control for whether a flat graphic composition holds still under a slow push.

```text
integrated_multimodal_description: [Shot 1] Graphic design motion piece, a flat poster composition fills the portrait frame: a deep indigo field, a centered block of solid off-white geometric bars standing in for a title, and a thin gold rule beneath it. The camera pushes in with small amplitude at slow speed. The bars hold their position, the gold rule stays level, and no other graphic appears. No cuts and no on-screen text.
overall_soundscape: A low, even room tone with a single soft click at the start, then near silence beneath it.
non_diegetic_music: A sparse analog synth chord at a slow tempo, held without swell and fading slightly at the end.
```

**C1 · variable: camera motion type Push In → Arc Shot**
Hypothesis: the arc produces lateral parallax between bars and background (a depth cue a flat
poster should not have) while the composition stays intact. If the poster warps or the bars
duplicate, arc on 2D graphics is off the table.

```text
integrated_multimodal_description: [Shot 1] Graphic design motion piece, a flat poster composition fills the portrait frame: a deep indigo field, a centered block of solid off-white geometric bars standing in for a title, and a thin gold rule beneath it. The camera makes a slow small-amplitude arc around the composition, so the bars shift slightly against the background and the gold rule keeps its level. The bars keep their position in the layout and no other graphic appears. No cuts and no on-screen text.
overall_soundscape: A low, even room tone with a single soft click at the start, then near silence beneath it.
non_diegetic_music: A sparse analog synth chord at a slow tempo, held without swell and fading slightly at the end.
```

**C2 · variable: audio forced to silence (`N/A` on both fields)**
Hypothesis: both fields as `N/A` yield a silent track rather than an invented ambience — the
documented silence route [H2 §4.6–4.7]. We need this for clips that will be cut to an external
music bed, so an error here changes our pipeline, not just one shot.

```text
integrated_multimodal_description: [Shot 1] Graphic design motion piece, a flat poster composition fills the portrait frame: a deep indigo field, a centered block of solid off-white geometric bars standing in for a title, and a thin gold rule beneath it. The camera pushes in with small amplitude at slow speed. The bars hold their position, the gold rule stays level, and no other graphic appears. No cuts and no on-screen text.
overall_soundscape: N/A
non_diegetic_music: N/A
```

### Swap bank — one-sentence substitutions, ready to run

| Test | Substitute this sentence | Hypothesis |
|---|---|---|
| Handheld / stability | `The camera shakes slightly as she approaches, the frame staying readable.` (replaces the `Static Shot` sentence in B0) | `Shake Slightly` reads as organic handheld rather than a jolt |
| Strong shake | `The camera shakes strongly as she approaches.` | amplitude scales, per [H2 §4.3] |
| Typography-free check | append `No readable text, logos, subtitles, reference-image flashes or freeze frames.` to C0 | NVIDIA's negation list suppresses invented signage [S1] |
| Whip-pan transition | `[Shot 2] At 00:02.000, the shot transitions to a close-up of the gold rule.` | whether `transitions to` behaves like a cut [H2 §4.2] |
| Music under dialogue | replace `non_diegetic_music` with `A restrained cello line at a slow tempo, sitting well below the spoken line.` | score ducks under dialogue instead of masking it |

**Not covered by this matrix, and worth running next:** `Roll Clockwise`/`POV` (documented, zero
examples), `cross-dissolve`/`wipe` (documented only "when explicitly requested"), morph via
continuous transformation [G5], and the whole Ref2VA path with `<Subject N>` labels.

---

## 8. Source index

**Local files** (relative to `production/video/mara/a039/h3-sol-engine/`)

| Code | Path |
|---|---|
| L1 | `models/minimax_h3/demo_prompt.json` — official 10 s / 16:9 T2VA prompt, tagged as H3-Context-IR output |
| L2 | `models/minimax_h3/README.md` — Sol-Engine H3 runtime overview, 1344×768 / 5–15 s presets |
| L3 | `models/minimax_h3/Sol-H3-Spark/README.md` — DGX Spark two-stage recipe, identity caveats, CLI |
| L4 | `models/minimax_h3/Sol-H3-Spark/examples/prompts.jsonl` — two local test prompts |
| L5 | `models/minimax_h3/Sol-H3-RTX5090/examples/prompts.jsonl` — same two prompts, 5090 entry |

**MiniMax official**

| Code | URL |
|---|---|
| H1 | https://huggingface.co/MiniMaxAI/MiniMax-H3 (model card: specs, `<d>` token, Ref2VA budgets, 2K regeneration) |
| H2 | https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md (base prompt grammar — the primary source for §1–§5) |
| H3 | https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md (full-reference six-section format) |
| H4 | https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/scripts/readme/reproducible-768p-t2va-request.sh (request JSON: `task`, `prompt`, `conditions`, `target`, `seed`) |
| G1 | https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/SKILL.md |
| G2 | https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/minimalist-product-ad-generator/SKILL.md |
| G3 | https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/brand-promo-video-generator/SKILL.md |
| G4 | https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/music-video-subtitle-generator/SKILL.md |
| G5 | https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/co-op-game-intro-generator/references/h3-video-prompt-template.md |

**NVIDIA Sol-Engine**

| Code | URL |
|---|---|
| S1 | https://nvlabs.github.io/Sana/Sol-Engine/Sol-H3-Spark/ — twelve "View exact prompt" panels. Text extracted from the page's rendered HTML; typographic quotes are as the page renders them. These are NVIDIA's showcase prompts, not H3-Context-IR output |
| S2 | https://nvlabs.github.io/Sana/Sol-Engine/ — landing page; JS-rendered, returned only the page title, so it contributed no citable prompt guidance |

Note on [S1] provenance: the page labels the panels "View exact prompt" and pairs each with a
rendered clip, but it states neither who authored them nor whether they were post-edited. Treat
them as strong evidence of *what ships*, not as official syntax.

---

### One-page cheat sheet

1. One string, three fields, in order: `integrated_multimodal_description:` →
   `overall_soundscape:` → `non_diegetic_music:`.
2. Style tag immediately after `[Shot 1]`; no timestamp on shot 1, ever.
3. Cuts are `[Shot N] At MM:SS.mmm, the camera cuts to…`, strictly increasing, inside the
   duration; in 5.17 s keep them ≤ 00:04.500.
4. Camera = type + `with small|large amplitude` + `at slow|fast speed`, written as a sentence.
5. On-screen text in English double quotes, verbatim; otherwise negate text explicitly.
6. Dialogue is `<d>[Language] …</d>` with a stable `(Sx)` outside the tag; silence is `N/A`.
7. No negative-prompt field exists — negations are prose, best placed at the end of the shot.
8. Prefer camera motion over cuts: every cut is another chance to drift.

## 8. Local results log (measured on a DGX Spark, not from documentation)

| Test | Prompt variable | Result observed in frames | Verdict |
|---|---|---|---|
| A0 | baseline slow push, 768×1344×124, 12 steps | bottle holds silhouette, liquid steady 5 s, highlight travels | baseline established |
| mg01 | "dolly push-in … orbit" wording, 480×832×124, 16 steps | push read weakly, "orbit" did nothing | **"dolly"/"orbit" are not control words — use Push/Pull/Arc** |
| C0 (I2V) | key art + "small amplitude, slow speed" | push happened but timid; type stayed sharp for all 124 f | type-lock works at small amplitude |
| C2-15s | 345 f = 14.375 s, two timed sweeps | type sharp for the whole 14 s, sweeps landed on cue | **timed events hold over a long pass** |
| MGP01-final | "large amplitude at medium speed" + arc + 2 sweeps, 345 f | push grew across the shot, arc read as lateral drift, both sweeps landed, type locked | large amplitude is safe with type in the plate |
| P-arc | "arcs slowly to the right … medium amplitude at slow speed", 768×1344×124, seed 42 | clear lateral displacement + perspective rotation of the bottle; plinth edge slides; no morph | **working control phrase** |
| P-track | "tracks sideways past the bottle … medium amplitude at slow speed" | lateral travel with a different perspective trajectory than arc; bottle angle changes; no morph | **working, distinct from arc** — see `camera-vocab-comparison.png` |

| P-cut | `[Shot 2] At 00:02.500, the camera cuts to an extreme close-up of the atomiser collar…` | **the cut fires on cue at 2.5 s**, shot 2 is a clean macro of the metal collar with the droplet; object reads as the same bottle | **designed, timed cuts work in one generation** |

### Envelope (one Spark, measured)

`megapixels × frames ≈ 130-140` is the budget. 768×1344×124 (128) OK · 480×832×345 (138) OK ·
768×1344×243 (250) CUDA illegal access · 768×1344×345 (356) CUDA illegal access.
So 14 s forces ~0.40 MP; 5 s allows 1.03 MP.

### Cache behaviour

Disk encode cache (`H3_ENCODE_CACHE_DIR`) turns a repeat prompt's encode into a lookup:
`MGP01-final` ran as a HIT and took **544 s** for 345 frames versus ~800 s cold.
Note for anyone reusing the cache: `text_token_tags` must stay on CPU — the packer builds CPU index
tensors from them and raises a device mismatch otherwise.