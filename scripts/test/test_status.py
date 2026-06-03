# SPDX-FileCopyrightText: 2026 Epic Games, Inc.
# SPDX-License-Identifier: MIT
import logging
import os

import pytest
from test_utils import posix_join

from lore import Lore
from lore_parsers import parse_status_count_json

logger = logging.getLogger(__name__)


@pytest.mark.smoke
def test_status(new_lore_repo):
    repo: Lore = new_lore_repo()
    for i in range(10):
        subpath = str(i)
        repo.make_dirs(subpath)
        for j in range(10):
            subsubpath = posix_join(subpath, str(j))
            repo.make_dirs(subsubpath)
            with repo.open_file(
                posix_join(subsubpath, "test.uasset"), "w+b"
            ) as output_file:
                output_file.write(os.urandom(i + j + 30))

    repo.stage(scan=True)
    repo.commit()
    repo.repository_verify()

    status_path = "test.txt"
    status_subpath = posix_join("subpath", "another.txt")
    with repo.open_file(status_path, "w+b") as output_file:
        output_file.write(os.urandom(100))
    repo.make_dirs("subpath")
    with repo.open_file(status_subpath, "w+b") as output_file:
        output_file.write(os.urandom(200))

    # Status with path filter to an untracked file
    output = repo.status(status_path, unstaged=True)

    counting = False
    num_unstaged = 0
    for line in output.splitlines():
        if counting:
            num_unstaged += 1
            assert line.startswith("A ") and line.endswith(status_path), (
                f"Filtered status found unexpected modified file path: {line}"
            )
        elif line.rstrip() == "Untracked files:":
            counting = True
        else:
            assert not line.startswith("Changes not staged"), (
                f"Filtered status --unstaged found unrelated changes"
            )
            assert not line.startswith("D ") or line.startswith("M "), (
                f"Filtered status --unstaged found unrelated changes"
            )

    assert num_unstaged == 1, (
        f"Filtered status --unstaged did not return the expected paths, got {num_unstaged} expected 1"
    )

    # Status with path filter to an untracked file in a subdir
    output = repo.status("subpath", unstaged=True)

    counting = False
    num_unstaged = 0
    for line in output.splitlines():
        if counting:
            num_unstaged += 1
            assert line.startswith("A ") and line.endswith(status_subpath), (
                f"Filtered status found unexpected modified file path: {line}"
            )
        elif line.rstrip() == "Untracked files:":
            counting = True
        else:
            assert not line.startswith("Changes not staged"), (
                f"Filtered status --unstaged found unrelated changes"
            )
            assert not line.startswith("D ") or line.startswith("M "), (
                f"Filtered status --unstaged found unrelated changes"
            )

    assert num_unstaged == 1, (
        f"Filtered status --unstaged did not return the expected paths, got {num_unstaged} expected 1"
    )

    # Status with path filter to an untracked file in a subdir
    output = repo.status(status_subpath, unstaged=True)

    counting = False
    num_unstaged = 0
    for line in output.splitlines():
        if counting:
            num_unstaged += 1
            assert line.startswith("A ") and line.endswith(status_subpath), (
                f"Filtered status found unexpected modified file path: {line}"
            )
        elif line.rstrip() == "Untracked files:":
            counting = True
        else:
            assert not line.startswith("Changes not staged"), (
                f"Filtered status --unstaged found unrelated changes"
            )
            assert not line.startswith("D ") or line.startswith("M "), (
                f"Filtered status --unstaged found unrelated changes"
            )

    assert num_unstaged == 1, (
        f"Filtered status --unstaged did not return the expected paths, got {num_unstaged} expected 1"
    )

    repo.stage(scan=True)
    repo.commit()

    with repo.open_file(status_path, "w+b") as output_file:
        output_file.write(os.urandom(1000))
    repo.make_dirs("subpath")
    with repo.open_file(status_subpath, "w+b") as output_file:
        output_file.write(os.urandom(2000))

    # Status with path filter to an untracked file
    output = repo.status(status_path, unstaged=True)

    counting = False
    num_unstaged = 0
    for line in output.splitlines():
        if counting:
            num_unstaged += 1
            assert line.startswith("M ") and line.endswith(status_path), (
                f"Filtered status found unexpected modified file path: {line}"
            )
        elif line.rstrip() == "Changes not staged for commit:":
            counting = True
        else:
            assert not line.startswith("Changes not staged"), (
                f"Filtered status --unstaged found unrelated changes"
            )
            assert not line.startswith("D ") or line.startswith("A "), (
                f"Filtered status --unstaged found unrelated changes"
            )

    assert num_unstaged == 1, (
        f"Filtered status --unstaged did not return the expected paths, got {num_unstaged} expected 1"
    )

    # Status with path filter to an untracked file in a subdir
    output = repo.status("subpath", unstaged=True)

    counting = False
    num_unstaged = 0
    for line in output.splitlines():
        if counting:
            num_unstaged += 1
            assert line.startswith("M ") and line.endswith(status_subpath), (
                f"Filtered status found unexpected modified file path: {line}"
            )
        elif line.rstrip() == "Changes not staged for commit:":
            counting = True
        else:
            assert not line.startswith("Changes not staged"), (
                f"Filtered status --unstaged found unrelated changes"
            )
            assert not line.startswith("D ") or line.startswith("A "), (
                f"Filtered status --unstaged found unrelated changes"
            )

    assert num_unstaged == 1, (
        f"Filtered status --unstaged did not return the expected paths, got {num_unstaged} expected 1"
    )

    # Status with path filter to an untracked file in a subdir
    output = repo.status(status_subpath, unstaged=True)

    counting = False
    num_unstaged = 0
    for line in output.splitlines():
        if counting:
            num_unstaged += 1
            assert line.startswith("M ") and line.endswith(status_subpath), (
                f"Filtered status found unexpected modified file path: {line}"
            )
        elif line.rstrip() == "Changes not staged for commit:":
            counting = True
        else:
            assert not line.startswith("Changes not staged"), (
                f"Filtered status --unstaged found unrelated changes"
            )
            assert not line.startswith("D ") or line.startswith("A "), (
                f"Filtered status --unstaged found unrelated changes"
            )

    assert num_unstaged == 1, (
        f"Filtered status --unstaged did not return the expected paths, got {num_unstaged} expected 1"
    )

    repo.remove_file(status_subpath)

    # Status with path filter to an untracked file in a subdir
    output = repo.status("subpath", unstaged=True)

    counting = False
    num_unstaged = 0
    for line in output.splitlines():
        if counting:
            num_unstaged += 1
            assert line.startswith("D ") and line.endswith(status_subpath), (
                f"Filtered status found unexpected modified file path: {line}"
            )
        elif line.rstrip() == "Changes not staged for commit:":
            counting = True
        else:
            assert not line.startswith("Changes not staged"), (
                f"Filtered status --unstaged found unrelated changes: {line}"
            )
            assert not line.startswith("A ") or line.startswith("M "), (
                f"Filtered status --unstaged found unrelated changes: {line}"
            )

    assert num_unstaged == 1, (
        f"Filtered status --unstaged did not return the expected paths, got {num_unstaged} expected 1"
    )

    # Status with path filter to an untracked file in a subdir
    output = repo.status(status_subpath, unstaged=True)

    counting = False
    num_unstaged = 0
    for line in output.splitlines():
        if counting:
            num_unstaged += 1
            assert line.startswith("D ") and line.endswith(status_subpath), (
                f"Filtered status found unexpected modified file path: {line}"
            )
        elif line.rstrip() == "Changes not staged for commit:":
            counting = True
        else:
            assert not line.startswith("Changes not staged"), (
                f"Filtered status --unstaged found unrelated changes: {line}"
            )
            assert not line.startswith("A ") or line.startswith("M "), (
                f"Filtered status --unstaged found unrelated changes: {line}"
            )

    assert num_unstaged == 1, (
        f"Filtered status --unstaged did not return the expected paths, got {num_unstaged} expected 1"
    )

    # Status to an ignored file path
    with repo.open_file(repo.ignore_file(), "w+") as output_file:
        output_file.writelines(["testpath/"])

    repo.make_dirs("testpath")
    with repo.open_file(posix_join("testpath", "testfile.txt"), "w+") as output_file:
        output_file.writelines(["testing ignore"])

    output = repo.status(posix_join("testpath", "testfile.txt"), unstaged=True)

    assert "Changes not staged for commit:" not in output, (
        "Found unrelated unstaged change when query status for ignored file"
    )
    assert "Untracked files:" not in output, (
        "Found unrelated untracked change when query status for ignored file"
    )


