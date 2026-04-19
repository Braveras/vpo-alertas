from unittest.mock import patch, MagicMock
from scrapers.idealista import scrape

SAMPLE_HTML_VPO = """
<html><body>
  <article class="item">
    <a href="/inmueble/123456/" class="item-link">
      <span class="item-title">Piso VPO 3 habitaciones Vallecas</span>
    </a>
    <span class="item-price">150.000 €</span>
  </article>
</body></html>
"""

SAMPLE_HTML_ALQUILER = """
<html><body>
  <article class="item">
    <a href="/inmueble/555555/" class="item-link">
      <span class="item-title">Piso alquiler con opción a compra Carabanchel</span>
    </a>
    <span class="item-price">800 €/mes</span>
  </article>
</body></html>
"""


def _mock_response(html):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_scrape_returns_listings_from_both_urls():
    with patch("scrapers.idealista.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert len(results) == 2


def test_scrape_builds_full_idealista_urls():
    with patch("scrapers.idealista.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert all(r.url.startswith("https://www.idealista.com") for r in results)


def test_scrape_sets_fuente_idealista():
    with patch("scrapers.idealista.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert all(r.fuente == "Idealista" for r in results)


def test_scrape_deduplicates_same_url():
    with patch("scrapers.idealista.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_VPO),
        ]
        results = scrape()
    urls = [r.url for r in results]
    assert len(urls) == len(set(urls))


def test_scrape_returns_empty_on_error():
    with patch("scrapers.idealista.requests.get", side_effect=Exception("blocked")):
        results = scrape()
    assert results == []
