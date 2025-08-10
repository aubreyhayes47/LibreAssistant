# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Application entrypoints and FastAPI app factory."""

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .kernel import kernel
from .plugins import echo


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="LibreAssistant")

    # Register built-in plugins
    echo.register()

    @app.get("/")
    def read_root() -> Dict[str, str]:
        return {"message": "LibreAssistant API"}

    class InvokeRequest(BaseModel):
        plugin: str
        payload: Dict[str, Any]
        user_id: str

    @app.post("/api/v1/invoke")
    def invoke(request: InvokeRequest) -> Dict[str, Any]:
        """Invoke a registered plugin through the microkernel."""
        try:
            result = kernel.invoke(request.plugin, request.user_id, request.payload)
        except KeyError as exc:  # pragma: no cover - error branch
            raise HTTPException(status_code=404, detail="Plugin not found") from exc
        state = kernel.get_state(request.user_id)
        return {"result": result, "state": state}

    return app


app = create_app()
