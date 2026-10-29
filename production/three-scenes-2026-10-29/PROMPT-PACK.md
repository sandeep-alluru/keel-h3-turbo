# Prompt pack: three Keel scenes (2026-10-29)

The prompts and settings below come from the ComfyUI graph saved in each shot's mp4 (`ffprobe -show_entries format_tags`, tag `prompt`), cross-checked against the spark2 ComfyUI `/history` record of the same run. The two match on every node. The only difference is the `is_changed` hash on LoadImage, and that equals the sha256 of the reference image we copied.

**Shared settings, every shot:**
- Model: MiniMax H3 image-to-video, `minimax_h3_fl2va_fp8.safetensors`.
- Text encoder: `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`.
- VAEs: `minimax_h3_video_vae_fp16`, `minimax_h3_audio_vae_fp32`.
- Sampler: KSampler, euler / simple, cfg 1.0, denoise 1.0, 16 steps.
- Sigma shift: video 12.0, audio 3.0.
- Output: 1280x704, 124 frames at 24 fps (5.167 s), video and audio from one model.
- Graph: the stock MiniMax H3 nodes only. Keel's acceleration nodes (FirstBlockCache, Motion-Context) are installed on that ComfyUI but are **not** in these graphs.

**Attempts:** one per shot. The history holds no failed or retried three-scenes prompt, and each output folder holds only attempt-001. Every shot was used in the final at 1.0x speed. Chained shots drop source frame 0, which repeats the previous shot's last frame.

## Forest chase: final 30.0 s, 6 shots, GPU 3533.9 s (58.9 min), 0 retries
Final: `~/Videos/FOREST-CHASE-30s-v001.mp4`

