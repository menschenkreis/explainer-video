#!/usr/bin/env bash
# Installs explainer-video as a Claude Code (and Codex) skill and puts the `ev` command on your PATH.
# Usage:  ./install.sh            (from a clone of this repo)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$SKILLS" "$HOME/.local/bin"
link_skill() {   # $1 = skills dir; never nest a link inside an existing real folder
  local dst="$1/explainer-video"
  if [ "$(cd "$dst" 2>/dev/null && pwd -P)" = "$HERE" ]; then echo "✓ skill already installed: $dst"; return; fi
  if [ -d "$dst" ] && [ ! -L "$dst" ]; then
    echo "! $dst is a separate copy, not linked to $HERE – rename it (e.g. ${dst}.old) and re-run, so only ONE copy is in use"; return
  fi
  mkdir -p "$1"; ln -sfn "$HERE" "$dst"; echo "✓ skill linked:  $dst  →  $HERE"
}
link_skill "$SKILLS"
# Codex reads the same SKILL.md format from ~/.codex/skills (or $CODEX_HOME/skills)
[ -d "${CODEX_HOME:-$HOME/.codex}" ] && link_skill "${CODEX_HOME:-$HOME/.codex}/skills"
ln -sfn "$HERE/ev" "$HOME/.local/bin/ev"
echo "✓ command:       ~/.local/bin/ev   (add ~/.local/bin to PATH if 'ev' is not found)"
bash "$HERE/scripts/setup.sh"
"$HERE/ev" doctor || true
echo
echo "Next:  ev preview $HERE/examples/rainbow     # no API key needed"
