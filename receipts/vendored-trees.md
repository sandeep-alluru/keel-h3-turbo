# The three vendored node packs, against their upstreams

Every pack under `custom_nodes/` is a third-party work, redistributed under its author's licence.
This is the record of the revision we took, and of every file we changed afterwards.

## Method

Each upstream repository was cloned fresh and compared against the tree in this repository with
`diff -rq`, which reports a differing file and a file present on one side only. The revision is
the commit the clone landed on.

| Pack | Author | Upstream | Revision | Result |
|---|---|---|---|---|
| `H3-Motion-Context/` | NikoDemon80 | <https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context> | `518c083` | identical — no differing file, no file on one side only |
| `H3-FirstBlockCache/` | duckyshell | <https://github.com/duckyshell/ComfyUI-MiniMaxH3-FirstBlockCache> | `d474755` | identical — no differing file, no file on one side only |
| `H3-SolAttn-SM121/` | drowzeys | <https://github.com/drowzeys/keys-SM121-Optimized-MiniMax-H3-Nvidia-Sol-Engine-Kijai-SolAttn_Triton-Single-DGX-Spark> | `7e3db54` | identical except the three files below |

## The three files we changed in the SM121 Sol-Attn pack

| File | Change | What it fixes |
|---|---|---|
| `install.sh` | pins ComfyUI `v0.41.0`, and installs all three packs as packs | the Motion-Context pack asks for ComfyUI 0.34.0 or newer, and a directory without `__init__.py` is skipped at start-up |
| `nodes/h3_vae_batch.py` | the batched-VAE decode takes a frame window | the stock call hands a frame slice to `tiled_decode`, so the batched signature has to accept it |
| `scripts/h3-comfy-launch.sh` | the launcher passes `--disable-comfy-compiler` | ComfyUI 0.41.0 plans the H3 allocations up front, and that plan needs more memory than a Spark with other work has left |

Every other file in that pack is as drowzeys published it, including the vendored kijai/KingGore
tree and the `NOTICE` and patch file that record his own changes to it. His licence, his README and
his upstream wording are carried as published.

## Why these trees sit outside the language audit

The three packs are third-party works under their own licences, redistributed as their authors
published them — including Apache-2.0 legal text that defines copyright in its own terms, and
upstream wording our vocabulary would otherwise edit away. The three files in the table above are
ours, so they sit inside the audit.

## The comparison, reproduced

```bash
git clone --depth 1 https://github.com/NikoDemon80/ComfyUI-H3-Motion-Context
git clone --depth 1 https://github.com/duckyshell/ComfyUI-MiniMaxH3-FirstBlockCache
git clone --depth 1 https://github.com/drowzeys/keys-SM121-Optimized-MiniMax-H3-Nvidia-Sol-Engine-Kijai-SolAttn_Triton-Single-DGX-Spark
diff -rq <upstream> custom_nodes/<pack>
```
