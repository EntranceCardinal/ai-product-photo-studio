"""Background segmentation stage.

Runs the ONNX bg_segmenter model to produce a soft alpha matte around the
product. Falls back to a GrabCut pass when the model is unavailable.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from studio.core.pipeline import RenderContext
from studio.models.loaders.onnx_loader import OnnxModel
from studio.utils.image_ops import load_rgb, resize_keep_aspect
from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)


class BackgroundSegmenter:
    name = "background_segmenter"

    def __init__(self, weights_path: Path | None = None) -> None:
        self._weights_path = weights_path
        self._model: OnnxModel | None = None

    def _ensure_model(self, ctx: RenderContext) -> OnnxModel | None:
        if self._model is not None:
            return self._model
        path = self._weights_path or (ctx.settings.paths.weights_dir / "bg_segmenter_v3.onnx")
        if not path.exists():
            _LOG.warning("bg_segmenter weights missing at %s; using grabcut fallback", path)
            return None
        self._model = OnnxModel(path)
        return self._model

    def __call__(self, ctx: RenderContext) -> RenderContext:
        if not ctx.settings.pipeline.segment_background:
            return ctx

        rgb = load_rgb(ctx.source_path)
        rgb, _scale = resize_keep_aspect(rgb, ctx.settings.compute.max_resolution)
        ctx.image = rgb

        model = self._ensure_model(ctx)
        if model is None:
            ctx.mask = self._grabcut_mask(rgb)
            return ctx

        inp = model.preprocess(rgb)
        out = model.run(inp)
        ctx.mask = model.postprocess_alpha(out, rgb.shape[:2])
        return ctx

    @staticmethod
    def _grabcut_mask(rgb: np.ndarray) -> np.ndarray:
        import cv2  # noqa: PLC0415

        h, w = rgb.shape[:2]
        rect = (int(w * 0.08), int(h * 0.08), int(w * 0.84), int(h * 0.84))
        mask = np.zeros((h, w), np.uint8)
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(rgb, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
        return np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)