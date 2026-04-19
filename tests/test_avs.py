from unittest.mock import patch, MagicMock
from scrapers.avs import scrape

SAMPLE_HTML = """
<html><body>
  <ul class="listado-noticias">
    <li>
      <a href="/convocatorias/sorteo-vpo-2026">Sorteo vivienda protección oficial 2026</a>
      <span class="fecha">19/04/2026</span>
    </li>
    <li>
      <a href="/convocatorias/renovacion-contrato">Renovación contratos alquiler social</a>
      <span class="fecha">18/04/2026</span>
    </li>
    <li>
      <a href="/convocatorias/alquiler-opcion-compra-vallecas">Alquiler con opción a compra Vallecas VPP</a>
      <span class="fecha">17/04/2026</span>
    </li>
  </ul>
</body></html>
"""


def _mock_response(html):
    mock = MagicMock()
    mock.status_code = 200
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


def test_scrape_returns_matching_listings():
    with patch("scrapers.avs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert len(results) == 2
    titles = [r.titulo for r in results]
    assert any("protección oficial" in t.lower() for t in titles)
    assert any("alquiler con opción a compra" in t.lower() for t in titles)


def test_scrape_sets_fuente_avs():
    with patch("scrapers.avs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert all(r.fuente == "AVS" for r in results)


def test_scrape_builds_full_url():
    with patch("scrapers.avs.requests.get", return_value=_mock_response(SAMPLE_HTML)):
        results = scrape()
    assert all(r.url.startswith("https://") for r in results)


def test_scrape_returns_empty_on_request_error():
    with patch("scrapers.avs.requests.get", side_effect=Exception("timeout")):
        results = scrape()
    assert results == []
