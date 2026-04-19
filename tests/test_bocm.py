from unittest.mock import patch, MagicMock
from scrapers.bocm import scrape


SAMPLE_FEED = {
    "entries": [
        {
            "title": "Convocatoria sorteo vivienda protección oficial Vallecas",
            "link": "https://www.bocm.es/boletin/1234",
            "published": "Sat, 19 Apr 2026 00:00:00 +0000",
        },
        {
            "title": "Resolución sobre impuesto municipal",
            "link": "https://www.bocm.es/boletin/5678",
            "published": "Sat, 19 Apr 2026 00:00:00 +0000",
        },
        {
            "title": "Adjudicación vivienda precio tasado VPP Madrid",
            "link": "https://www.bocm.es/boletin/9999",
            "published": "Sat, 19 Apr 2026 00:00:00 +0000",
        },
    ]
}


def test_scrape_returns_only_matching_entries():
    with patch("scrapers.bocm.feedparser.parse", return_value=SAMPLE_FEED):
        results = scrape()
    assert len(results) == 2
    urls = [r.url for r in results]
    assert "https://www.bocm.es/boletin/1234" in urls
    assert "https://www.bocm.es/boletin/9999" in urls
    assert "https://www.bocm.es/boletin/5678" not in urls


def test_scrape_sets_fuente_bocm():
    with patch("scrapers.bocm.feedparser.parse", return_value=SAMPLE_FEED):
        results = scrape()
    assert all(r.fuente == "BOCM" for r in results)


def test_scrape_returns_empty_on_feed_error():
    with patch("scrapers.bocm.feedparser.parse", side_effect=Exception("network error")):
        results = scrape()
    assert results == []
