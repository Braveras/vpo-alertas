from unittest.mock import patch, MagicMock, call
from pathlib import Path
from models import Listing
from main import run


def _listing(url: str, fuente: str = "TEST") -> Listing:
    return Listing(titulo=f"Test {url}", url=url, fuente=fuente, fecha="2026-04-19")


def test_run_sends_notification_for_new_listings(tmp_path):
    seen_file = tmp_path / "seen.json"
    seen_file.write_text('[]')
    new_listing = _listing("https://bocm.es/1")

    with patch("main.bocm.scrape", return_value=[new_listing]), \
         patch("main.avs.scrape", return_value=[]), \
         patch("main.emvs.scrape", return_value=[]), \
         patch("main.idealista.scrape", return_value=[]), \
         patch("main.fotocasa.scrape", return_value=[]), \
         patch("main.send_listing") as mock_send, \
         patch("main.send_warning"), \
         patch.dict("os.environ", {"CALLMEBOT_PHONE": "34600000000", "CALLMEBOT_APIKEY": "key"}):
        run(seen_file=seen_file)

    mock_send.assert_called_once_with(new_listing, phone="34600000000", apikey="key")


def test_run_does_not_notify_seen_listings(tmp_path):
    import hashlib
    url = "https://bocm.es/1"
    existing_id = hashlib.sha1(url.encode()).hexdigest()
    seen_file = tmp_path / "seen.json"
    seen_file.write_text(f'["{existing_id}"]')
    seen_listing = _listing(url)

    with patch("main.bocm.scrape", return_value=[seen_listing]), \
         patch("main.avs.scrape", return_value=[]), \
         patch("main.emvs.scrape", return_value=[]), \
         patch("main.idealista.scrape", return_value=[]), \
         patch("main.fotocasa.scrape", return_value=[]), \
         patch("main.send_listing") as mock_send, \
         patch("main.send_warning"), \
         patch.dict("os.environ", {"CALLMEBOT_PHONE": "34600000000", "CALLMEBOT_APIKEY": "key"}):
        run(seen_file=seen_file)

    mock_send.assert_not_called()


def test_run_updates_seen_json(tmp_path):
    import json
    seen_file = tmp_path / "seen.json"
    seen_file.write_text('[]')
    new_listing = _listing("https://bocm.es/1")

    with patch("main.bocm.scrape", return_value=[new_listing]), \
         patch("main.avs.scrape", return_value=[]), \
         patch("main.emvs.scrape", return_value=[]), \
         patch("main.idealista.scrape", return_value=[]), \
         patch("main.fotocasa.scrape", return_value=[]), \
         patch("main.send_listing"), \
         patch("main.send_warning"), \
         patch.dict("os.environ", {"CALLMEBOT_PHONE": "34600000000", "CALLMEBOT_APIKEY": "key"}):
        run(seen_file=seen_file)

    saved = json.loads(seen_file.read_text())
    assert new_listing.id in saved


def test_run_sends_warning_when_all_scrapers_return_empty(tmp_path):
    seen_file = tmp_path / "seen.json"
    seen_file.write_text('[]')

    with patch("main.bocm.scrape", return_value=[]), \
         patch("main.avs.scrape", return_value=[]), \
         patch("main.emvs.scrape", return_value=[]), \
         patch("main.idealista.scrape", return_value=[]), \
         patch("main.fotocasa.scrape", return_value=[]), \
         patch("main.send_listing") as mock_send, \
         patch("main.send_warning") as mock_warn, \
         patch.dict("os.environ", {"CALLMEBOT_PHONE": "34600000000", "CALLMEBOT_APIKEY": "key"}):
        run(seen_file=seen_file)

    mock_send.assert_not_called()
    mock_warn.assert_called_once()
    assert "Error" in mock_warn.call_args[0][0]
