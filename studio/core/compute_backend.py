"""Compute backend resolution.

Picks CUDA, DirectML, or CPU based on the requested backend and what's
actually installed. Never raises on a missing GPU — the CPU path is always
a valid fallback for this tool.
"""

from __future__ import annotations

import importlib.util

from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)

_SUPPORTED = ("auto", "cuda", "directml", "cpu")


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def resolve_backend(requested: str, device_index: int = 0) -> str:
    """Return the concrete backend string to use at runtime."""
    if requested not in _SUPPORTED:
        _LOG.warning("unknown backend %r, falling back to auto", requested)
        requested = "auto"

    if requested in ("auto", "cuda") and _has("torch"):
        try:
            import torch  # noqa: PLC0415

            if torch.cuda.is_available() and torch.cuda.device_count() > device_index:
                return "cuda"
        except Exception as exc:  # pragma: no cover - driver-dependent
            _LOG.debug("cuda probe failed: %s", exc)

    if requested in ("auto", "directml") and _has("torch_directml"):
        return "directml"

    if requested == "cuda":
        _LOG.warning("cuda requested but unavailable; using cpu")
    return "cpu"