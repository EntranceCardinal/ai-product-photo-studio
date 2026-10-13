# Security Policy — ai-product-photo-studio

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.6.x   | Yes       |
| 0.5.x   | Security fixes only |
| < 0.5   | No        |

## Reporting a vulnerability

Email `security@ai-product-photo-studio.dev` or open a private security
advisory on GitHub. Do not open a public issue for anything exploitable.

We acknowledge within 72 hours and aim to ship a patch within 14 days for
high-severity issues.

## Scope

In scope:
- Arbitrary code execution via model weight loading (pickle deserialization
  in `models/loaders/`).
- Path traversal in the batch renderer when processing user-supplied
  filenames.
- SSRF / key exfiltration in the cloud relight API client
  (`services/cloud_relight_client.py`).
- Memory disclosure between products in batch mode.

Out of scope:
- Output quality of generated images.
- Prompt-injection into the caption model.
- Local-only denial of service from huge image inputs (documented limit:
  8192x8192).

## Hardening notes

- Model weights are loaded from the local `models/weights/` dir only.
  Remote weight URLs must be pinned by SHA-256 in `config/models.yaml`.
- Never load `.pt` / `.pkl` weights from untrusted sources — the loader
  refuses pickle unless `STUDIO_ALLOW_PICKLE=1` is set.
- The cloud relight client never sends raw customer images without an
  explicit `--allow-upload` flag.