@pytest.mark.smoke
def test_status_revision_only(new_lore_repo):
    repo: Lore = new_lore_repo()

    with repo.open_file("test.txt", "w+b") as f:
        f.write(os.urandom(100))
    repo.stage(scan=True)
    repo.commit()

    # Create staged and unstaged changes
    with repo.open_file("staged.txt", "w+b") as f:
        f.write(os.urandom(100))
    repo.stage(scan=True)
    with repo.open_file("unstaged.txt", "w+b") as f:
        f.write(os.urandom(100))

    # --revision-only should emit revision info but no file changes
    output = repo.status(revision_only=True)

    assert "Repository" in output, "Expected repository header in revision-only output"
    assert "On branch" in output, "Expected branch info in revision-only output"
    assert "Changes staged for commit:" not in output, (
        "revision-only should not show staged changes"
    )
    assert "Changes not staged for commit:" not in output, (
        "revision-only should not show unstaged changes"
    )
    assert "Untracked files:" not in output, (
        "revision-only should not show untracked files"
    )


@pytest.mark.smoke
def test_status_count(new_lore_repo, tmp_path_factory):
    """`status --count` reports the directory and file totals of the tree.

    Covers: the full-tree total; agreement between `--count` and `--count
    --scan` (a single shared traversal); that no count event is emitted without
    `--count`; that the local view filter is honored (a view-filtered clone
    counts only its materialized subtree, not the filtered-out parts of the
    committed tree); the human-readable "Repository size" line; and that a
    staged add is reflected (the count walks the staged state when present).
    """
    repo: Lore = new_lore_repo()

    repo.make_dirs("included")
    repo.make_dirs("excluded")
    for name in ("a.txt", "b.txt"):
        with repo.open_file(posix_join("included", name), "w+b") as f:
            f.write(os.urandom(64))
    for name in ("x.txt", "y.txt"):
        with repo.open_file(posix_join("excluded", name), "w+b") as f:
            f.write(os.urandom(64))
    with repo.open_file("root.txt", "w+b") as f:
        f.write(os.urandom(64))

    repo.stage(scan=True)
    repo.commit()
    repo.push()

    count = parse_status_count_json(repo.status(count=True, json=True))
    assert count is not None, "Expected a repositoryStatusCount event with --count"
    assert count["directories"] == 2, f"Expected 2 directories, got {count}"
    assert count["files"] == 5, f"Expected 5 files, got {count}"

    count_scan = parse_status_count_json(repo.status(count=True, scan=True, json=True))
    assert count_scan is not None, "Expected a count event with --count --scan"
    assert count_scan["directories"] == 2 and count_scan["files"] == 5, (
        f"--count --scan disagreed with --count: {count_scan}"
    )

    assert parse_status_count_json(repo.status(json=True)) is None, (
        "Count event emitted without --count"
    )

    view_dir = tmp_path_factory.mktemp("view")
    view_path = os.path.join(view_dir, "view.txt")
    with open(view_path, "w+") as view_file:
        view_file.write("**\n")
        view_file.write("!included/**\n")
    clone: Lore = repo.clone(view=view_path)

    clone_count = parse_status_count_json(clone.status(count=True, json=True))
    assert clone_count is not None, "Expected a count event in the view-filtered clone"
    assert clone_count["directories"] == 1, (
        f"View filter ignored: expected only included/ (1 dir), got {clone_count}"
    )
    assert clone_count["files"] == 2, (
        f"View filter ignored: expected only included/ files (2), got {clone_count}"
    )

    assert "Repository size: 1 directories, 2 files" in clone.status(count=True), (
        "Unexpected repository size line in human-readable --count output"
    )

    with clone.open_file(posix_join("included", "c.txt"), "w+b") as f:
        f.write(os.urandom(64))
    clone.stage(posix_join("included", "c.txt"))
    staged_count = parse_status_count_json(clone.status(count=True, json=True))
    assert staged_count is not None, "Expected a count event after staging"
    assert staged_count["directories"] == 1 and staged_count["files"] == 3, (
        f"Staged add not reflected (count should walk the staged state): {staged_count}"
    )


