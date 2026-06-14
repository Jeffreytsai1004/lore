// SPDX-FileCopyrightText: 2026 Epic Games, Inc.
// SPDX-License-Identifier: MIT
//! `lore_revision_tree_modify` — update a leaf node's `mode`, `size`, and
//! `address` while preserving its `file_id` (the `address.context` slot).
//! Non-leaf targets are rejected with `LORE_ERROR_CODE_INVALID_ARGUMENTS`.

use lore_base::types::Address;
use lore_revision::node::NodeID;
use serde::Deserialize;
use serde::Serialize;

use crate::revision_tree::handle::LoreRevisionTree;

/// Arguments for `lore_revision_tree_modify`.
#[repr(C)]
#[derive(Copy, Clone, Debug, Default, PartialEq, Deserialize, Serialize)]
pub struct LoreRevisionTreeModifyArgs {
    /// Per-call correlation id echoed back in events
    pub id: u64,
    /// Loaded revision-tree handle to mutate
    pub handle: LoreRevisionTree,
    /// Leaf node to update; non-leaf targets are rejected
    pub node_id: NodeID,
    /// New POSIX permission bits
    pub mode: u16,
    /// New content size in bytes
    pub size: u64,
    /// New content address; the existing `file_id` context is preserved
    pub address: Address,
}
