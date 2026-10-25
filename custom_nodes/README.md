# Vendored node packs

The three directories here are third-party works, redistributed exactly as their authors published
them. Their upstream files are unmodified — the licences, READMEs, code and workflows in each
directory are the authors', byte for byte.

| Directory | Author | Project |
|---|---|---|
| `H3-SolAttn-SM121/` | KingGore, kijai, drowzeys | the SM121 port of Sol-Attn, FirstBlockCache, the batched VAE decode and the GB10 spin-wait patch |
| `H3-FirstBlockCache/` | duckyshell | the standalone FirstBlockCache pack |
| `H3-Motion-Context/` | NikoDemon80 | Motion-Context, clip chaining that survives a join |

The upstream repositories are named with links in the Credits section of the main README. Their
respective upstream licences and attribution notices apply.

`H3-SolAttn-SM121` carries the patches it needs for `sm_121`, including
`patches/UPSTREAM-LICENSE-KingGore-Apache2.0` for the vendored KingGore sources. The CI workflow
checks that each upstream licence is still present.
