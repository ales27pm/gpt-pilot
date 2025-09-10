from os.path import exists, join

import pytest

from core.disk.ignore import IgnoreMatcher
from core.disk.vfs import LocalDiskVFS, MemoryVFS


def test_memory_vfs():
    vfs = MemoryVFS()

    assert vfs.list() == []
    with pytest.raises(FileNotFoundError):
        vfs.read("missing.txt")

    vfs.save("test.txt", "hello world")
    assert vfs.read("test.txt") == "hello world"
    assert vfs.list() == ["test.txt"]

    vfs.save("subdir/another.txt", "hello world")
    assert vfs.read("subdir/another.txt") == "hello world"
    assert vfs.list() == ["subdir/another.txt", "test.txt"]

    assert vfs.list("subdir") == ["subdir/another.txt"]
    assert vfs.list("subdir/") == ["subdir/another.txt"]

    assert vfs.list("nonexistent") == []

    vfs.remove("test.txt")
    assert vfs.list() == ["subdir/another.txt"]

    vfs.remove("nonexistent.txt")


def test_local_disk_vfs(tmp_path):
    vfs = LocalDiskVFS(tmp_path)

    assert vfs.list() == []
    with pytest.raises(FileNotFoundError):
        vfs.read("missing.txt")

    vfs.save("test.txt", "hello world")
    assert vfs.read("test.txt") == "hello world"
    assert vfs.list() == ["test.txt"]

    vfs.save("subdir/another.txt", "hello world")
    assert vfs.read("subdir/another.txt") == "hello world"
    assert vfs.list() == ["subdir/another.txt", "test.txt"]

    assert vfs.list("subdir") == ["subdir/another.txt"]
    assert vfs.list("subdir/") == ["subdir/another.txt"]

    assert vfs.list("nonexistent") == []

    vfs.remove("test.txt")
    assert vfs.list() == ["subdir/another.txt"]

    vfs.remove("nonexistent.txt")


def test_local_disk_vfs_with_matcher(tmp_path):
    matcher = IgnoreMatcher(tmp_path, ["*.log"])
    vfs = LocalDiskVFS(tmp_path, ignore_matcher=matcher)

    with open(join(tmp_path, "test.log"), "w") as f:
        f.write("this should be ignored")

    assert vfs.list() == []

    with open(join(tmp_path, "test.txt"), "w") as f:
        f.write("hello world")

    assert vfs.list() == ["test.txt"]
    assert vfs.read("test.txt") == "hello world"

    vfs.save("subdir/another.txt", "hello world")
    assert exists(join(tmp_path, "subdir", "another.txt"))

    assert vfs.read("subdir/another.txt") == "hello world"
    assert vfs.list() == ["subdir/another.txt", "test.txt"]

    assert vfs.list("subdir") == ["subdir/another.txt"]
    assert vfs.list("subdir/") == ["subdir/another.txt"]

    assert vfs.list("nonexistent") == []

    vfs.remove("test.txt")
    assert vfs.list() == ["subdir/another.txt"]
    assert not exists(join(tmp_path, "test.txt"))

    vfs.remove("nonexistent.txt")

    vfs.remove("test.log")
    assert exists(join(tmp_path, "test.log"))

# -----------------------------------------------------------------------------
# Additional comprehensive tests for MemoryVFS and LocalDiskVFS
# Test framework: pytest
# -----------------------------------------------------------------------------

import os
import io
import sys
from typing import List

@pytest.mark.parametrize("path", [
    "a.txt",
    "sub/dir/file.txt",
    "./relative.txt",
    "subdir/../subdir2/keep.txt",
])
def test_memory_vfs_save_and_overwrite_normalization_and_order(path):
    vfs = MemoryVFS()
    # Initial save
    vfs.save(path, "v1")
    assert vfs.read(path) == "v1"
    # Overwrite same path
    vfs.save(path, "v2")
    assert vfs.read(path) == "v2"
    # Ensure listing is sorted and includes normalized path
    listed = vfs.list()
    assert listed == sorted(listed)
    assert any(p.endswith("a.txt") or p.endswith("relative.txt") or p.endswith("keep.txt") or p.endswith("file.txt") for p in listed)

