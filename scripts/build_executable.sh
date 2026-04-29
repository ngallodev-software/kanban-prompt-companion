#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_VERSION="$("$PYTHON_BIN" -c "from app.version import __version__; print(__version__)")"
PLATFORM="$("$PYTHON_BIN" -c "import platform; print(f'{platform.system().lower()}-{platform.machine().lower()}')")"
OUTPUT_NAME="kanban-prompt-companion-${APP_VERSION}-${PLATFORM}"

if [[ "$(uname -s)" == "Darwin" ]]; then
  DATA_SEP=":"
else
  DATA_SEP=":"
fi

"$PYTHON_BIN" -m pip install -q -e ".[build]"

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --name "$OUTPUT_NAME" \
  --add-data "templates${DATA_SEP}templates" \
  app/cli.py

echo "Built executable: dist/${OUTPUT_NAME}"
