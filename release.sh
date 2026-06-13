#!/usr/bin/env bash
# release.sh — stamp checksums for a new kickback release.
#
# Produces the two SHA256 values you paste into web/install.sh and
# Formula/kickback.rb, plus the release tarball Homebrew downloads.
#
#   ./release.sh            # reads VERSION from the kickback script
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

VERSION="$(grep -m1 '^VERSION = ' kickback | sed -E 's/.*"([^"]+)".*/\1/')"
echo "kickback version: $VERSION"

# 1) checksum of the raw script (for web/install.sh SHA256_EXPECTED, and the
#    file you upload to BASE_URL/kickback)
SCRIPT_SHA="$(shasum -a 256 kickback | awk '{print $1}')"
echo
echo "── web installer ──────────────────────────────"
echo "Upload:  ./kickback          → https://gabeperez.github.io/kickback-cli/kickback"
echo "Upload:  ./web/install.sh    → https://gabeperez.github.io/kickback-cli/install.sh"
echo "Set in web/install.sh:  SHA256_EXPECTED=\"$SCRIPT_SHA\""

# 2) tarball for Homebrew (mirrors the GitHub auto-generated tag tarball layout)
OUT="dist"; mkdir -p "$OUT"
TARBALL="$OUT/kickback-cli-$VERSION.tar.gz"
# emulate GitHub's archive: top dir = kickback-cli-<version>/
STAGE="$(mktemp -d)/kickback-cli-$VERSION"
mkdir -p "$STAGE"
cp kickback README.md LICENSE "$STAGE/" 2>/dev/null || true
tar -czf "$TARBALL" -C "$(dirname "$STAGE")" "kickback-cli-$VERSION"
TAR_SHA="$(shasum -a 256 "$TARBALL" | awk '{print $1}')"
echo
echo "── Homebrew formula ───────────────────────────"
echo "Tarball: $TARBALL"
echo "After you 'git tag v$VERSION && git push --tags', GitHub serves the same"
echo "archive at the formula's url. Set in Formula/kickback.rb:"
echo "  sha256 \"$TAR_SHA\""
echo
echo "(GitHub's tag tarball sha will match only if repo contents == staged files;"
echo " simplest: upload $TARBALL as a Release asset and point url at it.)"
echo
echo "Done."
