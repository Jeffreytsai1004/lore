// SPDX-FileCopyrightText: 2026 Epic Games, Inc.
// SPDX-License-Identifier: MIT
//! `lore_revision_tree_metadata_get` — read a metadata value by key. The
//! verb consults the handle's pending edits first, then falls back to the
//! loaded revision's frozen Metadata fragment. A missing key emits no value
//! event; `Complete` fires with status 0, matching the convention used by
//! `lore_revision_metadata_get_async`.

use lore_revision::interface::LoreString;
use serde::Deserialize;
use serde::Serialize;

use crate::revision_tree::handle::LoreRevisionTree;

/// Arguments for `lore_revision_tree_metadata_get`.
#[repr(C)]
#[derive(Clone, Debug, Default, PartialEq, Deserialize, Serialize)]
pub struct LoreRevisionTreeMetadataGetArgs {
    /// Per-call correlation id echoed back in events
    pub id: u64,
    /// Loaded revision-tree handle to read from
    pub handle: LoreRevisionTree,
    /// Metadata key to read; pending edits take precedence over the revision
    pub key: LoreString,
}
