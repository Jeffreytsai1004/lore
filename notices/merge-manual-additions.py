#!/usr/bin/env python3
"""Merge manual-additions entries into a cargo-about-rendered notices file.

The local notices flow runs this script after cargo-about renders the
plain-text notices file. The script reads the manual-additions TOML, filters
entries to those that ship inside the binary the rendered file was produced
for, and splices each matching entry into the rendered output by SPDX
license group.

Behaviour by group state:
  - Entry SPDX matches an existing `<!-- LORE-NOTICES-SECTION: <SPDX> -->`
    section: append a `-- <name> <version> --` block followed by the contents
    of the entry's license-text file inside that section.
  - Entry SPDX has no existing section: append a new section at the end of
    the file, with the section marker, a `License: <SPDX>` header, the
    contributing-source list, and the inlined license text.

License text appears at most once per entry. Within a section, manual
entries are sorted by (name, version) before splicing, so the output is
byte-deterministic across runs.

Usage:
    merge-manual-additions.py <binary> <manual-additions.toml> \
        <workspace-root> <notices-file>

The notices file is edited in place.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ALL_BINARIES_SENTINEL = "all"

# The section marker the Task 1 template emits, parameterised by SPDX text.
SECTION_MARKER_PREFIX = "<!-- LORE-NOTICES-SECTION: "
SECTION_MARKER_SUFFIX = " -->"
SECTION_MARKER_RE = re.compile(
    r"^<!-- LORE-NOTICES-SECTION: (?P<spdx>.+?) -->$"
)

# A contributing-source block header, e.g. `-- governor 0.10.1 --`. Crate names
# and versions carry no spaces, so two whitespace-free tokens are enough. The
# leading `-- ` (not `<!--`) distinguishes this from a section marker.
BLOCK_HEADER_RE = re.compile(r"^-- (?P<name>\S+) (?P<version>\S+) --$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", help="binary name (loreserver, lore, liblore)")
    parser.add_argument("config", type=Path, help="manual-additions TOML path")
    parser.add_argument("workspace_root", type=Path, help="workspace root")
    parser.add_argument("notices_file", type=Path, help="rendered notices file")
    return parser.parse_args()


def load_entries(config_path: Path) -> list[dict]:
    with config_path.open("rb") as fh:
        data = tomllib.load(fh)
    entries = data.get("entry", [])
    if not isinstance(entries, list):
        raise SystemExit(
            f"error: {config_path}: 'entry' must be an array of tables"
        )
    return entries


def load_overrides(config_path: Path) -> list[dict]:
    with config_path.open("rb") as fh:
        data = tomllib.load(fh)
    overrides = data.get("override", [])
    if not isinstance(overrides, list):
        raise SystemExit(
            f"error: {config_path}: 'override' must be an array of tables"
        )
    return overrides


def remove_crate_block(text: str, name: str, version: str) -> tuple[str, bool]:
    """Remove a crate's `-- name version --` block from the rendered file.

    The block runs from its header line up to (but not including) the next
    block header or section marker, which also drops the single blank line the
    template places before the next block. Returns the edited text and whether
    a matching block was found.
    """
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        match = BLOCK_HEADER_RE.match(line.rstrip("\n"))
        if match and match.group("name") == name and match.group("version") == version:
            start = i
            break
    if start is None:
        return text, False
    end = len(lines)
    for j in range(start + 1, len(lines)):
        stripped = lines[j].rstrip("\n")
        if BLOCK_HEADER_RE.match(stripped) or SECTION_MARKER_RE.match(stripped):
            end = j
            break
    del lines[start:end]
    return "".join(lines), True


def entry_applies_to(entry: dict, binary: str) -> bool:
    binaries = entry.get("binaries")
    if binaries == ALL_BINARIES_SENTINEL:
        return True
    if isinstance(binaries, list):
        return binary in binaries
    raise SystemExit(
        f"error: entry {entry.get('name')!r}: 'binaries' must be a list of "
        f"binary names or the sentinel {ALL_BINARIES_SENTINEL!r}"
    )


def split_sections(text: str) -> tuple[str, list[tuple[str, str]], str]:
    """Split the rendered file into (prologue, sections, trailer).

    sections is a list of (spdx, body) pairs in file order. body includes
    the section marker line, the `License:` header line, and the
    contributing-source blocks that follow until the next section marker
    (or end-of-file). The trailer is empty in the current template; we keep
    the structure flexible so a future template can carry one.
    """
    lines = text.splitlines(keepends=True)
    section_starts: list[int] = []
    section_spdxs: list[str] = []
    for i, line in enumerate(lines):
        match = SECTION_MARKER_RE.match(line.rstrip("\n"))
        if match:
            section_starts.append(i)
            section_spdxs.append(match.group("spdx"))
    if not section_starts:
        return text, [], ""
    prologue = "".join(lines[: section_starts[0]])
    sections: list[tuple[str, str]] = []
    for idx, start in enumerate(section_starts):
        end = section_starts[idx + 1] if idx + 1 < len(section_starts) else len(lines)
        body = "".join(lines[start:end])
        sections.append((section_spdxs[idx], body))
    return prologue, sections, ""


def render_entry_block(entry: dict, workspace_root: Path) -> str:
    """Render a `-- name version --` block with the license-text body."""
    license_path = workspace_root / entry["license"]
    license_text = license_path.read_text(encoding="utf-8")
    # Strip trailing whitespace so the spacing between blocks is consistent
    # regardless of trailing newlines in the source license file.
    license_text = license_text.rstrip() + "\n"
    return f"-- {entry['name']} {entry['version']} --\n{license_text}\n"


def extend_existing_section(body: str, entry_block: str) -> str:
    """Append the entry block to an existing SPDX section.

    The section body ends with two blank lines (one before the next section
    marker, one after the last crate). We normalise the trailing whitespace
    so the appended block keeps the same one-blank-line separator the
    template emits between contributing-source blocks.
    """
    trimmed = body.rstrip("\n")
    return trimmed + "\n\n" + entry_block + "\n"


def build_new_section(spdx: str, entries: list[dict], workspace_root: Path) -> str:
    """Build a brand-new section for an SPDX the upstream generator did not emit."""
    parts = [
        f"{SECTION_MARKER_PREFIX}{spdx}{SECTION_MARKER_SUFFIX}\n",
        f"License: {spdx}\n",
        "\n",
    ]
    for entry in entries:
        parts.append(render_entry_block(entry, workspace_root))
        parts.append("\n")
    return "".join(parts)


def merge(
    rendered: str,
    entries: list[dict],
    workspace_root: Path,
) -> str:
    prologue, sections, trailer = split_sections(rendered)

    # Sort entries by (name, version) inside each SPDX group so the output is
    # byte-deterministic regardless of authoring order in the TOML.
    by_spdx: dict[str, list[dict]] = {}
    for entry in entries:
        by_spdx.setdefault(entry["spdx"], []).append(entry)
    for spdx in by_spdx:
        by_spdx[spdx].sort(key=lambda e: (e["name"], e["version"]))

    existing_spdxs = {spdx for spdx, _ in sections}

    # Existing groups: extend in place.
    merged_sections: list[tuple[str, str]] = []
    for spdx, body in sections:
        if spdx in by_spdx:
            new_body = body
            for entry in by_spdx[spdx]:
                entry_block = render_entry_block(entry, workspace_root)
                new_body = extend_existing_section(new_body, entry_block)
            merged_sections.append((spdx, new_body))
        else:
            merged_sections.append((spdx, body))

    # New groups: append at the file's end, sorted by SPDX for determinism.
    new_spdxs = sorted(spdx for spdx in by_spdx if spdx not in existing_spdxs)
    new_section_bodies = [
        build_new_section(spdx, by_spdx[spdx], workspace_root) for spdx in new_spdxs
    ]

    body_text = "".join(body for _, body in merged_sections)
    new_text = "".join(new_section_bodies)
    return prologue + body_text + new_text + trailer


def main() -> int:
    args = parse_args()
    entries = load_entries(args.config)
    overrides = load_overrides(args.config)
    applicable = [e for e in entries if entry_applies_to(e, args.binary)]

    rendered = args.notices_file.read_text(encoding="utf-8")

    # Overrides replace a Cargo crate's placeholder block with vendored text.
    # Remove each override crate's existing block first, then re-add it through
    # the same splice path so it lands under the override's SPDX group. An
    # override whose crate is absent from this binary is skipped.
    present_overrides: list[dict] = []
    for override in overrides:
        rendered, found = remove_crate_block(
            rendered, override["name"], override["version"]
        )
        if found:
            present_overrides.append(override)

    additions = applicable + present_overrides
    merged = merge(rendered, additions, args.workspace_root)
    args.notices_file.write_text(merged, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
