"""Export stage — writes final renders to disk in configured formats."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from studio.core.pipeline import RenderContext
from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)


class Exporter:
    name = "exporter"

    def __call__(self, ctx: RenderContext) -> RenderContext:
        if ctx.image is None:
            ctx.errors.append("exporter: empty image")
            return ctx

        stem = Path(ctx.source_path).stem
        ctx.output_dir.mkdir(parents=True, exist_ok=True)

        for fmt in ctx.settings.export.formats:
            out = ctx.output_dir / f"{stem}_studio.{fmt}"
            self._write(ctx.image, out, fmt, ctx)
            _LOG.info("wrote %s", out.name)
        return ctx

    @staticmethod
    def _write(rgb: np.ndarray, path: Path, fmt: str, ctx: RenderContext) -> None:
        img = Image.fromarray(rgb, mode="RGB")
        kwargs: dict[str, int] = {}
        if fmt in ("jpg", "jpeg"):
            kwargs["quality"] = ctx.settings.export.jpg_quality
            kwargs["subsampling"] = 0
        elif fmt == "webp":
            kwargs["quality"] = ctx.settings.export.webp_quality
        img.save(path, **kwargs)