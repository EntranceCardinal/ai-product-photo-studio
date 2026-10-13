"""Color grading stage — applies a named preset's tone curve."""

from __future__ import annotations

import numpy as np
import yaml

from studio.core.pipeline import RenderContext
from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)


class ColorGrader:
    name = "color_grader"

    def __call__(self, ctx: RenderContext) -> RenderContext:
        if ctx.image is None:
            return ctx

        preset = ctx.settings.pipeline.color_grade
        curve = self._load_preset(ctx, preset)
        if curve is None:
            return ctx

        img = ctx.image.astype(np.float32) / 255.0
        contrast = curve.get("contrast", 1.0)
        sat = curve.get("saturation", 1.0)
        img = np.clip((img - 0.5) * contrast + 0.5, 0, 1)
        gray = img.mean(axis=2, keepdims=True)
        img = np.clip(gray + (img - gray) * sat, 0, 1)
        ctx.image = (img * 255).astype(np.uint8)
        return ctx

    @staticmethod
    def _load_preset(ctx: RenderContext, name: str) -> dict | None:
        path = ctx.settings.paths.presets_dir / f"{name}.yaml"
        if not path.exists():
            _LOG.warning("preset %s not found at %s", name, path)
            return None
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}