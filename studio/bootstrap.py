"""Entry point / bootstrap for AI Product Photo Studio.

Validates the environment, resolves the compute backend, warms the model
registry, then hands off to the Typer CLI.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from studio.cli.main import app as cli_app
from studio.config.settings import StudioSettings, load_settings
from studio.core.compute_backend import resolve_backend
from studio.models.registry import ModelRegistry
from studio.utils.logging_setup import get_logger

_LOG = get_logger(__name__)


@dataclass(slots=True)
class BootstrapReport:
    settings: StudioSettings
    backend: str
    weights_present: list[str] = field(default_factory=list)
    missing_weights: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return not self.missing_weights


def check_env(settings: StudioSettings | None = None) -> BootstrapReport:
    """Validate paths, resolve backend, and audit the weight registry."""
    cfg = settings or load_settings()
    backend = resolve_backend(cfg.compute.backend, cfg.compute.device_index)
    registry = ModelRegistry.from_config(cfg.paths.weights_dir)

    present: list[str] = []
    missing: list[str] = []
    for entry in registry.entries():
        (present if entry.path.exists() else missing).append(entry.file)

    report = BootstrapReport(settings=cfg, backend=backend, weights_present=present, missing_weights=missing)
    _LOG.info("bootstrap backend=%s present=%d missing=%d", backend, len(present), len(missing))
    return report


def main() -> int:
    """CLI entry point registered in pyproject `[project.scripts]`."""
    if "--check-env" in sys.argv:
        report = check_env()
        if not report.ready:
            _LOG.warning("missing weights: %s", ", ".join(report.missing_weights))
        return 0 if report.ready else 2
    cli_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())