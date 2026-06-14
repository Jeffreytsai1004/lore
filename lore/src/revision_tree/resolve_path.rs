// SPDX-FileCopyrightText: 2026 Epic Games, Inc.
// SPDX-License-Identifier: MIT
//! `lore_revision_tree_resolve_path` — translate a UTF-8 path string to a
//! `NodeID` against the loaded revision tree. An empty path resolves to the
//! root node id. The verb does not touch disk.

use lore_revision::interface::LoreString;
use serde::Deserialize;
use serde::Serialize;

use crate::revision_tree::handle::LoreRevisionTree;

/// Arguments for `lore_revision_tree_resolve_path`.
#[repr(C)]
#[derive(Clone, Debug, Default, PartialEq, Deserialize, Serialize)]
pub struct LoreRevisionTreeResolvePathArgs {
    /// Per-call correlation id echoed back in events
    pub id: u64,
    /// Loaded revision-tree handle to resolve against
    pub handle: LoreRevisionTree,
    /// UTF-8 path relative to the tree root; empty resolves to the root node
    pub path: LoreString,
}
