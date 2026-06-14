// SPDX-FileCopyrightText: 2026 Epic Games, Inc.
// SPDX-License-Identifier: MIT
//! `lore_revision_tree_metadata_set` — record a `(key, value, format)`
//! triple on the in-progress revision's metadata. A subsequent set on the
//! same key overwrites the previous value in the same uncommitted handle
//! state. `format` is a `u32` matching the existing
//! `LoreRevisionMetadataSetArgs::formats` element type.

use lore_revision::interface::LoreString;
use serde::Deserialize;
use serde::Serialize;

use crate::revision_tree::handle::LoreRevisionTree;

/// Arguments for `lore_revision_tree_metadata_set`.
#[repr(C)]
#[derive(Clone, Debug, Default, PartialEq, Deserialize, Serialize)]
pub struct LoreRevisionTreeMetadataSetArgs {
    /// Per-call correlation id echoed back in events
    pub id: u64,
    /// Loaded revision-tree handle to mutate
    pub handle: LoreRevisionTree,
    /// Metadata key; re-setting it overwrites the pending value
    pub key: LoreString,
    /// Value stored under the key
    pub value: LoreString,
    /// Value encoding, matching `LoreRevisionMetadataSetArgs::formats`
    pub format: u32,
}
