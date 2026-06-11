"""
Tests for card detection and file scanning.
"""

import os
import pytest
from app.services.card_detector import CardDetector, _looks_like_storage_card


# ── _looks_like_storage_card ───────────────────────────────────────

def test_detects_card_with_dcim(tmp_path, monkeypatch):
    """A mount point containing DCIM should be detected as a card."""
    card = tmp_path / "MY_CARD"
    card.mkdir()
    (card / "DCIM").mkdir()

    monkeypatch.setattr(os.path, "ismount", lambda p: p == str(card))
    assert _looks_like_storage_card(str(card), "MY_CARD") is True


def test_detects_card_with_misc(tmp_path, monkeypatch):
    """MISC directory alone is also a valid indicator."""
    card = tmp_path / "CARD01"
    card.mkdir()
    (card / "MISC").mkdir()

    monkeypatch.setattr(os.path, "ismount", lambda p: p == str(card))
    assert _looks_like_storage_card(str(card), "CARD01") is True


def test_rejects_non_mount(tmp_path):
    """A directory that is not a mount point should be rejected."""
    card = tmp_path / "NOT_MOUNTED"
    card.mkdir()
    (card / "DCIM").mkdir()

    assert _looks_like_storage_card(str(card), "NOT_MOUNTED") is False


def test_rejects_ignored_system_dir(tmp_path, monkeypatch):
    """Known NAS system directories should be rejected."""
    for name in ["@eadir", "#recycle", "lost+found"]:
        d = tmp_path / name
        d.mkdir()
        monkeypatch.setattr(os.path, "ismount", lambda p: True)
        assert _looks_like_storage_card(str(d), name) is False, f"{name} should be rejected"


def test_rejects_no_indicator(tmp_path, monkeypatch):
    """A mount without any camera indicator dir should be rejected."""
    card = tmp_path / "USBDRIVE"
    card.mkdir()
    (card / "some_file.txt").write_text("hello")

    monkeypatch.setattr(os.path, "ismount", lambda p: p == str(card))
    assert _looks_like_storage_card(str(card), "USBDRIVE") is False


# ── CardDetector.scan() ────────────────────────────────────────────

def test_scan_only_returns_real_cards(tmp_path, monkeypatch):
    """CardDetector.scan should only return entries that pass
    _looks_like_storage_card."""
    # Create a valid card path
    card = tmp_path / "SDCARD"
    card.mkdir()
    (card / "DCIM").mkdir()

    # Create a decoy that should NOT be detected (no indicator dir)
    decoy = tmp_path / "NAS_VOLUME"
    decoy.mkdir()

    # Make both directories appear as mount points
    monkeypatch.setattr(os.path, "ismount",
                        lambda p: p in (str(card), str(decoy)))

    d = CardDetector(scan_paths=[str(tmp_path)])
    cards = d.scan()
    assert len(cards) == 1
    assert cards[0].label == "SDCARD"


def test_scan_empty_on_nonexistent():
    assert len(CardDetector(scan_paths=["/nonexistent"]).scan()) == 0


# ── File scanner ───────────────────────────────────────────────────

def test_file_scanner_filters(mock_card_dir):
    from app.services.file_scanner import scan_files

    r = list(scan_files(mock_card_dir, {"photos": True, "videos": False}))
    # ARW (raw) + JPG should both be included under "photos"
    assert len(r) == 2
    names = {f["name"] for f in r}
    assert "DSC_0001.ARW" in names
    assert "DSC_0002.JPG" in names


def test_video_filter(mock_card_dir):
    from app.services.file_scanner import scan_files

    r = list(scan_files(mock_card_dir, {"photos": False, "videos": True}))
    assert len(r) == 1
    assert r[0]["name"] == "DSC_0003.MP4"


def test_ignored_files_skipped(mock_card_dir):
    from app.services.file_scanner import scan_files
    assert not any("._DSC" in f["name"] for f in scan_files(mock_card_dir))


def test_sanitize():
    from app.services.file_scanner import sanitize_filename
    assert sanitize_filename("a:b?.txt") == "a_b_.txt"
    assert sanitize_filename("  f.txt ") == "f.txt"
