# Receipt — corrupt text-encoder diagnosis and SHA-pinned replacement

Step-0 runtime verification of the production stack caught a corrupt model file *before* any production work ran on it. Recorded in the production plan ledger, 2026-10-25.

## The error

Configured text encoder: `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`

| Check | Value |
|---|---|
| File size on disk | 21,714,795,671 bytes |
| Bytes accounted for by the safetensors header | 15,687,142,551 bytes |
| Unaccounted trailing bytes | **6,027,653,120** |
| SHA-256 of the corrupt file | `61f55b01f03e9cd9ec2b10e3084e74519230373135aef5c84ec6b7ec04208340` |
| Loader verdict | both `safetensors.safe_open` and `comfy.utils.load_torch_file` reject it: `incomplete metadata, file not fully covered` |

Raw loader log: [`text-encoder-load.log`](text-encoder-load.log). Exact cause of the malformed file is unknown. No truncation, replacement or repair was attempted on it — the corrupt file was left unchanged, and step 0 stopped on the evidenced error, per protocol.

## The fix

A fresh download of the exact Comfy-Org / MiniMax-H3 encoder, pinned to the original revision `0543966fbdce5ba05709a8f2031c94bdba629b4a` (the source identified in the installed Comfy blueprint and the pinned checkpoint manifest), fetched under a **new filename only**:

- Single-stream download was slow, so the file was fetched in **12 parallel 128 MiB ranges**, each validated (HTTP 206 / Content-Range / length), then assembled and hash-checked whole.
- Assembled file: **15,687,142,551 bytes** — header covers the entire file.
- SHA-256 `35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6` — matches the source.
- `comfy.utils.load_torch_file` loads **2,054 tensors**. Download: 637.400 s.
- The new file is selected via `production/H3-WORKFLOW-CONFIG.json`; no global server defaults or old pipeline files were changed.

## The proof it worked

A real H3 forward pass on the fresh encoder (124 frames, 512×288, 24 fps, 2 Euler steps, CFG 1, seed 20261025): **succeeded in 30.02 s** — video 558,700 bytes, SHA-256 `dac049a47ac5e6db0450ffa6eaa17898f250190d087663aab87a7d538991d1e3`, full media decode clean, 32 kHz audio present. Receipt: [`forward-receipt.json`](forward-receipt.json); the clip `forward-proof.mp4` was removed from git in the best-clips curation — see [`CURATION-NOTE.md`](CURATION-NOTE.md). Runtime qualification only — not a production take.
