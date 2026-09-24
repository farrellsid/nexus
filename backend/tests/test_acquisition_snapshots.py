"""The object store keeps bytes by hash, only when rights allow, and never silently changes them."""

import hashlib

import pytest

from app.acquisition.snapshots import IntegrityError, ObjectStore


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_hash_only_and_none_write_nothing(tmp_path):
    store = ObjectStore(tmp_path)
    assert store.put(b"protected", "hash_only") is None
    assert store.put(b"protected", "none") is None
    assert list(tmp_path.rglob("*")) == []


def test_a_store_policy_writes_the_content_addressed_path(tmp_path):
    store = ObjectStore(tmp_path)
    stored = store.put(b"open data", "store")
    expected = tmp_path / "objects" / "sha256" / digest(b"open data")[:2] / digest(b"open data")
    assert stored.sha256 == digest(b"open data") and stored.size == 9
    assert stored.path == expected and expected.read_bytes() == b"open data"


def test_putting_the_same_bytes_again_is_a_no_op(tmp_path):
    store = ObjectStore(tmp_path)
    first = store.put(b"same", "store")
    modified = first.path.stat().st_mtime_ns
    assert store.put(b"same", "store") == first
    assert first.path.stat().st_mtime_ns == modified


def test_different_bytes_never_share_a_path(tmp_path):
    store = ObjectStore(tmp_path)
    assert store.put(b"one", "store").path != store.put(b"two", "store").path


def test_a_put_leaves_no_temporary_files(tmp_path):
    ObjectStore(tmp_path).put(b"clean", "store")
    assert [p.name for p in tmp_path.rglob("*") if p.is_file()] == [digest(b"clean")]


def test_reading_returns_the_bytes_and_none_for_an_unknown_hash(tmp_path):
    store = ObjectStore(tmp_path)
    stored = store.put(b"readable", "store")
    assert store.get(stored.sha256) == b"readable"
    assert store.get(digest(b"never stored")) is None


def test_a_corrupted_object_is_detected_on_read(tmp_path):
    store = ObjectStore(tmp_path)
    stored = store.put(b"original", "store")
    stored.path.write_bytes(b"tampered")
    with pytest.raises(IntegrityError):
        store.get(stored.sha256)


def test_a_path_holding_the_wrong_content_is_never_overwritten(tmp_path):
    store = ObjectStore(tmp_path)
    stored = store.put(b"original", "store")
    stored.path.write_bytes(b"tampered")
    with pytest.raises(IntegrityError):
        store.put(b"original", "store")
    assert stored.path.read_bytes() == b"tampered"
