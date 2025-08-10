# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

"""Run the LibreAssistant application with Uvicorn."""

import uvicorn

from .main import app


def main() -> None:
    """Run the Uvicorn development server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
