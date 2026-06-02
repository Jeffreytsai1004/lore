# Third-party notices

This directory builds the OSS third-party notices file that ships with each redistributed Lore binary. The generator walks the Rust dependency graph for each (binary, target) pair and writes one notices file per pair.

## Files

- `../about.toml` — the policy file. It mirrors the SPDX allow-list in `../deny.toml`, orders it as the dual-license preference list, and carries the per-crate `clarify` blocks.
- `third-party-notices.hbs` — the Handlebars template that renders the plain-text notices file. `<!-- LORE-NOTICES-SECTION: <SPDX> -->` markers delimit each license group so the merge step finds a group without reparsing the file.
- `generate-notices.sh` — the script you run. It renders the file with `cargo-about`, applies the manual additions and overrides, and runs the placeholder check.
- `manual-additions.toml` — declares non-Cargo vendored sources that ship inside the binaries, plus `[[override]]` entries that replace a Cargo crate's rendered block with vendored text.
- `license-overrides/` — vendored license texts that `[[override]]` entries point at, for crates `cargo-about` cannot resolve on its own.
- `merge-manual-additions.py` — the helper the script calls. It splices each manual entry into the rendered file by SPDX group and applies the overrides.

## Allow-list discipline

Update `about.toml`'s `accepted` list and `deny.toml`'s `[licenses].allow` list together in any change that edits either. If the two lists drift, a change the deny check accepts can still fail the notices generator, or the reverse.

## Local usage

Render the notices file for one binary on one target:

```
notices/generate-notices.sh loreserver x86_64-unknown-linux-gnu lore-server/Cargo.toml /tmp/notices.txt
```

The four arguments are the binary name, the Cargo target triple, the manifest path to the binary crate, and the output path. The script exits non-zero if the placeholder check fails. A local run leaves `__LORE_RELEASE_VERSION__` in the header; the release process substitutes the real version.

## Every dependency must render a real license

The script enforces one rule: the rendered file must not contain an unfilled license template, for example `Copyright (c) <year> <copyright holders>`. `cargo-about` writes that template when it cannot find a crate's real license text, and an unfilled placeholder is not an acceptable notice. When the check fails it names every crate that still carries a placeholder. Fix each one, in this order of preference:

1. **`[<crate>.clarify]` with a shipped file.** Use this when the crate ships a license file that `cargo-about` did not match; a lowercase name like `license-mit` is a common cause. The shape mirrors `[ring.clarify]`: an SPDX expression, then one `[[<crate>.clarify.files]]` block per file with a `path` and a `sha-256` `checksum`. The checksum catches drift: if upstream rewrites the file, the clarify stops applying and you re-validate. A per-file `license = "<SPDX>"` lets one clarify cover a compound expression; `ring` binds its ISC and Apache-2.0 files this way.
2. **`[<crate>.clarify]` with a git binding.** Use this when the file lives only in the crate's repository. Add `[[<crate>.clarify.git]]` with `path` and `checksum`, and `cargo-about` fetches that one file at the crate's published commit. This does not work when the crate's `repository` URL ends in `.git`: `cargo-about` 0.9.0 keeps the suffix and the fetch returns 404.
3. **`[[override]]` in `manual-additions.toml`.** Use this when no clarify can reach the text — the `.git` case, or a crate that ships no file anywhere. Vendor the real license text under `license-overrides/` and add an override that names the crate, its resolved `version`, the `spdx` group to render under, and the vendored `license` path. The merge step removes the crate's placeholder block and re-renders it with the vendored text. When a crate offers a choice of licenses that includes Apache-2.0 and states no copyright, render it as Apache-2.0: the canonical Apache-2.0 text needs no per-work copyright line.

The check runs on the rendered output. A crate that ships no license file still passes when it renders a complete notice; a crate whose only license is Apache-2.0, or another license that needs no per-work copyright, passes with no action because its canonical text is complete. Only an unfilled placeholder fails.

## Manual additions for non-Cargo vendored sources

`cargo-about` walks the Cargo dependency graph, so it cannot see native source code that a `build.rs` pulls in and compiles into a binary. Declare each such source in `manual-additions.toml`. Each entry carries:

- `name` — the source's name.
- `version` — a version string read from the vendored source when you write the entry.
- `spdx` — the source's SPDX license expression. A reviewer checks this; the placeholder check covers Cargo-resolved deps only.
- `license` — a workspace-relative path to the license file vendored next to the source, by convention under `*/native/thirdparty/<source>/`.
- `binaries` — the binary names from `{loreserver, lore, liblore}` the entry applies to, or `"all"` for a source that ships in every binary.

Add an entry whenever a `build.rs` pulls in a new vendored native source whose object code ships inside a binary. Place the license file next to the vendored source under `*/native/thirdparty/<source>/` and point the entry at it. When you review a change that edits a `build.rs` to add or remove vendored native source, check that `manual-additions.toml` changes with it.

## Override entries

`[[override]]` entries in `manual-additions.toml` replace a Cargo crate's rendered block with vendored text. Each carries `name`, `version` (it must match the version `cargo-about` resolves), `spdx` (the license group to render under), and `license` (a workspace-relative path under `license-overrides/`). An override applies only when the crate appears in the binary being rendered; the merge step skips it otherwise. When the resolved version moves, update `version` here or the check flags the crate again.
