# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Test configuration and fixtures."""

from __future__ import annotations

import pathlib
import shutil
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Add the src directory to the Python path so the package can be imported
# without installation.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import os
import sqlite3
import types

# Provide a lightweight stub for the optional pysqlcipher3 dependency used by
# the database module so tests can run without the compiled extension.
pysqlcipher3_stub = types.ModuleType("pysqlcipher3")
setattr(pysqlcipher3_stub, "dbapi2", sqlite3)
sys.modules.setdefault("pysqlcipher3", pysqlcipher3_stub)
sys.modules.setdefault("pysqlcipher3.dbapi2", sqlite3)

os.environ["LIBRE_DB_PATH"] = ":memory:"
os.environ["LIBRE_DB_KEY"] = "test-key"

if shutil.which("node") is None:
    # Mock out MCP-based plugins when Node.js isn't available to keep tests
    # hermetic. These plugins would otherwise spawn a Node server during app
    # creation.
    from libreassistant.plugins import law_by_keystone as _law_by_keystone  # type: ignore  # noqa: E402
    from libreassistant.plugins import think_tank as _think_tank  # type: ignore  # noqa: E402

    _law_by_keystone.register = lambda: None  # type: ignore
    _think_tank.register = lambda: None  # type: ignore

from libreassistant.main import app  # noqa: E402
from libreassistant.kernel import kernel  # noqa: E402
from libreassistant.plugins.echo import (  # noqa: E402
    register as register_echo,
)
from libreassistant.providers import providers  # noqa: E402
from libreassistant.providers.cloud import CloudProvider  # noqa: E402
from libreassistant.providers.local import LocalProvider  # noqa: E402
from libreassistant import db as app_db  # noqa: E402


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
    app_db.clear()
    yield
    app_db.close_conn()
