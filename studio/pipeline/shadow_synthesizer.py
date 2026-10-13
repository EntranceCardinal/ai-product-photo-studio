"""Contact-shadow synthesis.

Generates a soft ground shadow under the product using the alpha matte and
a configurable light direction. Output is a single-channel HxW layer.
"""

from __future__ import annotations

import cv2
import numpy as np

from studio.core.pipeline import RenderContext


class ShadowSynthesizer:
    name = "shadow_synthesizer"

    def __init__(self, opacity: float = 0.55, blur_px: int = 41) -> None:
        self._opacity = opacity
        self._blur_px = blur_px | 1  # force odd kernel

    def __call__(self, ctx: RenderContext) -> RenderContext:
        if not ctx.settings.pipeline.shadow_synthesis or ctx.mask is None:
            return ctx

        mask = ctx.mask
        h, w = mask.shape

        offset = int(max(h, w) * 0.02)
        m = np.roll(mask, (offset, offset), axis=(0, 1))
        blurred = cv2.GaussianBlur(m, (self._blur_px, self._blur_px), 0)

        shadow = (blurred.astype(np.float32) * self._opacity).clip(0, 255)
        ctx.shadow = shadow.astype(np.uint8)
        return ctx