# Vendored node packs

The three directories here are third-party works, redistributed under their own licences.
`H3-Motion-Context/` and `H3-FirstBlockCache/` are byte for byte as their authors published them —
licences, READMEs, code and workflows included.

`H3-SolAttn-SM121/` carries our changes in three of its files: `install.sh`,
`nodes/h3_vae_batch.py` and `scripts/h3-comfy-launch.sh`. Every other file in it is as its author
published it, including the vendored kijai/KingGore tree, whose own changes are recorded in that
tree's `NOTICE` and in the patch file beside it.

Each upstream repository, the revision we took and the files we changed are listed in
`receipts/vendored-trees.md`.

| Directory | Author | Project |
|---|---|---|
| `H3-SolAttn-SM121/` | KingGore, kijai, drowzeys | the SM121 port of Sol-Attn, FirstBlockCache, the batched VAE decode and the GB10 spin-wait patch |
| `H3-FirstBlockCache/` | duckyshell | the standalone FirstBlockCache pack |
| `H3-Motion-Context/` | NikoDemon80 | Motion-Context, clip chaining that survives a join |

The upstream repositories are named with links in the Credits section of the main README. Their
respective upstream licences and attribution notices apply.

`H3-SolAttn-SM121` ships `patches/UPSTREAM-LICENSE-KingGore-Apache2.0` for the vendored KingGore
sources. The CI workflow checks that each upstream licence is still present.
