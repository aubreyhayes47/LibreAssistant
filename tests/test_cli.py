# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Tests for the module entrypoint executed as a script."""

from __future__ import annotations

import runpy

import uvicorn

from libreassistant.main import app


def test_module_main_invokes_uvicorn(monkeypatch) -> None:
    """Running the module should call ``uvicorn.run`` with the app."""

    called = {}

    def fake_run(app_, host, port):
        called.update({"app": app_, "host": host, "port": port})

    monkeypatch.setattr(uvicorn, "run", fake_run)

    runpy.run_module("libreassistant.__main__", run_name="__main__")

    assert called == {"app": app, "host": "0.0.0.0", "port": 8000}
