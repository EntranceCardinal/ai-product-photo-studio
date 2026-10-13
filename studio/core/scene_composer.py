"""Scene compositor — places a cut-out product onto a background plate.

Blends the product mask, synthesized shadow, and optional reflection layer
into a single RGB frame. Deterministic given the same inputs.
"""

from __future__ import annotations

import numpy as np

from studio.utils.image_ops import alpha_composite


def compose_scene(
    product_rgb: np.ndarray,
    product_alpha: np.ndarray,
    background_rgb: np.ndarray,
    shadow: np.ndarray | None = None,
    reflection: np.ndarray | None = None,
) -> np.ndarray:
    """Composite product + shadow + reflection over the background plate.

    All layers must share HxW. Raises ValueError on a shape mismatch rather
    than broadcasting silently.
    """
    h, w = product_alpha.shape
    if product_rgb.shape[:2] != (h, w) or background_rgb.shape[:2] != (h, w):
        raise ValueError("product, alpha and background must share HxW")

    base = background_rgb.astype(np.float32).copy()

    if shadow is not None:
        if shadow.shape != (h, w):
            raise ValueError("shadow layer must be HxW")
        s = shadow.astype(np.float32)[..., None] / 255.0
        base *= 1.0 - 0.55 * s

    if reflection is not None:
        if reflection.shape[:2] != (h, w):
            raise ValueError("reflection layer must be HxW")
        r = reflection.astype(np.float32) / 255.0
        base = np.clip(base + r[..., None] * 18.0, 0, 255)

    return alpha_composite(product_rgb, product_alpha, base.astype(np.uint8))