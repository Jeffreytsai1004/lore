// SPDX-FileCopyrightText: 2026 Epic Games, Inc.
// SPDX-License-Identifier: MIT
//! `lore_revision_tree_delete` — mark a node and its transitive children as
//! deleted within the handle's in-progress revision. Subsequent reads in the
//! same handle do not observe the deleted subtree.

use lore_revision::node::NodeID;
use serde::Deserialize;
use serde::Serialize;

use crate::revision_tree::handle::LoreRevisionTree;

/// Arguments for `lore_revision_tree_delete`.
#[repr(C)]
#[derive(Copy, Clone, Debug, Default, PartialEq, Deserialize, Serialize)]
pub struct LoreRevisionTreeDeleteArgs {
    /// Per-call correlation id echoed back in events
    pub id: u64,
    /// Loaded revision-tree handle to mutate
    pub handle: LoreRevisionTree,
    /// Subtree root to mark deleted, including its transitive children
    pub node_id: NodeID,
}
