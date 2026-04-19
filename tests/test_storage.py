import json
import pytest
from pathlib import Path
from models import Listing
from storage import load_seen, save_seen, filter_new


def test_listing_id_is_sha1_of_url():
    listing = Listing(titulo="Test", url="https://example.com/1", fuente="TEST", fecha="2026-04-19")
    import hashlib
    expected = hashlib.sha1("https://example.com/1".encode()).hexdigest()
    assert listing.id == expected


def test_listing_to_dict():
    listing = Listing(titulo="Test", url="https://example.com/1", fuente="TEST", fecha="2026-04-19")
    d = listing.to_dict()
    assert d["titulo"] == "Test"
    assert d["url"] == "https://example.com/1"
    assert d["fuente"] == "TEST"
    assert d["fecha"] == "2026-04-19"
    assert "id" in d


def test_load_seen_returns_empty_set_for_empty_file(tmp_path):
    seen_file = tmp_path / "seen.json"
    seen_file.write_text("[]")
    result = load_seen(seen_file)
    assert result == set()


def test_load_seen_returns_ids(tmp_path):
    seen_file = tmp_path / "seen.json"
    seen_file.write_text('["abc123", "def456"]')
    result = load_seen(seen_file)
    assert result == {"abc123", "def456"}


def test_save_seen_writes_sorted_list(tmp_path):
    seen_file = tmp_path / "seen.json"
    save_seen({"zzz", "aaa", "mmm"}, seen_file)
    data = json.loads(seen_file.read_text())
    assert data == ["aaa", "mmm", "zzz"]


def test_filter_new_returns_only_new_listings():
    listings = [
        Listing(titulo="A", url="https://example.com/1", fuente="X", fecha="2026-04-19"),
        Listing(titulo="B", url="https://example.com/2", fuente="X", fecha="2026-04-19"),
    ]
    import hashlib
    existing_id = hashlib.sha1("https://example.com/1".encode()).hexdigest()
    seen = {existing_id}
    result = filter_new(listings, seen)
    assert len(result) == 1
    assert result[0].url == "https://example.com/2"
