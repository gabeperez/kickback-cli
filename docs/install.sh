#!/usr/bin/env bash
# kickback web installer — hosted at: https://gabeperez.github.io/kickback-cli/install.sh
# Usage:  curl -fsSL https://gabeperez.github.io/kickback-cli/install.sh | bash
#
# Downloads the single `kickback` script (pinned to a release), verifies its
# checksum, installs it to a bin dir on your PATH, and runs `kickback init`
# (which writes a config with SAFE DEFAULTS — every feature that writes anything
# is OFF until you opt in).
#
# Inspect before you run it — that's encouraged. Source: https://github.com/gabeperez/kickback-cli
set -euo pipefail

# ---- pinned release ------------------------------------------------------
SCRIPT_URL="${KICKBACK_SCRIPT_URL:-https://raw.githubusercontent.com/gabeperez/kickback-cli/v0.1.0/kickback}"
SHA256_EXPECTED="8b5c50bf709c3f6ddae033bafc0e9a7d31741326095b7429fa62308ca8d1d856"
# --------------------------------------------------------------------------

BIN="${KICKBACK_BIN:-$HOME/.local/bin}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

echo "kickback installer"

# 0) sanity: macOS + deps
[ "$(uname)" = "Darwin" ] || { echo "error: kickback is macOS-only." >&2; exit 1; }
command -v python3 >/dev/null || { echo "error: python3 not found (install Xcode CLT or Homebrew python)." >&2; exit 1; }
command -v curl >/dev/null   || { echo "error: curl not found." >&2; exit 1; }

# 1) download
echo "→ downloading kickback…"
curl -fsSL "$SCRIPT_URL" -o "$TMP/kickback"

# 2) verify checksum (refuse on mismatch)
GOT="$(shasum -a 256 "$TMP/kickback" | awk '{print $1}')"
if [ "$GOT" != "$SHA256_EXPECTED" ]; then
  echo "error: checksum mismatch — refusing to install." >&2
  echo "  expected $SHA256_EXPECTED" >&2
  echo "  got      $GOT" >&2
  exit 1
fi
echo "✓ checksum verified"

# 3) install
mkdir -p "$BIN"
install -m 0755 "$TMP/kickback" "$BIN/kickback"
echo "✓ installed → $BIN/kickback"

case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo "  note: add $BIN to your PATH:  echo 'export PATH=\"$BIN:\$PATH\"' >> ~/.zshrc" ;;
esac

# 4) safe-default config + first-run summary
"$BIN/kickback" init || true
echo
echo "Done. Try:  kickback   ·   kickback about   ·   kickback doctor"