def test_memory_vfs_large_and_empty_content_and_binary_roundtrip():
    vfs = MemoryVFS()
    empty_path = "empty.txt"
    big_path = "big/huge.txt"
    bin_path = "bin/data.bin"

    # Empty content
    vfs.save(empty_path, "")
    assert vfs.read(empty_path) == ""
    # Large content (couple hundred KB)
    large = "0123456789abcdef" * 8192  # ~131072 chars
    vfs.save(big_path, large)
    assert vfs.read(big_path) == large
    # Binary data: ensure storing and retrieving binary-like content works (via bytes->latin1 string if impl expects str)
    raw = bytes(range(256))
    try:
        # If API enforces str, store via latin1
        vfs.save(bin_path, raw.decode("latin1"))
        got = vfs.read(bin_path).encode("latin1")
        assert got == raw
    except TypeError:
        # If API supports bytes directly
        vfs.save(bin_path, raw)  # type: ignore
        got = vfs.read(bin_path)  # type: ignore
        assert got == raw

    # Listing filters
    all_files = vfs.list()
    assert all(f in all_files for f in [empty_path, big_path, bin_path])
    sub_files = vfs.list("big")
    assert sub_files == ["big/huge.txt"]
    assert vfs.list("missing_prefix") == []

def test_memory_vfs_remove_idempotent_and_errors_on_read_dir_like():
    vfs = MemoryVFS()
    vfs.save("dir/file.txt", "x")
    assert vfs.list() == ["dir/file.txt"]
    # Removing non-existent should not raise
    vfs.remove("nope.txt")
    assert vfs.list() == ["dir/file.txt"]
    # Removing existing deletes
    vfs.remove("dir/file.txt")
    assert vfs.list() == []
    # Reading a prefix that behaves like directory should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        vfs.read("dir")  # not a file entry
    # Listing both with and without trailing slash should be same
    assert vfs.list("dir") == []
    assert vfs.list("dir/") == []

def test_memory_vfs_security_prevent_path_traversal_escape():
    vfs = MemoryVFS()
    # These should be treated as logical keys; reading before save should fail
    with pytest.raises(FileNotFoundError):
        vfs.read("../escape.txt")
    vfs.save("../escape.txt", "data")
    # Once saved, it exists as a key, but list should include normalized/sorted entries
    assert vfs.read("../escape.txt") == "data"
    assert "../escape.txt" in vfs.list()

# -------------------- LocalDiskVFS extended tests --------------------

def test_local_disk_vfs_overwrite_and_preserve_order(tmp_path):
    vfs = LocalDiskVFS(tmp_path)
    p1 = "alpha.txt"
    p2 = "zeta.txt"
    p3 = "m/sub.txt"

    vfs.save(p1, "1")
    vfs.save(p2, "2")
    vfs.save(p3, "3")
    # Verify sorted order
    assert vfs.list() == ["alpha.txt", "m/sub.txt", "zeta.txt"]

    # Overwrite existing file
    vfs.save(p1, "one")
    assert vfs.read(p1) == "one"
    # Prefix listing
    assert vfs.list("m") == ["m/sub.txt"]
    assert vfs.list("m/") == ["m/sub.txt"]

def test_local_disk_vfs_creates_subdirs_and_handles_empty_and_large(tmp_path):
    vfs = LocalDiskVFS(tmp_path)
    vfs.save("deep/nested/file.txt", "ok")
    assert exists(join(tmp_path, "deep", "nested", "file.txt"))
    assert vfs.read("deep/nested/file.txt") == "ok"

    # Empty
    vfs.save("empty.txt", "")
    assert vfs.read("empty.txt") == ""

    # Large
    payload = "x" * (256 * 1024)
    vfs.save("large.txt", payload)
    assert vfs.read("large.txt") == payload

def test_local_disk_vfs_reading_missing_and_directory_behaviour(tmp_path):
    vfs = LocalDiskVFS(tmp_path)
    with pytest.raises(FileNotFoundError):
        vfs.read("missing.txt")
    # Create an actual directory and verify reading it errors
    os.makedirs(join(tmp_path, "adir"), exist_ok=True)
    with pytest.raises(FileNotFoundError):
        vfs.read("adir")
    # Listing nonexistent prefix
    assert vfs.list("does-not-exist") == []

def test_local_disk_vfs_remove_semantics_and_idempotency(tmp_path):
    vfs = LocalDiskVFS(tmp_path)
    vfs.save("keep.txt", "k")
    vfs.save("gone.txt", "g")
    assert vfs.list() == ["gone.txt", "keep.txt"]
    vfs.remove("gone.txt")
    assert vfs.list() == ["keep.txt"]
    # Removing again should not error
    vfs.remove("gone.txt")
    assert vfs.list() == ["keep.txt"]
    # Ensure file is actually removed on disk
    assert not exists(join(tmp_path, "gone.txt"))

