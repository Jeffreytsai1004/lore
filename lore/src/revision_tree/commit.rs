// SPDX-FileCopyrightText: 2026 Epic Games, Inc.
// SPDX-License-Identifier: MIT
//! `lore_revision_tree_commit` — freeze the handle's tree, write the 320-
//! byte revision record, and atomically advance the target branch tip. The
//! options struct carries the `remote_write` flag (`u8`, 0 or 1, not
//! `bool`) selecting between local-only and remote-uploading commits.

use lore_base::types::BranchId;
use serde::Deserialize;
use serde::Serialize;

use crate::revision_tree::handle::LoreRevisionTree;

/// Tuneables for `lore_revision_tree_commit`.
#[repr(C)]
#[derive(Copy, Clone, Debug, Default, PartialEq, Deserialize, Serialize)]
pub struct LoreRevisionTreeCommitOptions {
    /// Also upload the new revision to remote (local-only by default)
    pub remote_write: u8,
}

/// Arguments for `lore_revision_tree_commit`.
#[repr(C)]
#[derive(Copy, Clone, Debug, Default, PartialEq, Deserialize, Serialize)]
pub struct LoreRevisionTreeCommitArgs {
    /// Per-call correlation id echoed back in events
    pub id: u64,
    /// Loaded revision-tree handle to freeze and commit
    pub handle: LoreRevisionTree,
    /// Branch whose tip is atomically advanced to the new revision
    pub branch: BranchId,
    /// Commit tuneables (local-only vs remote-uploading)
    pub options: LoreRevisionTreeCommitOptions,
}
