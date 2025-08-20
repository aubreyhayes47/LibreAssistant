# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Application entrypoints and FastAPI app factory."""

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from pathlib import Path
import json

from .kernel import kernel
from .plugins import echo, file_io, law_by_keystone, think_tank
from .providers import providers
from .providers.cloud import CloudProvider
from .providers.local import LocalProvider
from .vault import DataVault
from .transparency import HealthMonitor, get_bill_of_materials
from .themes import get_theme_css


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="LibreAssistant")

    monitor = HealthMonitor()

    @app.middleware("http")
    async def record_metrics(request: Request, call_next):
        monitor.record_request()
        return await call_next(request)

    @app.middleware("http")
    async def catch_errors(request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - error branch
            monitor.record_error(str(exc))
            raise
        if response.status_code >= 500:  # pragma: no cover - error branch
            monitor.record_error(f"HTTP {response.status_code}")
        return response

    @app.middleware("http")
    async def set_csp(request: Request, call_next):
        response = await call_next(request)
        csp = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "object-src 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
        return response

    # Register built-in plugins
    echo.register()
    file_io.register()
    law_by_keystone.register()
    think_tank.register()

    # Register default providers
    providers.register("cloud", CloudProvider())
    providers.register("local", LocalProvider())

    vault = DataVault()

    @app.on_event("shutdown")
    def _cleanup_plugins() -> None:
        kernel.shutdown()

    registry_file = Path("config/mcp.registry.json")
    if registry_file.exists():
        registry = json.loads(registry_file.read_text())
        mcp_plugins: List[str] = [
            s["name"] for s in registry.get("servers", [])
        ]
    else:  # pragma: no cover - file may be missing in tests
        mcp_plugins = []

    @app.get("/")
    def read_root() -> Dict[str, str]:
        return {"message": "LibreAssistant API"}

    class InvokeRequest(BaseModel):
        plugin: str
        payload: Dict[str, Any]
        user_id: str
        granted: bool | None = None

    @app.post("/api/v1/invoke")
    def invoke(request: InvokeRequest) -> Dict[str, Any]:
        """Invoke a registered plugin through the microkernel."""
        try:
            result = kernel.invoke(
                request.plugin, request.user_id, request.payload
            )
        except KeyError as exc:  # pragma: no cover - error branch
            raise HTTPException(
                status_code=404, detail="Plugin not found"
            ) from exc
        state = kernel.get_state(request.user_id)
        history = state.setdefault("history", [])
        entry: Dict[str, Any] = {
            "plugin": request.plugin,
            "payload": request.payload,
        }
        if request.granted is not None:
            entry["granted"] = request.granted
        history.append(entry)
        return {"result": result, "state": state}

    @app.get("/api/v1/history/{user_id}")
    def get_history(user_id: str) -> Dict[str, Any]:
        """Retrieve a user's past plugin invocations."""
        state = kernel.get_state(user_id)
        return {"history": state.get("history", [])}

    @app.get("/api/v1/audit/file")
    def get_file_audit() -> Dict[str, Any]:
        log_path = Path("logs/file_io_audit.ndjson")
        if not log_path.exists():
            return {"logs": []}
        lines = [
            json.loads(l)
            for l in log_path.read_text().splitlines()
            if l.strip()
        ]
        return {"logs": lines}

    @app.get("/api/v1/audit/file/{user_id}")
    def get_file_audit_user(user_id: str) -> Dict[str, Any]:
        log_path = Path("logs/file_io_audit.ndjson")
        if not log_path.exists():
            return {"logs": []}
        lines = [
            json.loads(l)
            for l in log_path.read_text().splitlines()
            if l.strip()
        ]
        filtered = [e for e in lines if e.get("user_id") == user_id]
        return {"logs": filtered}

    class HistoryEntry(BaseModel):
        plugin: str
        payload: Dict[str, Any]
        granted: bool

    @app.post("/api/v1/history/{user_id}")
    def record_history(user_id: str, entry: HistoryEntry) -> Dict[str, str]:
        state = kernel.get_state(user_id)
        history = state.setdefault("history", [])
        history.append(
            {
                "plugin": entry.plugin,
                "payload": entry.payload,
                "granted": entry.granted,
            }
        )
        return {"status": "ok"}

    @app.get("/api/v1/mcp/plugins")
    def list_mcp_plugins() -> Dict[str, List[str]]:
        return {"plugins": mcp_plugins}

    class VaultData(BaseModel):
        data: Dict[str, Any]

    @app.post("/api/v1/vault/{user_id}")
    def store_data(user_id: str, request: VaultData) -> Dict[str, str]:
        try:
            vault.store(user_id, request.data)
        except PermissionError:
            raise HTTPException(status_code=403, detail="Consent required")
        return {"status": "ok"}

    @app.get("/api/v1/vault/{user_id}")
    def get_data(user_id: str) -> Dict[str, Any]:
        try:
            data = vault.retrieve(user_id)
        except PermissionError:
            raise HTTPException(status_code=403, detail="Consent required")
        return {"data": data}

    @app.get("/api/v1/vault/{user_id}/export")
    def export_data(user_id: str) -> Dict[str, Any]:
        try:
            data = vault.export(user_id)
        except PermissionError:
            raise HTTPException(status_code=403, detail="Consent required")
        return {"data": data}

    @app.delete("/api/v1/vault/{user_id}")
    def delete_data(user_id: str) -> Dict[str, str]:
        try:
            vault.delete(user_id)
        except PermissionError:
            raise HTTPException(status_code=403, detail="Consent required")
        return {"status": "deleted"}

    class Consent(BaseModel):
        consent: bool

    @app.post("/api/v1/consent/{user_id}")
    def set_consent(user_id: str, request: Consent) -> Dict[str, str]:
        vault.set_consent(user_id, request.consent)
        return {"status": "ok"}

    @app.get("/api/v1/consent/{user_id}")
    def get_consent(user_id: str) -> Dict[str, bool]:
        return {"consent": vault.get_consent(user_id)}

    class ProviderKey(BaseModel):
        key: str

    @app.post("/api/v1/providers/{name}/key")
    def set_provider_key(name: str, request: ProviderKey) -> Dict[str, str]:
        providers.set_api_key(name, request.key)
        return {"status": "ok"}

    class GenerateRequest(BaseModel):
        provider: str
        prompt: str

    @app.post("/api/v1/generate")
    def generate(request: GenerateRequest) -> Dict[str, str]:
        try:
            result = providers.generate(request.provider, request.prompt)
        except KeyError as exc:  # pragma: no cover - error branch
            raise HTTPException(
                status_code=404, detail="Provider not found"
            ) from exc
        except ValueError as exc:  # pragma: no cover - error branch
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"result": result}

    @app.get("/api/v1/themes/{theme_id}.css")
    def theme_css(theme_id: str) -> Response:
        try:
            css = get_theme_css(theme_id)
        except FileNotFoundError as exc:  # pragma: no cover - error branch
            raise HTTPException(
                status_code=404, detail="Theme not found"
            ) from exc
        return Response(css, media_type="text/css")

    @app.get("/api/v1/bom")
    def get_bom() -> Dict[str, Any]:
        """Return the application's Bill of Materials."""
        return get_bill_of_materials()

    @app.get("/api/v1/health")
    def health() -> Dict[str, Any]:
        """Expose basic system health metrics."""
        return monitor.get_status()

    return app


app = create_app()
