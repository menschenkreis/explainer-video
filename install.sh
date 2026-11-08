#!/usr/bin/env bash
# Installs explainer-video as a Claude Code skill and puts the `ev` command on your PATH.
# Usage:  ./install.sh            (from a clone of this repo)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$SKILLS" "$HOME/.local/bin"
if [ "$HERE" != "$SKILLS/explainer-video" ]; then
  ln -sfn "$HERE" "$SKILLS/explainer-video"
  echo "✓ skill linked:  $SKILLS/explainer-video  →  $HERE"
fi
ln -sfn "$HERE/ev" "$HOME/.local/bin/ev"
echo "✓ command:       ~/.local/bin/ev   (add ~/.local/bin to PATH if 'ev' is not found)"
bash "$HERE/scripts/setup.sh"
"$HERE/ev" doctor || true
echo
echo "Next:  ev preview $HERE/examples/rainbow     # no API key needed"
