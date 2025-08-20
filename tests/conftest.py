# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Test configuration and fixtures."""

from __future__ import annotations

import pathlib
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Add the src directory to the Python path so the package can be imported
# without installation.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from libreassistant.main import app  # noqa: E402
from libreassistant.kernel import kernel  # noqa: E402
from libreassistant.plugins.echo import (  # noqa: E402
    register as register_echo,
)
from libreassistant.providers import providers  # noqa: E402
from libreassistant.providers.cloud import CloudProvider  # noqa: E402
from libreassistant.providers.local import LocalProvider  # noqa: E402


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def reset_kernel() -> Generator[None, None, None]:
    """Reset the microkernel between tests."""
    kernel.reset()
    register_echo()
    providers.reset()
    providers.register("cloud", CloudProvider())
    providers.register("local", LocalProvider())
    yield
