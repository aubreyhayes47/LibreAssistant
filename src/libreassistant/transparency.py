# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Transparency utilities for Bill of Materials and system health."""

from __future__ import annotations

import os
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Set

import importlib.metadata

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older versions
    tomllib = None  # type: ignore


# Module-level caches to avoid repeated scanning
_DEPENDENCIES: List[str] | None = None
_MODELS_CACHE: Dict[Path, List[str]] = {}
_DATASETS_CACHE: Dict[Path, List[str]] = {}
_PYPROJECT_PACKAGES: Set[str] | None = None


class HealthMonitor:
    """Simple in-memory tracker for system health metrics."""

    def __init__(self) -> None:
        self.start_time = time.time()
        self.requests = 0
        self.error_count = 0
        self.errors: Deque[str] = deque(maxlen=100)

    def record_request(self) -> None:
        """Increment the total request count."""
        self.requests += 1

    def record_error(self, message: str) -> None:
        """Record an error event with a message."""
        self.error_count += 1
        self.errors.append(message)

    def get_status(self) -> Dict[str, Any]:
        """Return a snapshot of current system health metrics."""
        status = "error" if self.error_count > 0 else "ok"
        return {
            "status": status,
            "uptime": time.time() - self.start_time,
            "requests": self.requests,
            "error_count": self.error_count,
            "errors": list(self.errors),
        }


def _load_pyproject_packages() -> Set[str]:
    """Load package names declared in pyproject.toml."""
    global _PYPROJECT_PACKAGES
    if _PYPROJECT_PACKAGES is not None:
        return _PYPROJECT_PACKAGES
    if tomllib is None:  # pragma: no cover - Python <3.11 without tomli
        _PYPROJECT_PACKAGES = set()
        return _PYPROJECT_PACKAGES
    project_root = Path(__file__).resolve().parents[2]
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():  # pragma: no cover - missing file
        _PYPROJECT_PACKAGES = set()
        return _PYPROJECT_PACKAGES
    try:
        data = tomllib.loads(pyproject_path.read_text())
    except Exception:  # pragma: no cover - malformed file
        _PYPROJECT_PACKAGES = set()
        return _PYPROJECT_PACKAGES
    project = data.get("project", {})
    deps = list(project.get("dependencies", []))
    opt = project.get("optional-dependencies", {})
    for group in opt.values():
        deps.extend(group)
    names: Set[str] = set()
    for dep in deps:
        name = dep.split()[0].split("[")[0].lower()
        names.add(name)
    _PYPROJECT_PACKAGES = names
    return _PYPROJECT_PACKAGES


def _scan(path: Path) -> List[str]:
    """Return sorted non-hidden entries for the given path."""
    if not path.exists():
        return []
    if path.is_file():
        return [path.name]
    items = [
        p.name
        for p in path.iterdir()
        if (p.is_file() or p.is_dir()) and not p.name.startswith(".")
    ]
    return sorted(items)


def get_bill_of_materials() -> Dict[str, List[str]]:
    """Gather a list of installed dependencies, models, and datasets."""
    global _DEPENDENCIES, _MODELS_CACHE, _DATASETS_CACHE

    if _DEPENDENCIES is None:
        declared = _load_pyproject_packages()
        deps = [
            f"{dist.metadata['Name']}=={dist.version}"
            for dist in importlib.metadata.distributions()
            if not declared or dist.metadata['Name'].lower() in declared
        ]
        _DEPENDENCIES = sorted(deps)

    models_dir = Path(os.environ.get("LA_MODELS_DIR", "models"))
    datasets_dir = Path(os.environ.get("LA_DATASETS_DIR", "datasets"))

    if models_dir not in _MODELS_CACHE:
        _MODELS_CACHE[models_dir] = _scan(models_dir)
    if datasets_dir not in _DATASETS_CACHE:
        _DATASETS_CACHE[datasets_dir] = _scan(datasets_dir)

    return {
        "dependencies": _DEPENDENCIES,
        "models": _MODELS_CACHE[models_dir],
        "datasets": _DATASETS_CACHE[datasets_dir],
    }
