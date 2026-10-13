"""Render pipeline orchestration.

Chains the stages in fixed order: segment -> relight -> shadow -> reflect
-> upscale -> grade -> export. Each stage is a callable taking and returning
a `RenderContext`. Stages may short-circuit by returning the context
unchanged when the corresponding toggle is off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

import numpy as np

from studio.config.settings import StudioSettings
from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)


class Stage(Protocol):
    name: str

    def __call__(self, ctx: "RenderContext") -> "RenderContext": ...


@dataclass(slots=True)
class RenderContext:
    source_path: Path
    output_dir: Path
    settings: StudioSettings
    image: np.ndarray | None = None          # HxWx3 uint8 RGB
    mask: np.ndarray | None = None           # HxW uint8 alpha
    shadow: np.ndarray | None = None         # HxW uint8
    reflections: np.ndarray | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class Pipeline:
    """Ordered, fail-soft stage runner for the product-photo generator."""

    def __init__(self, stages: list[Stage]) -> None:
        if not stages:
            raise ValueError("pipeline needs at least one stage")
        self._stages = stages

    def run(self, ctx: RenderContext) -> RenderContext:
        for stage in self._stages:
            try:
                ctx = stage(ctx)
            except Exception as exc:  # noqa: BLE001 - pipeline is fail-soft
                msg = f"stage {stage.name!r} failed: {exc}"
                _LOG.error(msg)
                ctx.errors.append(msg)
                break
        return ctx

    @property
    def stage_names(self) -> list[str]:
        return [s.name for s in self._stages]


def build_default_pipeline() -> Pipeline:
    """Wire the standard stage set. Imported lazily to avoid GPU init cost."""
    from studio.pipeline.background_segmenter import BackgroundSegmenter
    from studio.pipeline.color_grader import ColorGrader
    from studio.pipeline.exporter import Exporter
    from studio.pipeline.reflection_pass import ReflectionPass
    from studio.pipeline.relight_engine import RelightEngine
    from studio.pipeline.shadow_synthesizer import ShadowSynthesizer
    from studio.pipeline.upscaler import Upscaler

    return Pipeline([
        BackgroundSegmenter(),
        RelightEngine(),
        ShadowSynthesizer(),
        ReflectionPass(),
        Upscaler(),
        ColorGrader(),
        Exporter(),
    ])