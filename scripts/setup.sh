#!/usr/bin/env bash
# One-time setup: python venv with pymupdf (PDF text) + playwright (frame screenshots / mp4 export).
# Uses an installed Google Chrome / Chromium if there is one; otherwise downloads playwright's chromium (EV_NO_BROWSER=1 to skip).
set -euo pipefail
VENV="${EV_VENV:-$HOME/.local/share/explainer-video/venv}"
if [ ! -x "$VENV/bin/python" ]; then
  mkdir -p "$(dirname "$VENV")"
  python3 -m venv "$VENV" || { echo "python3 -m venv failed (Debian/Ubuntu: apt install python3-venv)"; exit 1; }
  "$VENV/bin/pip" -q install --upgrade pip
  "$VENV/bin/pip" -q install pymupdf playwright
fi
echo "ok  python: $VENV/bin/python"

if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  case "$(uname)" in
    Darwin) hint="brew install ffmpeg" ;;
    Linux)  hint="sudo apt install ffmpeg   (Fedora: sudo dnf install ffmpeg · Arch: sudo pacman -S ffmpeg)" ;;
    *)      hint="install ffmpeg from https://ffmpeg.org and put it on PATH" ;;
  esac
  echo "!!  ffmpeg/ffprobe missing (needed for narration, sheets and MP4): $hint"
fi

chrome=""
for c in "/Applications/Google Chrome.app" "/Applications/Chromium.app"; do [ -d "$c" ] && chrome="$c"; done
for c in google-chrome google-chrome-stable chromium chromium-browser; do command -v "$c" >/dev/null && chrome="$c"; done
if [ -n "$chrome" ]; then echo "ok  browser: $chrome"
elif [ "${EV_NO_BROWSER:-0}" = 1 ]; then echo "note: no Chrome/Chromium found; for screenshots + MP4 run: $VENV/bin/playwright install chromium"
else echo "…   no Chrome/Chromium found – installing playwright's chromium"; "$VENV/bin/playwright" install chromium; fi