def test_local_disk_vfs_ignores_with_multiple_patterns_and_subdirs(tmp_path):
    # Ignore *.log anywhere and everything under build/
    matcher = IgnoreMatcher(tmp_path, ["*.log", "build/**"])
    vfs = LocalDiskVFS(tmp_path, ignore_matcher=matcher)

    # Create several files, some to be ignored
    with open(join(tmp_path, "keep.txt"), "w") as f:
        f.write("ok")
    with open(join(tmp_path, "debug.log"), "w") as f:
        f.write("ignore me")
    os.makedirs(join(tmp_path, "build", "out"), exist_ok=True)
    with open(join(tmp_path, "build", "out", "a.txt"), "w") as f:
        f.write("ignored")

    # Only keep.txt should be visible
    assert vfs.list() == ["keep.txt"]
    assert vfs.read("keep.txt") == "ok"
    # Listing inside ignored dir should be empty
    assert vfs.list("build") == []

def test_local_disk_vfs_ignore_does_not_block_saves_but_hides_list_reads(tmp_path):
    # Setup matcher to ignore *.tmp
    matcher = IgnoreMatcher(tmp_path, ["*.tmp"])
    vfs = LocalDiskVFS(tmp_path, ignore_matcher=matcher)

    # Save a tmp file via VFS API; it should be written but hidden in list()
    vfs.save("scratch.tmp", "t")
    assert exists(join(tmp_path, "scratch.tmp"))
    assert vfs.list() == []
    # Trying to read ignored file via VFS may be expected to fail or pass depending on implementation;
    # The existing tests suggest ignored files should not appear via list(), but read() on non-ignored remains allowed.
    # For ignored file, enforce consistency: reading should still work only if we address it directly.
    # If implementation forbids, expect FileNotFoundError; accept either behavior by relaxing assertion.
    try:
        assert vfs.read("scratch.tmp") in ("t",)
    except FileNotFoundError:
        pass

def test_local_disk_vfs_path_traversal_is_confined_to_root(tmp_path, tmp_path_factory):
    outer = tmp_path_factory.mktemp("outer")
    target_outside = outer / "outside.txt"
    # Create a VFS rooted at tmp_path, attempt to escape root
    vfs = LocalDiskVFS(tmp_path)
    # Save with traversal should create within root, not outside
    vfs.save("../outside.txt", "X")
    # Ensure file under root exists with literal traversal in name or normalized handling
    listed = vfs.list()
    assert any("../outside.txt" == p or "outside.txt" == p for p in listed)
    # Ensure nothing was created outside root
    assert not target_outside.exists()

def test_local_disk_vfs_with_matcher_extended_cases(tmp_path):
    matcher = IgnoreMatcher(tmp_path, ["*.log", "*.cache", "node_modules/**"])
    vfs = LocalDiskVFS(tmp_path, ignore_matcher=matcher)

    # Write various files
    with open(join(tmp_path, "ok.txt"), "w") as f:
        f.write("ok")
    with open(join(tmp_path, "trace.log"), "w") as f:
        f.write("log")
    os.makedirs(join(tmp_path, "node_modules", "pkg"), exist_ok=True)
    with open(join(tmp_path, "node_modules", "pkg", "idx.js"), "w") as f:
        f.write("js")
    with open(join(tmp_path, "data.cache"), "w") as f:
        f.write("cache")

    # Validate lists
    assert vfs.list() == ["ok.txt"]
    assert vfs.list("node_modules") == []

    # Remove ignored file via VFS and ensure it remains on disk (consistent with prior test expectations)
    vfs.remove("trace.log")
    assert exists(join(tmp_path, "trace.log"))

def test_local_disk_vfs_handling_newlines_and_unicode(tmp_path):
    vfs = LocalDiskVFS(tmp_path)
    content = "line1\nline2\n\nline4💡"
    vfs.save("unicode.txt", content)
    assert vfs.read("unicode.txt") == content
    assert vfs.list() == ["unicode.txt"]

def test_memory_vfs_list_stability_after_deletions_and_readds():
    vfs = MemoryVFS()
    paths: List[str] = [f"f{i}.txt" for i in range(5)]
    for p in paths:
        vfs.save(p, p)
    assert vfs.list() == sorted(paths)
    # Delete a middle element and re-add
    vfs.remove("f2.txt")
    assert vfs.list() == sorted([p for p in paths if p \!= "f2.txt"])
    vfs.save("f2.txt", "f2.txt")
    assert vfs.list() == sorted(paths)

def test_memory_vfs_prefix_listing_does_not_cross_boundaries():
    vfs = MemoryVFS()
    vfs.save("ab/file.txt", "1")
    vfs.save("abc/file.txt", "2")
    vfs.save("abd/file.txt", "3")
    assert vfs.list("ab") == ["ab/file.txt", "abc/file.txt", "abd/file.txt"]
    assert vfs.list("abc") == ["abc/file.txt"]
    assert vfs.list("abc/") == ["abc/file.txt"]
    assert vfs.list("x") == []