@pytest.mark.smoke
def test_status_count_link(new_lore_repo, tmp_path_factory):
    """`status --count` counts a link mount as a directory, descends only into
    the linked subtree (honoring path remapping), and applies the local view
    filter to the linked content via the remapped mount path.

    The target repository holds a `mounted/` subtree (`top.txt`, `keep/k.txt`,
    `drop/d.txt`) that is linked, plus unrelated `unmounted/` and `loose.txt`
    that are not. The link remaps the target's `mounted/` to a differently
    named `lk/` in the main repository.

    Without a view filter the count covers only `lk` and the linked subtree
    alongside `root.txt` — 3 directories, 4 files — never the target's
    unmounted entries. A view-filtered clone that re-includes `root.txt` and
    `lk/**` but excludes `lk/drop/` drops exactly that part of the linked
    subtree — 2 directories, 3 files — proving the view filter reaches inside
    the link via the mount path.
    """
    link_repo: Lore = new_lore_repo()
    link_repo.make_dirs(posix_join("mounted", "keep"))
    link_repo.make_dirs(posix_join("mounted", "drop"))
    with link_repo.open_file(posix_join("mounted", "top.txt"), "w+b") as f:
        f.write(os.urandom(64))
    with link_repo.open_file(posix_join("mounted", "keep", "k.txt"), "w+b") as f:
        f.write(os.urandom(64))
    with link_repo.open_file(posix_join("mounted", "drop", "d.txt"), "w+b") as f:
        f.write(os.urandom(64))
    link_repo.make_dirs("unmounted")
    with link_repo.open_file(posix_join("unmounted", "u.txt"), "w+b") as f:
        f.write(os.urandom(64))
    with link_repo.open_file("loose.txt", "w+b") as f:
        f.write(os.urandom(64))
    link_repo.stage(scan=True)
    link_repo.commit()
    link_repo.push()

    repo: Lore = new_lore_repo()
    with repo.open_file("root.txt", "w+b") as f:
        f.write(os.urandom(64))
    repo.stage(scan=True)
    repo.commit()
    repo.push()

    repo.link_add("lk", link_repo.get_id(), "mounted")
    repo.commit()
    repo.push()

    count = parse_status_count_json(repo.status(count=True, json=True))
    assert count is not None, "Expected a count event"
    assert count["directories"] == 3, (
        f"Expected 3 directories (lk + lk/keep + lk/drop), got {count}"
    )
    assert count["files"] == 4, (
        f"Expected 4 files (root.txt + lk/top.txt + lk/keep/k.txt + lk/drop/d.txt), got {count}"
    )

    view_dir = tmp_path_factory.mktemp("link-view")
    view_path = os.path.join(view_dir, "view.txt")
    with open(view_path, "w+") as view_file:
        view_file.write("**\n")
        view_file.write("!root.txt\n")
        view_file.write("!lk/**\n")
        view_file.write("lk/drop/\n")
    clone: Lore = repo.clone(view=view_path)

    clone_count = parse_status_count_json(clone.status(count=True, json=True))
    assert clone_count is not None, "Expected a count event in the view-filtered clone"
    assert clone_count["directories"] == 2, (
        f"View filter should drop lk/drop inside the link: expected 2 dirs, got {clone_count}"
    )
    assert clone_count["files"] == 3, (
        f"View filter should drop lk/drop/d.txt inside the link: expected 3 files, got {clone_count}"
    )
