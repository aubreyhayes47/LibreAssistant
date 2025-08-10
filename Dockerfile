# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project and install runtime dependencies
COPY . /app
RUN pip install --no-cache-dir .

# Default command
CMD ["python", "-m", "libreassistant"]
