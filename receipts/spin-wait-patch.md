# GB10 spin-wait patch — what it is, and who measured it

NVIDIA's GB10 puts the CPU and the GPU in one package with one thermal budget, so CPU heat
competes directly with the GPU. vLLM's `SpinCondition.wait()` busy-loops for `busy_loop_s = 1`
second before it sleeps; during decode, inter-process messages arrive at millisecond intervals, so
the sleep path is never taken and the performance cores spin at full clock.

The fix is one line in `vllm/distributed/device_communicators/shm_broadcast.py`:

```
busy_loop_s: float = 1,   ->   busy_loop_s: float = 0.002,
```

## Who measured what

| Number | Whose measurement | Where |
|---|---|---|
| CPU 333 % → 89 %, SoC −11 °C, no throughput change | **Upstream** (the vLLM GB10 spin-wait artifact the port credits) | the same file, quoted by the port author |
| SoC reaching 96 °C (shutdown ~87 °C) while the GPU was only 72.7 °C | **Upstream** | same |
| TP=1 single-GPU serve: container CPU 93.4 % unpatched vs 92.9 % patched — **no significant change** | **The port author's own fleet**, 2026-08-17 | `custom_nodes/H3-SolAttn-SM121/GB10_SPIN_WAIT_PATCH.md` |
| Anything on our own hardware | **Nothing.** | — |

Upstream source: <https://nacyot.github.io/artifacts/vllm-spin-wait-gb10/>
Full text as vendored: `custom_nodes/H3-SolAttn-SM121/GB10_SPIN_WAIT_PATCH.md`

## The part worth reading twice

The port author did not take the upstream numbers at face value. On a TP=1 single-GPU serve they
measured **no significant change** and said so, because the upstream 333 % → 89 % figure implies
roughly 3.3 cores spinning, which requires **multiple ranks** waiting on `shm_broadcast`. At TP=1
there is a single engine-core process, and that ~93 % is real scheduling and sampling work, not
spin.

Their conclusion: apply the patch anyway — it is free and carries no throughput cost — but expect
the win on **TP ≥ 2** deployments, not on single-GPU serves.

That is the honest shape of the result, and it is why this repository ships the patch as a
convenience rather than as a speed claim. On a single Spark it buys nothing measurable.

## How to apply it

Bake it into the image — a `docker exec` `sed` is lost the moment the container is recreated, and
every relaunch recreates it:

```dockerfile
RUN f=$(find /usr/local/lib -name shm_broadcast.py -path "*device_communicators*" 2>/dev/null | head -1); \
    if [ -n "$f" ]; then sed -i 's/busy_loop_s: float = 1,/busy_loop_s: float = 0.002,/' "$f"; fi
```

The path differs by image: `dist-packages` on stock `vllm/vllm-openai` and most community GB10
builds, `site-packages` on `ghcr.io/aeon-7/aeon-vllm-ultimate`. The `find` handles both.

Check a running container:

```bash
docker exec <container> grep -n 'busy_loop_s: float' \
  $(docker exec <container> find /usr/local/lib -name shm_broadcast.py -path "*device_communicators*" | head -1)
```

## The ComfyUI path

This patch is for vLLM, and the ComfyUI node stack in `custom_nodes/` never runs vLLM. The patch
matters if you serve H3 through a vLLM or SGLang route — it is the route NVIDIA's Sol-Engine
release uses, and the route the spin-wait artifact targets. It changes no number in the
ComfyUI bench in `receipts/bench-results.md`.
