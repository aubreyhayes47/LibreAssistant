#!/usr/bin/env bash
set -e

# Create Python virtual environment if not present
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

pip install -r backend/requirements.txt

# Install frontend dependencies
pushd frontend >/dev/null
npm install
popd >/dev/null

echo "Setup complete. Activate with 'source .venv/bin/activate'"
