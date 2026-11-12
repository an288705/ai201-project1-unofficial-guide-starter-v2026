#!/usr/bin/env bash
# Sets up the pi coding agent (npm) and the Python virtual environment.
# Usage: ./setup.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "error: '$1' is required but not installed." >&2; exit 1; }
}

# --- pi (Node) ---------------------------------------------------------------
echo "==> Setting up pi"
need node
need npm
npm install
echo "    pi installed: run it with 'npx pi' (or ./node_modules/.bin/pi)"

# --- Python venv -------------------------------------------------------------
echo "==> Setting up Python virtual environment"
need python3
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# --- .env --------------------------------------------------------------------
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "==> Created .env from .env.example — paste your API key into it."
fi

echo
echo "Done. Activate the venv in each new terminal with:"
echo "    source .venv/bin/activate"
echo "Then verify with: python test.py"
