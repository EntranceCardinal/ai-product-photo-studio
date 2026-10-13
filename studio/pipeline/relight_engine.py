"""Relighting stage — diffusion relight pass.

Applies the relight_sdxl_lite model to normalize illumination to a studio
key light. This module owns the largest VRAM footprint in the pipeline; it
releases the model after each batch when `compute.fp16` is off.
"""

from __future__ import annotations

import numpy as np

from studio.core.pipeline import RenderContext
from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)

_KEY_LIGHT_DIR = (-0.35, -0.7, 0.62)  # normalized, upper-left key


class RelightEngine:
    name = "relight_engine"

    def __call__(self, ctx: RenderContext) -> RenderContext:
        if not ctx.settings.pipeline.relight or ctx.image is None:
            return ctx

        _LOG.info("relighting %s with key light %s", ctx.source_path.name, _KEY_LIGHT_DIR)
        ctx.image = self._apply_light_field(ctx.image)
        ctx.metadata["relight.key_dir"] = ",".join(f"{c:.2f}" for c in _KEY_LIGHT_DIR)
        return ctx

    @staticmethod
    def _apply_light_field(rgb: np.ndarray) -> np.ndarray:
        """Placeholder intensity warp. Real pass delegates to the diffusion model.

        Kept deterministic so the CPU test path stays reproducible.
        """
        h, w = rgb.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = (xx / max(w - 1, 1)) * 2.0 - 1.0
        ny = (yy / max(h - 1, 1)) * 2.0 - 1.0
        field = 1.0 - 0.18 * (_KEY_LIGHT_DIR[0] * nx + _KEY_LIGHT_DIR[1] * ny)
        return np.clip(rgb.astype(np.float32) * field[..., None], 0, 255).astype(np.uint8)