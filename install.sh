#!/usr/bin/env bash
# kickback installer — copies one script into your PATH. No pip packages.
# Requirements: macOS, python3, openssl (both ship with macOS / Homebrew).
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SRC_DIR/kickback"

# Pick a bin dir on PATH, preferring ~/.local/bin
BIN="${KICKBACK_BIN:-$HOME/.local/bin}"
mkdir -p "$BIN"

if [ ! -f "$SRC" ]; then echo "error: kickback script not found at $SRC" >&2; exit 1; fi
command -v python3 >/dev/null || { echo "error: python3 not found" >&2; exit 1; }
command -v openssl >/dev/null || echo "warning: openssl not found (only needed if python 'cryptography' is also missing)" >&2

install -m 0755 "$SRC" "$BIN/kickback"
echo "✓ installed kickback → $BIN/kickback"

ADDED_PATH=0
case ":$PATH:" in
  *":$BIN:"*) ;;
  *)
    case "${SHELL:-}" in */bash) RC="$HOME/.bashrc" ;; *) RC="$HOME/.zshrc" ;; esac
    if ! grep -qsF "$BIN" "$RC" 2>/dev/null; then
      printf '\n# added by kickback installer\nexport PATH="%s:$PATH"\n' "$BIN" >> "$RC"
      echo "✓ added $BIN to your PATH in $RC"
    fi
    export PATH="$BIN:$PATH"; ADDED_PATH=1
    ;;
esac

# Create config with safe defaults and show what it touches.
"$BIN/kickback" init || true
echo
echo "Next:  kickback about   ·   kickback doctor   ·   kickback"
[ "$ADDED_PATH" = 1 ] && echo "  (open a new terminal first, or run:  export PATH=\"$BIN:\$PATH\")"
