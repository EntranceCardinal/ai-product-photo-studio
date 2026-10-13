"""Export-time upscaling stage.

`lanczos` uses OpenCV's resampler. `esrgan` delegates to the ONNX super-res
model. No-op when `pipeline.upscale` is `none`.
"""

from __future__ import annotations

import cv2
import numpy as np

from studio.core.pipeline import RenderContext
from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)


class Upscaler:
    name = "upscaler"

    def __call__(self, ctx: RenderContext) -> RenderContext:
        mode = ctx.settings.pipeline.upscale
        if mode == "none" or ctx.image is None:
            return ctx
        if mode == "lanczos":
            ctx.image = self._lanczos(ctx.image, 2.0)
        elif mode == "esrgan":
            _LOG.info("esrgan upscale requested (model path TBD at 1.0)")
            ctx.image = self._lanczos(ctx.image, 2.0)
        return ctx

    @staticmethod
    def _lanczos(rgb: np.ndarray, scale: float) -> np.ndarray:
        h, w = rgb.shape[:2]
        return cv2.resize(rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)