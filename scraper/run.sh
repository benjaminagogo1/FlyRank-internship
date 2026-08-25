#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

VENV_DIR="${VENV_DIR:-.venv}"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Creating virtual environment in $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c 'import requests, pydantic' >/dev/null 2>&1; then
  echo "Installing scraper dependencies"
  "$VENV_DIR/bin/python" -m pip install -r requirements.txt
fi

exec "$VENV_DIR/bin/python" src/main.py "$@"
