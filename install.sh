#!/usr/bin/env bash
# Installs explainer-video: links it as a Claude Code skill, puts an `ev` command on your PATH, sets up the helper venv.
#
#   ./install.sh                 interactive; asks before touching your shell config
#   ./install.sh --yes           also add the bin dir to PATH in your shell rc without asking
#   ./install.sh --no-path       never edit shell config (just print the line to add)
#   ./install.sh --no-skill      don't link into ~/.claude/skills (use with other agents / plain CLI)
#   ./install.sh --no-setup      skip the helper venv (pymupdf + playwright)
#
# Environment overrides: EV_BIN_DIR (default ~/.local/bin), CLAUDE_SKILLS_DIR (default ~/.claude/skills),
# EV_VENV (default ~/.local/share/explainer-video/venv).
set -euo pipefail
HERE="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${EV_BIN_DIR:-$HOME/.local/bin}"
SKILLS="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
PATH_MODE=ask; SKILL=1; SETUP=1
for a in "$@"; do
  case "$a" in
    -y|--yes) PATH_MODE=yes ;;
    --no-path) PATH_MODE=no ;;
    --no-skill) SKILL=0 ;;
    --no-setup) SETUP=0 ;;
    -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $a (see --help)" >&2; exit 2 ;;
  esac
done

# 1 · skill link
if [ "$SKILL" = 1 ]; then
  mkdir -p "$SKILLS"
  if [ "$(cd -P "$SKILLS" && pwd)/explainer-video" != "$HERE" ]; then
    if [ -e "$SKILLS/explainer-video" ] && [ ! -L "$SKILLS/explainer-video" ]; then
      echo "! $SKILLS/explainer-video exists and is not a symlink – left untouched"
    else
      ln -sfn "$HERE" "$SKILLS/explainer-video"
      echo "✓ skill linked:  $SKILLS/explainer-video → $HERE"
    fi
  fi
fi

# 2 · `ev` command: a tiny wrapper (not a symlink), so it works no matter how the bin dir is resolved
mkdir -p "$BIN"
if [ -e "$BIN/ev" ] && ! grep -q "explainer-video" "$BIN/ev" 2>/dev/null; then
  mv "$BIN/ev" "$BIN/ev.bak.$(date +%s)"; echo "! existing $BIN/ev moved aside (.bak)"
fi
rm -f "$BIN/ev"
printf '#!/usr/bin/env bash\n# explainer-video launcher (written by install.sh)\nexec "%s/ev" "$@"\n' "$HERE" > "$BIN/ev"
chmod +x "$BIN/ev"
echo "✓ command:       $BIN/ev"

# 3 · PATH (only with consent)
case ":$PATH:" in
  *":$BIN:"*) ;;
  *)
    sh_name="$(basename "${SHELL:-sh}")"
    case "$sh_name" in
      zsh)  RC="${ZDOTDIR:-$HOME}/.zshrc";  LINE="export PATH=\"$BIN:\$PATH\"" ;;
      bash) RC="$HOME/.bashrc"; [ "$(uname)" = Darwin ] && RC="$HOME/.bash_profile"; LINE="export PATH=\"$BIN:\$PATH\"" ;;
      fish) RC="$HOME/.config/fish/conf.d/explainer-video.fish"; LINE="fish_add_path \"$BIN\"" ;;
      *)    RC="$HOME/.profile"; LINE="export PATH=\"$BIN:\$PATH\"" ;;
    esac
    if [ "$PATH_MODE" = ask ] && [ -t 0 ]; then
      printf '? %s is not on your PATH. Add this line to %s?\n    %s\n  [y/N] ' "$BIN" "$RC" "$LINE"
      read -r reply || reply=""; case "$reply" in y|Y|yes|j|J|ja) PATH_MODE=yes ;; *) PATH_MODE=no ;; esac
    fi
    if [ "$PATH_MODE" = yes ]; then
      if [ -f "$RC" ] && grep -qF "$LINE" "$RC"; then echo "✓ PATH line already in $RC"
      else mkdir -p "$(dirname "$RC")"; printf '\n# explainer-video\n%s\n' "$LINE" >> "$RC"; echo "✓ added to $RC – open a new terminal (or: source $RC)"; fi
    else
      echo "• $BIN is not on your PATH. Shell config left untouched. To use plain \`ev\`, add to $RC:"
      echo "    $LINE"
      echo "  (or call it as $BIN/ev)"
    fi ;;
esac

# 4 · helpers + check
[ "$SETUP" = 1 ] && bash "$HERE/scripts/setup.sh"
"$BIN/ev" doctor || true
echo
echo "Next:  $BIN/ev preview $HERE/examples/rainbow     # no API key needed"