### 1. F01: film 0.000-5.167 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/ea57c94bdd58.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129001 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/forest/F01/attempt-001_00001_.mp4`)
- GPU: 595.9 s (2026-10-29 01:44:50.250 CDT to 2026-10-29 01:54:46.164 CDT, ComfyUI prompt `72a0742b-44af-4e70-95a2-1693a866bd32`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action cinematic forest chase. The mounted hyena gallops hard forward along the muddy trail toward the right, its powerful legs driving the ground backward. The crouched orc bounces naturally with its stride and grips the reins. The enormous bear charges after them, gaining slightly and throwing mud with each heavy footfall. The camera tracks rapidly alongside the rider, keeping pace as tree trunks and ferns sweep past; wet earth sprays behind the animals. One continuous moving shot.

overall_soundscape: Rapid pounding paws, heavy bear footfalls, splashing mud, the hyena's harsh panting, armour rattling and a pursuing bear roar.

non_diegetic_music: N/A
```

### 2. F02: film 5.167-10.292 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/2d19b0763137.png` (last frame of F01 (mean abs diff 0.8 on 64x36 luma))
- Seed 129002 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/forest/F02/attempt-001_00001_.mp4`)
- GPU: 585.8 s (2026-10-29 02:04:36.313 CDT to 2026-10-29 02:14:22.118 CDT, ComfyUI prompt `a83d0535-ecd7-4c13-a4bf-d509c7373445`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The live-action forest pursuit continues at full speed. The mounted hyena drives forward to the right with rapid powerful strides, the orc crouching low over the reins as his armour and hair jolt with the gallop. Behind them the massive bear charges around the muddy bend, following their exact path and scattering wet earth. The camera keeps tracking alongside, easing slightly wider to show the speed and the forest rushing past. The bear remains behind the mounted hyena. One continuous moving shot.

overall_soundscape: Continuous rapid galloping, heavy bear paws striking mud, harsh breath, rattling armour and rushing forest wind.

non_diegetic_music: N/A
```

### 3. F03: film 10.292-15.459 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/c7a72fe12056.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129003 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/forest/F03/attempt-001_00001_.mp4`)
- GPU: 589.7 s (2026-10-29 01:54:46.372 CDT to 2026-10-29 02:04:36.115 CDT, ComfyUI prompt `b42e7f30-d681-4b18-83c7-37741f10520e`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action cinematic close tracking shot during the forest chase. The mounted orc looks sharply over his shoulder, then faces forward and crouches lower as the hyena gallops hard to the right. His torso rises and falls with the animal's stride; his hands tighten the reins and battered armour rattles. The hyena's head drives forward with harsh panting. The camera races alongside at matching speed while wet forest trunks streak past behind them. One continuous shot.

overall_soundscape: Rapid galloping paws, leather creak, rattling iron, strained breathing and a bear roaring behind them.

non_diegetic_music: N/A
```

### 4. F04: film 15.458-20.584 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/d18ef900561b.png` (last frame of F03 (mean abs diff 0.7 on 64x36 luma))
- Seed 129004 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/forest/F04/attempt-001_00001_.mp4`)
- GPU: 587.5 s (2026-10-29 02:14:22.290 CDT to 2026-10-29 02:24:09.794 CDT, ComfyUI prompt `7139b4f7-8740-4629-85d7-bfe34e4f34d4`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The live-action mounted forest chase continues. The orc leans forward and urges the galloping hyena onward with his posture, gripping the reins as his body jolts with powerful running strides. The hyena pants and drives forward to the right. The camera tracks alongside and gradually eases back from the close view, revealing more of the animal's pumping shoulders and the rider firmly seated in the saddle while wet tree trunks whip past. One continuous moving shot.

overall_soundscape: Hard galloping paws, rattling armour, rough breathing, rushing air and the pursuing bear's deeper footfalls behind.

non_diegetic_music: N/A
```

### 5. F05: film 20.583-25.750 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/d09dd05ea4ca.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129005 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/forest/F05/attempt-001_00001_.mp4`)
- GPU: 587.9 s (2026-10-29 02:24:09.986 CDT to 2026-10-29 02:33:57.884 CDT, ComfyUI prompt `e98986f4-ca34-4405-8dfe-d843cf6be32c`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action cinematic forest chase, low tracking beside the pursuing bear. The massive bear bounds forward to the right with heavy ground-shaking paw strikes, shoulders rolling and wet fur rippling. Mud and crushed ferns fly backward. Ahead on the same trail the mounted hyena gallops away with the orc leaning forward; the bear steadily closes the gap without reaching them. The camera races alongside the bear at low height as tree trunks sweep past. One continuous shot.

overall_soundscape: Heavy pounding paws, a deep bear growl, splashing mud, snapping brush and the lighter gallop ahead.

non_diegetic_music: N/A
```

### 6. F06: film 25.750-30.000 s (source 0.000-4.250 s, speed 1.0)
- Reference: `_src/refs/0bc392fa1301.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129006 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/forest/F06/attempt-001_00001_.mp4`)
- GPU: 587.1 s (2026-10-29 02:33:58.058 CDT to 2026-10-29 02:43:45.181 CDT, ComfyUI prompt `49d17935-aafb-43a0-88a4-6a6f3962f005`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action cinematic fantasy forest chase. The mounted hyena gallops away along the muddy trail curving toward the right, the orc leaning low and holding the reins as the saddle rises and falls. The massive bear bounds after them with rolling shoulders and heavy paw strikes, remaining behind the rider. Mud flies backward and ferns shake as they rush past. The camera follows from the rear left, then gradually lets the animals gain distance, revealing the towering mossy forest ahead. The pursuit continues into the trees. One continuous shot.

overall_soundscape: Pounding paws through mud, heavy bear breaths, leather creaks, clattering armour and rushing forest wind.

non_diegetic_music: N/A
```

## Eagle hunt: final 36.042 s, 7 shots, GPU 4130.1 s (68.8 min), 0 retries
Final: `~/Videos/EAGLE-HUNT-36s-v001.mp4`

### 1. E01: film 0.000-5.167 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/26ab747c9252.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129101 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/eagle/E01/attempt-001_00001_.mp4`)
- GPU: 587.5 s (2026-10-29 02:43:45.356 CDT to 2026-10-29 02:53:32.874 CDT, ComfyUI prompt `63c56a7d-dd3d-4eb6-aa66-fca300c2054f`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Naturalistic cinematic wildlife. The golden eagle stands firmly on the cliff ledge as wind lifts the edge of its feathers. Its head turns sharply down and to the right, fixing on movement in the meadow below; it leans forward, alert and poised. The camera makes a slow, small push toward the eagle while keeping the ledge and open drop legible. One continuous shot.

overall_soundscape: Open mountain wind brushing the rock face, soft feather rustle and faint distant meadow ambience.

non_diegetic_music: N/A
```

### 2. E02: film 5.167-10.334 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/5817c8b2c4dd.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129102 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/eagle/E02/attempt-001_00001_.mp4`)
- GPU: 588.6 s (2026-10-29 02:53:33.079 CDT to 2026-10-29 03:03:21.701 CDT, ComfyUI prompt `966e1107-55ca-4347-8c72-ec48a997db59`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] A high, downward-looking wildlife view of the meadow below the cliff. The tawny rabbit makes several quick bounds toward the right through the short grass, pauses with its ears raised, and remains clearly visible against the ground. The camera gently follows its rightward movement without changing height. Sunlight and the meadow remain steady. One continuous shot.

overall_soundscape: Light wind through short grass, faint small paw impacts and distant mountain ambience.

non_diegetic_music: N/A
```

### 3. E03: film 10.333-15.500 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/2047f44f1880.png` (last frame of E01 (mean abs diff 0.7 on 64x36 luma))
- Seed 129103 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/eagle/E03/attempt-001_00001_.mp4`)
- GPU: 587.3 s (2026-10-29 03:03:21.899 CDT to 2026-10-29 03:13:09.175 CDT, ComfyUI prompt `cbc2671b-a620-40ac-bb5b-c2e5e8289dcd`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The golden eagle pushes firmly off the rock with both feet, spreads its broad wings and drops away from the cliff toward the meadow below on the right. Its wings draw closer to its body as the descent gathers speed. The camera follows the eagle outward and downward from the ledge, keeping the bird fully in view as rock recedes behind it. One continuous moving shot.

overall_soundscape: A brief scrape of talons on stone, a heavy wing stroke and rising wind rushing past feathers.

non_diegetic_music: N/A
```

### 4. E04: film 15.500-20.625 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/5a9cc0b65f3f.png` (last frame of E03 (mean abs diff 0.7 on 64x36 luma))
- Seed 129104 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/eagle/E04/attempt-001_00001_.mp4`)
- GPU: 589.6 s (2026-10-29 03:22:59.177 CDT to 2026-10-29 03:32:48.790 CDT, ComfyUI prompt `ac24b9b5-fead-478f-8789-5a11dd88a71e`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The golden eagle continues its fast descent and banks gently toward the sunlit grassy shoulder of the mountainside on the right. It follows the slope into a low approach over the alpine grass, spreading its wings to brake and extending its empty talons as the ground draws close. The camera follows from behind and lowers with the bird, keeping the flight continuous and the approaching grassy terrace readable. One continuous moving shot.

overall_soundscape: Strong rushing air gives way to a forceful wing flare and the close hiss of grass below.

non_diegetic_music: N/A
```

### 5. E05: film 20.625-25.792 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/5f516046f9a9.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129105 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/eagle/E05/attempt-001_00001_.mp4`)
- GPU: 589.6 s (2026-10-29 03:13:09.359 CDT to 2026-10-29 03:22:59.002 CDT, ComfyUI prompt `48379e1d-220c-4513-a6e4-982d7224e9e8`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The low-flying golden eagle reaches the tawny rabbit, flares its wings and brings its open talons down around the rabbit's body. The talons visibly close into a firm grip, and a powerful downstroke lifts the rabbit clear of the grass. The camera tracks beside the contact at a steady low height, keeping the eagle's feet, the rabbit and the ground visible through the grasp and first lift. One continuous shot.

overall_soundscape: A sudden rush of wings, brief grass rustle at contact and a deep close wingbeat as the eagle lifts.

non_diegetic_music: N/A
```

### 6. E06: film 25.792-30.917 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/6563abd0c971.png` (last frame of E05 (mean abs diff 0.7 on 64x36 luma))
- Seed 129106 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/eagle/E06/attempt-001_00001_.mp4`)
- GPU: 592.6 s (2026-10-29 03:32:48.963 CDT to 2026-10-29 03:42:41.566 CDT, ComfyUI prompt `6d3f6910-5442-45f9-bfb9-5f6753059e11`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The golden eagle continues climbing forward away from the grassy terrace with the same tawny rabbit held securely beneath its closed talons. Strong steady wingbeats lift both bodies higher; the rabbit stays held and hangs below the eagle, moving naturally with its flight. The camera tracks alongside the climb and gently eases farther back, widening enough to keep the eagle's full body and carried rabbit visible as the mountain meadow falls away below. One continuous moving shot.

overall_soundscape: Heavy rhythmic wing strokes over open mountain wind, with the close grass sounds falling away.

non_diegetic_music: N/A
```

### 7. E07: film 30.917-36.042 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/10a2c5f65614.png` (last frame of E06 (mean abs diff 0.7 on 64x36 luma))
- Seed 129107 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/eagle/E07/attempt-001_00001_.mp4`)
- GPU: 594.9 s (2026-10-29 03:52:35.223 CDT to 2026-10-29 04:02:30.160 CDT, ComfyUI prompt `91818fcf-1832-4548-a6f9-7b16599a9f57`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Still holding the same tawny rabbit securely beneath its talons, the golden eagle veers gently away from the camera and flies out toward the distant sunlit mountain horizon. Its strong wingbeats carry both eagle and rabbit farther into the landscape; they grow steadily smaller together, with the rabbit remaining suspended beneath the bird. The camera stops matching the eagle's sideways speed and lets it recede into the wide mountain view, gently following its departure. One continuous moving shot.

overall_soundscape: Wing strokes recede into spacious mountain wind and quiet distant meadow ambience.

non_diegetic_music: N/A
```

## Dragon net escape: final 48.708 s, 10 shots, GPU 6034.4 s (100.6 min), 0 retries
Final: `~/Videos/DRAGON-NET-ESCAPE-49s-v001.mp4`

### 1. D01: film 0.000-3.542 s (source 0.000-3.542 s, speed 1.0)
- Reference: `_src/refs/f77dcf854242.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129201 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D01/attempt-001_00001_.mp4`)
- GPU: 593.3 s (2026-10-29 03:42:41.761 CDT to 2026-10-29 03:52:35.048 CDT, ComfyUI prompt `2715a4ee-7662-4fa1-a8fb-e3ae3fada24e`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action cinematic fantasy. The small rust-red dragon flies from the mountain gap toward the rocky shelf on the right, driving forward with powerful, measured wingbeats. Its wing membranes flex under the air and its long tail steadies a shallow bank along the cliff. The soldiers hold their positions beside the net launcher as the dragon approaches. The camera tracks beside the dragon at a steady pace, keeping the mountain wall receding behind it and the shelf in view. One continuous moving shot.

overall_soundscape: Strong high-altitude wind, deep rhythmic wing strokes and a brief low dragon breath.

non_diegetic_music: N/A
```

### 2. D02: film 3.542-8.667 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/f2f3a97c14d3.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129202 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D02/attempt-001_00001_.mp4`)
- GPU: 595.2 s (2026-10-29 04:02:30.335 CDT to 2026-10-29 04:12:25.551 CDT, ComfyUI prompt `b85860a3-10d9-4635-837d-3018f11be33d`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The rust-red dragon tips its wings into a shallow outward bank along the cliff edge, sweeping through the open air in front of the soldiers' rocky shelf. Steady powerful wingbeats and its long tail balance the turn while the crew and their loaded net launcher remain on the shelf to the right. The camera eases back while tracking the bank, keeping the dragon's whole body and the nearby shelf visible rather than closing into its wings. One continuous moving shot.

overall_soundscape: High mountain wind, heavy membrane wing strokes and a low dragon exhalation.

non_diegetic_music: N/A
```

### 3. D03: film 8.667-13.834 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/1cb7e4674d76.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129203 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D03/attempt-001_00001_.mp4`)
- GPU: 600.3 s (2026-10-29 04:12:25.725 CDT to 2026-10-29 04:22:26.066 CDT, ComfyUI prompt `4dc0eab5-78ae-42d9-98b9-cf2045e06afb`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The braced soldiers pull the release on their loaded wooden net launcher. Its throwing beam snaps forward toward the open gap on the left, casting the weighted rope net free of the crossbar and out over the cliff. The released net visibly separates from the machine and sails leftward through the air, its weighted corners spreading the mesh. The camera holds a clear side view of the machine and departing net so the physical release and flight are readable together. One continuous shot.

overall_soundscape: A sharp wooden release, ropes snapping taut, a heavy mechanical clack and the airborne rush of the weighted net.

non_diegetic_music: N/A
```

### 4. D04: film 13.833-17.875 s (source 0.000-4.042 s, speed 1.0)
- Reference: `_src/refs/69c999655e05.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129204 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D04/attempt-001_00001_.mp4`)
- GPU: 604.8 s (2026-10-29 04:22:26.240 CDT to 2026-10-29 04:32:31.079 CDT, ComfyUI prompt `9f8e0efd-e9f0-43c7-ba11-1d22a7f2df6c`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The freely flying weighted rope net sails from right toward the dragon on the left. Its stone-weighted corners spread outward, opening the mesh across the dragon's flight path. The dragon raises its wings and checks its forward speed, its head facing the approaching net. The camera tracks alongside in a steady broadside view that keeps both the dragon's head and the opening net clearly visible. The intact mesh draws closer to its snout; the dragon remains outside the net. One continuous shot.

overall_soundscape: Mountain wind, leathery wingbeats and weighted ropes whipping through the air.

non_diegetic_music: N/A
```

### 5. D05: film 17.875-23.000 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/8b23fe0b6ff4.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129205 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D05/attempt-001_00001_.mp4`)
- GPU: 608.4 s (2026-10-29 04:42:37.385 CDT to 2026-10-29 04:52:45.832 CDT, ComfyUI prompt `5bbf4584-af41-43a7-bac6-b0f480d09910`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The rust-red dragon opens its jaws directly beside the intact rope mesh and blasts a concentrated stream of fire into the net in front of its snout. The flame visibly connects from its mouth to the central mesh. The struck ropes ignite, blacken and snap, forming a widening burning hole while the weighted perimeter remains visible. The dragon keeps flapping at the same height. The camera tracks alongside at a steady broadside distance, keeping the mouth, flame contact and burning strands clear together. One continuous shot.

overall_soundscape: A deep dragon breath becomes a roaring jet of flame, with sharp rope crackles and snapping burned strands over mountain wind.

non_diegetic_music: N/A
```

### 6. D06: film 23.000-28.125 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/ba6db63fa894.png` (last frame of D05 (mean abs diff 0.7 on 64x36 luma))
- Seed 129206 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D06/attempt-001_00001_.mp4`)
- GPU: 603.4 s (2026-10-29 05:02:54.985 CDT to 2026-10-29 05:12:58.342 CDT, ComfyUI prompt `adeec70b-b776-41c0-ba23-d537a58b6347`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The dragon closes its jaws and the flame jet stops. The burning rope net's weakened strands snap apart and its weighted remnants fall downward, leaving open air directly ahead. With a strong wingbeat the dragon drives forward through that cleared opening and emerges on the right beyond the falling burning ropes. The camera tracks alongside the dragon, clearly showing it move past the destroyed net as smoke and charred fragments trail below and behind. One continuous shot.

overall_soundscape: The flame roar subsides into sharp rope snaps and crackling falling fragments, followed by powerful leathery wingbeats through mountain wind.

non_diegetic_music: N/A
```

### 7. D07: film 28.125-33.292 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/4611dc7ac686.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129207 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D07/attempt-001_00001_.mp4`)
- GPU: 605.9 s (2026-10-29 04:32:31.284 CDT to 2026-10-29 04:42:37.211 CDT, ComfyUI prompt `c85b18f7-7a06-4921-b4ec-d7ef3f70a7e8`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The hovering rust-red dragon lowers its head toward the wooden net launcher and opens its jaws. A forceful stream of fire erupts from its mouth, crosses the short air gap and visibly strikes the launcher's wooden beam, frame and rope winch. The wood and ropes catch fire at the impact point as the soldiers recoil and step back to the right. The camera holds a clear broad side view containing the dragon's mouth, the connected flame and the equipment burning where it strikes. One continuous shot.

overall_soundscape: A deep dragon inhalation becomes a forceful flame roar, followed by wood crackling, ropes burning and boots scraping backward over stone.

non_diegetic_music: N/A
```

### 8. D08: film 33.292-38.417 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/3ff5eba2ff45.png` (last frame of D07 (mean abs diff 0.7 on 64x36 luma))
- Seed 129208 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D08/attempt-001_00001_.mp4`)
- GPU: 608.8 s (2026-10-29 04:52:46.023 CDT to 2026-10-29 05:02:54.810 CDT, ComfyUI prompt `91ac9dbb-88b6-4c1f-8c57-6510672fe340`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The net launcher continues burning fiercely after the dragon's flame burst. Its scorched rope winch snaps loose and the upper wooden supports buckle; the long launching beam crashes down onto the wheeled base in a shower of sparks and broken timber. The machine stays collapsed and burning. The soldiers keep hurrying to the right away from the wreck while the dragon holds its position in the air to the left. The camera remains steady enough to show the timber structure break and fall. One continuous shot.

overall_soundscape: Loud timber cracks, taut ropes snapping, falling wood hitting the wheeled frame, sustained fire and retreating boots on rock.

non_diegetic_music: N/A
```

### 9. D09: film 38.417-43.584 s (source 0.000-5.167 s, speed 1.0)
- Reference: `_src/refs/d53b348f8b16.png` (still image (generator not recorded in the ComfyUI graph))
- Seed 129209 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D09/attempt-001_00001_.mp4`)
- GPU: 603.1 s (2026-10-29 05:12:58.525 CDT to 2026-10-29 05:23:01.627 CDT, ComfyUI prompt `d8c711fe-5332-4129-a34d-d4e7fd7d7729`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The five frightened soldiers sprint along the rocky shelf away from the burning ruined net launcher. They run toward and past the camera's right side, their heavy boots scattering loose gravel and their worn armor jolting with urgent strides. The camera retreats along their escape route at running speed, keeping the staggered crew visible while the burning broken machine and the airborne dragon recede behind them to the left. One continuous moving shot.

overall_soundscape: Rapid boots scraping and pounding on loose stone, rattling armor, hard breathing and distant crackling fire under mountain wind.

non_diegetic_music: N/A
```

### 10. D10: film 43.583-48.709 s (source 0.042-5.167 s, speed 1.0)
- Reference: `_src/refs/f684e8a99d93.png` (last frame of D09 (mean abs diff 0.8 on 64x36 luma))
- Seed 129210 · 16 steps · 1280x704 · 124 frames · attempt 1 of 1 (`_src/attempts/dragon/D10/attempt-001_00001_.mp4`)
- GPU: 611.2 s (2026-10-29 05:24:12.446 CDT to 2026-10-29 05:34:23.684 CDT, ComfyUI prompt `0518eb75-0cd3-455f-bfb7-5db3881b1c9a`)

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] The three soldiers still in view keep sprinting along the rocky path toward the foreground and right, following their companions who have already run ahead out of frame. Their boots pound and kick up gravel as they put more distance between themselves and the burning ruined launcher behind them on the left. The camera continues retreating along the same escape route with a slight widening, keeping their hurried running readable while the abandoned burning machine grows farther away. One continuous moving shot.

overall_soundscape: Rapid boots, loose gravel, rattling armor and hard breathing remain close while the crackling fire grows more distant in the mountain wind.

non_diegetic_music: N/A
```
