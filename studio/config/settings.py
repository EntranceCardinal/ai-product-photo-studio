"""Typed settings loader.

Merges `config/default.yaml` with an optional `config/local.yaml` override
and validates through Pydantic v2. Environment variables prefixed with
STUDIO_ win over both.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_YAML = _REPO_ROOT / "config" / "default.yaml"
_LOCAL_YAML = _REPO_ROOT / "config" / "local.yaml"


class AppSection(BaseModel):
    name: str = "AI Product Photo Studio"
    version: str = "0.6.3"
    locale: str = "en_US"


class PathsSection(BaseModel):
    weights_dir: Path
    outputs_dir: Path
    cache_dir: Path
    presets_dir: Path


class ComputeSection(BaseModel):
    backend: str = "auto"
    device_index: int = 0
    fp16: bool = True
    max_resolution: int = Field(default=4096, ge=256, le=8192)
    batch_size: int = Field(default=4, ge=1, le=64)


class PipelineSection(BaseModel):
    segment_background: bool = True
    relight: bool = True
    shadow_synthesis: bool = True
    reflection_pass: bool = True
    upscale: str = "lanczos"
    color_grade: str = "studio_neutral"


class ExportSection(BaseModel):
    formats: list[str] = ["png", "jpg", "webp"]
    jpg_quality: int = Field(default=92, ge=1, le=100)
    webp_quality: int = Field(default=88, ge=1, le=100)
    embed_icc: bool = True
    transparent_bg: bool = False


class LoggingSection(BaseModel):
    level: str = "INFO"
    json: bool = False
    file: Path | None = None


class StudioSettings(BaseModel):
    app: AppSection
    paths: PathsSection
    compute: ComputeSection
    pipeline: PipelineSection
    export: ExportSection
    logging: LoggingSection

    def resolve_paths(self) -> StudioSettings:
        """Make relative paths absolute against the repo root."""
        for name in ("weights_dir", "outputs_dir", "cache_dir", "presets_dir"):
            p: Path = getattr(self.paths, name)
            if not p.is_absolute():
                setattr(self.paths, name, (_REPO_ROOT / p).resolve())
        return self


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def _apply_env_overrides(raw: dict) -> dict:
    backend = os.environ.get("STUDIO_BACKEND")
    if backend:
        raw.setdefault("compute", {})["backend"] = backend
    level = os.environ.get("STUDIO_LOG_LEVEL")
    if level:
        raw.setdefault("logging", {})["level"] = level
    return raw


def load_settings(default_path: Path | None = None, local_path: Path | None = None) -> StudioSettings:
    """Load, merge, and validate studio settings."""
    d_path = default_path or _DEFAULT_YAML
    l_path = local_path or _LOCAL_YAML

    with d_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if l_path.exists():
        with l_path.open("r", encoding="utf-8") as fh:
            raw = _deep_merge(raw, yaml.safe_load(fh) or {})

    raw = _apply_env_overrides(raw)
    return StudioSettings.model_validate(raw).resolve_paths()