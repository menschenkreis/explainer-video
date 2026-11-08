#!/usr/bin/env bash
# One-time setup: python venv with pymupdf (PDF text) + playwright (frame screenshots / mp4 export).
# Uses your installed Google Chrome, so no browser download is needed.
set -euo pipefail
VENV="${EV_VENV:-$HOME/.local/share/explainer-video/venv}"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" -q install --upgrade pip
  "$VENV/bin/pip" -q install pymupdf playwright
fi
command -v ffmpeg >/dev/null || { echo "ffmpeg missing: brew install ffmpeg"; exit 1; }
[ -d "/Applications/Google Chrome.app" ] || echo "note: Google Chrome not found; run '$VENV/bin/playwright install chromium' for export"
echo "ok  python: $VENV/bin/python"
