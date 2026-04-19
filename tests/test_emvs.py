from unittest.mock import patch, MagicMock
from scrapers.emvs import scrape

SAMPLE_HTML = """
<html><body>
  <div class="listado-viviendas">
    <div class="vivienda-item">
      <a href="/Viviendas/vivienda-proteccion-oficial-carabanchel">VPO Carabanchel - Promoción 2026</a>
    </div>
    <div class="vivienda-item">
      <a href="/Viviendas/vivienda-libre-centro">Vivienda libre Centro Madrid</a>
    </div>
    <div class="vivienda-item">
      <a href="/Viviendas/alquiler-opcion-compra-vallecas">Alquiler con opción a compra Vallecas</a>
    </div>
  </div>
</body></html>
"""


def _mock_response(html):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_scrape_returns_matching_listings():
    with patch("scrapers.emvs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert len(results) == 2
    titles = [r.titulo for r in results]
    assert any("vpo" in t.lower() for t in titles)
    assert any("alquiler con opción a compra" in t.lower() for t in titles)


def test_scrape_sets_fuente_emvs():
    with patch("scrapers.emvs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert all(r.fuente == "EMVS" for r in results)


def test_scrape_builds_full_url():
    with patch("scrapers.emvs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert all(r.url.startswith("https://") for r in results)


def test_scrape_returns_empty_on_error():
    with patch("scrapers.emvs.requests.get", side_effect=Exception("connection refused")):
        results = scrape()
    assert results == []
