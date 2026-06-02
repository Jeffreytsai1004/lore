#!/usr/bin/env bash
# Notices generator for one binary on one target.
#
# Renders the third-party notices file with cargo-about, fills in the manual
# additions and overrides, then enforces one gate: every contributing crate
# must render a real license with real attribution. The gate fails the run if
# any unfilled SPDX template (for example `Copyright (c) <year> <copyright
# holders>`) survives in the output, naming each offending crate.
#
# Usage:
#   notices/generate-notices.sh <binary-name> <target-triple> <manifest-path> <output-file>
#
# Example:
#   notices/generate-notices.sh loreserver x86_64-unknown-linux-gnu \
#       lore-server/Cargo.toml /tmp/notices.txt

set -euo pipefail

if [[ $# -ne 4 ]]; then
    echo "usage: $(basename "$0") <binary> <target> <manifest-path> <output-file>" >&2
    exit 2
fi

BINARY="$1"
TARGET="$2"
MANIFEST="$3"
OUTPUT="$4"

WORKSPACE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="${WORKSPACE_ROOT}/about.toml"
TEMPLATE="${WORKSPACE_ROOT}/notices/third-party-notices.hbs"

if ! command -v cargo-about >/dev/null 2>&1; then
    echo "error: cargo-about is not installed. Install with:" >&2
    echo "    cargo install cargo-about --locked --features cli" >&2
    exit 2
fi

# Render the plain-text notices file via the template. `--fail` makes
# cargo-about exit non-zero if a crate's license cannot be determined or is not
# accepted by about.toml. Missing per-crate attribution is caught by the
# placeholder gate below, since cargo-about itself falls back to canonical SPDX
# text rather than failing on a missing license file.
cargo about generate \
    --fail \
    -c "${CONFIG}" \
    --target "${TARGET}" \
    -m "${MANIFEST}" \
    "${TEMPLATE}" \
    > "${OUTPUT}"

# Fill the binary and target header tokens from the invocation arguments.
# cargo-about renders the template's literal `__LORE_BINARY__` / `__LORE_TARGET__`
# tokens verbatim (its context carries neither value), so we substitute them
# here. The `__LORE_RELEASE_VERSION__` token is left for the release workflow's
# substitution pass, since the version is only known at release time.
# Use a temp file rather than `sed -i` so the same command works under both
# BSD sed (macOS) and GNU sed (Linux CI).
HEADER_TMP="$(mktemp -t lore-notices-header.XXXXXX)"
sed "s|__LORE_BINARY__|${BINARY}|g; s|__LORE_TARGET__|${TARGET}|g" \
    "${OUTPUT}" > "${HEADER_TMP}"
mv "${HEADER_TMP}" "${OUTPUT}"

# Post-process: merge manual-additions entries for non-Cargo vendored sources
# the dep-graph walk cannot see, and apply overrides that replace a Cargo
# crate's rendered block with vendored text. The helper edits the file in place.
MANUAL_CONFIG="${WORKSPACE_ROOT}/notices/manual-additions.toml"
MERGE_HELPER="${WORKSPACE_ROOT}/notices/merge-manual-additions.py"
if [[ -f "${MANUAL_CONFIG}" ]]; then
    python3 "${MERGE_HELPER}" \
        "${BINARY}" \
        "${MANUAL_CONFIG}" \
        "${WORKSPACE_ROOT}" \
        "${OUTPUT}"
fi

# Gate: every contributing crate must render a real license with real
# attribution. cargo-about substitutes an unfilled SPDX template (for example
# `Copyright (c) <year> <copyright holders>`) when it cannot resolve a crate's
# license text. Those angle-bracket placeholders are not acceptable in a
# redistributed notices file, so fail loudly and name the offending crates.
# (Apache-2.0's "how to apply" appendix uses square brackets like `[yyyy]`, so
# matching only angle brackets does not flag a real Apache license.)
PLACEHOLDER_RE='<year>|<copyright holders>|<COPYRIGHT HOLDERS>|<owner>|<OWNER>|<name of author>|<organization>'
PLACEHOLDER_CRATES="$(awk -v re="${PLACEHOLDER_RE}" '
    /^-- /{crate=$0}
    $0 ~ re {print crate}
' "${OUTPUT}" | sort -u)"
if [[ -n "${PLACEHOLDER_CRATES//[[:space:]]/}" ]]; then
    echo "error: the rendered notices file has unfilled license-text placeholders for:" >&2
    printf '%s\n' "${PLACEHOLDER_CRATES}" | sed 's/^-- /  - /; s/ --$//' >&2
    echo "" >&2
    echo "Every dependency must render a real license with real attribution. For each crate," >&2
    echo "resolve it by one of:" >&2
    echo "  - a [<crate>.clarify] block in about.toml binding the crate's shipped license file;" >&2
    echo "  - a [<crate>.clarify] git binding when the file lives only in the crate's repository;" >&2
    echo "  - a [[override]] entry in notices/manual-additions.toml with vendored license text." >&2
    exit 1
fi

echo "notices: wrote ${OUTPUT} (binary=${BINARY}, target=${TARGET})" >&2
