from unittest.mock import patch, MagicMock, call
from models import Listing
from notifier import send_listing, send_warning, _format_message


def test_format_message():
    listing = Listing(
        titulo="Sorteo VPO Vallecas 2026",
        url="https://bocm.es/1234",
        fuente="BOCM",
        fecha="2026-04-19",
    )
    msg = _format_message(listing)
    assert "VPO" in msg
    assert "BOCM" in msg
    assert "https://bocm.es/1234" in msg
    assert "Sorteo VPO Vallecas 2026" in msg


def test_send_listing_calls_callmebot_api():
    listing = Listing(titulo="Test VPO", url="https://example.com", fuente="TEST", fecha="2026-04-19")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("notifier.requests.get", return_value=mock_resp) as mock_get:
        send_listing(listing, phone="34600000000", apikey="testkey")
    assert mock_get.called
    args, kwargs = mock_get.call_args
    assert "api.callmebot.com" in args[0]
    assert "34600000000" in args[0]
    assert "testkey" in args[0]


def test_send_listing_retries_on_failure():
    listing = Listing(titulo="Test VPO", url="https://example.com", fuente="TEST", fecha="2026-04-19")
    mock_resp_fail = MagicMock()
    mock_resp_fail.status_code = 500
    mock_resp_ok = MagicMock()
    mock_resp_ok.status_code = 200
    with patch("notifier.requests.get", side_effect=[mock_resp_fail, mock_resp_ok]) as mock_get, \
         patch("notifier.time.sleep"):
        send_listing(listing, phone="34600000000", apikey="testkey")
    assert mock_get.call_count == 2


def test_send_warning_calls_callmebot_api():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("notifier.requests.get", return_value=mock_resp) as mock_get:
        send_warning("⚠️ Error scrapers", phone="34600000000", apikey="testkey")
    assert mock_get.called
