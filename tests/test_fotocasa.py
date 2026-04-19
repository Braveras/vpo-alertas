from unittest.mock import patch, MagicMock
from scrapers.fotocasa import scrape

SAMPLE_HTML_VPO = """
<html><body>
  <article data-testid="re-CardPackPremium">
    <a href="/es/comprar/vivienda/madrid/piso-vpo-2hab/34/2345678" class="re-CardPackPremium-thumbnail">
      Piso VPO 2 habitaciones Getafe
    </a>
  </article>
  <article data-testid="re-CardPackPremium">
    <a href="/es/comprar/vivienda/madrid/piso-libre/34/9999999" class="re-CardPackPremium-thumbnail">
      Piso libre lujo centro
    </a>
  </article>
</body></html>
"""

SAMPLE_HTML_ALQUILER = """
<html><body>
  <article data-testid="re-CardPackPremium">
    <a href="/es/alquiler/vivienda/madrid/piso-opcion-compra/34/1111111" class="re-CardPackPremium-thumbnail">
      Alquiler con opción a compra Leganés VPP
    </a>
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
    with patch("scrapers.fotocasa.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert len(results) == 2


def test_scrape_sets_fuente_fotocasa():
    with patch("scrapers.fotocasa.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert all(r.fuente == "Fotocasa" for r in results)


def test_scrape_builds_full_fotocasa_urls():
    with patch("scrapers.fotocasa.requests.get") as mock_get:
        mock_get.side_effect = [
            _mock_response(SAMPLE_HTML_VPO),
            _mock_response(SAMPLE_HTML_ALQUILER),
        ]
        results = scrape()
    assert all(r.url.startswith("https://www.fotocasa.es") for r in results)


def test_scrape_returns_empty_on_error():
    with patch("scrapers.fotocasa.requests.get", side_effect=Exception("timeout")):
        results = scrape()
    assert results == []
