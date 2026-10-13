"""Reflection pass — mirrors the product below its contact line.

Adds a soft vertical flip with a falloff gradient so glossy surfaces read
as sitting on a reflective plate.
"""

from __future__ import annotations

import numpy as np

from studio.core.pipeline import RenderContext


class ReflectionPass:
    name = "reflection_pass"

    def __init__(self, strength: float = 0.35, fade: float = 2.4) -> None:
        self._strength = strength
        self._fade = fade

    def __call__(self, ctx: RenderContext) -> RenderContext:
        if not ctx.settings.pipeline.reflection_pass or ctx.image is None or ctx.mask is None:
            return ctx

        h, w = ctx.mask.shape
        product = ctx.image.astype(np.float32) * (ctx.mask[..., None] / 255.0)
        flipped = product[::-1, :, :]

        ramp = np.linspace(1.0, 0.0, h, dtype=np.float32) ** self._fade
        refl = flipped * ramp[:, None, None] * self._strength
        ctx.reflections = np.clip(refl[..., 1], 0, 255).astype(np.uint8)  # green channel as luma proxy
        return ctx