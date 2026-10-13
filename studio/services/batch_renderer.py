"""Batch renderer — walks an input dir and drives the pipeline per product.

Concurrency is bounded by `compute.batch_size`; each worker owns its own
pipeline instance so GPU state never leaks across threads.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from studio.config.settings import StudioSettings
from studio.core.pipeline import RenderContext, build_default_pipeline
from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)

_SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def discover_inputs(input_dir: Path) -> list[Path]:
    return sorted(p for p in input_dir.rglob("*") if p.suffix.lower() in _SUPPORTED_EXT)


def render_batch(input_dir: Path, output_dir: Path, settings: StudioSettings) -> dict[str, int]:
    """Render every supported image under `input_dir`. Returns a summary."""
    files = discover_inputs(input_dir