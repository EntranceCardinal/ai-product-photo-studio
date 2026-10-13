# Contributing to ai-product-photo-studio

Thanks for wanting to help build the AI product photography generator.
This is a Python desktop tool that renders studio-grade product shots from
phone snaps using diffusion relight + background compositing.

## Dev setup

```bash
git clone https://github.com/<org>/ai-product-photo-studio
cd ai-product-photo-studio
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python -m studio.bootstrap --check-env
```

Model weights are pulled on first run into `models/weights/` and are
gitignored. Do not commit weights, renders, or customer product photos.

## Branching

- `main` — stable, tagged releases only.
- `dev` — integration branch, PRs land here first.
- `feat/<scope>` — feature work (`feat/relight-pass`, `feat/bg-segmenter`).
- `fix/<ticket>` — bug fixes.

## Pull requests

1. Open an issue first for anything bigger than a bug fix.
2. Keep PRs scoped to one module. The render pipeline is coupled; touching
   `pipeline/` and `compositor/` in one PR needs a maintainer ack.
3. Run `pytest -q` and `ruff check .` before pushing. CI runs the same.
4. Add a test under `tests/` for any new pipeline stage.

## Code style

- Python 3.11+, `ruff` for lint + format, line length 100.
- Type hints on every public function. `mypy --strict` on `studio/`.
- No new heavyweight deps without an issue discussion. The GPU extras
  (`[cuda]`, `[directml]`) stay optional.
- Logging via `studio.utils.logging_setup.get_logger`, never bare `print`
  in shipped modules.

## Hardware support

We target CUDA (NVIDIA), DirectML (Windows/AMD/Intel), and CPU fallback.
Every pipeline change must degrade gracefully when the GPU backend is
unavailable. Test CPU path before requesting review.